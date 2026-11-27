# Moodreel 工作流指南

[项目首页](../README.zh-CN.md) · [English](workflows.md)

完成安装后，从仓库根目录运行下列命令。蒸馏示例假设你把自己的图片和一段视频放在 `refs/` 里。制作和交付示例使用已经创建的影片目录 `films/launch/`。

## 从参考素材蒸馏风格包

### 阅读参考与测量结果

```sh
project=out/projects/my-style
uv run moodreel intake "$project" refs/*.png refs/teaser.mp4 --source own
uv run moodreel measure "$project"
```

先读项目目录里的 `MEASURE.md`。它列出底色、墨色和强调色，以及表面纹理、字号、版式、运动与节奏的测量结果。顺着报告去 `measure/` 查具体数值，去 `evidence/` 看对应的连续帧。如果导入时发现参考分属两组调色板，先选定用于蒸馏的素材，再归纳规则。

在 `ANALYSIS.md` 里写出三到五个最能辨认这套风格的特征，同时列出原作特有的场景和构图。用 `STYLE.md` 的十一节描述可复用的风格，在 `LEDGER.md` 里注明数值来自观察、计算还是推断，把字体与声音等选择写入 `DECISIONS.md`。一段只出现过硬切的参考，能够说明这次如何切镜，更广泛的剪辑选择可以保留给下一部片。先确认这些决定，再开始绘制。[风格写作指南](../skills/moodreel/references/distill/writing-style-md.md) · [证据账本格式](../skills/moodreel/references/distill/ledger.md)

### 验证画面与动作

```sh
uv run moodreel kit "$project"
uv run moodreel scaffold "$project"
```

`kit/tokens.js` 和 `kit/motion.js` 保存从参考测出的视觉与运动参数。在 `look/main.js` 中用这些参数画一个新场景，再与参考比对。这里的渲染命令以 16:9 画幅为例。对于竖屏或方形项目，请用 `--size` 指定导入时报告的尺寸。

```sh
uv run moodreel render still "$project/look" 2.5
uv run moodreel frame-check "$project" "$project/look/stills/t_2.5.jpg"
uv run moodreel scene-check "$project" "$project/look/stills/t_2.5.jpg"
```

`frame-check` 检查调色板覆盖、超出色域的面积、明度和材质。可选的 CSD 风格嵌入还会根据参考图之间的一致程度，为新画面设定相似度门槛。如要启用，在 `measure` 之前运行 `uv run moodreel csd setup`，已有测量的项目需要重测一次。该命令下载 2.4 GB 的 CC BY 4.0 模型权重，本地约保留 0.6 GB。`scene-check` 比较画面构图，把相近的帧并排放在一张图上，便于对照 `ANALYSIS.md` 里记录的原作场景。[检查结果读法](../skills/moodreel/references/distill/checks.md)

绘制演示片之前，先让几何图形按测得的规则运动。画面越简单，越容易发现哪个缓动不对、哪一组物体的出场间隔偏了。

```sh
uv run moodreel sketch "$project"
uv run moodreel render video "$project/sketch" --fps 24 --size 1280x720 --out "$project/sketch.mp4"
uv run moodreel motion-check "$project" "$project/sketch.mp4"
```

`motion-check` 逐项对照动作时长、缓动、回弹、错峰间隔和原画更换频率。镜头长度、停留和动作密度由内容决定，结果列为剪辑建议。标记为 unknown 的项目表示证据不足。多段视频作参考时，用 `--reference vid01` 指定要对照的那段。

### 制作演示片并安装风格包

把确认后的风格帧保存为项目根目录下的 `styleframe.jpg`。在 `demo/` 中编写一部 15–30 秒的原创演示片，放好 `build.sh` 和素材署名，渲染为项目根目录下的 `demo.mp4`。看过成片、确认检查结果后再打包。

```sh
uv run moodreel motion-check "$project" "$project/demo.mp4"
uv run moodreel scene-check "$project" "$project/demo.mp4"
uv run moodreel pack "$project" --slug my-style --name "My Style" --strict --build
```

加上 `--strict` 后，风格文档中查不到出处的数值会导致打包失败。`--build` 在临时输出目录运行演示片的构建脚本。默认风格库在 `~/.moodreel/styles`。包中会记录参考文件的哈希。只有当所有参考都标为自己的作品时，才收录参考图的拼版。

