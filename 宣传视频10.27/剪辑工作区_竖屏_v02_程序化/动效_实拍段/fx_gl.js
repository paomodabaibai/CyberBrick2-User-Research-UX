// WebGL 后期两道：fire 把分层赛璐璐爆炸画进底片；post 给整帧加冲击波折射、径向模糊、色散和冲击帧。纯函数，同样参数同样结果。
// 冲击波折射公式参考 pixijs/filters 的 shockwave.frag（MIT）；冲击帧的阈值剪影、反相交替参考 icitry/ImpactFramesGenerator。
const VS = `#version 300 es
in vec2 a; out vec2 v; void main(){ v = a * .5 + .5; gl_Position = vec4(a, 0., 1.); }`;

const FIRE = `#version 300 es
precision highp float; in vec2 v; out vec4 o;
uniform sampler2D T; uniform vec4 B[4]; uniform float K[4];
const vec2 RES = vec2(1080., 1920.);
const vec3 RAMP[10] = vec3[10](
  vec3(.05,.08,.25), vec3(.09,.25,.72), vec3(.22,.60,1.), vec3(.74,.93,1.), vec3(1.),      // 蓝：烟 深 中 亮 白
  vec3(.17,.05,.08), vec3(.86,.13,.09), vec3(1.,.50,.10), vec3(1.,.87,.42), vec3(1.)       // 红：烟 深 中 亮 白
);
float h(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float n2(vec2 p){ vec2 i = floor(p), f = fract(p); f = f * f * (3. - 2. * f);
  return mix(mix(h(i), h(i + vec2(1, 0)), f.x), mix(h(i + vec2(0, 1)), h(i + vec2(1, 1)), f.x), f.y); }
float fbm(vec2 p){ float a = .5, s = 0.; for (int i = 0; i < 5; i++) { s += a * n2(p); p = p * 2.03 + 17.1; a *= .5; } return s; }
void main(){
  vec3 col = texture(T, v).rgb; vec2 px = vec2(v.x, 1. - v.y) * RES;
  for (int i = 0; i < 4; i++) {
    float age = B[i].w; if (age < 0. || age >= 1.) continue;
    vec2 p = (px - B[i].xy) / B[i].z; float r = length(p);
    if (r > 2.2) continue;
    float rr = mix(.22, 1., 1. - pow(1. - age, 4.));
    vec2 q = p / rr * 1.5 + K[i] * 13.7 + age * .35;                     // 跟着半径一起胀开，不做径向滚动，否则会出靶心一样的同心环
    float w = fbm(q + 1.1 * vec2(fbm(q + 3.1), fbm(q + 7.7)));           // 域扭曲出翻滚的云团
    float body = rr * (.52 + .92 * w) - r;
    float heat = (1. - r / rr) * 1.55 + (w - .5) * 1.5 + (1. - age) * 1.0 - age * 1.45;
    int base = K[i] < .5 ? 0 : 5;
    vec3 c = RAMP[base];
    c = mix(c, RAMP[base + 1], smoothstep(.16, .19, heat));
    c = mix(c, RAMP[base + 2], smoothstep(.54, .57, heat));
    c = mix(c, RAMP[base + 3], smoothstep(.94, .97, heat));
    c = mix(c, RAMP[base + 4], smoothstep(1.34, 1.37, heat));
    float a = smoothstep(0., .018, body);
    a *= smoothstep(0., .04, 1.02 - age * 1.08 + (w - .52) * 1.25);       // 后期被噪声蚀穿
    a *= 1. - smoothstep(.86, 1., age);
    // 烟的部分用网点印刷的颗粒，避开写实烟雾的廉价感
    if (heat < .2) { vec2 g = mod(mat2(.707, -.707, .707, .707) * px, 15.) - 7.5; float dotR = mix(9.5, 3.5, clamp(age * 1.2 - heat, 0., 1.)); a *= smoothstep(dotR + .8, dotR - .8, length(g)); }
    float glow = exp(-max(r - rr * .9, 0.) * 5.) * (1. - age) * (1. - age);
    col += RAMP[base + 2] * glow * .55;
    col = mix(col, c, a);
  }
  o = vec4(col, 1.);
}`;

