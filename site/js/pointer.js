/**
 * Shared pointer position — rAF-throttled for bento + magnetic modules.
 */
(function () {
  "use strict";

  let x = 0;
  let y = 0;
  let pending = false;
  const listeners = new Set();

  function flush() {
    pending = false;
    listeners.forEach((fn) => fn(x, y));
  }

  document.addEventListener(
    "pointermove",
    (event) => {
      x = event.clientX;
      y = event.clientY;
      if (!pending) {
        pending = true;
        requestAnimationFrame(flush);
      }
    },
    { passive: true }
  );

  window.AnimaPointer = {
    get x() {
      return x;
    },
    get y() {
      return y;
    },
    subscribe(fn) {
      listeners.add(fn);
      return () => listeners.delete(fn);
    },
    localXY(element) {
      const rect = element.getBoundingClientRect();
      return {
        x: x - rect.left,
        y: y - rect.top,
        nx: rect.width ? (x - rect.left) / rect.width - 0.5 : 0,
        ny: rect.height ? (y - rect.top) / rect.height - 0.5 : 0,
        rect,
      };
    },
  };
})();
