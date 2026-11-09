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
    var done = function () {
      root.classList.remove("rt-arrive"); body.classList.remove("spin-in"); body.style.transformOrigin = "";
    };
    body.addEventListener("animationend", function (ev) { if (ev.target === body) done(); }, { once: true });
    /* on attend que la page soit dessinee (logo + polices) pour que le recul soit fluide */
    var ready = [];
    if (portal && portal.decode) ready.push(portal.decode().catch(function () {}));
    if (document.fonts && document.fonts.ready) ready.push(document.fonts.ready);
    Promise.race([Promise.all(ready), wait(700)]).then(function () {
      requestAnimationFrame(function () { requestAnimationFrame(function () {
        vortex.classList.remove("out"); void vortex.offsetWidth; vortex.classList.add("out");
        body.classList.add("spin-in");
        setTimeout(done, 1400);
      }); });
    });
  }

  /* la page suivante est chargee a l'avance (HTML + ses premieres images) des qu'on
     survole ou touche un dessin ; au clic, le petit tourbillon tourne tant qu'elle n'est pas prete. */
  var cache = {};
  function preload(href) {
    if (cache[href]) return cache[href];
    cache[href] = fetch(href, { credentials: "same-origin" }).then(function (res) { return res.text(); }).then(function (html) {
      var doc = new DOMParser().parseFromString(html, "text/html"), base = new URL(href, location.href);
      var imgs = [].slice.call(doc.querySelectorAll("[data-portal], main img:not([loading=lazy]), .trunk, .scene img"))
        .slice(0, 8).map(function (im) { return new URL(im.getAttribute("src"), base).href; });
      return Promise.all(imgs.map(function (src) {
        return new Promise(function (ok) {
          var i = new Image(); i.onload = i.onerror = function () { ok(); }; i.src = src;
          if (i.decode) i.decode().then(ok, ok);
        });
      }));
    }).catch(function () {});
    return cache[href];
  }
  function wait(ms) { return new Promise(function (ok) { setTimeout(ok, ms); }); }
  var seed = document.createElement("div");
  seed.id = "vortex-seed"; seed.setAttribute("aria-hidden", "true");
  seed.innerHTML = '<svg viewBox="0 0 100 100"><path d="' + spiralPath(0) + '" fill="none" stroke="#1c1a17" stroke-width="5" stroke-linecap="round"/></svg>';
  root.appendChild(seed);

  [].slice.call(document.querySelectorAll("a[data-vortex]")).forEach(function (a) {
    var href0 = a.getAttribute("href");
    if (!href0 || href0.charAt(0) === "#") return;
    ["pointerenter", "touchstart", "focus"].forEach(function (ev) {
      a.addEventListener(ev, function () { preload(a.href); }, { passive: true, once: true });
    });
    a.addEventListener("click", function (e) {
      if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey || e.button) return;
      e.preventDefault();
      if (a.classList.contains("opening")) return;
      var href = a.href;
      var r = a.getBoundingClientRect();
      var x = r.left + r.width / 2, y = r.top + r.height / 2;
      var go = function () { window.location.href = href; };
      if (reduce) { remember(x, y); go(); return; }
      /* 1er mouvement : le tourbillon du dessin tourne... jusqu'a ce que la page suivante soit prete */
      a.classList.add("opening");
      if (!a.querySelector(".swirl")) {
        seed.style.left = x + "px"; seed.style.top = y + "px";
        seed.style.width = seed.style.height = Math.max(44, Math.min(90, Math.min(r.width, r.height) * .6)) + "px";
        seed.classList.add("spinning");
      }
      Promise.all([wait(420), Promise.race([preload(href), wait(5000)])]).then(function () {
        requestAnimationFrame(function () {
          seed.classList.remove("spinning");
          /* 2e mouvement : le vortex part du dessin et grandit en tournant jusqu'a couvrir la page */
          place(x, y);
          vortex.classList.remove("out", "in"); void vortex.offsetWidth; vortex.classList.add("in");
          /* ... et toute la page s'enroule autour du dessin clique */
          body.style.transformOrigin = x + "px " + (y + window.pageYOffset) + "px";
          root.classList.add("rt-spin");
          body.classList.add("spin-out");
          remember(x, y);
          setTimeout(go, 680);
        });
      });
    });
  });
  /* retour arriere depuis la page suivante : ne pas rester sur un ecran couvert */
  window.addEventListener("pageshow", function (e) {
    if (e.persisted) {
      vortex.classList.remove("in", "out");
      body.classList.remove("spin-out"); root.classList.remove("rt-spin", "rt-arrive"); body.style.transformOrigin = "";
    }
    [].slice.call(document.querySelectorAll(".opening")).forEach(function (x) { x.classList.remove("opening"); });
    seed.classList.remove("spinning");
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

/* 7. Accueil : le saut du nom (hauteur, cote au hasard) et jusqu'ou il tombe d'un dessin quand on le survole (juste sous le bas de l'ecran) */
[].slice.call(document.querySelectorAll(".scene .spot .cap")).forEach(function (cap) {
  cap.parentNode.addEventListener("mouseenter", function () {
    var top = cap.parentNode.getBoundingClientRect().top + cap.offsetTop;
    cap.style.setProperty("--fall", Math.max(120, window.innerHeight - top + 60) + "px");
    /* hauteur, cote et rotation tires au hasard, dans des limites raisonnables */
    var side = Math.random() < .5 ? -1 : 1, jx = side * (50 + Math.random() * 130);
    cap.style.setProperty("--jy", -(340 + Math.random() * 220) + "px");
    cap.style.setProperty("--jx", jx + "px");
    cap.style.setProperty("--fx", jx * (1.6 + Math.random() * .8) + "px");
    cap.style.setProperty("--r1", side * (6 + Math.random() * 14) + "deg");
    cap.style.setProperty("--r2", side * (25 + Math.random() * 50) + "deg");
  });
});
