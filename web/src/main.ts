import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { cellUv, colorFromQuery, type Layout, planeZ, viewFromQuery } from "./planes";
import { Grid, type GridData } from "./timeaxis";

const SCALE = 0.01;
const DISTANCE = 9;
const WIDE_ENOUGH = 1.4;
const query = new URLSearchParams(location.search);
const clipName = query.get("clip") ?? import.meta.env.VITE_CLIP ?? "demo";
const base = `${import.meta.env.BASE_URL}clips/${clipName}`;

const canvas = document.querySelector<HTMLCanvasElement>("#scene")!;
const spacingInput = document.querySelector<HTMLInputElement>("#spacing")!;
const opacityInput = document.querySelector<HTMLInputElement>("#opacity")!;
const backgroundInput = document.querySelector<HTMLInputElement>("#background")!;
const viewInputs = document.querySelectorAll<HTMLInputElement>('input[name="view"]');
const axis = document.querySelector<HTMLElement>("#axis")!;

const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

const background = new THREE.Color();
const scene = new THREE.Scene();
scene.background = background;

backgroundInput.value = colorFromQuery(query.get("fond"), backgroundInput.value);
background.set(backgroundInput.value);
backgroundInput.addEventListener("input", () => background.set(backgroundInput.value));

const camera = new THREE.PerspectiveCamera(40, 1, 0.1, 100);
camera.position.set(6.2, 2.2, 6.2);

const controls = new OrbitControls(camera, canvas);
controls.enableDamping = true;

async function json<T>(name: string): Promise<T> {
  const response = await fetch(`${base}/${name}`);
  if (!response.ok) throw new Error(`${name} introuvable pour le clip ${clipName}`);
  return response.json() as Promise<T>;
}

function planeGeometry(index: number, count: number, layout: Layout) {
  const geometry = new THREE.PlaneGeometry(layout.width * SCALE, layout.height * SCALE);
  const uv = cellUv(index, count, layout.columns);
  geometry.setAttribute(
    "uv",
    new THREE.Float32BufferAttribute(
      [uv.left, uv.top, uv.right, uv.top, uv.left, uv.bottom, uv.right, uv.bottom],
      2,
    ),
  );
  return geometry;
}

function fit() {
  renderer.setSize(window.innerWidth, window.innerHeight, false);
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  // A narrow screen needs more distance to show the whole length of the stack.
  camera.position.setLength(DISTANCE * Math.max(1, WIDE_ENOUGH / camera.aspect));
}

async function start() {
  const [layout, clip] = await Promise.all([
    json<Layout>("planes.json"),
    json<{ grids: { planes: GridData } }>("clip.json"),
  ]);
  const grid = new Grid(clip.grids.planes);
  const loader = new THREE.TextureLoader();
  const [texture, mask] = await Promise.all([
    loader.loadAsync(`${base}/atlas.webp`),
    loader.loadAsync(`${base}/mask.webp`),
  ]);
  texture.colorSpace = THREE.SRGBColorSpace;
  for (const image of [texture, mask]) {
    image.generateMipmaps = false;
    image.minFilter = THREE.LinearFilter;
  }

  const material = new THREE.MeshBasicMaterial({
    map: texture,
    transparent: true,
    opacity: Number(opacityInput.value),
    depthWrite: false,
    side: THREE.DoubleSide,
  });
  const planes = Array.from({ length: grid.n }, (_, i) => {
    const mesh = new THREE.Mesh(planeGeometry(i, grid.n, layout), material);
    scene.add(mesh);
    return mesh;
  });

  const place = () => {
    const spacing = (Number(spacingInput.value) * 6) / grid.n;
    planes.forEach((mesh, i) => {
      mesh.position.z = planeZ(i, grid.n, spacing);
    });
  };
  place();
  spacingInput.addEventListener("input", place);
  opacityInput.addEventListener("input", () => {
    material.opacity = Number(opacityInput.value);
  });

  const showView = (view: string) => {
    material.alphaMap = view === "image" ? null : mask;
    material.needsUpdate = true;
  };
  const firstView = viewFromQuery(query.get("vue"));
  showView(firstView);
  for (const input of viewInputs) {
    input.checked = input.value === firstView;
    input.addEventListener("change", () => showView(input.value));
  }

  const end = grid.time(grid.n - 1).toFixed(2).replace(".", ",");
  axis.textContent = `${grid.n} plans, de t = 0 à ${end} s`;

  renderer.setAnimationLoop(() => {
    controls.update();
    renderer.render(scene, camera);
  });
}

window.addEventListener("resize", fit);
fit();
start().catch((error: Error) => {
  axis.textContent = error.message;
});
