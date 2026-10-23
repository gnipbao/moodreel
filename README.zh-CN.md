# Moodreel

**情绪板进，影片出。** 给 Moodreel 几张风格统一的设计图和一两段同风格的视频，它会测出这种风格之所以一眼可辨的东西：
调色板、材质、字体、版式，尤其是**东西怎么动**。然后把这些写成一个**风格包**：导演要遵守的规则，加上影片可以直接
引用的代码工具包。之后由 AI 担任导演，按任意主题拍出同风格的新片，画面全部由代码绘制、逐帧渲染。

[English](README.md)

> **状态：早期开发。** 整条链路已经跑通：参考进来，测量，生成 kit，打包风格，用它出片、检查、交付。运动测量已在测试片上通过验收，两部示例片通过了往返测试（见下）。下一步是逐字动画。

## 为什么要"测"运动

视觉模型能模仿画面长什么样，却还原不了画面怎么动。Animation2Code 基准（2026）上，最好的模型外观相似度有 0.82–0.84，
时间相似度却全部 ≤ 0.31。所以 Moodreel 用确定性代码测时长、缓动、过冲、错峰和节奏，让模型去理解和使用这些数字。

在 10 条代码渲染、真值已知的测试片上评测（[bench/motion](bench/motion/README.md)），每条另有一份降质版
（3/4 尺寸、25fps、逐帧颗粒、crf 30）：

| | 召回 | t50 在 1 帧内 | 缓动方向正确 | 认定缓动族 / 认错 | 转场 |
|---|---|---|---|---|---|
| 干净版 | 94% | 86% | 97% | 29 / 0 | 13/14 |
| 降质版 | 92% | 88% | 86% | 9 / 0 | 13/14 |

模板跟不上的地方（柱子从底部长高、字收成一条线、字从槽里升起、色块擦入），改为逐帧量元素露出的范围。缓动没有 GSAP 名字时，
把方向类被认定的所有动画放在一起拟合一条 cubic-bezier，风格自己的曲线原样还原。测试片里标为超出读取器范围的 11 个运动，
干净版现在能找到 8 个（柱子生长、下划线和坐标轴描出来、一边放大一边转正的卡片，缓动 `power3.out` 准确认定）；逐字动画还没有覆盖。

详见 [docs/research/motion-extraction.md](docs/research/motion-extraction.md)，完整设计见 [docs/MVP-DESIGN.md](docs/MVP-DESIGN.md)。

### 往返测试

五部示例片（[examples/](examples/README.md)）各按风格库里的一套风格用代码做成，再当作用户的参考蒸馏回来，和片子代码里的数值逐项对比（[bench/roundtrip](bench/roundtrip/REPORT.md)）；然后用中性图形把 kit 的运动重放一遍（`moodreel sketch`），再和参考逐条比对运动断言：

| 影片（风格） | 静态数值 | 找到的运动 | 认定缓动 / 认错 | sketch 运动断言 | 成立的章节 |
|---|---|---|---|---|---|
| swiss-programme（瑞士动态排版） | 11/13，无失败 | 23 / 40 | 0 / 0 | 8 / 9 | 5 / 5 |
| first-light（孔版印刷） | 11/14，无失败 | 4 / 11 | 3 / 0 | 6 / 6 | 5 / 5 |
| shipped（深色发布会） | 10/13，无失败 | 6 / 11 | 0 / 0 | 6 / 6 | 5 / 5 |
| boot（ASCII 终端） | 10/14，清屏的硬切没测到 | 3 / 11 | 1 / 0 | 6 / 7 | 4 / 5 |
| morning（象形图标目录） | 9/13，黑体大写读成了粗体 | 12 / 24 | 0 / 0 | 4 / 4 | 4 / 5 |

没写“无失败”之外的数值，是 kit 留给导演的曲线，不会被认错。颜色、材质、字体和节奏都能还原；瑞士片那条没有 GSAP 名字的专属曲线（`bezier(0.73,−0.03,0.18,1.04)`，原片 `0.7,0,0.2,1`）和平涂底上的翻页（读成镜头平移）也能还原。“成立的章节”只算测量能说明的五节（材质、颜色、字体、运动、镜头），其余六节是导演的判断，要盲测：`moodreel bench blind` 把每部片的参考和测量打成材料包，交给没读过风格的导演蒸馏，再汇总评审的逐节判定（[BLIND.md](bench/roundtrip/BLIND.md)）。

## 风格库

[`styles/`](styles/README.md) 收录了从 [lemo-opuscar](https://github.com/lemomo-ai/lemo-opuscar) 导入的 59 套风格，
每套包含 `STYLE.md`（导演要遵守的不变量）、`DEMO.md`（上游 demo 片的做法）和 `style.json`。其中 23 套是 MVP 就能用代码
画出来的扁平 2D 风格（瑞士动态排版、孔版印刷、浮世绘、蓝图、间谍片头……）；36 套需要后期能力：绘画笔触、3D、像素、
配乐驱动、真实素材。只导入了文档，技法由 Moodreel 自己重新实现。

## 试用

需要 [uv](https://docs.astral.sh/uv/)、ffmpeg 和 Node 20 以上。`uv sync && npm install` 之后：

- `uv run moodreel intake <项目> <参考图和视频…>`：导入参考、归一化、检查是否属于同一风格；
- `uv run moodreel measure <项目>`：测调色板和颜色角色、材质、版式、字号和字重、运动语法、节奏，写出给导演看的 `MEASURE.md`；
- `uv run moodreel frame-check <项目> <风格帧>`：按参考给风格帧打分；
- `uv run moodreel kit <项目>`：由测量结果生成风格的 kit（`tokens.js`、`motion.js` 和共用原语，见 [kit/README.md](kit/README.md)）；
- `uv run moodreel scaffold <项目>`：只用测出的数值画出第一版风格帧，作为导演修改的起点；
- `uv run moodreel motion-check <项目> <影片>`：用同一套测量逐条比对影片的运动语法和参考是否一致；
- `uv run moodreel pack <项目> --slug <名> --name <名>`：校验蒸馏出的风格（11 节齐全、数值可追溯、名称不冲突）并存入 `~/.moodreel/styles`；
- `uv run moodreel styles`：列出你的风格和内置风格；
- `uv run moodreel film new <片名> --style <风格>`、`film check <目录>`、`film deliver <目录> --music <音乐>`：按风格新建影片、检查（文字停留时长、黑帧，蒸馏风格还会按参考给画面和运动打分）、交付（渲染、配乐响度归一到 −14 LUFS、合成）；
- `uv run moodreel motion <视频> --out <目录>`：只测一段视频的运动语法。

- `uv run moodreel sketch <项目>`：用中性图形把测出的运动语法重放成一段片子，在画 demo 片之前先检查 kit；

运动评测见 [bench/motion/README.md](bench/motion/README.md)；`uv run moodreel bench roundtrip` 把示例片蒸馏回来做往返对比，见 [bench/roundtrip/README.md](bench/roundtrip/README.md)。

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

## 许可证

Moodreel 采用 [MIT](LICENSE)。`styles/` 中来自 lemo-opuscar 的风格文档同为 MIT，版权归 LemoLab（见
[`styles/LICENSE-lemo-opuscar`](styles/LICENSE-lemo-opuscar)），每份文档都注明了来源版本。
