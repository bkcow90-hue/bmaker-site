/* 홈 영상: 페이지 로드가 끝난 뒤에만 받는다. 모션 저감·데이터 절약·느린 회선에서는 정지 이미지만. */
(function () {
  var rm = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  var c = navigator.connection || {};
  if (rm || c.saveData || /(^|-)2g$/.test(c.effectiveType || '')) return;
  var io = 'IntersectionObserver' in window;

  function play(v) { var p = v.play(); if (p && p.catch) p.catch(function () {}); }

  var hero = document.querySelector('.hero-video');
  if (hero) {
    var section = hero.closest('.hero');
    var labels = document.querySelectorAll('.hero-reel li');
    var CUT = [0, 3.4, 6.4, 9.4]; // 장면 전환 시점(초) — 영상 파일과 같이 바꾼다
    var start = function () {
      var phone = matchMedia('(max-width: 600px)').matches; // 휴대폰은 세로로 자른 영상
      hero.src = phone ? hero.getAttribute('data-src-mobile') : hero.getAttribute('data-src-desktop');
      hero.addEventListener('playing', function () {
        hero.classList.add('on'); if (section) section.classList.add('playing');
      }, { once: true });
      play(hero);
      if (io) new IntersectionObserver(function (es) {
        es.forEach(function (e) { if (e.isIntersecting) play(hero); else hero.pause(); });
      }).observe(hero);
    };
    if (document.readyState === 'complete') setTimeout(start, 200);
    else addEventListener('load', function () { setTimeout(start, 200); });

    // 장면 진행 막대: 재생 중에만 프레임마다 채운다
    var ticking = false;
    var tick = function () {
      if (hero.paused || hero.ended) { ticking = false; return; }
      var t = hero.currentTime, d = hero.duration || 12.8, i = 3;
      for (var k = 0; k < CUT.length; k++) if (t >= CUT[k]) i = k;
      var end = i < 3 ? CUT[i + 1] : d;
      for (var j = 0; j < labels.length; j++) {
        labels[j].classList.toggle('on', j === i);
        labels[j].classList.toggle('done', j < i);
      }
      if (labels[i]) labels[i].style.setProperty('--p', Math.min(1, (t - CUT[i]) / (end - CUT[i])).toFixed(3));
      requestAnimationFrame(tick);
    };
    if (labels.length) hero.addEventListener('playing', function () {
      if (!ticking) { ticking = true; requestAnimationFrame(tick); }
    });
  }

  var diag = document.querySelector('.diag-video');
  if (diag && io) new IntersectionObserver(function (es) {
    es.forEach(function (e) {
      if (e.isIntersecting) { if (!diag.getAttribute('src')) diag.src = diag.getAttribute('data-src'); play(diag); }
      else diag.pause();
    });
  }, { rootMargin: '200px' }).observe(diag);
})();

/* 휴대폰 구성 — 옆으로 넘기는 카드의 위치 점, 긴 문단 "더 보기", 이력·원장 띠 접기.
   글은 전부 HTML 에 있다. 스크립트가 없으면 전부 펼쳐진 채로 보인다. */
(function () {
  var phone = window.matchMedia && matchMedia('(max-width: 760px)').matches;

  // 1) 카드 묶음 위치 점 (CSS 가 760px 이하에서만 옆 넘김으로 바꾼다)
  var CARS = '#top .entry-grid, #top .trust-list, #top .why-grid, #top .svc-grid, #top .audience-routes, #top .case-track, #top .guides .g-grid';
  document.querySelectorAll(CARS).forEach(function (car) {
    var n = car.children.length; if (n < 2) return;
    var dots = document.createElement('div');
    dots.className = 'car-dots'; dots.setAttribute('aria-hidden', 'true');
    for (var i = 0; i < n; i++) dots.appendChild(document.createElement('i'));
    car.classList.add('car');
    car.parentNode.insertBefore(dots, car.nextSibling);
    var raf = 0;
    var mark = function () {
      raf = 0;
      var first = car.children[0], w = first ? first.getBoundingClientRect().width + 12 : 1;
      var idx = Math.min(n - 1, Math.round(car.scrollLeft / w));
      if (car.scrollLeft + car.clientWidth >= car.scrollWidth - 4) idx = n - 1;
      for (var j = 0; j < n; j++) dots.children[j].classList.toggle('on', j === idx);
    };
    car.addEventListener('scroll', function () { if (!raf) raf = requestAnimationFrame(mark); }, { passive: true });
    mark();
  });

  if (phone) {
    // 2) 긴 문단은 세 줄만 보이고 "더 보기"
    var CLAMP = '#top #principles .trust-intro > p, #top #about .about-grid > div > p, #top #experts .sub, #top #cases .sub,'
              + '#top #cases .note, #top #cases .audience-note, #top #guides .sub, #top .diagnosis-result, #top .evidence .ev-lead';
    document.querySelectorAll(CLAMP).forEach(function (p) {
      if (p.classList.contains('clamp-rest')) return;
      p.classList.add('clamp');
      // 바로 이어지는 문단들은 같은 버튼으로 함께 편다(버튼이 문단마다 붙지 않게)
      var rest = [], nx = p.nextElementSibling;
      while (nx && nx.tagName === 'P' && nx.matches(CLAMP)) { nx.classList.add('clamp-rest'); rest.push(nx); nx = nx.nextElementSibling; }
      if (!rest.length && p.scrollHeight <= p.clientHeight + 4) { p.classList.remove('clamp'); return; }
      var b = document.createElement('button');
      b.type = 'button'; b.className = 'clamp-more'; b.textContent = '더 보기'; b.setAttribute('aria-expanded', 'false');
      b.addEventListener('click', function () {
        var open = p.classList.toggle('open');
        rest.forEach(function (r) { r.classList.toggle('open', open); });
        b.setAttribute('aria-expanded', open ? 'true' : 'false'); b.textContent = open ? '접기' : '더 보기';
      });
      (rest.length ? rest[rest.length - 1] : p).insertAdjacentElement('afterend', b);
    });

    // 3) 이력 3칸·최근 사례 띠는 눌러서 편다
    var fold = function (el, label) {
      var b = document.createElement('button');
      b.type = 'button'; b.className = 'fold-btn'; b.textContent = label; b.setAttribute('aria-expanded', 'false');
      el.classList.add('fold');
      b.addEventListener('click', function () {
        el.style.setProperty('--fh', el.scrollHeight + 40 + 'px');
        var open = el.classList.toggle('open');
        b.setAttribute('aria-expanded', open ? 'true' : 'false');
      });
      el.parentNode.insertBefore(b, el);
    };
    document.querySelectorAll('#top .person-cols').forEach(function (el) { fold(el, '이력 보기'); });
    var ledger = document.querySelector('#top .cases-ledger'); if (ledger) fold(ledger, '최근 받은 사례 5건 보기');
  }

  // 4) 읽은 만큼 차는 상단 막대
  if (!(window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches)) {
    var bar = document.createElement('div'); bar.className = 'scroll-prog'; bar.setAttribute('aria-hidden', 'true');
    document.body.appendChild(bar);
    var q = 0, paint = function () {
      q = 0;
      var max = document.documentElement.scrollHeight - window.innerHeight;
      bar.style.transform = 'scaleX(' + (max > 0 ? Math.min(1, window.scrollY / max) : 0) + ')';
    };
    addEventListener('scroll', function () { if (!q) q = requestAnimationFrame(paint); }, { passive: true });
    paint();
  }
})();

