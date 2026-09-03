import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

// ---------------------------------------------------------------- renderer ----
const holder = document.getElementById("canvas-holder");
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
holder.appendChild(renderer.domElement);

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x080b10);

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
  const tnow = performance.now();
  // shapes draw themselves on — geometry revealed progressively (curves and surfaces alike)
  for (let i = drawAnim.length - 1; i >= 0; i--) {
    const d = drawAnim[i];
    const p = Math.min(1, (tnow - d.t0) / d.dur);
    const eased = 1 - Math.pow(1 - p, 3);
    d.geom.setDrawRange(0, p >= 1 ? d.count : Math.max(2, Math.floor(eased * d.count)));
    if (p >= 1) drawAnim.splice(i, 1);
  }
  // point markers grow in from nothing
  for (let i = growAnim.length - 1; i >= 0; i--) {
    const g = growAnim[i];
    const p = Math.min(1, (tnow - g.t0) / g.dur);
    const e = 1 - Math.pow(1 - p, 3);
    for (const m of g.meshes) m.mesh.scale.setScalar(Math.max(0.001, e) * m.base);
    if (p >= 1) { for (const m of g.meshes) m.mesh.scale.setScalar(m.base); growAnim.splice(i, 1); }
  }
  // the vector field / scalar grids fade in behind the drawing wavefront
  for (let i = fades.length - 1; i >= 0; i--) {
    const f = fades[i];
    const p = Math.min(1, (tnow - f.t0) / f.dur);
    const e = p * p * (3 - 2 * p);
    for (const m of f.ents) m.m.opacity = m.o0 * e;
    if (p >= 1) { for (const m of f.ents) { m.m.opacity = m.o0; m.m.transparent = m.tr; } fades.splice(i, 1); }
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
let sceneData = null;
let fieldHidden = false;               // vector-field toggle state
// how a layer ENTERS: shapes (surfaces, curves) DRAW themselves on; point markers GROW from
// nothing; the vector field and scalar grids FADE in behind the drawing. Slow and deliberate.
let drawAnim = [];                     // {geom, count, t0, dur} — geometry revealed by drawRange
let growAnim = [];                     // {meshes:[{mesh,base}], t0, dur} — point markers scaling in
let fades = [];                        // {ents, t0, dur} — field/grid layers fading in
const DRAW_DUR = 2600;
const FADE_DUR = 850;
const GROW_DUR = 620;

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

const FIELD_IDS = new Set(["vector_field", "flow_field", "gradient_field"]);

function buildScene(data) {
  sceneData = data;
  clearContent();
  drawAnim = []; growAnim = []; fades = [];
  zScale = computeZScale(data);
  // reference axes at the origin
  const axes = new THREE.AxesHelper(3.2);
  axes.material.transparent = true; axes.material.opacity = 0.22;
  contentGroup.add(axes);

  for (const layer of data.layers) {
    const obj = buildLayer(layer);
    obj.userData.step = layer.step;
    obj.userData.isField = layer.type === "vectors" && FIELD_IDS.has(layer.id);
    contentGroup.add(obj);
    layerObjects.push({ object: obj, step: layer.step, type: layer.type, wasVisible: false });
  }
  steps = data.steps || [];
  maxStep = layerObjects.reduce((m, l) => Math.max(m, l.step), 0);
  setStep(maxStep); // reveals every layer and triggers its entrance animation
  frameScene(false); // snap to a good first framing, then let steps ease from here
}

// fade a (non-curve) layer object in on first reveal; restores material state when done
function fadeIn(obj) {
  const ents = [];
  obj.traverse((o) => {
    if (!o.material) return;
    const arr = Array.isArray(o.material) ? o.material : [o.material];
    for (const m of arr) ents.push({ m, o0: (m.opacity == null ? 1 : m.opacity), tr: m.transparent });
  });
  if (!ents.length) return;
  for (const e of ents) { e.m.transparent = true; e.m.opacity = 0; }
  fades.push({ ents, t0: performance.now(), dur: FADE_DUR });
}

// A shape (surface, mesh, curve) draws itself on: reveal its geometry progressively via
// drawRange — the same mechanism whether it's a line's vertices or a surface's triangles.
function triggerDraw(object) {
  const geoms = new Set();
  object.traverse((o) => { if ((o.isLine || o.isMesh) && o.geometry) geoms.add(o.geometry); });
  for (const geom of geoms) {
    const count = geom.index ? geom.index.count : ((geom.getAttribute("position") || {}).count || 0);
    if (!count) continue;
    for (let i = drawAnim.length - 1; i >= 0; i--) if (drawAnim[i].geom === geom) drawAnim.splice(i, 1);
    geom.setDrawRange(0, 2);
    drawAnim.push({ geom, count, t0: performance.now(), dur: DRAW_DUR });
  }
}

// Point markers grow in from nothing — a shape appearing from a single point.
function triggerGrow(object) {
  const meshes = [];
  object.traverse((o) => { if (o.isMesh) { meshes.push({ mesh: o, base: o.scale.x || 1 }); o.scale.setScalar(0.001); } });
  if (meshes.length) growAnim.push({ meshes, t0: performance.now(), dur: GROW_DUR });
}

// Dispatch a layer's entrance by kind when it is first revealed.
function revealAnim(l) {
  const t = l.type;
  if (t === "surface" || t === "param_surface" || t === "polyline" || t === "curve") triggerDraw(l.object);
  else if (t === "points") triggerGrow(l.object);
  else fadeIn(l.object); // vectors (the field), scalar_grid, eigenvectors
}

// replay: forget what has entered, so re-revealing re-draws / re-grows / re-fades everything
function startDrawIn() {
  drawAnim = []; growAnim = []; fades = [];
  for (const l of layerObjects) l.wasVisible = false;
}

// reveal up to step k and fly the camera to the geometry that step introduces (G5)
function focusStep(k) {
  setStep(k);
  const box = new THREE.Box3();
  let any = false;
  for (const l of layerObjects) {
    if (l.step === k && l.object.visible) { box.expandByObject(l.object); any = true; }
  }
  if (any && !box.isEmpty()) {
    const c = box.getBoundingSphere(new THREE.Sphere()).center;
    focusOn([c.x, c.y, c.z / (zScale || 1)], 0.55);
  } else {
    fitCamera(); clearHighlight();
  }
}

// Frame the whole scene. ease=true glides there (used for every step/overview move so the
// camera never snaps); ease=false sets it immediately (used once, for the first framing).
function frameScene(ease = true) {
  const box = new THREE.Box3().setFromObject(contentGroup);
  if (box.isEmpty()) return;
  const sphere = box.getBoundingSphere(new THREE.Sphere());
  const r = Math.max(sphere.radius, 0.5);
  const dist = r / Math.sin((camera.fov * Math.PI) / 180 / 2) * 1.15;
  // keep the current viewing direction if we already have a scene, else a pleasing default
  let dir = camera.position.clone().sub(controls.target);
  if (dir.lengthSq() < 1e-6) dir = new THREE.Vector3(1, -1.1, 0.75);
  dir.normalize();
  const pos = sphere.center.clone().addScaledVector(dir, dist);
  // set clipping planes generously up front so nothing pops during the glide
  camera.near = Math.max(dist / 200, 0.001); camera.far = dist * 200;
  camera.updateProjectionMatrix();
  if (ease) { focusTarget = sphere.center.clone(); focusCamPos = pos; }
  else { controls.target.copy(sphere.center); camera.position.copy(pos); focusTarget = null; focusCamPos = null; controls.update(); }
}
function fitCamera() { frameScene(true); }

function setStep(k) {
  currentStep = Math.max(0, Math.min(maxStep, k));
  for (const l of layerObjects) {
    let vis = l.step <= currentStep;
    if (fieldHidden && l.object.userData.isField) vis = false;
    l.object.visible = vis;
    // each layer plays its entrance the moment it is first revealed
    if (vis && !l.wasVisible) revealAnim(l);
    l.wasVisible = vis;
  }
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
function focusOn(target, zoom = 0.9) {
  const p = V(target);
  focusTarget = p.clone();
  highlightMarker.position.copy(p);
  highlightMarker.visible = true;
  // ease the camera in while keeping its current viewing direction
  const dir = camera.position.clone().sub(controls.target).normalize();
  const r = new THREE.Box3().setFromObject(contentGroup).getBoundingSphere(new THREE.Sphere()).radius || 3;
  focusCamPos = p.clone().addScaledVector(dir, Math.max(r * zoom, 1.8));
}
function clearHighlight() {
  highlightMarker.visible = false;
  focusTarget = null; focusCamPos = null;
}
window.__ml.focusOn = focusOn;
// debug: how many entrance animations are in flight (0 once everything has finished drawing)
window.__ml.drawing = () => ({ draw: drawAnim.length, grow: growAnim.length, fade: fades.length });

// ---------------------------------------------------------------- UI ----------
const $ = (id) => document.getElementById(id);
const qEl = $("quantities");
const thinkingEl = $("thinking");
const errorEl = $("error");
const brainBadge = $("brain-badge");
const tracePanel = $("trace-panel");
const traceToggle = $("trace-toggle");
const replayBtn = $("replay-btn");
const fieldToggle = $("field-toggle");
const tutorCard = $("tutor-card");
const tutorLabel = $("tutor-label");
const tutorText = $("tutor-text");
const tutorPrev = $("tutor-prev");
const tutorNext = $("tutor-next");
const tutorDots = $("tutor-dots");
const tutorCounter = $("tutor-counter");
const tutorVerified = $("tutor-verified");
const modelDerived = $("model-derived");
const resultsToggle = $("results-toggle");
const resultsPanel = $("results-panel");
const chatInput = $("chat-input");
const sendBtn = $("send-btn");

const SESSION = Math.random().toString(36).slice(2);
let beats = [];       // {label, text, focus, revealStep, verified, model_derived}
let beatIdx = 0;

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
  busy = true; errorEl.hidden = true; thinkingEl.hidden = false; sendBtn.disabled = true;
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
    thinkingEl.hidden = true; busy = false; sendBtn.disabled = false;
  }
}

