/**
 * Kinetic typography — word reveal on load + optional scroll headlines.
 */
(function () {
  "use strict";

  function splitWords(el) {
    if (el.dataset.kineticSplit === "done") return el.querySelectorAll(".kinetic-word");
    const lines = el.querySelectorAll(".kinetic-line");
    const words = [];
    lines.forEach((line) => {
      if (line.querySelector(".kinetic-word")) {
        line.querySelectorAll(".kinetic-word").forEach((w) => words.push(w));
        return;
      }
      const text = line.textContent.trim();
      line.textContent = "";
      text.split(/(\s+)/).forEach((part) => {
        if (!part.trim()) return;
        const span = document.createElement("span");
        span.className = "kinetic-word";
        span.textContent = part;
        line.appendChild(span);
        words.push(span);
      });
    });
    el.dataset.kineticSplit = "done";
    return words;
  }

  function initHero() {
    if (!window.AnimaMotion?.enabled || typeof gsap === "undefined") return;

    const title = document.querySelector("[data-kinetic]");
    if (!title) return;

    const words = splitWords(title);
    gsap.set(words, { yPercent: 110, opacity: 0 });

    const hero = document.getElementById("hero");
    const tag = hero?.querySelector(".section-tag");
    const lead = hero?.querySelector(".lead");
    const ctas = hero?.querySelector(".cta-row");
    const canvas = hero?.querySelector(".canvas-wrap");

    const tl = gsap.timeline({ defaults: { ease: window.AnimaGSAP?.expo || "expo.out" } });

    if (tag) tl.from(tag, { opacity: 0, y: 20, duration: 0.5 }, 0.1);
    tl.to(words, { yPercent: 0, opacity: 1, duration: 0.9, stagger: 0.06 }, 0.2);
    if (lead) tl.from(lead, { opacity: 0, y: 24, duration: 0.7 }, "-=0.4");
    if (ctas) tl.from(ctas.children, { opacity: 0, y: 20, duration: 0.6, stagger: 0.08 }, "-=0.35");
    if (canvas) tl.from(canvas, { opacity: 0, scale: 0.94, duration: 1 }, "-=0.5");
  }

  function initScrollHeadlines() {
    if (!window.AnimaMotion?.enabled || typeof gsap === "undefined" || typeof ScrollTrigger === "undefined") {
      return;
    }

    document.querySelectorAll("h2[id]").forEach((heading) => {
      if (heading.closest("#hero")) return;
      const words = [];
      const text = heading.textContent.trim();
      heading.textContent = "";
      const line = document.createElement("span");
      line.className = "kinetic-line";
      text.split(/(\s+)/).forEach((part) => {
        if (!part.trim()) return;
        const span = document.createElement("span");
        span.className = "kinetic-word";
        span.textContent = part;
        line.appendChild(span);
        words.push(span);
      });
      heading.appendChild(line);
      gsap.set(words, { yPercent: 100, opacity: 0 });
      gsap.to(words, {
        scrollTrigger: { trigger: heading, start: "top 82%", once: true },
        yPercent: 0,
        opacity: 1,
        duration: 0.75,
        stagger: 0.04,
        ease: window.AnimaGSAP?.expo || "expo.out",
      });
    });
  }

  function init() {
    initHero();
    initScrollHeadlines();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => setTimeout(init, 50));
  } else {
    setTimeout(init, 50);
  }
})();
