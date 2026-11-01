# 人工测试计划（v0.1.0 之后）

自动测试（145 个）、运动测量基准、往返测试和盲蒸馏都已通过。人工测试要回答三件事：

- 测量在你的真实素材上是否准；
- 风格帧和成片在人眼里是否像参考；
- 每个功能按文档走一遍是否顺。

前两件对应设计方案 §8 里还没跑的两行（风格帧、端到端），以及 W2/W3 的真实素材校准。

每一项做完，在本文末尾的表里记一行。遇到问题，记下命令、项目或影片目录、终端输出（或截图），以及你期望看到什么。

## 0. 准备

需要 macOS（Apple 芯片）、[uv](https://docs.astral.sh/uv/)、ffmpeg、Node 22.18 以上。

```bash
uv sync && npm install
```

```bash
uv run moodreel csd setup
```

```bash
uv run moodreel samples fetch
```

后两步各下载一次：CSD 风格嵌入（2.4 GB，保留 0.6 GB）和采样乐器（272 MB）。不装也能测，只是 frame-check 不比较风格本身，采样乐器的配乐也渲染不了。

先确认环境：

```bash
uv run --group dev pytest -q
```

应当全部通过（Remotion 那一条会跳过）。

## 1. 真实素材校准（W2/W3）

准备 1–2 套你自己的参考。每套 3–12 张图加 1 段视频，风格统一，最好是你有权使用的作品。

```bash
uv run moodreel intake out/projects/mine refs/*.png refs/teaser.mp4 --source own
```

```bash
uv run moodreel measure out/projects/mine
```

读 `out/projects/mine/MEASURE.md`，对着参考逐条核对：

| 看什么 | 怎么判断 |
|---|---|
| 统一性 | 参考如果混了两种风格，开头会提示分成了几组；分组和你的判断一致吗 |
| 颜色 | 底色、主色、强调色认对了吗；面积最大的几种颜色是你看到的那几种吗 |
| 材质 | 颗粒、暗角、网点、扫描线、像素、笔触：有的报出来了吗，没有的有没有误报 |
| 版式和字 | 留白、对齐、标题和正文的字号比例、字重，大致对吗 |
| 运动（视频） | 入场时长、缓动、错峰、镜头、节拍：和你看视频的感觉一致吗；`evidence/motion-*/` 里的证据条带能对上吗 |
| 风格嵌入 | 参考彼此的一致度（留一法）高吗；风格不统一的参考会在这里显出低值 |

把明显不对的值记下来，并写上你认为应该是多少。

## 2. 风格帧（§8：Gate 2 通过率、frame-check 与人工判断的一致性，验收线 ≥ 70%）

让导演（Claude Code 加载 `skills/moodreel`）在上面的项目里按蒸馏流程做到 Gate 2：写 STYLE.md 草稿，用 kit 和原语画 1–3 张风格帧，跑 frame-check：

```bash
uv run moodreel render still out/projects/mine/look 2.5 --size 1920x1080 --out out/projects/mine/look/stills
```

```bash
uv run moodreel frame-check out/projects/mine out/projects/mine/look/stills/t_2.5.jpg
```

每张风格帧记三件事：

1. 你看了并排图（`evidence/frame-check-*.jpg`）后的判断：像，还是不像；
2. frame-check 的结论：PASS 或 FAIL，以及风格相似度对门槛（style 一项）；
3. 第几轮通过 Gate 2（最多两轮）。

**通过率**等于两轮内通过的风格帧数除以总数。**一致性**等于你的判断和 frame-check 结论相同的张数除以总数。两项都要 ≥ 70%。

## 3. 端到端（§8：同一风格做 3 个主题，盲评 ≥ 2 个被认为同风格）

用第 1 节蒸馏出的风格打包入库：

```bash
uv run moodreel pack out/projects/mine --slug mine --name "My Style"
```

然后让导演按出片流程做 3 个主题差别大的短片（各 10–15 秒）：

```bash
uv run moodreel film new topic-a --style mine
```

```bash
uv run moodreel film check films/topic-a
```

```bash
uv run moodreel film deliver films/topic-a
```

盲评：找一位没看过制作过程的人（或者隔几天的你自己），每部片和参考并排放，问"这是同一种风格吗"，只答是或否，再写一句理由。3 部里至少 2 部答"是"才算达标。

## 4. 功能走查

每条命令跑一遍，看结果是否和描述一致。

| 功能 | 命令 | 看什么 |
|---|---|---|
| 风格库 | `uv run moodreel styles` | 59 套内置风格，都标着 mvp 或 ready；你打包的风格排在前面 |
| 新建影片 | `uv run moodreel film new t1 --style swiss-motion --duration 8` | `films/t1/` 下有 TREATMENT.md、main.js、kit/、CREDITS |
| 文字停留检查 | 在 t1 里放一行很长、只停 0.5 s 的字，然后 `film check` | 报出 too short，并给出需要的秒数 |
| 交付（FrameVelo） | `uv run moodreel film deliver examples/quiz-night` | 几秒内出片；终端显示 framevelo 和 hardware h264；有配乐，响度约 −14 LUFS |
| 交付（Chrome） | 同上，加 `--engine chrome` | 慢一些；画面和上一条看不出差别 |
| 配乐（采样） | `uv run sh examples/opening-night/build.sh` | 钢琴、大号、小号、单簧管的音色像真乐器；画面动作落在乐句上 |
| 旁白 | 给一部片写 `narration.json`（格式见 `skills/moodreel/references/produce/brief-and-treatment.md`），然后 deliver | 人声清楚，音乐在台词下压低，字幕时间对得上 |
| 素材 | `uv run sh examples/every-style/build.sh` | 新闻片里的四段素材是其他示例片；CREDITS 记了来源和许可 |
| 没有来源的素材 | 用 `media add` 加一段素材，但不给 `--source` | 命令拒绝执行，说明原因 |
| 变体 | 在 film.json 里加 `variants`，然后 `film deliver --all-variants` | 每个变体一条片，颜色、文字或长度按变体变化 |
| 导出 HyperFrames | `uv run moodreel export hyperframes examples/quiz-night`，再在导出目录里 `npx hyperframes render` | 和原片一致 |
| 导出 Remotion | `uv run moodreel export remotion examples/quiz-night`，在导出目录里 `npm install && npm run render` | 和原片一致，有声音 |
| 风格相似度 | `uv run moodreel csd compare examples/quiz-night/quiz-night.mp4 examples/harbour-dawn/harbour-dawn.mp4 你的图.png` | 同风格的数值高，差得远的低 |
| 示例片重建 | 任选一个，`uv run sh examples/<片名>/build.sh` | 能重建，`film check` 通过 |

## 5. 记录

| 日期 | 节 | 项目或影片 | 结果（通过、不通过、数值） | 问题和备注 |
|---|---|---|---|---|
| 2026-10-24 | 3 | 逐镜头复刻 pdoom-video（156.7 s，约 60 个镜头） | 画面通过；节奏起初不通过，改为数据驱动后再评 | 画面还原度高，但手估的时间让卡点"差一口气"：词时间误差中位 66 ms（13% 在一帧内），速度 132.5 vs 132.007 BPM，强动作踩重音 43%（原片 66%），没有运动模糊。读了原片源码（MIT）后改为用歌曲数据驱动、加子帧运动模糊，沉淀为 `moodreel music`、`kit/music.js`、`--samples`，见 docs/MUSIC-SYNC.md |
| 2026-10-24 | 3 | pdoom 复刻整片交付（v5 节奏 + 音效） | 通过：1080p60、156.7 s、9402 帧，8 个子帧的运动模糊，−14.0 LUFS，真峰值 −1.4 dB | 334 个合成拟音按画面事件和唱词时间放在 `sfx.json`，比歌低 2–11 dB；交付时发现响度归一把比片子略长的混音截短 0.1 s（丢最后 6 帧），已修并加测试 |
| 2026-10-24 | 3 | pdoom 复刻：画面和动作逐镜对齐（黑洞、多眼怪物、运动轨迹） | 通过：整片中位数 structure 0.43 → 0.93、光流方向 0.11 → 0.91、速度 0.64 → 1.02、细节 0.76 → 1.08 | 用户反馈节奏对了但画面不够细、黑洞和怪物没还原、轨迹不对。`moodreel compare` 量出 v5 静帧像而动作不对；把源码（MIT）的场景经兼容层跑在新的 `kit/gl.js` 上，结尾按最佳时移重定时，最后 1.5 秒保留手画镜头。沉淀：`moodreel compare`、`kit/gl.js`、`kit/outline.js`、`kit/anim.js`、stage 的 faces 和 prepare，见 docs/GPU.md |
| 2026-10-28 | 3 | 逐镜复刻「帮我造一个世界」（64 s 一镜到底的 3D 体素片，36 个窗口，13 轮，只复刻不蒸馏） | compare 0.53 → 0.673，Jev 相似度 0.33 → 0.420；平面的终端段 0.92–0.96，3D 世界段 0.66（结构分 0.32） | 提升主要来自镜头：主体的位置和大小、参考片实测的镜头轨迹、导演式读片、逐窗口对齐画面速度；材质和渲染器贡献小（Blender 只改善颜色，结构不变，每帧 4.2 s）。上限在布局：规则生成的世界和原片的房子、树、河位置不同，结构分停在 0.3 左右。后几轮的提升都来自找到故障（镜头焦距延续、着色器缓存、锁定松开的跳变、测量掉帧），不是调参。未解决：倒料段（桌面锁定把三段绑在一起）、黄昏段（构图镜像）、小镇和人群的布局。沉淀：`moodreel camera`/`track`/`look`/`direct`/`pass`、`compare --against/--sheet/--motion`、`kit/follow.js`（`speed`、`pace`）、`kit/lock.js`、`kit/gl.js` 的 AgX。见 remaking.md 3D 片各轮和「The 3D film, in sum」 |
| 2026-10-28 | 3 | 逐镜复刻「定风波」（83 s 动态字体片，纸、墨和一抹橙，37 个窗口，8 轮，只复刻不蒸馏） | compare 0.529 → 0.695，Jev 相似度 0.506 → 0.616，37 个窗口里 31 个变好；结构分 0.64 始终不变，细节 0.55 → 0.83，速度 0.23 → 0.59 | 字体片的布局第一版就对了（每行字在哪、多大可以直接量出来），提升来自细节和速度，和 3D 片相反。每次大的提升都来自换一种看法：从墨迹量字号、粒子全尺寸并排、导演式读片、最弱窗口放大到 640 px、出片前的监制审查（27 处问题）、动效审查（原片 59 处瞬间动作里重做没跟上的 34 → 21）。同一种审查做第二遍只换来 +0.01，这时要换一种审查：前六轮速度分一直最低，逐帧看才发现剩下的是“怎么来、怎么走”：原片的字是砸进来的（三帧内从两倍大落定，年份带红青色差），重做是淡入。用户最后两轮点名的全是动效（活字排满、圆形消失、僧人步态和水纹、推进、拉远、逐行出现、碎裂），并指出缺少动效设计师的联合审查。未解决：湖心岛（太软）、也无风雨（亮度差 27 级）、谁怕?、问汝平生；字块 Jev 只有 0.19；文字墙分页差 0.13–0.23 s。第 8 轮：水滴的下落曲线（先停后加速）、字块按原片曲线变暗、夜景里方块按白天的位置站立（按原片构图反解相机）、海面做成透视的波浪和柔和的月光柱；一处行内注释把夜景的灯光关掉了，脚本改代码后要把改过的行整行读一遍。沉淀：`moodreel review`（监制 + 动效设计师两半）、`compare --motion`、`typed()` 的 slam。见 remaking.md「The motion designer's review」「The set by night, and the sea as water」和「The typography film, in sum」 |
| 2026-10-29 | 2, 3 | 把「定风波」复刻蒸馏成墨字列传（`ink-chronicle`，东方传统），走完三道关并打包 | 通过并打包：风格帧（晋陕峡谷，第二版）frame-check 通过，风格相似度 0.665；演示片《黄河》26.7 s，scene-check 26 帧里 25 帧是新构图、0 帧照搬；−14.0 LUFS，真峰值 −1.6 dBFS；motion-check 9 过、9 不过、2 无法判断；`pack --strict --build` 通过，重建的画面和审定版一致（801 帧里 662 帧像素相同，其余 PSNR ≥ 51.5 dB） | 第 1 关用户要求"只蒸馏风格特色，不要限制太死"。第 3 关第一版 demo 被指"把场景都卡死了"：kit 里装着原片的场景（墨滴炸开、字的地板、海上明月），demo 换了题材却重演了它们。改为只带签名：ANALYSIS 列出原片的场景，作为内容而不是风格；kit 只放原语；STYLE §6/§8 写原则，§10 列原语；新增 `moodreel scene-check`（复刻片 42% 的帧照搬，第一版 demo 4%，其他风格 0%）。打包前又发现 STYLE §11 的开场、结尾例子里还有原片的场景，已换掉；`film new` 只认 `OFL.txt`，按字体家族分开的许可证写不进新片的 CREDITS，已修。三个 CJK 字体（74 MB）不进 git，由包里的 `kit/fonts/fetch.sh` 下载并校验。motion-check 不过的主要是镜头带动的字（192 个计时事件里 170 个），是检查的局限，已开任务卡 |
| 2026-11-01 | 3, 4 | 复刻 Skillry「社媒口碑墙」模版（5.5 s 4K，13 张帖子卡），并沉淀成 `moodreel wall`：给一个产品，自动搜真实帖子、按用户挑选录屏、出 4K 口碑墙；用 YouMind 端到端测试 | 通过：模版用参考卡片宽度的灰卡校准，卡片位置差 1–5 px，标题差 5 px 以内，网格一致，每张卡的淡入逐帧对上（错开 35 ms、ease-out quart 0.467 s）；墙面转 10.3°、每秒回转 0.73°、每秒放大 0.66%。YouMind：YouTube 和 B站共 46 条候选，按推荐挑 13 条，全部录成；出片 3840×2160、5.5 s，`film check` 通过 | 用户选择：只用不需要登录的平台（YouTube、B站），先列候选再挑，测试产品 YouMind。搜索：YouTube 读 ytInitialData，Shorts 的作者用 oEmbed 补；B站读服务端渲染的 __pinia 状态，并用 view 接口读出「禁止转载」（24 条里 13 条）。录屏：无头 Chrome 的屏幕推流按 CSS 像素出帧，与设备像素比无关，所以窗口开到够大，卡片在 4K 墙上只缩不放；长视频页面按手机宽度录。第一版审片发现墙面只有参考的 70% 高（横版卡片把排宽顶满）；墙宽上限放到 3300 又太宽，左边几乎贴边，最后定为 3000，两侧留白和参考一致。现在墙面是参考的 78% 高，因为 13 张里有 6 张横版或近方形。新增标记：官方（产品自己的账号）、禁止转载、推广（推荐组里有 2 条是推广帖，19 和 23）。重录一张卡时原位替换，并记录每次录制的结果（`record.json`）；`--at` 可以跳过片头。一张 2.5 s 的截图里出现整屏 YouTube 标志，逐帧看才知道是帖子自己快剪里的一拍，不是录制出了问题。 |
| | | | | |
