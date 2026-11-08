# kit/3dcv：3DCodeVerse 展示片的画面引擎

> 许可：**CC BY-NC-SA 4.0**（署名—非商业性使用—相同方式共享），只能非商用，详见同目录的 `LICENSE`。仓库其余部分是 MIT，不包含这里的代码。

这里的代码移植自 [3DCodeVerse](https://github.com/gaoypeng/3dcodeverse) 的
[awesome showcase](https://huggingface.co/datasets/3dcodeverse/3dcodeverse-awesome-showcase)：那部 30 秒影片代码里的
`src/core/`（r02 轮）。只搬了和具体影片无关的通用部分：材质、后期、绘制纹理、笔画字、确定性工具，以及镜头的运行时；
镜头、场景、人物、道具和资产都没有搬。`look.js`、`post.js`、`paint.js`、`util.js` 除了文件头和 three.js 的导入行，
逐行就是原文；`text.js` 另外把两个引用影片画面文字的默认值换成了中性的 `['TITLE']` 和 `'HELLO'`；`stage.js` 改写成了
moodreel 舞台用的镜头适配器。完整的改动清单在 `LICENSE`。源码注释里提到的 `CORE_API.md` 是原展示片的接口说明，没有搬进来，
这份 README 就是这里的说明。

## 模块

| 文件 | 内容 |
|---|---|
| `look.js` | 色彩渐变材质 `LookMaterial`（`material(opts)`、`preset(名字, 覆盖)`、`set(mat, opts)`）。不是物理光照：每种材质有亮部、中间调、暗部三个颜色，按包裹后的漫反射在 gamma 2 的感知空间里混合；场景里第一盏平行光（投影的排在前面）是渐变的主光，颜色要接近白色。上面叠交界线的强调色、背光一侧气笔式的紫色形体阴影、暖色的地面反光、轮廓光、小块手绘形状的高光（`spec`）和风格化的环境反射（`reflect`）。点彩固定在表面上：格点按屏幕导数换算成约一个输出像素，镜头移动时点跟着表面走；色调先抖动再查渐变，所以点聚在交界线、暗部和投影边缘，每个点都是渐变里本来就有的颜色，`boil` 那部分按原画重新随机。软阴影是 16 或 24 次 Vogel 采样；雾可以分朝光的暖色和背光的冷色，并按视线仰角和天空耦合。`PRESETS` 是一套调好的材质（皮肤、头发、几种布料、陶土、地面、纸、玻璃、银、发光体、背景板……）。所有材质和天空共用的 `env`：`setEnv`、`resetEnv`、`ENV_DEFAULTS`、`setFrame`。另有 `skyDome`（按仰角分段的渐变天空，可带太阳、侧向色块和绘制的云，渐变本身也抖出颗粒）、`gradientBackground`、`shadows(root)` |
| `post.js` | 后期链 `new Post(renderer, w, h, ss)`，每帧 `post.render(scene, camera, params, frame)` 一次：场景以 `ss` 倍超采样、4× MSAA 渲进半浮点目标 → 带紫色调的 SSAO（可加第二圈大半径）→ 景深 → 不受景深影响的叠加层（`overlay`）→ 运动模糊（`motion`）→ 保持饱和度的辉光和气笔扩散 → 合成（屏幕雾、门洞、曝光、高光肩部、sRGB、调色、暗角）→ 镜头（桶形、鱼眼；比相机视角更广时改渲立方体各面再重映射）→ 可选的各向异性 Kuwahara 绘画滤镜 → 下采样加锐化，最后在输出像素网格上加按色调加权的颗粒（暗部和中间调强，亮部几乎干净）、稀疏的暗点和 3–9 px 的气笔斑驳。材质点彩的参数（`dither`）也由它每次写进 `env`。颗粒和点彩的种子按原画帧号换（`grain.hold`，默认 2 帧一换），`grain.flicker` 那部分每个输出帧都换。参数是普通对象，每次在一份新的 `defaultPostParams()` 上深合并（`mergeParams`），帧与帧之间不留状态。`renderToTexture` 把一个场景不经后期渲成 HDR 纹理（比如门洞里的另一个世界） |
| `paint.js` | Canvas 2D 画的纹理，转成 three.js 纹理：`canvas`、`texture`、`fill`、`gradient`、`blotches`（软色块）、`strokes`（有方向的笔触）、`blocks`（平涂色块）、`noise`、`valueNoise2`、`fbm`（斑驳）、`strata`（带受光边和阴影的波状色带：山坡、峡谷、梯田）、`speckle`（细点）、`paper`、`painted`（一次调用按顺序叠好几层，`repeat` 时自动无缝）和 `clouds`（给 `skyDome` 的绘制云）。随机数都带种子，同一个种子画出同一张 |
| `text.js` | 不用字体的矢量笔画字，字形骨架自带（A–Z 和几个标点）：`drawRoman`、`titleTexture` 是宽笔尖粗细对比、带托架衬线的罗马大写；`createWriter` 是手写的单线大写，按笔顺一笔一笔写出（`update(进度)`），给出笔尖位置（`nibAt`），刚写下的墨可以发光（`glowTexture` 当 emissiveMap 用）；`layout`、`GLYPHS` |
| `util.js` | 不碰页面和渲染器的确定性工具：`FPS`（24）、`frameTime`、`clamp`、`lerp`、`invLerp`、`remap`、`smoothstep`、`smootherstep`、`deg`、`mixValue`、缓动 `ease`、带种子的 `rng`（mulberry32：`range`、`int`、`pick`、`normal`、`fork`……）、`hash1`、`noise1`、`fbm1`、关键帧 `track`（ease / linear / catmull / step）、`spline`、`cameraRig`（位置、目标、视角、滚转，加确定性的手持漂移） |
| `stage.js` | 镜头适配器 `film()`（下面细说）、`setupShadows`、`keyLight`，以及 `util.js` 的全部导出 |

## 在影片里用

```js
import { stage } from './kit/stage.js';
import { THREE } from './kit/three.js';
import * as cv from './kit/3dcv/stage.js';
import * as look from './kit/3dcv/look.js';
import * as paint from './kit/3dcv/paint.js';

const W = 1920, H = 1080;

const roll = {
  id: 'roll', frames: [1, 72], hold: 2,             // 全片第 1–72 帧（3 秒），两帧一换
  init(ctx) {
    ctx.keyLight(ctx.scene, { dir: [-0.6, 1, 0.5], shadow: { size: 1024, extent: 4 } });
    const floor = new THREE.Mesh(new THREE.PlaneGeometry(12, 12),
      look.preset('floor', { map: paint.painted({ w: 512, base: '#ffffff', fbm: { seed: 3, alpha: 0.2 }, repeat: [3, 3] }) }));
    floor.rotation.x = -Math.PI / 2;
    this.ball = new THREE.Mesh(new THREE.SphereGeometry(0.6, 96, 48), look.preset('clay'));
    ctx.scene.add(floor, this.ball);
    look.shadows(ctx.scene);
    ctx.scene.add(look.skyDome());
    this.x = ctx.track([[1, -1.5], [72, 1.5]]);
    ctx.camera.position.set(0, 1.6, 5);
    ctx.camera.lookAt(0, 0.5, 0);
  },
  render(ctx, n) {                                  // n 的纯函数：会动的东西每帧都按 n 设一遍
    this.ball.position.set(this.x(n), 0.6, 0);
    return { grain: { amount: 0.03 }, vignette: { amount: 0.2 } };   // 交回后期参数，适配器拿它画 ctx.scene 和 ctx.camera
  },
};

const film = cv.film({ width: W, height: H, shots: [roll] });
stage({ width: W, height: H, duration: 3, prepare: () => film.init(), draw: (g, t) => film.draw(g, t, W, H) });
```

`film.init()` 放在 `stage({ prepare })` 里：它是异步的，建渲染器，给每个镜头建一个 ctx，再按顺序 await 每个镜头的 `init`。
`film.draw(g, t, w, h)` 放在 `draw` 里：算出 t 所在的全片帧号 n = `Math.floor(t * 24 + 1e-4) + 1`，把这一帧渲进
`film.canvas`，再画到舞台上。WebGL 画布在页面之外，从不放进页面，舞台的 2D 画布仍是页面上唯一的 `body > canvas`
（FrameVelo 录的就是它）。影片页面不需要 import map：这些模块从 `kit/three.js` 取 three.js，和 kit 里其他 3D 模块共用一份。

`cv.film({ width, height, ss = 2, shots, extras = {}, query = '' })`

- `width`、`height`：WebGL 画布的输出像素。
- `ss`：没写自己 `ss` 的镜头用的超采样倍数（1–3）。每种倍数建一个 `Post`，所有镜头共用一个渲染器。
- `shots`：镜头模块的数组，见下。
- `extras`：合并进每个 ctx，比如影片自己的模块 `{ props, kit }`；同名的会盖掉内置字段。
- `query`：`ctx.query`（URLSearchParams）读的字符串。原页面从地址栏读的几个开关照样有效：`hold=<n>` 覆盖所有镜头的
  每张原画帧数，`ss=<n>` 覆盖所有镜头的超采样，`nopost=1` 关掉后期各级（看材质本身），`post=<json>` 深合并到每次 draw 的参数上。

另外：`film.frameOf(t)`；`film.shotAt(n)` 是帧 n 所在的镜头，没有就是 `null`，范围重叠时取列在前面的；`film.render(n)`
把全片第 n 帧画进 `film.canvas`，没有镜头覆盖这一帧时返回 `false`（`film.draw` 这时什么都不画）；`film.canvas`；
`film.renderer`（init 之前是 `null`）；`film.contexts`（每个镜头一个 ctx，按 `shots` 的顺序）。

### 镜头模块

```js
export default {
  id: 'sh1',                // 可选，即 ctx.shotId；不写就是它在 shots 里的序号
  frames: [1, 139],         // 必填：全片帧号范围（24 fps，t = 0 是第 1 帧）
  hold: 2,                  // 可选：两帧一换（见下），默认 1
  ss: 2,                    // 可选：超采样倍数
  async init(ctx) { },      // 可选：建场景，只跑一次；纹理之类在这里 await
  render(ctx, n) { },       // 必填，同步：n 的纯函数
};
```

`init` 和 `render` 都作为镜头对象的方法调用，`this` 就是镜头，句柄可以挂在 `this` 上。`render` 每帧把会动的东西按 n 重设一遍，
然后用 `ctx.draw(scene, camera, params)` 自己画；或者返回后期参数，适配器用它们画 `ctx.scene` 和 `ctx.camera`；
什么都不返回就用 `ctx.postParams`。要绕过后期，就自己用 `ctx.renderer` 画到画布（渲染目标 `null`），再把 `ctx._drawn`
设成 `true`。不许用 `Date`、`Math.random`（用 `ctx.rng(种子)`）和跨帧累积的状态。moodreel 的 `render(t)` 是同步的，
`render` 返回 Promise（比如写成了 `async render`）会抛出错误：要等的东西都放进 `init`。

### ctx

| 字段 | 含义 |
|---|---|
| `THREE`、`renderer`、`post`、`look`、`paint`、`text` | three.js、共用的渲染器、这个镜头的 Post（按它的 ss）和各模块；再加上 `extras` |
| `w`、`h`、`aspect`、`query`、`shotId`、`shot`、`FPS` | 画布尺寸、URLSearchParams、镜头模块、24 |
| `frame` | 正在画的原画帧号（两帧一换时是 n − n % hold） |
| `outFrame` | 真正输出的帧号 n。后期的 `grain.flicker` 按它换种子，所以同一张原画的两帧仍有细微的闪动；必须每帧都动的东西用它 |
| `time(n)`、`local(n)`、`progress(n)` | 全片秒数 (n − 1) / 24、从镜头第一帧起的秒数、镜头内 0..1 的进度 |
| `rng`、`hash1`、`noise1`、`fbm1`、`ease`、`track`、`spline`、`cameraRig`、`clamp`、`lerp`、`invLerp`、`remap`、`smoothstep`、`smootherstep`、`deg`、`mixValue` | 来自 `util.js` |
| `keyLight(scene, o)`、`setupShadows(light, o)`、`loadTexture(url, { srgb })` | 主光（返回 DirectionalLight，默认带软阴影）、阴影设置、异步读纹理（在 init 里用） |
| `scene`、`camera` | 这个镜头自己的 Scene 和 PerspectiveCamera（35°，近 0.05，远 400） |
| `postParams` | 这个镜头的默认后期参数（一份 `defaultPostParams()`） |
| `draw(scene, camera, params)` | 经后期链画到画布；透视相机的 aspect 会被设成画布的 |
| `renderToTexture(scene, camera, slot, params)` | 不经后期渲成 HDR 纹理，只在这一帧有效；传入它要合进去的那次 draw 的参数，点彩和镜头补偿才对得上 |

### 两帧一换

`hold: 2` 时，全片第 n 帧画的是原画帧 d = max(frames[0], n − n % 2)：偶数帧开始一张新原画，下一帧沿用。
`look.setFrame(d)` 和 `ctx.frame` 拿到 d，`ctx.outFrame` 和 `post.outFrame` 拿到 n。后期的颗粒和材质的点彩按 d 换种子，
`grain.flicker`（默认 0.1）那部分按 n 换：要两帧逐像素相同，就把 flicker 设成 0。`query` 里写 `hold=1`，所有镜头就每帧一张。

### 每一帧都和之前画过什么无关

一页里有好几个镜头，而镜头会改全局状态：look 的 `env` 是所有 LookMaterial 和天空共用的 uniform，渲染器的设置也是共用的。所以适配器：

- 建好渲染器先记下初始状态，每个镜头的 `init` 都从这个状态开始，和它单独在一页里时一样；
- 每个镜头 `init` 之后，记下它留下的状态：`look.env` 里每个 uniform 的值；渲染器的色调映射和曝光、阴影贴图（开关、类型、
  自动更新）、清屏颜色和 alpha、输出颜色空间、局部裁剪、自动清屏、视口和裁剪框；
- 画这个镜头的每一帧之前，先把这份状态放回去（它的 `render` 可以再改）。

所以同一帧画两次逐像素相同，先画别的镜头再画回来也相同，和只有这一个镜头的影片也相同（`tests/test_3dcv.py` 验证）。
镜头自己的东西（场景、相机、挂在 `this` 上的对象）仍要在 `render` 里按 n 设好。

## 和 kit/look3d.js、kit/post3d.js 的关系

`kit/look3d.js`（`ramp()` 材质、点彩、原画时钟）和 `kit/post3d.js`（`chain()` 后期链）是 moodreel 自己的 MIT 模块：
只借了思路，代码另写，接口也不同。`ramp()` 不读场景里的灯，光的方向写在材质上；`chain()` 的参数是一层扁平的数值。
`kit/3dcv` 是展示片的原代码：材质跟着场景里的第一盏平行光走，后期参数是展示片的那套结构，适合照原片的做法重现它的画面，
或者直接用它调好的预设。两者可以放进同一部影片，都用 `kit/three.js` 的同一份 three.js。要以 MIT 发布的新东西用
look3d 和 post3d。

## 许可的边界

- 这个目录是 **CC BY-NC-SA 4.0**（[许可证](https://creativecommons.org/licenses/by-nc-sa/4.0/)）：要署名（保留每个文件开头的
  文件头和 `LICENSE`），**不得商用**，改编后的这些文件仍按 CC BY-NC-SA 4.0 发布。
- 仓库其余部分是 MIT，不包含这些代码。**不要把 kit/3dcv 的代码复制或改写进 MIT 文件**（kit 的其他模块、`moodreel/`、
  `tests/`、影片模板……）。MIT 那边需要同样的效果时，只按思路自己写，像 look3d 和 post3d 那样。
- 新影片默认不带 kit/3dcv。`moodreel film new <片名> --style <风格> --with 3dcv` 才把它连同 `LICENSE` 复制进影片（README
  不复制），同时放好 three.js，并在影片的 CREDITS 里写明出处和许可。在影片里它们仍是 CC BY-NC-SA 4.0：带着 kit/3dcv 的
  影片只能非商用。`moodreel wall make` 一律不带它。
