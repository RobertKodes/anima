/**
 * Bento cards — 3D tilt + cursor-following glow.
 */
(function () {
  "use strict";

  const MAX_TILT = 8;

  function init() {
    if (!window.matchMedia("(hover: hover)").matches) return;

    const cards = document.querySelectorAll("[data-bento-tilt]");
    if (!cards.length) return;

    const canTilt = window.AnimaMotion?.enabled && typeof gsap !== "undefined";

    cards.forEach((card) => {
      const glow = card.querySelector(".bento-glow");
      let rotX = canTilt ? gsap.quickTo(card, "rotateX", { duration: 0.5, ease: "power2.out" }) : null;
      let rotY = canTilt ? gsap.quickTo(card, "rotateY", { duration: 0.5, ease: "power2.out" }) : null;

      card.addEventListener("pointerenter", () => {
        card.classList.add("is-hover");
        if (canTilt) {
          card.style.willChange = "transform";
          gsap.set(card, { transformPerspective: 900 });
        }
      });

      card.addEventListener("pointermove", (event) => {
        const rect = card.getBoundingClientRect();
        const nx = (event.clientX - rect.left) / rect.width - 0.5;
        const ny = (event.clientY - rect.top) / rect.height - 0.5;

        if (glow) {
          const mx = ((event.clientX - rect.left) / rect.width) * 100;
          const my = ((event.clientY - rect.top) / rect.height) * 100;
          glow.style.setProperty("--mx", `${mx}%`);
          glow.style.setProperty("--my", `${my}%`);
        }

        if (rotX && rotY) {
          rotY(nx * MAX_TILT);
          rotX(-ny * MAX_TILT);
        }
      });

      card.addEventListener("pointerleave", () => {
        card.classList.remove("is-hover");
        if (rotX && rotY) {
          rotX(0);
          rotY(0);
          card.style.willChange = "auto";
        }
      });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
