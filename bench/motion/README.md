# 运动测量评测（motion bench）

10 条已知真值的代码渲染测试片，每条有干净版和压力版，用来检验 `moodreel motion` 测运动的准确度。测试片由
[`moodreel/bench/fixtures.py`](../../moodreel/bench/fixtures.py) 生成：同一份规格既生成按时间绘制的页面（`render(t)`），也生成真值。
最新逐条结果见 [REPORT.md](REPORT.md)，方法和取舍见 [docs/research/motion-extraction.md](../../docs/research/motion-extraction.md)。

| 测试片 | 测什么 |
|---|---|
| `mg-basic` | 上浮渐显、错峰回弹、位移、expo 放大、画外擦入、硬切、溶解、elastic 下落 |
| `keynote-dark` | 深色网格底、画外滑入、错峰面板、大字回弹、滑出画面、背景不变的硬切 |
| `vertical-social` | 竖屏 720×1280、回弹贴纸、旋转入场（V1）、快切、bounce 下落 |
| `camera-push` | 网格纸底上的镜头推进加平移，镜头下的元素渐显和位移 |
| `on-twos` | 24fps 一拍二（每两帧换一张画） |
| `dips-and-drifts` | 淡黑过渡、长溶解、匀速漂移、慢渐显 |
| `dataviz-bars` | 柱子生长（V1）、轴线描线（V1）、错峰数值标签 |
| `letters` | 逐字入场（V1）、下划线展开（V1）、文字渐显 |
| `busy` | 多元素同时运动、交叉位移、底边滑入错峰、画外滑出、缩小退场 |
| `print-rhythm` | 每秒一切的快节奏、孔版套色错位、逐帧颗粒 |

压力版：3/4 尺寸、对比度 0.85、逐帧颗粒、转 25fps、crf 30，模拟社交平台二次压缩后的素材。

## 运行

在仓库根目录执行，需要 `uv`、`ffmpeg` 和 Node 20 以上：

```bash
uv sync && npm install
```

```bash
uv run moodreel bench make && uv run moodreel bench render
```

```bash
uv run moodreel bench motion
```

渲染出的视频不进 git（约 18 MB，可随时重新生成）；测量结果写在 `out/bench/`，汇总写进本目录的 `REPORT.md`。

## 验收线与当前结果（2026-10-24）

只统计 MVP 范围内的运动（旋转、单轴拉伸、描线、逐字这些 V1 类型单独列出，不计入）。

| | 召回 | 误报 | t50 ≤ 1 帧 | 方向类 | 认定缓动族（认定 / 认错） | 转场 | 错峰 | 一拍二 |
|---|---|---|---|---|---|---|---|---|
| 验收线 | ≥ 90% | | ≥ 85% | ≥ 80% | 认错率 ≤ 5% | | | |
| 干净版 | 94% | 27 | 86% | 97% | 29 / 0 | 13/14 | 4/6 | 2/2 |
| 压力版 | 92% | 20 | 88% | 86% | 9 / 0 | 13/14 | 3/6 | 1/2 |

已知差距：
- keynote-dark 在 5.0 秒处的硬切只是一层很淡的网格消失，缩略图里看不出来。
- 压力版把 24fps 转成了 25fps，一拍二的节拍被打乱。
- 误报主要来自旋转入场（V1）和大面积交叠的运动。
