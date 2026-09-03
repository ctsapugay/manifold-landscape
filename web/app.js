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
  // tutor-driven view easing — runs every frame, independent of any agent request, so the
  // scene stays smooth while the agent thinks (constraint C-INTERACTIVE)
  if (focusTarget) {
    controls.target.lerp(focusTarget, 0.1);
    if (focusCamPos) camera.position.lerp(focusCamPos, 0.1);
    if (controls.target.distanceTo(focusTarget) < 0.01) { focusTarget = null; focusCamPos = null; }
  }
  if (highlightMarker.visible) {
    const s = 1 + 0.18 * Math.sin(performance.now() * 0.005);
    highlightMarker.scale.setScalar(s);
  }
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

// tutor-driven view: an eased focus target + a pulsing highlight marker (criterion G5)
let focusTarget = null;      // THREE.Vector3 the controls ease toward
let focusCamPos = null;      // THREE.Vector3 the camera eases toward
const highlightMarker = new THREE.Mesh(
  new THREE.SphereGeometry(0.32, 24, 24),
  new THREE.MeshBasicMaterial({ color: 0xffd166, wireframe: true, transparent: true, opacity: 0.9 }));
highlightMarker.visible = false;
scene.add(highlightMarker);

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

// Drive the view to a feature the tutor is explaining (criterion G5). ``target`` is a raw
// scene-space point [x, y, z]; it is mapped through the same V() transform the geometry uses.
function focusOn(target) {
  const p = V(target);
  focusTarget = p.clone();
  highlightMarker.position.copy(p);
  highlightMarker.visible = true;
  // ease the camera in while keeping its current viewing direction
  const dir = camera.position.clone().sub(controls.target).normalize();
  const r = new THREE.Box3().setFromObject(contentGroup).getBoundingSphere(new THREE.Sphere()).radius || 3;
  focusCamPos = p.clone().addScaledVector(dir, Math.max(r * 0.9, 2.5));
}
function clearHighlight() {
  highlightMarker.visible = false;
  focusTarget = null; focusCamPos = null;
}
window.__ml.focusOn = focusOn;

// ---------------------------------------------------------------- UI ----------
const $ = (id) => document.getElementById(id);
const stepList = $("step-list");
const stepLabel = $("step-label");
const qSection = $("quantities-section");
const qEl = $("quantities");
const titleEl = $("scene-title");
const thinkingEl = $("thinking");
const errorEl = $("error");
const answerSection = $("answer-section");
const answerText = $("answer-text");
const modelDerived = $("model-derived");
const tracePanel = $("trace-panel");
const traceToggle = $("trace-toggle");
const walkSection = $("walk-section");
const walkBtn = $("walk-btn");
const walkControls = $("walk-controls");
const chatSection = $("chat-section");
const chatLog = $("chat-log");
const brainBadge = $("brain-badge");

const SESSION = Math.random().toString(36).slice(2);

const EXAMPLES = [
  ["Surfaces", ["f = x^2 + y^2", "f = x^2 - y^2", "f = sin(x)*cos(y)"]],
  ["Optimization", ["minimize x^2 + 3y^2 starting at (3,2)",
                    "minimize x^2 + y^2 subject to x + y = 1"]],
  ["Vector fields", ["F = (-y, x)", "F = (x, y)"]],
  ["Linear algebra", ["[[2,1],[1,2]]", "the SVD of [[1,2,0],[0,1,2],[2,0,1]]"]],
  ["Dynamical systems", ["x' = y, y' = -x - y", "show me an example of chaos"]],
];

function buildExamples() {
  const host = $("examples");
  for (const [name, prompts] of EXAMPLES) {
    const g = document.createElement("div");
    g.className = "area-group";
    g.innerHTML = `<div class="area-name">${name}</div>`;
    for (const p of prompts) {
      const b = document.createElement("button");
      b.className = "problem"; b.textContent = p;
      b.onclick = () => { promptInput.value = p; submitProblem(p); };
      g.appendChild(b);
    }
    host.appendChild(g);
  }
}

async function loadHealth() {
  try {
    const h = await (await fetch("/api/agent/health")).json();
    brainBadge.textContent = h.claude_available ? `Claude · ${h.model}` : "offline engine";
    brainBadge.className = h.claude_available ? "badge-claude" : "badge-neutral";
  } catch { brainBadge.textContent = "offline engine"; }
}

// --- talking to the agent ----------------------------------------------------

let busy = false;
async function postAgent(text) {
  if (busy || !text.trim()) return null;
  busy = true; errorEl.hidden = true; thinkingEl.hidden = false;
  try {
    const res = await fetch("/api/agent", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session: SESSION, text }),
    });
    return await res.json();
  } catch (e) {
    errorEl.hidden = false; errorEl.textContent = "Request failed: " + e.message;
    return null;
  } finally {
    thinkingEl.hidden = true; busy = false;
  }
}