function firstFocus(r) {
  const d = (r.directives || []).find((x) => x && x.type === "focus" && Array.isArray(x.target));
  return d ? d.target : null;
}
function allVerified(qs) { return !!(qs && qs.length && qs.every((q) => q.verification && q.verification.passed)); }
function layerLabel(step) {
  const ls = (sceneData?.layers || []).filter((l) => l.step === step && l.label);
  return ls.map((l) => l.label).join(" · ");
}

function renderResult(userText, r) {
  const isSolve = (r.trace?.tool_sequence || []).some((t) => t.startsWith("solve_"));
  renderTrace(r.trace);
  if (r.scene && isSolve) {
    newProblem(r);
    return;
  }
  // follow-up, focus move, or decline — add a beat and jump to it
  if (!sceneData) {                     // nothing solved yet (e.g. a decline)
    tutorCard.hidden = false;
    beats = [{ label: r.declined ? "Note" : "Answer", text: r.answer, focus: "hold",
               revealStep: maxStep, verified: false, model_derived: r.model_derived }];
    goBeat(0);
    return;
  }
  const tgt = firstFocus(r);
  beats.push({ label: "Answer", text: r.answer, focus: tgt ? { target: tgt } : "hold",
               revealStep: maxStep, verified: !r.model_derived && allVerified(sceneData.quantities),
               model_derived: r.model_derived });
  goBeat(beats.length - 1);
}

