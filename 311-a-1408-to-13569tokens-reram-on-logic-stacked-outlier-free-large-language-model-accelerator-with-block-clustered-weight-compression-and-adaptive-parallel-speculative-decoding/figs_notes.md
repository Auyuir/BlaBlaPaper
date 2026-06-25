# 31.1 A 14.08-to-135.69Token/s ReRAM-on-Logic Stacked Outlier-Free Large-Language-Model Accelerator with Block-Clustered Weight-Compression and Adaptive Parallel-Speculative-Decoding 图表详解

### Issue: Redundant Codebook ReRAM Access

![f98bc50120253aedac614d0f349b77c963add39794e73276053d0d6e48d5eece.jpg](images/f98bc50120253aedac614d0f349b77c963add39794e73276053d0d6e48d5eece.jpg)

- **图像内容与给定说明存在不一致**：
  - 图片实际展示的是 **“FWHT-Based Global Rotation”**，即基于 **Fast Walsh-Hadamard Transform, FWHT** 的全局旋转方法。
  - 给定图片说明为 **“Issue: Redundant Codebook ReRAM Access”**，这更对应论文中 Figure 31.1.4 的 **BVQ / RS-PNM / Codebook ReRAM Access** 问题。
  - 因此，以下分析以图片真实内容为准，重点分析 **FWHT-Based Global Rotation 的计算结构、问题来源及其与 LRU 设计的关系**。

- **图片核心主题**：
  - 该图解释了在 LLM 低比特量化中，为消除 activation outliers 所采用的 **Hadamard-based global rotation**。
  - 其目标是通过正交旋转保持矩阵乘法等价性，同时改善 activation 分布，使 **W4A8 quantization** 更可靠。
  - 但图中强调的问题是：传统 **global rotation** 需要深层 FWHT 和高精度操作，硬件面积与能耗开销很大。

- **图中上半部分：Case 1，n = 2ᵏ 的标准 Hadamard 构造**：
  - 当输入维度 **n 是 2 的幂次** 时，Hadamard matrix 可以递归构造。
  - 图中公式为：
    - **H₂ᵏ⁺¹ = H₂ᵏ ⊗ H₂**
    - 或等价写成块矩阵形式：
      - **H₂ᵏ⁺¹ = [H₂ᵏ  H₂ᵏ; H₂ᵏ  -H₂ᵏ]**
  - 其中：
    - **⊗ 表示 Kronecker Product**
    - **H₂ = 1/√2 · [[1, 1], [1, -1]]**
  - 该结构对应标准 **Walsh-Hadamard Transform**，可以通过加减法实现，无需普通乘法。

- **Case 1 的硬件含义**：
  - 若 channel dimension 为 **2ᵏ**，FWHT 可以用 **k-stage butterfly network** 实现。
  - 每一级主要执行加法和减法。
  - 理论上计算高效，但当 **k 很大** 时，硬件深度、布线和寄存器需求显著增加。

- **图中下半部分：Case 2，n ≠ 2ᵏ 的非 2 幂维度处理**：
  - 现实 LLM 中很多 hidden dimension / intermediate dimension 并不是 2 的幂。
  - 图中给出非 2 幂维度的处理方式：
    - **reshape 1×n into 2ᵏ×m**
    - **Hₙ = H₂ᵏ ⊗ Hₘ**
  - 即将原始维度 **n** 分解为：
    - **n = 2ᵏ × m**
  - 其中：
    - **H₂ᵏ** 由 FWHT 实现
    - **Hₘ** 是预计算的 non-power-of-two Hadamard matrix

- **图中示例的潜在来源**：
  - 论文正文中提到一个典型例子：
    - **LLaMA3-8B down_proj layer**
    - 维度为 **14336 = 2⁹ × 28**
  - 因此图中出现 **2⁹ FWHT**，对应 **k = 9**。
  - **m = 28** 则对应一个非 2 幂 Hadamard matrix，需要额外高精度处理。

- **图中硬件流水结构解析**：

| 图中模块 | 含义 | 作用 | 主要问题 |
|---|---|---|---|
| **Hₘ matrix [n×m]** | non-power-of-two Hadamard matrix | 处理非 2 幂残余维度 | 需要高精度矩阵运算 |
| **FP16 GEMM** | FP16 general matrix multiplication | 执行 Hₘ 相关旋转 | 面积、功耗、延迟高 |
| **FWHT Selector** | FWHT 选择器 | 选择对应 FWHT 数据路径 | 控制复杂 |
| **2⁹ FWHT** | 9-depth FWHT array | 处理 2⁹ 维 Hadamard 旋转 | FWHT 深度大 |
| **Residual Rotation Matrix [2ᵏ×m]** | 残余旋转矩阵 | 补足 non-power-of-two rotation | 高精度操作多 |
| **Numerous High Precision Ops** | 大量高精度操作 | 图中明确指出的问题 | 面积开销严重 |

- **图片左侧矩阵 Hₙ 的意义**：
  - 左侧大矩阵标为 **Hₙ matrix [n×m]**。
  - 表示完整的 global rotation matrix。
  - 对于 LLM activation rotation，需要对 token feature 进行整体旋转：
    - **x′ = xH**
  - 旋转后 activation outliers 被扩散，极端值被平滑，从而提升低比特量化精度。

- **为什么 global rotation 能消除 outliers**：
  - Hadamard matrix 是正交矩阵。
  - 正交旋转具有如下特性：
    - **保持向量范数**
    - **保持内积关系**
    - **不改变线性层数学等价性**
  - 但旋转会重新分布 activation 中的异常大值。
  - 原本集中在少数 channel 的 outliers 会被扩散到多个 channel。
  - 这样 INT8 activation quantization 的 scale 不会被少数极端值严重拉大。

- **该方法与 QuaRot / SpinQuant 的关系**：
  - 图中方法与 **QuaRot**、**SpinQuant** 等 outlier-free quantization 技术相关。
  - 这些方法通过在模型中插入或吸收旋转矩阵，使 LLM 更适合低比特推理。
  - 图片展示的是其中硬件实现时最直接但代价较高的 **global rotation** 路径。

- **图片强调的关键瓶颈**：
  - 主要瓶颈不是数学正确性，而是 **hardware cost**。
  - 对于大维度 LLM 层，global FWHT 会导致：
    - **深 FWHT pipeline**
    - **大量 FP16 GEMM**
    - **高精度 residual rotation**
    - **复杂数据选择与重排**
    - **显著面积开销**
    - **较高延迟和功耗**

- **论文中给出的面积问题**：
  - 正文指出，面向 TLM 中多种维度的 deep FWHT array 面积很大。
  - 其面积接近：
    - **4.37× of a 4K INT8 MAC array**
  - 这说明直接实现 global rotation 对边缘 LLM accelerator 不划算。

- **为什么 non-power-of-two dimension 特别麻烦**：
  - 标准 FWHT 最适合 **2ᵏ dimension**。
  - 但 LLM 中常见维度如：
    - **11008**
    - **14336**
    - **28672**
  - 这些通常不是单纯的 2 的幂。
  - 因此必须引入：
    - **reshape**
    - **Kronecker Product**
    - **npot Hadamard matrix**
    - **residual rotation**
  - 这会破坏纯 FWHT 的简单加减法优势。

- **图中 “FP16 GEMM” 的重要性**：
  - FWHT 本身可以主要用加减法。
  - 但 **Hₘ** 或 residual rotation 部分无法完全用简单 butterfly 实现。
  - 因此需要 **FP16 GEMM** 来处理非 2 幂部分。
  - 这也是图中 “Numerous High Precision Ops” 的来源之一。

- **该图在论文整体论证中的作用**：
  - 图片用于说明：虽然 **global rotation** 可以提升 W4A8 TLM quantization 精度，但直接硬件实现代价过高。
  - 它为后续提出 **Local Rotation Unit, LRU** 提供动机。
  - LRU 的核心思路是：
    - 不做完整 global rotation
    - 将 deep FWHT 分解为低深度 local FWHT
    - 用 overlapped upper/lower rotations 近似 global rotation
    - 将 FWHT depth 限制到 **6-depth**
    - 显著降低面积

- **Global Rotation 与 LRU 的对比**：

| 对比项 | **Global Rotation** | **LRU Local Rotation** |
|---|---|---|
| 旋转范围 | 全维度 global | 局部 upper/lower overlapped |
| FWHT 深度 | 可达 9-depth 或更深 | 限制为 **6-depth** |
| npot 处理 | 依赖 Hₘ / residual rotation | 搜索合适的 **(m, k)** 组合 |
| 高精度操作 | 多 | 显著减少 |
| 硬件面积 | 很大 | 小得多 |
| 量化效果 | 好 | 接近 global rotation |
| 论文结果 | 面积昂贵 | **节省 92.7% area** |

- **图中 2⁹ FWHT 的含义**：
  - **2⁹ = 512**。
  - 表示需要 9 级 butterfly 结构。
  - 对每个 token feature 进行 rotation 时，需要经过多级数据交换和加减。
  - 当多个层有不同 channel size 时，需要支持多种 FWHT 尺寸，进一步增加可重构硬件复杂度。

- **图中 residual rotation matrix 的问题**：
  - residual rotation matrix 用于补充 **H₂ᵏ** 无法覆盖的非 2 幂部分。
  - 它通常不能像 FWHT 那样只靠加减法完成。
  - 因此需要更昂贵的乘加操作。
  - 对 edge accelerator 来说，这部分会带来明显的面积和能耗压力。

- **从数据流角度看该图**：
  - 输入 token feature 首先被 reshape。
  - 一部分经过 **FP16 GEMM** 处理 non-power-of-two Hadamard 部分。
  - 数据再经过 **FWHT Selector** 进入深层 FWHT array。
  - 最后结合 residual rotation matrix 得到完整旋转后的 activation。
  - 该路径虽然精度友好，但硬件路径长且复杂。

- **从系统性能角度看该图的问题**：
  - LLM decoding 本身已经受限于 weight EMA。
  - 如果 TLM 为了低比特量化而额外引入重型 global rotation，会抵消低比特化带来的部分收益。
  - 所以必须避免让 rotation 成为新的 latency bottleneck。
  - 这正是论文提出 **LRU** 的原因。

- **该图对应的论文关键结论**：
  - 直接使用 **FWHT-Based Global Rotation** 可以解决 activation outliers。
  - 但其硬件实现需要：
    - **deep FWHT**
    - **FP16 GEMM**
    - **residual rotation**
    - **high precision operators**
  - 因此不适合面积和功耗受限的边缘 LLM accelerator。
  - 论文通过 **LRU** 将 global rotation 近似为低成本 local rotation，实现了 outlier-free W4A8 TLM quantization。

- **与最终芯片结果的关系**：
  - 借助 LRU，论文实现了：
    - **W4A8 TLM quantization**
    - perplexity 接近 BF16 baseline
    - 相比 BF16 speculative decoding 获得 **3.82-to-3.93× speedup**
    - 相比 global rotation 节省 **92.7% area**
  - 因此，该图展示的是被优化掉的高成本 baseline，是 LRU 创新的直接背景。

- **一句话总结**：
  - 该图片说明 **FWHT-Based Global Rotation 虽能消除 LLM activation outliers，但在 non-power-of-two dimensions 下需要深层 FWHT、FP16 GEMM 和 residual rotation，导致大量高精度操作与严重面积开销；论文提出 LRU 正是为了以低成本近似这种 global rotation。**

### f4a3c9d1bcf4ad90a834be1e07d1967bc6f8bca553aa7c2333a8a212f00885e6.jpg

![f4a3c9d1bcf4ad90a834be1e07d1967bc6f8bca553aa7c2333a8a212f00885e6.jpg](images/f4a3c9d1bcf4ad90a834be1e07d1967bc6f8bca553aa7c2333a8a212f00885e6.jpg)

- 这张图展示的是论文中 **Local Rotation Unit (LRU)** 的核心思路：用 **decomposed FWHT** 近似原本需要完整大规模 Hadamard 变换的 **global rotation**，从而实现 **outlier-free low-bit quantization**，同时显著降低硬件面积和实现复杂度。

- 图中最上方的关键信息是：**把 FWHT 的最大规模从 2^9 限制到 2^6**。这说明作者不再直接实现深层、大尺寸的 FWHT array，而是把大变换拆成更小、更容易硬件化的子变换。

- 图里的核心变量是 **(m, k)**：
  - **k** 对应可配置的 **2^k-size FWHT**
  - **m** 对应非幂次维度下的 **Hadamard matrix Hm**
  - 目标是在满足覆盖原始维度 **n** 的前提下，选择一组 **(m, k)**，让变换规模最小、冗余最少、硬件成本最低

- 这张图表达的本质是：**用两阶段局部旋转代替一次全局旋转**。  
  这样做的目的不是追求数学上完全等价，而是追求对激活分布足够有效的近似旋转，从而消除 outlier，使后续 **W4A8 quantization** 可行。

- 图中两个阶段分别是：
  - **Stage 1: Upper Rot.**
  - **Stage 2: Lower Rot.**

- 两个阶段的处理流程几乎对称，都是：
  - **TAU 分配 token features**
  - 一部分送入 **RFA** 执行 **2^k FWHT**
  - 另一部分送入 **HAU** 执行 **Hm GEMM**
  - 两路结果组合后完成该阶段旋转

- 这张图可以按功能块理解为下表：

| 模块/步骤 | 作用 | 设计意义 |
|---|---|---|
| **TAU** | 分配 upper/lower token features | 负责把输入切分成适合局部旋转的子块 |
| **RFA** | 执行 **2^k FWHT** | 用较小规模的可重构 FWHT 阵列替代大阵列 |
| **HAU** | 执行 **Hm GEMM** | 处理 non-power-of-two 部分，补足维度覆盖 |
| **Stage 1 / Stage 2** | 上下两次局部旋转 | 用两次低成本变换逼近一次全局旋转 |
| **(m, k) 搜索** | 选择最优拆分参数 | 在精度、覆盖和硬件复杂度之间折中 |

- 图中 **“Upper Rot.”** 和 **“Lower Rot.”** 的设计体现了一个重要思想：  
  **不是强行让一个变换覆盖全部维度，而是通过重叠覆盖的局部变换拼出整体效果。**

- 这种“上半部分 + 下半部分”的分解方式有两个直接好处：
  - **降低 FWHT 深度**
  - **减少对高精度加法器和大规模变换阵列的依赖**

- 图中同时出现 **2^k FWHT in RFA** 和 **Hm GEMM in HAU**，说明作者采用了 **混合硬件路径**：
  - 幂次维度走 **FWHT**
  - 非幂次残余部分走 **GEMM**
  - 两者组合后实现对原始维度的近似旋转

- 这也是为什么论文强调 **npot Hadamard construction**。  
  对于实际 LLM 层的通道维度，很多都不是纯粹的 2 的幂，因此不能只靠标准 FWHT 直接覆盖。图中这个分解方案就是为了解决这个现实问题。

- 从硬件角度看，这张图对应的创新点非常明确：
  - 将原本需要大面积 **global rotation** 的结构，拆解为 **小规模、可复用、低开销** 的局部模块
  - 使 **RFA** 只需要支持 **2^1–2^6** 的 FWHT
  - 让 **HAU** 只承担补偿性的 Hadamard GEMM，而不是完整主变换

- 从算法角度看，这种拆分并不会破坏核心目标，因为 LRU 的任务不是做精确线性代数运算，而是做 **outlier suppression**。  
  只要旋转后激活分布更平滑，就能显著改善低比特量化误差。

- 这张图与论文整体贡献的关系很强：
  - 它支撑了 **TLM 侧的 W4A8 quantization**
  - 解决了 **FWHT 深阵列面积过大** 的问题
  - 让论文声称的 **92.7% area saving** 有了硬件实现基础

- 可以把这张图概括成一句话：  
  **用两段局部、可配置、低深度的 FWHT + Hm GEMM，替代一次高成本全局旋转，从而在硬件上实现 outlier-free quantization。**

- 进一步看，这个设计的价值在于它不是单纯“压缩算子”，而是 **算子、维度分解和硬件阵列共同协同设计**：
  - 算法上：分解旋转
  - 结构上：上下两阶段
  - 硬件上：RFA/HAU 分工
  - 系统上：为后续 speculative decoding 提速

- 如果总结这张图的技术重点，最重要的三点是：
  - **通过限制 FWHT 规模，降低硬件面积**
  - **通过 upper/lower 两阶段局部旋转，近似全局 rotation**
  - **通过 RFA + HAU 分工，实现对 non-power-of-two 维度的高效支持**

- 这张图虽然看起来结构简单，但它实际上是全文第一个关键支点：  
  **没有这个 LRU，后面的低比特 TLM 加速就很难同时兼顾精度与面积。**

### 71b823e601aa34e20d7d11475923109574c427a0b9c3ccbf178f1f8f23c96566.jpg

![71b823e601aa34e20d7d11475923109574c427a0b9c3ccbf178f1f8f23c96566.jpg](images/71b823e601aa34e20d7d11475923109574c427a0b9c3ccbf178f1f8f23c96566.jpg)

- 该图由两个归一化柱状图组成，分别展示 **LRU（Local Rotation Unit）** 相对基线方案在 **Speculative Decoding latency** 和 **Hadamard rotation engine area** 上的收益。

- 核心数据如下：

| 指标 | Baseline | LRU | 改善幅度 |
|---|---:|---:|---:|
| **Norm. SD Latency** | 1.00× | 约 0.262× | **3.82× speedup** |
| **Norm. Area** | 1.00× | 约 0.051× | **面积降低 94.9%** |

- 左图含义：
  - 纵轴为 **Norm. SD Latency**，即归一化 speculative decoding 延迟。
  - **Baseline 延迟被归一化为 1**。
  - 采用 **LRU** 后，延迟约降至基线的 **1 / 3.82 ≈ 26.2%**。
  - 这意味着在该测试条件下，LRU 可带来 **3.82× 推理加速**。
  - 图下注释表明该延迟测试条件为：
    - **TLM：LLaMA2-7B**
    - **DLM：LLaMA-160M**
    - 两者均为 **BF16**
  - 因此，这里的加速主要体现 **LRU 对 TLM 低比特量化友好的旋转预处理带来的系统级 SD 延迟下降潜力**。

- 右图含义：
  - 纵轴为 **Norm. Area**，即归一化硬件面积。
  - Baseline 对应 **original 2⁹ FWHT-based Hadamard rotation engine**。
  - LRU 面积仅约为原始全局旋转引擎的 **5.1%**。
  - 因此面积节省为：
    - **1 - 0.051 = 94.9%**
  - 这说明 LRU 用局部、分解式 FWHT 替代大规模全局 Hadamard rotation engine，显著降低硬件开销。

- 该图重点强调的技术结论是：
  - **LRU 同时解决了低比特量化中的 outlier 问题和全局旋转硬件面积过大的问题**。
  - 传统 **FWHT / Hadamard rotation** 虽然可以通过正交旋转消除 activation outliers，使 **W4A8 quantization** 更可靠，但如果直接实现全局旋转，会产生较大的高精度加法器阵列和路由开销。
  - LRU 通过 **decomposed FWHT** 和 **local rotation** 近似全局旋转，在保持量化精度的同时，大幅压缩面积。

- 从架构意义看：
  - **3.82× speedup** 表明 LRU 不只是一个量化辅助模块，而是直接影响 speculative decoding 的端到端延迟。
  - **94.9% area reduction** 表明其硬件实现成本极低，适合边缘端 LLM accelerator。
  - 该结果支撑论文主张：在资源受限芯片上，不能简单搬用软件侧的全局旋转 PTQ 方法，而需要 **hardware-aware rotation design**。

- 与论文正文对应关系：
  - 文中提到，传统 global rotation 的 FWHT array 面积可达到 **4K INT8 MAC array 的约 4.37×**，面积代价很高。
  - LRU 将深层 FWHT 分解为重叠的 **upper / lower 6-depth FWHT**，避免完整高深度 FWHT 实现。
  - 图中 **94.9% 面积节省** 正是该设计策略的直接量化结果。
  - 图中 **3.82× speedup** 与正文提到的 **3.82-to-3.93× speedup over vanilla SD** 对应，说明该方法在不同模型配置下均有稳定收益。

- 简要评价：
  - 该图展示的是本文第一个关键创新点 **LRU for outlier-free low-bit TLM quantization** 的硬件收益。
  - 它证明 LRU 在 **性能** 和 **面积效率** 上同时优于原始全局 FWHT rotation engine。
  - 对边缘 LLM 推理芯片而言，该结果非常关键，因为它使 **W4A8 TLM quantization** 在不显著牺牲精度的情况下具备实际可部署性。

### 685dfdb0e36eade9658ce13b30ffd23300ce19c0395ca2b1c7286906397a79da.jpg

![685dfdb0e36eade9658ce13b30ffd23300ce19c0395ca2b1c7286906397a79da.jpg](images/685dfdb0e36eade9658ce13b30ffd23300ce19c0395ca2b1c7286906397a79da.jpg)

- **图片核心含义**：该图展示了 **Traditional Vector Quantization, VQ** 在 LLM 权重量化/压缩加速中的硬件代价问题，重点指出传统 VQ 虽然能降低权重存储位宽，但会引入 **额外 Index Buffer** 和 **复杂 Multi-Port Decoder**，导致面积、带宽和控制开销上升。

- **图中上半部分描述传统 VQ 的压缩方式**：

  | 图中模块 | 含义 | 作用 |
  |---|---:|---|
  | **768×768 LLM Weight** | 原始 LLM 权重矩阵 | 以 **INT4，4bit/value** 存储 |
  | **Vector Length = v** | 将权重按长度为 **v** 的向量切分 | 每个向量用一个 codebook entry 表示 |
  | **INT8 Vector Codebook** | 码本，存储聚类中心向量 | 每个 entry 是长度为 **v** 的 INT8 向量 |
  | **Index** | 每个原始向量对应的码本索引 | 用于查找 codebook entry 并重构权重 |
  | **2.5bit/value @ v=4, cd=256** | VQ 后的等效压缩率 | 码本索引摊销后约为 2.5 bit/value |

