/**
 * Anima site — scrolljacking with accessibility fallbacks.
 * Disabled when prefers-reduced-motion or user chooses standard scroll.
 */

(function () {
  "use strict";

  const STORAGE_KEY = "anima-scroll-mode";
  const sections = () => Array.from(document.querySelectorAll(".scroll-stage .section"));
  const progress = document.getElementById("scroll-progress");
  const dotsContainer = document.getElementById("section-dots");
  const toggleBtn = document.getElementById("scroll-toggle");

  let index = 0;
  let locked = false;
  let jackEnabled = false;

  function prefersReducedMotion() {
    return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  }

  function readMode() {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved === "standard") return false;
    if (saved === "sections") return true;
    return !prefersReducedMotion();
  }

  function writeMode(enabled) {
    localStorage.setItem(STORAGE_KEY, enabled ? "sections" : "standard");
  }

  function buildDots() {
    if (!dotsContainer) return;
    dotsContainer.innerHTML = "";
    sections().forEach((section, i) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.setAttribute("aria-label", `Go to section ${i + 1}: ${section.dataset.title || section.id}`);
      btn.addEventListener("click", () => goTo(i));
      dotsContainer.appendChild(btn);
    });
  }

  function updateUI() {
    const list = sections();
    list.forEach((el, i) => {
      el.classList.toggle("is-active", jackEnabled && i === index);
      el.setAttribute("aria-hidden", jackEnabled && i !== index ? "true" : "false");
    });
    if (progress && list.length) {
      progress.style.width = `${((index + 1) / list.length) * 100}%`;
      progress.setAttribute("aria-valuenow", String(index + 1));
    }
    if (dotsContainer) {
      dotsContainer.querySelectorAll("button").forEach((btn, i) => {
        btn.classList.toggle("is-active", i === index);
      });
    }
    if (toggleBtn) {
      toggleBtn.textContent = jackEnabled ? "Standard scroll" : "Section scroll";
      toggleBtn.setAttribute("aria-pressed", jackEnabled ? "true" : "false");
    }
  }

  function goTo(i) {
    const list = sections();
    if (!list.length) return;
    index = Math.max(0, Math.min(list.length - 1, i));
    updateUI();
    if (!jackEnabled) {
      list[index].scrollIntoView({ behavior: prefersReducedMotion() ? "auto" : "smooth" });
    }
  }

  function next() {
    goTo(index + 1);
  }

  function prev() {
    goTo(index - 1);
  }

  function setJack(enabled) {
    jackEnabled = enabled;
    document.body.classList.toggle("scrolljack-active", enabled);
    document.documentElement.classList.toggle("reduced-motion", prefersReducedMotion());
    writeMode(enabled);
    updateUI();
    if (enabled) {
      listFocusable();
    }
  }

  function listFocusable() {
    const active = sections()[index];
    if (!active) return;
    const focusable = active.querySelector("a, button, input, textarea, select, [tabindex]:not([tabindex='-1'])");
    if (focusable && document.activeElement === document.body) {
      /* don't steal focus on every section change */
    }
  }

  function onWheel(event) {
    if (!jackEnabled || locked) return;
    if (Math.abs(event.deltaY) < 8) return;
    event.preventDefault();
    locked = true;
    if (event.deltaY > 0) next();
    else prev();
    window.setTimeout(() => {
      locked = false;
    }, 650);
  }

  function onKeyDown(event) {
    if (!jackEnabled) return;
    if (event.key === "ArrowDown" || event.key === "PageDown") {
      event.preventDefault();
      next();
    } else if (event.key === "ArrowUp" || event.key === "PageUp") {
      event.preventDefault();
      prev();
    } else if (event.key === "Home") {
      event.preventDefault();
      goTo(0);
    } else if (event.key === "End") {
      event.preventDefault();
      goTo(sections().length - 1);
    }
  }

  let touchY = 0;
  function onTouchStart(event) {
    touchY = event.touches[0].clientY;
  }

  function onTouchEnd(event) {
    if (!jackEnabled || locked) return;
    const delta = touchY - event.changedTouches[0].clientY;
    if (Math.abs(delta) < 40) return;
    locked = true;
    if (delta > 0) next();
    else prev();
    window.setTimeout(() => {
      locked = false;
    }, 650);
  }

  function initObserver() {
    if (jackEnabled) return;
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const i = sections().indexOf(entry.target);
            if (i >= 0) {
              index = i;
              if (progress) {
                progress.style.width = `${((index + 1) / sections().length) * 100}%`;
              }
            }
          }
        });
      },
      { threshold: 0.45 }
    );
    sections().forEach((s) => observer.observe(s));
  }

  function init() {
    buildDots();
    setJack(readMode());
    if (!jackEnabled) initObserver();

    document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
      anchor.addEventListener("click", (event) => {
        const id = anchor.getAttribute("href")?.slice(1);
        if (!id) return;
        const i = sections().findIndex((s) => s.id === id);
        if (i >= 0) {
          event.preventDefault();
          goTo(i);
        }
      });
    });

    const hash = window.location.hash.slice(1);
    if (hash) {
      const i = sections().findIndex((s) => s.id === hash);
      if (i >= 0) goTo(i);
    }

    window.addEventListener("wheel", onWheel, { passive: false });
    window.addEventListener("keydown", onKeyDown);
    window.addEventListener("touchstart", onTouchStart, { passive: true });
    window.addEventListener("touchend", onTouchEnd, { passive: true });

    if (toggleBtn) {
      toggleBtn.addEventListener("click", () => {
        setJack(!jackEnabled);
        if (!jackEnabled) initObserver();
      });
    }

    window.matchMedia("(prefers-reduced-motion: reduce)").addEventListener("change", () => {
      if (prefersReducedMotion() && jackEnabled) setJack(false);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
