# Anima — presentation website

Neo-brutalist landing page for [Anima](https://github.com/RobertKodes/anima). Static HTML/CSS/JS — no build step.

**Live URL (after GitHub Pages is enabled):**  
`https://robertkodes.github.io/anima/`

## Features

- Neo-brutalist design (thick borders, offset shadows, Anima palette)
- **Three.js** 3D hero — wireframe being with orbiting memory nodes
- **Scrolljacking** with section navigation — disabled when `prefers-reduced-motion` or user toggles “Standard scroll”
- Legal pages: Privacy (GDPR/CCPA), Terms, Cookies, Accessibility (WCAG 2.1 AA), Imprint

## Local preview

```bash
cd site
python -m http.server 8080
# open http://127.0.0.1:8080
```

## Deploy to GitHub Pages

1. Repo **Settings → Pages → Build and deployment → Source: GitHub Actions**
2. Push to `master` — workflow `.github/workflows/pages.yml` deploys the `site/` folder automatically.
3. Or manual: **Settings → Pages → Deploy from branch** is not used; we use Actions for the `site/` path.

## Structure

```
site/
  index.html          Landing (scroll sections)
  privacy.html        GDPR / UK GDPR / CCPA-oriented privacy policy
  terms.html          Terms of use
  cookies.html        Cookie & local storage policy
  accessibility.html  WCAG 2.1 AA statement
  imprint.html        Legal notice / Impressum-style
  css/style.css
  js/scroll.js        Section scroll + a11y fallbacks
  js/scene3d.js       Three.js hero
  js/consent.js       Cookie banner (essential-only by default)
```

## Compliance notes

- No analytics loaded without consent.
- Scrolljacking can be turned off via bottom-right toggle or respects `prefers-reduced-motion`.
- Third parties: Google Fonts, jsDelivr (Three.js), GitHub Pages hosting — documented in Privacy/Cookie policies.
- For formal EU legal service requiring a postal address, update `imprint.html` with your details.

## License

Site content: same as Anima project (MIT). Fonts: respective licenses (Google Fonts).