- **传统 VQ 的基本流程**：
  - 将原始 **LLM Weight** 按向量长度 **v** 划分。
  - 对这些权重向量进行聚类，得到 **Vector Codebook**。
  - 原始权重不再直接存储，而是存储对应的 **Index**。
  - 计算时通过 **Index Buffer** 读取索引。
  - 再通过 **Multi-Port Decoder** 查找 **Codebook**。
  - 最后将解码出的权重送入 **PE Array** 进行矩阵计算。

- **图中给出的关键数据关系**：

  | 项目 | 数值/形式 | 说明 |
  |---|---:|---|
  | 原始权重矩阵 | **768×768** | 示例 LLM layer weight |
  | 原始量化精度 | **INT4，4bit/value** | 直接低比特权重存储 |
  | VQ 向量长度 | **v** | 每个 codebook entry 包含 v 个权重 |
  | Codebook 精度 | **INT8** | 码本中心用更高精度表示 |
  | Codebook 规模 | **cd=256** | 需要 8-bit index 表示一个 entry |
  | 示例压缩率 | **2.5bit/value @ v=4** | Index 与 codebook 摊销后的等效位宽 |

- **图中下半部分展示传统 VQ 的硬件数据通路**：
  - **Global Token Buffer** 提供输入 token activation。
  - **Index Buffer** 存储 VQ 索引。
  - **Weight Buffer** 存储或缓存 codebook/重构权重。
  - **Multi-Port Decoder** 根据多个 index 并行访问 codebook。
  - **PE Array** 执行矩阵乘法或 MAC 计算。

- **该图强调的主要问题是：传统 VQ 的压缩收益会被硬件解码开销抵消**。

  | 问题 | 具体原因 | 硬件影响 |
  |---|---|---|
  | **Extra Index Buffer** | 每个权重向量都需要 index | 增加 SRAM/Buffer 面积 |
  | **Heavy Multi-Port Decoder** | PE Array 并行计算时需要大量并行 codebook lookup | Decoder 端口数多、面积大 |
  | **随机访存增加** | Index 指向不同 codebook entry | 访问模式不规则 |
  | **带宽压力转移** | 权重压缩后仍需读取 index 和 codebook | 片上搬运复杂 |
  | **控制复杂度高** | 每个 token tile/weight tile 都要解码 | 调度和同步困难 |

- **为什么 Multi-Port Decoder 很重**：
  - LLM 推理中的 **PE Array** 通常需要在同一周期消费大量权重。
  - 若权重以 VQ 形式存储，PE Array 不能直接读取连续权重，而必须先读取多个 **Index**。
  - 多个 index 可能同时指向不同 **Codebook entry**。
  - 因此 decoder 需要支持多端口并发查找，形成 **Multi-Port Decoder**。
  - 这会带来显著的 **面积、功耗、布线和时序压力**。

- **为什么 Index Buffer 是额外负担**：
  - 原始 INT4 权重只需要存储权重本身。
  - VQ 后虽然每个 value 的等效 bit 数下降，例如图中给出 **2.5bit/value**，但系统必须额外保存 **Index**。
  - Index Buffer 需要被频繁访问，其访问量与权重矩阵规模相关。
  - 对边缘 LLM accelerator 来说，片上 SRAM 容量有限，Index Buffer 会挤占宝贵片上存储资源。

- **图中“Extra Index Buffer and Heavy Multi-Port Decoder”是对传统 VQ 的批判性总结**：
  - 传统 VQ 在算法层面减少了权重 bit 数。
  - 但在硬件层面引入了新的解码结构。
  - 对高并行度 LLM accelerator 来说，解码结构可能成为新的瓶颈。
  - 因此，单纯使用传统 VQ 并不一定能带来端到端加速。

- **与本文提出的 BVQ 的关系**：
  - 该图是为了引出本文的 **Blockwise Vector Quantization, BVQ**。
  - 传统 VQ 是细粒度向量级索引，硬件需要大量 index buffer 和复杂 decoder。
  - BVQ 改为 **block-level clustering**，以 block 为单位共享 codebook entry。
  - 这样可以降低索引访问复杂度，并允许使用更轻量的 **ISA decoder** 来触发 codebook 读取。
  - 因此，BVQ 更适合本文的 **ReRAM-stacked Processing-Near-Memory, RS-PNM** 架构。

- **传统 VQ 与本文 BVQ 的对比可概括如下**：

  | 维度 | Traditional VQ | 本文 BVQ |
  |---|---|---|
  | 粒度 | 向量级 | **Block-level** |
  | 索引存储 | 需要大量 **Index Buffer** | 索引更结构化，可由 ISA 控制 |
  | 解码结构 | **Multi-Port Decoder** 复杂 | 轻量 **ISA decoder** |
  | 访存模式 | index-driven，较随机 | block/codebook-driven，更规整 |
  | 硬件友好性 | 较差 | 更适合 **RS-PNM + ReRAM** |
  | 目标 | 压缩权重 | 压缩权重并减少 EMA/解码开销 |

- **从系统瓶颈角度看，该图对应论文中的第二个挑战**：
  - Draft LLM, DLM 虽然比 Target LLM, TLM 小，但边缘芯片仍难以完整缓存 DLM 权重。
  - 如果采用传统 VQ，DLM 权重可以被压缩，但 index 和 decoder 又带来额外硬件成本。
  - 因此，论文提出 **BVQ + ReRAM-stacked RS-PNM**，目标是既压缩 DLM 权重，又避免传统 VQ 的硬件开销。

- **该图对 ReRAM-on-Logic 架构的启示**：
  - ReRAM 提供较大容量和高密度存储，适合放置 DLM codebook。
  - 但如果仍采用传统 VQ，频繁读取 index 和多端口解码会削弱 ReRAM 带来的收益。
  - 因此需要让 codebook 访问更加规整，并尽量减少重复访问。
  - 这也是后续图中 **Tile Fusion Unit, TFU** 和 **vertical CB mapping** 设计的动机。

- **总结性判断**：
  - 该图不是在强调传统 VQ 的压缩能力，而是在强调其 **硬件实现代价**。
  - 传统 VQ 的核心缺陷是：**把权重存储压力转化为了 index 存储压力和 decoder 复杂度压力**。
  - 本文通过 **BVQ** 将 VQ 从细粒度、随机访问、decoder-heavy 的模式，转化为更适合 ReRAM 堆叠架构的 **block-level codebook retrieval** 模式。
  - 因此，该图在论文中起到承上启下作用：先说明传统 VQ 不适合边缘 LLM accelerator，再引出 **RS-PNM + BVQ** 的必要性。

### 819f1860c7b38c47f1101cea72e371d35429b04af70f40b0620a4e01293f787f.jpg

![819f1860c7b38c47f1101cea72e371d35429b04af70f40b0620a4e01293f787f.jpg](images/819f1860c7b38c47f1101cea72e371d35429b04af70f40b0620a4e01293f787f.jpg)

- 这张图展示的是 **BVQ（Blockwise Vector Quantization）** 的核心思想：把原本需要逐元素存储/传输的 DLM 权重，改成按 **block** 进行聚类与索引化表示，从而显著压缩存储和外部访问开销。
- 图的主线非常清楚：**训练时学习“块属于哪个 codebook”**，推理时只保留 **index + codebook**，再由 **Lightweight Decoder** 按需还原权重块。

- 图中各区域含义如下：

| 区域 | 图中元素 | 作用 | 关键点 |
|---|---|---|---|
| 左上 | **Input Channel / DLM Weight** | 原始权重矩阵被切分成多个 block | 以块为单位而非逐权重处理 |
| 右上 | **INT4 Blockwise Codebook** | 存储若干个代表性 block 模板，如 **B00, B01, B02, B03** | codebook 采用 **INT4**，便于硬件存储 |
| 中间上 | **Index@Inference** | 推理阶段用离散 index 指示每个 block 选哪个 codebook entry | 典型为 **2-bit/value** 的索引语义 |
| 中间下 | **Index@Training + Gumbel Softmax** | 训练阶段用可导方式学习离散选择 | 通过 **Gumbel Softmax** 近似 one-hot 选择 |
| 下方 | **Weighted Block@Training / Learnable Blocks with QAT** | 训练时用软权重组合多个 codebook block | 让离散量化过程可训练，并兼顾精度 |

- 这张图的关键创新点是 **“训练软选择，推理硬选择”**：
  - **训练时**：一个 block 不是直接固定绑定到某个 codebook，而是通过 **Gumbel Softmax** 得到一组概率权重。
  - 图中示例里，某个 block 对 **B01** 的权重最高，接近 **0.96**，说明它最终几乎会被分配到 **B01**。
  - **推理时**：概率被离散化，只保留一个 **index**，例如 **00 / 01 / 10 / 11**，然后直接查表重构 block。

- 图里“**Weighted Block@Training**”那一行本质上表示：
  - 一个待量化 block ≈ **多个 codebook block 的加权和**
  - 这样做的好处是：
    - 保留梯度，便于训练
    - 逼近离散量化结果
    - 降低直接硬分配带来的精度损失

- 从压缩角度看，这个设计的价值很直接：
  - **权重不再逐值存储**
  - 只需存：
    - 少量 **codebook blocks**
    - 每个 block 的 **index**
  - 因而能把 DLM 的权重外存访问从“大体积权重搬运”变成“**小索引 + 共享模板**”的访问模式

- 从硬件角度看，这张图对应论文里的 RS-PNM 思路：
  - **codebook** 可以放在高密度 **ReRAM**
  - **index buffer / lightweight decoder** 负责快速选择对应块
  - 避免传统 VQ 里常见的 **大 index buffer、复杂 decoder、多端口访问** 问题
  - 这正是论文声称能降低 DLM EMA 的核心原因之一

- 这张图还隐含了一个重要设计取舍：
  - **粒度更粗**：block-level 而不是 element-level
  - **优点**：索引更少、硬件更简单、重构更快
  - **代价**：block 内共享同一模板，表达能力略受限制
  - 因此它必须配合 **QAT + Gumbel Softmax**，否则精度容易掉得太多

- 结合论文全文，这个 BVQ 模块的作用可以概括为一句话：
  - **用“可训练的块级代码本压缩”替代传统逐权重量化，使 DLM 在 ReRAM 堆叠架构中以更低带宽、更低访问开销运行。**

- 如果把这张图浓缩成流程，就是：
  - **原始权重 block**
  - → 训练时用 **Gumbel Softmax** 学习分配到哪个 codebook
  - → 得到 **block index**
  - → 推理时通过 **Lightweight Decoder** 查表重构
  - → 最终实现 **低开销 DLM 权重重建**

- 总体评价：
  - 这是一张典型的 **“算法—硬件协同压缩图”**
  - 它不是单纯追求极致压缩率，而是明确面向 **LLM decoding** 场景下的 **带宽瓶颈**
  - 所以它真正优化的是 **EMA 成本、重构复杂度和硬件可实现性**，而不仅仅是模型大小

### 97f80fa61e954e186a5dcf2ee5a4553835eaf57f696350627cf21031022499bb.jpg

![97f80fa61e954e186a5dcf2ee5a4553835eaf57f696350627cf21031022499bb.jpg](images/97f80fa61e954e186a5dcf2ee5a4553835eaf57f696350627cf21031022499bb.jpg)

- 这张图是一个**三组对比柱状图**，核心结论很明确：在不同的 **TLM + DLM** 组合下，所提方法都能带来**稳定的性能提升**，提升幅度分别达到 **1.46×、1.10×、1.23×**。

- 图中横轴对应三种模型组合：
  - **Vicuna-1B & LLaMA-160M**
  - **LLaMA2-7B & LLaMA-160M**
  - **LLaMA3-8B & LLaMA-296M**

- 每组包含两根柱子，表示**基线方案**与**优化方案**之间的对比。结合论文上下文，这里主要反映的是 **BVQ + RS-PNM / TFU** 对 **DLM 侧 ReRAM codebook 访问冗余** 的缓解效果，或者等价地说是**由减少重复访问带来的性能提升**。

- 图上方标出的倍率非常关键：
  
  | 模型组合 | 提升倍率 | 含义 |
  |---|---:|---|
  | Vicuna-1B & LLaMA-160M | **1.46×** | 提升最明显，说明该组合下 **codebook 复用收益最大** |
  | LLaMA2-7B & LLaMA-160M | **1.10×** | 提升最小，说明该组合下 **可消除的冗余较少** 或 **访问模式更均匀** |
  | LLaMA3-8B & LLaMA-296M | **1.23×** | 中等提升，说明仍存在较明显的重复 CB 访问 |

- 从视觉上看，柱高并不是“绝对性能值”，而更像是**归一化后的相对量**。这类画法通常用于展示：
  - **baseline** 下的冗余访问更高；
  - **optimized** 下通过 **CB fusion / tile fusion** 后，访问量或时间被压缩；
  - 最终体现为**吞吐提升**或**访问减少**。

- 结合论文内容，这张图对应的技术点主要是：
  - **BVQ（Blockwise Vector Quantization）**：把 DLM 权重压缩为 block-level codebook；
  - **RS-PNM**：让 ReRAM 直接存储并提供 codebook；
  - **TFU（Tile Fusion Unit）**：把共享同一 codebook entry 的 token tile 合并，只读取一次，避免**redundant codebook access**。

- 这张图的工程意义在于：
  - 证明 **BVQ 不是只做压缩**，而是能真正降低运行时的**重复 ReRAM 访问**；
  - 证明 **不同模型组合下收益不同**，说明该优化对模型结构和 token/CB 复用模式敏感；
  - 也侧面说明论文的系统设计是**“数据布局 + 存储层级 + 执行单元”协同优化**，不是单点优化。

- 如果从论文整体目标看，这张图支持了一个重要判断：  
  **DLM 的瓶颈不只是算力，而是 codebook 读取和外部/片上存储访问效率。**  
  通过 **ReRAM stacking + BVQ + TFU**，作者把这部分瓶颈压下去了。

- 简要结论：
  - **这是一个证明 BVQ/TFU 能降低 DLM 冗余 codebook 访问的对比图。**
  - **三组模型都有效，最好的是 Vicuna-1B & LLaMA-160M，达到 1.46× 提升。**
  - **说明该方法在 speculative decoding 场景下具有较强的通用性，但收益会随模型组合变化。**

- 若你需要，我还可以继续帮你把这张图和论文中的 **Figure 31.1.4 / RS-PNM / TFU / CILM** 之间的关系画成一张**逻辑链路图**。

### 0560972ac4dbc9161b2953474dfa5064336a4a15754a376109102544e96082e2.jpg

![0560972ac4dbc9161b2953474dfa5064336a4a15754a376109102544e96082e2.jpg](images/0560972ac4dbc9161b2953474dfa5064336a4a15754a376109102544e96082e2.jpg)

- **图片核心含义**
  - 该图展示了 **Local Rotation Unit（LRU）** 的一次工作示例，用于实现论文提出的 **decomposed FWHT** 局部旋转流程。
  - 目标是用低成本硬件近似传统 **Global Rotation（GR）/ full FWHT**，从而在 **Target LLM（TLM）** 中消除 activation outliers，支持可靠的 **W4A8 quantization**。
  - 图中体现了 LRU 的两阶段处理：
    - **Stage 1：Upper Token 旋转**
    - **Stage 2：Lower Token 旋转**
  - 每一阶段又由两类核心计算组成：
    - **FWHT：Fast Walsh-Hadamard Transform**
    - **Hm GEMM：non-power-of-two Hadamard matrix multiplication**

- **整体数据流概览**

| 模块 / 数据 | 图中标注 | 作用 |
|---|---:|---|
| **Local Token Buffer** | 128KB | 存储待旋转 token feature tile |
| **Upper Token** | 红色虚线区域 | 第一阶段处理的上半部分 token 特征 |
| **Lower Token** | 蓝色虚线区域 | 第二阶段处理的下半部分 token 特征 |
| **RFA #1** | Reconfigurable FWHT Array | 执行可配置 FWHT |
| **HAU** | Hadamard Accumulator Unit | 执行 Hadamard 累加 / Hm GEMM |
| **TAU** | Token Allocator Unit | 控制 token tile 分配、调度、模式选择 |
| **Hm Matrix / Hm Col** | npot Hadamard matrix | 处理 non-power-of-two channel 维度 |
| **Quantized Token** | 4×2⁶×8b | 输出量化后的 token |
| **Quantizer** | 4b | 对旋转结果进行低比特量化 |

- **图中左上部分：Stage 1 的 FWHT 处理**

| 项目 | 内容 |
|---|---|
| **输入数据** | Upper Token，对应 `Data 0` 到 `Data m-1` |
| **输入宽度** | `2⁶ × 32b` |
| **主要计算单元** | **RFA #1** |
| **操作类型** | **Stage 1 FWHT** |
| **控制单元** | **TAU** |
| **关键机制** | TAU 根据 **FWHT Mode Sel** 控制 RFA 工作模式 |

- **左上图的工作逻辑**
  - **Upper Token** 从 **Local Token Buffer（128KB）** 中取出。
  - 每个 token tile 的宽度为 **2⁶×32b**，说明该局部 FWHT 的最大深度为 **6-depth FWHT**。
  - **RFA #1** 对 Upper Token 执行第一阶段 **FWHT rotation**。
  - **TAU** 负责：
    - 分配 token tile 到 RFA。
    - 选择 FWHT 模式。
    - 控制不同 `2¹` 到 `2⁶` FWHT depth 的重构。
  - 该阶段主要完成 **power-of-two 部分的 Hadamard rotation**。

- **图中左下部分：Stage 1 的 Hm GEMM 处理**

| 项目 | 内容 |
|---|---|
| **输入数据** | Upper Token 与 `Hm Matrix` |
| **矩阵列** | `Hm Col 0` 到 `Hm Col m-1` |
| **主要计算单元** | **HAU** |
| **操作类型** | **Stage 1 Hm GEMM** |
| **输出** | 经过 npot Hadamard 部分融合后的 Upper Token |
| **量化位宽** | **4b** |

- **左下图的工作逻辑**
  - Stage 1 的第二步是处理 **non-power-of-two Hadamard matrix** 部分。
  - 图中 `Hm Matrix` 表示预计算的 **npot Hadamard matrix**。
  - `Hm Col 0` 到 `Hm Col m-1` 被送入 **HAU**。
  - **HAU** 执行 Hadamard accumulation，而不是完整高成本 GEMM。
  - 这里的设计重点是：
    - 利用 Hadamard matrix 的 ±1 / binary-like 特性。
    - 避免大量高精度乘法器。
    - 将 Hadamard accumulation 与 quantizer scale 融合。
  - 最终输出被送入 **4b quantizer**，形成低比特旋转 token。

- **图中右上部分：Stage 2 的 Hm GEMM 处理**

| 项目 | 内容 |
|---|---|
| **输入数据** | Lower Token，对应 `Data c` 到 `Data c+m-1` |
| **输入宽度** | `2⁶ × 32b` |
| **主要计算单元** | **HAU** |
| **操作类型** | **Stage 2 Hm GEMM** |
| **控制单元** | **TAU** |
| **输出数据** | `4 × 2⁶ × 8b Quantized Token` |

- **右上图的工作逻辑**
  - 第二阶段开始处理 **Lower Token**。
  - 与 Stage 1 不同，图中先展示 **Hm GEMM**。
  - `Data c` 到 `Data c+m-1` 表示 Lower Token 覆盖的是原始 channel 中的另一个局部窗口。
  - 这些数据与 `Hm Col 0` 到 `Hm Col m-1` 一起送入 **HAU**。
  - HAU 完成 npot Hadamard 部分的累加。
  - 输出形成 **4×2⁶×8b Quantized Token**，说明：
    - 局部旋转后 token 被压缩到 **INT8 activation**。
    - 每次可形成多个 token tile 或 channel group 的量化输出。
  - 这与论文中 **W4A8 TLM quantization** 对应。

- **图中右下部分：Stage 2 的 FWHT 处理**

| 项目 | 内容 |
|---|---|
| **输入数据** | Lower Token |
| **主要计算单元** | **RFA #1** |
| **操作类型** | **Stage 2 FWHT** |
| **控制

### 97c7394ad08263be0724e606d82e0ee89e81c8a67c8ad4bcac4fea1ad492e51a.jpg

![97c7394ad08263be0724e606d82e0ee89e81c8a67c8ad4bcac4fea1ad492e51a.jpg](images/97c7394ad08263be0724e606d82e0ee89e81c8a67c8ad4bcac4fea1ad492e51a.jpg)

- **图片核心对象**：该图展示的是 **Reconfigurable FWHT Array（RFA）**，属于论文中 **Local Rotation Unit（LRU）** 的关键子模块，用于执行低成本、可重构的 **Fast Walsh-Hadamard Transform（FWHT）**，以支持 **outlier-free low-bit TLM quantization**。

- **设计目标**：RFA 的主要目标是 **降低高精度加法器面积开销**，具体方法是：
  - **合并 early-stage adjacent FWHT**；
  - **共享输入数据**；
  - 使用 **4-input Router Network** 灵活选择不同 FWHT 模式下的数据路径；
  - 支持从 **2¹ 到 2⁶** 的可重构 FWHT 深度；
  - 避免为不同维度单独配置大量固定 FWHT 硬件。

- **图中左侧结构：2¹–2⁶ FWHT Selector**

| 模块 | 功能 | 说明 |
|---|---|---|
| **2¹/2² FWHT Selector** | 选择低阶 FWHT 模式 | 支持较小 tile 或局部旋转的浅层变换 |
| **4-input RFA PE #0** | 4 输入处理单元 | 对应小规模 FWHT 基础计算 |
| **4-input RFA PE #15** | 4 输入处理单元 | 与 PE #0 等构成并行处理阵列 |
| **32-input RFA PE #0** | 32 输入处理单元 | 支持更深层 FWHT |
| **32-input RFA PE #1** | 32 输入处理单元 | 与 PE #0 配合完成中等规模变换 |
| **64-input RFA PE #0** | 64 输入处理单元 | 支持最大 **2⁶ FWHT** 模式 |
| **2³–2⁶ FWHT Selector** | 选择高阶 FWHT 模式 | 根据 token tile 维度选择 8/16/32/64 点 FWHT |

- **左侧结构反映了 RFA 的可重构能力**：
  - 当需要执行 **2¹ 或 2² FWHT** 时，使用上方的 **4-input RFA PE**；
  - 当需要执行 **2³ 到 2⁵ FWHT** 时，可通过 **32-input RFA PE** 组合完成；
  - 当需要执行 **2⁶ FWHT** 时，使用底部的 **64-input RFA PE**；
  - 这种分层结构避免了为每种 FWHT size 单独实现完整阵列。

