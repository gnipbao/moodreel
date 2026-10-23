# 运动 / 动效提取：调研与原型验证

> 日期：2026-10-23 · 原型代码：[research/motion-spike/](../../research/motion-spike/) · 结论用于 [MVP 设计](../MVP-DESIGN.md)

## 结论

1. **运动必须"量"，不能"看"。** VLM 能复刻画面外观，但还原不了时间。Animation2Code（2026.6）用 1069 段网页动画做了测试：GPT-5.4 和 Claude Sonnet 4.6 的外观相似度有 0.82–0.84，时间相似度所有模型都 ≤ 0.31；微调反而更差，把采样从 2fps 提到 24fps 几乎没有帮助。所以运动参数（时长、缓动、错峰、节奏）要用确定性算法测出来，再交给导演模型去理解和使用。
2. **GitHub 上已有成熟思路可以直接借鉴**：REM 和 motiscope（都是 MIT 协议）各自解决了一半问题。REM 做单个特效的精确测量和重建验证；motiscope 做整段片子的时间结构。我们需要的是第三件事：**把一部片子里所有元素的运动汇总成"风格级运动语法"**，再写进 STYLE.md 的 §5 运动、§6 镜头语法、§8 标志性动作。
3. **原型已经验证可行。** 用 Moodreel 自己的渲染器（`render/render.mjs`）渲染了一条已知真值的 MG 测试片（18 个动画属性、1 个硬切、1 个溶解），本地运行，不依赖云端分割模型：
   - 干净版：18/18 全部找到，0 误报；t50 时间点中位误差 0.1 帧，94% 在 1 帧以内；缓动方向类 94% 正确；认定了 10 个缓动族，0 个认错；错峰间隔测得 0.121s（真值 0.12s）。
   - 压力版（960×540、25fps、颗粒噪声、对比度 0.85、crf 30）：18/18，0 误报；t50 有 89% 在 1 帧以内；方向类 78% 正确；只认定 4 个缓动族，0 个认错。
4. **这套方法对"代码做的 MG 视频"最有效**：扁平图形、tween 驱动、元素有静止态。镜头运动、旋转/3D、逐字动画、描边生长、遮罩擦除、粒子和循环动画还没覆盖，下文列了补法。

## 1. 调研：可借鉴的库与论文

