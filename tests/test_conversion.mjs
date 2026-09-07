// Run the production handler in a small DOM fixture; fetch cannot reach a network.
import vm from 'node:vm';
import fs from 'node:fs';
import assert from 'node:assert/strict';
import { webcrypto } from 'node:crypto';
const script = fs.readFileSync('assets/conversion.js', 'utf8');
class Element {
  constructor() { this.value = ''; this.listeners = {}; this.dataset = {}; this.attributes = {}; this.children = []; this.textContent = ''; }
  addEventListener(type, fn) { this.listeners[type] = fn; }
  setAttribute(k, v) { this.attributes[k] = v; }
  getAttribute(k) { return this.attributes[k]; }
  removeAttribute(k) { delete this.attributes[k]; }
  setCustomValidity(v) { this.invalid = v; }
  appendChild(x) { this.children.push(x); }
  focus() {} contains() { return false; }
}
function fixture(mode, service = "general") {
  const els = Object.fromEntries(['leadForm','applyMsg','lf-phone','lf-name','lf-biz','lf-memo','lf-consent','lf-website','lf-service'].map(id => [id,new Element()]));
  const button = new Element(), f = els.leadForm;
  f.querySelector = () => button;
  f.reportValidity = () => !els['lf-phone'].invalid && !els['lf-name'].invalid && els['lf-consent'].checked;
  f.reset = () => { for (const x of Object.values(els)) x.value = ''; };
  els['lf-name'].value = '테스트'; els['lf-phone'].value = '010-0000-0000'; els['lf-consent'].checked = true;
  const events = [], bodies = []; let abort;
  const window = { dataLayer: { push: e => events.push(e) } };
  const document = { getElementById: id => els[id], querySelectorAll: () => [], querySelector: () => null, addEventListener() {}, createElement: () => new Element() };
  const fetch = async (_, opts) => {
    bodies.push(JSON.parse(opts.body));
    if (mode === 'timeout') { abort(); throw Object.assign(new Error(), { name:'AbortError' }); }
    if (mode === 'network') throw new Error('mock');
    if (mode === 'bad_json') return { ok:true, json: async () => { throw new SyntaxError(); } };
    return { ok: mode !== 'http_error', json: async () => mode === 'success' ? { ok:true, delivery:'accepted' } : mode === 'legacy' ? { ok:true } : { ok:false, delivery:'failed' } };
  };
  vm.runInNewContext(script, { window, document, location:{ pathname:'/', search:'?service='+service }, URLSearchParams, Element, fetch, crypto:webcrypto, AbortController, setTimeout:fn => {abort=fn; return 1;}, clearTimeout() {} });
  return { els, button, events, bodies, submit: () => f.listeners.submit({ preventDefault() {} }) };
}
for (const mode of ['success','legacy','http_error','network','bad_json','timeout']) {
  const f = fixture(mode); await f.submit();
  assert.equal(f.button.disabled, false);
  assert.equal(f.bodies[0].delivery_required, true);
  assert.equal(f.events.filter(e => e.event === 'generate_lead').length, mode === 'success' ? 1 : 0);
  if (mode === 'success') { await f.submit(); assert.equal(f.bodies.length,1,'double submit after completion ignored'); }
  else {
    assert.equal(f.els['lf-name'].value, '테스트'); assert.equal(f.els.applyMsg.children[0].children.length, 2);
    await f.submit(); assert.equal(f.bodies[0].request_id, f.bodies[1].request_id); assert.equal(f.bodies[0].submitted_at, f.bodies[1].submitted_at);
  }
  assert.ok(!JSON.stringify(f.events).includes('01000000000'), 'analytics exclude contact data');
}
const invalid = fixture('success'); invalid.els['lf-phone'].value = 'invalid'; await invalid.submit(); assert.equal(invalid.bodies.length, 0);
const pending = fixture('network'); await Promise.all([pending.submit(),pending.submit()]); assert.equal(pending.bodies.length,1);
console.log('Conversion handler: delivery contract, duplicate guard, retries, validation, errors and privacy passed.');

for (const service of ['policy', 'marketing', 'startup', 'certification', 'general']) {
  const f = fixture('success', service);
  assert.equal(f.els['lf-service'].value, service, 'landing choice preselected');
  await f.submit();
  assert.equal(f.bodies[0].consultation_service, service);
  assert.equal(f.bodies[0].service, service === 'policy' ? 'pfm' : service);
  assert.ok(f.bodies[0].answers_text.includes(f.bodies[0].service_name));
  assert.equal(f.events.find(e => e.event === 'generate_lead').service_category, service, 'category survives form reset');
}
const unknown = fixture('success', '__proto__');
assert.equal(unknown.els['lf-service'].value, 'general');
const changed = fixture('network', 'marketing'); await changed.submit();
changed.els['lf-service'].value = 'startup'; await changed.submit();
assert.notEqual(changed.bodies[0].request_id, changed.bodies[1].request_id, 'changed inquiry gets new id');
assert.equal(changed.bodies[1].consultation_service, 'startup');
console.log('Service preselection, lead routing, category tracking and changed-service retries passed.');
