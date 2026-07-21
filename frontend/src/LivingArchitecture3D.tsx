import { useEffect, useMemo, useRef, useState } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import type { State } from './types';

type Props = {
  state: State;
  selectedId: string | null;
  onSelect: (id: string) => void;
};

type Runtime = {
  renderer: THREE.WebGLRenderer;
  scene: THREE.Scene;
  camera: THREE.PerspectiveCamera;
  controls: OrbitControls;
  content: THREE.Group;
  selectable: THREE.Object3D[];
  organismObjects: Map<string, THREE.Object3D>;
  firstSeen: Map<string, number>;
  activeMorph: { id: string; bornAt: number } | null;
  lastStep: number;
  reducedMotion: boolean;
  observer: ResizeObserver;
  frame: number;
  dispose: () => void;
};

const WORLD_SCALE = 0.72;
const MICRO_Y = -2.55;
const ORGANISM_Y = 0;
const MEMORY_Y = 2.75;
const MORPH_DURATION = 6200;

function clamp01(value: number) {
  return Math.max(0, Math.min(1, value));
}

function smooth01(value: number) {
  const t = clamp01(value);
  return t * t * (3 - 2 * t);
}

function morphPhase(now: number, bornAt: number, start: number, end: number) {
  return smooth01((now - bornAt - start) / Math.max(1, end - start));
}

function hashUnit(value: string, salt = 0) {
  let hash = 2166136261 ^ salt;
  for (let index = 0; index < value.length; index += 1) {
    hash ^= value.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }
  return ((hash >>> 0) % 100000) / 100000;
}

function worldPosition(x: number, y: number, vertical = ORGANISM_Y) {
  const projectAxis = (value: number) => {
    const centered = value - 50;
    return Math.sign(centered) * Math.sqrt(Math.abs(centered)) * WORLD_SCALE;
  };
  return new THREE.Vector3(projectAxis(x), vertical, projectAxis(y));
}

function addLine(
  parent: THREE.Object3D,
  points: THREE.Vector3[],
  color: THREE.ColorRepresentation,
  opacity: number,
) {
  if (points.length < 2) return null;
  const geometry = new THREE.BufferGeometry().setFromPoints(points);
  const material = new THREE.LineBasicMaterial({ color, transparent: true, opacity, depthWrite: false });
  const line = new THREE.Line(geometry, material);
  parent.add(line);
  return line;
}

function createDnaHelix(color: THREE.ColorRepresentation, bornAt: number) {
  const dna = new THREE.Group();
  dna.userData = { kind: 'dna', bornAt, baseScale: 1 };
  const strandA: THREE.Vector3[] = [];
  const strandB: THREE.Vector3[] = [];
  const turns = 26;
  for (let index = 0; index < turns; index += 1) {
    const progress = index / (turns - 1);
    const angle = progress * Math.PI * 4.2;
    const y = (progress - 0.5) * 0.72;
    strandA.push(new THREE.Vector3(Math.cos(angle) * 0.12, y, Math.sin(angle) * 0.12));
    strandB.push(new THREE.Vector3(Math.cos(angle + Math.PI) * 0.12, y, Math.sin(angle + Math.PI) * 0.12));
  }
  addLine(dna, strandA, color, 0.92);
  addLine(dna, strandB, 0xd8f9ff, 0.82);
  for (let index = 1; index < turns - 1; index += 3) {
    addLine(dna, [strandA[index], strandB[index]], color, 0.42);
  }
  dna.traverse((object) => {
    if (object instanceof THREE.Line) {
      object.userData.targetOpacity = (object.material as THREE.LineBasicMaterial).opacity;
    }
  });
  return dna;
}

function organicGeometry(radius: number, seed: string, detail = 2) {
  const geometry = new THREE.IcosahedronGeometry(radius, detail);
  const positions = geometry.attributes.position as THREE.BufferAttribute;
  const vertex = new THREE.Vector3();
  for (let index = 0; index < positions.count; index += 1) {
    vertex.fromBufferAttribute(positions, index);
    const variation = 0.84 + hashUnit(`${seed}:${index}`, 57) * 0.28;
    vertex.multiplyScalar(variation);
    positions.setXYZ(index, vertex.x, vertex.y, vertex.z);
  }
  positions.needsUpdate = true;
  geometry.computeVertexNormals();
  return geometry;
}

