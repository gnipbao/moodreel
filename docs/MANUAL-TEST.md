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
| | | | | |
