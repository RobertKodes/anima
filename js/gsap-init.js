/**
 * GSAP + ScrollTrigger registration and shared easings.
 */
(function () {
  "use strict";

  function init() {
    if (typeof gsap === "undefined") return null;
    if (typeof ScrollTrigger !== "undefined") {
      gsap.registerPlugin(ScrollTrigger);
    }
    gsap.defaults({ ease: "power3.out" });
    window.AnimaGSAP = {
      smooth: "power3.out",
      expo: "expo.out",
      duration: { fast: 0.4, normal: 0.85, slow: 1.2 },
    };
    return gsap;
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
