import * as THREE from "three";
import type { GridData } from "./timeaxis";

export interface VolumeLayout {
  width: number;
  height: number;
  depth: number;
  grid: GridData;
}

/** Opacity of one slice, so that the full stack matches the 64 planes at the same setting. */
export function sliceOpacity(opacity: number, depth: number, planes = 64): number {
  return 1 - Math.pow(1 - opacity, planes / depth);
}

/** The bytes of the volume, whether the server sent them compressed or not. */
export async function gunzip(buffer: ArrayBuffer): Promise<Uint8Array> {
  const bytes = new Uint8Array(buffer);
  // A server may already have removed the compression, as the Vite server does.
  if (bytes[0] !== 0x1f || bytes[1] !== 0x8b) return bytes;
  const stream = new Blob([buffer]).stream().pipeThrough(new DecompressionStream("gzip"));
  return new Uint8Array(await new Response(stream).arrayBuffer());
}

export async function loadVolume(url: string, layout: VolumeLayout): Promise<THREE.Data3DTexture> {
  const response = await fetch(url);
  if (!response.ok) throw new Error("volume introuvable pour ce clip");
  const data = await gunzip(await response.arrayBuffer());
  if (data.length !== layout.width * layout.height * layout.depth * 4) {
    throw new Error("volume de taille inattendue");
  }
  const texture = new THREE.Data3DTexture(data, layout.width, layout.height, layout.depth);
  texture.format = THREE.RGBAFormat;
  texture.type = THREE.UnsignedByteType;
  texture.minFilter = THREE.LinearFilter;
  texture.magFilter = THREE.LinearFilter;
  texture.unpackAlignment = 1;
  texture.needsUpdate = true;
  return texture;
}

const vertexShader = /* glsl */ `
out vec3 vOrigin;
out vec3 vDirection;

void main() {
  vOrigin = (inverse(modelMatrix) * vec4(cameraPosition, 1.0)).xyz;
  vDirection = position - vOrigin;
  gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
}
`;

// Front-to-back compositing along each ray. The texture keeps the colours of the
// video in sRGB, so they reach the screen without conversion.
const fragmentShader = /* glsl */ `
precision highp float;
precision highp sampler3D;

uniform sampler3D volume;
uniform vec3 halfSize;
uniform float steps;
uniform float sliceAlpha;
uniform float sliceLength;
uniform bool useMask;

in vec3 vOrigin;
in vec3 vDirection;
out vec4 color;

vec2 hitBox(vec3 origin, vec3 dir) {
  vec3 inv = 1.0 / dir;
  vec3 a = (-halfSize - origin) * inv;
  vec3 b = (halfSize - origin) * inv;
  vec3 near = min(a, b);
  vec3 far = max(a, b);
  return vec2(max(max(near.x, near.y), near.z), min(min(far.x, far.y), far.z));
}

void main() {
  vec3 dir = normalize(vDirection);
  vec2 hit = hitBox(vOrigin, dir);
  if (hit.x > hit.y) discard;
  hit.x = max(hit.x, 0.0);
  float stepLength = length(2.0 * halfSize) / steps;
  float exponent = stepLength / sliceLength;
  // A random start per pixel turns the bands of a fixed step into fine noise.
  float jitter = fract(sin(dot(gl_FragCoord.xy, vec2(12.9898, 78.233))) * 43758.5453);
  vec4 sum = vec4(0.0);
  for (float t = hit.x + jitter * stepLength; t < hit.y; t += stepLength) {
    vec3 uvw = (vOrigin + t * dir) / (2.0 * halfSize) + 0.5;
    uvw.y = 1.0 - uvw.y;
    vec4 s = texture(volume, uvw);
    float a = 1.0 - pow(1.0 - (useMask ? s.a : 1.0) * sliceAlpha, exponent);
    sum.rgb += (1.0 - sum.a) * a * s.rgb;
    sum.a += (1.0 - sum.a) * a;
    if (sum.a > 0.98) break;
  }
  if (sum.a < 0.002) discard;
  color = vec4(sum.rgb / sum.a, sum.a);
}
`;

export function volumeMaterial(texture: THREE.Data3DTexture): THREE.ShaderMaterial {
  return new THREE.ShaderMaterial({
    glslVersion: THREE.GLSL3,
    uniforms: {
      volume: { value: texture },
      halfSize: { value: new THREE.Vector3(1, 1, 1) },
      steps: { value: 256 },
      sliceAlpha: { value: 0.1 },
      sliceLength: { value: 0.01 },
      useMask: { value: true },
    },
    vertexShader,
    fragmentShader,
    side: THREE.BackSide,
    transparent: true,
    depthWrite: false,
  });
}
