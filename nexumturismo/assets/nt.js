/* NexumTurismo shared behaviour: language (ES/EN, remembered across pages),
   header dropdowns, mobile menu, generated landscape scenes and the
   contact/trip request form. Pages listen for the "nt:lang" event to
   re-render their own dynamic parts. */
(function () {
  "use strict";
  var KEY = "nxt_lang";
  var NT = window.NT = window.NT || {};

  /* ---------- language ---------- */
  function store(l) { try { localStorage.setItem(KEY, l); } catch (e) {} }
  function read() { try { return localStorage.getItem(KEY); } catch (e) { return null; } }
  NT.lang = "es";
  NT.t = function (es, en) { return NT.lang === "en" ? en : es; };
  NT.setLang = function (l) {
    NT.lang = l;
    document.documentElement.lang = l;
    var els = document.querySelectorAll("[data-en]");
    for (var i = 0; i < els.length; i++) {
      var el = els[i];
      if (el.dataset.es === undefined) el.dataset.es = el.tagName === "TITLE" ? el.textContent : el.innerHTML;
      var v = l === "en" ? el.dataset.en : el.dataset.es;
      if (el.tagName === "TITLE") { document.title = v; } else { el.innerHTML = v; }
    }
    var phs = document.querySelectorAll("[data-en-ph]");
    for (var j = 0; j < phs.length; j++) {
      var p = phs[j];
      if (p.dataset.esPh === undefined) p.dataset.esPh = p.getAttribute("placeholder") || "";
      p.setAttribute("placeholder", l === "en" ? p.dataset.enPh : p.dataset.esPh);
    }
    var btns = document.querySelectorAll(".lang button");
    for (var k = 0; k < btns.length; k++) btns[k].setAttribute("aria-pressed", String(btns[k].dataset.lang === l));
    store(l);
    document.dispatchEvent(new CustomEvent("nt:lang", { detail: l }));
  };
  document.addEventListener("click", function (e) {
    var b = e.target.closest && e.target.closest(".lang button");
    if (b) NT.setLang(b.dataset.lang);
  });

  /* ---------- header dropdowns ---------- */
  function closeAll(except) {
    var open = document.querySelectorAll('.dd-btn[aria-expanded="true"]');
    for (var i = 0; i < open.length; i++) if (open[i] !== except) open[i].setAttribute("aria-expanded", "false");
  }
  document.addEventListener("click", function (e) {
    var btn = e.target.closest && e.target.closest(".dd-btn");
    if (btn) {
      var on = btn.getAttribute("aria-expanded") === "true";
      closeAll(btn);
      btn.setAttribute("aria-expanded", String(!on));
      return;
    }
    if (!(e.target.closest && e.target.closest(".dd-menu"))) closeAll();
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
      var open = document.querySelector('.dd-btn[aria-expanded="true"]');
      if (open) { open.setAttribute("aria-expanded", "false"); open.focus(); }
    }
  });

  /* ---------- mobile menu ---------- */
  var burger = document.querySelector(".burger"), mnav = document.getElementById("mnav");
  if (burger && mnav) {
    burger.addEventListener("click", function () {
      var o = mnav.classList.toggle("open");
      burger.setAttribute("aria-expanded", String(o));
    });
    mnav.addEventListener("click", function (e) {
      if (e.target.closest("a")) { mnav.classList.remove("open"); burger.setAttribute("aria-expanded", "false"); }
    });
  }

  /* ---------- landscape scenes (no external images) ---------- */
  var PALETTES = {
    volcan: { sky: ["#F2C27A", "#E9A0A8"], hills: ["#3E7A5A", "#2C5E45", "#1F4634"], peak: true },
    nuboso: { sky: ["#C9D8D2", "#A9C0B8"], hills: ["#5E8C78", "#3F6F5B", "#2B5443"], mist: true },
    playa: { sky: ["#F5B865", "#E57B5A"], hills: ["#A08A4A", "#7A6B3A"], sea: "#2F7F98" },
    pacifico: { sky: ["#9FD0DA", "#F3D59A"], hills: ["#3E8A5E", "#2A6B48"], sea: "#2B8BA6" },
    caribe: { sky: ["#BFE3DA", "#8FCBC4"], hills: ["#2F8A62", "#216B4B"], sea: "#1C9AA0" },
    selva: { sky: ["#A9C9B6", "#7FAE95"], hills: ["#2D6B49", "#1E5238", "#143D29"], sea: "#25708A" },
    valle: { sky: ["#DCE6C8", "#B9CDA0"], hills: ["#6E9A57", "#4F7D3F", "#36602C"] },
    ciudad: { sky: ["#E7D3B8", "#C9B49A"], hills: ["#7C8A80", "#5D6B62"], city: true },
    rio: { sky: ["#BFDCE0", "#9CC7CB"], hills: ["#3C7F5C", "#28603F"], river: true },
    noche: { sky: ["#3A4A6B", "#1E2A44"], hills: ["#2A4A3A", "#1A3226"], moon: true }
  };
  NT.scene = function (kind, seed) {
    var r = PALETTES[kind] || PALETTES.valle, i = seed || 0, w = 320, h = 180, id = "g" + kind + i + Math.floor(Math.random() * 1e6);
    var s = '<svg viewBox="0 0 320 180" preserveAspectRatio="xMidYMid slice" aria-hidden="true" focusable="false">';
    s += '<defs><linearGradient id="' + id + '" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="' + r.sky[0] + '"/><stop offset="1" stop-color="' + r.sky[1] + '"/></linearGradient></defs>';
    s += '<rect width="' + w + '" height="' + h + '" fill="url(#' + id + ')"/>';
    s += '<circle cx="' + (60 + (i * 37) % 200) + '" cy="50" r="' + (r.moon ? 12 : 16) + '" fill="#FFF6DD" fill-opacity="' + (r.moon ? ".95" : ".85") + '"/>';
    if (r.peak) s += '<path d="M120 150 L185 48 L200 54 L250 150 Z" fill="#4A4F4A"/><path d="M176 62 L185 48 L200 54 L192 66 Z" fill="#E8E2D6"/>';
    if (r.city) { for (var c = 0; c < 9; c++) { var bh = 30 + ((c * 53 + i * 17) % 45); s += '<rect x="' + (30 + c * 30) + '" y="' + (150 - bh) + '" width="22" height="' + bh + '" fill="#8E8378" fill-opacity=".8"/>'; } }
    var base = r.sea ? 120 : 110;
    r.hills.forEach(function (col, j) {
      var y = base + j * 18, a = 8 + j * 6, f = 0.02 + j * 0.012, d = "M0 " + h + " L0 " + y;
      for (var x = 0; x <= w; x += 10) d += " L" + x + " " + (y + Math.sin(x * f + i + j) * a).toFixed(1);
      s += '<path d="' + d + " L" + w + " " + h + ' Z" fill="' + col + '"/>';
    });
    if (r.river) s += '<path d="M150 180 C160 160 140 150 170 138 C200 126 180 118 210 110" stroke="#7FD3D6" stroke-width="10" fill="none" stroke-linecap="round"/>';
    if (r.sea) s += '<rect x="0" y="152" width="320" height="28" fill="' + r.sea + '"/><path d="M0 156 Q40 151 80 156 T160 156 T240 156 T320 156" stroke="#FFFFFF" stroke-opacity=".5" fill="none"/>';
    if (r.mist) s += '<rect y="70" width="320" height="40" fill="#FFFFFF" fill-opacity=".35"/><rect y="118" width="320" height="22" fill="#FFFFFF" fill-opacity=".25"/>';
    return s + "</svg>";
  };
  NT.paintScenes = function (root) {
    var els = (root || document).querySelectorAll(".scene[data-scene]");
    for (var i = 0; i < els.length; i++) if (!els[i].firstChild) els[i].innerHTML = NT.scene(els[i].dataset.scene, +els[i].dataset.seed || i);
  };

  /* ---------- request form ---------- */
  function setupForm(form) {
    var done = form.querySelector(".done"), sum = form.querySelector("pre"), copy = form.querySelector(".copy");
    function labelFor(el) { var l = form.querySelector('label[for="' + el.id + '"]'); return l ? l.textContent.trim() : el.name; }
    function err(id, msg) { var e = form.querySelector('[data-err="' + id + '"]'); if (e) e.textContent = msg; }
    function build() {
      var lines = [NT.t("Solicitud de viaje · NexumTurismo", "Trip request · NexumTurismo")];
      var fields = form.querySelectorAll("input[name], select[name], textarea[name]");
      for (var i = 0; i < fields.length; i++) {
        var f = fields[i];
        if (f.type === "checkbox") continue;
        var v = f.tagName === "SELECT" ? f.options[f.selectedIndex].textContent : f.value.trim();
        lines.push(labelFor(f) + ": " + (v || "—"));
      }
      sum.textContent = lines.join("\n");
    }
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var name = form.querySelector('[name="name"]'), mail = form.querySelector('[name="email"]'), ok = form.querySelector('[name="consent"]');
      var good = true, first = null;
      if (!name.value.trim()) { err("name", NT.t("Escriba su nombre.", "Enter your name.")); good = false; first = first || name; } else err("name", "");
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(mail.value.trim())) { err("email", NT.t("Escriba un correo válido, como nombre@empresa.com.", "Enter a valid email, like name@company.com.")); good = false; first = first || mail; } else err("email", "");
      if (!ok.checked) { err("consent", NT.t("Marque la casilla para que podamos responderle.", "Check the box so we can reply to you.")); good = false; first = first || ok; } else err("consent", "");
      if (!good) { first.focus(); return; }
      build(); done.hidden = false; done.scrollIntoView({ block: "nearest", behavior: "smooth" });
    });
    if (copy) copy.addEventListener("click", function () {
      function sel() { var r = document.createRange(); r.selectNodeContents(sum); var s = window.getSelection(); s.removeAllRanges(); s.addRange(r); }
      var b = this;
      try {
        navigator.clipboard.writeText(sum.textContent).then(function () {
          var prev = b.innerHTML; b.textContent = NT.t("Copiado", "Copied");
          setTimeout(function () { b.innerHTML = prev; }, 1800);
        }, sel);
      } catch (x) { sel(); }
    });
    document.addEventListener("nt:lang", function () { if (!done.hidden) build(); });
    /* prefill from ?tour= / ?tipo= when the page is opened from a tour card */
    try {
      var q = new URLSearchParams(location.search), tour = q.get("tour"), tipo = q.get("tipo");
      var msg = form.querySelector('[name="msg"]'), type = form.querySelector('[name="type"]');
      if (tour && msg && !msg.value) msg.value = NT.t("Me interesa el tour: ", "I'm interested in the tour: ") + tour;
      if (tipo && type) type.value = tipo;
    } catch (x) {}
  }

  /* ---------- boot ---------- */
  function boot() {
    var start = read();
    if (start !== "en" && start !== "es") start = /^en/i.test(navigator.language || "") ? "en" : "es";
    NT.lang = start;
    NT.paintScenes();
    var forms = document.querySelectorAll("form.nt-form");
    for (var i = 0; i < forms.length; i++) setupForm(forms[i]);
    var yr = document.getElementById("yr"); if (yr) yr.textContent = new Date().getFullYear();
    NT.setLang(start);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot); else boot();
})();
