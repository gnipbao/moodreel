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

morning 用旧渲染器连渲两次，从第 25 帧起有细微差异（PSNR ≥ 59 dB，肉眼不可见）；shipped 在 1280×720 下连渲两次也有 57/240 帧不同（≥ 61.7 dB）。差异虽然看不见，却足以让往返测试里几个处在边界上的读数（未认定的猜测、shipped 的出场时长）在两次运行之间翻转。

原因是 2D 画布在 GPU 上光栅化：阴影（`shadowBlur`）和模糊的结果在两次渲染之间会差一两级。现在渲染器加了
`--disable-accelerated-2d-canvas`，2D 画布改在 CPU 上画，shipped 连渲三次逐位一致（和完全关掉 GPU 的结果也逐位一致），
WebGL 仍走 GPU。代价不大：shipped 720p 2.2 → 2.8 s，first-light 1080p 9.5 → 10.3 s，swiss-programme 1080p 3.9 → 3.5 s。
CPU 和 GPU 画出的像素本身略有不同（42–52 dB），换过来之后往返测试的数字会有一次性的小变动。

## FrameVelo 引擎（2026-10-24）

[FrameVelo](https://github.com/gnipbao/framevelo) 把帧留在 GPU 上：舞台画布直接变成 VideoFrame，交给 WebCodecs 的硬件
H.264 编码器（VideoToolbox），再无损封装成 MP4，帧不经过 Node、JPEG 和 x264。`render.mjs video --engine framevelo`
用一个入口页渲染片子：先设 `window.VARIANT`，再载入 `main.js`，片子 READY 后把 `render(t)` 交给 FrameVelo 逐帧调用；
页面出错时 seek 直接抛错，渲染立即停止。默认 `--engine auto`：装了 FrameVelo 且在 macOS 上就用它，否则用 Chrome 引擎。

六部示例片，1920×1080，Chrome 引擎 3 个 worker，含启动和封装：

| 示例片 | Chrome 引擎 | FrameVelo | 快 | CPU（user） | 与 Chrome 引擎 PSNR（平均 / 最低） |
|---|---|---|---|---|---|
| quiz-night（288 帧） | 4.3 s | 2.3 s | 1.8× | 23.9 → 2.3 s | 42.3 / 41.3 dB |
| tide-town（240 帧，WebGL） | 5.7 s | 2.1 s | 2.7× | 35.6 → 2.6 s | 43.8 / 42.8 dB |
| every-style（300 帧，素材） | 7.8 s | 2.5 s | 3.1× | 44.9 → 2.7 s | 43.2 / 42.2 dB |
| opening-night（384 帧，颗粒和模糊） | 14.5 s | 3.4 s | 4.3× | 114.9 → 3.1 s | 37.1 / 35.6 dB |
| first-save（240 帧，像素） | 3.9 s | 2.1 s | 1.8× | 18.6 → 2.1 s | 41.7 / 39.9 dB |
| harbour-dawn（240 帧，笔触） | 4.4 s | 2.2 s | 2.0× | 21.5 → 2.1 s | 40.2 / 39.9 dB |

画面相同，逐帧对齐（每部片的最低 PSNR 都接近平均值，切换和动作处没有跌落）。opening-night 低一些：满屏的胶片颗粒在
硬件编码器的码率下被抹平（文件 32 MB，x264 crf 14 是 92 MB），而且 GPU 和 CPU 画的颗粒叠加和半像素模糊本身略有差别；
码率提到 80 Mbps 也只到 39.2 dB，肉眼看不出。颗粒重的片子交付时可以加 `--bitrate`。

基准（运动测试片、往返测试）仍用 Chrome 引擎：GPU 上的 2D 画布不保证两次渲染逐位一致，而基准的报告要求每次都一样。
