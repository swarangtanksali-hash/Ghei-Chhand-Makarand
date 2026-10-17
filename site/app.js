(function () {
  'use strict';
  function $(id) { return document.getElementById(id); }
  var DATA = JSON.parse($('data').textContent);
  var THEMES = JSON.parse($('themes').textContent);
  DATA.sort(function (x, y) { return x.d < y.d ? 1 : x.d > y.d ? -1 : y.n - x.n; });
  var TN = {}; THEMES.forEach(function (t) { TN[t.k] = t; });
  var byN = {}; DATA.forEach(function (p) { byN[p.n] = p; });
  var DIG = '०१२३४५६७८९';
  function mnum(n) { return String(n).replace(/\d/g, function (d) { return DIG[+d]; }); }
  function same(n) { return String(n); }

  /* ---------- interface text: Marathi only, or Marathi + English ---------- */
  var T = {
    mr: {
      num: mnum,
      months: ['जानेवारी', 'फेब्रुवारी', 'मार्च', 'एप्रिल', 'मे', 'जून', 'जुलै', 'ऑगस्ट', 'सप्टेंबर', 'ऑक्टोबर', 'नोव्हेंबर', 'डिसेंबर'],
      mi: ['जा', 'फे', 'मा', 'ए', 'मे', 'जू', 'जु', 'ऑ', 'स', 'ऑ', 'नो', 'डि'],
      name: 'मकरंद जोशी',
      today: 'आजचे कडवे', anotherLbl: 'आणखी एक कडवे',
      read: 'संपूर्ण कविता वाचा', another: 'दुसरे कडवे',
      byTopic: 'विषयानुसार', byDate: 'तारखेनुसार', browse: 'कविता कशा पाहायच्या',
      search: 'शब्द किंवा ओळ शोधा', searchLbl: 'कविता शोधा',
      poems: function (n) { return mnum(n) + ' कविता'; },
      entries: function (n) { return mnum(n) + ' नोंदी'; },
      allDesc: 'सर्व कविता',
      none: 'अशी कविता सापडली नाही.',
      newer: '‹ नवीन', older: 'जुनी ›', copy: 'कॉपी', copied: 'कॉपी झाली', copyFail: 'मजकूर निवडून कॉपी करा',
      revised: 'सुधारित',
      earlier: function (n) { return (n > 1 ? 'पूर्वीच्या आवृत्त्या' : 'पूर्वीची आवृत्ती') + ' (' + mnum(n) + ')'; },
      earlierOne: 'पूर्वीची आवृत्ती',
      list: 'कवितांची यादी',
      themeName: function (t) { return t.mr; },
      themeDesc: function (t) { return t.mrd; },
      tag: function (t) { return t.mr; }
    },
    mx: {
      num: same,
      months: ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'],
      mi: ['J', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D'],
      name: 'Makarand Joshi',
      today: "Today's verse", anotherLbl: 'Another verse',
      read: 'Read the poem', another: 'Another verse',
      byTopic: 'By topic', byDate: 'By date', browse: 'Browse poems',
      search: 'Search a word or line', searchLbl: 'Search poems',
      poems: function (n) { return n + (n === 1 ? ' poem' : ' poems'); },
      entries: function (n) { return n + (n === 1 ? ' entry' : ' entries'); },
      allDesc: 'All poems',
      none: 'No poem matches.',
      newer: '‹ Newer', older: 'Older ›', copy: 'Copy', copied: 'Copied', copyFail: 'Select the text to copy',
      revised: 'revised',
      earlier: function (n) { return 'Earlier version' + (n > 1 ? 's' : '') + ' (' + n + ')'; },
      earlierOne: 'Earlier version',
      list: 'Poems',
      themeName: function (t) { return t.mr; },
      themeDesc: function (t) { return t.en; },
      tag: function (t) { return t.mr + ' · ' + t.en; }
    }
  };
  var lang = 'mr';
  try { var saved = localStorage.getItem('bhavchhand-ui'); if (saved === 'mx' || saved === 'mr') lang = saved; } catch (e) {}
  function L() { return T[lang]; }

  function fdate(iso) {
    var p = iso.split('-'), t = L();
    if (lang === 'mr') return t.num(+p[2]) + ' ' + t.months[+p[1] - 1] + ' ' + t.num(p[0]);
    return +p[2] + ' ' + t.months[+p[1] - 1].slice(0, 3) + ' ' + p[0];
  }
  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }
  /* a line of text with every match of the search term marked */
  function marked(tag, cls, text, q) {
    var e = el(tag, cls);
    if (!q) { e.textContent = text; return e; }
    var lo = text.toLowerCase(), i = 0, j;
    while ((j = lo.indexOf(q, i)) >= 0) {
      if (j > i) e.appendChild(document.createTextNode(text.slice(i, j)));
      e.appendChild(el('mark', null, text.slice(j, j + q.length)));
      i = j + q.length;
    }
    if (i < text.length) e.appendChild(document.createTextNode(text.slice(i)));
    return e;
  }
  function flat(s) { return s.map(function (st) { return st.join(' '); }).join(' '); }
  DATA.forEach(function (p) {
    p.text = (flat(p.s) + ' ' + p.e.map(function (e) { return flat(e.s); }).join(' ')).toLowerCase();
    p.key = flat(p.s).normalize('NFC').replace(/[\s।॥.,;:!?\-–—'"()*_~\/]/g, '');
  });
  /* A poem re-posted on another date is one poem: totals count unique poems, the list shows every entry. */
  function uniq(items) {
    var seen = {}, n = 0;
    items.forEach(function (p) { if (!seen[p.key]) { seen[p.key] = 1; n++; } });
    return n;
  }

  var st = { view: 'topic', topic: null, month: null, q: '', cur: DATA[0].n };
  function term() { return st.q.trim().toLowerCase(); }

  function filtered() {
    var q = term();
    return DATA.filter(function (p) {
      if (st.view === 'topic' && st.topic && p.t.indexOf(st.topic) < 0) return false;
      if (st.view === 'date' && st.month && p.d.slice(0, 7) !== st.month) return false;
      if (q && p.text.indexOf(q) < 0) return false;
      return true;
    });
  }

  /* ---------- static labels ---------- */
  function applyStatic() {
    var t = L();
    document.documentElement.setAttribute('data-ui', lang);
    [].forEach.call(document.querySelectorAll('[data-t]'), function (n) { n.textContent = t[n.getAttribute('data-t')]; });
    [].forEach.call(document.querySelectorAll('[data-tp]'), function (n) { n.setAttribute('placeholder', t[n.getAttribute('data-tp')]); });
    [].forEach.call(document.querySelectorAll('[data-ta]'), function (n) { n.setAttribute('aria-label', t[n.getAttribute('data-ta')]); });
    var img = document.querySelector('.portrait img'); if (img) img.alt = t.name;
    [].forEach.call(document.querySelectorAll('.lang button'), function (b) { b.setAttribute('aria-pressed', String(b.dataset.l === lang)); });
  }

  /* ---------- topics ---------- */
  var topicsBox = $('topics');
  var counts = {};
  THEMES.forEach(function (t) { counts[t.k] = uniq(DATA.filter(function (p) { return p.t.indexOf(t.k) >= 0; })); });
  var maxC = Math.max.apply(null, THEMES.map(function (t) { return counts[t.k]; }));
  function buildTopics() {
    var t = L();
    topicsBox.textContent = '';
    var all = el('button', 'chip'); all.type = 'button'; all.dataset.k = '';
    all.appendChild(el('span', 'mr', 'सर्व')); all.appendChild(el('span', 'en', t.allDesc));
    all.appendChild(el('span', 'n', t.poems(uniq(DATA))));
    topicsBox.appendChild(all);
    THEMES.forEach(function (th) {
      var b = el('button', 'chip'); b.type = 'button'; b.dataset.k = th.k;
      b.appendChild(el('span', 'mr', t.themeName(th))); b.appendChild(el('span', 'en', t.themeDesc(th)));
      b.appendChild(el('span', 'n', t.poems(counts[th.k])));
      var bar = el('span', 'bar'); bar.style.width = 'calc((100% - 24px) * ' + (counts[th.k] / maxC).toFixed(3) + ')';
      b.appendChild(bar);
      topicsBox.appendChild(b);
    });
  }
  topicsBox.addEventListener('click', function (e) {
    var b = e.target.closest('.chip'); if (!b) return;
    st.topic = b.dataset.k || null; refresh(true);
  });

  /* ---------- rhythm by month ---------- */
  var rhythm = $('rhythm');
  var perMonth = {};
  DATA.forEach(function (p) { var k = p.d.slice(0, 7); perMonth[k] = (perMonth[k] || 0) + 1; });
  var keys = Object.keys(perMonth).sort();
  var maxM = Math.max.apply(null, keys.map(function (k) { return perMonth[k]; }));
  function buildRhythm() {
    var t = L();
    rhythm.textContent = '';
    var y0 = +keys[0].slice(0, 4), y1 = +keys[keys.length - 1].slice(0, 4);
    for (var y = y0; y <= y1; y++) {
      var wrap = el('div', 'yr'); wrap.appendChild(el('span', 'y', t.num(y)));
      var mos = el('div', 'mos');
      for (var m = 1; m <= 12; m++) {
        var key = y + '-' + (m < 10 ? '0' + m : m);
        var c = perMonth[key] || 0;
        if (!c && ((y === y0 && key < keys[0]) || (y === y1 && key > keys[keys.length - 1]))) continue;
        var b = el('button', 'mo'); b.type = 'button'; b.dataset.m = key;
        b.title = t.months[m - 1] + ' ' + t.num(y) + ' · ' + t.poems(c);
        b.setAttribute('aria-label', b.title);
        if (!c) b.disabled = true;
        var i = el('i'); i.style.height = (c ? Math.max(6, c / maxM * 62) : 2) + 'px';
        b.appendChild(i); b.appendChild(el('b', null, t.mi[m - 1]));
        mos.appendChild(b);
      }
      wrap.appendChild(mos); rhythm.appendChild(wrap);
    }
  }
  rhythm.addEventListener('click', function (e) {
    var b = e.target.closest('.mo'); if (!b || b.disabled) return;
    st.month = (st.month === b.dataset.m) ? null : b.dataset.m; refresh(true);
  });

  /* ---------- list ---------- */
  var list = $('list'), reader = $('reader'), countEl = $('count');
  function firstHit(p, q) {
    if (!q) return p.s[0][0];
    for (var a = 0; a < p.s.length; a++) for (var b = 0; b < p.s[a].length; b++) {
      if (p.s[a][b].toLowerCase().indexOf(q) >= 0) return p.s[a][b];
    }
    return p.s[0][0];
  }
  function renderList(items) {
    var t = L(), q = term();
    list.textContent = '';
    if (!items.length) { list.appendChild(el('div', 'none', t.none)); return; }
    var frag = document.createDocumentFragment();
    items.forEach(function (p) {
      var b = el('button', 'item'); b.type = 'button'; b.dataset.n = p.n;
      b.appendChild(marked('span', 'l1', firstHit(p, q), q));
      var l2 = el('span', 'l2'); l2.appendChild(el('em', null, mnum(p.n)));
      l2.appendChild(document.createTextNode(fdate(p.d)));
      b.appendChild(l2);
      if (p.n === st.cur) b.setAttribute('aria-current', 'true');
      frag.appendChild(b);
    });
    list.appendChild(frag);
  }
  list.addEventListener('click', function (e) {
    var b = e.target.closest('.item'); if (!b) return; select(+b.dataset.n);
  });

  /* ---------- reader ---------- */
  function stanzasEl(sts, q, ink) {
    var f = document.createDocumentFragment(), k = 0;
    sts.forEach(function (s) {
      var d = el('div', 'stanza');
      s.forEach(function (l) {
        var p = marked('p', ink ? 'ink' : null, l, q);
        if (ink) p.style.animationDelay = Math.min(k++ * 70, 1400) + 'ms';
        d.appendChild(p);
      });
      f.appendChild(d);
    });
    return f;
  }

  function renderReader(p) {
    var t = L(), q = term();
    reader.textContent = '';
    var h = el('div', 'rhead'); h.appendChild(el('span', 'num', mnum(p.n)));
    var tm = el('time', null, fdate(p.d)); tm.setAttribute('datetime', p.d); h.appendChild(tm);
    if (p.r) h.appendChild(el('span', 'rev', '· ' + t.revised + ' ' + fdate(p.r)));
    reader.appendChild(h);
    var tr = el('div', 'tagrow');
    p.t.forEach(function (k) {
      var b = el('button', 'tag', t.tag(TN[k])); b.type = 'button'; b.dataset.k = k; tr.appendChild(b);
    });
    reader.appendChild(tr);
    if (p.inv) reader.appendChild(el('p', 'inv', p.inv));
    reader.appendChild(stanzasEl(p.s, q, true));
    if (p.g) reader.appendChild(el('p', 'sig', p.g));
    var nav = el('div', 'rnav');
    var prev = el('button', 'pill', t.newer), next = el('button', 'pill', t.older), cp = el('button', 'pill', t.copy);
    prev.type = next.type = cp.type = 'button';
    prev.dataset.act = 'prev'; next.dataset.act = 'next'; cp.dataset.act = 'copy';
    nav.appendChild(prev); nav.appendChild(cp); nav.appendChild(next);
    reader.appendChild(nav);
    if (p.e.length) {
      var d = el('details', 'earlier');
      d.appendChild(el('summary', null, t.earlier(p.e.length)));
      p.e.forEach(function (e) {
        var o = el('div', 'older'); o.appendChild(el('p', 'd', t.earlierOne + ' · ' + fdate(e.d)));
        o.appendChild(stanzasEl(e.s, q, false)); d.appendChild(o);
      });
      reader.appendChild(d);
    }
    reader.scrollTop = 0;
    reader.classList.remove('turn'); void reader.offsetWidth; reader.classList.add('turn');
  }

  function select(n) {
    st.cur = n;
    renderReader(byN[n]);
    var cur = list.querySelector('[aria-current]'); if (cur) cur.removeAttribute('aria-current');
    var it = list.querySelector('.item[data-n="' + n + '"]');
    if (it) {
      it.setAttribute('aria-current', 'true');
      if (it.offsetTop < list.scrollTop || it.offsetTop + it.offsetHeight > list.scrollTop + list.clientHeight) {
        list.scrollTop = it.offsetTop - (list.clientHeight - it.offsetHeight) / 2;
      }
    }
    try { history.replaceState(null, '', '#p' + n); } catch (e) {}
  }

  function step(dir) {
    var items = filtered(); if (!items.length) return;
    var i = items.findIndex(function (p) { return p.n === st.cur; });
    i = i < 0 ? 0 : (i + dir + items.length) % items.length;
    select(items[i].n);
  }

  reader.addEventListener('click', function (e) {
    var a = e.target.closest('[data-act]'), tg = e.target.closest('.tag');
    if (tg) {
      st.view = 'topic'; st.topic = tg.dataset.k; st.q = ''; $('q').value = '';
      refresh(true); $('explore').scrollIntoView({ block: 'start' }); return;
    }
    if (!a) return;
    if (a.dataset.act === 'prev') step(-1);
    else if (a.dataset.act === 'next') step(1);
    else if (a.dataset.act === 'copy') {
      var t = L(), p = byN[st.cur];
      var txt = (p.inv ? p.inv + '\n' : '') + p.s.map(function (s) { return s.join('\n'); }).join('\n\n') + (p.g ? '\n' + p.g : '');
      var done = function (m) { a.textContent = m; setTimeout(function () { a.textContent = L().copy; }, 1400); };
      try { navigator.clipboard.writeText(txt).then(function () { done(t.copied); }, function () { done(t.copyFail); }); }
      catch (err) { done(t.copyFail); }
    }
  });

  function refresh(pick) {
    var t = L(), items = filtered();
    topicsBox.hidden = st.view !== 'topic';
    rhythm.hidden = st.view !== 'date';
    [].forEach.call(topicsBox.children, function (b) { b.setAttribute('aria-pressed', String((b.dataset.k || null) === st.topic)); });
    [].forEach.call(rhythm.querySelectorAll('.mo'), function (b) { b.setAttribute('aria-pressed', String(b.dataset.m === st.month)); });
    [].forEach.call(document.querySelectorAll('.view button'), function (b) { b.setAttribute('aria-pressed', String(b.dataset.v === st.view)); });
    var u = uniq(items);
    var label = t.poems(u) + (items.length > u ? ' · ' + t.entries(items.length) : '');
    if (st.view === 'topic' && st.topic) label += ' · ' + t.themeName(TN[st.topic]);
    if (st.view === 'date' && st.month) { var p = st.month.split('-'); label += ' · ' + t.months[+p[1] - 1] + ' ' + t.num(p[0]); }
    countEl.textContent = label;
    if (pick && items.length && !items.some(function (p) { return p.n === st.cur; })) st.cur = items[0].n;
    renderList(items);
    if (items.length) {
      renderReader(byN[st.cur]);
      var it = list.querySelector('[aria-current]'); if (it) list.scrollTop = Math.max(0, it.offsetTop - 80);
    } else reader.textContent = '';
  }

  document.querySelector('.view').addEventListener('click', function (e) {
    var b = e.target.closest('button'); if (!b) return; st.view = b.dataset.v; refresh(true);
  });
  $('q').addEventListener('input', function () { st.q = this.value; refresh(true); });
  document.addEventListener('keydown', function (e) {
    var tn = e.target.tagName;
    if (tn === 'INPUT' || tn === 'TEXTAREA') return;
    if (e.key === 'ArrowRight') step(1); else if (e.key === 'ArrowLeft') step(-1);
  });

  /* ---------- today's verse: the same verse for everyone on a given day ---------- */
  var feat = $('feat'), featLbl = $('featLbl');
  var dayNo = Math.floor((Date.now() - new Date().getTimezoneOffset() * 60000) / 86400000);
  var featN = DATA[dayNo % DATA.length].n, featDaily = true;
  function renderFeature() {
    var p = byN[featN];
    feat.textContent = '';
    featLbl.textContent = featDaily ? L().today : L().anotherLbl;
    p.s[0].slice(0, 4).forEach(function (l, k) {
      var e = el('p', 'ink', l); e.style.animationDelay = (k * 140) + 'ms'; feat.appendChild(e);
    });
  }
  $('another').addEventListener('click', function () {
    var p; do { p = DATA[Math.floor(Math.random() * DATA.length)]; } while (p.n === featN && DATA.length > 1);
    featN = p.n; featDaily = false; renderFeature();
  });
  $('readit').addEventListener('click', function () {
    st.view = 'topic'; st.topic = null; st.month = null; st.q = ''; $('q').value = '';
    st.cur = featN; refresh(false); select(featN);
    $('explore').scrollIntoView({ block: 'start' });
  });

  /* ---------- language toggle ---------- */
  function renderAll() {
    applyStatic(); buildTopics(); buildRhythm(); renderFeature(); refresh(false);
  }
  document.querySelector('.lang').addEventListener('click', function (e) {
    var b = e.target.closest('button'); if (!b || b.dataset.l === lang) return;
    lang = b.dataset.l;
    try { localStorage.setItem('bhavchhand-ui', lang); } catch (err) {}
    renderAll();
  });

  var m = /^#p(\d+)$/.exec(location.hash || '');
  if (m && byN[+m[1]]) st.cur = +m[1];
  renderAll();

  /* ---------- drifting motes of light behind the title page ---------- */
  (function motes() {
    var c = $('motes');
    if (!c || !c.getContext) return;
    var still = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (still) { c.hidden = true; return; }
    var ctx = c.getContext('2d'), W = 0, H = 0, P = [], raf = 0, col = '165,125,63';
    function readCol() {
      var v = getComputedStyle(document.documentElement).getPropertyValue('--mote').trim();
      if (/^\d+\s*,\s*\d+\s*,\s*\d+$/.test(v)) col = v;
    }
    function size() {
      var r = c.getBoundingClientRect(), dpr = Math.min(2, window.devicePixelRatio || 1);
      W = r.width; H = r.height; c.width = Math.round(W * dpr); c.height = Math.round(H * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }
    function spawn(p, init) {
      p.x = Math.random() * W; p.y = init ? Math.random() * H : H + 8;
      p.r = 0.6 + Math.random() * 1.7; p.vy = 0.06 + Math.random() * 0.2;
      p.ph = Math.random() * 6.283; p.a = 0.18 + Math.random() * 0.5;
    }
    size(); readCol();
    for (var i = 0; i < 30; i++) { var p = {}; spawn(p, true); P.push(p); }
    function tick(t) {
      ctx.clearRect(0, 0, W, H);
      for (var k = 0; k < P.length; k++) {
        var q = P[k];
        q.y -= q.vy; q.x += Math.sin(t / 2600 + q.ph) * 0.14;
        if (q.y < -8) spawn(q, false);
        var tw = 0.5 + 0.5 * Math.sin(t / 1100 + q.ph * 3);
        ctx.beginPath();
        ctx.fillStyle = 'rgba(' + col + ',' + (q.a * tw).toFixed(3) + ')';
        ctx.shadowColor = 'rgba(' + col + ',.7)'; ctx.shadowBlur = 8;
        ctx.arc(q.x, q.y, q.r, 0, 6.283); ctx.fill();
      }
      raf = requestAnimationFrame(tick);
    }
    raf = requestAnimationFrame(tick);
    window.addEventListener('resize', size);
    document.addEventListener('visibilitychange', function () {
      cancelAnimationFrame(raf); if (!document.hidden) raf = requestAnimationFrame(tick);
    });
    try { window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', readCol); } catch (e) {}
    try { new MutationObserver(readCol).observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] }); } catch (e) {}
  })();
})();
