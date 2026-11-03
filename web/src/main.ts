import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { journal, journalErrors } from "./journal";
import { frameStats } from "./measure";
import {
  cellUv,
  colorFromQuery,
  type Layout,
  planeZ,
  renderFromQuery,
  viewFromQuery,
} from "./planes";
import { Grid, type GridData } from "./timeaxis";
import { loadVolume, sliceOpacity, type VolumeLayout, volumeMaterial } from "./volume";

const SCALE = 0.01;
const LENGTH = 6;
const DISTANCE = 9;
const WIDE_ENOUGH = 1.4;
const MEASURE_WARMUP_MS = 2000;
const MEASURE_MS = 10000;
const query = new URLSearchParams(location.search);
const clipName = query.get("clip") ?? import.meta.env.VITE_CLIP ?? "demo";
const base = `${import.meta.env.BASE_URL}clips/${clipName}`;

const canvas = document.querySelector<HTMLCanvasElement>("#scene")!;
const spacingInput = document.querySelector<HTMLInputElement>("#spacing")!;
const opacityInput = document.querySelector<HTMLInputElement>("#opacity")!;
const backgroundInput = document.querySelector<HTMLInputElement>("#background")!;
const viewInputs = document.querySelectorAll<HTMLInputElement>('input[name="view"]');
const renderInputs = document.querySelectorAll<HTMLInputElement>('input[name="render"]');
const axis = document.querySelector<HTMLElement>("#axis")!;
const status = document.querySelector<HTMLElement>("#status")!;

journalErrors();

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

function gpuName(): string {
  const gl = renderer.getContext();
  const info = gl.getExtension("WEBGL_debug_renderer_info");
  return String(gl.getParameter(info ? info.UNMASKED_RENDERER_WEBGL : gl.RENDERER));
}

function seconds(value: number): string {
  return value.toFixed(2).replace(".", ",");
}

/** Spin the camera for a while and report the frame times of the screen. */
function measure(mode: string) {
  const deltas: number[] = [];
  let start = -1;
  let last = -1;
  controls.autoRotate = true;
  controls.autoRotateSpeed = 6;
  status.textContent = "Mesure en cours, ne touche à rien pendant 12 s…";
  return (time: number) => {
    if (start < 0) start = time;
    if (last >= 0 && time - start > MEASURE_WARMUP_MS) deltas.push(time - last);
    last = time;
    if (time - start < MEASURE_WARMUP_MS + MEASURE_MS) return false;
    controls.autoRotate = false;
    const stats = frameStats(deltas);
    const size = renderer.getDrawingBufferSize(new THREE.Vector2());
    const report = { mode, width: size.x, height: size.y, gpu: gpuName(), ...stats };
    console.log(JSON.stringify(report));
    journal({ type: "mesure", clip: clipName, ...report });
    status.textContent =
      `Mesure ${mode}, ${size.x}×${size.y} px : médiane ${stats.median.toFixed(1)} ms, ` +
      `p95 ${stats.p95.toFixed(1)} ms, ${stats.slow} images au-delà de 33 ms sur ${stats.frames}, ` +
      `pause la plus longue ${stats.longest.toFixed(0)} ms.`;
    return true;
  };
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
    depthWrite: false,
    side: THREE.DoubleSide,
  });
  const planes = new THREE.Group();
  for (let i = 0; i < grid.n; i++) {
    planes.add(new THREE.Mesh(planeGeometry(i, grid.n, layout), material));
  }
  scene.add(planes);

  let view = viewFromQuery(query.get("vue"));
  let volume: THREE.Mesh<THREE.BoxGeometry, THREE.ShaderMaterial> | null = null;
  let volumeLayout: VolumeLayout | null = null;
  const length = () => Number(spacingInput.value) * LENGTH;

  const update = () => {
    const opacity = Number(opacityInput.value);
    planes.children.forEach((mesh, i) => {
      mesh.position.z = planeZ(i, grid.n, length() / grid.n);
    });
    material.opacity = opacity;
    material.alphaMap = view === "image" ? null : mask;
    material.needsUpdate = true;
    if (volume && volumeLayout) {
      const size = new THREE.Vector3(
        volumeLayout.width * SCALE,
        volumeLayout.height * SCALE,
        length(),
      );
      volume.geometry.dispose();
      volume.geometry = new THREE.BoxGeometry(size.x, size.y, size.z);
      const uniforms = volume.material.uniforms;
      uniforms.halfSize.value.copy(size).multiplyScalar(0.5);
      uniforms.sliceLength.value = size.z / volumeLayout.depth;
      uniforms.sliceAlpha.value = sliceOpacity(opacity, volumeLayout.depth);
      uniforms.useMask.value = view !== "image";
    }
  };

  const showVolume = async () => {
    if (!volume) {
      status.textContent = "Chargement du volume…";
      const started = performance.now();
      volumeLayout = await json<VolumeLayout>("volume.json");
      const data = await loadVolume(`${base}/volume.bin.gz`, volumeLayout);
      const loadMs = Math.round(performance.now() - started);
      journal({ type: "volume", clip: clipName, depth: volumeLayout.depth, ms: loadMs });
      volume = new THREE.Mesh(new THREE.BoxGeometry(), volumeMaterial(data));
      scene.add(volume);
      const end = seconds(new Grid(volumeLayout.grid).time(volumeLayout.depth - 1));
      status.textContent = `Volume de ${volumeLayout.depth} tranches, de t = 0 à ${end} s.`;
    }
    planes.visible = false;
    volume.visible = true;
    update();
  };

  const showRender = async (mode: string) => {
    if (mode === "volume") {
      await showVolume();
    } else {
      planes.visible = true;
      if (volume) volume.visible = false;
      status.textContent = "";
    }
    for (const input of renderInputs) input.checked = input.value === mode;
  };

  update();
  spacingInput.addEventListener("input", update);
  opacityInput.addEventListener("input", update);
  for (const input of viewInputs) {
    input.checked = input.value === view;
    input.addEventListener("change", () => {
      view = viewFromQuery(input.value);
      update();
    });
  }
  for (const input of renderInputs) {
    input.addEventListener("change", () => {
      showRender(input.value).catch(async (error: Error) => {
        await showRender("plans");
        status.textContent = error.message;
      });
    });
  }

  axis.textContent = `${grid.n} plans, de t = 0 à ${seconds(grid.time(grid.n - 1))} s`;
  const mode = renderFromQuery(query.get("rendu"));
  await showRender(mode).catch(async (error: Error) => {
    journal({ type: "erreur", message: error.message });
    await showRender("plans");
    status.textContent = error.message;
  });

  let measuring = query.get("mesure") === "1" ? measure(mode) : null;
  renderer.setAnimationLoop((time: number) => {
    controls.update();
    renderer.render(scene, camera);
    if (measuring && measuring(time)) measuring = null;
  });
}

window.addEventListener("resize", fit);
fit();
start().catch((error: Error) => {
  journal({ type: "erreur", message: error.message });
  status.textContent = error.message;
});
