// GLSL for the GoldGraft world.
// 1. silkFrag  — the living background: domain-warped light moving through black,
//    lit from the upper left, bent toward the pointer. Rendered at half resolution.
// 2. compositeFrag — upscales the silk, adds film grain + vignette at full resolution.
// 3. dustVert / dustFrag — tens of thousands of gold particles that morph between
//    "states" (photos or drawings sampled into points) as the visitor scrolls.

const noise = /* glsl */ `
float hash12(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * .1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }
float vnoise(vec2 p){
  vec2 i = floor(p), f = fract(p);
  vec2 u = f * f * (3.0 - 2.0 * f);
  return mix(mix(hash12(i), hash12(i + vec2(1,0)), u.x), mix(hash12(i + vec2(0,1)), hash12(i + vec2(1,1)), u.x), u.y);
}
float fbm(vec2 p){
  float v = 0.0, a = 0.5;
  mat2 r = mat2(0.8, -0.6, 0.6, 0.8);
  for (int i = 0; i < 5; i++){ v += a * vnoise(p); p = r * p * 2.03 + 11.7; a *= 0.5; }
  return v;
}`;

export const fullscreenVert = /* glsl */ `
varying vec2 vUv;
void main(){ vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }`;

export const silkFrag = /* glsl */ `
precision highp float;
varying vec2 vUv;
uniform float uTime;
uniform vec2 uRes;
uniform vec2 uPointer;      // 0..1 screen space
uniform float uPointerLight;
uniform float uIntensity;   // per chapter
uniform float uWarm;        // 0 = neutral, 1 = warmer gold
uniform float uScroll;      // page progress 0..1 (moves the light slowly)
${noise}
void main(){
  vec2 uv = vUv;
  float aspect = uRes.x / max(uRes.y, 1.0);
  vec2 p = vec2(uv.x * aspect, uv.y) * 1.35;
  float t = uTime * 0.018;
  p += vec2(0.0, -uScroll * 1.6);

  vec2 q = vec2(fbm(p + vec2(0.0, t)), fbm(p + vec2(5.2, 1.3) - t * 0.8));
  vec2 r = vec2(fbm(p + 2.6 * q + vec2(1.7, 9.2) + t * 0.6), fbm(p + 2.6 * q + vec2(8.3, 2.8) - t * 0.5));
  float f = fbm(p + 3.2 * r);

  // silk veins: thin bright ridges where the warped field folds
  float ridge = 1.0 - abs(f * 2.0 - 1.0);
  float silk = pow(smoothstep(0.55, 1.0, ridge), 2.2) * 0.85 + smoothstep(0.45, 0.95, f) * 0.35;

  // key light from the upper left (315°) + a soft pull toward the pointer
  vec2 keyPos = vec2(-0.15 * aspect, 1.15);
  float key = smoothstep(2.3, 0.0, distance(vec2(uv.x * aspect, uv.y), keyPos));
  vec2 pp = vec2(uPointer.x * aspect, uPointer.y);
  float lamp = smoothstep(0.75, 0.0, distance(vec2(uv.x * aspect, uv.y), pp)) * uPointerLight;

  vec3 ink = vec3(0.051, 0.047, 0.035);
  vec3 gold = mix(vec3(0.80, 0.745, 0.61), vec3(0.86, 0.70, 0.43), uWarm);
  vec3 bark = vec3(0.16, 0.12, 0.075);

  float light = silk * (0.20 + 0.80 * key) + lamp * (0.35 + silk);
  vec3 col = ink + bark * (q.x * 0.55) * (0.4 + key) * uIntensity;
  col += gold * light * 0.135 * uIntensity;
  gl_FragColor = vec4(col, 1.0);
}`;

export const compositeFrag = /* glsl */ `
precision highp float;
varying vec2 vUv;
uniform sampler2D uSilk;
uniform float uTime;
uniform vec2 uRes;
uniform float uGrain;
float hash(vec2 p){ return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453); }
void main(){
  vec3 col = texture2D(uSilk, vUv).rgb;
  vec2 c = vUv - 0.5;
  c.x *= uRes.x / uRes.y;
  float vig = smoothstep(1.25, 0.25, length(c * vec2(0.9, 1.15)));
  col *= mix(0.55, 1.0, vig);
  float g = hash(vUv * uRes + fract(uTime * 7.31) * 113.0) - 0.5;
  col += g * uGrain;                       // film grain
  col += (hash(vUv * uRes * 1.37) - 0.5) / 255.0; // dither against banding
  gl_FragColor = vec4(col, 1.0);
}`;