function newProblem(r) {
  fieldHidden = false;
  clearHighlight();
  buildScene(r.scene);                  // shows the finished scene, self-drawing (G4)
  showQuantities(r.quantities || []);
  const area = (r.scene.title || r.area || "").trim();
  beats = [{ label: area || "Answer", text: r.answer, focus: "fit", revealStep: maxStep,
             verified: allVerified(r.quantities) && !r.model_derived, model_derived: r.model_derived }];
  for (const s of (r.walkthrough || [])) {
    beats.push({ label: s.introduces, text: s.description || layerLabel(s.step) || s.introduces,
                 focus: { step: s.step }, revealStep: s.step,
                 verified: !!s.description, model_derived: false });
  }
  // end the walkthrough by zooming back out to the whole finished picture
  if ((r.walkthrough || []).length) {
    beats.push({ label: "The full picture", focus: "fit", revealStep: maxStep,
                 text: "Every feature together — rotate, zoom, and explore the finished visual.",
                 verified: false, model_derived: false });
  }
  beatIdx = 0;
  tutorCard.hidden = false;
  replayBtn.hidden = false;
  traceToggle.hidden = false;
  resultsPanel.hidden = true;
  const hasField = (r.scene.layers || []).some((l) => l.type === "vectors" && FIELD_IDS.has(l.id));
  fieldToggle.hidden = !hasField;
  fieldToggle.classList.toggle("on", hasField && !fieldHidden);
  goBeat(0);
}