const POST = `#version 300 es
precision highp float; in vec2 v; out vec4 o;
uniform sampler2D T; uniform vec4 S[3]; uniform vec2 RC; uniform float RB, CA, DARK; uniform int MODE; uniform vec3 TEAM;
const vec2 RES = vec2(1080., 1920.); const float PI = 3.14159;
void main(){
  vec2 uv = v, px = vec2(v.x, 1. - v.y) * RES; float lit = 1.;
  for (int i = 0; i < 3; i++) {
    if (S[i].w <= 0.) continue;
    vec2 d = px - S[i].xy; float L = length(d), hw = 120. + S[i].z * .12, k = (L - S[i].z) / hw;
    if (abs(k) < 1. && L > 0.) { float p = 1. - k * k, off = 1.25 * sin(k * PI) * p * S[i].w; uv += vec2(d.x, -d.y) / L * off / RES; lit += .22 * p * S[i].w / 90.; }
  }
  vec2 c = vec2(RC.x, RES.y - RC.y) / RES, dir = uv - c; vec3 sum = vec3(0.);
  const int N = 10;
  for (int i = 0; i < N; i++) {
    float f = float(i) / float(N - 1), z = 1. - RB * f;
    vec2 u = c + dir * z, a = (u - c) * CA / 300.;
    sum += vec3(texture(T, clamp(u + a, 0., 1.)).r, texture(T, clamp(u, 0., 1.)).g, texture(T, clamp(u - a, 0., 1.)).b);
  }
  vec3 col = sum / float(N) * lit;
  float l = dot(col, vec3(.3, .59, .11));
  if (MODE == 1) { float m = smoothstep(.40, .46, l); col = mix(vec3(.02, .025, .06), vec3(1.), m); }     // 冲击帧：黑剪影白底
  if (MODE == 2) { float m = smoothstep(.40, .46, l); col = mix(TEAM, vec3(.015, .02, .05), m); }          // 反相：黑底、队色剪影
  if (DARK > 0.) { float q = length((v - .5) * vec2(1., 1.5)); col *= 1. - DARK * smoothstep(.12, .85, q); }
  o = vec4(col, 1.);
}`;

export function initGL() {
  const cv = document.createElement('canvas'); cv.width = 1080; cv.height = 1920;
  const gl = cv.getContext('webgl2', { preserveDrawingBuffer: true, antialias: false, alpha: false });
  if (!gl) throw new Error('没有 WebGL2');
  const prog = fs => {
    const sh = (t, s) => { const x = gl.createShader(t); gl.shaderSource(x, s); gl.compileShader(x); if (!gl.getShaderParameter(x, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(x)); return x; };
    const p = gl.createProgram(); gl.attachShader(p, sh(gl.VERTEX_SHADER, VS)); gl.attachShader(p, sh(gl.FRAGMENT_SHADER, fs)); gl.bindAttribLocation(p, 0, 'a'); gl.linkProgram(p);
    if (!gl.getProgramParameter(p, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(p)); return p;
  };
  const pF = prog(FIRE), pP = prog(POST), U = (p, n) => gl.getUniformLocation(p, n);
  gl.bindBuffer(gl.ARRAY_BUFFER, gl.createBuffer()); gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
  gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0);
  const tex = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, tex);
  for (const [k, x] of [[gl.TEXTURE_MIN_FILTER, gl.LINEAR], [gl.TEXTURE_MAG_FILTER, gl.LINEAR], [gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE], [gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE]]) gl.texParameteri(gl.TEXTURE_2D, k, x);
  gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, true); gl.viewport(0, 0, 1080, 1920);
  const up = src => gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, src);
  return {
    canvas: cv,
    // booms: [{x, y, R, age, team}] team 0 蓝 1 红；K 里带队色和噪声种子（整数位是队，小数位是种子）
    fire(src, booms) {
      gl.useProgram(pF); up(src);
      const B = new Float32Array(16).fill(-1), K = new Float32Array(4);
      booms.slice(0, 4).forEach((b, i) => { B.set([b.x, b.y, b.R, b.age], i * 4); K[i] = (b.team ? 0.5 : 0) + (b.seed % 7) * 0.06; });
      gl.uniform4fv(U(pF, 'B'), B); gl.uniform1fv(U(pF, 'K'), K); gl.drawArrays(gl.TRIANGLES, 0, 3);
    },
    post(src, o) {
      gl.useProgram(pP); up(src);
      const S = new Float32Array(12); (o.shock || []).slice(0, 3).forEach((s, i) => S.set(s, i * 4));
      gl.uniform4fv(U(pP, 'S'), S); gl.uniform2f(U(pP, 'RC'), o.rc?.[0] ?? 540, o.rc?.[1] ?? 960);
      gl.uniform1f(U(pP, 'RB'), o.rb ?? 0); gl.uniform1f(U(pP, 'CA'), o.ca ?? 0); gl.uniform1f(U(pP, 'DARK'), o.dark ?? 0);
      gl.uniform1i(U(pP, 'MODE'), o.mode ?? 0); gl.uniform3fv(U(pP, 'TEAM'), o.team ?? [1, 1, 1]); gl.drawArrays(gl.TRIANGLES, 0, 3);
    },
  };
}
