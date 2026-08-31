/**
 * Motion preferences — gates all GSAP / tilt / magnetic effects.
 */
(function () {
  "use strict";

  function prefersReducedMotion() {
    return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  }

  function apply() {
    const enabled = !prefersReducedMotion();
    document.documentElement.classList.toggle("no-motion", !enabled);
    return enabled;
  }

  window.AnimaMotion = {
    enabled: apply(),
    prefersReducedMotion,
  };

  window.matchMedia("(prefers-reduced-motion: reduce)").addEventListener("change", () => {
    window.AnimaMotion.enabled = apply();
  });
})();
