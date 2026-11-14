// 液态玻璃（竖屏版）：实时折射实拍画面。移植自 007 engine/glass.js，算法源自 Liquid Glass Studio（iyinchao/liquid-glass-studio，MIT，© 2024 Charles Yin）。
// 改动：画布 1080×1920；内色换成红/蓝；加 mag 放大倍率（透镜里看得清球）；不画投影。
const W = 1080, H = 1920;
const VS = `#version 300 es
in vec2 a_pos; out vec2 v_px;
void main() { v_px = (a_pos * 0.5 + 0.5) * vec2(${W}.0, ${H}.0); v_px.y = ${H}.0 - v_px.y; gl_Position = vec4(a_pos, 0.0, 1.0); }`;
const FS = `#version 300 es
precision highp float;
#define MAXL 8
uniform sampler2D u_src; uniform vec4 u_L[MAXL]; uniform vec4 u_C[MAXL]; uniform int u_n; uniform float u_t;
in vec2 v_px; out vec4 o;
float sasin(float x) { return asin(clamp(x, -1.0, 1.0)); }
void main() {
  float S = 0.0, K = 0.0; vec2 g = vec2(0.0), C = vec2(0.0); float T = 0.0, A = 0.0, Hu = 0.0, R = 0.0, M = 0.0;
  for (int i = 0; i < MAXL; i++) { if (i >= u_n) break;
    vec4 L = u_L[i]; if (L.w <= 0.001 || L.z < 0.5) continue;
    vec2 q = v_px - L.xy; float len = max(length(q), 1e-4), d = len - L.z, k = max(1.0, u_C[i].z);
    float e = exp(-clamp(d / k, -30.0, 30.0));
    S += e; K += e * k; g += e * q / len; C += e * L.xy; R += e * L.z; T += e * L.z * u_C[i].y; A += e * L.w; Hu += e * u_C[i].x; M += e * u_C[i].w; }
  if (S <= 1e-6) discard;
  float kk = K / S, d = -kk * log(S);
  if (d > 0.0) discard;
  vec2 n = g / S; float nl = length(n); n = nl > 1e-5 ? n / nl : vec2(0.0);
  C /= S; R /= S; T /= S; A /= S; Hu /= S; M /= S;
  float inside = -d;
  vec2 px2uv = 1.0 / vec2(${W}.0, ${H}.0), uv = v_px * px2uv;
  float rho = clamp(length(v_px - C) / max(R, 1.0), 0.0, 1.0);
  vec2 magOff = -(v_px - C) * (1.0 - 1.0 / max(M, 1.0));
  vec2 lensOff = -(v_px - C) * (1.0 - sqrt(max(0.0, 1.0 - rho * rho))) * 0.9;
  float x = clamp(1.0 - inside / max(T, 1.0), 0.0, 1.0);
  float thI = sasin(x * x), thT = sasin(sin(thI) / 1.5);
  vec2 edgeOff = -n * (-tan(thT - thI)) * T * 0.35;
  vec2 off = (magOff + lensOff + edgeOff) * px2uv;
  float disp = (0.008 + 0.028 * x);
  float lod = mix(0.0, 2.2, x * x);
  vec3 c;
  c.r = textureLod(u_src, uv + off * (1.0 - disp), lod).r;
  c.g = textureLod(u_src, uv + off, lod).g;
  c.b = textureLod(u_src, uv + off * (1.0 + disp), lod).b;
  vec3 tint = Hu < 0.5 ? vec3(1.0, 0.27, 0.19) : vec3(0.24, 0.47, 1.0);
  vec2 lp = (v_px - C) / max(R, 1.0);
  c = mix(c, tint, 0.10 + 0.34 * smoothstep(0.45, 1.0, rho));
  float band = smoothstep(0.0, T * 0.10 + 1.0, inside) * (1.0 - smoothstep(T * 0.10, T * 0.32, inside));
  c *= 1.0 - 0.14 * band;
  float rim = 1.0 - smoothstep(0.0, 2.0 + R * 0.03, inside);
  c = mix(c, vec3(1.0), rim * 0.9);
  float ang = atan(n.y, n.x);
  float cres = pow(max(0.0, cos(ang + 2.35)), 5.0) * smoothstep(0.0, R * 0.04, inside) * (1.0 - smoothstep(R * 0.06, R * 0.22, inside));
  vec2 hs = lp - vec2(-0.40, -0.44); float hot = exp(-dot(hs, hs) / 0.010);
  float back = pow(max(0.0, cos(ang - 0.79)), 6.0) * (1.0 - smoothstep(0.0, R * 0.12, inside));
  c += vec3(1.0) * (cres * 0.85 + hot * 0.6 + back * 0.3) + tint * rim * 0.2;
  o = vec4(min(c, vec3(1.0)), clamp(0.5 - d, 0.0, 1.0) * A);
}`;

export function mountGlass(source) {
  const cv = document.createElement('canvas'); cv.width = W; cv.height = H;
  const gl = cv.getContext('webgl2', { premultipliedAlpha: false, alpha: true, preserveDrawingBuffer: true, antialias: false });
  if (!gl) throw new Error('无 WebGL2');
  const sh = (t, s) => { const x = gl.createShader(t); gl.shaderSource(x, s); gl.compileShader(x); if (!gl.getShaderParameter(x, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(x)); return x; };
  const pr = gl.createProgram(); gl.attachShader(pr, sh(gl.VERTEX_SHADER, VS)); gl.attachShader(pr, sh(gl.FRAGMENT_SHADER, FS)); gl.linkProgram(pr);
  if (!gl.getProgramParameter(pr, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(pr));
  gl.useProgram(pr);
  const U = n => gl.getUniformLocation(pr, n);
  const tex = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, tex);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
  gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, false);
  const vao = gl.createVertexArray(); gl.bindVertexArray(vao);
  const b = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, b); gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW);
  const a = gl.getAttribLocation(pr, 'a_pos'); gl.enableVertexAttribArray(a); gl.vertexAttribPointer(a, 2, gl.FLOAT, false, 0, 0);
  gl.uniform1i(U('u_src'), 0); gl.viewport(0, 0, W, H); gl.disable(gl.BLEND);
  const LA = new Float32Array(32), CA = new Float32Array(32);
  // lenses: [{x, y, r, a, hue(0 红 / 1 蓝), thick, k, mag}]
  return (lenses, t) => {
    gl.clearColor(0, 0, 0, 0); gl.clear(gl.COLOR_BUFFER_BIT);
    const L = lenses.filter(l => (l.a ?? 1) > 0.002 && l.r > 0.8).slice(0, 8);
    if (!L.length) return null;
    gl.bindTexture(gl.TEXTURE_2D, tex); gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, source); gl.generateMipmap(gl.TEXTURE_2D);
    LA.fill(0); CA.fill(0);
    L.forEach((l, i) => { LA.set([l.x, l.y, l.r, l.a ?? 1], i * 4); CA.set([l.hue ?? 0, l.thick ?? 0.55, l.k ?? Math.max(2, l.r * 0.2), l.mag ?? 2], i * 4); });
    gl.uniform4fv(U('u_L'), LA); gl.uniform4fv(U('u_C'), CA); gl.uniform1i(U('u_n'), L.length); gl.uniform1f(U('u_t'), t);
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
    return cv;
  };
}
