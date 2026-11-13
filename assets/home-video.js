/* 홈 영상: 페이지 로드가 끝난 뒤에만 받는다. 모션 저감·데이터 절약·느린 회선에서는 정지 이미지만. */
(function () {
  var rm = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  var c = navigator.connection || {};
  if (rm || c.saveData || /(^|-)2g$/.test(c.effectiveType || '')) return;
  var io = 'IntersectionObserver' in window;

  function play(v) { var p = v.play(); if (p && p.catch) p.catch(function () {}); }

  var hero = document.querySelector('.hero-video');
  if (hero) {
    var labels = document.querySelectorAll('.hero-reel li');
    var start = function () {
      var mobile = matchMedia('(max-width: 860px)').matches;
      hero.src = mobile ? hero.getAttribute('data-src-mobile') : hero.getAttribute('data-src-desktop');
      hero.addEventListener('playing', function () { hero.classList.add('on'); }, { once: true });
      play(hero);
      if (io) new IntersectionObserver(function (es) {
        es.forEach(function (e) { if (e.isIntersecting) play(hero); else hero.pause(); });
      }).observe(hero);
    };
    if (document.readyState === 'complete') setTimeout(start, 200);
    else addEventListener('load', function () { setTimeout(start, 200); });
    if (labels.length) hero.addEventListener('timeupdate', function () {
      var t = hero.currentTime, i = t < 3.4 ? 0 : t < 6.4 ? 1 : t < 9.4 ? 2 : 3;
      for (var j = 0; j < labels.length; j++) labels[j].classList.toggle('on', j === i);
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
