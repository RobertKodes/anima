# Anima — presentation website

Dark, high-tech landing page for [Anima](https://github.com/RobertKodes/anima). Static HTML/CSS/JS — no build step.

**Live URL:** https://robertkodes.github.io/anima/

## Features

- Dark-first design — slate backgrounds, amber accent glow, dot-matrix grid
- **GSAP + ScrollTrigger** — cinematic section reveals, kinetic typography, scroll progress
- **Bento grids** — 3D tilt + cursor glow on Memory and Experiences sections
- **Magnetic buttons** — primary CTAs pull toward cursor (desktop hover only)
- **Three.js** 3D hero — wireframe being with orbiting memory nodes
- Native scroll (scrolljacking removed in Phase 1)
- Legal pages: Privacy (GDPR/CCPA), Terms, Cookies, Accessibility (WCAG 2.1 AA), Imprint

## Local preview

```bash
cd site
python -m http.server 8080
# open http://127.0.0.1:8080
```

## Deploy to GitHub Pages

Push to `master` with changes under `site/` — workflow `.github/workflows/pages.yml` deploys automatically.

## Structure

```
site/
  index.html              Landing (hero + bento sections)
  css/
    tokens.css            Design tokens
    effects.css           Dot grid, border-beam, bento glow
    style.css             Layout + components
  js/
    motion-prefs.js       prefers-reduced-motion gate
    gsap-init.js          GSAP + ScrollTrigger setup
    pointer.js            Shared rAF pointer tracker
    kinetic-headlines.js  Hero + h2 word reveals
    magnetic-buttons.js   Magnetic CTA effect
    bento-cards.js        3D tilt + cursor glow
    scroll-reveal.js      ScrollTrigger section/bento reveals
    scroll.js             Smooth anchor navigation
    scene3d.js            Three.js hero
    consent.js            Cookie banner
```

## Third parties

- Google Fonts (Space Grotesk, IBM Plex Mono)
- jsDelivr: Three.js, GSAP, ScrollTrigger
- GitHub Pages hosting

## Accessibility

- `prefers-reduced-motion`: disables GSAP, tilt, magnetic effects, 3D animation
- Bento tilt / magnetic buttons: `(hover: hover)` only — static on touch
- Focus-visible rings on all interactive elements

## License

Site content: same as Anima project (MIT).