function tissueSegment(
  parent: THREE.Object3D,
  start: THREE.Vector3,
  end: THREE.Vector3,
  color: THREE.ColorRepresentation,
  opacity: number,
  bornAt: number,
  seed: string,
) {
  const direction = end.clone().sub(start);
  const midpoint = start.clone().add(end).multiplyScalar(0.5);
  const normal = direction.clone().cross(new THREE.Vector3(0, 1, 0));
  if (normal.lengthSq() < 0.001) normal.set(1, 0, 0);
  normal.normalize().multiplyScalar(0.08 + hashUnit(seed, 67) * 0.13);
  const control = midpoint.clone().add(normal);
  const curve = new THREE.QuadraticBezierCurve3(start, control, end);
  const segmentCount = 5;
  for (let index = 0; index < segmentCount; index += 1) {
    const segmentStart = curve.getPoint(index / segmentCount);
    const segmentEnd = curve.getPoint((index + 1) / segmentCount);
    const segmentDirection = segmentEnd.clone().sub(segmentStart);
    const length = Math.max(0.001, segmentDirection.length());
    const segmentMidpoint = segmentStart.clone().add(segmentEnd).multiplyScalar(0.5);
    const mesh = new THREE.Mesh(
      new THREE.CylinderGeometry(0.014, 0.03, length, 7, 1, true),
      new THREE.MeshStandardMaterial({
        color,
        emissive: color,
        emissiveIntensity: 0.75,
        roughness: 0.42,
        transparent: true,
        opacity,
        depthWrite: false,
      }),
    );
    mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), segmentDirection.normalize());
    mesh.position.copy(segmentStart);
    mesh.scale.set(1, 0.001, 1);
    mesh.userData = {
      kind: 'tissue',
      bornAt: bornAt + index * 95,
      startPosition: segmentStart,
      targetPosition: segmentMidpoint,
      targetOpacity: opacity,
    };
    parent.add(mesh);
  }
  return curve;
}

function textSprite(text: string, color = '#dff8ff') {
  const canvas = document.createElement('canvas');
  canvas.width = 384;
  canvas.height = 72;
  const context = canvas.getContext('2d');
  if (!context) return new THREE.Sprite();
  context.clearRect(0, 0, canvas.width, canvas.height);
  context.fillStyle = 'rgba(3, 11, 20, .78)';
  context.beginPath();
  context.roundRect(4, 7, 376, 58, 18);
  context.fill();
  context.strokeStyle = `${color}66`;
  context.lineWidth = 2;
  context.stroke();
  context.fillStyle = color;
  context.font = '500 24px DM Mono, monospace';
  context.textAlign = 'center';
  context.textBaseline = 'middle';
  context.fillText(text, 192, 36);
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.minFilter = THREE.LinearFilter;
  const material = new THREE.SpriteMaterial({ map: texture, transparent: true, depthWrite: false });
  const sprite = new THREE.Sprite(material);
  sprite.scale.set(3.2, 0.6, 1);
  return sprite;
}

function disposeTree(root: THREE.Object3D) {
  root.traverse((object) => {
    const mesh = object as THREE.Mesh;
    mesh.geometry?.dispose();
    const materials = mesh.material ? (Array.isArray(mesh.material) ? mesh.material : [mesh.material]) : [];
    materials.forEach((material) => {
      const spriteMaterial = material as THREE.SpriteMaterial;
      spriteMaterial.map?.dispose();
      material.dispose();
    });
  });
}

function createStaticField(scene: THREE.Scene) {
  const field = new THREE.Group();
  scene.add(field);

  const grid = new THREE.GridHelper(22, 22, 0x2d8bac, 0x16374b);
  grid.position.y = -3.18;
  const gridMaterials = Array.isArray(grid.material) ? grid.material : [grid.material];
  gridMaterials.forEach((material) => {
    material.transparent = true;
    material.opacity = 0.17;
  });
  field.add(grid);

  [
    { y: MICRO_Y, radius: 6.8, color: 0xffb45c },
    { y: ORGANISM_Y, radius: 7.7, color: 0x64d9ff },
    { y: MEMORY_Y, radius: 5.3, color: 0x76e7ad },
  ].forEach((layer) => {
    const ring = new THREE.Mesh(
      new THREE.RingGeometry(layer.radius - 0.025, layer.radius, 128),
      new THREE.MeshBasicMaterial({ color: layer.color, transparent: true, opacity: 0.15, side: THREE.DoubleSide, depthWrite: false }),
    );
    ring.rotation.x = -Math.PI / 2;
    ring.position.y = layer.y;
    field.add(ring);
  });

  const starGeometry = new THREE.BufferGeometry();
  const starPositions: number[] = [];
  for (let index = 0; index < 280; index += 1) {
    const radius = 6 + hashUnit(`star-${index}`, 1) * 17;
    const angle = hashUnit(`star-${index}`, 2) * Math.PI * 2;
    starPositions.push(
      Math.cos(angle) * radius,
      -4 + hashUnit(`star-${index}`, 3) * 13,
      Math.sin(angle) * radius,
    );
  }
  starGeometry.setAttribute('position', new THREE.Float32BufferAttribute(starPositions, 3));
  const stars = new THREE.Points(
    starGeometry,
    new THREE.PointsMaterial({ color: 0x8cdfff, size: 0.035, transparent: true, opacity: 0.42, depthWrite: false }),
  );
  field.add(stars);
  return field;
}

