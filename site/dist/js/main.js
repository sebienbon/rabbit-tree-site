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
    '<path d="' + spiralPath(0) + '" fill="none" stroke="#3b382b" stroke-opacity=".55" stroke-width="3.2" stroke-linecap="round"/>' +
    '<path d="' + spiralPath(Math.PI) + '" fill="none" stroke="#3b382b" stroke-opacity=".2" stroke-width="2" stroke-linecap="round"/></svg>';
  document.body.appendChild(vortex);

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
      place(window.innerWidth / 2, window.innerHeight / 2);
      vortex.classList.add("out");
      vortex.addEventListener("animationend", function () { vortex.classList.remove("out"); }, { once: true });
    }
  } catch (e) {}

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
        remember(x, y);
        setTimeout(go, 680);
      }, delay);
    });
  });
  /* retour arriere depuis la page suivante : ne pas rester sur un ecran couvert */
  window.addEventListener("pageshow", function (e) {
    if (e.persisted) { vortex.classList.remove("in", "out"); }
    [].slice.call(document.querySelectorAll(".opening")).forEach(function (x) { x.classList.remove("opening"); });
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
