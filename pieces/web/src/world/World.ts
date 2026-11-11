import * as THREE from 'three';
import { compositeFrag, dustFrag, dustVert, fullscreenVert, plateFrag, plateVert, silkFrag } from './shaders';
import { buildState, type Layout, type Motion, type PointState, type StateDef } from './states';

export type Blend = { from: string; to: string; mix: number };

type Loaded = { def: StateDef; attr: THREE.BufferAttribute; color: THREE.BufferAttribute; aspect: number; tex?: THREE.Texture };
const PLATE = 0.3; // how strongly the real photo shows behind its dust

const FOV = 35;
const CAM_Z = 10;

function pickCount(): number {
  const cores = navigator.hardwareConcurrency || 4;
  const mem = (navigator as Navigator & { deviceMemory?: number }).deviceMemory ?? 8;
  const small = Math.min(window.innerWidth, window.innerHeight) < 700;
  if (small || cores <= 4 || mem <= 4) return 26000;
  return 80000;
}

export class World {
  readonly n = pickCount();
  private renderer: THREE.WebGLRenderer;
  private camera = new THREE.PerspectiveCamera(FOV, 1, 0.1, 100);
  private scene = new THREE.Scene();
  private silkScene = new THREE.Scene();
  private silkTarget: THREE.WebGLRenderTarget;
  private silkMat: THREE.ShaderMaterial;
  private compMat: THREE.ShaderMaterial;
  private dustMat: THREE.ShaderMaterial;
  private geom = new THREE.BufferGeometry();
  private states = new Map<string, Loaded>();
  private pending = new Map<string, Promise<void>>();
  private clock = new THREE.Clock();
  private raf = 0;
  private running = false;
  private visible = true;
  private pointer = { x: 0.5, y: 0.5, tx: 0.5, ty: 0.5, active: 0, tactive: 0 };
  private blend: Blend = { from: 'cloud', to: 'cloud', mix: 0 };
  private intro = 0;
  private scroll = 0;
  private narrow = false;
  private viewW = 1;
  private viewH = 1;
  private onFrameCbs: Array<(t: number) => void> = [];
  private plates: THREE.Mesh[] = [];
  private loader = new THREE.TextureLoader();