- **图中右侧结构：RFA PE 内部数据路径**

| 组件 | 图中标注 | 功能 |
|---|---|---|
| **输入索引组合** | i×2²+0、i×2²+1、i×2²+2、i×2²+3 | 表示每个 PE 处理一组 4 路输入 |
| **4-input Router Network** | 4-input Router Network | 根据 FWHT mode 选择和重排输入 |
| **Neg. Ctrl** | Negative Control | 控制 Hadamard 符号翻转，即加/减关系 |
| **32b ADD** | 32-bit Adder | 执行高精度加法累加 |
| **FWHT Mode Sel** | FWHT Mode Sel 2¹ or 2² | 选择当前 PE 工作于 2¹ 或 2² 模式 |
| **Sel** | 输出选择 | 选择最终输出路径 |

- **右侧 PE 的关键机制是 input sharing**：
  - 多个 adjacent FWHT 在 early stage 具有相似输入；
  - RFA 将这些输入合并后送入 **4-input Router Network**；
  - Router 根据模式选择不同输入组合；
  - 再由 **Neg. Ctrl** 决定符号；
  - 最后通过 **32b ADD** 完成 FWHT 中的加减运算。

- **为什么需要 Neg. Ctrl**：
  - Hadamard Transform 本质由 **+1 / -1** 构成；
  - FWHT 计算可以转化为加法和减法；
  - **Neg. Ctrl** 用于控制某一路输入是否取负；
  - 因此无需显式乘法器，实现 **MAC-free Hadamard operation**；
  - 这与论文中 HAU 的 **MAC-free accumulation** 思路一致。

- **为什么使用 32b ADD**：
  - FWHT 过程中 activation 可能经过多级加减累积；
  - 为避免精度损失，需要较高位宽的加法器；
  - 图中采用 **32-bit Adder**，说明 RFA 在旋转阶段保持较高内部精度；
  - 旋转完成后再进行 dynamic quantization 到 INT8 activation。

- **该 RFA 与普通 FWHT 阵列的区别**

| 对比项 | 普通 Global FWHT Array | 图中 RFA |
|---|---|---|
| 支持维度 | 通常针对固定大维度 | 支持 **2¹–2⁶** 可重构 |
| 硬件规模 | 深 FWHT 阵列面积大 | 使用 shallow FWHT 降低面积 |
| 数据路径 | 固定连接较多 | 使用 **Router Network** 动态选择 |
| 加法器需求 | 大量高精度加法器 | 通过 **input sharing** 减少加法器 |
| 适配 npot 维度 | 成本高 | 配合 LRU 的 local rotation 更灵活 |
| 面积效率 | 较低 | 论文称相比 global rotation 节省 **92.7% area** |

- **图中“Reduce High-Precision Adders by Merging Early Adjacent FWHTs and Input Sharing”的含义**：
  - FWHT 前几级计算中，多个小规模 butterfly 操作之间存在输入复用机会；
  - 如果直接实现，每个 butterfly 都需要独立高精度加法器；
  - RFA 将相邻 FWHT 的 early stage 合并；
  - 通过共享输入和可配置路由减少重复加法；
  - 因此显著降低 **32b ADD** 数量。

- **RFA 在 LRU 中的角色**

| LRU 流程阶段 | RFA 作用 |
|---|---|
| Token tile 分配 | TAU 将 token features 分配给 RFA |
| Local FWHT | RFA 执行 2¹–2⁶ 的可重构 FWHT |
| 符号控制 | Neg. Ctrl 完成 Hadamard 正负号控制 |
| 输出传递 | RFA 输出送往 HAU 或后续量化路径 |
| 动态量化 | 旋转后的 token 再进行 INT8 dynamic quantization |

- **为什么 RFA 只支持到 2⁶ FWHT**：
  - 论文指出传统 global rotation 对于如 LLaMA3-8B down_proj 的 **14336 = 2⁹ × 28** 维度，可能需要较深 FWHT；
  - 深 FWHT 会带来大量高精度加法器和面积开销；
  - 本文通过 **decomposed FWHT** 将深度限制到 **6-depth FWHT**；
  - 再通过 upper/lower overlapped local rotation 近似 global rotation；
  - 因此 RFA 只需支持最大 **64-point FWHT**，即可覆盖设计需求。

- **图中结构对应论文贡献**

| 论文贡献 | 图中体现 |
|---|---|
| **Local Rotation Unit（LRU）** | RFA 是 LRU 的核心计算单

### 8c4baa23a1ba69610aff40a4916b97489e65eafaae6404b25f2608dc6e7d54b5.jpg

![8c4baa23a1ba69610aff40a4916b97489e65eafaae6404b25f2608dc6e7d54b5.jpg](images/8c4baa23a1ba69610aff40a4916b97489e65eafaae6404b25f2608dc6e7d54b5.jpg)

- **图片定位**
  - 该图是 Figure 31.1.3 中 **Local Rotation Unit, LRU** 的局部电路模块，具体展示 **HAU PE #3** 的内部结构。
  - HAU 指 **Hadamard Accumulator Unit**，用于在 LRU 中执行 decomposed FWHT 后半段的 **Hadamard 累加与动态量化融合**。
  - 该模块服务于 **outlier-free low-bit TLM quantization**，目标是在不引入大面积 global rotation 硬件的情况下，实现近似全局旋转效果。

- **图中核心数据流**
  - 输入来自两路：
    - **Hn Tile [0]**
      - 表示当前使用的 **npot Hadamard tile** 或 Hadamard 子矩阵块。
    - **RFA Data i**
      - 表示来自 **Reconfigurable FWHT Array, RFA** 的输出数据。
  - 数据先进入 **32b ADD** 累加器。
  - 累加结果形成 **26×32b PSUM**。
  - PSUM 进一步送入 **Dynamic Quantizer**。
  - Dynamic Quantizer 输出 **26×8b INT8 Quant.**
  - 旁路输出 **Scale**，供后续 TFTE 或量化 GEMM 使用。

- **结构组成表**

| 模块 | 图中标注 | 功能 | 关键意义 |
|---|---|---|---|
| Hadamard Tile 输入 | **Hn Tile [0]** | 提供 Hadamard 符号/系数 tile | 支持 npot Hadamard 构造 |
| RFA 输出输入 | **RFA Data i** | 接收前级 6-depth FWHT 的局部旋转结果 | 承接 decomposed FWHT |
| 选择/控制逻辑 | 小型 MUX/门控路径 | 选择当前 tile 和数据路径 | 支持不同 tile-m 配置 |
| 高精度累加器 | **32b ADD** | 执行 Hadamard accumulation | 保持旋转后数值精度 |
| 部分和缓存 | **26×32b PSUM** | 存储多个通道/向量元素的累加结果 | 支持 tile-wise 并行处理 |
| 动态量化器 | **Dynamic Quantizer** | 将 FP/高精度 PSUM 转为 INT8 | 降低后续计算与存储开销 |
| 缩放因子 | **Scale** | 记录动态量化 scale | 保证反量化或后续层量化正确性 |
| 输出激活 | **26×8b INT8 Quant.** | 输出 INT8 激活 | 匹配 W4A8 TLM 推理 |

- **关键计算过程**
  - **RFA Data i** 是前级 FWHT 局部旋转后的特征。
  - **Hn Tile [0]** 提供 Hadamard tile 的符号或二值结构。
  - HAU PE 通过累加方式完成：
    - **Hadamard tile 与 RFA 输出的融合**
    - **高精度 partial sum accumulation**
    - **动态量化 scale 融合**
  - 图中标注 **“Store i-1 in Hn as 0”**，表示在特定 tile 映射或边界条件下，将上一位置或无效位置写为 0，用于处理 **non-power-of-two dimension** 的对齐与覆盖问题。
  - 最终输出为 **INT8 Quant.**，并同时输出 **Scale**。

- **为什么需要 HAU PE**
  - LLM 中很多维度不是 2 的幂，例如文中举例：
    - LLaMA3-8B down_proj layer: **14336 = 2⁹ × 28**
  - 传统 FWHT 对 2 的幂维度友好，但对 **non-power-of-two, npot** 维度需要额外 Hadamard matrix 处理。
  - 若直接使用 global rotation，会产生大量高精度算子和深层 FWHT 阵列，面积开销巨大。
  - 该 HAU PE 的作用是：
    - **避免完整 global rotation 硬件**
    - **用局部 tile 累加近似全局 Hadamard rotation**
    - **减少高精度加法器数量**
    - **将 rotation 与 dynamic quantization 合并**

- **图中 “Fusing FP Had. and Dynamic Quantizer’s Scales” 的含义**
  - 图顶部文字说明该 PE 支持：
    - **Fusing FP Had.**
    - **Dynamic Quantizer’s Scales**
  - 即 Hadamard 旋转中的高精度 Hadamard 系数处理，与动态量化 scale 计算被融合在同一数据路径中。
  - 这样可以减少：
    - 额外乘法
    - 独立 scale 处理单元
    - 中间数据搬移
    - SRAM/寄存器访问

- **Dynamic Quantizer 的作用**
  - 图中 Dynamic Quantizer 包含：
    - **Scale FIFO**
    - **INT8 Quant.**
    - **Scale 输出路径**
  - 它对 HAU 累加后的 PSUM 执行动态量化：
    - 根据当前 token/tile 的数值范围生成 scale。
    - 将 32b PSUM 压缩为 INT8 activation。
    - 将 scale 旁路到后续计算单元。
  - 这对应论文中的 **W4A8 TLM quantization**：
    - Weight: INT4
    - Activation: INT8
  - 其价值是缓解 activation outlier 对 INT8 激活量化的破坏。

- **数据位宽分析**

| 数据节点 | 位宽 | 说明 |
|---|---:|---|
| RFA Data i | 图中未完整给出，通常为高精度/中间精度 | 来自 RFA 的 FWHT 输出 |
| Hn Tile | 符号/低复杂度 Hadamard tile | 用于 Hadamard 累加 |
| ADD 输出 | **32b** | 保留旋转累加精度 |
| PSUM | **26×32b** | 26 个 32-bit partial sums |
| Quantized Output | **26×8b** | INT8 激活输出 |
| Scale | scale path | 动态量化缩放因子 |

- **“26×32b PSUM” 与 “26×8b” 的意义**
  - **26** 很可能对应当前 tile 或通道分组中的并行元素数量。
  - 先用 **32b PSUM** 保存累加结果，避免旋转累加中的精度损失。
  - 再压缩为 **26×8b INT8**，减少后续 TFTE/GEMM 的计算与带宽压力。
  - 这种设计体现了典型硬件折中：
    - **内部高精度**
    - **外部低位宽**
    - **量化 scale 旁路保持数值可恢复性**

- **与 LRU 整体设计的关系**
  - LRU 的整体流程是：
    - TAU 分配 token tile。
    - RFA 执行低深度 FWHT。
    - HAU 执行 Hadamard accumulation。
    - Dynamic Quantizer 产生 INT8 activation 与 scale。
  - 该图中的 HAU PE 位于 **RFA 之后、TFTE 之前**。
  - 它是 LRU 能够支持 **npot Hadamard construction** 和 **local rotation approximation** 的关键部件。

- **硬件优化点**
  - **MAC-free accumulation**
    - Hadamard 矩阵元素通常为 ±1，因此乘法可转化为加减法。
    - 图中核心是 **32b ADD**，而不是 multiplier。
  - **Scale fusion**
    - 将 Hadamard 处理与 dynamic quantization scale 融合，减少独立数据路径。
  - **Tile-based processing**
    - 使用 tile 而非完整矩阵，降低面积和缓存需求。
  - **局部高精度、全局低位宽**
    - 内部用 32b PSUM 保证精度。
    - 输出用 INT8 降低后续访存与计算开销。
  - **边界补零**
    - 通过 “Store i-1 in Hn as 0” 等控制处理 npot 维度中的无效位置。

- **该模块解决的问题**
  - 解决 **activation outlier**：
    - 通过 Hadamard rotation 平滑激活分布。
    - 使 W4A8 量化更稳定。
  - 解决 **global rotation area overhead**：
    - 用 local/decomposed FWHT 替代深层全局 FWHT。
    - 文中报告 LRU 相比 global rotation 节省 **92.7% area**。
  - 解决 **npot dimension compatibility**：
    - 支持非 2 的幂通道维度。
    - 避免为每个大维度设计复杂 cascaded FWHT-GEMM array。
  - 解决 **量化数据搬移开销**：
    - 旋转、累加、量化、scale 生成在近邻路径中完成。

- **从系统性能角度看该 PE 的贡献**
  - 该 PE 是 LRU 实现 W4A8 TLM 的底层算子。
  - LRU 使 TLM 能够从 BF16 降到 W4A8，同时保持 perplexity 接近 BF16。
  - 文中结果显示：
    - Vicuna-1B: BF16 **9.18**，W4A8 w/ LRU **9.41**
    - LLaMA2-7B: BF16 **5.47**，W4A8 w/ LRU **5.68**
    - LLaMA3-8B: BF16 **6.14**，W4A8 w/ LRU **6.71**
  - LRU 带来 **3.82-to-3.93× speedup over BF16 SD**。
  - 因此，该 HAU PE 虽然是小模块，但对系统级吞吐提升非常关键。

- **总结**
  - 该图片展示的是 **LRU 中 HAU PE 的局部微架构**。
  - 它通过 **32b Hadamard accumulation + Dynamic Quantizer + Scale bypass** 实现局部旋转后的低位量化。
  - 设计重点是：
    - **MAC-free Hadamard accumulation**
    - **支持 npot dimension**
    - **融合 dynamic quantization scale**
    - **输出 INT8 activation**
    - **降低 global rotation 面积开销**
  - 该模块直接支撑论文提出的 **outlier-free W4A8 TLM quantization**，是实现高吞吐 speculative decoding accelerator 的关键硬件单元。

### 575f904a6141fe74ac1be14c939977e542cf59406dcbb2f76feac93b82137f69.jpg

![575f904a6141fe74ac1be14c939977e542cf59406dcbb2f76feac93b82137f69.jpg](images/575f904a6141fe74ac1be14c939977e542cf59406dcbb2f76feac93b82137f69.jpg)

- **图片主题**：该图展示了 **ReRAM-Stacked PNM（RS-PNM）Architecture based on BVQ**，即基于 **Blockwise Vector Quantization（BVQ）** 的 **ReRAM 堆叠式近存计算架构**。其核心目标是：  
  - 将 **Draft LLM（DLM）压缩后的 codebook（CB）** 存储在高密度 **stacked ReRAM** 中。  
  - 通过高带宽 **face-to-face ReRAM-on-logic stacking interface** 快速读取 codebook。  
  - 在逻辑 die 上重构/使用 DLM 权重，减少甚至避免 DLM 的外部 DRAM 访问。  
  - 配合 **Tile Fusion Unit（TFU）** 消除重复 codebook 访问，提高 ReRAM 带宽利用率。

- **整体结构可分为 4 个主要层次**：

| 层次 | 图中模块 | 主要功能 |
|---|---|---|
| **ReRAM Storage Layer** | ReRAM Die #0~#3，每个 2MB | 存储 DLM 的 BVQ codebook，总计 8MB ReRAM |
| **ReRAM Load Interface Layer** | RLI、Double-Rate Stabilizer、Asynchronous FIFO Groups、WB Bank Write Interface | 从 ReRAM 读取 codebook，并完成高速/异步时钟域转换 |
| **Weight Buffer & Codebook Fetch Layer** | CFU、Codebook Selector、WB Bank Addr Controller、1MB Weight Buffer | 选择 codebook、控制写入地址、缓存重构/待用权重数据 |
| **Compute & Token Buffer Layer** | TFTE、TFU、Mixed-Precision MAC Array、2MB Global Token Buffer | 执行 tile fusion、矩阵计算，并管理 token tile 数据 |

- **顶部 ReRAM die 结构分析**：

| 模块 | 规模/数量 | 作用 |
|---|---:|---|
| **ReRAM Die #0** | 2MB | 存储部分 DLM codebook |
| **ReRAM Die #1** | 2MB | 存储部分 DLM codebook |
| **ReRAM Die #2** | 2MB | 存储部分 DLM codebook |
| **ReRAM Die #3** | 2MB | 存储部分 DLM codebook |
| **总 ReRAM 容量** | **8MB** | 用于存储 BVQ 压缩后的 DLM codebooks |
| **ReRAM Controller** | 位于 Die #0 一侧 | 控制 ReRAM 读取流程 |

- **该设计的关键点是 ReRAM 并不是直接执行模拟 CIM 计算，而是作为高密度近存储层使用**：  
  - 图中 ReRAM dies 主要承担 **codebook storage**。  
  - 计算仍主要在 logic die 中的 **Mixed-Precision MAC Array** 完成。  
  - 因此这是 **Processing-Near-Memory（PNM）**，不是典型 **Processing-In-Memory（PIM/CIM）**。  
  - 优点是更容易保证计算精度、可编程性和工艺兼容性。

- **ReRAM Load Interface（RLI）是图中的数据入口核心**：

| 子模块 | 图中标注 | 功能 |
|---|---|---|
| **Double-Rate Stabilizer** | 200MHz Domain | 对 ReRAM 读出数据进行双倍速率稳定化 |
| **Asynchronous FIFO Groups** | 异步 FIFO 组 | 完成 ReRAM 时钟域与逻辑计算时钟域之间的数据跨域 |
| **WB Bank Write Interface** | 250MHz Domain | 将读取到的 codebook/权重数据写入 Weight Buffer |

- **RLI 的设计意义**：  
  - ReRAM die 工作频率为 **100MHz**，但逻辑侧存在更高频域。  
  - 图中通过 **Double-Rate Stabilizer（200MHz Domain）** 先稳定 ReRAM 输出。  
  - 再通过 **Asynchronous FIFO Groups** 解决跨时钟域问题。  
  - 最后由 **WB Bank Write Interface（250MHz Domain）** 写入片上 SRAM buffer。  
  - 该路径保证了 **ReRAM 低频读出与逻辑高频计算之间的可靠衔接**。

- **Codebook Fetcher Unit（CFU）位于左侧，是 BVQ 的控制中心**：

| CFU 子模块 | 功能 |
|---|---|
| **Codebook Selector** | 根据当前 DLM layer/block/tile 所需索引选择对应 codebook |
| **WB Bank Addr Controller** | 控制 codebook 写入 1MB Weight Buffer 的 bank 地址 |
| **与 RLI 协作** | 触发 ReRAM 读取，并决定数据落入哪个 WB bank |

- **CFU 的作用可以理解为“把压缩权重索引翻译成 ReRAM codebook 读取动作”**：  
  - BVQ 将 DLM 权重压缩为 **block-level codebook + block index**。  
  - 推理时不需要从 DRAM 读取完整 DLM 权重。  
  - CFU 根据 block index 定位 codebook。  
  - 通过 RLI 从 ReRAM 中读取 codebook entry。  
  - 写入 **Weight Buffer（WB）** 后供 MAC 阵列使用。

- **1MB Weight Buffer（WB）结构**：

| 模块 | Bank 范围 | 作用 |
|---|---|---|
| **WB Bank #0-3** | Bank 0~3 | 缓存一部分 codebook/权重数据 |
| **WB Bank #4-7** | Bank 4~7 | 缓存一部分 codebook/权重数据 |
| **WB Bank #8-11** | Bank 8~11 | 缓存一部分 codebook/权重数据 |
| **WB Bank #12-15** | Bank 12~15 | 缓存一部分 codebook/权重数据 |
| **总容量** | **1MB** | 为 Mixed-Precision MAC Array 提供权重输入 |

- **WB 被划分为 16 个 bank 的意义**：  
  - 支持并行读取。  
  - 匹配多个 MAC cluster。  
  - 降低 bank conflict。  
  - 与 ReRAM 多 die、多 bank 的高带宽读取方式对齐。  
  - 支持 intra-layer parallelism 和 tile-level 数据复用。

- **中部 TFTE（Tile-Fused Tensor Engine）是计算核心**：  
  - 图中 TFTE 包含：  
    - **Tile Fusion Unit（TFU）**  
    - **Mixed-Precision MAC Array**  
  - TFTE 的关键作用是将具有相同 codebook entry 的 token tiles 融合，避免重复加载相同 CB。  
  - 这对应论文中提到的 **“TFU fuses token tiles that share the same CB entry, ensuring each CB is fetched only once”**。

- **Tile Fusion Unit（TFU）的核心价值**：

| 问题 | 普通做法 | TFU 优化 |
|---|---|---|
| 多个 token tile 使用相同 codebook | 重复访问 ReRAM | 只读取一次 codebook |
| 垂直 CB mapping 导致重复 CB access | 带来额外 latency | TFU 合并相同 CB entry 的 tile |
| ReRAM 带宽有限 | 容易被重复访问浪费 | 提高有效带宽利用率 |
| DLM drafting 延迟 | 受 ReRAM load 限制 | 降低 CB read latency |

- **图中 TFU 左侧标注 “TFU Maps”**，表示 TFU 需要维护 tile 与 codebook 的映射关系：  
  - 哪些 token tile 使用同一个 CB entry。  
  - 哪些 tile 可以融合计算。  
  - 哪些 WB bank 中已有目标 codebook。  
  - 如何调度 MAC array 避免重复权重读取。

- **Mixed-Precision MAC Array 的作用**：  
  - 执行 DLM 的矩阵乘法。  
  - 支持混合精度计算。  
  - 与论文整体精度配置对应：  
    - **TLM: W4A8**  
    - **DLM: W4A8 with BVQ，约 2bit/value 表示能力**  
  - 图中 MAC array 被划分为多个 cluster，对应下方/上方 bank 组的数据输入。

- **Mixed-Precision MAC Array 与上下 buffer 的数据流关系**：

| 输入来源 | 输入类型 | 流向 |
|---|---|---|
| **1MB Weight Buffer** | codebook/重构权重数据 | 输入 MAC Array |
| **2MB Global Token Buffer** | token activation/tile | 输入 MAC Array |
| **MAC Array 输出** | partial sum / computed token feature | 写回 GTB 或送往后续单元 |

