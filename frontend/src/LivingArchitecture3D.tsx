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
  observer: ResizeObserver;
  frame: number;
  dispose: () => void;
};

const WORLD_SCALE = 0.145;
const MICRO_Y = -2.55;
const ORGANISM_Y = 0;
const MEMORY_Y = 2.75;

function hashUnit(value: string, salt = 0) {
  let hash = 2166136261 ^ salt;
  for (let index = 0; index < value.length; index += 1) {
    hash ^= value.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }
  return ((hash >>> 0) % 100000) / 100000;
}

function worldPosition(x: number, y: number, vertical = ORGANISM_Y) {
  return new THREE.Vector3((x - 50) * WORLD_SCALE, vertical, (y - 50) * WORLD_SCALE);
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
    camera.position.set(12.5, 9.2, 14.5);
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
      if (!reducedMotion) {
        content.traverse((object) => {
          if (object.userData.kind === 'organism') {
            object.position.y = object.userData.baseY + Math.sin(elapsed * 0.7 + object.userData.phase) * 0.075;
          } else if (object.userData.kind === 'memory') {
            object.rotation.z = elapsed * object.userData.speed + object.userData.phase;
          } else if (object.userData.kind === 'information') {
            object.rotation.x = elapsed * 0.9 + object.userData.phase;
            object.rotation.y = elapsed * 1.2;
            const pulse = 0.86 + Math.sin(elapsed * 3 + object.userData.phase) * 0.14;
            object.scale.setScalar(pulse);
          } else if (object.userData.kind === 'active-micro') {
            const pulse = 0.82 + Math.sin(elapsed * 4.2 + object.userData.phase) * 0.24;
            object.scale.setScalar(pulse);
          }
        });
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
    const { content } = runtime;
    disposeTree(content);
    content.clear();
    runtime.selectable = [];
    runtime.organismObjects = new Map();

    const lastPatch = state.informationPatches[state.informationPatches.length - 1];
    const activeMicroIds = new Set(lastPatch?.microActivations ?? []);
    const microPositions = new Map<string, THREE.Vector3>();

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
      const radiusValue = 0.055 + Math.min(0.11, Math.log2(2 + micro.observations) * 0.012);
      const mesh = new THREE.Mesh(
        new THREE.IcosahedronGeometry(radiusValue, 1),
        new THREE.MeshStandardMaterial({
          color: active ? 0xffe1a3 : 0xffa84f,
          emissive: active ? 0xff9f2d : 0x7d3208,
          emissiveIntensity: active ? 3.2 : 0.8,
          roughness: 0.35,
          transparent: true,
          opacity: 0.45 + Math.min(0.45, micro.energy * 0.3),
        }),
      );
      mesh.position.copy(position);
      if (active) {
        mesh.userData = { kind: 'active-micro', phase: index * 0.7 };
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
      const group = new THREE.Group();
      const basePosition = worldPosition(organism.x, organism.y, ORGANISM_Y + (hashUnit(organism.id, 6) - 0.5) * 0.75);
      group.position.copy(basePosition);
      group.userData = { kind: 'organism', baseY: basePosition.y, phase: organismIndex * 1.71 };
      organismPositions.set(organism.id, basePosition.clone());
      runtime.organismObjects.set(organism.id, group);

      const organismCells = state.cells.filter((cell) => cell.organism_id === organism.id);
      const cellCount = Math.max(1, organismCells.length);
      const growth = Math.min(1, 0.3 + Math.max(0, organism.ageSteps) / 80);
      const coreRadius = (0.28 + Math.sqrt(cellCount) * 0.105) * growth;
      const dormant = organism.lifecycleState === 'dormant';
      const color = new THREE.Color(organism.color);
      const core = new THREE.Mesh(
        new THREE.IcosahedronGeometry(coreRadius, 3),
        new THREE.MeshPhysicalMaterial({
          color,
          emissive: color,
          emissiveIntensity: dormant ? 0.18 : 0.72 + Math.min(0.8, organism.energy * 0.32),
          roughness: 0.24,
          metalness: 0.08,
          clearcoat: 0.7,
          clearcoatRoughness: 0.25,
          transparent: true,
          opacity: dormant ? 0.35 : 0.94,
        }),
      );
      core.castShadow = true;
      core.userData.organismId = organism.id;
      group.add(core);
      runtime.selectable.push(core);

      const membrane = new THREE.Mesh(
        new THREE.IcosahedronGeometry(coreRadius * 1.42, 2),
        new THREE.MeshBasicMaterial({ color, wireframe: true, transparent: true, opacity: dormant ? 0.08 : 0.22, depthWrite: false }),
      );
      membrane.userData.organismId = organism.id;
      group.add(membrane);

      const attachmentPoints: THREE.Vector3[] = [];
      organismCells.forEach((cell, cellIndex) => {
        const count = organismCells.length;
        const vertical = 1 - 2 * (cellIndex + 0.5) / Math.max(1, count);
        const radial = Math.sqrt(Math.max(0, 1 - vertical * vertical));
        const angle = cellIndex * 2.399963 + hashUnit(cell.id, 8) * 0.8;
        const orbit = coreRadius * (1.65 + (cellIndex % 3) * 0.18);
        const cellPosition = new THREE.Vector3(
          Math.cos(angle) * radial * orbit,
          vertical * orbit,
          Math.sin(angle) * radial * orbit,
        );
        attachmentPoints.push(cellPosition);
        const cellGrowth = Math.min(1, 0.35 + cell.age_steps / 45);
        const cellRadius = (0.075 + Math.min(0.07, cell.activation * 0.08)) * cellGrowth;
        const cellMesh = new THREE.Mesh(
          new THREE.SphereGeometry(cellRadius, 14, 10),
          new THREE.MeshStandardMaterial({
            color,
            emissive: color,
            emissiveIntensity: 1 + cell.activation * 2.5,
            roughness: 0.32,
            transparent: true,
            opacity: dormant ? 0.3 : 0.9,
          }),
        );
        cellMesh.position.copy(cellPosition);
        cellMesh.userData.organismId = organism.id;
        group.add(cellMesh);
        runtime.selectable.push(cellMesh);
        addLine(group, [new THREE.Vector3(), cellPosition], color, dormant ? 0.1 : 0.32 + cell.activation * 0.24);
      });

      if (attachmentPoints.length > 2) {
        addLine(group, [...attachmentPoints, attachmentPoints[0]], color, dormant ? 0.06 : 0.16);
      }

      const aura = new THREE.Mesh(
        new THREE.SphereGeometry(coreRadius * (2.2 + Math.min(0.9, organism.energy * 0.35)), 18, 12),
        new THREE.MeshBasicMaterial({ color, transparent: true, opacity: dormant ? 0.015 : 0.035, side: THREE.BackSide, depthWrite: false }),
      );
      group.add(aura);

      if (selectedId === organism.id) {
        const selection = new THREE.Mesh(
          new THREE.TorusGeometry(coreRadius * 1.95, 0.025, 8, 64),
          new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.95 }),
        );
        selection.rotation.x = Math.PI / 2;
        group.add(selection);
      }

      const label = textSprite(`${organism.id}  ·  ${organismCells.length} cells`, organism.color);
      label.position.set(0, coreRadius * 2.5 + 0.32, 0);
      label.scale.multiplyScalar(selectedId === organism.id ? 1.14 : 0.88);
      group.add(label);
      content.add(group);
    });

    state.colonies.forEach((colony, colonyIndex) => {
      const members = colony.member_ids.map((id) => organismPositions.get(id)).filter(Boolean) as THREE.Vector3[];
      if (members.length < 2) return;
      const center = members.reduce((sum, point) => sum.add(point), new THREE.Vector3()).multiplyScalar(1 / members.length);
      const maxDistance = Math.max(...members.map((point) => point.distanceTo(center)));
      addLine(content, [...members, members[0]], 0xb791ff, 0.52);
      members.forEach((member) => addLine(content, [center, member], 0xb791ff, 0.22));
      const membrane = new THREE.Mesh(
        new THREE.SphereGeometry(Math.max(0.8, maxDistance + 0.75), 24, 16),
        new THREE.MeshBasicMaterial({ color: 0xa985ff, wireframe: true, transparent: true, opacity: 0.075, depthWrite: false }),
      );
      membrane.position.copy(center);
      membrane.scale.y = 0.48;
      content.add(membrane);
      const ring = new THREE.Mesh(
        new THREE.TorusGeometry(Math.max(0.65, maxDistance + 0.42), 0.018 + colony.synergy * 0.08, 8, 96),
        new THREE.MeshBasicMaterial({ color: 0xb996ff, transparent: true, opacity: 0.55 }),
      );
      ring.position.copy(center);
      ring.position.y -= 0.28 + colonyIndex * 0.015;
      ring.rotation.x = Math.PI / 2;
      content.add(ring);
    });

    state.memories.forEach((memory, memoryIndex) => {
      const members = memory.member_ids.map((id) => organismPositions.get(id)).filter(Boolean) as THREE.Vector3[];
      if (!members.length) return;
      const center = members.reduce((sum, point) => sum.add(point), new THREE.Vector3()).multiplyScalar(1 / members.length);
      const angle = memoryIndex * 2.399963;
      const orbit = 0.5 + (memoryIndex % 4) * 0.18;
      const position = new THREE.Vector3(
        center.x + Math.cos(angle) * orbit,
        MEMORY_Y + (memoryIndex % 5) * 0.17,
        center.z + Math.sin(angle) * orbit,
      );
      const ring = new THREE.Mesh(
        new THREE.TorusGeometry(0.12 + memory.stability * 0.16, 0.025, 10, 36),
        new THREE.MeshStandardMaterial({
          color: 0x79e6b0,
          emissive: 0x1ecb7c,
          emissiveIntensity: 1.5 + Math.min(2.5, memory.recall_count * 0.025),
          transparent: true,
          opacity: 0.48 + memory.stability * 0.45,
        }),
      );
      ring.position.copy(position);
      ring.rotation.x = Math.PI / 2;
      ring.userData = { kind: 'memory', phase: angle, speed: 0.1 + (memoryIndex % 3) * 0.025 };
      content.add(ring);
      addLine(content, [position, center], 0x75e2aa, 0.1 + memory.stability * 0.16);
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
    runtime.camera.position.set(12.5, 9.2, 14.5);
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
    <div ref={hostRef} className="architecture-viewport">
      {webglError && <div className="architecture-error">3D acceleration is unavailable in this browser.</div>}
      {!state.organisms.length && <div className="architecture-empty"><b>ZERO LEARNED STRUCTURE</b><span>The first retinal sample will seed this space.</span></div>}
    </div>
    <div className="architecture-instructions">Drag to rotate · wheel or pinch to zoom · click an organism to inspect</div>
    {selected && <div className="architecture-selection">
      <i style={{ background: selected.color }} />
      <span><b>{selected.id}</b>{selectedCells} cells · {selected.lifecycleState} · {selected.colonyId ?? 'independent'}</span>
      <em>{selected.memoryIds.length} memories</em>
    </div>}
  </div>;
}
