/**
 * Magnetic buttons — subtle pull toward cursor.
 */
(function () {
  "use strict";

  const RADIUS = 80;
  const STRENGTH = 0.35;

  function init() {
    if (!window.AnimaMotion?.enabled || typeof gsap === "undefined") return;
    if (!window.matchMedia("(hover: hover)").matches) return;

    document.querySelectorAll("[data-magnetic]").forEach((btn) => {
      let inner = btn.querySelector(".magnetic-inner");
      if (!inner) {
        inner = document.createElement("span");
        inner.className = "magnetic-inner";
        while (btn.firstChild) inner.appendChild(btn.firstChild);
        btn.appendChild(inner);
      }

      const xTo = gsap.quickTo(inner, "x", { duration: 0.45, ease: "power3.out" });
      const yTo = gsap.quickTo(inner, "y", { duration: 0.45, ease: "power3.out" });

      btn.addEventListener("pointerenter", () => {
        inner.style.willChange = "transform";
      });

      btn.addEventListener("pointermove", (event) => {
        const rect = btn.getBoundingClientRect();
        const cx = rect.left + rect.width / 2;
        const cy = rect.top + rect.height / 2;
        const dx = event.clientX - cx;
        const dy = event.clientY - cy;
        const dist = Math.hypot(dx, dy);
        if (dist > RADIUS) {
          xTo(0);
          yTo(0);
          return;
        }
        const pull = (1 - dist / RADIUS) * STRENGTH;
        xTo(dx * pull);
        yTo(dy * pull);
      });

      btn.addEventListener("pointerleave", () => {
        xTo(0);
        yTo(0);
        inner.style.willChange = "auto";
      });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
