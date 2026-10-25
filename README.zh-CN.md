# Moodreel

**情绪板进，影片出。** 给 Moodreel 几张风格统一的设计图和一两段同风格的视频，它会测出这种风格之所以一眼可辨的东西：
调色板、材质、字体、版式，尤其是**东西怎么动**。然后把这些写成一个**风格包**：导演要遵守的规则，加上影片可以直接
引用的代码工具包。之后由 AI 担任导演，按任意主题拍出同风格的新片，画面全部由代码绘制、逐帧渲染。

[English](README.md)

> **状态：v0.1.0，MVP（早期开发）。** 整条链路已经跑通：参考进来，测量，生成 kit，打包风格，用它出片、检查、交付。运动测量已在测试片上通过验收，五部示例片通过了往返测试和盲蒸馏（见下）。还没做的：用真实参考校准，以及需要人来判断的评测，见 [CHANGELOG.md](CHANGELOG.md)。

## 为什么要"测"运动

视觉模型能模仿画面长什么样，却还原不了画面怎么动。Animation2Code 基准（2026）上，最好的模型外观相似度有 0.82–0.84，
时间相似度却全部 ≤ 0.31。所以 Moodreel 用确定性代码测时长、缓动、过冲、错峰和节奏，让模型去理解和使用这些数字。

在 12 条代码渲染、真值已知的测试片上评测（[bench/motion](bench/motion/README.md)），每条另有一份降质版
（3/4 尺寸、25fps、逐帧颗粒、crf 30）：

| | 召回 | t50 在 1 帧内 | 缓动方向正确 | 认定缓动族 / 认错 | 转场 |
|---|---|---|---|---|---|
| 干净版 | 96% | 85% | 96% | 30 / 0 | 13/14 |
| 降质版 | 92% | 87% | 82% | 10 / 0 | 13/14 |

模板跟不上的地方（柱子从底部长高、字收成一条线、字从槽里升起、色块擦入），改为逐帧量元素露出的范围。缓动没有 GSAP 名字时，
把方向类被认定的所有动画放在一起拟合一条 cubic-bezier，风格自己的曲线原样还原。测试片里标为超出读取器范围的 15 个运动，
干净版现在能找到 13 个：柱子生长、下划线和坐标轴描出来、一边放大一边转正的卡片（缓动 `power3.out` 准确认定）、一行字逐字进来（11 个字母、间隔 0.04 s、每个都是 `power3.out`）、数字跳动（0 到 4,200 的 `power3.out`、$0.0M 到 $12.5M 的 `sine.inOut`，时间精确到帧；装了 tesseract 才用 OCR 读数）。
环境动效按整个镜头来读：循环（脉动、浮动、旋转、呼吸式渐隐，各有周期和幅度）和粒子场（数量、大小、速度、方向），干净版和降质版都是 5/5。

详见 [docs/research/motion-extraction.md](docs/research/motion-extraction.md)，完整设计见 [docs/MVP-DESIGN.md](docs/MVP-DESIGN.md)。

### 往返测试

五部示例片（[examples/](examples/README.md)）各按风格库里的一套风格用代码做成，再当作用户的参考蒸馏回来，和片子代码里的数值逐项对比（[bench/roundtrip](bench/roundtrip/REPORT.md)）；然后用中性图形把 kit 的运动重放一遍（`moodreel sketch`），再和参考逐条比对运动断言：

| 影片（风格） | 静态数值 | 找到的运动 | 认定缓动 / 认错 | sketch 运动断言 | 成立的章节 |
|---|---|---|---|---|---|
| swiss-programme（瑞士动态排版） | 12/13，无失败 | 24 / 40 | 0 / 0 | 10 / 10 | 5 / 5 |
| first-light（孔版印刷） | 11/14，无失败 | 2 / 11 | 1 / 0 | 5 / 6 | 5 / 5 |
| shipped（深色发布会） | 10/13，无失败 | 6 / 11 | 0 / 0 | 5 / 5 | 5 / 5 |
| boot（ASCII 终端） | 10/14，清屏的硬切没测到 | 3 / 11 | 1 / 0 | 5 / 6 | 4 / 5 |
| morning（象形图标目录） | 9/13，黑体大写读成了粗体 | 12 / 24 | 0 / 0 | 4 / 4 | 4 / 5 |

没写“无失败”之外的数值，是 kit 留给导演的曲线，不会被认错。现在每次渲染同一部片都逐位一致，这些数字每次运行都一样；first-light 里升起的
太阳和游泳的人起点都藏着（在地平线下、在画面外），外推出来的起点落不落在真值 0.25 s 以内取决于一级灰度，所以算作没找到。颜色、材质、字体和节奏都能还原；瑞士片那条没有 GSAP 名字的专属曲线（`bezier(0.73,−0.03,0.18,1.04)`，原片 `0.7,0,0.2,1`）和平涂底上的翻页（读成镜头平移）也能还原。“成立的章节”只算测量能说明的五节（材质、颜色、字体、运动、镜头），其余六节是导演的判断，要盲测：`moodreel bench blind` 把每部片的参考和测量打成材料包，交给没读过风格的导演蒸馏，再汇总评审的逐节判定（[BLIND.md](bench/roundtrip/BLIND.md)）。第一轮盲测里五套风格只有一套达到 11 节中 8 节判为“同”：导演把这一部片子没用到的东西写成了“从不”。skill 改成“没见过不等于禁止”、Moodreel 学会从无声的运动里测节拍网格之后，第二轮（换了新的导演和评审）五套全部通过：10、10、8、8、8 节。

