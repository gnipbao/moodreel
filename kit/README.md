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
