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
  /* en quittant la page, on la remet dans son etat normal AVANT que le navigateur la garde en memoire :
     ainsi le bouton retour la retrouve telle quelle, sans flash d'animation */
  window.addEventListener("pagehide", function () {
    vortex.classList.remove("in", "out"); seed.classList.remove("spinning");
    body.classList.remove("spin-out", "spin-in"); root.classList.remove("rt-spin", "rt-arrive"); body.style.transformOrigin = "";
    [].slice.call(document.querySelectorAll(".opening")).forEach(function (x) { x.classList.remove("opening"); });
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

  /* --- 6b. carte du bar et de la cuisine, en lecture seule : onglet "Menu" du fichier relais public,
         rempli par la caisse (POS). Colonnes : Category | Item | Price | Web | Sort | Description.
         Si l'onglet n'existe pas ou ne repond pas, la section reste cachee et les prix de repli restent. --- */
  var menuBox = document.querySelector("[data-menu]"), posEls = [].slice.call(document.querySelectorAll(".px[data-pos]"));
  if ((menuBox || posEls.length) && window.fetch) {
    var MENU = "https://docs.google.com/spreadsheets/d/19A5y3XcOOgQ0mxiDxdueaXwKxcSGujh_5xpgT4QfocI/gviz/tq?tqx=out:csv&sheet=Menu";
    var csv = function (text) {
      var rows = [], row = [], cell = "", q = false;
      for (var i = 0; i < text.length; i++) {
        var c = text[i];
        if (q) { if (c === '"') { if (text[i + 1] === '"') { cell += '"'; i++; } else q = false; } else cell += c; }
        else if (c === '"') q = true; else if (c === ",") { row.push(cell); cell = ""; }
        else if (c === "\n") { row.push(cell); rows.push(row); row = []; cell = ""; } else if (c !== "\r") cell += c;
      }
      if (cell || row.length) { row.push(cell); rows.push(row); }
      return rows;
    };
    var key = function (k) { return String(k).toLowerCase().replace(/[^a-z0-9]/g, ""); };
    var kfmt = function (n) { return String(Math.round(n / 1000)).replace(/\B(?=(\d{3})+(?!\d))/g, ",") + "K"; };
    var esc2 = function (s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); };
    fetch(MENU).then(function (r) { return r.ok ? r.text() : Promise.reject(); }).then(function (text) {
      var rows = csv(text);
      var h = (rows[0] || []).map(key);
      var ci = h.indexOf("category"), ii = h.indexOf("item"), pi = h.indexOf("price"), wi = h.indexOf("web"), si = h.indexOf("sort"), di = h.indexOf("description");
      if (ci < 0 || ii < 0 || pi < 0) return;            /* pas (encore) d'onglet Menu : on ne touche a rien */
      var items = rows.slice(1).map(function (r) {
        return { cat: (r[ci] || "").trim(), name: (r[ii] || "").trim(), price: parseInt(String(r[pi] || "").replace(/[^\d]/g, ""), 10) || 0,
                 web: wi < 0 || !/^(no|non|0|false|n)$/i.test((r[wi] || "").trim()), sort: parseFloat(r[si]) || 0, desc: di < 0 ? "" : (r[di] || "").trim() };
      }).filter(function (x) { return x.name && x.price > 0; });
      var byName = {};
      items.forEach(function (x) { byName[key(x.name)] = x.price; });
      posEls.forEach(function (el) { var v = byName[key(el.getAttribute("data-pos"))]; if (v) el.textContent = kfmt(v); });
      if (!menuBox) return;
      var cats = [], groups = {};
      items.filter(function (x) { return x.web; }).sort(function (a, b) { return a.sort - b.sort; }).forEach(function (x) {
        if (!groups[x.cat]) { groups[x.cat] = []; cats.push(x.cat); }
        groups[x.cat].push(x);
      });
      if (!cats.length) return;
      menuBox.querySelector(".menu-cols").innerHTML = cats.map(function (c) {
        return '<div class="menu-cat"><h3>' + esc2(c || "Menu") + "</h3><ul>" + groups[c].map(function (x) {
          return '<li><span class="mi">' + esc2(x.name) + (x.desc ? "<small>" + esc2(x.desc) + "</small>" : "") +
                 '</span><span class="dots"></span><span class="px">' + kfmt(x.price) + "</span></li>";
        }).join("") + "</ul></div>";
      }).join("");
      menuBox.hidden = false;
    }).catch(function () {});
  }

  /* --- 3b. carrousel « coverflow » : les rubans de photos deviennent un manege arrondi en 3D.
         Photo du centre en grand, voisines inclinees de chaque cote ; il tourne tout seul, s'arrete
         sous la souris, la photo du centre suit le curseur ; clic sur une voisine = elle vient au centre,
         clic au centre = plein ecran. Glisser au doigt, fleches du clavier. Sans JS : le ruban simple. --- */
  [].slice.call(document.querySelectorAll(".strip[data-cflow]")).forEach(function (strip) {
    var links = [].slice.call(strip.children);
    if (links.length < 3) return;
    var reduce2 = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;
    var box = document.createElement("div");
    box.className = "cflow"; box.tabIndex = 0;
    box.setAttribute("role", "region"); box.setAttribute("aria-label", "Photo carousel, use the arrow keys");
    var track = document.createElement("div"); track.className = "cf-track";
    links.forEach(function (a) { a.classList.add("cf-item"); track.appendChild(a); });
    var prev = document.createElement("button"), next = document.createElement("button"), count = document.createElement("div");
    prev.className = "cf-nav cf-prev"; prev.setAttribute("aria-label", "Previous photo"); prev.innerHTML = '<svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true"><path d="M15 4 7 12l8 8" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>';
    next.className = "cf-nav cf-next"; next.setAttribute("aria-label", "Next photo"); next.innerHTML = '<svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true"><path d="M9 4l8 8-8 8" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>';
    count.className = "cf-count";
    box.appendChild(track); box.appendChild(prev); box.appendChild(next); box.appendChild(count);
    strip.parentNode.replaceChild(box, strip);
    var n = links.length, cur = 0, timer = null, tilt = 0;

    function layout() {
      var W = box.clientWidth, H = box.clientHeight, step = Math.min(W * .3, 330);
      links.forEach(function (a) {                                  /* une photo tres large ne deborde jamais */
        var im = a.firstChild, r = (+im.getAttribute("width") || 4) / (+im.getAttribute("height") || 3);
        a.style.height = Math.min(H * (W < 560 ? .76 : .78), W * .84 / r) + "px";
      });
      links.forEach(function (a, i) {
        var d = i - cur;
        if (d > n / 2) d -= n; if (d < -n / 2) d += n;
        var ad = Math.abs(d), img = a.firstChild;
        if (ad <= 3 && img.loading === "lazy") img.loading = "eager";
        var x = d * step - (d ? Math.sign(d) * Math.pow(ad, 1.3) * 18 : 0);
        var rot = d === 0 ? tilt : -Math.sign(d) * Math.min(ad * 24, 52);
        var sc = d === 0 ? 1 : Math.max(.55, 1 - ad * .16);
        a.style.transform = "translate(-50%, -50%) translateX(" + x + "px) translateZ(" + (-ad * 140) + "px) rotateY(" + rot + "deg) scale(" + sc + ")";
        a.style.opacity = ad > 3 ? 0 : 1 - ad * .18;
        a.style.zIndex = 10 - ad;
        a.style.pointerEvents = ad > 3 ? "none" : "";
        a.classList.toggle("cf-on", d === 0);
        a.setAttribute("aria-hidden", ad > 0 ? "true" : "false");
        a.tabIndex = d === 0 ? 0 : -1;
      });
      count.textContent = (cur + 1) + " / " + n;
    }
    function go(i) { cur = (i + n) % n; tilt = 0; layout(); }
    function play() { if (reduce2 || timer) return; timer = setInterval(function () { go(cur + 1); }, 3800); }
    function stop() { clearInterval(timer); timer = null; }

    prev.addEventListener("click", function () { go(cur - 1); });
    next.addEventListener("click", function () { go(cur + 1); });
    links.forEach(function (a, i) {
      a.addEventListener("click", function (e) {
        if (i !== cur) { e.preventDefault(); e.stopImmediatePropagation(); go(i); }
      }, true);
    });
    box.addEventListener("keydown", function (e) {
      if (e.key === "ArrowLeft") { go(cur - 1); e.preventDefault(); }
      if (e.key === "ArrowRight") { go(cur + 1); e.preventDefault(); }
    });
    box.addEventListener("mouseenter", stop);
    box.addEventListener("mouseleave", function () { tilt = 0; layout(); play(); });
    box.addEventListener("mousemove", function (e) {                 /* la photo du centre suit la souris */
      var r = box.getBoundingClientRect();
      tilt = ((e.clientX - r.left) / r.width - .5) * 16;
      var on = links[cur]; if (on) on.style.transform = on.style.transform.replace(/rotateY\([^)]*\)/, "rotateY(" + tilt + "deg)");
    });
    var sx = null, moved = false;                                     /* glisser au doigt ou a la souris */
    box.addEventListener("pointerdown", function (e) { sx = e.clientX; moved = false; stop(); });
    box.addEventListener("pointerup", function (e) {
      if (sx === null) return;
      var dx = e.clientX - sx; sx = null;
      if (Math.abs(dx) > 40) { moved = true; go(cur + (dx < 0 ? 1 : -1)); }
      if (e.pointerType !== "mouse") setTimeout(play, 4000);
    });
    box.addEventListener("click", function (e) { if (moved) { e.preventDefault(); e.stopPropagation(); moved = false; } }, true);
    window.addEventListener("resize", layout);
    if ("IntersectionObserver" in window) {
      new IntersectionObserver(function (es) { es.forEach(function (en) { if (en.isIntersecting) play(); else stop(); }); }).observe(box);
    } else play();
    layout();
  });

  /* --- 3c. reservation de bateau : le formulaire prepare le message WhatsApp (lien wa.me?text=, gratuit) --- */
  var waf = document.getElementById("book-boat");
  if (waf) {
    var d0 = waf.querySelector("[name=date]");
    if (d0) d0.min = new Date().toISOString().slice(0, 10);
    waf.addEventListener("submit", function (e) {
      e.preventDefault();
      var v = function (n) { var el = waf.querySelector("[name=" + n + "]"); return el ? el.value.trim() : ""; };
      var date = v("date");
      if (date) { var p = date.split("-"); date = p[2] + "/" + p[1] + "/" + p[0]; }
      var lines = [
        "Hi Rabbit Tree! " + (v("name") ? "This is " + v("name") + ". " : "") + "I would like to book a boat:",
        "- From: " + v("from"),
        "- To: " + v("to"),
        "- Date: " + (date || "not sure yet"),
        "- People: " + (v("people") || "1"),
        "- Ticket: " + v("trip"),
        "- Pick-up / drop-off: " + v("pick"),
        "- Preferred time: " + v("time")
      ];
      if (v("note")) lines.push("- Note: " + v("note"));
      lines.push("Thank you!");
      window.open(waf.getAttribute("data-wa") + "?text=" + encodeURIComponent(lines.join("\n")), "_blank", "noopener");
    });
  }

  [].slice.call(document.querySelectorAll('a[href^="https://wa.me/"]')).forEach(function (a) {
    if (a.href.indexOf("?") < 0) a.href += "?text=" + encodeURIComponent("Hi Rabbit Tree! I have a question: ");
  });

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
    /* l'arbre (Rooms) et la spirale (Gallery) sont tout en haut : leur nom saute 40 % moins haut */
    var low = /\/(rooms|gallery)\/?$/.test(cap.parentNode.getAttribute("href") || "") ? .6 : 1;
    cap.style.setProperty("--jy", -(340 + Math.random() * 220) * low + "px");
    cap.style.setProperty("--jx", jx + "px");
    cap.style.setProperty("--fx", jx * (1.6 + Math.random() * .8) + "px");
    cap.style.setProperty("--r1", side * (6 + Math.random() * 14) + "deg");
    cap.style.setProperty("--r2", side * (25 + Math.random() * 50) + "deg");
  });
});