要试用现成的蒸馏包，可运行 `uv run python scripts/packs.py install signal-plates`。同一脚本的 `export` 命令可以把本地风格包导回仓库，并刷新索引。各包目录中说明了如何重建演示片、需要下载哪些字体。[风格包目录](../packs/README.md) · [风格总索引](../styles/README.md)

## 制作与交付影片

如果编程智能体直接调用 `moodreel` 命令，可以在仓库根目录运行 `uv tool install --editable .`，然后让它读取 `skills/moodreel/SKILL.md`。这样在其他影片目录里工作时，也能使用本仓库的渲染器、绘制工具和风格库。

先在拍摄方案里定下主题、分镜和每段的节拍，再用风格包编写画面。影片的 `main.js` 根据时间 `t` 绘制完整的一帧。交付时保留拍摄方案、源码与素材署名，后续就能重现每个镜头。[从简报到拍摄方案](../skills/moodreel/references/produce/brief-and-treatment.md) · [影片绘制指南](../skills/moodreel/references/produce/drawing.md)

| 想做什么 | 做法 |
| --- | --- |
| 画出特定媒介的质感 | `kit/pixel.js` 提供索引色像素和 Bayer 抖动，`kit/brush.js` 提供笔触、水彩晕染和墨迹，`kit/three.js` 让三维场景按同一个时间参数运动。[绘图模块](../kit/README.md) |
| 使用实拍、静图或数据 | `media add` 导入文件并记录来源、许可和哈希。`kit/media.js` 按影片时间取对应帧。[带素材署名的示例](../examples/every-style/TREATMENT.md) |
| 配乐和旁白 | 在 `score.json` 中写音乐段落和提示点，`moodreel score` 输出 `score.js` 和 WAV。合成乐器可以直接使用，`uv run moodreel samples fetch` 可另行下载 272 MB 的 CC0 管弦乐器采样。在 macOS 上，`moodreel voice` 可以为 `narration.json` 中的台词合成草稿旁白，并将字幕时间写入 `voice.js`。[按提示点剪辑的示例](../examples/quiz-night/TREATMENT.md) |
| 同一份代码交付多个版本 | 在 `film.json` 中定义变体，用 `kit/variant.js` 中的 `pick()` 取值。`film deliver --all-variants` 会为每个变体分别输出影片和海报。[交付指南](../skills/moodreel/references/produce/delivery.md) |

```sh
uv run moodreel film deliver films/launch --music track.wav
uv run moodreel film check films/launch
uv run moodreel export hyperframes films/launch
uv run moodreel export remotion films/launch
```

交付命令会渲染画面、混合可用的配乐、旁白和音效，以 −14 LUFS 为音频响度目标，输出 MP4 和海报。渲染后再运行 `film check`，可以对实际视频检查黑帧和音乐提示点。它还会检查已声明文字的停留时长、素材署名，以及蒸馏风格的画面与动作是否符合测量结果。导出的 HyperFrames 和 Remotion 工程都会按目标时间调用影片原有的绘图函数。macOS 上安装了 FrameVelo 时默认用它渲染视频，需要反复对比渲染结果时可在交付命令中指定 `--engine chrome`。[渲染器实测](research/render-speed.md)

### 让画面跟着歌走

有歌词的片子可以传入对齐工具给出的逐词时间。生成的数据模块含节拍网格、小节、鼓点、包络和带时间的词。在片中用 `kit/music.js` 读取它们，让切镜、砸字或推镜落在对应的拍子上。`sync` 可以测量画面对节拍、底鼓和每个唱词的响应。[音乐同步指南](MUSIC-SYNC.md)

```sh
uv run moodreel music song.wav --lyrics words.json --out films/launch/music-data.js
uv run moodreel sync reference.mp4 --music films/launch/music-data.js --json reference-sync.json
uv run moodreel sync remake.mp4 --music films/launch/music-data.js --against reference-sync.json
```

要加入子帧运动模糊，在 `film.json` 中设置 `"motion_blur": {"samples": 8, "shutter": 0.2}`，或向 `render video` 传入 `--samples 8 --shutter 0.2`。每一帧会在五分之一帧的曝光时间里采样八次再取平均。

### 绘制插画感 3D 镜头

