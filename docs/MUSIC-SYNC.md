# 卡点：让画面跟着歌走

音乐片的"卡点感"不是调出来的，是算出来的：每个动作都从歌的数据里来——节拍网格、小节、鼓点、人声、逐词歌词，
而不是从画面或缩略图里估时间。这套做法学自 [mexicat/pdoom-video](https://github.com/mexicat/pdoom-video)
（MIT，Copyright (c) 2026 Giacomo Magnanini），一支每一帧都由歌曲时间算出的音乐录像；下面的配方和数值都出自它的源码。

## 为什么

复刻这支片子时，我们先按 0.2 秒一张的缩略图手工估时间，画面像了，节奏却始终差一口气。和源码对齐的歌词比：

- 手估的词时间误差中位数 66 ms，四分之一超过 127 ms；只有 13% 落在一帧以内，35% 在 50 ms 以内。
- 速度估成 132.5 BPM，真值是 132.007：越往后拍子漂得越远。
- 强动作落在重音上的比例 43%，和随机差不多（原片 66%）。
- 没有运动模糊：快动作是一格一格跳过去的，不是划过去的。

换成数据驱动之后，歌词每个字都在唱出来的那一帧落下，切点、推拉、砸字都踩在真实的鼓点和拍子上。

## 数据：`moodreel music`

```sh
moodreel music song.wav --out film/music-data.js                      # 从混音分析
moodreel music song.wav --lyrics words.json --out film/music-data.js  # 加上逐词歌词
moodreel music audio.json --lyrics lyrics.json --offset 0.048 \
  --credit "from mexicat/pdoom-video, MIT" --out film/music-data.js   # 导入别处做好的分析（pdoom-video 的格式）
```

写出的 `music-data.js` 是 `export const AUDIO = {...}; export const LYRICS = [...]`：

- `bpm`、`beats`（恒定速度网格，整首歌拟合，相位按底鼓修正）、`downbeats`（小节：军鼓在 2、4 拍）、`sections`；
- `onsets`：`kick`、`snare`、`hat`、`vocal`，每个是 `[时间, 力度 0–1]`；
- `features`：100 fps 的包络 `rms`、`low`、`mid`、`high`（导入的数据还可能有分轨包络 `vocal`、`drums`、`bass`）；
- `LYRICS`：`[{text, start, end, words: [{w, start, end}]}]`。

逐词歌词来自任何对齐工具的输出，三种形状都认：pdoom-video 的 `{"lines": [...]}`、行的列表、或一串词 `[{w, start, end}]`。
没有分轨和对齐时，鼓点按频段从混音里找，并要求落在 4/4 律动该在的位置（底鼓在拍上、军鼓在 2、4 拍、镲在八分音符上），
流行和舞曲大多如此；其他音乐加 `--no-grid`。

### 校准（在 pdoom-video 自己的歌上，对照它用分轨和强制对齐做出的数据）

| 项 | 结果 |
|---|---|
| 速度 | 132.002 BPM，真值 132.007 |
| 拍点 | 345 个全部在 15 ms 以内 |
| 小节 | 87 个全部正确 |
| 底鼓 | 召回 0.88，精确 0.97 |
| 军鼓 | 召回 0.89，精确 0.83 |
| 镲 | 召回 0.73，精确 0.47 |

起音时刻按合成鼓点校准（采样级真值）：频段能量在 Hann 窗里上升最陡时，起音在窗的四分之三处。在原歌上，我们的鼓点比
pdoom-video 标的晚约 20–33 ms（它标的是更早的起点）。复刻一支用别人数据做的片子时，直接导入那份数据，不要重新检测。

还没做：分轨（Demucs）和歌词强制对齐（Whisper / CTC）要下载模型，之后再加；段落检测；按区块自适应的子帧数。

## 用：`kit/music.js`

```js
import { AUDIO, LYRICS } from './music-data.js';
import { music, pop } from './kit/music.js';
const M = music(AUDIO, LYRICS);
```

| 函数 | 用途 |
|---|---|
| `M.hit(kind, t, half)` | 鼓点或人声的冲击：命中时为力度，按半衰期衰减。底鼓轻推画面、色差随之加大 |
| `M.env(name, t)` | 包络 0–1：响度驱动亮度、粒子、呼吸 |
| `M.beatAt(t)`、`M.barAt(t)`、`M.timeOfBeat(i)`、`M.nearestBeat(t)` | 节拍和小节：切点、频闪、每拍一跳 |
| `M.ct(t)` | 镜头时钟：每拍刚过时跑得快、下一拍前慢下来。`keys(镜头关键帧, M.ct(t))` 让平滑的运镜变成踩拍的一冲一停 |
| `M.step(t, at, dur)` | 按镜头时钟走的进度：增长、计数、堆叠一步一跳 |
| `M.sung(text, t)` | 这句词在 t 附近真正被唱出的时刻；不是歌词（标签、注释）就原样返回 t |
| `M.letters(text, t)` | 第 i 个字母何时点亮：均分演唱时长，长音不拖慢（最多 0.09 s 一个） |
| `M.span(text, t)`、`M.line(q, n)`、`M.progress(word, t)` | 词的起止、整行、唱到百分之几 |
| `M.slams(starts, {shake})` | 砸字：返回 `t => {s, x, y}`，交给收尾去缩放和抖动整帧 |
| `pop(age)` | 字落下：先大 20%，0.16 s 指数回落，不回弹 |

## 规则（出自 pdoom-video 的 TREATMENT 和源码）

1. **不手调时间。** 画面里的词在它的 `start` 出现或高亮，在 `end` 前完成；可以提前几百毫秒显示淡淡的虚影，高亮绝不抢在嗓音前。
2. **切点**落在"这句第一个词之前的最后一拍"，绝大多数是硬切。
3. **命中**：底鼓让画面轻推 1–3%，色差随命中从 1.2 px 往上加；大的抖动和闪光只留给特定的砸点。
4. **砸字**：每个词大 14% 落下，0.16 s 指数回落；停住的词每秒向镜头爬 3.5%；每次砸字反色两帧；抖动 7–26 px，50 ms 半衰，种子用帧序号。
5. **镜头**：在拍点上冲、在拍点之间停，或缓入强拍；不要漂浮的通用运动。用强缓动（`outExpo`、`inOutCubic`）和停顿，再一下打断。
6. **运动模糊**：每帧是快门内若干子帧的平均（`render.mjs --samples 8 --shutter 0.2`，快门是帧时长的五分之一）；
   每帧都要变的抖动和闪烁用帧序号做种子（`Math.round(t * fps)`），否则一帧里会叠出两个状态。
7. **后期**：光晕只给高光（阈值约 0.85），halation 0.25，色差 1.2 px，颗粒；纸面（亮底）画面不加光晕和 halation，深色字才不会起黑边。

## 收尾：`kit/stage.js` 和 `kit/texture.js`

`stage({ draw, finish })`：`draw(g, t)` 每个子帧画一次，只能依赖 t；`finish(g, t, src)` 每帧在平均好的画面上跑一次，
放颗粒、暗角、闪光和读取画面的效果。`kit/texture.js` 新增 `bloom`、`halation`、`aberrate`（色差，放在收尾的第一步）。

```js
stage({ width: 1920, height: 1080, duration: 30,
  draw: (g, t) => { /* 画面 */ },
  finish: (g, t, src) => { aberrate(g, src, 1.2 + 2 * M.hit('kick', t)); bloom(g, src, 0.6); halation(g, src, 0.25);
                           vignette(g, g.canvas.width, g.canvas.height, 0.3); grain(g, 6, Math.round(t * 60)); } });
```

## 许可

`kit/music.js` 的冲击衰减和砸字配方、本文的规则和数值改编自 mexicat/pdoom-video，按其 MIT 许可保留版权声明，见仓库根目录的 `NOTICE`。
