/**
 * Cookie consent — GDPR / ePrivacy aligned.
 * No non-essential cookies until explicit opt-in. No third-party scripts loaded by default.
 */

(function () {
  "use strict";

  const STORAGE_KEY = "anima-cookie-consent";
  const banner = document.getElementById("cookie-banner");

  function getConsent() {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY) || "null");
    } catch {
      return null;
    }
  }

  function setConsent(choice) {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({ choice, at: new Date().toISOString() })
    );
    if (banner) banner.classList.remove("is-visible");
    document.dispatchEvent(new CustomEvent("anima:consent", { detail: { choice } }));
  }

  function init() {
    if (!banner) return;
    const consent = getConsent();
    if (!consent) {
      banner.classList.add("is-visible");
    }

    banner.querySelector("[data-consent=accept]")?.addEventListener("click", () => setConsent("all"));
    banner.querySelector("[data-consent=essential]")?.addEventListener("click", () => setConsent("essential"));
    banner.querySelector("[data-consent=settings]")?.addEventListener("click", () => {
      window.location.href = "cookies.html";
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
