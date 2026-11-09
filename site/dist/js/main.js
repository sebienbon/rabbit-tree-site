/* The Rabbit Tree Hostel — interactions
   1. menu mobile   3. diaporama   4. vortex entre les pages   5. lightbox */
(function () {
  "use strict";

  /* --- 1. menu --- */
  var nav = document.getElementById("nav");
  var toggle = nav && nav.querySelector(".nav-toggle");
  if (toggle) {
    toggle.addEventListener("click", function () {
      var open = nav.classList.toggle("open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
    document.addEventListener("click", function (e) {
      if (nav.classList.contains("open") && !nav.contains(e.target)) {
        nav.classList.remove("open");
        toggle.setAttribute("aria-expanded", "false");
      }
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && nav.classList.contains("open")) {
        nav.classList.remove("open");
        toggle.setAttribute("aria-expanded", "false");
      }
    });
  }

  /* --- 3. diaporama des chambres : pellicule + glissement dans le cadre --- */
  var stage = document.querySelector(".stage");
  if (stage) {
    var slides = [].slice.call(stage.querySelectorAll(".slide"));
    var thumbs = [].slice.call(document.querySelectorAll(".strip a[data-full]"));
    thumbs.forEach(function (t, i) {
      t.addEventListener("click", function (e) {
        e.preventDefault();
        var s = slides[i];
        if (s) stage.scrollTo({ left: s.offsetLeft - stage.offsetLeft, behavior: "smooth" });
      });
    });
    var sync = function () {
      var c = stage.scrollLeft + stage.clientWidth / 2, best = 0, bd = 1e9;
      slides.forEach(function (s, i) {
        var d = Math.abs(s.offsetLeft + s.offsetWidth / 2 - stage.offsetLeft - c);
        if (d < bd) { bd = d; best = i; }
      });
      thumbs.forEach(function (x, i) { x.classList.toggle("active", i === best); });
    };
    stage.addEventListener("scroll", function () { window.requestAnimationFrame(sync); });
    sync();
  }

  /* --- 4. le vortex : on clique un dessin, il tourne et aspire la page ; la page suivante
         s'ouvre en sortant du meme vortex. Un seul clic, deux mouvements enchaines. --- */
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  function spiralPath(phase) {
    var d = "", turns = 7, n = 300;
    for (var i = 0; i <= n; i++) {
      var t = i / n * turns * 2 * Math.PI, r = 50 * i / n;
      d += (i ? " L" : "M") + (50 + r * Math.cos(t + phase)).toFixed(1) + "," + (50 + r * Math.sin(t + phase)).toFixed(1);
    }
    return d;
  }
  var vortex = document.createElement("div");
  vortex.id = "vortex";
  vortex.setAttribute("aria-hidden", "true");
  vortex.innerHTML = '<svg viewBox="0 0 100 100" preserveAspectRatio="xMidYMid slice">' +
    '<path d="' + spiralPath(0) + '" fill="none" stroke="#1c1a17" stroke-width="3.4" stroke-linecap="round"/>' +
    '<path d="' + spiralPath(Math.PI) + '" fill="none" stroke="#1c1a17" stroke-width="1.6" stroke-linecap="round"/></svg>';
  document.documentElement.appendChild(vortex);
  var root = document.documentElement, body = document.body;

  function place(x, y) {
    /* un disque assez grand pour couvrir l'ecran depuis le point de depart */
    var w = window.innerWidth, h = window.innerHeight;
    var R = Math.sqrt(Math.pow(Math.max(x, w - x), 2) + Math.pow(Math.max(y, h - y), 2)) * 2.1;
    vortex.style.width = vortex.style.height = R + "px";
    vortex.style.left = x + "px";
    vortex.style.top = y + "px";
  }
  function remember(x, y) {
    try { sessionStorage.setItem("rt-vortex", JSON.stringify({ x: x / window.innerWidth, y: y / window.innerHeight, t: Date.now() })); } catch (e) {}
  }

  /* arrivee : si on vient d'un vortex, la page sort du tourbillon */
  try {
    var v = JSON.parse(sessionStorage.getItem("rt-vortex") || "null");
    sessionStorage.removeItem("rt-vortex");
    if (v && Date.now() - v.t < 4000 && !reduce) {
      vortex.addEventListener("animationend", function () { vortex.classList.remove("out"); }, { once: true });
    }
  } catch (e) {}
  /* arrivee : on ressort du logo de la page (data-portal), sinon du centre de l'ecran */
  if (root.classList.contains("rt-arrive")) {
    var ox = window.innerWidth / 2, oy = window.innerHeight / 2;
    var portal = document.querySelector("[data-portal]");
    if (portal) {
      body.style.transform = "none";              /* mesure sans le zoom d'attente */
      var pr = portal.getBoundingClientRect();
      body.style.transform = "";
      if (pr.width) { ox = pr.left + pr.width / 2; oy = pr.top + pr.height / 2; }
    }
    body.style.transformOrigin = ox + "px " + (oy + window.pageYOffset) + "px";
    place(ox, oy);
    vortex.classList.remove("out"); void vortex.offsetWidth; vortex.classList.add("out");
    var done = function () {
      root.classList.remove("rt-arrive"); body.classList.remove("spin-in"); body.style.transformOrigin = "";
    };
    body.addEventListener("animationend", function (ev) { if (ev.target === body) done(); }, { once: true });
    void body.offsetWidth;
    body.classList.add("spin-in");
    setTimeout(done, 1400);
  }

  [].slice.call(document.querySelectorAll("a[data-vortex]")).forEach(function (a) {
    a.addEventListener("click", function (e) {
      if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey || e.button) return;
      var href = a.getAttribute("href");
      if (!href || href.charAt(0) === "#") return;
      e.preventDefault();
      var r = a.getBoundingClientRect();
      var x = r.left + r.width / 2, y = r.top + r.height / 2;
      var go = function () { window.location.href = href; };
      if (reduce) { remember(x, y); go(); return; }
      /* 1er mouvement : sur l'arbre, la spirale du medaillon s'ouvre en tournant */
      var delay = 0;
      if (a.querySelector(".swirl")) { a.classList.add("opening"); delay = 380; }
      setTimeout(function () {
        /* 2e mouvement : le vortex part du dessin et grandit en tournant jusqu'a couvrir la page */
        place(x, y);
        vortex.classList.remove("out", "in"); void vortex.offsetWidth; vortex.classList.add("in");
        /* ... et toute la page s'enroule autour du dessin clique */
        body.style.transformOrigin = x + "px " + (y + window.pageYOffset) + "px";
        root.classList.add("rt-spin");
        body.classList.add("spin-out");
        remember(x, y);
        setTimeout(go, 680);
      }, delay);
    });
  });
  /* retour arriere depuis la page suivante : ne pas rester sur un ecran couvert */
  window.addEventListener("pageshow", function (e) {
    if (e.persisted) {
      vortex.classList.remove("in", "out");
      body.classList.remove("spin-out"); root.classList.remove("rt-spin", "rt-arrive"); body.style.transformOrigin = "";
    }
    [].slice.call(document.querySelectorAll(".opening")).forEach(function (x) { x.classList.remove("opening"); });
  });

  /* --- 6. prix en direct : feuille "Data activities" (colonnes A et B) via le fichier relais public.
         Le nom de la colonne A sert de cle ; la page garde son prix de repli si la feuille ne repond pas. --- */
  var pxEls = [].slice.call(document.querySelectorAll(".px[data-price]"));
  if (pxEls.length) {
    var SHEET = "https://docs.google.com/spreadsheets/d/19A5y3XcOOgQ0mxiDxdueaXwKxcSGujh_5xpgT4QfocI/gviz/tq?tqx=out:csv";
    var norm = function (k) { return String(k).toLowerCase().replace(/^\s*-\s*/, "").replace(/\s+/g, ""); };
    var parseCsv = function (text) {
      var rows = [], row = [], cell = "", q = false;
      for (var i = 0; i < text.length; i++) {
        var c = text[i];
        if (q) { if (c === '"') { if (text[i + 1] === '"') { cell += '"'; i++; } else q = false; } else cell += c; }
        else if (c === '"') q = true;
        else if (c === ",") { row.push(cell); cell = ""; }
        else if (c === "\n") { row.push(cell); rows.push(row); row = []; cell = ""; }
        else if (c !== "\r") cell += c;
      }
      if (cell || row.length) { row.push(cell); rows.push(row); }
      return rows;
    };
    var fmt = function (n, sample) {
      var commas = function (x) { return String(Math.round(x)).replace(/\B(?=(\d{3})+(?!\d))/g, ","); };
      if (/IDR/i.test(sample)) return commas(n) + " IDR";
      return commas(n / 1000) + "K";
    };
    var apply = function (prices) {
      pxEls.forEach(function (el) {
        var v = prices[norm(el.getAttribute("data-price"))];
        if (!v) return;
        var div = parseInt(el.getAttribute("data-div"), 10) || 1;
        el.textContent = fmt(v / div, el.textContent);
      });
    };
    var cached = null;
    try { cached = JSON.parse(sessionStorage.getItem("rt-prices") || "null"); } catch (e) {}
    if (cached && Date.now() - cached.t < 10 * 60 * 1000) apply(cached.p);
    else if (window.fetch) {
      fetch(SHEET).then(function (r) { return r.ok ? r.text() : Promise.reject(); }).then(function (text) {
        var prices = {};
        parseCsv(text).slice(1).forEach(function (r) {
          var n = parseInt(String(r[1] || "").replace(/[^\d]/g, ""), 10);
          if (r[0] && n > 0) prices[norm(r[0])] = n;
        });
        apply(prices);
        try { sessionStorage.setItem("rt-prices", JSON.stringify({ t: Date.now(), p: prices })); } catch (e) {}
      }).catch(function () {});
    }
  }

  /* --- 5. lightbox --- */
  var box = document.getElementById("lightbox");
  if (!box) return;
  var big = box.querySelector("img");
  var close = box.querySelector(".x");
  var items = [].slice.call(document.querySelectorAll("a[data-lb], .gal a"));
  var idx = -1;

  function show(i) {
    if (!items.length) return;
    idx = (i + items.length) % items.length;
    big.src = items[idx].getAttribute("href");
    big.alt = items[idx].querySelector("img") ? items[idx].querySelector("img").alt : "";
    box.classList.add("on");
    document.body.style.overflow = "hidden";
  }
  function hide() {
    box.classList.remove("on");
    big.src = "";
    document.body.style.overflow = "";
  }
  items.forEach(function (a, i) {
    a.addEventListener("click", function (e) {
      if (window.innerWidth < 560 && !("ontouchstart" in window)) return; /* laisser le clic direct sur petit ecran */
      e.preventDefault();
      show(i);
    });
  });
  box.addEventListener("click", function (e) {
    if (e.target === box || e.target === close) hide();
  });
  document.addEventListener("keydown", function (e) {
    if (!box.classList.contains("on")) return;
    if (e.key === "Escape") hide();
    if (e.key === "ArrowRight") show(idx + 1);
    if (e.key === "ArrowLeft") show(idx - 1);
  });
})();

/* 7. Les racines de l'arbre des chambres : elles partent du bas du tronc et viennent
   encadrer les cartes des chambres. Dessinees a la taille reelle de la page (SVG),
   redessinees quand la largeur change, et elles « poussent » quand on arrive dessus. */
(function () {
  var zone = document.querySelector(".rooted");
  if (!zone) return;
  var svg = zone.querySelector("svg.roots"), tree = zone.querySelector(".tree-wrap"),
      grid = zone.querySelector(".grid");
  if (!svg || !tree || !grid) return;
  var NS = "http://www.w3.org/2000/svg";

  function rnd(seed) { return function () { seed = (seed * 16807) % 2147483647; return (seed - 1) / 2147483646; }; }
  // une ligne guide (points de controle) -> une racine effilee, legerement tremblee, comme a l'encre
  function root(pts, w0, w1, seed, wob) {
    var r = rnd(seed), P = [], i, k;
    for (i = 0; i < pts.length - 1; i++) {          // Catmull-Rom echantillonne
      var p0 = pts[Math.max(i - 1, 0)], p1 = pts[i], p2 = pts[i + 1], p3 = pts[Math.min(i + 2, pts.length - 1)];
      for (k = 0; k < 14; k++) {
        var t = k / 14, t2 = t * t, t3 = t2 * t;
        P.push([
          .5 * (2 * p1[0] + (-p0[0] + p2[0]) * t + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3),
          .5 * (2 * p1[1] + (-p0[1] + p2[1]) * t + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)]);
      }
    }
    P.push(pts[pts.length - 1]);
    var n = P.length, L = [], R = [], ph = r() * 6, ph2 = r() * 6;
    for (i = 0; i < n; i++) {
      var a = P[Math.max(i - 1, 0)], b = P[Math.min(i + 1, n - 1)];
      var dx = b[0] - a[0], dy = b[1] - a[1], d = Math.hypot(dx, dy) || 1, nx = -dy / d, ny = dx / d;
      var u = i / (n - 1), w = (w0 + (w1 - w0) * Math.pow(u, .7)) / 2;
      w *= 1 + .18 * Math.sin(u * 23 + ph);                       // epaisseur irreguliere
      var off = (wob || 0) * Math.sin(u * 9 + ph2) * Math.sin(u * Math.PI);  // petite ondulation
      var cx = P[i][0] + nx * off, cy = P[i][1] + ny * off;
      L.push([cx + nx * w, cy + ny * w]); R.push([cx - nx * w, cy - ny * w]);
    }
    var all = L.concat(R.reverse()), s = "M" + all[0][0].toFixed(1) + " " + all[0][1].toFixed(1);
    for (i = 1; i < all.length; i++) s += "L" + all[i][0].toFixed(1) + " " + all[i][1].toFixed(1);
    var p = document.createElementNS(NS, "path"); p.setAttribute("d", s + "Z");
    svg.appendChild(p);
  }

  function draw() {
    while (svg.firstChild) svg.removeChild(svg.firstChild);
    var Z = zone.getBoundingClientRect(), T = tree.getBoundingClientRect(), G = grid.getBoundingClientRect();
    var W = Z.width, H = Z.height;
    svg.setAttribute("viewBox", "0 0 " + W + " " + H);
    svg.setAttribute("width", W); svg.setAttribute("height", H);
    var s = T.width / 1200, wide = W > 700;
    function tp(x, y) { return [T.left - Z.left + x * s, T.top - Z.top + y * s]; }   // point du dessin d'arbre (1200 x 1428)
    var vw = document.documentElement.clientWidth;
    var gl = G.left - Z.left, gr = G.right - Z.left, gt = G.top - Z.top, gb = G.bottom - Z.top;
    var padL = Math.max(3, Math.min(24, G.left - 7)), padR = Math.max(3, Math.min(24, vw - G.right - 7));
    var L = gl - padL, R = gr + padR, B = gb + Math.min(26, padL + 8), top = gt - (wide ? 30 : 18);
    var m = Math.max(1.6, 2.6 * s * 1.6), big = Math.max(6, 19 * s), mid = Math.max(4, 12 * s);
    var base = tp(0, 1275)[1], cxm = (gl + gr) / 2;

    var r0 = rnd(5);
    function jit(pts, amp) { return pts.map(function (p, i) { return (i < 2 || i === pts.length - 1) ? p : [p[0] + (r0() - .5) * amp, p[1] + (r0() - .5) * amp]; }); }
    // une boucle qui s'enroule (vrille d'encre), sens +1 / -1
    function curl(cx, cy, rad, from, dir) {
      var out = [];
      for (var k = 0; k <= 10; k++) { var a = from + dir * k * .62, rr = rad * (1 - k / 13); out.push([cx + Math.cos(a) * rr, cy + Math.sin(a) * rr]); }
      return out;
    }
    var midY = gt + (gb - gt) * .5, bulge = wide ? Math.min(14, padL * .6) : 0;

    // 1. grandes racines laterales : du tronc jusqu'aux bords, puis tout autour des cartes
    root([tp(219, 1263), tp(196, 1288)].concat(jit([[L + (tp(196, 0)[0] - L) * .5, base + (top - base) * .55],
          [L + 6, top + 60], [L - bulge, gt + (gb - gt) * .28], [L + 3, midY], [L - bulge * .7, gt + (gb - gt) * .75],
          [L + 10, B - 20], [L + 70, B + 6], [cxm - 120, B - 2], [cxm - 50, B + 5]], wide ? 18 : 6)).concat(
          curl(cxm - 40, B - 9, 14, Math.PI / 2, -1).slice(1, 7)), big, m * .7, 7, 4);
    root([tp(862, 1241), tp(890, 1262)].concat(jit([[R - (R - tp(890, 0)[0]) * .45, base + (top - base) * .58],
          [R - 6, top + 64], [R + bulge, gt + (gb - gt) * .3], [R - 3, midY + 10], [R + bulge * .7, gt + (gb - gt) * .72],
          [R - 10, B - 22], [R - 70, B + 5], [cxm + 120, B + 2], [cxm + 50, B + 5]], wide ? 18 : 6)).concat(
          curl(cxm + 40, B - 9, 14, Math.PI / 2, 1).slice(1, 7)), big, m * .7, 11, 4);
    // 2. racines secondaires : elles descendent en biais et s'enroulent au-dessus des cartes
    var lx = gl + (cxm - gl) * .3, rx = gr - (gr - cxm) * .3, cy0 = top - 26;
    root([tp(388, 1276), tp(380, 1300), [lx + 70, (base + cy0) / 2 + 10], [lx + 20, cy0 + 12]].concat(curl(lx, cy0, 20, 0.2, -1).slice(1)), mid, 1, 3, 3);
    root([tp(796, 1240), tp(806, 1270), [rx - 70, (base + cy0) / 2 + 14], [rx - 20, cy0 + 12]].concat(curl(rx, cy0, 20, Math.PI - 0.2, 1).slice(1)), mid, 1, 5, 3);
    // 3. la racine pivot descend en serpentant
    var px = tp(560, 0)[0];
    root([tp(559, 1268), tp(562, 1300), [px + 14, base + (top - base) * .4], [px - 12, base + (top - base) * .7], [px + 6, top - 34]], mid * .8, 1, 13, 4);
    // 3b. petites fourches qui partent des grandes racines vers l'exterieur
    [[L, gt + (gb - gt) * .2, -1], [L, gt + (gb - gt) * .62, -1], [R, gt + (gb - gt) * .4, 1], [R, gt + (gb - gt) * .85, 1]].forEach(function (f, q) {
      var o = Math.min(wide ? 30 : 10, (f[2] < 0 ? padL : padR) + 6);
      root([[f[0], f[1]], [f[0] + f[2] * o * .5, f[1] + 16], [f[0] + f[2] * o, f[1] + 40 + q * 4]], Math.max(2.5, 6 * s), .6, 50 + q, 1);
    });

    // 4. radicelles dans les allees entre les rangees de cartes
    var tops = [];
    grid.querySelectorAll(".card").forEach(function (c) {
      var t = Math.round(c.getBoundingClientRect().top - Z.top);
      if (tops.indexOf(t) < 0) tops.push(t);
    });
    tops.sort(function (a, b) { return a - b; });
    var r = rnd(17);
    for (var i = 1; i < tops.length; i++) {
      var y = tops[i] - Math.max(6, (tops[i] - tops[i - 1]) > 0 ? 9 : 9), reach = (gr - gl) * (.16 + r() * .2);
      if (i % 2) root([[L, y - 34], [L + 14, y - 6], [gl + reach * .5, y + 2]].concat(curl(gl + reach, y - 5, 7, Math.PI / 2, -1).slice(1, 8)), mid * .6, .8, 20 + i, 2);
      else root([[R, y - 34], [R - 14, y - 6], [gr - reach * .5, y + 2]].concat(curl(gr - reach, y - 5, 7, Math.PI / 2, 1).slice(1, 8)), mid * .6, .8, 30 + i, 2);
    }
    // 5. quelques poils de racine sous le cadre
    for (var j = 0; j < (wide ? 7 : 4); j++) {
      var x = L + 50 + r() * (R - L - 100), y0 = B + 1;
      root([[x, y0], [x + (r() - .5) * 20, y0 + 10 + r() * 10], [x + (r() - .5) * 30, y0 + 18 + r() * 22]], Math.max(2, 4 * s), .6, 40 + j, 1);
    }
  }

  var last = 0, timer;
  function redraw() { var w = zone.offsetWidth; if (w === last && svg.firstChild) return; last = w; draw(); }
  redraw();
  window.addEventListener("load", function () { last = 0; redraw(); });
  window.addEventListener("resize", function () { clearTimeout(timer); timer = setTimeout(redraw, 150); });
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(function () { last = 0; redraw(); });

  // elles poussent quand on les voit
  if ("IntersectionObserver" in window && !(window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches)) {
    zone.classList.add("roots-wait");
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) { if (e.isIntersecting) { zone.classList.add("roots-grow"); io.disconnect(); } });
    }, { rootMargin: "0px 0px -25% 0px" });
    io.observe(grid);
  }
})();