export function LivingArchitecture3D({ state, selectedId, onSelect }: Props) {
  const hostRef = useRef<HTMLDivElement>(null);
  const stageRef = useRef<HTMLDivElement>(null);
  const morphRef = useRef<HTMLDivElement>(null);
  const runtimeRef = useRef<Runtime | null>(null);
  const [autoOrbit, setAutoOrbit] = useState(
    () => !window.matchMedia('(prefers-reduced-motion: reduce)').matches,
  );
  const [webglError, setWebglError] = useState(false);

  const selected = useMemo(
    () => state.organisms.find((organism) => organism.id === selectedId) ?? null,
    [state.organisms, selectedId],
  );
  const selectedCells = selected
    ? state.cells.filter((cell) => cell.organism_id === selected.id).length
    : 0;
  const selectedAffinities = selected?.microAffinities ?? {};
  const strongestAffinity = Math.max(0, ...Object.values(selectedAffinities));
  const meaningfulAffinity = Math.max(0.015, strongestAffinity * 0.35);
  const selectedMicroIds = new Set(
    Object.entries(selectedAffinities)
      .filter(([, affinity]) => affinity >= meaningfulAffinity)
      .map(([microId]) => microId),
  );

  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;
    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' });
    } catch {
      setWebglError(true);
      return;
    }
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.75));
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.18;
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.domElement.className = 'architecture-webgl';
    renderer.domElement.setAttribute('aria-label', 'Interactive three-dimensional self-organizing learning habitat');
    host.appendChild(renderer.domElement);

    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x030a13, 0.038);
    createStaticField(scene);
    const content = new THREE.Group();
    scene.add(content);

    const camera = new THREE.PerspectiveCamera(44, 1, 0.1, 70);
    camera.position.set(9.8, 7.1, 11.2);
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.055;
    controls.minDistance = 5;
    controls.maxDistance = 32;
    controls.maxPolarAngle = Math.PI * 0.78;
    controls.target.set(0, 0.1, 0);
    controls.autoRotate = true;
    controls.autoRotateSpeed = 0.38;

    scene.add(new THREE.HemisphereLight(0x8bdfff, 0x07101b, 1.65));
    const keyLight = new THREE.DirectionalLight(0xd9f7ff, 2.8);
    keyLight.position.set(7, 12, 8);
    keyLight.castShadow = true;
    scene.add(keyLight);
    const cyanLight = new THREE.PointLight(0x44d7ff, 18, 22, 2);
    cyanLight.position.set(-5, 2.5, 5);
    scene.add(cyanLight);
    const violetLight = new THREE.PointLight(0x9c78ff, 13, 18, 2);
    violetLight.position.set(6, 1, -5);
    scene.add(violetLight);
    const amberLight = new THREE.PointLight(0xffa84f, 10, 15, 2);
    amberLight.position.set(0, -2.2, 1);
    scene.add(amberLight);

    const resize = () => {
      const box = host.getBoundingClientRect();
      const width = Math.max(1, box.width);
      const height = Math.max(1, box.height);
      renderer.setSize(width, height, false);
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
    };
    const observer = new ResizeObserver(resize);
    observer.observe(host);
    resize();

    const raycaster = new THREE.Raycaster();
    const pointer = new THREE.Vector2();
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    let pointerStart = { x: 0, y: 0 };
    const pointerDown = (event: PointerEvent) => {
      pointerStart = { x: event.clientX, y: event.clientY };
    };
    const pointerUp = (event: PointerEvent) => {
      if (Math.hypot(event.clientX - pointerStart.x, event.clientY - pointerStart.y) > 5) return;
      const box = renderer.domElement.getBoundingClientRect();
      pointer.x = ((event.clientX - box.left) / box.width) * 2 - 1;
      pointer.y = -((event.clientY - box.top) / box.height) * 2 + 1;
      raycaster.setFromCamera(pointer, camera);
      const hit = raycaster.intersectObjects(runtimeRef.current?.selectable ?? [], true)[0];
      const organismId = hit?.object.userData.organismId as string | undefined;
      if (organismId) onSelect(organismId);
    };
    renderer.domElement.addEventListener('pointerdown', pointerDown);
    renderer.domElement.addEventListener('pointerup', pointerUp);

    const clock = new THREE.Clock();
    const animate = () => {
      const elapsed = clock.getElapsedTime();
      const now = performance.now();
      content.traverse((object) => {
        const birthNow = reducedMotion && object.userData.bornAt
          ? object.userData.bornAt + MORPH_DURATION + 1
          : now;
        if (object.userData.kind === 'organism') {
          const emergence = morphPhase(birthNow, object.userData.bornAt, 350, 4300);
          const float = reducedMotion ? 0 : Math.sin(elapsed * 0.7 + object.userData.phase) * 0.075;
          object.position.y = THREE.MathUtils.lerp(MICRO_Y + 0.35, object.userData.baseY, emergence) + float;
        } else if (object.userData.kind === 'dna') {
          const seed = morphPhase(birthNow, object.userData.bornAt, 0, 900);
          const settle = morphPhase(birthNow, object.userData.bornAt, 3900, 6100);
          object.scale.setScalar(Math.max(0.001, seed * (1.15 - settle * 0.28)));
          if (!reducedMotion) object.rotation.y = elapsed * (settle > 0.9 ? 0.35 : 1.25) + object.userData.phase;
          object.traverse((child) => {
            if (!(child instanceof THREE.Line)) return;
            const material = child.material as THREE.LineBasicMaterial;
            material.opacity = child.userData.targetOpacity * seed * (1 - settle * 0.62);
          });
        } else if (object.userData.kind === 'cell') {
          const budding = morphPhase(birthNow, object.userData.bornAt, 750, 2350);
          object.position.lerpVectors(object.userData.startPosition, object.userData.targetPosition, budding);
          const pulseDepth = 0.025 + object.userData.activation * 0.055;
          const pulse = reducedMotion ? 1 : 1 + Math.sin(elapsed * 2.2 + object.userData.phase) * pulseDepth;
          object.scale.setScalar(Math.max(0.001, budding * pulse));
          if (!reducedMotion) object.rotation.y = elapsed * 0.18 + object.userData.phase * 0.12;
        } else if (object.userData.kind === 'tissue') {
          const weaving = morphPhase(birthNow, object.userData.bornAt, 1550, 3450);
          object.position.lerpVectors(object.userData.startPosition, object.userData.targetPosition, weaving);
          object.scale.set(1, Math.max(0.001, weaving), 1);
          const material = (object as THREE.Mesh).material as THREE.MeshStandardMaterial;
          material.opacity = object.userData.targetOpacity * weaving;
        } else if (object.userData.kind === 'membrane') {
          const forming = morphPhase(birthNow, object.userData.bornAt, 3300, 5500);
          const targetScale = object.userData.targetScale as THREE.Vector3 | undefined;
          if (targetScale) object.scale.copy(targetScale).multiplyScalar(Math.max(0.001, forming));
          else object.scale.setScalar(Math.max(0.001, forming));
          const material = (object as THREE.Mesh).material as THREE.Material & { opacity: number };
          material.opacity = object.userData.targetOpacity * forming;
          if (!reducedMotion) object.rotation.y = elapsed * 0.12 + object.userData.phase;
        } else if (object.userData.kind === 'signal') {
          const connected = morphPhase(birthNow, object.userData.bornAt, 1900, 3500);
          const travel = reducedMotion
            ? 1
            : (elapsed * object.userData.speed + object.userData.phase) % 1;
          object.position.copy(object.userData.curve.getPoint(travel));
          const pulse = reducedMotion ? 1 : 0.72 + Math.sin(elapsed * 7 + object.userData.phase) * 0.28;
          object.scale.setScalar(Math.max(0.001, connected * pulse));
        } else if (object.userData.kind === 'colony') {
          const cooperation = morphPhase(birthNow, object.userData.bornAt, 700, 3100);
          object.scale.copy(object.userData.targetScale).multiplyScalar(Math.max(0.001, cooperation));
          const material = (object as THREE.Mesh).material as THREE.MeshBasicMaterial;
          material.opacity = object.userData.targetOpacity * cooperation;
        } else if (object.userData.kind === 'memory') {
          const consolidation = morphPhase(birthNow, object.userData.bornAt, 300, 1900);
          const pulse = reducedMotion ? 1 : 0.86 + Math.sin(elapsed * 1.8 + object.userData.phase) * 0.14;
          object.scale.setScalar(Math.max(0.001, consolidation * pulse));
          if (!reducedMotion) {
            object.position.y = object.userData.baseY + Math.sin(elapsed * object.userData.speed + object.userData.phase) * 0.08;
            object.rotation.y = elapsed * 0.22 + object.userData.phase;
          }
        } else if (object.userData.kind === 'information' && !reducedMotion) {
          object.rotation.x = elapsed * 0.9 + object.userData.phase;
          object.rotation.y = elapsed * 1.2;
          const pulse = 0.86 + Math.sin(elapsed * 3 + object.userData.phase) * 0.14;
          object.scale.setScalar(pulse);
        } else if (object.userData.kind === 'active-micro' && !reducedMotion) {
          const pulse = 0.82 + Math.sin(elapsed * 4.2 + object.userData.phase) * 0.24;
          object.scale.setScalar(pulse);
        } else if (object.userData.kind === 'related-micro' && !reducedMotion) {
          const pulse = 1 + Math.sin(elapsed * 2.4 + object.userData.phase) * (0.04 + object.userData.affinity * 0.08);
          object.scale.setScalar(pulse);
        }
      });
      const activeMorph = runtimeRef.current?.activeMorph;
      const morphElement = morphRef.current;
      if (activeMorph && morphElement) {
        const age = reducedMotion ? MORPH_DURATION : now - activeMorph.bornAt;
        let phase = 'MATURE ADAPTIVE TISSUE';
        if (age < 1150) phase = 'DNA SEED EXPRESSION';
        else if (age < 2700) phase = 'CELL BUDDING';
        else if (age < 4250) phase = 'TISSUE WEAVING';
        else if (age < MORPH_DURATION) phase = 'MEMBRANE FORMATION';
        morphElement.dataset.phase = age < MORPH_DURATION ? 'growing' : 'mature';
        const progress = Math.round(clamp01(age / MORPH_DURATION) * 100);
        const phaseElement = morphElement.querySelector('b');
        const detailElement = morphElement.querySelector('small');
        if (phaseElement) phaseElement.textContent = phase;
        if (detailElement) detailElement.textContent = `${activeMorph.id} · ${progress}% morphogenesis`;
      }
      controls.update();
      renderer.render(scene, camera);
      if (runtimeRef.current) runtimeRef.current.frame = requestAnimationFrame(animate);
    };

    runtimeRef.current = {
      renderer,
      scene,
      camera,
      controls,
      content,
      selectable: [],
      organismObjects: new Map(),
      firstSeen: new Map(),
      activeMorph: null,
      lastStep: 0,
      reducedMotion,
      observer,
      frame: requestAnimationFrame(animate),
      dispose: () => {
        renderer.domElement.removeEventListener('pointerdown', pointerDown);
        renderer.domElement.removeEventListener('pointerup', pointerUp);
        observer.disconnect();
        controls.dispose();
        cancelAnimationFrame(runtimeRef.current?.frame ?? 0);
        disposeTree(scene);
        renderer.dispose();
        renderer.domElement.remove();
      },
    };

    return () => {
      runtimeRef.current?.dispose();
      runtimeRef.current = null;
    };
  }, [onSelect]);

  useEffect(() => {
    const runtime = runtimeRef.current;
    if (!runtime) return;
    runtime.controls.autoRotate = autoOrbit;
  }, [autoOrbit]);

  useEffect(() => {
    const runtime = runtimeRef.current;
    if (!runtime) return;
    if (state.stepCount < runtime.lastStep) {
      runtime.firstSeen.clear();
      runtime.activeMorph = null;
    }
    runtime.lastStep = state.stepCount;
    const snapshotNow = performance.now();
    const firstSeen = (key: string, stagger = 0) => {
      const existing = runtime.firstSeen.get(key);
      if (existing !== undefined) return existing;
      const bornAt = snapshotNow + stagger;
      runtime.firstSeen.set(key, bornAt);
      return bornAt;
    };
    const { content } = runtime;
    disposeTree(content);
    content.clear();
    runtime.selectable = [];
    runtime.organismObjects = new Map();

    const lastPatch = state.informationPatches[state.informationPatches.length - 1];
    const activeMicroIds = new Set(lastPatch?.microActivations ?? []);
    const microPositions = new Map<string, THREE.Vector3>();
    const selectedColor = selected?.color ?? '#64d9ff';

    state.microSignatures.forEach((micro, index) => {
      const colonyIndex = micro.colonyId
        ? Math.max(0, state.microColonies.findIndex((colony) => colony.id === micro.colonyId))
        : index;
      const sector = hashUnit(micro.colonyId ?? micro.id, 9) * Math.PI * 2;
      const angle = sector + hashUnit(micro.id, 3) * 1.35;
      const radius = 1.15 + (colonyIndex % 4) * 1.15 + hashUnit(micro.id, 4) * 1.1;
      const position = new THREE.Vector3(
        Math.cos(angle) * radius,
        MICRO_Y + (hashUnit(micro.id, 5) - 0.5) * 0.38,
        Math.sin(angle) * radius,
      );
      microPositions.set(micro.id, position);
      const active = activeMicroIds.has(micro.id);
      const affinity = selectedAffinities[micro.id] ?? 0;
      const related = selectedMicroIds.has(micro.id);
      const dimmed = Boolean(selected) && !related;
      const radiusValue = 0.055
        + Math.min(0.11, Math.log2(2 + micro.observations) * 0.012)
        + (related ? affinity * 0.09 : 0);
      const mesh = new THREE.Mesh(
        new THREE.IcosahedronGeometry(radiusValue, 1),
        new THREE.MeshStandardMaterial({
          color: related ? selectedColor : active ? 0xffe1a3 : 0xffa84f,
          emissive: related ? selectedColor : active ? 0xff9f2d : 0x7d3208,
          emissiveIntensity: active && related ? 4.4 : active ? 3.2 : related ? 2.2 + affinity * 2.4 : 0.8,
          roughness: 0.35,
          transparent: true,
          opacity: dimmed ? 0.11 : 0.45 + Math.min(0.45, micro.energy * 0.3),
        }),
      );
      mesh.position.copy(position);
      if (active) {
        mesh.userData = { kind: 'active-micro', phase: index * 0.7 };
      } else if (related) {
        mesh.userData = { kind: 'related-micro', phase: index * 0.7, affinity };
      }
      content.add(mesh);
    });

    state.microColonies.forEach((colony) => {
      const points = colony.member_ids.map((id) => microPositions.get(id)).filter(Boolean) as THREE.Vector3[];
      if (points.length < 2) return;
      const closedPoints = [...points, points[0]];
      addLine(content, closedPoints, 0xffb45c, 0.24 + colony.stability * 0.38);
    });

    const organismPositions = new Map<string, THREE.Vector3>();
    state.organisms.forEach((organism, organismIndex) => {
      const organismKey = `organism:${organism.id}`;
      const isNewOrganism = !runtime.firstSeen.has(organismKey);
      const organismBornAt = firstSeen(organismKey, Math.min(organismIndex, 18) * 110);
      if (
        isNewOrganism
        && (!runtime.activeMorph || snapshotNow - runtime.activeMorph.bornAt > MORPH_DURATION)
      ) runtime.activeMorph = { id: organism.id, bornAt: organismBornAt };

      const group = new THREE.Group();
      const basePosition = worldPosition(organism.x, organism.y, ORGANISM_Y + (hashUnit(organism.id, 6) - 0.5) * 0.75);
      group.position.copy(basePosition);
      group.userData = {
        kind: 'organism',
        bornAt: organismBornAt,
        baseY: basePosition.y,
        phase: organismIndex * 1.71,
      };
      organismPositions.set(organism.id, basePosition.clone());
      runtime.organismObjects.set(organism.id, group);

      const organismCells = state.cells.filter((cell) => cell.organism_id === organism.id);
      const cellCount = Math.max(1, organismCells.length);
      const dormant = organism.lifecycleState === 'dormant';
      const color = new THREE.Color(organism.color);
      const dna = createDnaHelix(color, organismBornAt);
      dna.userData.phase = hashUnit(organism.lineage, 31) * Math.PI * 2;
      dna.userData.organismId = organism.id;
      group.add(dna);

      const attachmentPoints: THREE.Vector3[] = [];
      organismCells.forEach((cell, cellIndex) => {
        const parentIndex = cellIndex === 0 ? 0 : Math.floor((cellIndex - 1) / 2);
        const parentPosition = attachmentPoints[parentIndex] ?? new THREE.Vector3();
        const angle = hashUnit(cell.id, 8) * Math.PI * 2 + organism.heading;
        const vertical = (hashUnit(cell.id, 18) - 0.43) * 1.15;
        const direction = new THREE.Vector3(Math.cos(angle), vertical, Math.sin(angle)).normalize();
        const branchLength = cellIndex === 0
          ? 0
          : 0.34 + hashUnit(cell.id, 28) * 0.31 + Math.min(0.2, Math.sqrt(cellIndex) * 0.023);
        const cellPosition = cellIndex === 0
          ? new THREE.Vector3()
          : parentPosition.clone().add(direction.multiplyScalar(branchLength));
        attachmentPoints.push(cellPosition);

        const cellBornAt = firstSeen(`cell:${organism.id}:${cell.id}`, Math.min(cellIndex, 26) * 92);
        const cellRadius = 0.09 + Math.min(0.058, cell.activation * 0.06) + Math.min(0.02, cell.energy * 0.009);
        const cellGroup = new THREE.Group();
        cellGroup.position.copy(parentPosition);
        cellGroup.scale.setScalar(0.001);
        cellGroup.userData = {
          kind: 'cell',
          organismId: organism.id,
          bornAt: cellBornAt,
          startPosition: parentPosition.clone(),
          targetPosition: cellPosition.clone(),
          activation: cell.activation,
          phase: hashUnit(cell.id, 38) * Math.PI * 2,
        };

        const cellShell = new THREE.Mesh(
          organicGeometry(cellRadius, cell.id, 2),
          new THREE.MeshPhysicalMaterial({
            color,
            emissive: color,
            emissiveIntensity: 0.18 + cell.activation * 0.55,
            roughness: 0.16,
            clearcoat: 0.9,
            clearcoatRoughness: 0.22,
            transmission: dormant ? 0.05 : 0.22,
            thickness: 0.18,
            transparent: true,
            opacity: dormant ? 0.12 : 0.34,
            depthWrite: false,
            side: THREE.DoubleSide,
          }),
        );
        cellShell.userData.organismId = organism.id;
        cellGroup.add(cellShell);
        runtime.selectable.push(cellShell);

        const nucleus = new THREE.Mesh(
          organicGeometry(cellRadius * 0.38, `${cell.id}:nucleus`, 1),
          new THREE.MeshStandardMaterial({
            color: 0xeaffff,
            emissive: color,
            emissiveIntensity: 1.5 + cell.activation * 3.2,
            roughness: 0.32,
            transparent: true,
            opacity: dormant ? 0.35 : 0.92,
          }),
        );
        nucleus.userData.organismId = organism.id;
        cellGroup.add(nucleus);
        runtime.selectable.push(nucleus);

        const cytoplasm = new THREE.Mesh(
          new THREE.SphereGeometry(cellRadius * 1.5, 12, 8),
          new THREE.MeshBasicMaterial({
            color,
            transparent: true,
            opacity: dormant ? 0.012 : 0.045,
            blending: THREE.AdditiveBlending,
            depthWrite: false,
          }),
        );
        cellGroup.add(cytoplasm);
        group.add(cellGroup);
        if (cellIndex > 0) {
          const tissueCurve = tissueSegment(
            group,
            parentPosition,
            cellPosition,
            color,
            dormant ? 0.1 : 0.3 + cell.activation * 0.24,
            cellBornAt,
            cell.id,
          );
          const signal = new THREE.Mesh(
            new THREE.SphereGeometry(0.018 + cell.activation * 0.012, 8, 6),
            new THREE.MeshStandardMaterial({
              color: 0xf0ffff,
              emissive: color,
              emissiveIntensity: 4 + cell.activation * 4,
              transparent: true,
              opacity: dormant ? 0.18 : 0.92,
              depthWrite: false,
            }),
          );
          signal.userData = {
            kind: 'signal',
            bornAt: cellBornAt,
            curve: tissueCurve,
            speed: 0.22 + cell.activation * 0.42,
            phase: hashUnit(cell.id, 78),
          };
          group.add(signal);
        }
      });

      const tissueRadius = Math.max(0.34, ...attachmentPoints.map((point) => point.length()));
      if (organismCells.length >= 3) {
        const membraneOpacity = dormant ? 0.035 : 0.085;
        const membrane = new THREE.Mesh(
          organicGeometry(tissueRadius + 0.2, `${organism.id}:membrane`, 3),
          new THREE.MeshPhysicalMaterial({
            color,
            emissive: color,
            emissiveIntensity: 0.12,
            roughness: 0.18,
            clearcoat: 0.75,
            transmission: 0.35,
            thickness: 0.25,
            transparent: true,
            opacity: 0,
            depthWrite: false,
            side: THREE.DoubleSide,
          }),
        );
        membrane.scale.setScalar(0.001);
        membrane.userData = {
          kind: 'membrane',
          organismId: organism.id,
          bornAt: organismBornAt,
          targetOpacity: membraneOpacity,
          targetScale: new THREE.Vector3(
            0.88 + hashUnit(organism.id, 81) * 0.22,
            0.72 + hashUnit(organism.id, 82) * 0.2,
            0.86 + hashUnit(organism.id, 83) * 0.25,
          ),
          phase: hashUnit(organism.id, 48) * Math.PI,
        };
        group.add(membrane);
        runtime.selectable.push(membrane);
      }

      if (selectedId === organism.id) {
        const selection = new THREE.Mesh(
          new THREE.TorusGeometry(tissueRadius + 0.42, 0.025, 8, 64),
          new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.95 }),
        );
        selection.rotation.x = Math.PI / 2;
        group.add(selection);
      }

      if (selectedId === organism.id) {
        const label = textSprite(`${organism.id}  ·  ${cellCount} cells`, organism.color);
        label.position.set(0, tissueRadius + 0.62, 0);
        label.scale.multiplyScalar(1.04);
        group.add(label);
      }
      content.add(group);
    });

    if (selected) {
      const organismPosition = organismPositions.get(selected.id);
      if (organismPosition) {
        selectedMicroIds.forEach((microId) => {
          const microPosition = microPositions.get(microId);
          if (!microPosition) return;
          const affinity = selectedAffinities[microId] ?? 0;
          addLine(
            content,
            [microPosition, organismPosition],
            selectedColor,
            0.08 + Math.min(0.42, affinity * 0.72),
          );
        });
      }
    }

    state.colonies.forEach((colony, colonyIndex) => {
      const colonyBornAt = firstSeen(`colony:${colony.id}`);
      const members = colony.member_ids.map((id) => organismPositions.get(id)).filter(Boolean) as THREE.Vector3[];
      if (members.length < 2) return;
      const center = members.reduce((sum, point) => sum.add(point), new THREE.Vector3()).multiplyScalar(1 / members.length);
      const maxDistance = Math.max(...members.map((point) => point.distanceTo(center)));
      addLine(content, [...members, members[0]], 0xb791ff, 0.52);
      members.forEach((member) => addLine(content, [center, member], 0xb791ff, 0.22));
      const ring = new THREE.Mesh(
        new THREE.TorusGeometry(Math.max(0.65, maxDistance + 0.42), 0.018 + colony.synergy * 0.08, 8, 96),
        new THREE.MeshBasicMaterial({ color: 0xb996ff, transparent: true, opacity: 0 }),
      );
      ring.position.copy(center);
      ring.position.y -= 0.28 + colonyIndex * 0.015;
      ring.rotation.x = Math.PI / 2;
      ring.userData = {
        kind: 'colony',
        bornAt: colonyBornAt,
        targetOpacity: 0.55,
        targetScale: new THREE.Vector3(1, 1, 1),
      };
      content.add(ring);
    });

    state.memories.forEach((memory, memoryIndex) => {
      const memoryBornAt = firstSeen(`memory:${memory.id}`);
      const members = memory.member_ids.map((id) => organismPositions.get(id)).filter(Boolean) as THREE.Vector3[];
      if (!members.length) return;
      const center = members.reduce((sum, point) => sum.add(point), new THREE.Vector3()).multiplyScalar(1 / members.length);
      const angle = hashUnit(memory.id, 91) * Math.PI * 2;
      const orbit = 0.42 + hashUnit(memory.id, 92) * 1.55;
      const position = new THREE.Vector3(
        center.x + Math.cos(angle) * orbit,
        MEMORY_Y - 0.75 + hashUnit(memory.id, 93) * 1.6,
        center.z + Math.sin(angle) * orbit,
      );
      const engram = new THREE.Mesh(
        organicGeometry(0.035 + memory.stability * 0.055, `${memory.id}:engram`, 1),
        new THREE.MeshPhysicalMaterial({
          color: 0x79e6b0,
          emissive: 0x1ecb7c,
          emissiveIntensity: 1.7 + Math.min(3.8, memory.recall_count * 0.035),
          roughness: 0.22,
          clearcoat: 0.7,
          transparent: true,
          opacity: 0.46 + memory.stability * 0.42,
        }),
      );
      engram.position.copy(position);
      engram.scale.setScalar(0.001);
      engram.userData = {
        kind: 'memory',
        bornAt: memoryBornAt,
        baseY: position.y,
        phase: angle,
        speed: 0.32 + hashUnit(memory.id, 94) * 0.34,
      };
      content.add(engram);
      if (memoryIndex % 12 === 0) addLine(content, [position, center], 0x75e2aa, 0.08 + memory.stability * 0.12);
    });

    state.informationPatches.forEach((patch, patchIndex) => {
      const age = Math.max(0, state.stepCount - patch.createdStep);
      const progress = Math.min(1, age / 18);
      const ground = worldPosition(patch.x, patch.y, ORGANISM_Y + 0.5);
      const target = patch.consumedBy ? organismPositions.get(patch.consumedBy) ?? ground : ground;
      const start = worldPosition(patch.x, patch.y, 5.2 + (patchIndex % 4) * 0.26);
      const position = start.clone().lerp(target, progress);
      const color = patch.digested ? 0x79e6b0 : patch.consumedBy ? 0x64d9ff : 0xffb45c;
      const food = new THREE.Mesh(
        new THREE.OctahedronGeometry(0.075 + patch.amount * 0.11, 0),
        new THREE.MeshStandardMaterial({ color, emissive: color, emissiveIntensity: 2.2, transparent: true, opacity: Math.max(0.16, 0.9 - age * 0.04) }),
      );
      food.position.copy(position);
      food.userData = { kind: 'information', phase: patchIndex * 0.73 };
      content.add(food);
      if (patch.consumedBy && age < 16) addLine(content, [position, target], color, 0.17);
    });
  }, [state, selectedId]);

  function resetView() {
    const runtime = runtimeRef.current;
    if (!runtime) return;
    runtime.camera.position.set(9.8, 7.1, 11.2);
    runtime.controls.target.set(0, 0.1, 0);
    runtime.controls.update();
  }

  function focusSelected() {
    const runtime = runtimeRef.current;
    const object = selectedId ? runtime?.organismObjects.get(selectedId) : null;
    if (!runtime || !object) return;
    const target = new THREE.Vector3();
    object.getWorldPosition(target);
    runtime.controls.target.copy(target);
    runtime.camera.position.copy(target).add(new THREE.Vector3(4.3, 3.1, 5.1));
    runtime.controls.update();
  }

  async function toggleFullscreen() {
    const stage = stageRef.current;
    if (!stage) return;
    if (document.fullscreenElement) await document.exitFullscreen();
    else await stage.requestFullscreen();
  }

  return <div ref={stageRef} className="architecture-stage">
    <div className="architecture-toolbar" aria-label="3D view controls">
      <button type="button" className={autoOrbit ? 'active' : ''} aria-pressed={autoOrbit} onClick={() => setAutoOrbit((value) => !value)}>{autoOrbit ? 'Pause orbit' : 'Auto orbit'}</button>
      <button type="button" onClick={focusSelected} disabled={!selectedId}>Focus selected</button>
      <button type="button" onClick={resetView}>Reset view</button>
      <button type="button" onClick={() => void toggleFullscreen()}>Full screen</button>
    </div>
    <div className="architecture-layer-map" aria-hidden="true">
      <span className="memory-layer"><i />MEMORY <b>{state.memories.length}</b></span>
      <span className="organism-layer"><i />ORGANISMS <b>{state.organisms.length}</b></span>
      <span className="micro-layer"><i />MICRO LAYER <b>{state.microSignatures.length}</b></span>
    </div>
    <div ref={morphRef} className="architecture-morphogenesis" data-phase="mature" aria-live="polite">
      <i /><span><b>ORGANIC NETWORK</b><small>Awaiting a morphogenesis event</small></span>
    </div>
    <div ref={hostRef} className="architecture-viewport">
      {webglError && <div className="architecture-error">3D acceleration is unavailable in this browser.</div>}
      {!state.organisms.length && <div className="architecture-empty"><b>ZERO LEARNED STRUCTURE</b><span>The first retinal sample will seed this space.</span></div>}
    </div>
    <div className="architecture-instructions">Drag to rotate · wheel or pinch to zoom · click an organism to inspect</div>
    {selected && <div className="architecture-selection">
      <i style={{ background: selected.color }} />
      <span><b>{selected.id}</b>{selectedCells} cells · {selected.lifecycleState} · {selected.colonyId ?? 'independent'}</span>
      <em>{selectedMicroIds.size} micro links · {selected.memoryIds.length} memories</em>
    </div>}
  </div>;
}