- **底部 2MB Global Token Buffer（GTB）结构**：

| 模块 | Bank 范围 | 作用 |
|---|---|---|
| **GTB Bank #0-3** | Bank 0~3 | 存储 token tiles / activations |
| **GTB Bank #4-7** | Bank 4~7 | 存储 token tiles / activations |
| **GTB Bank #8-11** | Bank 8~11 | 存储 token tiles / activations |
| **GTB Bank #12-15** | Bank 12~15 | 存储 token tiles / activations |
| **总容量** | **2MB** | 缓存 DLM/TLM 中间 token 数据 |

- **GTB 的作用不仅是普通 activation buffer，还服务于 TFU 的 token tile fusion**：  
  - token tile 被分布在多个 GTB bank 中。  
  - TFU 根据 tile-codebook 映射关系选择可融合 tile。  
  - MAC array 读取对应 token tile 与 WB 中的 codebook 权重。  
  - 这样可减少 ReRAM 重复访问，同时保持计算阵列利用率。

- **图中的数据流可以概括为**：  
  - **Step 1：BVQ codebook 存储在 ReRAM Die #0~#3 中。**  
  - **Step 2：CFU 根据 block index/codebook selector 发起 codebook fetch。**  
  - **Step 3：RLI 从 ReRAM 并行读取 codebook。**  
  - **Step 4：Double-Rate Stabilizer 与 Asynchronous FIFO 完成数据稳定和跨时钟域传输。**  
  - **Step 5：WB Bank Write Interface 将 codebook 写入 1MB Weight Buffer。**  
  - **Step 6：TFU 检测多个 token tiles 是否共享同一 CB entry。**  
  - **Step 7：若共享，则融合 tile，避免重复 ReRAM access。**  
  - **Step 8：Mixed-Precision MAC Array 从 WB 和 GTB 读取数据执行计算。**  
  - **Step 9：结果写回 GTB 或送往后续非线性/调度模块。**

- **该架构解决的核心瓶颈是 DLM 的 EMA（External Memory Access）**：  
  - 在 speculative decoding 中，DLM 需要频繁生成 draft tokens。  
  - 如果 DLM 权重无法全部片上缓存，则每个 token 都会产生大量 DRAM 访问。  
  - 本图架构使用 **BVQ + ReRAM stacking**，将 DLM 权重压缩为 codebook 并放入 ReRAM。  
  - 通过片上/近存访问替代外部 DRAM 访问。  
  - 因此显著降低 DLM drafting latency 和 energy。

- **BVQ 与 RS-PNM 的协同关系**：

| 技术 | 解决的问题 | 在图中的体现 |
|---|---|---|
| **BVQ** | 压缩 DLM 权重，降低存储需求 | codebook 存入 ReRAM |
| **ReRAM stacking** | 提供高密度、较高带宽近存储 | 4 个 ReRAM dies，每个 2MB |
| **RLI** | 解决 ReRAM 到 logic 的高速可靠传输 | 200MHz stabilizer + async FIFO |
| **CFU** | 根据索引选择并加载 codebook | Codebook Selector + WB Addr Controller |
| **TFU** | 减少重复 codebook 访问 | Tile fusion |
| **MAC Array** | 执行实际矩阵计算 | Mixed-Precision MAC Array |

- **该图体现了“存储压缩 + 近存读取 + 片上复用”的完整闭环**：  
  - **存储压缩**：BVQ 将 DLM 权重编码为较小 codebook。  
  - **近存读取**：ReRAM die 通过 stacking interface 提供高带宽读取。  
  - **片上复用**：TFU 将共享同一 CB 的 token tile 融合，减少重复读取。  
  - **高效计算**：Mixed-Precision MAC Array 使用 WB 和 GTB 数据执行推理。

- **与传统 VQ 架构相比，该设计更适合硬件实现**：  
  - 传统 VQ 往往需要大量 index buffer 和复杂 multi-port decoder。  
  - 图中的 BVQ 以 block-level codebook 为单位，降低索引解码复杂度。  
  - CFU 只需较轻量的 codebook selection 和 bank address control。  
  - 更适合 55nm 逻辑 die 与 ReRAM die 堆叠实现。

- **该架构的关键优势总结**：

| 优势 | 说明 |
|---|---|
| **减少 DLM DRAM EMA** | DLM codebook 存在 8MB stacked ReRAM 中 |
| **提高带宽密度** | 通过多 ReRAM die 并行读取 |
| **降低片上 SRAM 压力** | 不需要完整缓存 DLM 权重，只缓存 codebook/工作集 |
| **提升 ReRAM 有效利用率** | TFU 避免重复 CB access |
| **支持 speculative decoding** | 降低 DLM drafting 开销，提升 SD 整体吞吐 |
| **易于数字逻辑集成** | 计算在 Mixed-Precision MAC Array 中完成，ReRAM 主要作存储 |

- **可能的设计权衡**：  
  - **ReRAM 读取延迟与可靠性**：需要 Double-Rate Stabilizer 和 FIFO 处理。  
  - **CFU/TFU 控制复杂度**：需要维护 codebook、bank、tile 之间的映射。  
  - **BVQ 精度损失**：需要 QAT 和合适 block/codebook 设计维持 DLM 质量。  
  - **ReRAM 写入不适合频繁更新**：更适合存储推理阶段相对静态的 DLM codebook。  
  - **扩展到更大 DLM 时**：单芯片 8MB ReRAM 可能不足，需要多芯片扩展。

- **结合论文结果，该 RS-PNM 模块带来的收益是明确的**：  
  - 相比 **W4A8 SD with LRU**，RS-PNM with INT4 BVQ 实现 **1.1× 到 1.46× speedup**。  
  - 在 4-chip system 中，ReRAM 容量扩展到 **32MB**，带宽扩展到 **102.4GB/s**。  
  - 足以存储全部 DLM codebooks，从而显著降低 DLM 外部访存。  
  - 对 LLaMA2-7B + LLaMA-160M 配置，系统实现 **17.82 Token/s** 和 **123.41 mJ/Token**。

- **一句话概括该图**：  
  - **该 RS-PNM 架构通过将 BVQ 压缩后的 DLM codebook 存入 stacked ReRAM，并利用 CFU/RLI/TFU/MAC Array 完成高带宽读取、跨域缓存、tile 融合和混合精度计算，从而有效消除 DLM 的外部权重访存瓶颈，是该 LLM accelerator 提升 speculative decoding 吞吐的核心硬件模块之一。**

### 8beebfaf9fe91b303af3d48282e07ba4826d9ef0518f861897a6732b67385637.jpg

![8beebfaf9fe91b303af3d48282e07ba4826d9ef0518f861897a6732b67385637.jpg](images/8beebfaf9fe91b303af3d48282e07ba4826d9ef0518f861897a6732b67385637.jpg)

- **图片核心含义**：该图展示了 **Tile-Fused Tensor Engine / TFTE** 中一个计算簇如何从 **GTB Bank** 读取 token/activation tiles，从 **WB Bank** 读取 weight/codebook tiles，并在 **Cluster #0-1** 内完成并行 **8b-MAC** 运算。

- **图中主要模块对应关系如下：**

| 图中标注 | 含义 | 作用 |
|---|---|---|
| **GTB Bank #0-1** | Global Token Buffer 的 bank | 存放输入 token activation tiles，例如 **A0-A7** |
| **WB Bank #0-1** | Weight Buffer 的 bank | 存放从 ReRAM / codebook 中取出的 weight tiles，例如 **B00、B01、B02、B03** |
| **红色虚线框** | 被选中的 weight/codebook tiles | 表示当前 cluster 需要访问的一组 weight tiles |
| **Cluster #0-1** | 计算簇 | 包含 **32×16 8b-MACs**，执行 INT8 乘加 |
| **A×B 表达式** | activation tile 与 weight tile 的乘加 | 表示一次 tile-level GEMM / dot-product 计算 |

- **数据流分析：**

| 阶段 | 数据来源 | 数据内容 | 去向 |
|---|---|---|---|
| **1. Activation 读取** | **GTB Bank #0-1** | **A0, A1, A2, …, A7** | 输入到计算簇 |
| **2. Weight 读取** | **WB Bank #0-1** | **B00, B01, B02, B03 等 codebook/weight tiles** | 输入到计算簇 |
| **3. Tile 匹配** | GTB + WB | 将不同 activation tile 与对应 weight tile 配对 | 形成多个 **A×B** 运算 |
| **4. Cluster 计算** | **Cluster #0-1** | 并行执行多个 **8b-MAC** | 输出 partial sums |
| **5. 结果累加** | MAC array | 多个 tile 乘加结果 | 写回后续 buffer 或送往 nonlinear / accumulation 单元 |

- **图中计算簇的作用重点是：**
  - **Cluster #0-1** 不是只处理单个 activation-weight pair，而是同时处理多个 tile 对。
  - 图中公式形式类似：
    - **A0×B00 + A1×B00 + A2×B02 + A3×B02 + …**
  - 这说明多个 activation tiles 可能共享相同的 weight/codebook entry。
  - 因此硬件可以利用 **tile fusion** 减少重复 weight/codebook 读取。

- **与论文中 BVQ / RS-PNM 的关系：**

| 论文机制 | 图中体现 |
|---|---|
| **BVQ, Blockwise Vector Quantization** | weight 被压缩成 block-level codebook entries，例如 **B00、B01、B02** |
| **ReRAM-stacked PNM** | codebook 从 stacked ReRAM 读取后进入 **WB Bank** |
| **TFTE, Tile-Fused Tensor Engine** | 将共享同一 codebook entry 的 token tiles 融合计算 |
| **减少 redundant CB access** | 多个 A tile 复用同一个 B tile，降低 ReRAM 访问次数 |
| **提升 bandwidth utilization** | WB 中的 codebook tile 被多次计算复用，而不是反复加载 |

- **红色虚线框的意义：**
  - 红色虚线框圈出了 **WB Bank** 中当前被 cluster 使用的 weight/codebook tile 区域。
  - 这些 weight tiles 可能来自同一个或多个 codebook entry。
  - 由于 BVQ 会让多个 weight blocks 指向相同 codebook vector，因此这些 **Bxx** 可以被多个 activation tiles 共享。
  - 这正是图中强调的 **codebook reuse** 和 **tile fusion**。

- **为什么该设计可以降低 ReRAM 访问？**
  - 传统做法中，每个 token tile 或 weight block 可能单独触发一次 codebook 读取。
  - 但在 BVQ 下，多个 block 可能共享相同 codebook entry。
  - TFTE 识别这些共享关系后，将对应 activation tiles 合并调度到同一个 cluster。
  - 于是同一个 **B00 / B01 / B02** 被读取一次后，可服务多个 **A×B** 运算。
  - 结果是：
    - **减少 ReRAM codebook 重复读取**
    - **降低 read latency**
    - **提升 weight buffer reuse**
    - **提升 MAC array 利用率**

- **硬件并行性分析：**

| 并行维度 | 图中体现 | 好处 |
|---|---|---|
| **Bank-level parallelism** | GTB Bank 与 WB Bank 同时供数 | 减少访存等待 |
| **Tile-level parallelism** | A0-A7 多个 activation tile 并行参与计算 | 提升吞吐 |
| **Cluster-level parallelism** | Cluster #0-1 同时处理多组 MAC | 提高算力利用率 |
| **Codebook reuse parallelism** | 多个 A tile 复用同一 B tile | 降低 ReRAM 带宽压力 |

- **32×16 8b-MACs 的含义：**
  - **32×16** 表示该 cluster 内部 MAC 阵列规模。
  - **8b-MACs** 表示支持 INT8 activation/weight 乘加。
  - 在论文整体设定中：
    - TLM 使用 **W4A8**
    - DLM 使用 **W4A8 / BVQ effective 2bit/value**
    - 但计算时 codebook reconstructed weight 可进入 INT8 MAC pipeline。
  - 因此图中 **8b-MACs** 对应的是实际计算阵列的数据通路宽度。

- **该图想表达的关键设计思想：**
  - **不是简单地把 ReRAM 当作大容量存储器使用。**
  - 而是通过 **BVQ + Weight Buffer + Tile Fusion + MAC Cluster** 形成完整的数据复用路径。
  - 其目标是让 ReRAM 高带宽真正转化为计算吞吐，而不是被重复 codebook access 浪费。

- **与普通 VQ 加速方式相比的优势：**

| 方案 | 问题 | 本图方案的改进 |
|---|---|---|
| 普通 VQ | index buffer 和 decoder 开销大 | BVQ 使用 block-level codebook，解码更轻量 |
| 普通 codebook 读取 | 相同 CB entry 可能被重复访问 | TFTE 进行 tile fusion，只读取一次 |
| 普通 GEMM mapping | activation/weight tile 复用不足 | cluster 内部显式复用 B tile |
| 单纯 ReRAM 存储 | 带宽可能被低效访问浪费 | 通过 WB Bank 和 cluster mapping 提高有效带宽 |

- **性能意义：**
  - 图中结构服务于论文的第二个核心贡献：**RS-PNM with BVQ**。
  - 其直接收益包括：
    - **避免 Draft LLM weight external memory access**
    - **降低 DLM 解码延迟**
    - **减少 ReRAM redundant codebook access**
    - **提升 intra-layer parallelism**
    - **提升 ReRAM bandwidth utilization**
  - 论文中该部分带来的结果是：相比带 LRU 的 W4A8 speculative decoding，**RS-PNM + INT4 BVQ 实现 1.1× 到 1.46× speedup**。

- **总结：**
  - 这张图展示的是 **BVQ codebook tile 在 TFTE cluster 中的复用计算方式**。
  - 左侧 **GTB Bank** 提供 activation tiles，右侧 **WB Bank** 提供 codebook/weight tiles。
  - 中间通过 **Cluster #0-1, 32×16 8b-MACs** 执行多路并行乘加。
  - 其核心价值是：**让多个 activation tiles 共享相同 codebook tile，从而减少 ReRAM 访问、降低延迟、提高 DLM speculative decoding 的硬件效率**。

### f4d39f2876e6eb226b282f9701b8c76d6e5d82de20a6ca7509c7944bc336c449.jpg

![f4d39f2876e6eb226b282f9701b8c76d6e5d82de20a6ca7509c7944bc336c449.jpg](images/f4d39f2876e6eb226b282f9701b8c76d6e5d82de20a6ca7509c7944bc336c449.jpg)

- 这张图展示的是 **RS-PNM 中的 Tile Fusion Unit（TFU）机制**，核心目标是解决 **BVQ（Blockwise Vector Quantization）带来的 redundant Codebook ReRAM access**，通过 **token/activation tile fusion** 让相同 Codebook Entry 只访问一次，从而 **降低 ReRAM 读取延迟约 50%**。

- 图中整体数据流可以概括为：

| 模块 | 图中位置 | 功能 |
|---|---:|---|
| **ISA** | 左上 | 提供 Codebook index / 控制信息，指示哪些 tile 使用相同 CB entry |
| **GTB Bank #0-1** | 左侧 | 存放 token / activation tiles，如 A0、A1、A2、A3 |
| **INT8 Quantization** | 左中 | 对 activation 进行 INT8 量化，适配低比特计算 |
| **TFU #0-1** | 左侧核心 | 将共享同一 Codebook entry 的 activation tile 相加融合 |
| **WB Bank #0-1** | 中上 | 存放从 ReRAM 读取来的 Codebook block，如 B0、B1、B2、B3 |
| **Cluster #0-1** | 中下 | 执行 fused activation × codebook block 的矩阵乘计算 |
| **8MB Stacked ReRAM Die #0-3** | 右上 | 存储 DLM 的 BVQ Codebook，提供高带宽近存储读取 |
| **Ctrl. / TFU / Cluster array** | 右下 | 多个独立 TFU 与计算 Cluster 并行执行，实现 independent token fusion |

- 图中的关键思想是利用乘法分配律进行计算融合：

| 原始计算 | TFU 融合后 |
|---|---|
| **A0 × B0 + A1 × B0** | **（A0 + A1）× B0** |
| **A2 × B2 + A3 × B2** | **（A2 + A3）× B2** |
| **A4 × B3 + A5 × B3** | **（A4 + A5）× B3** |

- 这样做的直接收益是：如果多个 activation tile 对应同一个 **Codebook block Bx**，系统无需重复从 ReRAM 读取 Bx，而是先在 TFU 内部把 activation tile 融合，再对该 Codebook block 执行一次乘法。

- 图中标注的 **“Reduce 50% Latency”** 表明，在该示例中，TFU 通过减少重复 Codebook 读取和重复计算，使 Codebook 访问相关延迟降低约 **50%**。

- 图中标注的 **“No Redundant ReRAM Access”** 是该设计的核心优势。传统方式下，如果不同 tile 都引用同一个 Codebook entry，可能会产生多次 ReRAM read；而 TFU 会识别这些相同引用，并将它们融合为一次 Codebook 读取。

- 中间的 **WB Bank #0-1** 表示 Codebook block 会先从 stacked ReRAM 读入到 weight buffer，再送入计算 Cluster。TFU 的作用是在 Codebook 进入计算前尽量提升其复用率。

- 图中的 **Cluster #0-1** 标注为 **32×16 b-MACs**，说明每个计算 Cluster 由多个低比特 MAC 单元组成，适合执行 BVQ 后的 block-level 矩阵计算。

- 右侧的 **8MB Stacked ReRAM Die #0-3** 体现了该论文的 ReRAM-on-Logic stacking 架构：  
  - **DLM Codebook 存在 ReRAM 中**；  
  - 通过 face-to-face bumping interface 提供高带宽；  
  - Logic die 上的 TFU / Cluster 近距离读取并计算；  
  - 避免频繁访问外部 DRAM。

- 右下角的 **Ctrl. #0 / #1 / #15、TFU #0 / #1 / #15、Cluster #0 / #1 / #15** 表示该机制是多通道并行的。每个控制器对应一个 TFU 和一个计算 Cluster，可独立执行 fusion 与计算。

- 图中 **“Independent Token Fusion”** 表示不同 TFU 可以独立处理不同 token tile 或 block group，不需要全局同步，从而提高并行度并降低调度复杂度。

- 该图对应论文中的 **BVQ + RS-PNM 协同设计**：

| 问题 | 传统 VQ / BVQ 可能带来的开销 | 图中方案 |
|---|---|---|
| Codebook 存储 | DLM 权重压缩为 Codebook 后仍需频繁读取 | Codebook 存入 stacked ReRAM |
| Codebook 访问 | 相同 CB entry 可能被重复访问 | TFU 融合同 CB entry 的 tile |
| 带宽利用 | ReRAM 读带宽可能被重复访问浪费 | 减少冗余访问，提高有效带宽 |
| 计算效率 | 重复 MAC 造成延迟 | 使用 fused activation 降低 MAC 次数 |
| 并行性 | 多 tile 访问可能拥塞 | 多 TFU / Cluster 独立并行 |

- 该图的系统意义在于：**BVQ 负责压缩 DLM 权重，ReRAM 负责高密度存储 Codebook，TFU 负责消除 Codebook 访问冗余，Cluster 负责低比特计算**。四者共同降低 DLM 在 speculative decoding 中的延迟。

- 从算法角度看，TFU 不改变数学结果，只改变计算顺序：

| 层面 | 作用 |
|---|---|
| **数学等价性** | 利用加法与乘法分配律保持结果一致 |
| **访存优化** | 相同 Codebook block 只读一次 |
| **计算优化** | 多次乘法变成一次乘法加一次加法 |
| **硬件友好性** | activation 加法比 ReRAM 访问和 MAC 更便宜 |
| **能效收益** | 减少 ReRAM read 与 MAC 次数，降低能耗 |

- 这张图的重点不是展示 ReRAM 本身的存储结构，而是展示 **ReRAM 读取后的 Codebook 复用机制**。它解决的是 stacked ReRAM 带宽虽高但仍需避免无效访问的问题。

- 总结来看，该图说明：**TFU 是 RS-PNM 架构中连接 BVQ 压缩算法与 ReRAM 硬件带宽的关键模块**。它通过 **Codebook-aware token tile fusion**，在不损失精度的前提下减少 ReRAM 访问、降低延迟，并提高 DLM 推理阶段的吞吐与能效。

### Figure 31.1.4: ReRAM-stacked processing-near-memory (RS-PNM) architecture with blockwise vector quantization (BVQ) to avoid draft LLM external memory access (EMA).

![3b0e66f5354f2e35897d0d77f0d4a63bb57d425d98a22069e68b01a57a98d1b7.jpg](images/3b0e66f5354f2e35897d0d77f0d4a63bb57d425d98a22069e68b01a57a98d1b7.jpg)

- 这张图展示的是论文中的 **RS-PNM（ReRAM-stacked processing-near-memory）架构**，核心目标是解决 **Draft LLM 在 speculative decoding 中反复访问外部权重存储的 EMA（External Memory Access）瓶颈**。  
- 图的重点不是单纯“把 ReRAM 接上去”，而是把 **DLM 权重压缩、存储、读取、重建、计算** 整体协同设计，形成一条面向解码阶段的高带宽近存计算链路。  
- 这张图与左侧“Issue: Redundant Codebook ReRAM Access”问题直接对应：传统 VQ / codebook 方案在解码时会出现 **重复读取同一 codebook**、访问粒度太细、索引/解码开销大等问题；RS-PNM 用 **BVQ（Blockwise Vector Quantization）+ stacked ReRAM** 来把这类开销压下去。

- 图中整体可以分成两层：  

| 层级 | 主要模块 | 作用 |
|---|---|---|
| **Logic die** | MCU、top controller、ISA buffer、weight buffer、token buffer、EMAC、inter-chip transceiver、LRU、RS-PNM 相关控制 | 负责任务调度、数据搬运、推理控制、量化与解码协同 |
| **ReRAM dies** | 4 个 stacked ReRAM die、CFU、RLI、TFTE、NLPU | 负责高密度 codebook 存储、快速读取、权重重建、张量计算 |