`kit/look3d.js` 用色阶为几何表面着色，让点彩跟着表面走。`kit/post3d.js` 加入有色遮蔽、景深、泛光和颗粒。用 `look3d.held(t, fps, 2)` 让人物两帧一换，镜头仍逐帧移动。如果要从有符号距离场（SDF）制作角色，可以从内置人偶开始。[插画感 3D 绘制](../skills/moodreel/references/produce/drawing.md) · [GPU 工具](GPU.md)

```sh
uv run moodreel model build mannequin
uv run moodreel model check mannequin --model out/model/mannequin/mannequin.json
uv run moodreel model sheet out/model/mannequin/mannequin.json --out out/model/mannequin/sheet.png
```

`build` 为 `kit/figure.js` 生成网格和骨骼绑定。`check` 检查部件是否封闭、哪些部件悬空，以及每个姿势中指定部件对的穿插深度。`sheet` 将同一组姿势按四个视角排成联系表，便于发现建模或绑定问题。更新日志记录了这套做法的实测结果，包括镜头平移时点彩能否贴住物体表面。[3D 实现与测量](../CHANGELOG.md)

### 制作社媒口碑墙

```sh
uv run moodreel wall search YouMind
uv run moodreel wall record out/walls/youmind --pick 3,5,8,11
uv run moodreel wall make out/walls/youmind
```

搜索会把 YouTube 和 B 站的公开帖子整理为带编号的联系表和 `CANDIDATES.md`。查看作者、推广及转载标记后，按实际编号选帖。录制保留原平台外观，遇到必须登录的页面会跳过。最后的命令会生成 4K 口碑墙影片，并为每张卡片署名。[口碑墙指南](../skills/moodreel/references/produce/social-wall.md)

## 逐镜比较复刻和参考

`origin` 识别切点，根据运动与换帧节奏推断镜头的制作方式。`dossier` 按镜头整理关键帧、运动与画面测量。要对照特定片段，可以创建 `scenes.json`，用秒表示每段的起点、终点并附上名称，例如 `[[0, 2.5, "opening"], [2.5, 5, "title"]]`。请按参考片的实际时间填写。

```sh
uv run moodreel origin reference.mp4 --out origin
uv run moodreel dossier reference.mp4 --shots scenes.json --out dossier
uv run moodreel compare reference.mp4 remake.mp4 --shots scenes.json --json pass1.json --sheet pairs.jpg
uv run moodreel review reference.mp4 remake.mp4 --shots scenes.json --out review
uv run moodreel diff reference.mp4 remake.mp4 --shots scenes.json --out diff
```

| 想知道什么 | 怎么查 |
| --- | --- |
| 最该先改哪一个镜头？ | `compare` 按结构、细节、明暗和运动方向及速度的差异排序。新一轮加上 `--against pass1.json` 可查看变化。`--motion opening` 查看指定片段内部的动作。 |
| 时间从哪里开始错位？ | `diff` 列出提前、延后、缺失和多出的切点，音频偏移，以及黑场、纯色和冻结片段。`review` 将对应帧并排展示，供检查颜色与瞬间动作。 |
| 镜头是怎样移动的？ | `camera --against` 对照平移、推拉和滚转。`--js` 输出的轨迹可交给 `kit/follow.js`。三维镜头里有可追踪的矩形时，`pose --track` 能从矩形顶点推算相机并写出 `cameraAt(t)`。[镜头和音乐的测量](research/VISION-TO-CODE.md) |
| 怎样重跑整轮检查？ | `uv run moodreel pass reference.mp4 films/launch --shots scenes.json --name p1` 会重新渲染、打分，并把联系表及逐帧差异写入 `films/passes/p1/`。下一轮加上 `--against films/passes/p1` 即可比较。 |

可选的 Jev 分析使用 `TYPESAFE_API_KEY`。给 `pass` 加上 `--jev --allow-text-upload` 会发送片段名和测量数值，用于排列修订优先级。`--vision --allow-image-upload` 会发送抽取的画面用于视觉比对。`look`、`direct` 和 `track` 也支持基于帧图像的分析。`track --js` 能输出主体边界框，供 `kit/lock.js` 做位置匹配。[逐镜复刻指南](../skills/moodreel/references/distill/remaking.md)

## 了解测量精度

