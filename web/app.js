import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

// ---------------------------------------------------------------- renderer ----
const holder = document.getElementById("canvas-holder");
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
holder.appendChild(renderer.domElement);

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0e1116);

const camera = new THREE.PerspectiveCamera(50, 1, 0.01, 1000);
camera.up.set(0, 0, 1); // math z is up
camera.position.set(7, -7, 6);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.08;

scene.add(new THREE.AmbientLight(0xffffff, 0.65));
const key = new THREE.DirectionalLight(0xffffff, 0.9);
key.position.set(5, -3, 10);
scene.add(key);
const fill = new THREE.DirectionalLight(0x88aaff, 0.35);
fill.position.set(-6, 4, 3);
scene.add(fill);

function resize() {
  const w = holder.clientWidth || window.innerWidth - 320;
  const h = holder.clientHeight || window.innerHeight;
  renderer.setSize(w, h); // updates the canvas CSS size too, so it fills the holder
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
}
window.addEventListener("resize", resize);

function animate() {
  requestAnimationFrame(animate);
  controls.update();
  renderer.render(scene, camera);
  _frames++;
  const now = performance.now();
  if (now - _lastFpsT >= 500) {
    _fps = Math.round((_frames * 1000) / (now - _lastFpsT));
    _frames = 0; _lastFpsT = now;
  }
}
resize();

// ---------------------------------------------------------------- state -------
let contentGroup = new THREE.Group();
scene.add(contentGroup);
let zScale = 1;
let layerObjects = []; // {object, step}
let currentStep = 0;
let maxStep = 0;
let steps = [];
let currentId = null;
let _frames = 0, _fps = 0, _lastFpsT = performance.now();

const V = (p) => new THREE.Vector3(p[0], p[1], (p[2] || 0) * zScale);

// viridis-ish colormap
const STOPS = [
  [0.267, 0.005, 0.329], [0.283, 0.141, 0.458], [0.254, 0.265, 0.53],
  [0.207, 0.372, 0.553], [0.164, 0.471, 0.558], [0.128, 0.567, 0.551],
  [0.135, 0.659, 0.518], [0.267, 0.749, 0.441], [0.478, 0.821, 0.318],
  [0.741, 0.873, 0.15], [0.993, 0.906, 0.144],
];
function colormap(t) {
  t = Math.max(0, Math.min(1, t));
  const f = t * (STOPS.length - 1), i = Math.floor(f), r = f - i;
  const a = STOPS[i], b = STOPS[Math.min(i + 1, STOPS.length - 1)];
  return new THREE.Color(a[0] + (b[0] - a[0]) * r, a[1] + (b[1] - a[1]) * r,
                         a[2] + (b[2] - a[2]) * r);
}

// ---------------------------------------------------------------- layers ------
function buildSurface(d) {
  const nx = d.x.length, ny = d.y.length;
  const geo = new THREE.BufferGeometry();
  const pos = [], col = [];
  const zmin = d.z_min, zmax = d.z_max, span = (zmax - zmin) || 1;
  for (let i = 0; i < ny; i++)
    for (let j = 0; j < nx; j++) {
      pos.push(d.x[j], d.y[i], d.z[i][j] * zScale);
      const c = colormap((d.z[i][j] - zmin) / span);
      col.push(c.r, c.g, c.b);
    }
  const idx = [];
  for (let i = 0; i < ny - 1; i++)
    for (let j = 0; j < nx - 1; j++) {
      const a = i * nx + j, b = a + 1, c = a + nx, e = c + 1;
      idx.push(a, c, b, b, c, e);
    }
  geo.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
  geo.setAttribute("color", new THREE.Float32BufferAttribute(col, 3));
  geo.setIndex(idx);
  geo.computeVertexNormals();
  const mat = new THREE.MeshStandardMaterial({
    vertexColors: true, side: THREE.DoubleSide, roughness: 0.85, metalness: 0.0,
    flatShading: false,
  });
  const mesh = new THREE.Mesh(geo, mat);
  const wire = new THREE.Mesh(geo, new THREE.MeshBasicMaterial({
    color: 0x000000, wireframe: true, transparent: true, opacity: 0.08 }));
  const g = new THREE.Group(); g.add(mesh); g.add(wire);
  return g;
}