- 从结构上看，这是一种 **ReRAM-on-logic face-to-face stacking** 架构。  
- **4 个 ReRAM dies** 叠在 logic die 上，通过 **2048 个 face-to-face bumps** 提供并行读出能力。  
- 这种结构的价值在于：  
  - **更高带宽**：图中给出 **25.6 GB/s @ 100 MHz**。  
  - **更大容量**：总计 **8 MB memory capacity**。  
  - **更短数据路径**：codebook 不再从远端 DRAM 反复搬运，而是直接从 stacked ReRAM 近端读取。  
  - **更适合 DLM 权重访问模式**：因为 DLM 的权重访问呈现“重复、块状、局部热度高”的特点，正适合在近存端做压缩存储与重建。

- 图中逻辑 die 的模块分工很清楚，体现了“控制面”和“数据面”分离：  

| 模块 | 作用 | 设计意义 |
|---|---|---|
| **Top controller / MCU** | 系统级控制、codebook 管理、配置下发 | 统一协调 SD 流程 |
| **ISA buffer** | 缓存指令流 | 降低控制开销 |
| **Weight buffer** | 缓存部分权重或重建后的数据 | 缓冲 ReRAM 读出结果 |
| **Global token buffer** | 缓存 token / intermediate activations | 支撑解码流水 |
| **EMAC** | External Memory Access Controller | 管理外部访存和数据流 |
| **LRU** | 给 TLM 做 outlier-free rotation quantization | 保证 TLM 低比特量化精度 |
| **Inter-chip transceiver** | 多芯片协同通信 | 支持 4-chip 系统扩展 |
| **RS-PNM** | 近存计算执行单元 | 完成 DLM codebook 读取与计算 |

- 图中 RS-PNM 的内部由四个关键单元组成：  

| 单元 | 缩写 | 功能 |
|---|---|---|
| **Codebook Fetcher Unit** | **CFU** | 触发并组织 ReRAM 中 codebook 的读取 |
| **ReRAM Load Interface** | **RLI** | 从 stacked ReRAM 取数据并搬运到逻辑侧 |
| **Tile-Fused Tensor Engine** | **TFTE** | 对共享同一 codebook 的 token tile 做融合计算，减少重复访问 |
| **Non-Linear Processing Unit** | **NLPU** | 处理非线性操作与相关后处理 |

- 这张图最关键的创新点是 **BVQ（Blockwise Vector Quantization）**。  
- 它不是传统 VQ 那种“单个向量一个码本索引”的粗粒度方案，而是：  
  - 把 DLM 权重按 **block** 切分；  
  - 在 block 级别学习 **codebook（CB）**；  
  - 用 **INT4 QAT + Gumbel softmax reparameterization** 学习 block index；  
  - 最终只需一个相对轻量的 **ISA decoder** 来恢复 codebook。  
- 这样做的直接收益是：  
  - **显著减少 weight EMA**；  
  - **降低索引缓存和多端口 decoder 的面积开销**；  
  - 更适合 ReRAM 的高密度存储方式。

- 图里还专门强调了 **vertical CB mapping**。  
- 原因是如果 codebook 水平映射，受限于频率和 bank width，会产生 **数据拥塞**。  
- 采用 vertical mapping 后：  
  - 更容易对齐 ReRAM bank 宽度；  
  - 提高带宽利用率；  
  - 减少控制复杂度。  
- 但 vertical mapping 会带来一个副作用：**同一个 codebook 可能被多个 token tile 重复访问**，这就是图左边“Redundant Codebook ReRAM Access”要解决的问题。  
- 为此，图中引入 **TFU / tile fusion** 思想：  
  - 把共享同一 CB entry 的 token tiles 融合；  
  - 让 CB **只读一次**；  
  - 再把它广播/复用到多个 tile 计算中。  
- 这一步是本图性能提升的核心之一，因为它直接把“重复读 ReRAM”的问题改成“单次读取、多次复用”。

- 图中的数据流可以按顺序理解为：  

| 流程阶段 | 数据路径 | 作用 |
|---|---|---|
| **1. 代码本存储** | MCU 将 DLM CB 写入 stacked ReRAM | 完成离线/初始化压缩部署 |
| **2. 读取触发** | CFU 触发 ReRAM controller 和 RLI | 进入在线推理阶段 |
| **3. codebook 搬运** | RLI 从 ReRAM 读取 CB 到 weight buffer | 实现近存读出 |
| **4. 时钟整形** | RLI 使用 **200 MHz double clock rate**，并经 FIFO 跨时钟域 | 提高稳定性与传输可靠性 |
| **5. 计算重建** | TFTE 将 token tiles 与 CB 融合 | 避免重复 CB 读取 |
| **6. 输出处理** | NLPU 处理非线性或后处理 | 完整完成一层/一个 block 的推理 |

- 图中对比了两类数据映射思路：  
  - **Horizontal mapping**：更容易引发 congestion。  
  - **Vertical mapping**：更适合提升带宽利用率，但要处理重复访问。  
- 作者的解决策略不是否定 vertical mapping，而是用 **TFU + tile fusion** 去消除它的副作用。  
- 这说明该设计是典型的 **“存储布局 + 计算调度 + 数据复用”协同优化**。

- 从系统层面看，RS-PNM 的目标非常明确：  
  - 不是追求单点 TOPS 最大化；  
  - 而是把 speculative decoding 中最耗时的 **DLM 权重搬运** 压缩到最低；  
  - 用 stacked ReRAM 的高带宽与高密度优势，把 DLM 从“频繁访存模型”变成“近存重建模型”。  
- 这也是为什么它能在论文里宣称相对 W4A8 SD 进一步实现 **1.1× 到 1.46× speedup**。

- 这张图的技术意义可以概括为三点：  

| 维度 | 贡献 |
|---|---|
| **存储** | 用 stacked ReRAM 承担 DLM codebook 的高密度存储 |
| **访问** | 用 BVQ 和 vertical mapping 降低 EMA 和带宽压力 |
| **执行** | 用 TFTE / tile fusion 消除重复 codebook 访问，提升吞吐 |

- 如果从硬件架构研究角度评价，这张图最大的亮点是 **把 speculative decoding 的“draft LLM 小模型优势”真正落到硬件上**。  
- 传统方案往往只在算法层说“DLM 更小”，但在边缘芯片上，DLM 依然可能因为 **权重外存访问频繁** 而成为瓶颈。  
- RS-PNM 的价值就在于：  
  - **把 DLM 的压缩权重放进高密度 ReRAM**；  
  - **把解码时的权重重建搬到近存侧**；  
  - **把重复 codebook 访问变成 tile 级复用**。  
- 所以这张图本质上是在说明：**DLM 不是只要“更小”就够了，还必须“更近”**。

- 结合论文全文，这张图与另外两项技术形成闭环：  
  - **LRU** 解决 TLM outlier-free quantization；  
  - **RS-PNM + BVQ** 解决 DLM EMA；  
  - **APSD** 解决 speculative decoding 中长短 draft 长度的动态权衡。  
- 也就是说，这张图展示的是整篇工作的中间核心：**把 draft 侧的权重访问问题系统性地硬件化解决**。  

- 如果进一步压缩成一句话，这张图表达的是：  
  - **通过 ReRAM-on-logic stacking，把 DLM codebook 放到近存层；再通过 BVQ、vertical mapping 和 TFTE/tile fusion，消除重复 codebook 访问，从而显著降低 speculative decoding 的 EMA 开销。**

### 93453bef2b1f9c1c07b8fb1ba2f2fb0eb982a9c971f32097381b09d5f5365ca7.jpg

![93453bef2b1f9c1c07b8fb1ba2f2fb0eb982a9c971f32097381b09d5f5365ca7.jpg](images/93453bef2b1f9c1c07b8fb1ba2f2fb0eb982a9c971f32097381b09d5f5365ca7.jpg)

- **图片核心主题**：该图展示了 **Codebook-Interleaved Intra-Layer Mapping，CILM**，即**码本交织式层内映射**。它用于在多芯片、多 ReRAM die 的系统中，将 DLM 的 **BVQ codebook** 更均匀地分布到不同 ReRAM/accelerator 上，从而提升 **ReRAM bandwidth utilization**，避免某些 ReRAM 空闲、某些 ReRAM 拥塞。

- **图中整体结构可分为四个部分**：

| 区域 | 内容 | 作用 |
|---|---|---|
| 左上 | **Full BW Util. when loading each block** | 说明每个 DLM block 加载时都能充分利用 ReRAM 带宽 |
| 左下红框 | **Codebook-Interleaved Mapping** | 展示一个 block 内不同层、不同投影矩阵的 codebook 被交织映射 |
| 中部 | **ReRAM #0~#3 + Accelerator #0~#3** | 展示 4 个 ReRAM/accelerator 并行加载和计算 |
| 右侧 | **DLM in this work** | 展示 DLM block 结构：Attention + FFN |

- **CILM 的基本目标**：

| 问题 | CILM 的解决方式 |
|---|---|
| 单个 DLM block 内不同权重矩阵大小不均 | 将 codebook 按 block 内层级进行交织分配 |
| ReRAM 带宽利用不均 | 将 codebook 均匀映射到 **ReRAM #0~#3** |
| parallel draft-and-verify 中 DLM 可能等待数据 | 保证每个 block 加载时 4 个 ReRAM 并行工作 |
| 多 chip / 多 accelerator 资源竞争 | 通过 intra-layer mapping 平衡各 accelerator 负载 |

- **左上区域含义：Full BW Util. when loading each block**

| 图中元素 | 含义 |
|---|---|
| **Block #11 Codebooks** | DLM 第 11 个 block 的全部 codebook |
| **Block #0 Codebooks** | DLM 第 0 个 block 的全部 codebook |
| 多个 block 纵向排列 | 表示 DLM 每一层/block 都经过类似的 codebook 映射 |
| **Full BW Util.** | 表示加载任意 block 的 codebook 时，都能使用完整 ReRAM 带宽 |

- **左下红框：Codebook-Interleaved Mapping 的细节**

| Codebook 类型 | 对应 Transformer 权重 |
|---|---|
| **Wgate CB#11** | FFN 中 gate projection 的 codebook |
| **Wup CB#11** | FFN 中 up projection 的 codebook |
| **Wup CB#3** | 来自另一位置/分片的 up projection codebook |
| **Wq/k/v/o CB#0** | Attention 中 query/key/value/output projection 的 codebook |
| **Wdown CB#2** | FFN 中 down projection 的 codebook |
| **Wq/k/v/o CB#2** | Attention projection 的另一组 codebook |

- **关键点**：图中不是将一个矩阵的所有 codebook 连续放在同一个 ReRAM 中，而是将 **Attention 和 FFN 中不同 projection 的 codebook 交错排列**，使得每个 ReRAM 在加载一个 DLM block 时都有数据可读。

- **中部区域：4 个 ReRAM 与 4 个 Accelerator 的映射**

| ReRAM | 存储内容示例 | 对应计算单元 |
|---|---|---|
| **ReRAM #0** | Wq/k/v/o、Wup/gate、Wdown 等 CB | **Accelerator #0** |
| **ReRAM #1** | Wq/k/v/o、Wup/gate、Wdown 等 CB | **Accelerator #1** |
| **ReRAM #2** | Wq/k/v/o、Wup/gate、Wdown 等 CB | **Accelerator #2** |
| **ReRAM #3** | Wq/k/v/o、Wup/gate、Wdown 等 CB | **Accelerator #3** |

- **图中箭头 “Allocate CBs evenly to ReRAM #0~3” 的含义**：

| 设计动作 | 效果 |
|---|---|
| 将 codebook 均匀分配到 4 个 ReRAM | 避免单一 ReRAM 访问热点 |
| 每个 ReRAM 都保存不同 CB 分片 | 提高并行读取效率 |
| 每个 accelerator 对应一个 ReRAM 数据源 | 减少跨单元搬运 |
| loading each block 时同时读取 | 实现 **full bandwidth utilization** |

- **右侧 DLM block 结构说明**

| 模块 | 权重矩阵 |
|---|---|
| **Attention** | **Wq / Wk / Wv / Wo** |
| **FFN** | **Wup / Wgate / Wdown** |

- **图中标注的维度信息**：

| 权重类型 | 图中维度示例 | 说明 |
|---|---|---|
| **Attention heads** | **12 Heads** | DLM 使用 12 个 attention heads |
| **Wq/k/v/o** | **768 × 768** | Attention projection 矩阵规模 |
| **Wup/gate** | **3072 × 768** | FFN expansion projection |
| **Wdown** | **768 × 3072** | FFN contraction projection |

- **这些维度揭示了一个重要问题**：FFN 中 **Wup / Wgate / Wdown** 的参数量通常显著大于 Attention projection，因此如果采用朴素映射，FFN codebook 可能集中压到部分 ReRAM，造成带宽不均。CILM 通过交织布局解决这一点。

- **与 BVQ 的关系**：

| 技术 | 作用 |
|---|---|
| **BVQ, Blockwise Vector Quantization** | 将 DLM 权重压缩为 block-level codebook 和 index |
| **CILM** | 决定这些 codebook 在 ReRAM dies 中如何物理映射 |
| **RS-PNM** | 从 ReRAM 近存加载 codebook 并在 logic die 中重构/计算 |
| **TFU / TFTE** | 对共享同一 CB entry 的 token tile 进行融合，减少重复访问 |

- **CILM 不是单纯的数据压缩方法**，而是一个**存储布局与调度优化方法**。它依赖 BVQ 产生的 codebook，但核心贡献在于让 codebook 在多 ReRAM 通道中均衡分布。

- **为什么需要 CILM**：

| 若无 CILM | 使用 CILM 后 |
|---|---|
| 某些 ReRAM 存储大量当前 block 需要的 CB | CB 均匀分布到 ReRAM #0~#3 |
| 当前 block 加载时只有部分 ReRAM 忙碌 | 4 个 ReRAM 并行读取 |
| ReRAM 带宽利用率下降 | 带宽利用率接近满载 |
| DLM drafting 延迟增加 | DLM drafting 更快 |
| APSD 并行 draft-and-verify 容易受阻 | APSD 资源利用率提高 |

- **图中 “Full BW Util. when loading each block” 是 CILM 的关键评价目标**：每加载一个 DLM block，系统都希望 **ReRAM #0~#3 同时输出 codebook 数据**，而不是只依赖某一两个 ReRAM。

- **与论文中 APSD 的联系**：

| 模块 | CILM 的作用 |
|---|---|
| **APSD** | 需要 DLM 和 TLM 尽可能并行运行 |
| **WDOS** | 调度 compute / ReRAM load / EMAC / inter-chip transceiver |
| **CILM** | 确保 ReRAM load 队列不会因带宽不均成为瓶颈 |
| **RS-PNM** | 利用堆叠 ReRAM 的高带宽加载 DLM codebook |

- **因此，CILM 是 APSD 能够进行 intra-chip parallel draft-and-verify 的底层支撑之一**。如果 DLM codebook 加载不均衡，APSD 即使有并行调度，也会被 ReRAM 访问瓶颈限制。

- **从硬件角度看，CILM 的价值在于**：

| 硬件资源 | 优化效果 |
|---|---|
| **4 ReRAM dies / banks** | 并行读，避免空闲 |
| **2048 data bumps** | 更充分利用 face-to-face stacking 带宽 |
| **Accelerator #0~#3** | 负载更均衡 |
| **ReRAM load interface, RLI** | 数据流更连续 |
| **asynchronous FIFO groups** | 减少突发拥塞 |
| **WDOS ReRAM load queue** | 更易与 compute queue 重叠 |

- **从系统性能角度看，CILM 的直接收益**：

| 性能指标 | 影响 |
|---|---|
| **DLM latency** | 降低 |
| **ReRAM bandwidth utilization** | 提高 |
| **draft token generation speed** | 提高 |
| **parallel draft-and-verify efficiency** | 提高 |
| **APSD speedup** | 增强 |
| **DLM idle time** | 减少 |

- **图中设计隐含了一个关键判断**：在 speculative decoding 中，虽然 TLM 是大模型，但 DLM 的延迟同样不能忽视。若 DLM 因 codebook 加载受限而变慢，就会削弱 speculative decoding 的收益。CILM 通过提升 DLM codebook loading 效率，避免 DLM 成为新的瓶颈。

- **CILM 与传统 horizontal mapping 的差异**：

| 映射方式 | 特点 | 问题 |
|---|---|---|
| **Horizontal mapping** | 一个矩阵或连续 codebook 顺序映射 | 容易导致部分 ReRAM 访问集中 |
| **Vertical mapping** | 按 ReRAM bank 宽度进行垂直分布 | 可提升带宽，但可能有重复 CB access |
| **CILM** | 在 intra-layer 范围内交织 codebook | 兼顾带宽均衡与 block 加载效率 |

- **图中 “Codebook-Interleaved” 的核心并不是随机打散，而是结构化交织**：它根据 DLM block 中 Attention 和 FFN 的权重矩阵组成，将不同 CB 分片映射到不同 ReRAM，使每个 block 的加载请求天然分布均衡。

- **与论文整体贡献的对应关系**：

| 论文技术 | 对应挑战 | 图中体现 |
|---|---|---|
| **LRU** | TLM W4A8 量化中的 activation outliers | 不在本图重点展示 |
| **BVQ + RS-PNM** | DLM 权重 EMA 过大 | codebook 存在 ReRAM 中 |
| **CILM** | ReRAM 带宽利用不均 | 本图核心 |
| **APSD + WDOS** | 长 DL 下 DLM token rejection 与资源竞争 | CILM 为并行调度提供带宽基础 |

- **总结性理解**：该图说明，本文不仅把 DLM 权重通过 **BVQ** 压缩进 ReRAM，还进一步通过 **CILM** 设计了细粒度的 codebook 物理布局，使每个 DLM block 在加载时都能均匀访问 **ReRAM #0~#3**，从而实现高带宽利用、低 DLM 延迟，并支撑 **APSD** 中的高效 intra-chip parallel draft-and-verify。

### e91dc4a6d3187e74220e2b1c432d25c936e3984be1155107aa9c012d7313da76.jpg

![e91dc4a6d3187e74220e2b1c432d25c936e3984be1155107aa9c012d7313da76.jpg](images/e91dc4a6d3187e74220e2b1c432d25c936e3984be1155107aa9c012d7313da76.jpg)

- **图片核心含义**：该图展示了在同一 LLM 解码任务中，逐步加入 **LRU、RS-PNM、WDOS** 三项技术后，相比 **Baseline** 在 **Throughput、Energy、Avg. DRAM EMA** 三个指标上的增益。

- **图例说明**：

| 颜色 | 配置 | 含义 |
|---|---|---|
| 灰色 | **Baseline** | 原始 BF16 speculative decoding 基线 |
| 蓝色 | **+LRU** | 加入 **Local Rotation Unit**，支持 outlier-free W4A8 TLM quantization |
| 绿色 | **+RS-PNM** | 加入 **ReRAM-stacked Processing-Near-Memory** 与 **BVQ**，降低 DLM EMA |
| 红色 | **+WDOS** | 加入 **Workload-Decoupled Out-of-Order Scheduler**，支撑 APSD 并提升并行利用率 |

- **三项指标的数值对比**：

| 配置 | Throughput Token/s | Energy mJ/Token | Avg. DRAM EMA GB/Token |
|---|---:|---:|---:|
| **Baseline** | **2.54** | **574.5** | **4.33** |
| **+LRU** | **10.37** | **181.8** | **1.09** |
| **+RS-PNM** | **12.72** | **171.9** | **0.91** |
| **+WDOS** | **14.08** | **151.6** | **0.87** |

- **Throughput 分析**：

| 阶段 | Throughput 提升 | 主要原因 |
|---|---:|---|
| **Baseline → +LRU** | **约 3.93×** | LRU 支持 TLM 从 BF16 降到 **W4A8**，显著减少 TLM 权重访问和计算开销 |
| **+LRU → +RS-PNM** | **约 1.24×** | RS-PNM 将 DLM codebook 放入 stacked ReRAM，减少 DLM 外部访存 |
| **+RS-PNM → +WDOS** | **约 1.11×** | WDOS 提高 APSD 中 DLM drafting 与 TLM verification 的资源并行度 |
| **Baseline → +WDOS** | **约 5.54×** | 三项技术叠加后，解码吞吐从 **2.54 Token/s** 提升到 **14.08 Token/s** |

- **关键观察**：**LRU 是吞吐提升的最大贡献来源**。从 2.54 到 10.37 Token/s，占总提升的大部分，说明该任务中主要瓶颈首先来自 **TLM weight EMA**，而 LRU 通过 outlier-free low-bit quantization 有效缓解了这一瓶颈。

- **Energy 分析**：

| 阶段 | Energy 变化 | 节能倍数/效果 |
|---|---:|---|
| **Baseline → +LRU** | 574.5 → 181.8 mJ/Token | **3.16× energy saving** |
| **Baseline → +RS-PNM** | 574.5 → 171.9 mJ/Token | **3.34× energy saving** |
| **Baseline → +WDOS** | 574.5 → 151.6 mJ/Token | **3.79× energy saving** |

- **关键观察**：能耗下降同样主要来自 **LRU**。原因是 TLM 参数规模远大于 DLM，TLM 的 BF16 权重访问和计算能耗很高；采用 **W4A8 quantization** 后，数据搬移与 MAC 能耗同时下降。

- **RS-PNM 的能耗贡献**：**+RS-PNM** 将能耗从 181.8 降到 171.9 mJ/Token，改善幅度较温和，但它解决的是 **DLM weight EMA** 问题，并通过 ReRAM high-density storage 和 BVQ codebook 访问降低外部 DRAM 依赖。

- **WDOS 的能耗贡献**：**+WDOS** 将能耗进一步降到 151.6 mJ/Token，说明 APSD + out-of-order scheduling 不只是提升吞吐，也减少了无效 DLM drafting、资源空转和 rejected token 带来的浪费。

- **Avg. DRAM EMA 分析**：

| 阶段 | Avg. DRAM EMA | 相对 Baseline 降低倍数 |
|---|---:|---:|
| **Baseline** | **4.33 GB/Token** | 1× |
| **+LRU** | **1.09 GB/Token** | **3.97×** |
| **+RS-PNM** | **0.91 GB/Token** | **4.76×** |
| **+WDOS** | **0.87 GB/Token** | **4.98×** |

- **关键观察**：DRAM EMA 从 **4.33 GB/Token** 降至 **0.87 GB/Token**，减少约 **79.9%**。这直接解释了吞吐提升和能耗下降，因为 autoregressive decoding 中最大的系统瓶颈通常不是算力，而是 **weight external memory access**。

