# 运动提取原型（motion spike）

从参考视频里测出风格级的运动语法：镜头与转场、每个元素的入场/出场/位移，以及它们的时长、缓动、过冲、错峰和静止。
用已知真值的测试片评分。调研背景和结果分析见 [docs/research/motion-extraction.md](../../docs/research/motion-extraction.md)。

## 文件

| 路径 | 内容 |
|---|---|
| `motionx/eases.py` | GSAP 命名的缓动函数（与测试页面的 JS 版保持一致） |
| `motionx/video.py` | 解码一次，得到分析宽度下的 RGB 帧 |
| `motionx/shots.py` | 硬切、溶解、局部运动能量、运动段 |
| `motionx/track.py` | 静止帧锚定的元素发现与模板跟踪（位置、缩放、不透明度） |
| `motionx/fit.py` | 单个 tween 拟合：BIC 选缓动族、认定规则、检查点、cubic-bezier |
| `motionx/profile.py` | 元素事件、同 tween 部件合并、风格级语法汇总 |
| `extract.py` | 命令行：视频 → `motion.json` + `evidence/*.jpg` |
| `evaluate.py` | 命令行：`motion.json` 对照 `truth.json` 评分 |
| `fixtures/make_fixture.py` | 写出按时间绘制的测试页面（`render(t)`）和真值 |

## 运行

在仓库根目录执行，需要 `uv`、`ffmpeg` 和 Node 20 以上：

```bash
uv sync && npm install
```

```bash
uv run research/motion-spike/fixtures/make_fixture.py research/motion-spike/fixtures/mg-basic
```

```bash
node render/render.mjs video research/motion-spike/fixtures/mg-basic --fps 30 --size 1280x720 --workers 3 --out research/motion-spike/fixtures/mg-basic/clean.mp4
```

```bash
ffmpeg -y -v error -i research/motion-spike/fixtures/mg-basic/clean.mp4 -vf "scale=960:540:flags=bicubic,eq=contrast=0.85,noise=alls=14:allf=t+u,fps=25" -c:v libx264 -crf 30 -pix_fmt yuv420p research/motion-spike/fixtures/mg-basic/stress.mp4
```

```bash
uv run research/motion-spike/extract.py research/motion-spike/fixtures/mg-basic/stress.mp4 --out research/motion-spike/out/stress
```

```bash
uv run research/motion-spike/evaluate.py research/motion-spike/fixtures/mg-basic/truth.json research/motion-spike/out/stress/motion.json --md research/motion-spike/out/stress/eval.md
```

## 当前结果（2026-10-23）

| | 召回 / 误报 | t50 在 1 帧内 | 方向类正确 | 认定缓动族（认定 / 认错） |
|---|---|---|---|---|
| 干净版 1280×720 30fps | 18/18 · 0 | 94% | 94% | 10 / 0 |
| 压力版 960×540 25fps 颗粒 crf30 | 18/18 · 0 | 89% | 78% | 4 / 0 |

这是原型：只有一条测试片，参数也是在这条片上调出来的。进入 MVP 前需要更多不同的测试片（见 [MVP 设计](../../docs/MVP-DESIGN.md) §8）。
