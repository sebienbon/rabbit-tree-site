/* The Rabbit Tree Hostel — interactions
   1. menu mobile   2. spirales de l'arbre   3. lightbox de la galerie */
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

  /* --- 2. spirales de l'arbre : un clic les ouvre, le logo reste dessous --- */
  [].slice.call(document.querySelectorAll(".disc")).forEach(function (d) {
    d.addEventListener("click", function (e) {
      e.preventDefault();
      e.stopPropagation();
      if (d.classList.contains("gone")) return;
      d.classList.add("gone");
      var kill = function () { if (d.parentNode) d.parentNode.removeChild(d); };
      d.addEventListener("animationend", kill, { once: true });
      setTimeout(kill, 1500); /* filet de securite si l'animation ne se declenche pas */
    });
  });

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

  /* --- 4. transition spirale quand on entre dans une chambre depuis l'arbre --- */
  var roomLinks = [].slice.call(document.querySelectorAll(".node a.hit"));
  if (roomLinks.length) {
    var logo = document.querySelector(".node img");
    var base = logo ? logo.getAttribute("src").replace(/[^/]*$/, "") : "images/";
    var wipe = document.createElement("div");
    wipe.id = "spiral-wipe";
    wipe.innerHTML = '<img src="' + base + 'spiral.webp" alt="">';
    document.body.appendChild(wipe);
    var wimg = wipe.querySelector("img");
    roomLinks.forEach(function (a) {
      a.addEventListener("click", function (e) {
        if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
        var href = a.getAttribute("href");
        if (!href) return;
        e.preventDefault();
        var r = a.getBoundingClientRect();
        wimg.style.left = (e.clientX || r.left + r.width / 2) + "px";
        wimg.style.top = (e.clientY || r.top + r.height / 2) + "px";
        wipe.classList.remove("go"); void wipe.offsetWidth; wipe.classList.add("go");
        setTimeout(function () { window.location.href = href; }, 560);
      });
    });
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