运行 `uv run moodreel motion clip.mp4 --out out/clip` 可单独测量一段素材，结果在 `out/clip/motion.json`。程序跟踪元素的位置、缩放、透明度与可见范围，拟合缓动曲线，并检测错峰、镜头运动、转场、换帧节奏及循环。证据能区分不同曲线时，才认定具体缓动族。安装 Tesseract 后还可以逐帧识别跳动的数字。[运动提取方法](research/motion-extraction.md)

仓库中的运动基准包括 12 部已知真值的短片。每部片都有干净版和降质版，后者缩到原尺寸的 ¾、降低对比度、加入颗粒、转为 25 fps 并以 CRF 30 编码。“中点”指动作达到一半行程的时刻。[逐片运动评测](../bench/motion/REPORT.md)

| 输入 | 检出的目标属性 | 误报 | 中点误差在一帧内 | 缓动方向正确率 | 认定缓动族 / 其中认错 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 干净版 | 95/99 | 25 | 85% | 96% | 30 / 0 |
| 降质版 | 91/99 | 19 | 87% | 82% | 10 / 0 |

两组均检出 14 个转场中的 13 个，五项循环和粒子测试全部通过。多个元素重叠运动时会出现误报，帧率转换也会干扰一拍二的判断。另一个往返基准用五部示例片反推风格，再与源码中的真值核对。它漏掉了《Boot》的清屏切点，还判断错了《Morning》的标题字重。第二轮盲测中，新的 agent 导演和评审对五套风格都判出了至少八节一致（共十一节）。真实素材校准与人工评估仍待完成。[往返评测](../bench/roundtrip/REPORT.md) · [盲测判定](../bench/roundtrip/BLIND.md) · [人工评估计划](MANUAL-TEST.md)

```sh
uv run moodreel bench make
uv run moodreel bench render
uv run moodreel bench motion
uv run moodreel bench roundtrip
```

基准命令会重新生成仓库中的测试页面或报告。如需盲测，先完成往返评测，运行 `bench blind make` 生成匿名材料包，分别由导演和评审提供新风格文档及判定，再用 `bench blind score` 汇总结果。[盲测操作说明](../bench/roundtrip/README.md)

## 致谢

| 项目 | 对 Moodreel 的贡献 |
| --- | --- |
| REM 与 motiscope | REM 启发了缓动曲线的拟合比较，以及用同一种测量检查重建结果的做法。局部运动能量和分位数阈值的做法借鉴了 motiscope。[REM](https://github.com/sidart10/rem) · [motiscope](https://github.com/KumarSashank/motiscope) |
| MoVer | 将运动特性写成可验证条件的研究，启发了影片制作过程中的检查与反馈。[MoVer 论文](https://arxiv.org/abs/2502.13372) |
| lemo-opuscar | 导入的 59 套风格文档将可复用的视觉规则整理成篇，每份文档保留来源提交和 MIT 署名。[上游项目](https://github.com/lemomo-ai/lemo-opuscar) · [LemoLab 许可](../styles/LICENSE-lemo-opuscar) |
| HyperFrames 与 rea-video | HyperFrames 启发了浏览器确定性渲染、帧级时间规则与逐帧比对清单。rea-video 启发了在复刻之前先识别镜头制作方式的做法。[HyperFrames](https://github.com/heygen-com/hyperframes) · [rea-video](https://github.com/JuneYaooo/rea-video) |
| pdoom-video | 以歌曲数据驱动画面、逐词歌词和子帧运动模糊的做法启发了音乐工作流。改编自该项目的绘图模块和文档保留上游 MIT 声明。[上游项目](https://github.com/mexicat/pdoom-video) · [第三方声明](../NOTICE) |
| FrameVelo | 该 Apache-2.0 依赖支持将帧保存在 GPU 上，并使用硬件 H.264 编码。[FrameVelo](https://github.com/gnipbao/framevelo) |
| 3DCodeVerse | 该框架和展示片启发了 Moodreel 自己实现的色阶材质、表面点彩、SDF 角色、姿势检查和多视角联系表。可选的 `kit/3dcv/` 则移植了展示片的外观引擎和镜头运行时，沿用 CC BY-NC-SA 4.0。用 `--with 3dcv` 创建的影片带有相应署名，仅供非商业使用。[框架](https://github.com/gaoypeng/3dcodeverse) · [展示片](https://huggingface.co/datasets/3dcodeverse/3dcodeverse-awesome-showcase) · [移植许可与逐文件改动](../kit/3dcv/LICENSE) |