- **各模块作用拆解**：

| 技术 | 主要优化对象 | 对应瓶颈 | 图中体现 |
|---|---|---|---|
| **LRU** | TLM | Activation outlier 导致低比特量化精度下降 | 最大幅度提升 throughput、降低 energy 和 DRAM EMA |
| **RS-PNM + BVQ** | DLM | Draft model 权重无法完全片上缓存，导致 EMA | 进一步降低 DRAM EMA，提升吞吐 |
| **WDOS + APSD** | SD 调度流程 | Draft-and-verify 并行度不足、DLM idle、rejected token 浪费 | 进一步提升吞吐并降低能耗 |

- **LRU 的意义**：通过 **decomposed FWHT local rotation** 近似 global rotation，去除 activation outlier，使 TLM 可以可靠运行在 **W4A8**。图中 **Baseline → +LRU** 的突增说明，低比特 TLM 是整个系统加速的基础。

- **RS-PNM 的意义**：DLM 虽小，但在 speculative decoding 中会频繁执行 drafting，若权重仍从 DRAM 加载，会形成额外瓶颈。**RS-PNM** 利用 stacked ReRAM 存储 BVQ codebook，通过 near-memory reconstruction 降低 DLM 的 DRAM EMA。

- **WDOS 的意义**：单纯硬件加速不足以完全释放 speculative decoding 的潜力。**WDOS** 将 workloads 解耦为 compute、ReRAM load、EMAC、inter-chip transceiver 等队列，并进行 dependency-aware out-of-order scheduling，从而提高 APSD 中的资源利用率。

- **综合结论**：该图清晰表明，论文提出的三项技术形成递进式优化链条：  
  **LRU 解决 TLM 低比特量化与访存主瓶颈，RS-PNM 解决 DLM 权重访存瓶颈，WDOS 解决 speculative decoding 并行调度瓶颈**。最终实现 **14.08 Token/s、151.6 mJ/Token、0.87 GB/Token DRAM EMA**，相比 Baseline 获得显著系统级收益。

### 8d98fc348c2192be50b13ed830308a24ca0388f5e6f7b35120799051f30bd216.jpg

![8d98fc348c2192be50b13ed830308a24ca0388f5e6f7b35120799051f30bd216.jpg](images/8d98fc348c2192be50b13ed830308a24ca0388f5e6f7b35120799051f30bd216.jpg)

- **图片主题**：该图展示了 **Workload-Decoupled Out-of-Order Scheduler，WDOS** 的架构与调度机制，用于支持 **Adaptive Parallel Speculative Decoding，APSD** 中的 **intra-chip parallel draft-and-verify**，目标是在同一芯片内同时执行 **DLM drafting** 与 **TLM verification/computation**，并提高 **compute、ReRAM、DRAM、inter-chip transceiver** 等资源利用率。

- **核心思想**：
  - 将 APSD 中复杂的推理流程拆解为 **4 类主工作负载**。
  - 每类工作负载对应一个独立的 **Instruction Queue**。
  - 队列之间通过 **dependency marker** 与 **synchronous counter matrix** 进行依赖同步。
  - 队列内部保持 **sequential issue**，队列之间允许 **out-of-order scheduling**。
  - 这样可以避免 DLM 与 TLM 并行执行时对片上资源、ReRAM 带宽、DRAM 带宽的竞争。

- **上半部分：APSD 被简化为 3 类主要执行场景**：

| 场景 | 图中含义 | 主要数据路径 | 关键硬件资源 | 作用 |
|---|---|---|---|---|
| **Load KV or Weight** | 从 DRAM 读取 KV cache 或 TLM weight | DRAM → EMAC → Weight Buffer / Global Token Buffer → Inter-Chip Transceiver | **EMAC、DRAM、Weight Buffer、Global Token Buffer、Inter-Chip Transceiver** | 支持 TLM 相关权重或 KV 数据加载 |
| **Load KV or Weight + DLM Codebooks** | 同时加载 DRAM 数据与 ReRAM 中的 DLM codebooks | DRAM → EMAC；ReRAM → DLM Codebooks → Weight Buffer；Weight Buffer → TFTE | **DRAM、EMAC、ReRAM、TFTE、Weight Buffer** | 支持 DLM draft 计算，利用 ReRAM 存储压缩后的 codebooks |
| **Store KV** | 将生成的 KV cache 写回 DRAM | Global Token Buffer / Weight Buffer → EMAC → DRAM | **EMAC、DRAM、Global Token Buffer、Weight Buffer** | 保存 TLM 或 DLM 推理过程中的 KV cache |

- **图中上半部分的关键观察**：
  - **DRAM** 主要服务于 **TLM weight、KV cache** 的外部访存。
  - **ReRAM** 主要存储 **DLM Codebooks**，用于 BVQ 压缩权重的近存加载。
  - **TFTE** 负责利用从 ReRAM 读取的 codebook 执行 DLM 计算。
  - **LRU** 与 **NLPU** 在中间和右侧场景中部分激活，用于 TLM/DLM computation，尤其是 TLM 的 outlier-free quantization。
  - 图中灰色模块表示当前阶段未使用或弱使用资源，彩色模块表示活跃资源。
  - WDOS 的目的就是让这些资源在不同 workload 之间尽可能错峰或并行使用。

- **中间部分：4 个并行 Instruction Queues**：

| Queue 编号 | 名称 | 对应工作负载 | 典型指令示例 | 主要依赖 |
|---|---|---|---|---|
| **Queue #0** | Transceiver | 片间通信 | Attention input、Block #0 Attention input、Block #1 Attention input | 依赖计算或访存结果 |
| **Queue #1** | Compute | TLM/DLM 计算 | FFN input、Attention computation | 依赖输入 token、weight、KV |
| **Queue #2** | ReRAM Load | DLM codebook 读取 | Block #0 CBs、Block #1 CBs | 依赖 ReRAM 带宽与 codebook index |
| **Queue #3** | EMAC | DRAM 访存 | Block #0 KV load、TLM tile weight load、Block #0 KV store | 依赖 DRAM 与 EMAC 可用性 |

- **该设计的关键点**：
  - **Queue #0 Transceiver**：负责跨芯片数据传输，例如 token tile、attention input 等。
  - **Queue #1 Compute**：负责核心计算任务，包括 attention、FFN、TLM/DLM compute。
  - **Queue #2 ReRAM Load**：专门负责从 stacked ReRAM 读取 DLM codebooks。
  - **Queue #3 EMAC**：专门负责 DRAM 访问，包括 TLM weight load、KV load/store。
  - 通过拆分为 4 个队列，WDOS 将原本耦合的 APSD workload 解构为可并行调度的资源流。

- **下半部分左侧：队列间乱序、队列内顺序调度机制**：
  - 图中标注 **“Inter-Queue Out-of-Order, Intra-Queue Sequential”**。
  - 含义是：
    - **同一个 Queue 内部指令按顺序执行**，避免复杂的队列内乱序硬件。
    - **不同 Queue 之间可以乱序发射**，只要依赖满足即可。
  - 例如：
    - Queue #2 可以提前加载 **Block #0 CBs**。
    - Queue #3 可以同时加载 **Block #0 KV Load** 或 **TLM Tile Weight Load**。
    - Queue #1 在所需 input、weight、KV ready 后执行 compute。
    - Queue #0 在计算结果或输入准备好后执行 transceiver 操作。

- **图中红色圆圈数字的含义**：
  - 红色数字表示不同队列之间的依赖关系或同步阶段。
  - 例如：
    - **0**：初始阶段，可能对应 attention input 或 DLM codebook 读取准备。
    - **1**：第一组依赖满足后，compute 或 load 继续执行。
    - **2**：中间阶段，TLM projection 或 tile weight 相关任务被触发。
    - **3**：后续 Block #1 或 KV store 相关任务进入执行。
  - 这些编号不是简单时间戳，而是用于展示 **跨队列依赖传播**。

- **右下部分：Intra-Queue Decoder 与同步矩阵**：
  - 每个队列前端有一个 **Intra-Queue Decoder**。
  - Decoder 从指令中解析：
    - **Queue ID**
    - **Init Par. Mark**
    - **3-bit Dau. Mark**
    - 其他 dependency marker

| 字段 | 可能含义 | 作用 |
|---|---|---|
| **Queue ID** | 当前指令所属队列编号 | 判断指令属于 Transceiver、Compute、ReRAM Load 或 EMAC |
| **Init Par. Mark** | Parent dependency marker | 表示当前指令依赖哪些父队列 |
| **3-bit Dau. Mark** | Daughter dependency marker | 表示当前指令完成后需要通知哪些子队列 |
| **Instruction body** | 实际操作内容 | 如 load CB、load KV、compute、transfer |

- **Synchronous Counter Matrix 的作用**：
  - 图中显示一个 **4×4 synchronous counter matrix**。
  - 行可以理解为 **daughter queue**，列可以理解为 **parent queue**，用于记录队列间依赖是否满足。
  - 当某条指令完成后：
    - 更新对应的 daughter queue counter。
    - 通知依赖它的后续 queue。
  - 当某条指令准备发射时：
    - 检查其 parent queue counter 是否满足。
    - 如果依赖满足，则 issue instruction。
    - 如果依赖不满足，则继续等待。

- **右侧同步流程可概括为**：

| 步骤 | 操作 | 目的 |
|---|---|---|
| **1** | Check If Par. Queue Cnt. > 0 | 检查父队列依赖是否满足 |
| **2** | Update Parent Queue Cnt. -- | 当前指令消耗一个父依赖 token |
| **3** | Issue Instruction | 发射当前队列指令 |
| **4** | Update Daughter Queue Cnt. ++ | 指令完成后通知子队列依赖已满足 |

- **WDOS 解决的问题**：
  - 传统 speculative decoding 中，DLM drafting 与 TLM verification 容易出现：
    - **DLM idle**
    - **TLM waiting**
    - **ReRAM bandwidth under-utilization**
    - **DRAM bandwidth contention**
    - **compute unit stall**
  - WDOS 通过工作负载解耦与依赖感知调度，使：
    - DLM codebook loading 可与 TLM weight/KV loading 重叠。
    - DLM compute 可与部分 TLM memory operation 重叠。
    - ReRAM 与 DRAM 可以被不同 workload 同时利用。
    - Transceiver、TFTE、EMAC 等模块减少空闲。

- **与 APSD 的关系**：
  - APSD 在算法层面动态切换：
    - **short DL non-parallel drafting**
    - **long DL parallel draft-and-verify**
  - WDOS 在硬件层面支撑这种切换：
    - 当进入 parallel draft-and-verify 时，WDOS 将 TLM 与 DLM 操作拆成不同 queue 并行推进。
    - 当 draft token 被拒绝，需要回退到 non-parallel drafting 时，WDOS 可以通过依赖标记快速调整执行流。
  - 因此，WDOS 是 APSD 从算法变成高效硬件执行的关键调度器。

- **图中体现的资源利用优化**：

| 资源 | 没有 WDOS 时的问题 | WDOS 的改进 |
|---|---|---|
| **ReRAM** | DLM 不工作时 ReRAM 空闲 | Queue #2 独立调度，提前加载 DLM CBs |
| **DRAM** | TLM weight/KV load 与其他任务冲突 | Queue #3 独立管理 EMAC/DRAM |
| **TFTE** | 等待 weight 或 codebook | 与 ReRAM load 依赖同步，减少 stall |
| **Inter-Chip Transceiver** | 通信与计算耦合导致等待 | Queue #0 独立传输 |
| **Compute** | 等待 input、KV、weight ready | Queue #1 依赖满足即执行 |
| **Global Token Buffer / Weight Buffer** | 数据到达时间不匹配 | 通过同步矩阵协调生产者与消费者 |

- **图中设计的硬件复杂度取舍**：
  - 该调度器没有采用完全乱序执行，因为完全乱序会带来较大的硬件开销。
  - 它采用的是 **inter-queue out-of-order + intra-queue sequential** 的折中方案。
  - 好处是：
    - 调度硬件简单。
    - 依赖关系清晰。
    - 适合边缘 LLM accelerator。
    - 能显著提高并行度。
  - 代价是：
    - 队列内部仍可能受顺序约束。
    - 调度效果依赖编译器或 ISA 对 instruction stream 的合理划分。

- **结合论文结果，该图对应的性能贡献**：
  - WDOS 支撑 APSD 的片内并行 draft-and-verify。
  - 相比仅使用 RS-PNM 的方案，APSD + WDOS 可带来：
    - **1.1× 到 1.29× speedup**
    - **10% 到 14% rejected DLM latency reduction**
  - 这说明 WDOS 不只是控制逻辑，而是直接减少 speculative decoding 中被拒绝 draft token 造成的无效开销。

- **总体评价**：
  - 该图展示的是一个面向 speculative decoding 的专用调度微架构。
  - 其价值在于将 APSD 的不规则控制流转化为可硬件执行的 **4-queue dependency-driven scheduling problem**。
  - 通过 **Queue decoupling、dependency marker、synchronous counter matrix、out-of-order inter-queue issue**，WDOS 同时提升了 **compute utilization、ReRAM bandwidth utilization、DRAM access overlap**。
  - 在该 ReRAM-on-Logic LLM accelerator 中，WDOS 是连接 **APSD algorithm** 与 **RS-PNM hardware** 的关键控制模块。

### 689be0a96b8fba5d2fe8e5b216718f0705478276414c1ed3c7098595dd0aa93e.jpg

![689be0a96b8fba5d2fe8e5b216718f0705478276414c1ed3c7098595dd0aa93e.jpg](images/689be0a96b8fba5d2fe8e5b216718f0705478276414c1ed3c7098595dd0aa93e.jpg)

- **图片类型与位置**
  - 该图是论文 Figure 31.1.7 中的 **logic die 显微照片 / die photo**。
  - 展示的是该 LLM accelerator 的 **55nm logic die floorplan**，即逻辑芯片版图实物照片。
  - 该 logic die 与上方 **4 个 ReRAM dies** 通过 **face-to-face bumping stacking** 连接，构成 ReRAM-on-Logic 堆叠式架构。

- **芯片尺寸信息**

| 项目 | 数值 |
|---|---:|
| **Die 宽度** | **6.9984 mm** |
| **Die 高度** | **7.9992 mm** |
| **估算面积** | **约 55.98 mm²** |
| **工艺节点** | **55nm** |
| **主要功能** | LLM speculative decoding accelerator logic die |

- **整体观察**
  - 芯片呈近似矩形，宽约 **7.0 mm**，高约 **8.0 mm**。
  - 版图被划分为多个明确的功能区域，包括：
    - **WDOS**
    - **TX/RX**
    - **MCU**
    - **PLLs**
    - **Weight Buffer**
    - **EMAC**
    - **TFTE + CFU + RLI**
    - **NLPU**
    - **LRU**
    - **Global Token Buffer**
  - 从面积占比看，**Global Token Buffer**、**Weight Buffer**、以及 **TFTE + CFU + RLI** 是主要面积消耗模块。
  - 该布局反映出芯片的核心瓶颈并非单纯计算，而是围绕 **LLM decoding 中的权重访问、token 缓冲、ReRAM 读出与 speculative decoding 调度** 进行优化。

- **主要模块分布**

| 位置 | 模块 | 功能分析 |
|---|---|---|
| 左上 | **WDOS** | Workload-Decoupled Out-of-Order Scheduler，用于 APSD 中的乱序调度与依赖同步 |
| 上中 | **TX/RX** | Inter-chip transceiver，用于多芯片系统中的芯片间通信 |
| 上中右 | **MCU** | 微控制器，负责系统控制、配置、ReRAM 初始化/管理等 |
| 右上 | **PLLs** | 时钟产生模块，为 logic die 和相关接口提供时钟 |
| 左侧大块 | **Weight Buffer** | 权重缓存，主要缓冲从 DRAM/ReRAM 读取或重构后的权重/Codebook 数据 |
| 左下 | **EMAC** | External Memory Access Controller，管理外部存储访问，尤其是 TLM 权重 EMA |
| 中央大块 | **TFTE + CFU + RLI** | RS-PNM 核心，包括 Tile-Fused Tensor Engine、Codebook Fetcher Unit、ReRAM Load Interface |
| 右中 | **NLPU** | Non-Linear Processing Unit，执行 softmax、activation、normalization 等非线性操作 |
| 右下中 | **LRU** | Local Rotation Unit，用于 FWHT-based local rotation，支持 outlier-free W4A8 TLM quantization |
| 下方大块 | **Global Token Buffer** | 全局 token 缓冲区，存储中间 token features、KV/activation 相关数据或 tile 数据 |

- **面积占比解读**
  - **Global Token Buffer** 占据底部大面积区域，是全芯片最大的单一区域之一。
    - 这说明 LLM decoding 中 token feature、中间激活、并行 speculative decoding 数据流对片上缓存需求很高。
  - **Weight Buffer** 位于左侧，面积也较大。
    - 用于缓冲 TLM/DLM 相关权重数据、BVQ codebook 重构结果或从外部存储加载的数据。
  - **TFTE + CFU + RLI** 位于芯片中央偏上，是计算与 ReRAM 数据加载的核心区域。
    - 该区域承担 **DLM codebook fetch、weight reconstruction、tile fusion、tensor compute** 等功能。
  - **LRU** 面积较小，位于右侧中下部。
    - 这与论文声称的 **LRU 相比 global rotation 节省 92.7% area** 一致。
    - 说明 decomposed FWHT local rotation 的硬件代价较低。
  - **WDOS** 面积较小但位置靠近顶层控制和通信模块。
    - 体现其作为调度控制单元，而非大规模计算单元。

- **与论文架构的对应关系**

| 论文核心技术 | 图中对应模块 | 作用 |
|---|---|---|
| **LRU: Local Rotation Unit** | **LRU** | 支持 decomposed FWHT，消除 activation outliers，实现可靠 W4A8 TLM quantization |
| **RS-PNM** | **TFTE + CFU + RLI** | 通过 ReRAM-stacked process-near-memory 加速 DLM codebook 读取与权重重构 |
| **BVQ: Blockwise Vector Quantization** | **CFU + RLI + Weight Buffer + TFTE** | 从 ReRAM 读取 codebook，并通过 tile fusion 降低重复访问 |
| **APSD** | **WDOS + TX/RX + TFTE + EMAC** | 实现 adaptive parallel speculative decoding |
| **外部权重访问控制** | **EMAC** | 管理 TLM 权重的 DRAM access |
| **多芯片扩展** | **TX/RX** | 支持 4-chip system 中的通信 |
| **Token 数据缓存** | **Global Token Buffer** | 支持 draft/verify 并行过程中的 token feature 存储 |

- **关键架构含义**
  - 该 die photo 直观体现出芯片是一个 **memory-centric LLM decoding accelerator**。
  - 大量面积用于 **Weight Buffer** 与 **Global Token Buffer**，说明系统重点是缓解 autoregressive decoding 中的存储访问瓶颈。
  - 中央的 **TFTE + CFU + RLI** 是 ReRAM-on-Logic 架构的关键接口与计算融合区域。
  - 右侧的 **LRU** 面积较小，说明 outlier-free quantization 的旋转操作被设计为轻量级硬件，而不是完整 global FWHT 阵列。
  - 左上角的 **WDOS** 面积有限，但对 APSD 性能贡献显著，负责提高 intra-chip parallel draft-and-verify 的资源利用率。

- **模块功能细节分析**
  - **WDOS**
    - 全称为 **Workload-Decoupled Out-of-Order Scheduler**。
    - 对应论文中的 4 个并行 instruction queues：
      - **inter-chip transceiver queue**
      - **compute queue**
      - **ReRAM load queue**
      - **EMAC queue**
    - 其作用是解耦 APSD 工作负载，减少资源竞争。
    - 虽然面积小，但直接影响 speculative decoding 的并行效率。

  - **TX/RX**
    - 用于芯片间传输。
    - 在 4-chip system 中，多个芯片需要共同完成 LLM 推理。
    - TX/RX 支持 token、partial result、控制信息或同步信号传输。
    - 对 APSD 的 multi-chip / intra-chip 协同均有意义。

  - **MCU**
    - 控制系统初始化、配置、指令流管理。
    - 负责与 ReRAM 编程/加载流程相关的控制。
    - 可能通过 SPI 或片上控制路径管理 DLM codebook 写入 stacked ReRAM。

  - **PLLs**
    - 为不同模块生成所需时钟。
    - 论文中 logic die 工作在 **63.5–285MHz**，ReRAM die 工作在 **100MHz**。
    - PLLs 支持多时钟域系统。

  - **Weight Buffer**
    - 面积较大，说明权重缓存是重要资源。
    - 用于暂存：
      - TLM quantized weights
      - DLM reconstructed weights
      - BVQ codebook entries
      - tile-fused weight blocks
    - 与 **EMAC** 和 **RLI** 都存在密切数据流关系。

  - **EMAC**
    - 即 **External Memory Access Controller**。
    - 主要负责外部 DRAM 权重访问。
    - 在 SD 中，TLM 仍然是主要 EMA 来源，因此 EMAC 对整体吞吐和能耗有关键影响。
    - 图中 EMAC 紧邻 Weight Buffer，布局合理，有利于降低数据搬移开销。

  - **TFTE + CFU + RLI**
    - 是 RS-PNM 的核心组合模块。
    - **CFU: Codebook Fetcher Unit**
      - 从 ReRAM 中取回 BVQ codebook。
    - **RLI: ReRAM Load Interface**
      - 负责 ReRAM 到 logic die 的高速读接口。
      - 论文中 ReRAM stacking interface 提供 **25.6GB/s** 带宽。
    - **TFTE: Tile-Fused Tensor Engine**
      - 执行 tile-level tensor compute。
      - 支持将共享同一 codebook entry 的 token tiles 融合，减少重复 ReRAM access。
    - 该模块位于芯片中央，有利于连接 Weight Buffer、Global Token Buffer、LRU 和 NLPU。

  - **NLPU**
    - 负责非线性算子。
    - 可能包括：
      - activation function
      - normalization
      - softmax
      - element-wise operation
    - 位于右侧，靠近 compute core 和 LRU，利于 transformer layer 数据流。

  - **LRU**
    - 即 **Local Rotation Unit**。
    - 用于 TLM 的 outlier-free low-bit quantization。
    - 通过 decomposed FWHT 近似 global rotation。
    - 支持 W4A8 TLM，降低权重 EMA。
    - 图中 LRU 面积明显小于大缓存和 TFTE 区域，支撑论文中“相比 global rotation 节省大量面积”的论点。

  - **Global Token Buffer**
    - 位于芯片底部，占据大面积。
    - 用于存储 speculative decoding 中的 token features、中间激活、draft tokens、verification tokens 等。
    - APSD 需要同时处理 DLM drafting 与 TLM verification，因此对 token buffer 的容量和带宽要求更高。
    - 该模块面积大，说明芯片针对 decoding 阶段的数据复用进行了强化。

