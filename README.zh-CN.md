# Moodreel

**情绪板进，影片出。** 给 Moodreel 几张风格统一的设计图和一两段同风格的视频，它会测出这种风格之所以一眼可辨的东西：
调色板、材质、字体、版式，尤其是**东西怎么动**。然后把这些写成一个**风格包**：导演要遵守的规则，加上影片可以直接
引用的代码工具包。之后由 AI 担任导演，按任意主题拍出同风格的新片，画面全部由代码绘制、逐帧渲染。

[English](README.md)

> **状态：早期研究阶段。** 运动测量原型已在带真值的测试片上验证；风格包格式、导演流程和命令行已经设计，尚未实现。

## 为什么要"测"运动

视觉模型能模仿画面长什么样，却还原不了画面怎么动。Animation2Code 基准（2026）上，最好的模型外观相似度有 0.82–0.84，
时间相似度却全部 ≤ 0.31。所以 Moodreel 用确定性代码测时长、缓动、过冲、错峰和节奏，让模型去理解和使用这些数字。

| 测试片（18 个动画属性、1 个硬切、1 个溶解） | 找到 / 误报 | t50 在 1 帧内 | 缓动方向正确 | 认定缓动族 / 认错 |
|---|---|---|---|---|
| 干净版 · 1280×720 · 30fps | 18/18 · 0 | 94% | 94% | 10 / 0 |
| 压力版 · 960×540 · 25fps · 颗粒 · crf 30 | 18/18 · 0 | 89% | 78% | 4 / 0 |

详见 [docs/research/motion-extraction.md](docs/research/motion-extraction.md)，完整设计见 [docs/MVP-DESIGN.md](docs/MVP-DESIGN.md)。

## 风格库

[`styles/`](styles/README.md) 收录了从 [lemo-opuscar](https://github.com/lemomo-ai/lemo-opuscar) 导入的 59 套风格，
每套包含 `STYLE.md`（导演要遵守的不变量）、`DEMO.md`（上游 demo 片的做法）和 `style.json`。其中 23 套是 MVP 就能用代码
画出来的扁平 2D 风格（瑞士动态排版、孔版印刷、浮世绘、蓝图、间谍片头……）；36 套需要后期能力：绘画笔触、3D、像素、
配乐驱动、真实素材。只导入了文档，技法由 Moodreel 自己重新实现。

## 试用原型

需要 [uv](https://docs.astral.sh/uv/)、ffmpeg 和 Node 20 以上。命令见 [research/motion-spike/README.md](research/motion-spike/README.md)。

## 致谢

Moodreel 借鉴了以下项目的思路：[REM](https://github.com/sidart10/rem)、
[motiscope](https://github.com/KumarSashank/motiscope)、[MoVer](https://arxiv.org/abs/2502.13372)、
[lemo-opuscar](https://github.com/lemomo-ai/lemo-opuscar)、[HyperFrames](https://github.com/heygen-com/hyperframes)。
除了 `styles/` 中来自 lemo-opuscar 的风格文档，没有使用它们的代码。

## 许可证

Moodreel 采用 [MIT](LICENSE)。`styles/` 中来自 lemo-opuscar 的风格文档同为 MIT，版权归 LemoLab（见
[`styles/LICENSE-lemo-opuscar`](styles/LICENSE-lemo-opuscar)），每份文档都注明了来源版本。
