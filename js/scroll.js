/**
 * Native scroll — smooth anchor navigation + hash support.
 */
(function () {
  "use strict";

  function prefersReducedMotion() {
    return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  }

  function scrollToSection(id) {
    const el = document.getElementById(id);
    if (!el) return;
    el.scrollIntoView({ behavior: prefersReducedMotion() ? "auto" : "smooth", block: "start" });
  }

  function init() {
    document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
      anchor.addEventListener("click", (event) => {
        const id = anchor.getAttribute("href")?.slice(1);
        if (!id || !document.getElementById(id)) return;
        event.preventDefault();
        scrollToSection(id);
        history.replaceState(null, "", `#${id}`);
      });
    });

    const hash = window.location.hash.slice(1);
    if (hash && document.getElementById(hash)) {
      window.setTimeout(() => scrollToSection(hash), 100);
    }

    initSectionStatus();
  }

  function initSectionStatus() {
    const stage = document.getElementById("status-stage");
    if (!stage || typeof IntersectionObserver === "undefined") return;

    const sections = document.querySelectorAll(".section[data-title]");
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const title = entry.target.dataset.title || entry.target.id;
            stage.textContent = title.toLowerCase();
          }
        });
      },
      { threshold: 0.5 }
    );
    sections.forEach((s) => observer.observe(s));
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
