# 渲染加速：瓶颈在哪、试过什么

> 日期：2026-10-23 · 代码：[render/render.mjs](../../render/render.mjs) · 测试：[tests/test_render.py](../../tests/test_render.py) · 机器：Apple M3 Pro（11 核），Chrome for Testing 154

## 结论

1. **慢在等帧，不在截图本身。** 旧渲染器每帧约 42 ms，720p 和 1080p 一样，JPEG、PNG、WebP 也一样；关掉 Chrome 按显示器 60 Hz 出帧的节拍（`--disable-gpu-vsync --disable-frame-rate-limit`）后，同一张截图只要 7–11 ms（扁平画面）到 18 ms（满屏颗粒，720p JPEG）。
2. **关掉节拍后每张截图仍是刚画的那一帧。** 五条示例片各取 40 个连续帧，截图与画布自己的像素逐一比对，200 帧全部一致；`tests/test_render.py` 用逐帧灰度不同的页面守住这一点。
3. **每个 worker 一个 Chrome。** 同一站点的标签页共用一个渲染进程，多 worker 会轮流占用它的主线程；改成各自的浏览器后，worker 数才真正起作用。
4. **整片对比**（1920×1080，24 fps，2 个 worker，含启动和拼接）：

| 示例片 | 旧版 | 新版 | 倍数 | 画面 |
|---|---|---|---|---|
| swiss-programme（360 帧） | 12.4 s | 3.5 s | 3.5× | 逐帧一致 |
| morning（288 帧） | 10.3 s | 3.7 s | 2.8× | 与旧版两次渲染之间的差异同级（≥ 59 dB，见下） |
| boot（240 帧） | 8.3 s | 3.8 s | 2.2× | 逐帧一致 |
| shipped（240 帧） | 8.6 s | 4.2 s | 2.0× | 逐帧一致 |
| first-light（288 帧） | 16.9 s | 9.4 s | 1.8× | 逐帧一致 |

first-light 满屏颗粒：crf 14 下 x264 编码本身就占满全部核心（288 帧 6.6 s，约 56 Mbps），加 worker 不再变快，这时瓶颈是编码器。

## 试过但没用的

- **画布直读（getImageData）+ 回传原始 RGBA。** 绕开截图，帧是无损的。但字节要从页面送回 Node：`fetch` 上传约 36 MB/s（720p 一帧 103 ms），经 DevTools 协议传 base64 约 100 ms，WebSocket 最快，单帧 15 ms，可每帧都经过浏览器进程中转（实测它占 124% CPU），多个 worker 叠加后总吞吐卡在约 135 MB/s；1080p 单 worker 22.8 s，反而比关掉节拍的截图慢。放弃。
- **`HeadlessExperimental.beginFrame`（按需出帧，headless shell）。** 在 macOS 上不可用：Chrome 报 "BeginFrameControl is not supported on MacOS yet"。Linux 上可以再试。
- **截图格式和 `optimizeForSpeed`。** 节拍没关时都是约 42 ms，几乎没有差别；关掉后 JPEG q95 仍最快，PNG 在颗粒画面上要慢一倍（36 ms 对 18 ms）。保留 JPEG q95，另加 `optimizeForSpeed`。

## 顺带发现

morning 用旧渲染器连渲两次，从第 25 帧起有细微差异（PSNR ≥ 59 dB，肉眼不可见），说明这条片子里有一处画法不完全确定，与渲染器无关，留待排查。