function buildParamSurface(d, color) {
  const grid = d.grid, nu = grid.length, nv = grid[0].length;
  const geo = new THREE.BufferGeometry();
  const pos = [];
  for (let i = 0; i < nu; i++)
    for (let j = 0; j < nv; j++)
      pos.push(grid[i][j][0], grid[i][j][1], grid[i][j][2]);
  const idx = [];
  for (let i = 0; i < nu - 1; i++)
    for (let j = 0; j < nv - 1; j++) {
      const a = i * nv + j, b = a + 1, c = a + nv, e = c + 1;
      idx.push(a, c, b, b, c, e);
    }
  geo.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
  geo.setIndex(idx);
  geo.computeVertexNormals();
  return new THREE.Mesh(geo, new THREE.MeshStandardMaterial({
    color, side: THREE.DoubleSide, roughness: 0.6, metalness: 0.1,
    transparent: true, opacity: 0.75 }));
}

function arrowGroup(arrows, color, targetMax = 0.55) {
  const g = new THREE.Group();
  let maxMag = 1e-9;
  for (const a of arrows) maxMag = Math.max(maxMag, Math.hypot(...a.vector));
  const scale = targetMax / maxMag * 2.2;
  for (const a of arrows) {
    const v = new THREE.Vector3(a.vector[0], a.vector[1], a.vector[2] * zScale);
    const len = v.length() * scale;
    if (len < 1e-6) continue;
    const dir = v.clone().normalize();
    const arr = new THREE.ArrowHelper(dir, V(a.origin), len, color,
                                      Math.min(0.22, len * 0.35), Math.min(0.14, len * 0.22));
    g.add(arr);
  }
  return g;
}

function buildPoints(d) {
  const g = new THREE.Group();
  for (const p of d.points) {
    const s = new THREE.Mesh(
      new THREE.SphereGeometry(0.12, 20, 20),
      new THREE.MeshStandardMaterial({ color: p.color || 0xffffff, roughness: 0.4 }));
    s.position.copy(V(p.position));
    g.add(s);
  }
  return g;
}

function buildPolyline(d, color, width) {
  const pts = d.points.map(V);
  const geo = new THREE.BufferGeometry().setFromPoints(pts);
  return new THREE.Line(geo, new THREE.LineBasicMaterial({ color, linewidth: width || 2 }));
}

function buildScalarGrid(d) {
  // colored dots slightly above the z=0 plane; blue = negative, red = positive
  const g = new THREE.Group();
  let amax = 1e-9;
  for (const row of d.values) for (const v of row) amax = Math.max(amax, Math.abs(v));
  for (let i = 0; i < d.y.length; i++)
    for (let j = 0; j < d.x.length; j++) {
      const v = d.values[i][j], t = 0.5 + 0.5 * (v / amax);
      const c = new THREE.Color(t, 0.25, 1 - t);
      const dot = new THREE.Mesh(new THREE.SphereGeometry(0.05, 8, 8),
        new THREE.MeshBasicMaterial({ color: c }));
      dot.position.set(d.x[j], d.y[i], 0.02);
      g.add(dot);
    }
  return g;
}

function buildEigenvectors(d) {
  const g = new THREE.Group();
  for (const a of d.arrows) {
    // the direction (unit) in grey, its image λv in accent — showing the invariance
    g.add(new THREE.ArrowHelper(new THREE.Vector3(...a.vector).normalize(),
      new THREE.Vector3(0, 0, 0), 1.0, 0x8b98a5, 0.18, 0.11));
    g.add(new THREE.ArrowHelper(new THREE.Vector3(...a.image).normalize(),
      new THREE.Vector3(0, 0, 0), Math.hypot(...a.image), 0x4c9be8, 0.2, 0.13));
  }
  return g;
}

function buildLayer(layer) {
  switch (layer.type) {
    case "surface": return buildSurface(layer.data);
    case "param_surface":
      return buildParamSurface(layer.data, layer.id === "unit_sphere" ? 0x5b6b7a : 0x4c9be8);
    case "vectors":
      return arrowGroup(layer.data.arrows,
        layer.id === "singular_axes" ? 0x4c9be8 : 0x9fb4c8);
    case "points": return buildPoints(layer.data);
    case "polyline": return buildPolyline(layer.data, 0xffb454, 3);
    case "curve": return buildPolyline(layer.data, layer.id === "unit_circle" ? 0x8b98a5 : 0x4c9be8);
    case "scalar_grid": return buildScalarGrid(layer.data);
    case "eigenvectors": return buildEigenvectors(layer.data);
    default: return new THREE.Group();
  }
}

