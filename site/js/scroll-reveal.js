/**
 * Scroll-driven section + bento reveals via ScrollTrigger.
 */
(function () {
  "use strict";

  function initProgress() {
    if (typeof gsap === "undefined" || typeof ScrollTrigger === "undefined") return;

    const progress = document.getElementById("scroll-progress");
    if (!progress) return;

    ScrollTrigger.create({
      trigger: document.body,
      start: "top top",
      end: "bottom bottom",
      onUpdate: (self) => {
        progress.style.width = `${self.progress * 100}%`;
      },
    });
  }

  function initReveals() {
    if (!window.AnimaMotion?.enabled || typeof gsap === "undefined" || typeof ScrollTrigger === "undefined") {
      return;
    }

    gsap.utils.toArray(".section").forEach((section) => {
      const inner = section.querySelector(".section-inner");
      if (!inner || section.id === "hero") return;

      inner.setAttribute("data-reveal", "");
      gsap.from(inner, {
        scrollTrigger: {
          trigger: section,
          start: "top 75%",
          once: true,
        },
        opacity: 0,
        scale: 0.96,
        y: 48,
        duration: 0.9,
        ease: window.AnimaGSAP?.smooth || "power3.out",
      });
    });

    gsap.utils.toArray(".bento-grid").forEach((grid) => {
      const cards = grid.querySelectorAll(".bento-card");
      if (!cards.length) return;
      gsap.from(cards, {
        scrollTrigger: {
          trigger: grid,
          start: "top 80%",
          once: true,
        },
        opacity: 0,
        y: 32,
        scale: 0.97,
        duration: 0.7,
        stagger: 0.1,
        ease: window.AnimaGSAP?.expo || "expo.out",
      });
    });
  }

  function init() {
    initProgress();
    initReveals();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => setTimeout(init, 80));
  } else {
    setTimeout(init, 80);
  }
})();
