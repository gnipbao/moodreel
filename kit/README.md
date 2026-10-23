# kit：影片代码的原语库

按时间绘制的页面（`window.render(t)`）用的 ES 模块，无依赖、全确定性：同一个 t 永远画出同一帧，可以任意顺序、
多进程渲染。`moodreel kit <项目>` 会把这些文件连同风格专属的 `tokens.js`、`motion.js` 复制进项目；影片目录再
复制一份，保持自包含。

| 模块 | 内容 |
|---|---|
| `stage.js` | 页面契约：`stage({ width, height, duration, fonts, images, draw })` 设置 `DUR`/`render`/`READY`，按设计尺寸绘制，任意输出尺寸自动缩放；`texts(fn)` 提供文字停留检查用的 `TEXTS` |
| `eases.js` | GSAP 命名的缓动（与 `moodreel/motion/eases.py` 同一套公式，测试保证一致）和 `bezier(x1, y1, x2, y2)` |
| `core.js` | `tween`、`value`、`keys`（分段关键帧）、`stagger`、`step`（一拍二）、带种子的 `rng`、`hash`、`noise1` |
| `texture.js` | `paper`（纸底与斑驳）、`grain`（颗粒）、`vignette`（暗角）、`screen`（网点）、`scanlines`（扫描线）、`misregister`（套色错位）。`grain` 和 `vignette` 的参数就是 `moodreel measure` 测出的数值，内部已按测量校准 |
| `text.js` | `fit`（按宽度定字号）、`wrap`（中英文换行）、`glyphs`（逐字位置，用于逐字动画） |
| `brush.js` | 绘画笔触：`stroke`（有宽度轮廓和毛边的笔触加鬃毛痕，`reveal` 控制画到哪里）、`wash`（水彩：多遍抖动叠加，边缘积色变深）、`dab`（刮刀：斜端、明暗抖动、受光起伏）、`crayon`（蜡笔：被纸纹打断的斑点）、`ink`（墨：芯加晕）、`repaint`（把用平涂画好的画面重画成刀块或笔触，沿边缘走，按画面颜色，缓存）；以及 `spine`、`ribbon`、`wobble`、`tooth` 几何工具。参数对应 `moodreel measure` 测出的 `TEXTURE.brush`（笔触边缘间距、方向、一致度） |
| `media.js` | 真实素材：`const M = await load()`（在 stage 之前，全部帧载完页面才算就绪），`M.frame(name, t, { from, rate, loop })` 取影片时间 t 对应的那一帧（素材按影片帧率存成一帧一张图，任何一帧都能单独渲染，不需要视频寻址），`M.still(name)`、`M.data(name)`（CSV 解析成对象数组、JSON 解析好）、`M.credit(name)`（来源和许可，可直接上字幕卡）。素材由 `moodreel media add` 放进 `media/` 并写进 manifest 和 CREDITS |
| `three.js` | 3D：`layer3d(w, h, { background, shadows, exposure, fov, toneMapping })` 建 three.js 场景、相机和 WebGL 渲染器，`draw(g)` 把这一帧的 3D 画到舞台上（字和叠加层照常用 2D 画在上面），`look(eye, target)`、`orbit(angle, radius, height)`、`toScreen(point)`（把字钉在世界里的一点上）。每个物体、灯光和相机都由 t 算出，不用时钟和会保留状态的动画混合器。three.js（MIT）由 `moodreel film new` 为需要 3D 的风格复制到 `kit/vendor/three/`，并写进 CREDITS |
| `pixel.js` | 像素画：`pixels(w, h, palette)` 建一张低分辨率的索引帧（`put`、`rect`、`line`、`disc`、按 Bayer 抖动的 `shade`、字符画 `sprite`、一像素描边 `outline`），`present` 按整数倍、不插值放大画到舞台上，可传查找表；`reduce`（降色深表）、`stepTable`（沿色阶提亮或压暗）、`nearest`、`snap`（镜头按整像素移动）。参数就是 `moodreel measure` 测出的 `TEXTURE.pixel`（倍数、原生尺寸、色数、抖动） |

风格专属（由测量生成）：

| 文件 | 内容 |
|---|---|
| `tokens.js` | `SIZE`、`PALETTE`（ground / ink / accent / secondary 和全部颜色）、`TYPE`（标题和正文行高占画面比例、字重；字体族先占位，由导演选定有授权的字体）、`LAYOUT`（边距、对齐、密度）、`TEXTURE`（颗粒、斑驳、暗角、网点、扫描线、边缘） |
| `motion.js` | `MOTION`（入场 / 出场 / 位移的缓动、时长、cubic-bezier、过冲比例、起始缩放、位移幅度，错峰、静止、镜头长度、转场、一拍几、镜头运动），以及 `enter(t, at, i)`、`exit`、`move` 三个便捷函数 |

```js
import { stage } from './kit/stage.js';
import { PALETTE, TYPE } from './kit/tokens.js';
import { enter } from './kit/motion.js';

stage({ width: 1920, height: 1080, duration: 6, background: PALETTE.ground, draw: (g, t) => {
  g.globalAlpha = enter(t, 0.4);
  g.fillStyle = PALETTE.ink;
  g.font = `${TYPE.titleWeight} ${TYPE.title * 1080}px ${TYPE.display}`;
  g.fillText('Hello', 160, 540);
}});
```