// ---------------------------------------------------------------- scene build -
function clearContent() {
  contentGroup.traverse((o) => {
    if (o.geometry) o.geometry.dispose();
    if (o.material) (Array.isArray(o.material) ? o.material : [o.material]).forEach((m) => m.dispose());
  });
  scene.remove(contentGroup);
  contentGroup = new THREE.Group();
  scene.add(contentGroup);
  layerObjects = [];
}

function computeZScale(sceneData) {
  const surf = sceneData.layers.find((l) => l.type === "surface");
  if (!surf) return 1;
  const m = Math.max(Math.abs(surf.data.z_min), Math.abs(surf.data.z_max), 1e-6);
  return Math.min(1, 4 / m);
}

function buildScene(sceneData) {
  clearContent();
  zScale = computeZScale(sceneData);
  // reference axes at the origin
  const axes = new THREE.AxesHelper(3.2);
  axes.material.transparent = true; axes.material.opacity = 0.35;
  contentGroup.add(axes);

  for (const layer of sceneData.layers) {
    const obj = buildLayer(layer);
    obj.userData.step = layer.step;
    contentGroup.add(obj);
    layerObjects.push({ object: obj, step: layer.step });
  }
  steps = sceneData.steps || [];
  maxStep = layerObjects.reduce((m, l) => Math.max(m, l.step), 0);
  setStep(maxStep); // show the finished scene first
  fitCamera();
}

function fitCamera() {
  const box = new THREE.Box3().setFromObject(contentGroup);
  if (box.isEmpty()) return;
  const sphere = box.getBoundingSphere(new THREE.Sphere());
  const r = Math.max(sphere.radius, 0.5);
  controls.target.copy(sphere.center);
  const dist = r / Math.sin((camera.fov * Math.PI) / 180 / 2) * 1.15;
  const dir = new THREE.Vector3(1, -1.1, 0.75).normalize();
  camera.position.copy(sphere.center).addScaledVector(dir, dist);
  camera.near = dist / 100;
  camera.far = dist * 100;
  camera.updateProjectionMatrix();
  controls.update();
}

function setStep(k) {
  currentStep = Math.max(0, Math.min(maxStep, k));
  for (const l of layerObjects) l.object.visible = l.step <= currentStep;
  renderStepList();
}

// Verification/debug hook: lets a test (and the eventual automated G2/G3 checks) read the
// live render state — the current step, which layer steps are actually visible, and a
// rolling frame rate — without reaching into module internals.
window.__ml = {
  state: () => ({
    currentStep, maxStep,
    visibleSteps: layerObjects.filter((l) => l.object.visible).map((l) => l.step),
    layerSteps: layerObjects.map((l) => l.step),
    fps: _fps,
  }),
  setStep,
  // Render-throughput benchmark: time N forced renders while orbiting the camera. Does
  // not use requestAnimationFrame, so it measures true frame cost even when the pane is
  // hidden (rAF would pause). Frame cost << 16.7 ms means 60 fps interaction has headroom.
  bench: (n = 180) => {
    const t0 = performance.now();
    for (let i = 0; i < n; i++) {
      contentGroup.rotation.z = i * 0.02; // force matrix/scene work like a real orbit
      controls.update();
      renderer.render(scene, camera);
    }
    contentGroup.rotation.z = 0;
    const ms = performance.now() - t0;
    return { frames: n, total_ms: +ms.toFixed(1), ms_per_frame: +(ms / n).toFixed(3),
             fps: Math.round((n * 1000) / ms) };
  },
};

// ---------------------------------------------------------------- UI ----------
const catalogEl = document.getElementById("catalog");
const stepSection = document.getElementById("step-section");
const stepList = document.getElementById("step-list");
const stepLabel = document.getElementById("step-label");
const qSection = document.getElementById("quantities-section");
const qEl = document.getElementById("quantities");
const titleEl = document.getElementById("scene-title");
const loadingEl = document.getElementById("loading");
const errorEl = document.getElementById("error");

