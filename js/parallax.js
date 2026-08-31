/**
 * Scroll parallax — Y2K orbs, hero layers, section depth via ScrollTrigger.
 */
(function () {
  "use strict";

  function initOrbs() {
    if (!window.AnimaMotion?.enabled || typeof gsap === "undefined" || typeof ScrollTrigger === "undefined") {
      return;
    }

    document.querySelectorAll("[data-parallax]").forEach((el) => {
      const speed = parseFloat(el.dataset.parallax) || 0.2;
      gsap.to(el, {
        y: () => speed * 120,
        ease: "none",
        scrollTrigger: {
          trigger: document.body,
          start: "top top",
          end: "bottom bottom",
          scrub: 1.2,
        },
      });
    });
  }

  function initHeroParallax() {
    if (!window.AnimaMotion?.enabled || typeof gsap === "undefined" || typeof ScrollTrigger === "undefined") {
      return;
    }

    const hero = document.getElementById("hero");
    if (!hero) return;

    const copy = hero.querySelector(".hero-copy");
    const canvas = hero.querySelector(".canvas-wrap");

    if (copy) {
      gsap.to(copy, {
        y: -40,
        ease: "none",
        scrollTrigger: {
          trigger: hero,
          start: "top top",
          end: "bottom top",
          scrub: 1,
        },
      });
    }

    if (canvas) {
      gsap.to(canvas, {
        y: 60,
        scale: 0.95,
        ease: "none",
        scrollTrigger: {
          trigger: hero,
          start: "top top",
          end: "bottom top",
          scrub: 1,
        },
      });
    }
  }

  function initSectionDepth() {
    if (!window.AnimaMotion?.enabled || typeof gsap === "undefined" || typeof ScrollTrigger === "undefined") {
      return;
    }

    gsap.utils.toArray(".terminal-window").forEach((win, i) => {
      if (win.closest("#hero")) return;
      gsap.from(win, {
        scrollTrigger: {
          trigger: win,
          start: "top 85%",
          end: "top 40%",
          scrub: 1,
        },
        y: 30 + i * 5,
        ease: "none",
      });
    });
  }

  function initMouseParallax() {
    if (!window.AnimaMotion?.enabled || !window.matchMedia("(hover: hover)").matches) return;

    const root = document.querySelector(".parallax-root");
    if (!root) return;

    let targetX = 0;
    let targetY = 0;
    let currentX = 0;
    let currentY = 0;

    document.addEventListener(
      "pointermove",
      (e) => {
        targetX = (e.clientX / window.innerWidth - 0.5) * 24;
        targetY = (e.clientY / window.innerHeight - 0.5) * 24;
      },
      { passive: true }
    );

    function tick() {
      currentX += (targetX - currentX) * 0.06;
      currentY += (targetY - currentY) * 0.06;
      root.style.transform = `translate(${currentX}px, ${currentY}px)`;
      requestAnimationFrame(tick);
    }
    tick();
  }

  function init() {
    initOrbs();
    initHeroParallax();
    initSectionDepth();
    initMouseParallax();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => setTimeout(init, 100));
  } else {
    setTimeout(init, 100);
  }
})();