- **数据流推测**
  - **TLM 路径**
    - 外部 DRAM 权重通过 **EMAC** 进入 **Weight Buffer**。
    - token feature 从 **Global Token Buffer** 送入 **LRU**。
    - LRU 执行 local rotation，降低 activation outlier。
    - 旋转后的 activation 进入 **TFTE** 进行 W4A8 tensor compute。
    - 非线性部分交给 **NLPU**。
    - 结果写回 **Global Token Buffer**。

  - **DLM 路径**
    - DLM 的 BVQ codebook 存储在 stacked **ReRAM dies** 中。
    - codebook 通过 **RLI** 进入 logic die。
    - **CFU** 控制 codebook fetch。
    - **TFTE** 根据 block index 进行 weight reconstruction / tile fusion。
    - 计算结果写入 **Global Token Buffer**。
    - APSD 中，DLM drafting 与 TLM verification 通过 **WDOS** 调度并行执行。

- **与性能结果的关系**
  - 图中的硬件布局对应论文报告的关键性能：
    - **14.08–135.69 Token/s**
    - **4.46–7.17× speedup over BF16 SD**
    - **3.74–4.85× energy saving**
    - **25.6GB/s ReRAM bandwidth**
    - **3.43MB SRAM + 8MB stacked ReRAM**
  - 大容量 **Global Token Buffer** 和 **Weight Buffer** 支撑片上数据复用。
  - **TFTE + CFU + RLI** 支撑高带宽 ReRAM codebook loading。
  - **LRU** 支撑低比特 TLM without severe accuracy degradation。
  - **WDOS** 支撑 APSD 的高资源利用率。

- **版图设计特点**
  - **存储靠边、计算居中**
    - Weight Buffer 和 EMAC 位于左侧。
    - Global Token Buffer 位于底部。
    - TFTE 位于中央，方便访问多个 buffer。
  - **控制与时钟靠顶部**
    - WDOS、TX/RX、MCU、PLLs 位于顶部，符合控制逻辑和 I/O 规划习惯。
  - **专用功能单元靠右**
    - NLPU 和 LRU 位于右侧，作为 TFTE 的辅助处理路径。
  - **ReRAM 接口相关模块居中**
    - RLI 与 CFU 被放置在中央大计算区域中，说明 ReRAM 数据加载与计算紧耦合。

- **该图传达的核心信息**
  - 该芯片不是传统只堆 MAC 的 AI accelerator，而是围绕 **speculative decoding + ReRAM bandwidth + quantization + scheduling** 协同设计。
  - Die photo 中面积分配体现出：
    - **片上 SRAM buffer 是 decoding 的核心资源**
    - **ReRAM stacking 用于缓解 DLM weight EMA**
    - **LRU 用很小面积换取 W4A8 TLM 可用性**
    - **WDOS 用控制复杂度换取 APSD 并行效率**
  - 整体设计目标是提升 edge LLM decoding 的 **tokens/s** 和 **mJ/token**，而不是单纯追求峰值 TOPS。

### 9803b827d487e67bd8eb38ea75c69f970a8e00c01f95d136cb5184057fd071e4.jpg

![9803b827d487e67bd8eb38ea75c69f970a8e00c01f95d136cb5184057fd071e4.jpg](images/9803b827d487e67bd8eb38ea75c69f970a8e00c01f95d136cb5184057fd071e4.jpg)

- **图片主体内容**
  - 该图展示的是论文中提出的 **ReRAM-on-Logic face-to-face stacking** 芯片实物照片。
  - 图中可见一个较大的 **Logic Die** 作为底层逻辑芯片，其上方堆叠了一个较小的 **ReRAM Die #0-3**。
  - 标注表明，该封装/堆叠结构中包含 **4 个 ReRAM dies**，即 **ReRAM Die #0-3**，共同堆叠在同一块 Logic Die 上方。
  - 这张图对应 Figure 31.1.7 中的芯片实物照片部分，用于证明该工作并非纯架构仿真，而是完成了 **55nm ReRAM-on-Logic stacking prototype** 的实际制造与封装验证。

- **可见结构分析**

| 图中区域 | 视觉特征 | 技术含义 |
|---|---|---|
| **Logic Die** | 底部大面积金黄色/棕色芯片基底，边缘可见封装或划片轮廓 | 承载计算逻辑、SRAM、控制器、LRU、RS-PNM、WDOS 等主要数字逻辑模块 |
| **ReRAM Die #0-3** | 中央偏上的银蓝色矩形区域，覆盖在 Logic Die 上 | 表示堆叠的 ReRAM 存储芯片，用于提供高密度、近距离、低功耗的 DLM codebook 存储 |
| **Face-to-face stacking interface** | ReRAM die 与 Logic die 直接贴合，未见传统长引线连接 | 对应论文中的 **bumping-based face-to-face ReRAM-on-logic stacking technology** |
| **芯片边界与封装区域** | Logic Die 外围可见规则边框 | 说明该图为实物 die photo，而非版图示意图 |

- **与论文架构的对应关系**
  - 图片中的 **Logic Die** 对应整体架构中的计算与调度核心，包含：
    - **Top controller**
    - **MCU**
    - **64KB ISA buffer**
    - **1MB weight buffer**
    - **2MB global token buffer**
    - **EMAC**
    - **LRU**
    - **WDOS**
    - **RS-PNM**
    - **TFTE / CFU / RLI / NLPU**
  - 图片中的 **ReRAM Die #0-3** 对应论文提出的片上堆叠存储层：
    - 总容量为 **8MB ReRAM**
    - 通过 **2048 data bumps** 提供并行读通道
    - 在 **100MHz** 下实现 **25.6GB/s** ReRAM bandwidth
    - 主要用于存储 **DLM blockwise codebooks**
  - 该实物堆叠结构是 **RS-PNM** 能够避免 Draft LLM 频繁 external memory access 的硬件基础。

- **关键规格对应**

| 项目 | 数值/描述 |
|---|---|
| **工艺节点** | 55nm |
| **堆叠方式** | Bumping-based face-to-face ReRAM-on-Logic stacking |
| **底层芯片** | Logic Die |
| **上层芯片** | 4 个 ReRAM dies |
| **Logic Die 面积** | **55.98 mm²** |
| **ReRAM Die 总面积** | **22.21 mm²**，即 5.553 × 4 mm² |
| **ReRAM 总容量** | **8MB** |
| **Data bumps 数量** | **2048** |
| **Control bumps 数量** | **864** |
| **总 bump 数量** | **2912** |
| **Bump diameter** | **40μm** |
| **ReRAM 工作频率** | **100MHz** |
| **ReRAM 电压** | **1.1V** |
| **ReRAM 带宽** | **25.6GB/s** |
| **单个 ReRAM die 读功耗** | **49.54mW** |

- **图片体现的核心设计意图**
  - **降低 Draft LLM 权重访问延迟**
    - 传统边缘 LLM accelerator 受限于片上 SRAM 容量，无法完整缓存 DLM weights。
    - 该设计通过在 Logic Die 上方直接堆叠 ReRAM dies，将 DLM 的压缩 codebooks 存入 ReRAM。
    - 这样可以减少或避免 DLM 权重从外部 DRAM 反复搬运。
  - **提高近存储带宽**
    - Face-to-face stacking 缩短信号传输距离。
    - 通过大量 bumps 并行读出 ReRAM 数据。
    - 实现 **25.6GB/s** 的片上 ReRAM bandwidth，远高于低功耗外部接口的典型带宽。
  - **支持 RS-PNM**
    - 图中的 ReRAM die 并不是独立存储器，而是与 Logic Die 上的 **CFU、RLI、TFTE** 等模块协同工作。
    - ReRAM 存储 **BVQ codebooks**，Logic Die 负责 codebook fetching、weight reconstruction 和 tensor computation。
  - **服务 Speculative Decoding**
    - TLM 仍主要依赖外部 DRAM 访问大模型权重。
    - DLM 则通过 ReRAM 堆叠和 BVQ 压缩尽量留在片上/近片上。
    - 这种 TLM/DLM 分工是本文提升 SD decoding throughput 的关键。

- **从图片可推断的封装与集成特点**
  - **异质集成**
    - Logic Die 与 ReRAM Die 功能不同，属于典型 **memory-on-logic heterogeneous integration**。
  - **垂直互连**
    - ReRAM die 直接位于 Logic Die 上方，暗示两者通过微凸点进行垂直连接，而非传统 PCB 级互连。
  - **短互连路径**
    - 与外部 DRAM 相比，ReRAM 到 Logic 的数据路径显著缩短，有利于降低访问能耗和延迟。
  - **面积换带宽**
    - 上层 ReRAM die 占据 Logic Die 中央区域，但换来了高带宽、高密度的近存储能力。
  - **适合边缘 LLM decoding**
    - Decoding 阶段 batch size 通常较小，计算阵列利用率低，瓶颈主要是 weight EMA。
    - 该结构通过堆叠 ReRAM 缓解 memory-bound decoding 问题。

- **与论文三个核心创新的关系**

| 创新点 | 图片中的对应体现 | 作用 |
|---|---|---|
| **LRU** | 位于 Logic Die 内部，图片不可直接分辨 | 支持 TLM outlier-free W4A8 quantization |
| **RS-PNM + BVQ** | **ReRAM Die #0-3 堆叠在 Logic Die 上** | 存储 DLM codebooks，减少 DLM EMA |
| **APSD + WDOS** | 位于 Logic Die 内部，图片不可直接分辨 | 调度 TLM/DLM 并行 draft-and-verify，提高资源利用率 |

- **性能意义**
  - 该 ReRAM-on-Logic 实物结构支撑论文报告的整体性能：
    - **14.08 to 135.69 token/s**
    - 相比 BF16 SD baseline 实现 **4.46 to 7.17× speedup**
    - 实现 **3.74 to 4.85× energy saving**
  - 对于 4-chip system：
    - ReRAM 容量扩展到 **32MB**
    - ReRAM bandwidth 扩展到 **102.4GB/s**
    - 足以存储所有 DLM codebooks
  - 在 LLaMA2-7B + LLaMA-160M 场景下：
    - Decoding throughput 为 **17.82 token/s**
    - Energy consumption 为 **123.41 mJ/token**

- **该图的论文证明价值**
  - **证明芯片已完成流片与堆叠封装**
    - 不是单纯架构仿真或 FPGA 原型。
  - **证明 ReRAM-on-Logic 堆叠可用于 LLM accelerator**
    - 展示了 ReRAM dies 与 Logic Die 的实际物理集成。
  - **支撑高带宽近存储 claims**
    - 图中堆叠结构与文中 **2048 data bumps / 25.6GB/s bandwidth** 直接对应。
  - **支撑边缘端 LLM decoding 优化路线**
    - 通过近存储减少 DLM EMA，是本文区别于纯数字 CIM 或传统 SRAM accelerator 的关键。

- **总结**
  - 这张图片展示了本文芯片的核心物理实现：**4 个 ReRAM dies face-to-face 堆叠在 55nm Logic Die 上**。
  - 它是实现 **RS-PNM、BVQ codebook storage、高带宽 DLM weight reconstruction** 的硬件基础。
  - 从系统角度看，该堆叠结构直接服务于 **speculative decoding**，通过减少 Draft LLM 的外部存储访问，提高 decoding throughput 并降低 energy/token。
  - 图中最关键的信息是：**本文不是仅依靠算法压缩或调度优化，而是通过 ReRAM-on-Logic 3D-like stacking 把存储带宽和容量物理上拉近到计算核心旁边。**

### 32977dd54a68f280b87c0b1422c89b24b547899b091aabdc546f5574c5347b7f.jpg

![32977dd54a68f280b87c0b1422c89b24b547899b091aabdc546f5574c5347b7f.jpg](images/32977dd54a68f280b87c0b1422c89b24b547899b091aabdc546f5574c5347b7f.jpg)

- **图片类型**：该图是 **Cross-Sectional SEM Image**，即芯片堆叠结构的**横截面扫描电子显微镜图像**，用于展示本文提出的 **ReRAM-on-Logic face-to-face stacking** 实物互连形貌。

- **图中主要结构可分为三部分**：

| 区域 | 图中位置 | 含义 | 作用 |
|---|---:|---|---|
| **ReRAM Die** | 上方深灰区域 | 阻变存储器芯片层 | 提供高密度片上/近片上权重存储 |
| **Logic Die** | 下方深灰区域 | 逻辑计算芯片层 | 集成 TFTE、LRU、WDOS、控制器、SRAM 等计算与调度模块 |
| **Face-to-Face Bumps** | 中间一排亮色柱状结构 | ReRAM die 与 logic die 之间的微凸点互连 | 提供高带宽、短距离、低功耗垂直数据通路 |

- **最关键的信息是中间的亮色微凸点阵列**。这些凸点对应论文中提到的 **bumping-based face-to-face ReRAM-on-logic stacking interface**，是实现 **ReRAM die** 与 **logic die** 垂直互连的物理基础。

- 图中可以看到 **ReRAM Die 位于 Logic Die 正上方**，二者之间通过多个规则排列的 bump 连接，说明该芯片采用的是**垂直堆叠架构**，而不是传统的片外 DRAM 或二维封装互连。

- **图像标尺为 200 μm**，说明该 SEM 图展示的是局部截面区域。结合论文参数，整颗芯片采用 **2048 data bumps + 864 control bumps，共 2912 bumps**，其中数据 bump 用于实现 ReRAM 到 logic 的并行读出。

- **互连结构观察**：

| 观察项 | 图像表现 | 技术含义 |
|---|---|---|
| **Bump 排列** | 中间亮色柱状结构横向分布较均匀 | 表明堆叠界面具备规则化并行互连 |
| **上下 die 对准** | ReRAM Die 与 Logic Die 垂直贴合 | 支持 face-to-face stacking |
| **互连距离** | ReRAM 与 logic 间距很短 | 降低 I/O 能耗与延迟 |
| **截面完整性** | bump 与上下芯片接触清晰 | 说明封装/键合质量较稳定 |
| **无明显空洞或断裂** | 图中未见显著 void/crack | 有利于高可靠性数据传输 |

- 该图直接支撑论文中的核心硬件贡献：**使用 ReRAM-on-Logic stacking 提供高带宽近存储访问**。论文指出 4 个 ReRAM dies 通过 face-to-face bumps 堆叠在 logic die 上，可提供 **8 MB ReRAM 容量**和 **25.6 GB/s 带宽**。

- 从系统架构角度看，这种堆叠方式主要解决的是 **Draft LLM 权重访问瓶颈**。传统 edge LLM accelerator 受限于片上 SRAM 容量，DLM 权重仍需频繁访问外部存储，导致 EMA latency 较高。该图中的堆叠互连让 DLM 的 BVQ codebook 可以放入 ReRAM，并通过短距离高并行 bump 直接传输到 logic die。

- **与论文中的 RS-PNM 关系非常直接**：

| 论文模块 | 与该 SEM 图的关系 |
|---|---|
| **ReRAM dies** | 图中上方 ReRAM Die，对应 codebook 存储介质 |
| **Logic die** | 图中下方 Logic Die，对应 RS-PNM、TFTE、CFU、RLI 等逻辑 |
| **RLI, ReRAM Load Interface** | 依赖该垂直 bump interface 接收 ReRAM 读出数据 |
| **CFU, Codebook Fetcher Unit** | 通过该堆叠通道触发并获取 BVQ codebooks |
| **TFTE, Tile-Fused Tensor Engine** | 使用从 ReRAM 获取的 codebook 重构/计算 DLM 权重 |

- 该图展示的 **face-to-face stacking** 相比传统封装或片外 DRAM 访问有明显优势：

| 对比项 | 传统片外 DRAM/封装 | ReRAM-on-Logic stacking |
|---|---|---|
| 数据路径 | 长 | **短** |
| I/O 功耗 | 高 | **低** |
| 带宽密度 | 受封装引脚限制 | **受益于大量 micro-bumps** |
| 延迟 | 较高 | **较低** |
| 存储靠近计算程度 | 低 | **高** |
| 适合任务 | 大带宽片外访问 | **DLM codebook 近存储读取** |

- 该 SEM 图也说明论文并非仅提出算法或架构仿真，而是具有**实测芯片与真实三维互连工艺验证**。这对 ISSCC/VLSI 类芯片论文尤其关键，因为它证明了 **ReRAM-on-logic stacking interface** 已经实际制造并可用于系统测量。

- 从图像中可推断，堆叠结构采用的是 **face-to-face bonding**，因为 ReRAM Die 与 Logic Die 的有源面通过 bump 直接相对连接。这种方式可以让存储阵列输出端与逻辑接收端之间距离更短，有利于实现论文中的 **100 MHz ReRAM read** 和 **25.6 GB/s stacked bandwidth**。

- 该图与论文性能结果之间的因果链条为：

| 物理实现 | 架构效果 | 系统收益 |
|---|---|---|
| **ReRAM-on-Logic bump stacking** | 提供高带宽 ReRAM 读取 | 减少 DLM EMA |
| **2048 data bumps** | 并行数据传输 | 提升 ReRAM bandwidth |
| **短垂直互连** | 降低访问延迟和 I/O 能耗 | 提升 token/s 与 energy efficiency |
| **8 MB ReRAM 容量** | 存储 BVQ codebooks | 避免频繁外部存储访问 |
| **与 RS-PNM 协同** | codebook 近存储加载与 tile fusion | 实现 1.1-to-1.46× speedup over W4A8 SD with LRU |

- 该图的论文意义可以概括为：**它验证了本文加速器的存储-计算垂直集成基础，是实现 RS-PNM、BVQ codebook 高带宽读取以及 speculative decoding 加速的关键物理证据**。

- 需要注意的是，该 SEM 图本身只展示了**局部截面结构**，不能单独反映 ReRAM 电学特性、良率、保持时间或 endurance；这些需要结合论文中其他图，例如 **ReRAM resistance distribution curve**、die photo 和系统测量结果共同判断。

- 综合来看，该图片的核心价值是展示：**ReRAM Die 与 Logic Die 通过规则微凸点实现紧密垂直互连，使 DLM codebook 可在堆叠 ReRAM 中以高带宽方式被 logic die 访问，从而支撑本文 14.08-to-135.69 token/s 的 LLM decoding throughput 和 3.74-to-4.85× energy saving。**

### bf0656fcae4cef71f65aea5b8e1301a29199f539f11d48f423f8063d907ffb1f.jpg

![bf0656fcae4cef71f65aea5b8e1301a29199f539f11d48f423f8063d907ffb1f.jpg](images/bf0656fcae4cef71f65aea5b8e1301a29199f539f11d48f423f8063d907ffb1f.jpg)

- **图片对象**：该图展示的是论文 Figure 31.1.7 中的 **ReRAM die 显微照片 / die photo**，对应堆叠在 logic die 上方的 **ReRAM 存储芯片**。

- **核心视觉信息如下**：

| 项目 | 图中信息 | 分析 |
|---|---:|---|
| 芯片宽度 | **2.4934 mm** | 图顶部标注，表示单颗 ReRAM die 的横向尺寸 |
| 芯片高度 | **2.2270 mm** | 图左侧标注，表示单颗 ReRAM die 的纵向尺寸 |
| 估算面积 | **约 5.55 mm²** | 2.4934 × 2.2270 ≈ **5.55 mm²**，与论文表格中 **5.553 mm² × 4 ReRAM dies** 一致 |
| 主要区域 | **ReRAM Core** | 占据 die 的绝大部分面积，用于存储压缩后的 DLM codebook / CB |
| 底部区域 | **ReRAM Controller** | 面积较小，负责 ReRAM 访问控制、读出时序、接口管理等 |
| 工艺 | **55nm** | 与 logic die 同工艺节点，支持 ReRAM-on-Logic stacking |
| 单 die 容量 | 推测约 **2MB** | 论文说明 4 个 ReRAM dies 总容量为 **8MB**，因此单 die 约 2MB |
| 堆叠方式 | **face-to-face bumping** | 通过微凸点与 logic die 垂直互连 |

- **版图结构分析**：

  - 图中上方大面积矩形区域标注为 **ReRAM Core**，说明该 die 的面积主要用于非易失存储阵列。
  - 底部窄条区域标注为 **ReRAM Controller**，其面积明显小于存储阵列，体现出该芯片设计目标是 **最大化存储密度**。
  - ReRAM Controller 被放置在 die 的一侧边缘，有利于：
    - **简化阵列读写控制布线**
    - **靠近 bump / interface 区域进行数据输出**
    - **降低控制逻辑对存储阵列面积的侵占**
  - ReRAM Core 内部呈现规则阵列纹理，说明其由大量重复 memory bank / sub-array 构成，符合 ReRAM 高密度存储阵列特征。

- **与论文系统架构的关系**：

| 系统组件 | 图中对应 | 作用 |
|---|---|---|
| **ReRAM die** | 当前图片 | 存储 DLM 的压缩 codebook |
| **ReRAM Core** | 大面积阵列 | 保存 BVQ 压缩后的 DLM weights / CBs |
| **ReRAM Controller** | 底部控制区 | 管理 ReRAM 读访问 |
| **Logic die** | 图中未显示 | 通过 face-to-face bumps 与 ReRAM die 连接 |
| **RLI / CFU** | 图中未显示，位于 logic die | 从 ReRAM 中加载 CB 到 weight buffer |
| **TFTE / TFU** | 图中未显示，位于 logic die | 重构权重并执行 tile fusion，减少重复 CB 访问 |

- **面积与容量意义**：

  - 单颗 ReRAM die 面积约为 **5.55 mm²**。
  - 论文中使用 **4 颗 ReRAM dies** 堆叠在 logic die 上，总 ReRAM 面积约：
  
