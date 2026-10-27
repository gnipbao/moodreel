# kit：影片代码的原语库

按时间绘制的页面（`window.render(t)`）用的 ES 模块，无依赖、全确定性：同一个 t 永远画出同一帧，可以任意顺序、
多进程渲染。`moodreel kit <项目>` 会把这些文件连同风格专属的 `tokens.js`、`motion.js` 复制进项目；影片目录再
复制一份，保持自包含。

| 模块 | 内容 |
|---|---|
| `stage.js` | 页面契约：`stage({ width, height, duration, fonts, faces, images, prepare, draw, finish })` 设置 `DUR`/`render`/`READY`，按设计尺寸绘制，任意输出尺寸自动缩放；`faces` 按字族名注册字体文件，`prepare` 在字体和图片就绪后、第一帧之前跑一次（要量字的东西在这里建）；`texts(fn)` 提供文字停留检查用的 `TEXTS`。运动模糊：渲染器 `--samples N --shutter s` 时，每帧是快门内 N 个子帧的平均，`draw` 每个子帧画一次，`finish(g, t, src)` 在平均好的画面上跑一次（颗粒、暗角、闪光） |
| `music.js` | 跟着歌走：`music(AUDIO, LYRICS)` 读 `moodreel music` 写的 `music-data.js`，给出 `hit`（鼓点冲击）、`env`（包络）、`beatAt`/`barAt`、`ct`（踩拍的镜头时钟）、`step`、`sung`/`letters`/`span`（词在什么时候真正被唱出）、`slams`（砸字）；`pop`（字落下）。做法和数值见 docs/MUSIC-SYNC.md |
| `gl.js` | GPU 层：`gpu(w, h)` 给出全屏着色器 pass（`pass`，HDR 半浮点目标 `rt`，多输出 G-buffer）、Canvas 图层当纹理（`layer`）、每帧成千上万根抗锯齿发丝线（`lines`，2D 像素或带相机的 3D）、混合模式合成（`comp`）和胶片后期（`post`：辉光金字塔、晕光、色差、色调肩部、饱和度、暗角、抖动和推近）；GLSL 库里有哈希、simplex 噪声、fbm、curl、2D/3D 距离场、平滑并集、版画排线和热度色阶。光线步进的生物、引力透镜、流线场都靠它。做法见 docs/GPU.md |
| `anim.js` | 按事件驱动的时间工具：`prog`（缓动进度）、`pulse`（命中后衰减）、`springStep`（弹簧阶跃）、`keys`（关键帧）、`frameIdx`（整帧不变的种子，抖动不在运动模糊里重影）、`hash`、`noise1`、`path`（按弧长走折线） |
| `outline.js` | 从 TrueType 文件读字形轮廓：`outline(buffer).charToGlyph(ch).getPath(x, y, size).commands`、`path2D`；简单和复合字形，cmap 4 和 12；用来把字拆成笔画、填粒子、让火花描字 |
| `eases.js` | GSAP 命名的缓动（与 `moodreel/motion/eases.py` 同一套公式，测试保证一致）和 `bezier(x1, y1, x2, y2)` |
| `core.js` | `tween`、`value`、`keys`（分段关键帧）、`stagger`、`step`（一拍二）、带种子的 `rng`、`hash`、`noise1` |
| `texture.js` | `paper`（纸底与斑驳）、`grain`（颗粒）、`vignette`（暗角）、`screen`（网点）、`scanlines`（扫描线）、`misregister`（套色错位）；收尾用的 `bloom`（光晕）、`halation`（高光周围的橙红晕）、`aberrate`（色差）。`grain` 和 `vignette` 的参数就是 `moodreel measure` 测出的数值，内部已按测量校准 |
| `text.js` | `fit`（按宽度定字号）、`wrap`（中英文换行）、`glyphs`（逐字位置，用于逐字动画） |
| `brush.js` | 绘画笔触：`stroke`（有宽度轮廓和毛边的笔触加鬃毛痕，`reveal` 控制画到哪里）、`wash`（水彩：多遍抖动叠加，边缘积色变深）、`dab`（刮刀：斜端、明暗抖动、受光起伏）、`crayon`（蜡笔：被纸纹打断的斑点）、`ink`（墨：芯加晕）、`repaint`（把用平涂画好的画面重画成刀块或笔触，沿边缘走，按画面颜色，缓存）；以及 `spine`、`ribbon`、`wobble`、`tooth` 几何工具。参数对应 `moodreel measure` 测出的 `TEXTURE.brush`（笔触边缘间距、方向、一致度） |
| `variant.js` | 批量变体：`pick(key, 默认值)` 读 film.json 里 `variants` 的参数（渲染器以 `window.VARIANT` 传进页面）；同一份画面代码，换调色板、种子、一句文案或片长，`moodreel film deliver --variant 名` 或 `--all-variants` 各出一条 |
| `media.js` | 真实素材：`const M = await load()`（在 stage 之前，全部帧载完页面才算就绪），`M.frame(name, t, { from, rate, loop })` 取影片时间 t 对应的那一帧（素材按影片帧率存成一帧一张图，任何一帧都能单独渲染，不需要视频寻址），`M.still(name)`、`M.data(name)`（CSV 解析成对象数组、JSON 解析好）、`M.credit(name)`（来源和许可，可直接上字幕卡）。素材由 `moodreel media add` 放进 `media/` 并写进 manifest 和 CREDITS |
| `three.js` | 3D：`layer3d(w, h, { background, shadows, exposure, fov, toneMapping })` 建 three.js 场景、相机和 WebGL 渲染器，`draw(g)` 把这一帧的 3D 画到舞台上（字和叠加层照常用 2D 画在上面），`look(eye, target)`、`orbit(angle, radius, height)`、`toScreen(point)`（把字钉在世界里的一点上）。每个物体、灯光和相机都由 t 算出，不用时钟和会保留状态的动画混合器。three.js（MIT）由 `moodreel film new` 为需要 3D 的风格复制到 `kit/vendor/three/`，并写进 CREDITS |
| `lock.js` | 复刻的主体和镜头按参考片的画面对位：`lock(cam, TRACK, { set, moving }, { spans })` 读 `moodreel track --js` 写的 `track-data.js`（Jev 视觉在参考片每帧里框出的每个主体：`[t, seen, cx, cy, w, h]`），每个采样时刻做一次联合求解：镜头移动和转向（x、y、z、偏航、俯仰）加上可移动的主体沿允许的轴滑动（站在键盘上的小怪只在 x、z 上动，空中还能升降），让每个主体在画面里的可见部分（近裁剪面和画框都裁过）落在参考片的框里，Jev 没看到的主体推出画面；每一刻的解贴近上一刻（`hold`），镜头修正按 0.3 秒、主体按 0.2 秒高斯平滑（不给画面加参考片没有的运动），在片段两端淡入淡出（剪切点除外）。只靠框分不出镜像，加两个键位（空格、Esc）给出朝向。河、镇、人群这种不成一个凸体的主体写成 `{ cloud: points }`，取画面内那些点的外框。只锁布局已经和参考片一致的主体：布局不同时锁定只会让镜头停住（俯掠的运动掉到参考片的 0.31 倍）。`window.REPORT = () => L.report` 后 `node render/render.mjs report <影片>` 打印每个主体修正前后的像素误差。做法见 `skills/moodreel/references/distill/remaking.md` |
| `follow.js` | 复刻的镜头按参考片的走：`follow(MOTION, anchors, end, { own })` 读 `moodreel camera --js` 写的 `camera-data.js`（参考片每秒 15 次的画面平移、推拉、滚转），把测到的转向和推拉加在穿过几个锚点的平滑路径上：锚点处镜头站在、看向你定的位置，锚点之间按参考片的节奏摇、推。推拉沿当时的视线方向积分；滚转只听锚点（累加测到的滚转会漂）；`own` 里的时段（画面读的是主体而不是镜头，比如暗场里落下的碎块）锚点就是普通关键帧。锚点的 `speed` 定镜头经过它的快慢（0 即停，同 `ease`；1.5 冲过去），`speed: [进, 出]` 让进出不同：`[0.3, 1.7]` 是被跺脚震开的猛退，`[1.4, 0.2]` 是冲进去急停；`{ pace: true }` 让锚点之间的路径按参考片测到的速度走（参考片停它就等，参考片冲它就冲），每个运镜的形状（冲向揭示时加速、进入停顿时减速）直接来自参考片，`moodreel camera --against` 按三段速度核对。做法见 `skills/moodreel/references/distill/remaking.md` |
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