export const dustVert = /* glsl */ `
attribute vec4 aFrom;   // xyz in state space, w = brightness
attribute vec4 aTo;
attribute vec4 aSeed;   // four randoms in 0..1
uniform float uMix;
uniform vec4 uFromX;    // cx, cy (world units), scale (world units per state unit), unused
uniform vec4 uToX;
uniform vec4 uFromMotion; // drift, swirl, flow, fall
uniform vec4 uToMotion;
uniform float uTime;
uniform float uIntro;   // 0 = scattered, 1 = gathered
uniform vec3 uPointer;  // world x, y, strength
uniform float uSize;
uniform float uPR;
uniform vec2 uView;     // visible world width, height at z = 0
varying float vAlpha;
varying float vB;
varying float vSeed;

vec3 swirlNoise(vec3 p, float t){
  return vec3(
    sin(p.y * 1.7 + t * 0.9 + aSeed.z * 6.2831),
    cos(p.x * 1.3 - t * 0.7 + aSeed.w * 6.2831),
    sin((p.x + p.y) * 0.9 + t * 0.5 + aSeed.x * 6.2831)
  );
}

vec3 place(vec4 s, vec4 x, vec4 m, float t){
  vec3 p = s.xyz * x.z;
  // idle breathing
  p.xy += m.x * 0.018 * x.z * vec2(sin(t * 0.55 + aSeed.x * 6.2831), cos(t * 0.47 + aSeed.y * 6.2831));
  // swirl around the state centre
  float ang = m.y * t * 0.08 * (1.2 - clamp(length(s.xy), 0.0, 1.0));
  p.xy = mat2(cos(ang), -sin(ang), sin(ang), cos(ang)) * p.xy;
  // flow: particles travel left to right and wrap (buyers moving)
  if (m.z > 0.0) {
    float w = 2.2 * x.z;
    p.x = mod(p.x + w * 0.5 + t * m.z * 0.12 * (0.6 + aSeed.y), w) - w * 0.5;
  } else if (m.z < 0.0) {
    float w = 2.2 * x.z;
    p.x = mod(p.x + w * 0.5 + t * m.z * 0.12 * (0.6 + aSeed.y), w) - w * 0.5;
  }
  // fall: the dimmest specks drift down like ash and wrap
  if (m.w > 0.0) {
    float k = step(s.w, 0.55) * m.w;
    float fall = fract(t * 0.035 * (0.5 + aSeed.z) + aSeed.w) * 2.4 * x.z;
    p.y -= fall * k;
    p.x += sin(t * 0.6 + aSeed.x * 9.0) * 0.06 * x.z * k;
  }
  p.xy += x.xy;
  return p;
}

void main(){
  float t = uTime;
  float e = uMix * uMix * (3.0 - 2.0 * uMix);
  vec3 a = place(aFrom, uFromX, uFromMotion, t);
  vec3 b = place(aTo, uToX, uToMotion, t);
  vec3 pos = mix(a, b, e);

  // in-flight turbulence: strongest halfway through a morph
  float flight = sin(3.14159 * e);
  pos += swirlNoise(pos * 0.6, t) * flight * (0.25 + aSeed.x * 0.55) * 0.55;

  // intro: dust gathers from a wide cloud
  vec3 cloud = (aSeed.xyz * 2.0 - 1.0) * vec3(uView.x * 0.75, uView.y * 0.75, 4.0);
  float ie = 1.0 - pow(1.0 - uIntro, 3.0);
  pos = mix(cloud, pos, ie);

  // pointer parts the dust
  vec2 d = pos.xy - uPointer.xy;
  float r = 0.85;
  float f = smoothstep(r, 0.0, length(d)) * uPointer.z;
  pos.xy += normalize(d + 1e-4) * f * 0.42;
  pos.z += f * 0.35;

  vec4 mv = modelViewMatrix * vec4(pos, 1.0);
  gl_Position = projectionMatrix * mv;

  float bri = mix(aFrom.w, aTo.w, e);
  vB = bri;
  vSeed = aSeed.y;
  float tw = 0.75 + 0.25 * sin(t * (0.8 + aSeed.z * 1.6) + aSeed.w * 40.0);
  vAlpha = (0.10 + 0.62 * bri) * tw * (0.35 + 0.65 * ie) * (1.0 + flight * 0.25);
  gl_PointSize = uSize * uPR * (0.45 + bri * 0.85) * (0.55 + aSeed.y * aSeed.y * 1.1) * (10.0 / -mv.z);
}`;

export const dustFrag = /* glsl */ `
precision highp float;
varying float vAlpha;
varying float vB;
varying float vSeed;
uniform float uOpacity;
void main(){
  vec2 c = gl_PointCoord - 0.5;
  float d = length(c);
  if (d > 0.5) discard;
  float core = pow(smoothstep(0.5, 0.0, d), 1.7);
  vec3 bark = vec3(0.42, 0.33, 0.22);
  vec3 gold = vec3(0.80, 0.745, 0.61);
  vec3 ivory = vec3(0.96, 0.95, 0.93);
  vec3 col = mix(bark, gold, smoothstep(0.05, 0.6, vB));
  col = mix(col, ivory, smoothstep(0.72, 1.0, vB) * (0.5 + 0.5 * vSeed));
  gl_FragColor = vec4(col, core * vAlpha * uOpacity);
}`;
