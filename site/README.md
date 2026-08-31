# Anima — presentation website

Dark, high-tech landing page for [Anima](https://github.com/RobertKodes/anima). Static HTML/CSS/JS — no build step.

**Live URL:** https://robertkodes.github.io/anima/

## Features

- Dark terminal aesthetic matching the Anima TUI (`#140f0a`, amber prompts, orange borders)
- **Y2K glassmorphism** — frosted panels, iridescent borders, floating orbs, CRT scanlines
- **Parallax** — scroll-driven layers + subtle mouse shift on orbs
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

GitHub Pages for this repo serves the **`gh-pages` branch** (not `master/site` directly).

After changing files under `site/`, push to `master` then deploy:

```powershell
# Windows
.\scripts\deploy_pages.ps1
```

```bash
# macOS / Linux
./scripts/deploy_pages.sh
```

Or manually: `git subtree split --prefix=site -b deploy-gh-pages && git push origin deploy-gh-pages:gh-pages --force`

**Live URL:** https://robertkodes.github.io/anima/

The workflow `.github/workflows/pages.yml` runs on push but only works if repo **Settings → Pages → Source** is set to **GitHub Actions**. If you still see an old design, run the deploy script above.

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