## 风格库

[`styles/`](styles/README.md) 收录了从 [lemo-opuscar](https://github.com/lemomo-ai/lemo-opuscar) 导入的 59 套风格，
每套包含 `STYLE.md`（导演要遵守的不变量）、`DEMO.md`（上游 demo 片的做法）和 `style.json`。其中 23 套是 MVP 就能用代码
画出来的扁平 2D 风格（瑞士动态排版、孔版印刷、浮世绘、蓝图、间谍片头……）；36 套需要后期能力：绘画笔触、3D、像素、
配乐驱动、真实素材。只导入了文档，技法由 Moodreel 自己重新实现。配乐驱动现在已经有了（`moodreel score`：片子自己的节拍网格、
段落和提示点，用确定性的合成乐器或采样乐器（立式钢琴、弦乐、拨弦、小号、圆号、大号、单簧管、马林巴、钟琴、竖琴、定音鼓）画成音乐，并把提示点时间交给画面去对齐），综艺节奏扁平、微游戏快闪、1930s 橡皮管卡通三套风格因此可以出片。像素画也有了（`kit/pixel.js`：索引帧加调色板、整像素放大、Bayer 抖动和调色板查找表；测量能从参考里读出像素倍数、原生尺寸、色数和抖动），16-bit 像素 RPG 因此可以出片。绘画笔触也有了（`kit/brush.js`：带鬃毛的笔触、边缘积色的水彩、受光的刮刀块、纸纹打断的蜡笔、带晕的墨，以及把平涂画面重画成笔触的 repaint；测量能读出可见笔触的覆盖、尺度和方向），油画厚涂、水彩、水墨、80 年代赛璐珞等七套风格因此可以出片。3D 也有了（`kit/three.js`：three.js 场景按 t 设置，渲染到自己的 WebGL 画布再合到 2D 舞台上，字可以钉在世界坐标上；`film new` 会把 three.js 复制进片子），低多边形岛屿、玻璃产品、移轴微缩、HD-2D 等十套风格因此可以出片。真实素材也有了（`moodreel media add`：素材按影片帧率一帧一张图存好，静图和数据原样进来，每一份都在 manifest 和 CREDITS 里记下来源、许可和哈希；`kit/media.js` 按影片时间取帧；`film check` 会让没有来源或许可的素材不通过），最后 15 套风格也可以出片了：风格库里的每一套现在都能做。片子也可以有旁白（`narration.json` → `moodreel voice`：台词按时间或配乐提示点放好、合成语音、用 `voice.js` 出字幕，交付时音乐在人声下压低）和不带音乐的音效（只有提示点的 score.json），还能用同一份画面代码出多个变体（film.json 里的 variants，用 `pick()` 读，`film deliver --all-variants`），或导出成 HyperFrames composition（`moodreel export hyperframes`：一条暂停的时间轴，每次 seek 都画出片子自己的那一帧）或 Remotion 工程（`moodreel export remotion`：一个 composition，每一帧都是片子自己的那一帧）。

[`packs/`](packs/README.md) 存放在本仓库蒸馏出的完整风格包（STYLE.md、DECISIONS.md、来源账本和测量、带本风格自有模块的
kit、演示片源码），按同样的分类存放：信号图版（图形与排版）和字符故障发布片（信息与发布）。`python scripts/packs.py install`
装进你的风格库，`export` 把风格库里的包导回来（并刷新总索引）；演示片由源码重建（`sh demo/build.sh`）。
[`styles/README.md`](styles/README.md) 是全部风格的总索引：导入的和蒸馏的按分类列在一起，并注明来源。

## 试用

需要 [uv](https://docs.astral.sh/uv/)、ffmpeg 和 Node 20 以上；[tesseract](https://github.com/tesseract-ocr/tesseract) 可选，用来读跳动的数字（`brew install tesseract` 或 `apt install tesseract-ocr`）。`uv sync && npm install` 之后：

- `uv run moodreel intake <项目> <参考图和视频…>`：导入参考、归一化、检查是否属于同一风格；
- `uv run moodreel measure <项目>`：测调色板和颜色角色、材质、版式、字号和字重、运动语法、节奏，写出给导演看的 `MEASURE.md`；
- `uv run moodreel frame-check <项目> <风格帧>`：按参考给风格帧打分（调色板、色外面积、明度、材质；装了风格嵌入后还比较风格本身：CSD 相似度对照参考彼此之间的一致程度）；
- `uv run moodreel kit <项目>`：由测量结果生成风格的 kit（`tokens.js`、`motion.js` 和共用原语，见 [kit/README.md](kit/README.md)）；
- `uv run moodreel scaffold <项目>`：只用测出的数值画出第一版风格帧，作为导演修改的起点；
- `uv run moodreel motion-check <项目> <影片>`：用同一套测量逐条比对影片的运动语法和参考是否一致；
- `uv run moodreel pack <项目> --slug <名> --name <名>`：校验蒸馏出的风格（11 节齐全、数值可追溯、名称不冲突）并存入 `~/.moodreel/styles`；
- `uv run moodreel styles`：列出你的风格和内置风格；
- `uv run moodreel music <歌> --lyrics <逐词歌词> --out <片子>/music-data.js`：把歌变成数据（节拍网格、小节、底鼓/军鼓/镲、包络、逐词演唱时间），片子里用 `kit/music.js` 读，让切点、砸字、推拉都踩在歌上；渲染加 `--samples 8 --shutter 0.2` 出运动模糊。做法见 docs/MUSIC-SYNC.md；
- `uv run moodreel compare <参考片> <复刻>`：逐镜比对复刻和参考：画面结构、细节、明暗、动作方向（光流）和速度，最差的排前面并写明问题；2D 画布画不出的东西（光线步进的生物、引力透镜、密集流线、随表面走的版画排线）用 GPU 层 `kit/gl.js`。见 docs/GPU.md；
- `uv run moodreel film new <片名> --style <风格>`、`film check <目录>`、`film deliver <目录> --music <音乐>`：按风格新建影片、检查（文字停留时长、黑帧，蒸馏风格还会按参考给画面和运动打分）、交付（渲染、配乐响度归一到 −14 LUFS、合成）；
- `uv run moodreel motion <视频> --out <目录>`：只测一段视频的运动语法；
- `uv run moodreel export hyperframes|remotion <影片>`：把片子导出成 HyperFrames composition 或 Remotion 工程。

两项下载是可选的，需要时按名字下载一次：`uv run moodreel csd setup` 下载风格嵌入（CSD 模型权重，CC BY 4.0，下载 2.4 GB、保留 0.6 GB），`uv run moodreel samples fetch` 下载配乐的采样乐器（Versilian Studios Chamber Orchestra 2 的 272 MB 录音，CC0）。

- `uv run moodreel sketch <项目>`：用中性图形把测出的运动语法重放成一段片子，在画 demo 片之前先检查 kit；

人工测试计划见 [docs/MANUAL-TEST.md](docs/MANUAL-TEST.md)。运动评测见 [bench/motion/README.md](bench/motion/README.md)；`uv run moodreel bench roundtrip` 把示例片蒸馏回来做往返对比，见 [bench/roundtrip/README.md](bench/roundtrip/README.md)。

## 交给 AI 导演使用

Moodreel 设计为由 agent 担任导演来驱动（Claude Code、Codex 等能读 `SKILL.md` 的 agent）。以可编辑模式安装命令行
（这样它始终能找到本仓库的渲染器、kit 和风格库），再链接 skill：

```bash
uv tool install --editable .
```

```bash
ln -s "$PWD/skills/moodreel" ~/.claude/skills/moodreel
```

然后直接说："把这些参考蒸馏成一个风格包"、"用我的〈风格〉做一个 20 秒的发布片，讲 X"、"有哪些风格？"。
导演的流程、确认节点和规则见 [skills/moodreel/SKILL.md](skills/moodreel/SKILL.md)。

## 致谢

Moodreel 借鉴了以下项目的思路：[REM](https://github.com/sidart10/rem)、
[motiscope](https://github.com/KumarSashank/motiscope)、[MoVer](https://arxiv.org/abs/2502.13372)、
[lemo-opuscar](https://github.com/lemomo-ai/lemo-opuscar)、[HyperFrames](https://github.com/heygen-com/hyperframes)。
除了 `styles/` 中来自 lemo-opuscar 的风格文档，没有使用它们的代码。

卡点的做法学自 [pdoom-video](https://github.com/mexicat/pdoom-video)（MIT）：一支每个切点、砸字和运镜都由歌曲数据（逐词对齐的歌词、
鼓点、节拍网格）算出、带子帧运动模糊的音乐录像。`moodreel music`、`kit/music.js` 和 docs/MUSIC-SYNC.md 以它为蓝本，`kit/gl.js` 和 `kit/anim.js` 改编自它的引擎，
改编的部分按其 MIT 许可保留版权声明（见 `NOTICE`）。

出片的视频引擎是 [FrameVelo](https://github.com/gnipbao/framevelo)（依赖，Apache-2.0）：每一帧留在 GPU 上，由硬件 H.264 编码器编码。
示例片上比 Chrome 引擎快 1.8–4.3 倍，CPU 少用 8–36 倍；装了它且在 macOS 上时默认使用。测试基准仍用 Chrome 引擎，因为它每次渲染逐位一致。

## 许可证

Moodreel 采用 [MIT](LICENSE)。`styles/` 中来自 lemo-opuscar 的风格文档同为 MIT，版权归 LemoLab（见
[`styles/LICENSE-lemo-opuscar`](styles/LICENSE-lemo-opuscar)），每份文档都注明了来源版本。