  constructor(canvas: HTMLCanvasElement) {
    this.renderer = new THREE.WebGLRenderer({ canvas, antialias: false, alpha: false, powerPreference: 'high-performance' });
    this.renderer.setClearColor(0x0d0c09, 1);
    this.renderer.outputColorSpace = THREE.LinearSRGBColorSpace; // shaders write display values directly
    this.camera.position.set(0, 0, CAM_Z);

    this.silkTarget = new THREE.WebGLRenderTarget(2, 2, { depthBuffer: false });
    this.silkMat = new THREE.ShaderMaterial({
      vertexShader: fullscreenVert,
      fragmentShader: silkFrag,
      depthTest: false,
      depthWrite: false,
      uniforms: {
        uTime: { value: 0 }, uRes: { value: new THREE.Vector2(1, 1) }, uPointer: { value: new THREE.Vector2(0.5, 0.5) },
        uPointerLight: { value: 0 }, uIntensity: { value: 1 }, uWarm: { value: 0 }, uScroll: { value: 0 },
      },
    });
    const tri = new THREE.BufferGeometry();
    tri.setAttribute('position', new THREE.Float32BufferAttribute([-1, -1, 0, 3, -1, 0, -1, 3, 0], 3));
    tri.setAttribute('uv', new THREE.Float32BufferAttribute([0, 0, 2, 0, 0, 2], 2));
    const silkMesh = new THREE.Mesh(tri, this.silkMat);
    silkMesh.frustumCulled = false;
    this.silkScene.add(silkMesh);

    this.compMat = new THREE.ShaderMaterial({
      vertexShader: fullscreenVert,
      fragmentShader: compositeFrag,
      depthTest: false,
      depthWrite: false,
      uniforms: { uSilk: { value: this.silkTarget.texture }, uTime: { value: 0 }, uRes: { value: new THREE.Vector2(1, 1) }, uGrain: { value: 0.045 } },
    });
    const comp = new THREE.Mesh(tri, this.compMat);
    comp.frustumCulled = false;
    comp.renderOrder = -1;
    this.scene.add(comp);

    // dust
    const seeds = new Float32Array(this.n * 4);
    for (let i = 0; i < seeds.length; i++) seeds[i] = Math.random();
    const zero = new Float32Array(this.n * 4);
    this.geom.setAttribute('position', new THREE.BufferAttribute(new Float32Array(this.n * 3), 3));
    this.geom.setAttribute('aSeed', new THREE.BufferAttribute(seeds, 4));
    this.geom.setAttribute('aFrom', new THREE.BufferAttribute(zero, 4));
    this.geom.setAttribute('aTo', new THREE.BufferAttribute(zero, 4));
    const zc = new Float32Array(this.n * 3).fill(0.7);
    this.geom.setAttribute('aFromC', new THREE.BufferAttribute(zc, 3));
    this.geom.setAttribute('aToC', new THREE.BufferAttribute(zc, 3));
    this.dustMat = new THREE.ShaderMaterial({
      vertexShader: dustVert,
      fragmentShader: dustFrag,
      transparent: true,
      depthTest: false,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
      uniforms: {
        uMix: { value: 0 }, uFromX: { value: new THREE.Vector4(0, 0, 1, 0) }, uToX: { value: new THREE.Vector4(0, 0, 1, 0) },
        uFromMotion: { value: new THREE.Vector4() }, uToMotion: { value: new THREE.Vector4() },
        uTime: { value: 0 }, uIntro: { value: 0 }, uPointer: { value: new THREE.Vector3(99, 99, 0) },
        uSize: { value: 2.1 }, uPR: { value: 1 }, uView: { value: new THREE.Vector2(1, 1) }, uOpacity: { value: 1 },
      },
    });
    // faint real photos behind the dust (from + to), additive, so the picture reads at a glance
    for (let i = 0; i < 2; i++) {
      const m = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), new THREE.ShaderMaterial({
        vertexShader: plateVert, fragmentShader: plateFrag, transparent: true, depthTest: false, depthWrite: false,
        blending: THREE.AdditiveBlending, uniforms: { uMap: { value: null }, uOpacity: { value: 0 } },
      }));
      m.frustumCulled = false;
      m.renderOrder = -0.5;
      m.visible = false;
      this.plates.push(m);
      this.scene.add(m);
    }
    const points = new THREE.Points(this.geom, this.dustMat);
    points.frustumCulled = false;
    this.scene.add(points);

    this.resize();
  }

  /** Register states; images load lazily in the background. */
  async load(defs: StateDef[], first: string[] = []): Promise<void> {
    const order = [...first, ...defs.map((d) => d.id).filter((id) => !first.includes(id))];
    const byId = new Map(defs.map((d) => [d.id, d]));
    for (const id of order) {
      const def = byId.get(id);
      if (def) await this.ensure(def);
    }
  }

  private ensure(def: StateDef): Promise<void> {
    if (this.states.has(def.id)) return Promise.resolve();
    const existing = this.pending.get(def.id);
    if (existing) return existing;
    const p = buildState(def, this.n).then(async (ps: PointState) => {
      const loaded: Loaded = { def, attr: new THREE.BufferAttribute(ps.data, 4), color: new THREE.BufferAttribute(ps.color, 3), aspect: ps.aspect };
      if (def.source.kind === 'image' && ps.aspect !== 2.2) {
        try {
          const tex = await this.loader.loadAsync(def.source.src);
          tex.colorSpace = THREE.NoColorSpace;
          loaded.tex = tex;
        } catch { /* no plate, dust only */ }
      }
      this.states.set(def.id, loaded);
      this.applyBlend();
      this.applyPos();
    });
    this.pending.set(def.id, p);
    return p;
  }

  has(id: string) { return this.states.has(id); }

  setBlend(b: Blend) {
    if (b.from === this.blend.from && b.to === this.blend.to && Math.abs(b.mix - this.blend.mix) < 1e-4) return;
    this.blend = b;
    this.applyBlend();
  }

  setScroll(p: number) { this.scroll = p; }

  /** A state's layout changed (the page measured where its picture may go): redraw with it. */
  relayout() { this.applyBlend(); }

  /** The chain of pictures in scroll order, and where along it the page is (eased every frame). */
  private timeline: string[] = [];
  private pos = 0;
  private targetPos = 0;
  private lastT = -1;
  setTimeline(ids: string[]) { this.timeline = ids; this.applyPos(); }
  setTarget(p: number, immediate = false) {
    this.targetPos = p;
    if (immediate) { this.pos = p; this.applyPos(); }
  }
  private applyPos() {
    const n = this.timeline.length;
    if (!n) return;
    const p = Math.min(n - 1, Math.max(0, this.pos));
    const i = Math.floor(p);
    const j = Math.min(n - 1, i + 1);
    this.setBlend({ from: this.timeline[i], to: this.timeline[j], mix: j === i ? 0 : p - i });
  }

  setPointer(clientX: number, clientY: number, active = true) {
    this.pointer.tx = clientX / window.innerWidth;
    this.pointer.ty = 1 - clientY / window.innerHeight;
    this.pointer.tactive = active ? 1 : 0;
  }

  setIntro(v: number) { this.intro = v; }

  onFrame(cb: (t: number) => void) { this.onFrameCbs.push(cb); }

  private layoutOf(l: Loaded): Layout {
    return (this.narrow && l.def.layoutNarrow) || l.def.layout;
  }

  private xform(l: Loaded | undefined, out: THREE.Vector4) {
    if (!l) { out.set(0, 0, 1, 0); return; }
    const lay = this.layoutOf(l);
    const scale = (lay.h * this.viewH) / 2; // state y spans -1..1 → lay.h of the view height
    out.set((lay.cx * this.viewW) / 2, (lay.cy * this.viewH) / 2, scale, 0);
  }

  private motion(l: Loaded | undefined, out: THREE.Vector4) {
    const m: Motion = l?.def.motion ?? { drift: 1, swirl: 0, flow: 0, fall: 0 };
    out.set(m.drift, m.swirl, m.flow, m.fall);
  }

  private applyBlend() {
    const from = this.states.get(this.blend.from) ?? this.states.get('cloud');
    const to = this.states.get(this.blend.to) ?? from;
    if (!from || !to) return;
    if (this.geom.getAttribute('aFrom') !== from.attr) this.geom.setAttribute('aFrom', from.attr);
    if (this.geom.getAttribute('aTo') !== to.attr) this.geom.setAttribute('aTo', to.attr);
    if (this.geom.getAttribute('aFromC') !== from.color) this.geom.setAttribute('aFromC', from.color);
    if (this.geom.getAttribute('aToC') !== to.color) this.geom.setAttribute('aToC', to.color);
    const u = this.dustMat.uniforms;
    u.uMix.value = this.states.has(this.blend.to) ? this.blend.mix : 0;
    this.xform(from, u.uFromX.value);
    this.xform(to, u.uToX.value);
    this.motion(from, u.uFromMotion.value);
    this.motion(to, u.uToMotion.value);
    const e = u.uMix.value * u.uMix.value * (3 - 2 * u.uMix.value);
    // plates fade out while the dust is in flight and back in when it lands
    const calm = Math.pow(Math.abs(e - 0.5) * 2, 3);
    this.placePlate(this.plates[0], from, (from === to ? 1 : 1 - e) * calm);
    this.placePlate(this.plates[1], to, from === to ? 0 : e * calm);
    const a = from.def.silk, b = to.def.silk;
    const s = this.silkMat.uniforms;
    s.uIntensity.value = a.intensity + (b.intensity - a.intensity) * e;
    s.uWarm.value = a.warm + (b.warm - a.warm) * e;
    this.pointerLight = a.pointer + (b.pointer - a.pointer) * e;
  }
  private pointerLight = 0.6;

  private placePlate(m: THREE.Mesh, l: Loaded, k: number) {
    const mat = m.material as THREE.ShaderMaterial;
    const plate = l.def.source.kind === 'image' ? l.def.source.plate ?? PLATE : 0;
    if (!l.tex || k <= 0.001 || plate <= 0) { m.visible = false; return; }
    const lay = this.layoutOf(l);
    const scale = (lay.h * this.viewH) / 2;
    m.visible = true;
    m.position.set((lay.cx * this.viewW) / 2, (lay.cy * this.viewH) / 2, -0.35);
    m.scale.set(scale * 2 * l.aspect, scale * 2, 1);
    mat.uniforms.uMap.value = l.tex;
    mat.uniforms.uOpacity.value = plate * k * this.plateIntro;
  }
  private plateIntro = 0;

  resize() {
    const w = window.innerWidth, h = window.innerHeight;
    const pr = Math.min(window.devicePixelRatio || 1, 1.5);
    this.renderer.setPixelRatio(pr);
    this.renderer.setSize(w, h, false);
    this.silkTarget.setSize(Math.max(2, Math.round(w * 0.42)), Math.max(2, Math.round(h * 0.42)));
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
    this.viewH = 2 * CAM_Z * Math.tan(THREE.MathUtils.degToRad(FOV / 2));
    this.viewW = this.viewH * this.camera.aspect;
    this.narrow = w < 900;
    this.silkMat.uniforms.uRes.value.set(w, h);
    this.compMat.uniforms.uRes.value.set(w * pr, h * pr);
    const u = this.dustMat.uniforms;
    u.uPR.value = pr;
    u.uView.value.set(this.viewW, this.viewH);
    u.uSize.value = this.narrow ? 2.1 : 1.75;
    this.applyBlend();
  }

  setVisible(v: boolean) {
    this.visible = v;
    if (v && this.running && !this.raf) this.loop();
  }

  start() {
    if (this.running) return;
    this.running = true;
    this.clock.start();
    this.loop();
  }

  stop() {
    this.running = false;
    cancelAnimationFrame(this.raf);
    this.raf = 0;
  }

  /** Draw one still frame (reduced motion). */
  still(t = 12) {
    this.pos = this.targetPos;
    this.applyPos();
    this.renderAt(t);
  }

  private loop = () => {
    if (!this.running || !this.visible) { this.raf = 0; return; }
    this.raf = requestAnimationFrame(this.loop);
    this.renderAt(this.clock.getElapsedTime());
  };

  private renderAt(t: number) {
    for (const cb of this.onFrameCbs) cb(t);
    // ease along the chain of pictures: fast scrolls glide, they never jump
    const dt = this.lastT < 0 ? 0.016 : Math.min(0.05, Math.max(0, t - this.lastT));
    this.lastT = t;
    if (Math.abs(this.targetPos - this.pos) > 0.0005) {
      this.pos += (this.targetPos - this.pos) * (1 - Math.exp(-dt * 6.5));
      this.applyPos();
    }
    const p = this.pointer;
    p.x += (p.tx - p.x) * 0.06;
    p.y += (p.ty - p.y) * 0.06;
    p.active += (p.tactive - p.active) * 0.04;

    const s = this.silkMat.uniforms;
    s.uTime.value = t;
    s.uPointer.value.set(p.x, p.y);
    s.uPointerLight.value = this.pointerLight * p.active;
    s.uScroll.value = this.scroll;

    const u = this.dustMat.uniforms;
    u.uTime.value = t;
    u.uIntro.value = this.intro;
    if (Math.abs(this.plateIntro - this.intro) > 0.01) { this.plateIntro = this.intro; this.applyBlend(); }
    u.uPointer.value.set((p.x - 0.5) * this.viewW, (p.y - 0.5) * this.viewH, p.active);
    this.compMat.uniforms.uTime.value = t;

    // gentle parallax: the camera leans toward the pointer
    this.camera.position.x += ((p.x - 0.5) * 0.55 - this.camera.position.x) * 0.04;
    this.camera.position.y += ((p.y - 0.5) * 0.35 - this.camera.position.y) * 0.04;
    this.camera.lookAt(0, 0, 0);

    this.renderer.setRenderTarget(this.silkTarget);
    this.renderer.render(this.silkScene, this.camera);
    this.renderer.setRenderTarget(null);
    this.renderer.render(this.scene, this.camera);
  }

  dispose() {
    this.stop();
    this.geom.dispose();
    for (const m of this.plates) { m.geometry.dispose(); (m.material as THREE.Material).dispose(); }
    for (const l of this.states.values()) l.tex?.dispose();
    this.dustMat.dispose();
    this.silkMat.dispose();
    this.compMat.dispose();
    this.silkTarget.dispose();
    this.renderer.dispose();
  }
}
