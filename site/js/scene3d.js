/**
 * Dark-tech 3D hero — Three.js wireframe being (brain + memory metaphor).
 * Respects prefers-reduced-motion: static frame only.
 */

(function () {
  "use strict";

  const canvas = document.getElementById("scene3d");
  if (!canvas || typeof THREE === "undefined") return;

  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setClearColor(0x0a0c10, 1);

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(42, 1, 0.1, 100);
  camera.position.set(0, 0.4, 4.2);

  const ambient = new THREE.AmbientLight(0x8b93a7, 0.4);
  scene.add(ambient);
  const key = new THREE.DirectionalLight(0xe8a04a, 1.4);
  key.position.set(3, 4, 5);
  scene.add(key);
  const fill = new THREE.DirectionalLight(0x5eb8d4, 0.55);
  fill.position.set(-4, -1, 2);
  scene.add(fill);

  const group = new THREE.Group();
  scene.add(group);

  const matCore = new THREE.MeshStandardMaterial({
    color: 0xe8a04a,
    roughness: 0.25,
    metalness: 0.35,
    flatShading: true,
    emissive: 0x3d2a0a,
    emissiveIntensity: 0.4,
  });
  const matWire = new THREE.MeshBasicMaterial({ color: 0xe8a04a, wireframe: true, transparent: true, opacity: 0.35 });
  const matOrb = new THREE.MeshStandardMaterial({
    color: 0x5eb8d4,
    roughness: 0.3,
    metalness: 0.4,
    flatShading: true,
    emissive: 0x1a3040,
    emissiveIntensity: 0.3,
  });

  const core = new THREE.Mesh(new THREE.IcosahedronGeometry(0.85, 1), matCore);
  group.add(core);
  const wire = new THREE.Mesh(new THREE.IcosahedronGeometry(1.05, 2), matWire);
  group.add(wire);

  const orbitGroup = new THREE.Group();
  group.add(orbitGroup);
  for (let i = 0; i < 5; i++) {
    const orb = new THREE.Mesh(new THREE.BoxGeometry(0.22, 0.22, 0.22), matOrb);
    const angle = (i / 5) * Math.PI * 2;
    orb.position.set(Math.cos(angle) * 1.55, Math.sin(angle * 0.7) * 0.35, Math.sin(angle) * 1.55);
    orb.rotation.set(angle, angle * 0.5, 0);
    orbitGroup.add(orb);
  }

  const floor = new THREE.Mesh(
    new THREE.PlaneGeometry(6, 6),
    new THREE.MeshStandardMaterial({ color: 0x12151c, roughness: 1, metalness: 0 })
  );
  floor.rotation.x = -Math.PI / 2;
  floor.position.y = -1.35;
  scene.add(floor);

  let mx = 0;
  let my = 0;
  canvas.addEventListener("pointermove", (event) => {
    const rect = canvas.getBoundingClientRect();
    mx = ((event.clientX - rect.left) / rect.width - 0.5) * 2;
    my = ((event.clientY - rect.top) / rect.height - 0.5) * 2;
  });

  function resize() {
    const rect = canvas.getBoundingClientRect();
    const w = Math.max(rect.width, 1);
    const h = Math.max(rect.height, 1);
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  }

  resize();
  window.addEventListener("resize", resize);

  let raf = 0;
  function tick(time) {
    const t = time * 0.001;
    if (!reduced) {
      group.rotation.y = t * 0.35 + mx * 0.25;
      group.rotation.x = my * 0.18;
      orbitGroup.rotation.y = -t * 0.55;
      core.position.y = Math.sin(t * 1.2) * 0.06;
    }
    camera.lookAt(0, 0, 0);
    renderer.render(scene, camera);
    if (!reduced) raf = requestAnimationFrame(tick);
  }

  if (reduced) {
    group.rotation.y = 0.6;
    tick(0);
  } else {
    raf = requestAnimationFrame(tick);
  }

  document.addEventListener("visibilitychange", () => {
    if (reduced) return;
    if (document.hidden) cancelAnimationFrame(raf);
    else raf = requestAnimationFrame(tick);
  });
})();