async function submitProblem(text) {
  const r = await postAgent(text);
  if (r) renderResult(text, r);
}

function renderResult(userText, r) {
  applyDirectives(r.directives || []);
  const isSolve = (r.trace?.tool_sequence || []).some((t) => t.startsWith("solve_"));
  if (r.scene && isSolve) {
    newProblem(r);
  } else if (answerSection.hidden) {
    answerText.textContent = r.answer;
    modelDerived.hidden = !r.model_derived;
    renderTrace(r.trace);
    answerSection.hidden = false;
  } else {
    appendChat("you", userText);
    appendChat("tutor", r.answer);
    chatSection.hidden = false;
  }
}

function newProblem(r) {
  clearHighlight();
  titleEl.textContent = (r.scene && r.scene.title) || "";
  buildScene(r.scene);              // shows the finished scene — no forced stepping (G4)
  showQuantities(r.quantities || []);
  answerText.textContent = r.answer;
  modelDerived.hidden = !r.model_derived;
  renderTrace(r.trace);
  answerSection.hidden = false;
  qSection.hidden = !(r.quantities || []).length;
  walkReset(r.walkthrough || []);
  chatLog.innerHTML = "";
  chatSection.hidden = false;
  applyDirectives(r.directives || []);
}

function applyDirectives(dirs) {
  for (const d of dirs) {
    if (d && d.type === "focus" && Array.isArray(d.target)) focusOn(d.target);
  }
}

// --- rendering pieces --------------------------------------------------------

function renderStepList() {
  const introduced = steps.map((s) => s.introduces);
  stepLabel.textContent = currentStep === 0 ? "base scene" : `step ${currentStep} of ${maxStep}`;
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

function renderTrace(trace) {
  if (!trace || !trace.calls) { tracePanel.innerHTML = ""; return; }
  const rows = trace.calls.map((c) => {
    const badge = c.ok
      ? (c.verified ? '<span class="ok">✓ verified</span>'
                    : (c.produced && c.produced.length ? '<span class="ok">ok</span>' : '<span class="ok">ok</span>'))
      : '<span class="bad">error</span>';
    const prov = (c.provenance || []).length ? ` · via ${(c.provenance).join(", ")}` : "";
    return `<div class="tcall"><code>${escapeHtml(c.tool)}(${escapeHtml(JSON.stringify(c.input))})</code>`
         + ` ${badge}${prov}</div>`;
  }).join("");
  tracePanel.innerHTML =
    `<div class="tinterp">interpretation: ${escapeHtml(trace.interpretation || "—")}</div>`
    + (rows || '<div class="tcall">no tools called (answered from the current problem)</div>');
}

function appendChat(who, text) {
  const div = document.createElement("div");
  div.className = "bubble " + (who === "you" ? "you" : "tutor");
  div.innerHTML = `<span class="who">${who}</span> ${escapeHtml(text)}`;
  chatLog.appendChild(div);
  chatLog.scrollTop = chatLog.scrollHeight;
}

function escapeHtml(s) {
  return String(s).replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));
}

// --- walkthrough (opt-in) ----------------------------------------------------

function walkReset(walkthrough) {
  walkSection.hidden = !(walkthrough && walkthrough.length);
  walkControls.hidden = true;
  walkBtn.hidden = false;
  setStep(maxStep); // default: the finished scene
}
walkBtn.onclick = () => { walkControls.hidden = false; walkBtn.hidden = true; setStep(0); };
$("step-prev").onclick = () => setStep(currentStep - 1);
$("step-next").onclick = () => setStep(currentStep + 1);

// --- trace toggle (G7) -------------------------------------------------------

traceToggle.onclick = () => {
  const show = tracePanel.hidden;
  tracePanel.hidden = !show;
  traceToggle.setAttribute("aria-expanded", String(show));
  traceToggle.textContent = (show ? "▾ hide" : "▸ show") + " the agent's tool calls";
};

// --- inputs ------------------------------------------------------------------

const promptInput = $("prompt-input");
$("solve-btn").onclick = () => submitProblem(promptInput.value);
promptInput.addEventListener("keydown", (e) => { if (e.key === "Enter") submitProblem(promptInput.value); });

const chatInput = $("chat-input");
async function sendChat() {
  const text = chatInput.value.trim();
  if (!text) return;
  chatInput.value = "";
  const r = await postAgent(text);
  if (r) renderResult(text, r);
}
$("chat-send").onclick = sendChat;
chatInput.addEventListener("keydown", (e) => { if (e.key === "Enter") sendChat(); });

buildExamples();
loadHealth();
animate(); // start the render loop once all module state is initialized