/* 스크롤 움직임 — 카드·사람·절차·숫자. 모션 저감이면 실행하지 않는다(내용은 처음부터 보임). */
(function () {
  if (!('IntersectionObserver' in window)) return;
  if (window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  var phone = matchMedia('(max-width: 760px)').matches;
  var vh = window.innerHeight || document.documentElement.clientHeight;
  var io = new IntersectionObserver(function (es) {
    es.forEach(function (e) {
      if (!e.isIntersecting) return;
      var el = e.target;
      if (el.classList.contains('steps')) el.classList.add('mo-line');
      else if (el.classList.contains('person')) { var ph = el.querySelector('.person-photo.mo'); if (ph) ph.classList.add('mo-in'); }
      else el.classList.add('mo-in');
      if (el.hasAttribute('data-count')) count(el);
      io.unobserve(el);
    });
  }, { threshold: 0.15, rootMargin: '0px 0px -8% 0px' });

  function prep(sel, step) {
    var groups = new Map();
    document.querySelectorAll(sel).forEach(function (el) {
      if (el.getBoundingClientRect().top < vh) return; // 이미 보이는 것은 숨기지 않는다
      var p = el.parentElement, i = groups.get(p) || 0; groups.set(p, i + 1);
      el.style.setProperty('--mo-d', Math.min(i, 6) * step + 'ms');
      el.classList.add('mo'); io.observe(el);
    });
  }
  // 휴대폰은 카드 묶음(옆 넘김)을 통째로, PC 는 카드 하나씩 차례로
  prep(phone
    ? '#top .car, #top .diag-media, #top #process .step, #top .ev-row a, #top .exp-banner, #top .person .fold-btn'
    : '#top .entry-card, #top .why-card, #top .diag-media, #top #process .step, #top .person-body, #top .case, #top .ev-row a, #top .trust-list article', 90);
  // 사진은 clip-path 로 가려 두므로(교차 판정이 안 잡힘) 카드 전체를 관찰한다
  document.querySelectorAll('#top .person').forEach(function (card) {
    var ph = card.querySelector('.person-photo');
    if (!ph || card.getBoundingClientRect().top < vh) return;
    ph.classList.add('mo'); io.observe(card);
  });
  var steps = document.querySelector('#top #process .steps'); if (steps) io.observe(steps);

  function count(el) {
    var end = parseInt(el.getAttribute('data-count'), 10), t0 = null, dur = 1100;
    function f(ts) {
      if (!t0) t0 = ts;
      var k = Math.min(1, (ts - t0) / dur), v = Math.round(end * (1 - Math.pow(1 - k, 3)));
      el.textContent = v.toLocaleString('ko-KR');
      if (k < 1) requestAnimationFrame(f);
    }
    requestAnimationFrame(f);
  }
  document.querySelectorAll('#top #principles [data-stat="total-n"], #top #principles [data-stat="ev-n"]').forEach(function (el) {
    var n = parseInt(el.textContent.replace(/[^\d]/g, ''), 10);
    if (!n || el.getBoundingClientRect().top < vh) return;
    el.setAttribute('data-count', n); io.observe(el);
  });
})();