| 项目 | 做法 | 我们借鉴了什么 |
|---|---|---|
| [REM · Reverse Engineer Motion](https://github.com/sidart10/rem)（MIT，2026.10） | SAM 3 逐帧分割 → 匈牙利算法连成轨迹 → ORB 配准扣除镜头运动 → 拟合 GSAP 缓动族（BIC 选优，领先 ≥10 才认定）→ 生成 t10/t50/t90/过冲等可检验的断言 → 对重建结果**用同一套代码重测**，逐条判过/不过 | BIC 族排序和"差距足够大才认定"；用检查点（t50）而不是 t0 作为断言；每个数都标明是观测、推导还是推断；重建后用同一套测量复核 |
| [motiscope](https://github.com/KumarSashank/motiscope)（MIT） | 只做一次 ffmpeg 解码，取 32×32 缩略图；**局部运动能量**（取最活跃 10% 的格子）；阈值锚定在分位数而不是峰值；能量积分得到位移曲线，再拟合 cubic-bezier；挑关键帧给 VLM 看 | 局部能量、分位数阈值；"数字管时间（WHEN），帧图管内容（WHAT）"的分工；把测量值和估计值分开报告的约定 |
| [animation-reverse-engineering](https://github.com/scriptscrypt/animation-reverse-engineering) | 先分清动画是时间驱动还是交互驱动；裁出运动区域，按帧堆叠成条带给模型逐帧读 | 给导演看的证据条带（evidence strip） |
| [competitor-ui-teardown](https://github.com/DEOWL-kan/competitor-ui-teardown) | 用逐帧差分测过渡时长和缓动 | （思路同上） |
| [MoVer](https://arxiv.org/html/2502.13372v1)（Stanford，TOG 2025） | 用一阶逻辑写运动谓词（类型、方向、幅度、时长、Allen 时间关系），验证 LLM 生成的动画，把不通过的谓词反馈给 LLM；通过率从 58.8% 提升到 93.6% | 生成后的"运动一致性检查"写成谓词，失败项反馈给导演模型修改 |
| [LogoMotion](https://arxiv.org/html/2405.07065v2)（Adobe，CHI 2025） | 按图层生成动画代码，渲染后检查画面并修复 | 渲染 → 检查 → 修复的闭环 |
| [Animation2Code](https://arxiv.org/html/2606.28593v1)（2026） | 视频转代码的基准测试 | 第 1 条结论的数据依据；迭代修复只有第一轮收益最大 |
| [OmniLottie](https://arxiv.org/html/2603.02138v1) / [LiveSVG](https://arxiv.org/pdf/2605.30174) | 生成 Lottie / SVG 动画 | P2 阶段：Lottie 可以作为运动的交换格式 |

**我们新增的部分（REM 和 motiscope 都没有）：**

- **静止帧锚定的模板跟踪**：不需要 SAM，完全本地。用运动段前后两个静止帧的差 `Q−P` 找出变化区域，以元素静止时的样子做模板，一次匹配同时得到位置、缩放和不透明度。
- **起点不可见的处理**：渐显的元素起点透明，从画外进入的元素起点在画外，都读不到起始位置。两种办法：
  - 与渐显共享起点：同一个 tween 里位置和透明度通常一起开始，如果把起点绑到渐显的起点上 BIC 几乎不变，就采用绑定后的结果。
  - 钉住画外起点：从画外进入的元素，假定它从刚好在画框外的位置出发。
- **汇总成风格级语法**：入场/出场/位移各自的时长分布、缓动类占比、过冲比例和幅度、错峰间隔和方向、静止时长、运动密度、镜头长度、转场类型和时长。

## 2. 原型方法

```
video ─► 解码一次（640 宽）
      ├─► 镜头：硬切（大面积变化 + 直方图距离）· 溶解（全帧小幅变化，且每帧都是首尾两帧的线性混合）
      ├─► 局部运动能量：64×36 灰度缩略图，6×8 网格，取最活跃 10% 的格子；
      │     先减去每帧格子的中位数（去颗粒和关键帧刷新），再减去每格在本镜头内的噪声底（去文字边缘的编码闪烁）
      ├─► 运动段（run）：能量高于分位数阈值的连续帧；向前多看 0.2s、向后多看 0.3s 作为静止帧
      ├─► 元素：|Q−P| 的变化区域 → 与周围环形背景比较，判断 P、Q 哪一侧有前景
      │     只有 Q 有 = 入场；只有 P 有 = 出场；重叠 = 原地变化；分离 = 位移
      ├─► 跟踪：带符号差分模板 + 零值外环（防止小模板缩进大色块里）
      │     TM_CCORR_NORMED，搜索窗围绕匀速预测位置；缩放用对数抛物线插值到亚级；不透明度 = 在模板上的投影
      │     （只统计画框内的部分）；位移和原地变化改用原始像素 + CCOEFF
      ├─► 拟合：v(t) = A + B·ease((t−t0)/(t1−t0))，半帧网格搜索 t0/t1，加权最小二乘直接解出 A/B
      │     候选：GSAP 全族 + back(s) + elastic(a,p) + bounce；按 BIC 排序
      │     认定条件：BIC 领先 ≥10（不透明度要 ≥25），且曲线"过渡中"的采样 ≥ 6
      └─► 汇总：事件 → 同一 tween 的部件合并（如标题的多个单词）→ 语法（motion.json）
```

运行耗时约 10 秒（7 秒片段，M 系列 Mac，640 宽分析分辨率）。

## 3. 实测结果

测试片由 [make_fixture.py](../../research/motion-spike/fixtures/make_fixture.py) 生成：一份规格同时生成按时间绘制的页面（`render(t)`）和真值，用 `render/render.mjs` 渲染（Puppeteer 无头 Chrome，JPEG 截帧，H.264 crf 14）。内容：

- 标题上浮 + 渐显（power3.out）
- 4 张卡片 back.out(1.7) 弹出 + power1.out 渐显，错峰 0.12s
- 卡片下移（sine.inOut）
- 硬切到纸纹背景："42" expo.out 从 0.05 放大；红条从画外 power2.out 擦入；两者同时 power2.in 渐隐
- 0.5s sine.inOut 溶解
- 圆球 elastic.out(1,0.3) 从画外落下；文字上浮 + 渐显

| 指标 | 干净版 1280×720 30fps | 压力版 960×540 25fps 颗粒 crf30 |
|---|---|---|
| 召回 / 误报 | 18/18 · 0 | 18/18 · 0 |
| t0 / t50 / t90 中位误差 | 0.05 / 0.1 / 0.1 帧 | 0.75 / 0.2 / 0.3 帧 |
| t50 在 1 帧内 | 94% | 89% |
| 缓动方向类正确（in/out/inOut/+回弹/+弹性） | 94% | 78% |
| 缓动族正确 / 完全一致 | 72% / 61% | 50% / 28% |
| **认定的缓动族（认定数 / 认错数）** | **10 / 0** | **4 / 0** |
| 硬切 | 3.000s ✓ | 3.000s ✓ |
| 溶解 | 5.03–5.47s sine.inOut（真值 5.0–5.5） | 5.04–5.60s sine.inOut |
| 错峰 | 4 个，0.121s，从左到右 | 4 个，0.117s，从左到右 |

逐项明细见 `research/motion-spike/out/{clean,stress}/eval.md`（运行后生成）。

**怎么读这些数字：**

- **时间测得准**（t50 基本在 1 帧内），**缓动方向类基本对**，**具体缓动族只在有把握时才认定**。压力版只认定了 4 个，但一个没错，这是有意为之：风格包里写错的规则比"未认定"危害更大。
- t0 比 t50 难测：ease-out 起步快、ease-in 起步慢，加上起点经常被透明度或画框遮住，所以断言和错峰都用 t50。
- 回弹幅度（back 的 s 参数）有 ±40% 的误差，测得过冲比例 0.05–0.15（真值 0.10）。写进风格规则时用区间。

## 4. 原型中踩到的坑（都已修复，都会在真实素材上再遇到）

| 现象 | 原因 | 修法 |
|---|---|---|
| 两张相邻卡片串轨 | 红、黄卡片的差分向量高度相关，搜索窗又太大 | 搜索窗围绕匀速预测位置，半径 = 1.6×上一帧位移 + 1.5% 画宽 |
| 移动的元素被测出假的缩放和横移 | 差分模板在新旧位置重叠时被抵消、截断 | 判定为位移后，改用原始像素模板 + CCOEFF 跟踪 |
| 小元素 / 画外元素出现假"渐显" | 极小尺寸或被画框裁切时，不透明度读不准 | 只有在 ≥3 个可信的中间读数（尺寸 ≥0.3、NCC ≥0.75、完全在画内）时才认定渐显；只有 1 帧的跳变算"出现"，不算渐显 |
| 压缩版整段镜头连成一个运动段 | B/P 帧交替在文字锐边上产生局部闪烁 | 每个格子扣除自己在本镜头内的噪声底 |
| 缩放从负数开始 | 起点不可见时 A 没有约束 | 缩放不能小于 0，出现负值就钉 A=0 重新拟合 |
| 0.25s 渐显被错认缓动族 | 过渡中只有 5 个点，power1/sine/circ 都能穿过 | 认定要求"过渡中"采样 ≥6，不透明度的 BIC 门槛提到 25 |

## 5. 还没覆盖的运动类型

| 类型 | 风格里的分量 | 补法 | 阶段 |
|---|---|---|---|
| 镜头推拉摇移 | 高（§6 镜头语法） | 背景纹理足够：ORB+RANSAC 配准到首帧（REM camera.py）；扁平背景：用所有元素的共同运动反推镜头 | MVP |
| 一拍二 / 一拍三（12fps 步进） | 高（定格、像素、赛璐璐风格） | 运动段内统计"与上一帧完全相同"的比例和周期，测量很便宜 | MVP |
| 逐字 / 逐词动画（split text） | 高 | 词级区域照现在的方法测；字形级参考 REM 的 glyph_motion.py；错峰检测已经可以复用 | V1 |
| 旋转 / 3D 翻转 | 中 | 模板加角度搜索；翻转用四角四边形拟合（REM measure.py） | V1 |
| 描边生长 / 遮罩擦除 | 中高 | 像素规则测量"已显露的长度/面积"随时间的曲线（REM pixels.py），再拟合缓动 | V1 |
| 环境循环 / 粒子 / 漂浮 | 中 | 没有静止帧，锚定法失效。改用能量自相关检测循环周期（motiscope），粒子只统计密度和速度分布 | V1 |
| 一个运动段内进出 | 低 | 段内局部能量再细分 | V1 |
| 卡点（剪辑和动作对齐音乐节拍） | 高（§7 节奏） | librosa 测节拍和起音，统计剪辑点 / 事件 t50 落在节拍 ±1 帧内的比例 | MVP |
| 实拍 / AI 生成视频（非代码 MG） | 视需求 | 不拟合 tween，改用光流统计：镜头运动类型、速度分布、剪辑节奏 | V2 |

**兜底**：测不了的运动，导演模型读证据条带和能量曲线写成定性规则，并在台账里标注为"推断"。

## 6. 从运动语法到 STYLE.md

原型输出的 `grammar` 片段（压力版）：

```json
"entrance": {"duration_s": {"median": 0.56, "p25": 0.54, "p75": 0.7},
             "classes": {"out": 3, "out+overshoot": 3, "out+oscillate": 2, "inOut": 1},
             "overshoot_share": 0.56, "overshoot": {"median": 0.135},
             "scale_from": {"median": 0.40}},
"exit": {"duration_s": {"median": 0.36}, "classes": {"in": 1}},
"stagger": [{"count": 4, "interval_s": 0.117, "order": "left-to-right"}],
"hold_s": {"median": 0.36}, "motion_density": 0.51,
"shots": {"length_s": {"median": 2.08}, "cuts": 1, "dissolves": 1, "dissolve_s": {"median": 0.56}}
```

导演模型据此写进 STYLE.md §5（只写对每部片都成立的规则，不写过程）：

> **5. Motion quality** — Entrances are quick and decisive: 0.5–0.7 s, always ease-out; about half land with a visible overshoot of 10–15 % (back.out(1.5–2)), cards grow from ~0.4–0.6 of their size while fading in over the first half of the move. Exits are shorter than entrances (~0.35 s) and ease-in: things leave by fading, never by sliding. Groups enter as a left-to-right stagger of ~0.12 s. Rests matter: every change is followed by a hold of at least 0.35 s, and the frame is still about half the time…

具体数值和 cubic-bezier 同时写进 `demo/kit/motion.js`，影片代码直接 import，不靠人手抄数字。

## 7. 复现

完整命令（生成测试片 → 渲染 → 压力版 → 提取 → 评分）见 [research/motion-spike/README.md](../../research/motion-spike/README.md)。
