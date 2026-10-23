// 3D: a three.js scene drawn as a function of time, composited onto the 2D stage. Build the scene once; in draw(g, t)
// set every object, light and the camera from t (no clocks, no animation mixers that keep state between frames), then
// L.draw(g): the scene renders into its own WebGL canvas and lands on the stage, and type and overlays go on top
// with the usual 2D calls (L.toScreen pins them to points in the world). three.js (MIT) lives in kit/vendor/three/,
// copied into the film by `moodreel film new` for a style that needs 3D.
import * as THREE from './vendor/three/three.module.js';

export { THREE };

export function layer3d(width, height, { background = null, antialias = true, shadows = false, exposure = 1,
  fov = 35, near = 0.1, far = 1000, toneMapping = 'aces' } = {}) {
  const canvas = document.createElement('canvas');
  const renderer = new THREE.WebGLRenderer({ canvas, antialias, preserveDrawingBuffer: true, alpha: background === null });
  renderer.setPixelRatio(1);
  renderer.setSize(width, height, false);
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = { aces: THREE.ACESFilmicToneMapping, agx: THREE.AgXToneMapping, neutral: THREE.NeutralToneMapping,
    none: THREE.NoToneMapping }[toneMapping];
  renderer.toneMappingExposure = exposure;
  if (shadows) {
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  }
  const scene = new THREE.Scene();
  if (background) scene.background = new THREE.Color(background);
  const camera = new THREE.PerspectiveCamera(fov, width / height, near, far);
  const L = {
    THREE, renderer, scene, camera, canvas,
    // render the scene and put it on the stage (or in a box on it)
    draw(g, x = 0, y = 0, w = width, h = height) {
      renderer.render(scene, camera);
      g.drawImage(canvas, x, y, w, h);
    },
    // the camera at `eye`, looking at `target`
    look(eye, target = [0, 0, 0], up = [0, 1, 0]) {
      camera.position.set(...eye);
      camera.up.set(...up);
      camera.lookAt(...target);
      camera.updateMatrixWorld();
    },
    // where a point in the world falls on the stage, in px, and whether it is in front of the camera
    toScreen(p) {
      const v = new THREE.Vector3(...(Array.isArray(p) ? p : [p.x, p.y, p.z])).project(camera);
      return [((v.x + 1) / 2) * width, ((1 - v.y) / 2) * height, v.z < 1];
    },
  };
  return L;
}

// a point at `radius` around `target`, `angle` radians round (0 = in front, +z) and `height` above it: for an orbit
export const orbit = (angle, radius, height = 0, target = [0, 0, 0]) =>
  [target[0] + radius * Math.sin(angle), target[1] + height, target[2] + radius * Math.cos(angle)];
