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
  // the vector field / scalar grids fade in behind the drawing wavefront; the same loop
  // fades a shape OUT when the user switches surface⇄contour (dir < 0), restoring its
  // material state at the end so it draws cleanly if shown again
  for (let i = fades.length - 1; i >= 0; i--) {
    const f = fades[i];
    const p = Math.min(1, (tnow - f.t0) / f.dur);
    const e = p * p * (3 - 2 * p);
    const k = f.dir < 0 ? 1 - e : e;
    for (const m of f.ents) m.m.opacity = m.o0 * k;
    if (p >= 1) {
      for (const m of f.ents) { m.m.opacity = m.o0; m.m.transparent = m.tr; }
      if (f.done) f.done();
      fades.splice(i, 1);
    }
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
// how the base SURFACE is revealed: "surface" = the mesh grows on from its centre (default);
// "contour" = the surface is dropped and level-set rings bloom outward from the centre. The
// user switches between the two and back; grow-from-centre is always the default per problem.
let surfaceMode = "surface";
let surfaceLayerObj = null;            // the layerObjects entry whose type === "surface"
let surfaceGroup = null;               // its mesh+wireframe group (grow-from-centre)
let contourGroup = null;               // the level-set rings (contours-bloom), built lazily, hidden by default
// how a layer ENTERS: shapes (surfaces, curves) DRAW themselves on; point markers GROW from
// nothing; the vector field and scalar grids FADE in behind the drawing. Slow and deliberate.
let drawAnim = [];                     // {geom, count, t0, dur} — geometry revealed by drawRange
let growAnim = [];                     // {meshes:[{mesh,base}], t0, dur} — point markers scaling in
let fades = [];                        // {ents, t0, dur} — field/grid layers fading in
// Deliberately unhurried so a first-time learner can follow each shape being drawn on before
// the next arrives (criterion G11 / C-STEPWISE). Slower than the first pass, which Clara found
// still too fast to track on a complex problem.
const DRAW_DUR = 4200;
const FADE_DUR = 1300;
const GROW_DUR = 1100;

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
  // Order the triangles centre-outward so a progressive drawRange reveals the surface
  // GROWING FROM ITS CENTRE (the default reveal) rather than wiping across row by row.
  const cx = (d.x[0] + d.x[nx - 1]) / 2, cy = (d.y[0] + d.y[ny - 1]) / 2;
  const tris = [];
  for (let t = 0; t < idx.length; t += 3) {
    const a = idx[t], b = idx[t + 1], c = idx[t + 2];
    const mx = (pos[3 * a] + pos[3 * b] + pos[3 * c]) / 3 - cx;
    const my = (pos[3 * a + 1] + pos[3 * b + 1] + pos[3 * c + 1]) / 3 - cy;
    tris.push([a, b, c, mx * mx + my * my]);
  }
  tris.sort((p, q) => p[3] - q[3]);
  const sortedIdx = [];
  for (const tr of tris) sortedIdx.push(tr[0], tr[1], tr[2]);
  geo.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
  geo.setAttribute("color", new THREE.Float32BufferAttribute(col, 3));
  geo.setIndex(sortedIdx);
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

// Level-set contours of the same surface, as line segments coloured by height and ordered
// centre-outward so a progressive drawRange makes the rings BLOOM from the middle. This is
// the alternate reveal the user can switch to (the surface is dropped for these rings).
function buildContours(d, levels = 11) {
  const nx = d.x.length, ny = d.y.length;
  const zmin = d.z_min, zmax = d.z_max, span = (zmax - zmin) || 1;
  const cx = (d.x[0] + d.x[nx - 1]) / 2, cy = (d.y[0] + d.y[ny - 1]) / 2;
  const segs = []; // { a:[x,y,z], b:[x,y,z], t, dist }
  const mkseg = (a, b, z, t) => {
    const mx = (a[0] + b[0]) / 2 - cx, my = (a[1] + b[1]) / 2 - cy;
    return { a: [a[0], a[1], z], b: [b[0], b[1], z], t, dist: mx * mx + my * my };
  };
  for (let kk = 1; kk <= levels; kk++) {
    const level = zmin + (span * kk) / (levels + 1);
    const t = (level - zmin) / span, z = level * zScale;
    for (let i = 0; i < ny - 1; i++)
      for (let j = 0; j < nx - 1; j++) {
        const z00 = d.z[i][j], z10 = d.z[i][j + 1], z01 = d.z[i + 1][j], z11 = d.z[i + 1][j + 1];
        const x0 = d.x[j], x1 = d.x[j + 1], y0 = d.y[i], y1 = d.y[i + 1];
        const cross = (za, zb) => (za < level) !== (zb < level);
        const lerp = (xa, ya, za, xb, yb, zb) => {
          const f = (level - za) / (zb - za); return [xa + (xb - xa) * f, ya + (yb - ya) * f];
        };
        const pts = [];
        if (cross(z00, z10)) pts.push(lerp(x0, y0, z00, x1, y0, z10)); // bottom edge
        if (cross(z10, z11)) pts.push(lerp(x1, y0, z10, x1, y1, z11)); // right edge
        if (cross(z01, z11)) pts.push(lerp(x0, y1, z01, x1, y1, z11)); // top edge
        if (cross(z00, z01)) pts.push(lerp(x0, y0, z00, x0, y1, z01)); // left edge
        if (pts.length === 2) segs.push(mkseg(pts[0], pts[1], z, t));
        else if (pts.length === 4) { // ambiguous saddle cell — connect the two nearest pairs
          segs.push(mkseg(pts[0], pts[1], z, t));
          segs.push(mkseg(pts[2], pts[3], z, t));
        }
      }
  }
  segs.sort((p, q) => p.dist - q.dist); // centre-outward => rings bloom from the middle
  const pos = [], col = [];
  for (const s of segs) {
    const c = colormap(s.t);
    pos.push(s.a[0], s.a[1], s.a[2], s.b[0], s.b[1], s.b[2]);
    col.push(c.r, c.g, c.b, c.r, c.g, c.b);
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
  geo.setAttribute("color", new THREE.Float32BufferAttribute(col, 3));
  return new THREE.LineSegments(geo, new THREE.LineBasicMaterial({
    vertexColors: true, transparent: true, opacity: 0.95 }));
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
  surfaceMode = "surface";              // every new problem starts on grow-from-centre
  surfaceLayerObj = null; surfaceGroup = null; contourGroup = null;
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
    const entry = { object: obj, step: layer.step, type: layer.type, wasVisible: false };
    layerObjects.push(entry);
    if (layer.type === "surface") {
      surfaceLayerObj = entry; surfaceGroup = obj;
      contourGroup = buildContours(layer.data);   // its alternate reveal, hidden until chosen
      contourGroup.visible = false;
      contentGroup.add(contourGroup);
    }
  }
  steps = data.steps || [];
  maxStep = layerObjects.reduce((m, l) => Math.max(m, l.step), 0);
  setStep(maxStep); // reveals every layer and triggers its entrance animation
  frameScene(false); // snap to a good first framing, then let steps ease from here
}

// collect every material under an object, remembering its base opacity + transparent flag
function materialsOf(obj) {
  const ents = [];
  obj.traverse((o) => {
    if (!o.material) return;
    const arr = Array.isArray(o.material) ? o.material : [o.material];
    for (const m of arr) ents.push({ m, o0: (m.opacity == null ? 1 : m.opacity), tr: m.transparent });
  });
  return ents;
}

// fade a (non-curve) layer object in on first reveal; restores material state when done
function fadeIn(obj) {
  const ents = materialsOf(obj);
  if (!ents.length) return;
  for (const e of ents) { e.m.transparent = true; e.m.opacity = 0; }
  fades.push({ ents, t0: performance.now(), dur: FADE_DUR, dir: 1 });
}

// fade an object out, then run done() (used when swapping the surface for its contours);
// the fade loop restores each material's opacity/transparent when it finishes, so the
// object draws cleanly at full opacity the next time it is shown
function fadeOut(obj, done) {
  const ents = materialsOf(obj);
  if (!ents.length) { if (done) done(); return; }
  for (const e of ents) e.m.transparent = true;
  fades.push({ ents, t0: performance.now(), dur: FADE_DUR, dir: -1, done });
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
  if (t === "surface") { // grows from the centre, or its contours bloom, per the current mode
    triggerDraw(surfaceMode === "contour" && contourGroup ? contourGroup : l.object);
  } else if (t === "param_surface" || t === "polyline" || t === "curve") triggerDraw(l.object);
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
  // the base surface shows in exactly ONE representation: the grown mesh, or its contours
  if (surfaceLayerObj && contourGroup) {
    const on = surfaceLayerObj.step <= currentStep;
    if (surfaceMode === "contour") { surfaceGroup.visible = false; contourGroup.visible = on; }
    else contourGroup.visible = false;
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
// Phase 3: one unified conversation. The tutor's explanation and the chat are a single thread
// (G16); follow-ups are answered by the agent, grounded in the step's verified state (G17);
// clickable suggested prompts keep continuing and common questions a click away (G18); a start
// state opens into a session with a collapsible conversation and a "new chat" return (G19); and
// the visualization's domain can be expanded (G20).
const $ = (id) => document.getElementById(id);
const thinkingEl = $("thinking");
const errorEl = $("error");
const brainBadge = $("brain-badge");
const tracePanel = $("trace-panel");
const traceToggle = $("trace-toggle");
const fieldToggle = $("field-toggle");
const contourToggle = $("contour-toggle");
const launcher = $("launcher");
const launchInput = $("launch-input");
const launchSend = $("launch-send");
const launchChips = $("launch-chips");
const launchNote = $("launch-note");
const dock = $("dock");
const dockTab = $("dock-tab");
const dockCollapse = $("dock-collapse");
const dockSub = $("dock-sub");
const suggestionsEl = $("suggestions");
const threadEl = $("thread");
const chatInput = $("chat-input");
const sendBtn = $("send-btn");
const newChatBtn = $("new-chat");
const boundsEl = $("bounds");
const bdMinus = $("bd-minus");
const bdPlus = $("bd-plus");
const bdExpand = $("bd-expand");
const bdLabel = $("bd-label");

let SESSION = Math.random().toString(36).slice(2);
let sessionActive = false;
let thread = [];          // the one conversation (also the history — G14/G16)
let lessonSteps = [];     // the current problem's walkthrough steps
let stepCursor = -1;      // index of the last-revealed walkthrough step (-1 = not started)
let curScene = null;
let boundsFactor = 1;
let busy = false;

const IC_SPARK = '<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="#4fd6c9" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l1.9 5.3L19 10l-5.1 1.7L12 17l-1.9-5.3L5 10l5.1-1.7z"/></svg>';
const IC_CHECK = '<svg viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="#4fd6c9" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6L9 17l-5-5"/></svg>';

// --- notation: render raw expression source as readable notation in the UI (G12) -----------
const _SUP = { "0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴", "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹", "-": "⁻" };
function notation(src) {
  if (src == null) return "";
  let s = String(src);
  s = s.replace(/\*\*\s*(\d+)/g, (_m, d) => [...d].map((c) => _SUP[c] || c).join(""));
  s = s.replace(/\*\*/g, "^");
  s = s.replace(/(\d)\s*\*\s*(?=[A-Za-z(])/g, "$1");
  s = s.replace(/\s*\*\s*/g, "·");
  s = s.replace(/([\w).²³¹⁰⁴⁵⁶⁷⁸⁹])\s*-\s*(?=[\w(])/g, "$1 − ");
  s = s.replace(/(^|[(,=])\s*-\s*/g, (_m, p) => (p === "(" || p === "") ? p + "−" : p + " −");
  return s.replace(/\s{2,}/g, " ").trim();
}
function escapeHtml(s) {
  return String(s).replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));
}

async function loadHealth() {
  try {
    const h = await (await fetch("/api/agent/health")).json();
    brainBadge.textContent = h.claude_available ? `Claude · ${h.model}` : "offline engine";
    brainBadge.className = h.claude_available ? "badge-claude" : "badge-neutral";
  } catch { brainBadge.textContent = "offline engine"; }
}

// --- talking to the agent ----------------------------------------------------
async function api(path, body) {
  if (busy) return null;
  busy = true; errorEl.hidden = true; thinkingEl.hidden = false;
  sendBtn.disabled = true; launchSend.disabled = true;
  try {
    const res = await fetch(path, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    return await res.json();
  } catch (e) {
    errorEl.hidden = false; errorEl.textContent = "Request failed: " + e.message;
    return null;
  } finally {
    thinkingEl.hidden = true; busy = false; sendBtn.disabled = false; launchSend.disabled = false;
  }
}

// --- thread rendering (steps and chat are the SAME thread) -------------------
function scrollThread() { threadEl.scrollTop = threadEl.scrollHeight; }

function pushUserMsg(text) {
  thread.push({ role: "user", text });
  const d = document.createElement("div");
  d.className = "msg user";
  d.textContent = text;
  threadEl.appendChild(d); scrollThread();
}
function pushAgentMsg(answer, r) {
  thread.push({ role: "agent", text: answer });
  const d = document.createElement("div");
  d.className = "msg agent";
  const verified = r && !r.model_derived;
  const srcs = (r && r.grounded_in && r.grounded_in.length)
    ? `<span class="src">grounded in ${escapeHtml(r.grounded_in.join(", "))}</span>` : "";
  const warn = (r && r.model_derived) ? `<span class="mderiv">model-derived · unverified</span>` : "";
  d.innerHTML = `<div class="who">${IC_SPARK}<span>Claude</span>${warn}</div>` +
    `<div class="txt">${escapeHtml(answer)}${srcs}</div>`;
  threadEl.appendChild(d); scrollThread();
}
function appendStepMsg(step) {
  thread.push({ role: "tutor", step });
  const d = document.createElement("div");
  d.className = "msg tutor";
  const stage = step.stage ? `<span class="stage">stage ${step.stage.index}/${step.stage.total}</span>` : "";
  const ver = step.verified ? `<span class="vpill">${IC_CHECK} verified</span>` : "";
  let lines = "";
  for (const l of (step.lines || [])) {
    lines += `<div class="ln ${l.kind || "say"}">${escapeHtml(l.text || "")}</div>`;
  }
  d.innerHTML = `<div class="m-lbl"><span class="lab">${escapeHtml(step.title || "")}</span>${stage}${ver}</div>${lines}`;
  threadEl.appendChild(d); scrollThread();
}

// --- driving the visualization from a walkthrough step ----------------------
function driveStep(step) {
  const reveal = step.reveal == null ? maxStep : step.reveal;
  setStep(reveal);
  if (step.title === "The full picture") { clearHighlight(); fitCamera(); }
  else if (step.focus_target) focusOn(step.focus_target, 0.55);
  else clearHighlight();
}

// advance the walkthrough one step (the "show me the next step" action) — G18
function nextStep() {
  if (!lessonSteps.length) return;
  if (stepCursor === -1) { startDrawIn(); stepCursor = 0; }
  else if (stepCursor < lessonSteps.length - 1) stepCursor += 1;
  else return;
  const step = lessonSteps[stepCursor];
  appendStepMsg(step);
  driveStep(step);
  updateSuggestions();
}

function updateSuggestions() {
  suggestionsEl.innerHTML = "";
  const chips = [];
  if (lessonSteps.length) {
    if (stepCursor === -1) chips.push({ t: "walk me through it", next: true });
    else if (stepCursor < lessonSteps.length - 1) chips.push({ t: "show me the next step", next: true });
  }
  chips.push({ t: "why is this?" });
  const cur = stepCursor >= 0 ? lessonSteps[stepCursor] : null;
  chips.push({ t: cur && cur.quantity ? "explain this step" : "what does this show?" });
  for (const c of chips) {
    const el = document.createElement("button");
    el.className = "sugchip" + (c.next ? " primary" : "");
    el.textContent = c.t;
    el.onclick = () => { if (c.next) nextStep(); else sendQuestion(c.t); };
    suggestionsEl.appendChild(el);
  }
}

// --- asking a question (answered by the agent, grounded in the current step) -
async function sendQuestion(text) {
  text = (text || "").trim();
  if (!text || !sessionActive) return;
  pushUserMsg(text);
  const cur = stepCursor >= 0 ? lessonSteps[stepCursor] : (lessonSteps[0] || null);
  const step = cur ? { quantity: cur.quantity, focus: cur.focus, focus_target: cur.focus_target,
                       id: cur.id, title: cur.title } : null;
  const r = await api("/api/agent", { session: SESSION, text, step });
  if (!r) return;
  renderTrace(r.trace);
  pushAgentMsg(r.answer, r);
  const d = (r.directives || []).find((x) => x && x.type === "focus" && Array.isArray(x.target));
  if (d) focusOn(d.target, 0.55);
}

// --- posing a problem from the launcher (starts a session) ------------------
async function solveProblem(text) {
  text = (text || "").trim();
  if (!text) return;
  launchNote.hidden = true;
  const r = await api("/api/agent", { session: SESSION, text });
  if (!r) return;
  renderTrace(r.trace);
  const isSolve = (r.trace && r.trace.tool_sequence || []).some((t) => t.startsWith("solve_"));
  if (r.scene && isSolve) startSession(r, text);
  else { launchNote.hidden = false; launchNote.textContent = r.answer || "I couldn't solve that — try rephrasing."; }
}

const FIELD_HAS = (scene) => (scene.layers || []).some((l) => l.type === "vectors" && FIELD_IDS.has(l.id));

function startSession(r, userText) {
  fieldHidden = false; clearHighlight();
  buildScene(r.scene); curScene = r.scene;                 // shows the full scene (G4)
  lessonSteps = r.walkthrough || [];
  stepCursor = -1;
  sessionActive = true;
  launcher.hidden = true; dock.hidden = false; dockTab.hidden = true;
  newChatBtn.hidden = false; traceToggle.hidden = false;
  const hasField = FIELD_HAS(r.scene);
  fieldToggle.hidden = !hasField; fieldToggle.classList.toggle("on", hasField && !fieldHidden);
  const hasSurface = (r.scene.layers || []).some((l) => l.type === "surface");
  contourToggle.hidden = !hasSurface; contourToggle.classList.remove("on");
  const clbl = contourToggle.querySelector(".label"); if (clbl) clbl.textContent = "Contours";
  const domainBased = (r.area || r.scene.area) !== "linear-algebra";
  boundsEl.hidden = !domainBased; boundsFactor = 1; bdLabel.textContent = "bounds ×1";
  const rawTitle = (r.scene.title || "").trim();
  dockSub.textContent = (rawTitle ? notation(rawTitle) : (r.area || "")) || "";
  thread = []; threadEl.innerHTML = "";
  pushUserMsg(userText);
  pushAgentMsg(r.answer, r);
  updateSuggestions();
}

function newChat() {
  SESSION = Math.random().toString(36).slice(2);
  sessionActive = false; lessonSteps = []; stepCursor = -1; curScene = null;
  dock.hidden = true; dockTab.hidden = true; newChatBtn.hidden = true; boundsEl.hidden = true;
  fieldToggle.hidden = true; contourToggle.hidden = true; traceToggle.hidden = true; tracePanel.hidden = true;
  clearContent();
  thread = []; threadEl.innerHTML = ""; suggestionsEl.innerHTML = "";
  launcher.hidden = false; launchNote.hidden = true; launchInput.value = "";
}

// --- expandable bounds (G20) -------------------------------------------------
async function applyBounds(factor) {
  boundsFactor = Math.max(0.5, Math.min(4, factor));
  bdLabel.textContent = "bounds ×" + (boundsFactor % 1 ? boundsFactor.toFixed(1) : boundsFactor);
  const r = await api("/api/rescale", { session: SESSION, factor: boundsFactor });
  if (!r || !r.scene) return;
  fieldHidden = false;
  buildScene(r.scene); curScene = r.scene;
  if (r.walkthrough && r.walkthrough.length) lessonSteps = r.walkthrough;
  const hasSurface = (r.scene.layers || []).some((l) => l.type === "surface");
  contourToggle.hidden = !hasSurface;
  const hasField = FIELD_HAS(r.scene);
  fieldToggle.hidden = !hasField; fieldToggle.classList.toggle("on", hasField && !fieldHidden);
  if (stepCursor >= 0) {                              // keep the walkthrough position framed
    startDrawIn();
    const s = lessonSteps[Math.min(stepCursor, lessonSteps.length - 1)];
    if (s) driveStep(s);
  }
}

// --- trace (tool calls) — G7 -------------------------------------------------
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

// ---------------------------------------------------------------- controls ----
launchSend.onclick = () => solveProblem(launchInput.value);
launchInput.addEventListener("keydown", (e) => { if (e.key === "Enter") solveProblem(launchInput.value); });
launchChips.querySelectorAll(".ex").forEach((el) => {
  el.onclick = () => { launchInput.value = el.dataset.q || el.textContent; solveProblem(launchInput.value); };
});
sendBtn.onclick = () => { const t = chatInput.value; chatInput.value = ""; sendQuestion(t); };
chatInput.addEventListener("keydown", (e) => { if (e.key === "Enter") { const t = chatInput.value; chatInput.value = ""; sendQuestion(t); } });
newChatBtn.onclick = newChat;
dockCollapse.onclick = () => { dock.hidden = true; dockTab.hidden = false; };
dockTab.onclick = () => { dock.hidden = false; dockTab.hidden = true; };
bdMinus.onclick = () => applyBounds(boundsFactor - 0.5);
bdPlus.onclick = () => applyBounds(boundsFactor + 0.5);
bdExpand.onclick = () => applyBounds(Math.max(2, boundsFactor + 1));

fieldToggle.onclick = () => {
  fieldHidden = !fieldHidden;
  fieldToggle.classList.toggle("on", !fieldHidden);
  setStep(currentStep);
};
// switch the base surface between growing-from-centre and its contours-bloom, and back.
contourToggle.onclick = () => {
  if (!surfaceGroup || !contourGroup) return;
  const toContour = surfaceMode !== "contour";
  surfaceMode = toContour ? "contour" : "surface";
  if (toContour) {
    fadeOut(surfaceGroup, () => { surfaceGroup.visible = false; });
    contourGroup.visible = true; triggerDraw(contourGroup);
  } else {
    fadeOut(contourGroup, () => { contourGroup.visible = false; });
    surfaceGroup.visible = true; triggerDraw(surfaceGroup);
  }
  contourToggle.classList.toggle("on", toContour);
  const lbl = contourToggle.querySelector(".label");
  if (lbl) lbl.textContent = toContour ? "Surface" : "Contours";
};
traceToggle.onclick = () => {
  const show = tracePanel.hidden;
  tracePanel.hidden = !show;
  traceToggle.classList.toggle("on", show);
  traceToggle.setAttribute("aria-expanded", String(show));
};

// expose conversation state for tests / the automated checks
window.__ml.session = () => ({
  active: sessionActive, threadLen: thread.length,
  roles: thread.map((m) => m.role), stepCursor,
  steps: lessonSteps.length, collapsed: dock.hidden && !dockTab.hidden, boundsFactor,
});

loadHealth();
animate(); // start the render loop once all module state is initialized