const AREA_NAMES = {
  "scalar-fields": "Scalar fields & surfaces",
  "optimization": "Gradients & optimization",
  "vector-fields": "Vector fields",
  "linear-algebra": "Linear algebra as geometry",
};

async function loadCatalog() {
  const items = await (await fetch("/api/catalog")).json();
  const byArea = {};
  for (const it of items) (byArea[it.area] ||= []).push(it);
  for (const [area, list] of Object.entries(byArea)) {
    const group = document.createElement("div");
    group.className = "area-group";
    group.innerHTML = `<div class="area-name">${AREA_NAMES[area] || area}</div>`;
    for (const it of list) {
      const b = document.createElement("button");
      b.className = "problem"; b.textContent = it.title; b.dataset.id = it.id;
      b.onclick = () => selectProblem(it.id, b);
      group.appendChild(b);
    }
    catalogEl.appendChild(group);
  }
}

async function selectProblem(id, btn) {
  document.querySelectorAll(".problem").forEach((b) => b.classList.remove("active"));
  if (btn) btn.classList.add("active");
  errorEl.hidden = true; loadingEl.hidden = false;
  try {
    const res = await fetch(`/api/scene?id=${encodeURIComponent(id)}`);
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "solve failed");
    titleEl.textContent = data.title;
    buildScene(data);
    showQuantities(data.quantities);
    stepSection.hidden = false;
    currentId = id;
    document.getElementById("ask-section").hidden = false;
    document.getElementById("ask-answer").classList.remove("show");
    document.getElementById("ask-grounding").textContent = "";
  } catch (e) {
    errorEl.hidden = false; errorEl.textContent = "Could not solve: " + e.message;
  } finally {
    loadingEl.hidden = true;
  }
}

function renderStepList() {
  const introduced = steps.map((s) => s.introduces);
  stepLabel.textContent = currentStep === 0
    ? "base scene" : `step ${currentStep} of ${maxStep}`;
  stepList.innerHTML = "";
  introduced.forEach((name, i) => {
    const stepIdx = steps[i].step;
    const li = document.createElement("li");
    li.textContent = name;
    if (stepIdx === currentStep) li.className = "current";
    else if (stepIdx > currentStep) li.className = "future";
    stepList.appendChild(li);
  });
}

function showQuantities(quantities) {
  qEl.innerHTML = "";
  for (const q of quantities) {
    const v = q.verification;
    const div = document.createElement("div");
    div.className = "quantity";
    div.innerHTML =
      `<div class="qname">${q.name.replace(/_/g, " ")}</div>` +
      `<div class="qval">${escapeHtml(q.display)}</div>` +
      `<div class="badge">✓ verified · residual ${v.residual.toExponential(1)} ≤ ` +
      `${v.tolerance.toExponential(0)} <span class="prov">via ${q.provenance}</span></div>`;
    qEl.appendChild(div);
  }
  qSection.hidden = quantities.length === 0;
}

function escapeHtml(s) {
  return String(s).replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));
}

document.getElementById("step-prev").onclick = () => setStep(currentStep - 1);
document.getElementById("step-next").onclick = () => setStep(currentStep + 1);

const askInput = document.getElementById("ask-input");
const askBtn = document.getElementById("ask-btn");
const askAnswer = document.getElementById("ask-answer");
const askGrounding = document.getElementById("ask-grounding");

async function ask() {
  const question = askInput.value.trim();
  if (!question || !currentId) return;
  askBtn.disabled = true;
  askAnswer.classList.add("show");
  askAnswer.textContent = "…";
  askGrounding.textContent = "";
  try {
    const res = await fetch("/api/ask", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id: currentId, question }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "no answer");
    askAnswer.textContent = data.answer;
    askGrounding.textContent = "grounded in verified results: " + data.grounded_in.join(", ");
  } catch (e) {
    askAnswer.textContent = "Could not answer: " + e.message;
  } finally {
    askBtn.disabled = false;
  }
}
askBtn.onclick = ask;
askInput.addEventListener("keydown", (e) => { if (e.key === "Enter") ask(); });

loadCatalog();
animate(); // start the render loop once all module state is initialized