function goBeat(i) {
  if (!beats.length) return;
  beatIdx = Math.max(0, Math.min(beats.length - 1, i));
  const b = beats[beatIdx];
  // drive the visualization
  if (b.focus === "fit") { setStep(b.revealStep); clearHighlight(); fitCamera(); }
  else if (b.focus === "hold") { setStep(b.revealStep); }
  else if (b.focus && b.focus.step != null) { focusStep(b.focus.step); }
  else if (b.focus && b.focus.target) { setStep(b.revealStep); focusOn(b.focus.target, 0.55); }
  // update the card
  tutorLabel.textContent = b.label;
  tutorText.textContent = b.text;
  tutorVerified.hidden = !b.verified;
  modelDerived.hidden = !b.model_derived;
  tutorCounter.textContent = `${beatIdx + 1} / ${beats.length}`;
  tutorPrev.disabled = beatIdx === 0;
  tutorNext.disabled = beatIdx === beats.length - 1;
  tutorDots.innerHTML = "";
  beats.forEach((_, k) => {
    const s = document.createElement("span");
    if (k === beatIdx) s.className = "on";
    tutorDots.appendChild(s);
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
}

function renderTrace(trace) {
  if (!trace || !trace.calls) { tracePanel.innerHTML = ""; return; }
  const rows = trace.calls.map((c) => {
    const badge = c.ok ? (c.verified ? '<span class="ok">✓ verified</span>' : '<span class="ok">ok</span>')
                       : '<span class="bad">error</span>';
    const prov = (c.provenance || []).length ? ` · via ${(c.provenance).join(", ")}` : "";
    return `<div class="tcall"><code>${escapeHtml(c.tool)}(${escapeHtml(JSON.stringify(c.input))})</code> ${badge}${prov}</div>`;
  }).join("");
  tracePanel.innerHTML =
    `<div class="tinterp">interpretation: ${escapeHtml(trace.interpretation || "—")}</div>`
    + (rows || '<div class="tcall">answered from the current problem (no tools called)</div>');
}

function escapeHtml(s) {
  return String(s).replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));
}

// --- controls ----------------------------------------------------------------

tutorPrev.onclick = () => goBeat(beatIdx - 1);
tutorNext.onclick = () => goBeat(beatIdx + 1);

replayBtn.onclick = () => { startDrawIn(); beatIdx = 0; goBeat(0); };

fieldToggle.onclick = () => {
  fieldHidden = !fieldHidden;
  fieldToggle.classList.toggle("on", !fieldHidden);
  setStep(currentStep);
};

traceToggle.onclick = () => {
  const show = tracePanel.hidden;
  tracePanel.hidden = !show;
  traceToggle.classList.toggle("on", show);
  traceToggle.setAttribute("aria-expanded", String(show));
};

resultsToggle.onclick = () => {
  const show = resultsPanel.hidden;
  resultsPanel.hidden = !show;
  tutorCard.hidden = show;            // swap the two (they share the lower-left slot)
  resultsToggle.setAttribute("aria-expanded", String(show));
};
resultsPanel.addEventListener("click", (e) => {
  if (e.target === resultsPanel) { resultsPanel.hidden = true; tutorCard.hidden = false; }
});

async function sendChat() {
  const text = chatInput.value.trim();
  if (!text) return;
  chatInput.value = "";
  const r = await postAgent(text);
  if (r) renderResult(text, r);
}
sendBtn.onclick = sendChat;
chatInput.addEventListener("keydown", (e) => { if (e.key === "Enter") sendChat(); });

loadHealth();
animate(); // start the render loop once all module state is initialized