| 数量 | 单 die 面积 | 总面积 |
|---:|---:|---:|
| 1 | **5.55 mm²** | **5.55 mm²** |
| 4 | **5.55 mm²** | **22.21 mm²** |

  - 这与论文表格中的 **22.21 mm² ReRAM die area** 对应。
  - 4 个 ReRAM dies 提供 **8MB 容量** 和 **25.6GB/s 带宽**。
  - 在 4-chip 系统中，ReRAM 容量扩展到 **32MB**，带宽扩展到 **102.4GB/s**。

- **架构价值分析**：

  - 该 ReRAM die 的主要作用不是直接做 compute-in-memory，而是作为 **high-density stacked memory**，为 Draft LLM 提供高带宽近存储访问。
  - 论文中的 DLM 经过 **BVQ, Blockwise Vector Quantization** 压缩后，权重不以完整矩阵形式存储，而是以 **codebook entries** 形式保存在 ReRAM Core 中。
  - 这样可以显著减少 DLM 权重对外部 DRAM 的访问，即降低 **EMA, External Memory Access**。
  - ReRAM die 与 logic die face-to-face stacking 后，通过大量 bumps 实现高并行读出，相比传统片外 DRAM 访问具有：
    - **更高局部带宽**
    - **更低访问能耗**
    - **更短互连距离**
    - **更适合边缘 LLM decoding**

- **从图片可推断的设计取向**：

  - **存储阵列优先**：ReRAM Core 占比极高，说明设计重点是容量密度，而非复杂外围计算。
  - **控制逻辑精简**：ReRAM Controller 面积较小，说明大量复杂调度、解码、tile fusion 和计算逻辑放在 logic die 中完成。
  - **适合垂直堆叠**：die 尺寸较小，便于多个 ReRAM dies 与大面积 logic die 进行 face-to-face integration。
  - **面向带宽扩展**：多个 ReRAM dies 并行读出，通过 2048 data bumps 提供 **25.6GB/s @ 100MHz** 的读取带宽。

- **与论文性能结果的关联**：

| 设计点 | 图片体现 | 性能贡献 |
|---|---|---|
| **大面积 ReRAM Core** | 存储阵列占主要面积 | 存储 DLM BVQ codebooks |
| **小型 Controller** | 底部窄条控制区 | 支持 ReRAM 读取和接口控制 |
| **多 die 堆叠** | 单 die 可复制扩展 | 4 dies 达到 8MB / 25.6GB/s |
| **高带宽近存储** | ReRAM-on-Logic stacking | 减少 DLM EMA |
| **配合 BVQ** | 存 CB 而非完整权重 | 降低存储容量需求 |
| **配合 TFU** | 避免重复 CB 读取 | 降低 ReRAM 访问延迟 |

- **关键结论**：

  - 该图片展示的是论文中 **ReRAM-on-Logic stacked LLM accelerator** 的基础存储单元。
  - 单颗 ReRAM die 尺寸约为 **2.4934mm × 2.2270mm**，面积约 **5.55mm²**。
  - 其内部主要由 **ReRAM Core** 构成，底部集成 **ReRAM Controller**。
  - 该 die 是实现 **RS-PNM, ReRAM-stacked Processing-Near-Memory** 架构的关键硬件基础。
  - 它通过高密度 ReRAM 存储 **BVQ-compressed DLM codebooks**，帮助系统避免 Draft LLM 的频繁外部存储访问。
  - 因此，该图虽只是 die photo，但直接支撑了论文中的核心贡献之一：**利用 ReRAM 堆叠存储显著降低 LLM speculative decoding 中 DLM 的 EMA bottleneck**。

### 8663f9c5d3f9e8ea39bbb770bef7ff9c1e67f4572a092748d5c166fdd30ed823.jpg

![8663f9c5d3f9e8ea39bbb770bef7ff9c1e67f4572a092748d5c166fdd30ed823.jpg](images/8663f9c5d3f9e8ea39bbb770bef7ff9c1e67f4572a092748d5c166fdd30ed823.jpg)

- **图片对象**：该图展示了论文中所实现的 **4-chip System** 实物测试平台，对应 Figure 31.1.7 中的系统级硬件照片。

- **核心内容概览**：

| 观察项 | 图中表现 | 技术含义 |
|---|---|---|
| 系统形态 | 一块大型 PCB 测试板 | 用于验证多芯片 LLM accelerator 系统 |
| 芯片数量 | 右上角插图标注 **4-chip System** | 表明系统采用 **4 个加速器芯片并行工作** |
| 散热结构 | 左侧中央有大型圆形风扇/散热器 | 芯片运行时功耗较高，需要主动散热 |
| 接口资源 | 底部和侧边分布多个连接器、USB/排针/电源接口 | 支持供电、配置、数据通信和调试 |
| 系统用途 | 原型板/评估板 | 用于测量吞吐率、能效、ReRAM 带宽和多芯片扩展能力 |

- **图像结构分析**：
  - 左侧主体区域是一块完整的 **evaluation board / prototype PCB**。
  - PCB 上布满电源管理、电容、电感、连接器和测试点。
  - 中央偏左位置有一个明显的 **主动散热风扇**，覆盖在主要高功耗器件上方。
  - 右上角有一个放大插图，标注 **“4-chip System”**，展示了 4 个芯片模组/封装区域。
  - 插图中可以看到多个黑色芯片封装或散热盖，说明系统并非单芯片演示，而是多芯片级联平台。

- **与论文系统架构的对应关系**：

| 论文描述 | 图片对应 |
|---|---|
| 单芯片包含 **logic die + 4 ReRAM dies** | 图片中每个芯片封装可能对应一个 ReRAM-on-logic stacked accelerator |
| 4-chip system | 右上角插图明确标注 **4-chip System** |
| ReRAM 容量从单芯片 **8MB** 扩展到系统级 **32MB** | 4 个芯片并行后容量线性扩展 |
| ReRAM 带宽从单芯片 **25.6GB/s** 扩展到 **102.4GB/s** | 多芯片并行提升片上/近存储访问带宽 |
| 用于 LLM decoding 测试 | 图片平台用于测量 token/s 与 mJ/token |

- **硬件系统意义**：
  - 该图片证明论文不是纯架构仿真，而是基于真实硅片和 PCB 的 **silicon measurement platform**。
  - 4 芯片系统用于验证：
    - **多芯片并行 speculative decoding**；
    - **ReRAM-stacked PNM** 的带宽扩展；
    - **DLM codebook 全量驻留 ReRAM** 的可行性；
    - **APSD + WDOS** 在系统级并行下的吞吐提升。

- **4-chip System 的关键价值**：

| 指标 | 单芯片 | 4 芯片系统 |
|---|---:|---:|
| ReRAM 容量 | **8MB** | **32MB** |
| ReRAM 带宽 | **25.6GB/s** | **102.4GB/s** |
| 用途 | 单芯片功能验证 | LLM 系统级推理测试 |
| 适配对象 | 局部 DLM CB 存储 | 可存储全部 DLM codebooks |
| 并行能力 | 单 accelerator | 多 accelerator 协同 |

- **为什么需要 4-chip System**：
  - 单芯片虽然集成 **3.43MB SRAM + 8MB ReRAM**，但对于完整 LLM 推理仍然容量有限。
  - 通过 4 芯片并行，系统可获得 **32MB ReRAM**，足以存储论文中 draft LLM 的压缩 **codebooks**。
  - 多芯片系统还能提升 ReRAM 读取带宽，使 **DLM weight reconstruction** 不再频繁依赖外部 DRAM。
  - 这与论文核心目标一致：降低 **external memory access, EMA**，提升 autoregressive decoding 阶段的 token throughput。

- **与性能结果的关联**：
  - 论文中系统级结果是在 **4 chips working** 条件下评估的。
  - 对应性能如下：

| TLM & DLM | Decoding Throughput | Energy Consumption |
|---|---:|---:|
| **Vicuna-1B & LLaMA-160M** | **135.69 Token/s** | **18.26 mJ/Token** |
| **LLaMA2-7B & LLaMA-160M** | **17.82 Token/s** | **123.41 mJ/Token** |
| **LLaMA3-8B & LLaMA-296M** | **14.08 Token/s** | **151.59 mJ/Token** |

- **图中散热设计解读**：
  - 大型风扇说明该平台在测试时可能运行于较高频率或较高电压状态。
  - 论文给出的 logic die 工作范围为 **0.89–1.40V, 63.5–285MHz**。
  - 单个 ReRAM die 工作于 **1.1V, 100MHz**，每个 ReRAM die 读功耗约 **49.54mW**。
  - 4 芯片系统下，多个 logic die 与 ReRAM dies 同时工作，因此需要稳定散热以保证测量可靠性。

- **接口与调试能力分析**：
  - PCB 底部存在多个高速/低速接口，可能用于：
    - 电源输入；
    - FPGA/MCU 控制；
    - SPI 配置；
    - 数据加载；
    - 调试与测量。
  - 侧边和板上大量排针/连接器说明该平台更偏向 **research prototype**，而不是最终产品形态。
  - 这类设计便于进行电压、频率、功耗、带宽和功能正确性的实验测量。

- **与 ReRAM-on-logic stacking 的关系**：
  - 图片本身主要展示系统板，而非显微级 stacking 结构。
  - 论文中每个芯片采用 **bumping-based face-to-face ReRAM-on-logic stacking**。
  - 单芯片由 **logic die** 与 **4 个 ReRAM dies** 堆叠形成。
  - 因此，图中 4-chip system 实际上代表了多个 ReRAM-on-logic stacked accelerators 的系统级组合。

- **技术亮点在该图片中的体现**：
  - **真实硬件平台**：展示完整 PCB，而非仅芯片显微图。
  - **多芯片可扩展性**：明确标注 4-chip system。
  - **面向 LLM decoding**：支持论文中高吞吐 speculative decoding 实测。
  - **近存储系统验证**：用于证明 ReRAM bandwidth 与 BVQ codebook 存储方案可落地。
  - **系统级能效评估**：支撑论文中的 mJ/token 指标。

- **该图在论文中的作用**：
  - 它是 Figure 31.1.7 的一部分，用于补充说明：
    - 芯片已经完成流片；
    - ReRAM-on-logic stacking 已完成封装；
    - 多芯片系统已经搭建；
    - 性能数据来自真实测量环境。
  - 相比单独的 die photo，该图更强调 **system-level deployment capability**。

- **可能的系统工作流程**：
  - Host 或 MCU 将模型相关配置、指令和 codebook 数据加载到系统。
  - 每个芯片内部的 **RS-PNM** 从 stacked ReRAM 中读取 DLM codebooks。
  - **WDOS** 调度 compute、ReRAM load、EMAC 和 inter-chip transceiver 队列。
  - 多芯片协同执行 **APSD**，实现 intra-chip 与 inter-chip 的并行 draft-and-verify。
  - 输出 decoding throughput 与 energy/token 测量结果。

- **综合评价**：
  - 该图片展示的是论文成果的 **系统级硬件验证平台**。
  - 其核心价值不在于单个器件细节，而在于证明该 ReRAM-on-logic LLM accelerator 可以扩展到 **4-chip System**。
  - 该平台支撑了论文中最关键的系统级指标：**14.08–135.69 Token/s**、**4.46–7.17× speedup** 和 **3.74–4.85× energy saving**。
  - 从硬件形态看，该系统仍属于实验评估平台，但已经能够验证面向边缘 LLM decoding 的多芯片 ReRAM-stacked accelerator 架构。

### 98b7fc0199735f1c14551b1e436854c2c21efd402e7027bb8eb213dbb9aaa96a.jpg

![98b7fc0199735f1c14551b1e436854c2c21efd402e7027bb8eb213dbb9aaa96a.jpg](images/98b7fc0199735f1c14551b1e436854c2c21efd402e7027bb8eb213dbb9aaa96a.jpg)

- 这张图是 **ReRAM-on-logic 堆叠器件的 TEM 截面图**，核心用途是验证 **1T1R ReRAM Array** 的物理结构、层间连通性以及堆叠界面的加工质量。
- 图中同时包含两个层级的信息：
  - **上半部分**：更大尺度的截面，显示堆叠后的金属互连和垂直结构；
  - **下半部分**：局部放大图，展示 **1T1R ReRAM Array TEM** 的单元阵列形貌。

- 从图面特征看，最重要的观察点如下：

  | 区域 | 主要内容 | 视觉特征 | 说明 |
  |---|---|---|---|
  | 右侧放大区 | **M1 / M2 / M3 金属层** | 红色框线标出不同金属层位置，层间上下排列明显 | 证明器件内部存在清晰的多层互连结构 |
  | 中央主截面 | **垂直堆叠界面** | 结构边界清楚，层间过渡较规整 | 说明 face-to-face stacking 对准度较好 |
  | 左下角 | **1T1R ReRAM Array** 局部 TEM | 周期性柱状/接触结构明显，标尺为 **500 nm** | 表明 ReRAM 阵列具有可辨识的单元重复性 |
  | 右下局部 | 更细的阵列边缘/接触区 | 结构密集，边界锐利 | 体现工艺分辨率和阵列集成度 |
  | 全图标注 | **M1, M2, M3** | 层名直接标出 | 便于识别不同金属互连层与堆叠路径 |

- **M1、M2、M3** 的标注说明该结构至少包含三层金属互连/布线层，通常可理解为：
  - **M1**：最底层局部互连；
  - **M2**：中间互连层；
  - **M3**：更上层的跨区或堆叠相关互连层。
- 这种层级结构的意义在于：
  - 支持 **ReRAM 单元阵列** 与逻辑电路之间的高密度连接；
  - 提升 **并行读出** 和 **高带宽数据搬运** 能力；
  - 为论文中提到的 **25.6GB/s ReRAM bandwidth** 提供物理基础。

- 从图像清晰度和层边界来看，可以得到几个工艺层面的判断：
  - **层间界面较平整**，没有明显的大尺度空洞或严重偏移；
  - **金属层连续性较好**，说明堆叠互连较可靠；
  - **阵列重复单元规整**，反映出 ReRAM 阵列具备较好的可制造性；
  - 图中未见明显灾变性缺陷，支持论文中“**bumping-based face-to-face stacking technology**”的工程可行性。

- 结合论文整体内容，这张图的论文作用非常明确：
  - 为 **ReRAM-stacked process-near-memory (RS-PNM)** 提供 **硬件实证**；
  - 说明 DLM 的 codebook 可以被存放在 ReRAM 中，并通过堆叠接口高效读取；
  - 支撑作者关于 **减少 DLM external memory access (EMA)** 的主张；
  - 从材料和封装层面证明，这不是纯架构假设，而是 **已流片实现**。

- 如果从“图像信息密度”角度总结，这张图传达的关键结论是：

  | 结论 | 图像依据 | 对论文的意义 |
  |---|---|---|
  | **ReRAM 与逻辑层已成功堆叠** | 上下结构清晰、界面可辨 | 支撑 3D integration 方案 |
  | **互连层分布明确** | M1/M2/M3 标注清楚 | 说明层间路由设计完整 |
  | **阵列具有纳米级结构特征** | TEM 细节可见、500 nm 标尺 | 说明 ReRAM 阵列加工精细 |
  | **适合高带宽并行访问** | 结构规整且密集 | 对应论文中的 25.6GB/s 读带宽 |
  | **可用于存放 DLM codebook** | 阵列稳定、可重复 | 支撑 BVQ + RS-PNM 架构 |

- 若从论文叙事链条看，这张图属于“**制造验证图**”，它不是用来展示算法效果，而是用来证明：
  - **堆叠封装真实存在**
  - **ReRAM 阵列真实可用**
  - **高带宽近存计算架构可落地**
- 因此，它在全文中承担的是 **physical evidence** 的角色，属于论文硬件可信度的重要支撑图。

- 简要评价：
  - **优点**：结构层次清晰、标注明确、能够直接证明 ReRAM-on-logic 堆叠与阵列实现。
  - **局限**：单张 TEM 图只能证明局部结构质量，不能单独说明大规模均匀性或长期可靠性。
  - **总体判断**：这是一张典型的 **工艺验证型显微图**，直接服务于论文的 **RS-PNM + BVQ** 体系论证。

### 647cf3ea756a0760bcca765ccbca7eb51e6e189e7d7fb8bf98e9c6d7e7074531.jpg

![647cf3ea756a0760bcca765ccbca7eb51e6e189e7d7fb8bf98e9c6d7e7074531.jpg](images/647cf3ea756a0760bcca765ccbca7eb51e6e189e7d7fb8bf98e9c6d7e7074531.jpg)

- **图片核心内容**
  - 该图展示的是 **ReRAM Resistance State Distribution**，即 ReRAM 单元在两种阻态下的统计分布。
  - 两条曲线分别对应：
    - **HRS（High Resistance State）**：高阻态，通常表示逻辑 **“0”** 或未导通状态。
    - **LRS（Low Resistance State）**：低阻态，通常表示逻辑 **“1”** 或导通状态。
  - 图中重点标注：**Clear 0/1 Distinction at 0.1 PPM Level**，说明 HRS 与 LRS 在极低误判概率水平下仍具有清晰区分度。

- **图中坐标含义**

| 项目 | 含义 | 观察 |
|---|---|---|
| 横轴 | **Current (Arbitrary Unit)** | 电流，采用任意单位，近似对数尺度 |
| 纵轴 | **CD (PPM)** | Cumulative Distribution，单位为 ppm，表示统计分布尾部概率 |
| 蓝色曲线 | **HRS Distribution** | 位于左侧，电流较小 |
| 红色曲线 | **LRS Distribution** | 位于右侧，电流较大 |
| 虚线圈注区域 | **0/1 Distinction** | HRS 与 LRS 之间存在明显间隔 |

- **HRS 与 LRS 分布特征**

| 状态 | 曲线颜色 | 电流范围特征 | 分布位置 | 物理含义 |
|---|---|---|---|---|
| **HRS** | 蓝色 | 电流较低 | 图左侧 | ReRAM 处于高阻状态，导电能力弱 |
| **LRS** | 红色 | 电流较高 | 图右侧 | ReRAM 处于低阻状态，导电能力强 |

- **关键观察**
  - **HRS 与 LRS 分布明显分离**：
    - 蓝色 HRS 曲线集中在低电流区域。
    - 红色 LRS 曲线集中在高电流区域。
    - 两者中间存在明显空隙，说明读出窗口较大。
  - **0.1 PPM 级别仍可区分**：
    - 图中标注表明，即使考虑到极低概率的分布尾部，HRS 和 LRS 仍未严重重叠。
    - 这意味着 ReRAM 阵列具有较好的 **read reliability**。
  - **适合存储压缩后的 DLM codebook**：
    - 本文中 ReRAM 主要用于存储 **Draft LLM (DLM)** 的 **Blockwise Vector Quantization (BVQ) codebook**。
    - 清晰的阻态区分有助于降低 codebook 读取错误率。

- **与论文架构的关系**
  - 该图属于 **Figure 31.1.7** 的一部分，用于证明 ReRAM-on-Logic stacking 中 ReRAM 存储介质的可靠性。
  - 论文提出的系统将 **4 个 ReRAM dies** 堆叠在 logic die 上，通过 face-to-face bumps 提供：
    - **8MB ReRAM capacity**
    - **25.6GB/s bandwidth**
    - **100MHz ReRAM read frequency**
  - 该阻态分布图支撑了一个关键结论：**ReRAM 可稳定承担 DLM codebook 存储与高带宽读取任务**。

- **对系统性能的意义**

| 影响方向 | 具体意义 |
|---|---|
| **读取可靠性** | HRS/LRS 分离明显，降低 bit error 风险 |
| **低功耗存储** | ReRAM 作为非易失存储，可减少外部 DRAM 访问 |
| **高带宽近存储访问** | 支撑 RS-PNM 从 ReRAM 快速读取 codebook |
| **DLM EMA 降低** | 避免频繁 external memory access |
| **推理吞吐提升** | 有助于实现 14.08-to-135.69 Token/s |
| **能耗下降** | 支撑 3.74-to-4.85× energy saving |

- **为什么该图重要**
  - 本文的核心之一是用 **stacked ReRAM** 存储压缩后的 DLM 权重 codebook。
  - 如果 ReRAM 的 HRS/LRS 分布重叠严重，则会导致：
    - codebook 读取错误；
    - DLM 权重重构错误；
    - speculative decoding 质量下降；
    - accepted token ratio 降低；
    - 系统性能和精度受损。
  - 该图表明 ReRAM 的状态分布稳定，能够支撑本文的 **RS-PNM + BVQ** 设计。

- **技术解读**
  - ReRAM 通过不同阻值状态存储 bit 信息。
  - 读取时，本质上是通过检测电流大小判断单元处于 **HRS** 还是 **LRS**。
  - 图中 HRS 电流低、LRS 电流高，且二者间隔明显，说明 sense margin 较充足。
  - **sense margin 越大，读出电路越容易准确判别 0/1 状态**。
  - 这对于多 die 堆叠、高并行读取场景尤其重要，因为大规模并行访问会放大存储误差和工艺波动影响。

- **潜在隐含结论**
  - ReRAM 单元一致性较好。
  - 写入后的阻态保持稳定。
  - HRS/LRS 的尾部分布没有明显交叠。
  - 在 **0.1 PPM** 级别仍能区分，说明极端错误概率较低。
  - 适合用于本文所需的高带宽、低延迟、近存储读取场景。

- **与 BVQ 的结合价值**
  - BVQ 将 DLM 权重压缩为 block-level codebook。
  - ReRAM 存储的是 codebook，而不是完整高精度权重。
  - 由于 codebook 是重构权重的基础，其读取准确性非常关键。
  - 该图证明 ReRAM 具备足够可靠的二值存储能力，从而支撑：
    - **codebook fetch**
    - **weight reconstruction**
    - **tile fusion**
    - **DLM speculative drafting**

- **简要评价**
  - 该图从器件层面验证了系统设计的可行性。
  - **HRS/LRS 清晰分离** 是 ReRAM 用于 LLM accelerator 的关键前提。
  - 对本文而言，该结果不仅是存储器件指标，也直接支撑了 **ReRAM-stacked PNM architecture** 的系统级性能收益。

