import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const code = fs.readFileSync('assets/conversion.js', 'utf8');
function setup(hostname) {
  const scripts = [], listeners = {};
  const context = {
    window: {}, URL, URLSearchParams,
    location: { hostname, origin: 'https://' + hostname, pathname: '/sojingong', search: '?utm_source=naver&utm_medium=cpc&phone=01012345678#private' },
    document: {
      referrer: 'https://example.com/article?email=private@example.com',
      head: { appendChild: s => scripts.push(s) },
      createElement: () => ({}), getElementById: () => null, querySelectorAll: () => [],
      addEventListener: (name, fn) => { listeners[name] = fn; }
    },
    Element: class Element {}
  };
  vm.createContext(context);
  vm.runInContext(code, context);
  return { context, scripts, listeners };
}
for (const host of ['bmaker.kr', 'www.bmaker.kr']) {
  const { context, scripts, listeners } = setup(host);
  assert.equal(scripts.length, 1);
  assert.equal(scripts[0].async, true);
  assert.equal(scripts[0].src, 'https://www.googletagmanager.com/gtag/js?id=G-DBGR3P6ZHD');
  const config = context.window.dataLayer.find(args => args[0] === 'config');
  assert.equal(config[1], 'G-DBGR3P6ZHD');
  assert.equal(config[2].page_location, `https://${host}/sojingong?utm_source=naver&utm_medium=cpc`);
  assert.equal(config[2].page_referrer, 'https://example.com/article');
  assert.equal(config[2].allow_google_signals, false);
  const link = { getAttribute: () => '/#apply', dataset: {}, closest: () => null };
  const target = new context.Element(); target.closest = () => link;
  listeners.click({ target });
  const event = context.window.dataLayer.find(args => args[0] === 'event');
  assert.equal(event[1], 'consultation_click');
  assert.equal(event[2].page_path, '/sojingong');
  assert.ok(!JSON.stringify(context.window.dataLayer).includes('01012345678'));
  assert.ok(!JSON.stringify(context.window.dataLayer).includes('private@example.com'));
  vm.runInContext(code, context);
  assert.equal(scripts.length, 1);
  assert.equal(context.window.dataLayer.filter(args => args[0] === 'config').length, 1);
}
for (const host of ['localhost', 'preview.workers.dev']) {
  const { context, scripts } = setup(host);
  assert.equal(scripts.length, 0);
  assert.equal(context.window.gtag, undefined);
}
console.log('GA4 initialization, event queue, campaign attribution, URL filtering and preview exclusion passed.');
