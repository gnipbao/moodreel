# GPU 图版和逐镜比对：把复刻做到"像"

节奏对了，画面还是"差一点"：细节不够、黑洞和怪物这种东西 2D 画布画不出来、动作的方向和速度跟原片不一样。
这一页讲三件事：怎么量出差在哪（`moodreel compare`），GPU 层能画什么（`kit/gl.js` 和它的伙伴），以及参考片的
源码公开时怎么把它的场景直接搬进来。做法和数值学自 [mexicat/pdoom-video](https://github.com/mexicat/pdoom-video)
（MIT，Copyright (c) 2026 Giacomo Magnanini）。

## 先量：`moodreel compare`

```sh
moodreel compare ref.mp4 remake.mp4                       # 按参考片自己的镜头切窗口
moodreel compare ref.mp4 remake.mp4 --shots shots.json    # 或者按自己的镜头表 [[t0, t1, "名字"], ...]
moodreel compare ref.mp4 remake.mp4 --every 4 --json out.json
```

两支片子缩到同样大小，每个窗口量五样，最差的排在前面，后面写着问题：

| 量 | 含义 | 读法 |
|---|---|---|
| structure | 亮度的 SSIM，0–1 | 低于 0.5：画的不是同一个东西 |
| detail | 高频能量之比（复刻 / 参考） | 低于 0.8：软、空；高于 1.4：比原片还碎 |
| tone | 平均亮度差，0–255 级 | 高于 12：整体偏亮或偏暗 |
| flow | 光流方向一致度，-1–1（4×4 格，两边都在动的格子） | 低于 0.2：往别的方向动；负数：反着动 |
| speed | 平均光流之比 | 0.7–1.4 之外：太慢或太快 |

只看静帧会漏掉 flow 和 speed：pdoom 复刻的 v5 静帧很像，可是 46 个镜头里光流一致度的中位数只有 0.1，速度中位数
0.6 —— 画面对了，动作没对。

## GPU 层：`kit/gl.js`

```js
import { gpu } from './kit/gl.js';
const G = gpu(1920, 1080);
const sky = G.pass(`uniform float uT;
  void main() { fragColor = vec4(heat(0.5 + 0.5 * fbm(vec3(vUv * 3.0, uT * 0.2), 4)), 1.0); }`, { uT: { value: 0 } });
const hdr = G.rt(), L = G.lines(20000);
draw: (g, t) => {
  sky.u.uT.value = t; sky.render(hdr);                       // 全屏着色器：线性 HDR，可以超过 1
  L.clear(); /* L.seg2(x0, y0, x1, y1, 宽度, [r, g, b]) 成千上万根 */ L.render(hdr);
  G.post(hdr.texture, { bloom: 0.6, ca: 1.2 });               // 辉光金字塔、晕光、色差、色调肩部、暗角
  G.show(g);                                                  // 放到 2D 舞台上，上面还可以继续画字
}
```

- `pass(frag, uniforms)`：全屏片元着色器，`vUv` 和 GLSL 库都在作用域里；`{ raw: true }` 写完整着色器，可以多输出
  （G-buffer）。`rt(w, h, { count })` 半浮点线性目标。
- `layer(w, h)`：一张 Canvas 2D 当纹理，`upload()` 之后着色器能读（字先在 2D 里画好，再在 3D 平面上"刻"出来）。
- `lines(n, { screen2D, worldWidth, blend })`：抗锯齿胶囊线段，2D 像素或经过相机的 3D；细于 0.7 px 的线变淡而不是变细，
  发丝线在 1080p 上也稳。版画排线、流线场、线框、毛发都用它。
- GLSL 库：`hash*`、`snoise`、`fbm`、`curl2`、`sd*` 距离场、`smin`/`smax`（平滑并集，长出有机体）、`hatch`/`engrave`
  （线宽随明暗变的版画排线）、`heat`（墨→信号橙→白热）、`toSRGB`；调色板是 `C_INK`、`C_BONE`、`C_SIGNAL`…，
  `gpu(w, h, { palette })` 换掉或加上。
- `post` 的默认值就是原片的：辉光 0.55、阈值 0.85、晕光 0.25、色差 1.2 px、暗角 0.35。颗粒默认关：在运动模糊下
  它每个子帧都会被平均掉，留给舞台的 `finish` 每帧画一次。

配套：`kit/outline.js` 从 TrueType 文件读字形轮廓（把字拆成碎笔画、填粒子、让火花描字）；`kit/anim.js` 是事件驱动的
时间工具（`pulse` 命中后衰减、`springStep`、`keys`、`frameIdx` 让抖动在快门里不重影、`path` 按弧长走）；舞台的
`faces` 按字族名注册字体文件，`prepare` 在字体就绪后、第一帧之前建好要量字的东西。

## 源码公开时：把场景搬进来

参考片的源码以宽松许可公开（MIT、BSD、Apache）时，最像的复刻是让它自己的场景在我们的渲染器里跑：

1. 只读源码，不运行它的脚本，不装它的依赖。
2. 用 Node 自带的类型剥离把 TypeScript 变成 JavaScript（`node:module` 的 `stripTypeScriptTypes`，transform 模式），
   只改 import 路径。
3. 写一层兼容层，把它引擎的接口接到 `kit/gl.js`、`kit/anim.js` 和片子自己的数据上：场景基类、全屏 pass、图层、
   线段批、歌词和音频对象、字体和排版、调色板、HUD。场景一行不改。
4. 用 `moodreel compare` 逐镜对照；源码当前版本和发布的视频对不上的段落（作者后来又改过），保留自己画的镜头。
5. 每个文件头写来源和许可；NOTICE 和 CREDITS 里列出；歌曲和歌词的权利不随代码的 MIT 许可过来。

## pdoom 复刻的结果

`moodreel compare`，以原片自己的镜头为窗口，整片中位数：

| | structure | detail | tone | flow | speed | 综合 |
|---|---|---|---|---|---|---|
| v5：手画的镜头，数据驱动的节奏 | 0.43 | 0.76 | 9.7 | 0.11 | 0.64 | 0.52 |
| v6：源码自己的图版，经兼容层跑在 `kit/gl.js` 上 | 0.93 | 1.08 | 1.3 | 0.91 | 1.02 | 0.93 |

最典型的几段：多眼怪物 structure 0.36 → 0.96、flow 0.11 → 0.87；示波器 0.41 → 0.97；黑洞 0.29 → 0.93、
flow 0.15 → 0.99；"原子重组成回形针" flow −0.64 → 0.98（原来是反着动的）。

结尾是个例外：源码仓库比发布的视频新一版（无穷大先变 8 和 0/0 再变 NaN，最后倒带回开场），直接用的话最后五秒
综合只有 0.71。用 `compare --offset` 找出每段的最佳时移，给图版加一条时间映射（跳过新加的两步、爆开放慢、在静止的
Regenerate 画面上追回来），最后一秒半用手画的镜头，结尾升到 0.85。
