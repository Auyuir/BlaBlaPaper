# 31.1 A 14.08-to-135.69Token/s ReRAM-on-Logic Stacked Outlier-Free Large-Language-Model Accelerator with Block-Clustered Weight-Compression and Adaptive Parallel-Speculative-Decoding 论文解析

## 0. 论文基本信息

**作者 (Authors)**: Pingcheng Dong, Yonghao Tan, Xuejiao Liu, et al.

**发表期刊/会议 (Journal/Conference)**: ISSCC

**发表年份 (Publication Year)**: 2025

**研究机构 (Affiliations)**: Hong Kong University of Science and Technology, AI Chip Center for Emerging Smart System

---

## 1. 摘要

**目的**
- 解决边缘加速器上大语言模型（LLM）在投机解码中面临的延迟瓶颈。
- 克服目标LLM（TLM）外部内存访问（EMA）开销大、草稿LLM（DLM）片上内存容量受限以及长草稿长度（DL）下高拒绝率三大挑战。

---

**方法**
- 提出一款基于投机解码的LLM加速器，采用基于凸点的面对面ReRAM-on-logic堆叠技术。
- 设计局部旋转单元（LRU）：
  - 将深度快速沃尔什-阿达马变换（FWHT）分解为重叠的上下低成本6深度FWHT，近似全局旋转。
  - 消除激活异常值，实现低比特无异常量化，支持精确的W4A8 TLM量化。
- 提出ReRAM堆叠近存处理（RS-PNM）架构与块级向量量化（BVQ）算法：
  - BVQ将DLM权重聚类为块级码本存储于高密度ReRAM中。
  - RS-PNM通过高带宽堆叠接口检索CBs重建权重，避免DLM EMA。
  - 采用垂直CB映射与Tile融合单元（TFU）消除冗余CB访问，减半读取延迟。
- 提出自适应并行投机解码（APSD）方案与工作负载解耦的乱序调度器（WDOS）：
  - 结合短DL的低拒绝率和长DL的高接受Token产量，动态调整草稿策略。
  - WDOS将APSD工作负载解耦为4个并行指令队列，实现依赖感知同步，最大化片内并行草稿与验证的资源利用率。
![](images/35e0a769328cec7f2a443cbeac62806291ffe25f5ef4f66f0cc9a730a3033ad2.jpg) *Figure 31.1.2: Overall architecture and three main features of the LLM accelerator with bumping-based ReRAM die on logic wafer face-to-face stacking technology.*

---

**结果**
- 芯片采用55nm工艺，逻辑die运行在63.5-285MHz，ReRAM die运行在100MHz，实现2.33 TOPS峰值性能。
- 实现14.08至135.69 Token/s的解码吞吐量。
- 相比BF16 SD基线，实现4.46至7.17倍加速和3.74至4.85倍节能。
- LRU相比全局旋转节省92.7%面积；RS-PNM相比带LRU的W4A8 SD实现1.1至1.46倍加速；APSD相比RS-PNM实现1.1至1.29倍加速并减少10-14%拒绝Token延迟。
- 关键性能指标对比：

| TLM & DLM | Vicuna-1B & LLaMA-160M | LLaMA2-7B & LLaMA-160M | LLaMA3-8B & LLaMA-296M |
| :--- | :--- | :--- | :--- |
| **Decoding Throughput** | **135.69 Token/s** | **17.82 Token/s** | **14.08 Token/s** |
| **Speedup** | **7.17×** | **4.46×** | **5.33×** |
| **Energy Consumption** | **18.26 mJ/Token** | **123.41 mJ/Token** | **151.59 mJ/Token** |
| **Energy Saving** | **4.85×** | **3.74×** | **3.95×** |

![](images/8d98fc348c2192be50b13ed830308a24ca0388f5e6f7b35120799051f30bd216.jpg)

---

**结论**
- 成功设计并流片了一款基于ReRAM-on-logic堆叠技术的LLM加速器。
- 通过软硬件协同设计（LRU、RS-PNM、APSD）有效解决了边缘设备上LLM投机解码的内存访问和延迟瓶颈。
- 在吞吐量、能效和量化精度上均达到业界领先水平，为边缘端部署大模型提供了高效的硬件架构范式。

---

## 2. 背景知识与核心贡献

**研究背景与动机**

- **LLM 自回归解码瓶颈**：Large Language Models（LLMs）在自然语言处理任务中表现卓越，但其逐 Token 的自回归解码范式导致严重的延迟开销，主要源于大量的权重外部内存访问。
- **Speculative Decoding 的局限性**：Speculative Decoding（SD）通过小规模 Draft LLM（DLM）提前解码多个 Token 并由大规模 Target LLM（TLM）并行验证，在 GPU 上有效缓解了该问题。然而，在资源受限的边缘加速器上，SD 的延迟仍由权重 EMA 主导（超 60% 来自 TLM）。
- **三大核心挑战**：
  - **TLM 量化精度与面积开销矛盾**：低比特 Post-Training Quantization（PTQ）受 Activation Outliers 影响导致精度下降。基于 Fast Walsh-Hadamard Transform（FWHT）的方法可消除异常值，但深度 FWHT 阵列带来巨大的面积开销（约为 4K INT8 MAC 阵列的 4.37 倍）。
  - **DLM 片上存储容量不足**：DLM 虽小且易通过 Quantization-Aware Training（QAT）量化，但边缘加速器有限的片上内存无法缓存所有 DLM 权重，导致频繁的 EMA 并加剧延迟。
  - **长 Draft Length 拒绝率过高**：在长 DL 下，超 90% 的 DLM 草稿 Token 被 TLM 拒绝，其延迟开销抵消了减少 TLM EMA 带来的收益。

![](images/ec0516b27a8f1e1311aa35f8bb84ec8ad64c53a82f0e0c8245ee857fed4d3573.jpg) *Figure 31.1.1: Challenges raised by target and draft large language model (LLM) in speculative decoding (SD) and proposed solutions.*

---

**核心贡献**

针对上述挑战，本文提出了一种基于 SD 的 LLM 加速器，结合 ReRAM-on-Logic 堆叠技术，具备三大核心特性：

- **Local Rotation Unit（LRU）**：
  - 将深度 FWHT 分解为重叠的上下低成本的 6 深度 FWHT，近似全局旋转。
  - 通过两阶段旋转 Token 特征，以极小的面积负担消除 Activation Outliers。
  - 支持精确的 W4A8 TLM 量化，相比 BF16 SD 实现 **3.82-to-3.93×** 加速，并节省 **92.7%** 的面积。
- **ReRAM-Stacked Process-Near-Memory（RS-PNM）架构与 Blockwise Vector Quantization（BVQ）**：
  - 采用基于凸块的正面对齐 ReRAM-on-logic 堆叠技术扩展片上内存容量，避免 DLM EMA。
  - BVQ 算法将 DLM 权重聚类为块级 Codebooks（CBs）并存储于高密度 ReRAM 中。
  - RS-PNM 通过高带宽堆叠接口检索 CBs 重构权重，相比带有 LRU 的 W4A8 SD 实现 **1.1-to-1.46×** 加速。
- **Adaptive Parallel Speculative Decoding（APSD）与 Workload-Decoupled Out-of-Order Scheduler（WDOS）**：
  - 结合短 DL 的低拒绝率和长 DL 的高接受 Token 产量，根据 TLM 验证反馈动态切换起草策略。
  - 设计具有 4 个并行指令队列的乱序调度器，避免并行起草与验证中的资源竞争。
  - 相比 RS-PNM 实现 **1.1-to-1.29×** 加速，并将拒绝的 Token 比率降低 **10-to-14%**。

---

**性能指标与对比**

- **工艺与架构**：采用 **55nm** 工艺制造，基于凸块的正面对齐 ReRAM-on-logic 堆叠技术。
- **硬件规格**：

| 组件 | 参数规格 |
| :--- | :--- |
| Logic Die | 频率 **63.5-to-285MHz**，电压 **0.89-to-1.40V**，峰值性能 **2.33TOPS** |
| ReRAM Die | 频率 **100MHz**，容量 **8MB**，带宽 **25.6GB/s**，功耗 **49.54mW** |
| 4-Chip System | ReRAM 扩展至 **32MB**，带宽达 **102.4GB/s** |

- **系统级性能**：
  - 实现 **14.08-to-135.69 Token/s** 的解码吞吐量。
  - 相比 BF16 SD 基准，实现 **4.46-to-7.17×** 加速和 **3.74-to-4.85×** 能量节省。
  - 在 LLaMA2-7B 模型上，解码吞吐量达 **17.82 tokens/s**，能耗低至 **123.41 mJ/token**。

![](images/8d98fc348c2192be50b13ed830308a24ca0388f5e6f7b35120799051f30bd216.jpg)

---

## 3. 核心技术和实现细节

### 0. 技术架构概览

**物理层架构与3D堆叠技术**

本文提出的 LLM Accelerator 采用 **55nm** 工艺制造，基于 **bumping-based face-to-face ReRAM-on-logic stacking technology** 构建。该架构通过 **2048** 个 face-to-face bumps 将 **4个 ReRAM die** 堆叠在 logic die 之上，实现并行读取，提供高达 **25.6GB/s** 的带宽与 **8MB** 的片上存储容量。

![](images/35e0a769328cec7f2a443cbeac62806291ffe25f5ef4f66f0cc9a730a3033ad2.jpg) *Figure 31.1.2: Overall architecture and three main features of the LLM accelerator with bumping-based ReRAM die on logic wafer face-to-face stacking technology.*

---

**Logic Die 核心模块**

Logic Die 负责整体控制、计算调度与数据流处理，主要包含以下组件：
- **控制与存储单元**：Top controller、MCU、64KB ISA buffer、4 PLLs、Interconnect bus。
- **数据缓冲区**：1MB weight buffer、2MB global token buffer。
- **外部存储接口**：EMA controller (EMAC) 用于管理外部 DRAM 访问。
- **片间通信**：Inter-chip transceiver 支持多芯片扩展。
- **核心处理引擎**：LRU、WDOS 以及 RS-PNM。

---

**核心处理引擎：RS-PNM**

ReRAM-stacked process-near-memory (RS-PNM) 架构利用高带宽堆叠接口加载 DLM Codebooks，包含以下关键子模块：
- **Codebook Fetcher Unit (CFU)**：触发 ReRAM controller 加载 Codebooks。
- **ReRAM Load Interface (RLI)**：采用双倍时钟速率 (**200MHz**) 稳定读取数据，并通过异步 FIFO groups 实现可靠的时钟域跨越。采用 Vertical CB mapping 最大化带宽利用率。
- **Tile-Fused Tensor Engine (TFTE)**：融合共享相同 CB entry 的 token tiles，确保每个 CB 仅被读取一次，从而减半 CB 读取延迟，并支持层内与层间并行。
- **Non-Linear Processing Unit (NLPU)**：处理非线性运算。

---

**架构协同设计的三大核心特征**

- **Local Rotation Unit (LRU)**：针对 TLM 设计，通过将深度 FWHT 分解为重叠的上下低深度 6-depth FWHT 来近似全局旋转。消除 activation outliers，实现高精度的 W4A8 量化，同时节省 **92.7%** 的面积开销。
- **Blockwise Vector Quantization (BVQ)**：结合 INT4 QAT 与 Gumbel softmax 重参数化，在块级聚类学习 Codebooks。将 DLM 权重压缩并存储于高密度 ReRAM 中，彻底避免 DLM 的外部存储访问 (EMA)。
- **Adaptive Parallel Speculative Decoding (APSD) 与 WDOS**：APSD 根据验证反馈动态切换短 DL drafting 与长 DL parallel draft-and-verify。Workload-decoupled out-of-order scheduler (WDOS) 将工作负载解耦至 4 个并行指令队列，通过依赖感知同步机制最大化资源与带宽利用率。

---

**芯片规格参数**

| 规格 | Logic Die | ReRAM Die (×4) |
| :--- | :--- | :--- |
| **Technology** | 55nm | 55nm |
| **Voltage** | 0.89 - 1.40 V | 1.1 V |
| **Frequency** | 62.5 - 285 MHz | 100 MHz |
| **Die Area** | 55.98 mm² | 5.553 × 4 mm² |
| **Memory Capacity** | 3.43 MB SRAM | 2 × 4 MB |
| **Power** | 0.265 - 3.060 W | 49.54 × 4 mW (Read) |
| **Bump #** | - | 2912 (Data: 2048, Ctrl.: 864) |

### 1. Local Rotation Unit (LRU) with Decomposed FWHT

**核心观点**

Local Rotation Unit (LRU) 通过将深层的 Fast Walsh-Hadamard Transform (FWHT) 分解为重叠的低成本 6-depth FWHTs，以极小的面积开销近似实现全局旋转，从而消除 activation outliers，支持高精度的 W4A8 Target LLM (TLM) 量化。

---

**实现原理与算法流程**

- **维度分解与深度限制**
  - TLM 常包含非 2 的幂次方维度，传统方法将维度 $n$ 分解为 $2^k \times m$（例如 LLaMA3-8B 的 down_proj 层中 $14336 = 2^9 \times 28$）。
  - 这种级联的 FWHT-GEMM 阵列需要大量高精度运算器，导致巨大的面积开销。
  - LRU 利用 npot Hadamard construction，将 FWHT 的深度从 9 限制至低成本的 6。
- **两阶段局部旋转**
  - 搜索合适的 $(m, k)$ 参数对，使其组合覆盖范围跨越原始维度 $n$。
  - 将全局旋转近似为两个阶段：overlapped upper rotation 和 lower rotation。
  - 在每个阶段，Token Allocator Unit (TAU) 将 token tiles 分配给 Reconfigurable FWHT Array (RFA)。
- **硬件优化与无 MAC 累加**
  - RFA 可重构以支持 $2^1$ 至 $2^6$ 的 FWHT。
  - 为减少高精度加法器的需求，早期阶段的相邻 FWHTs 被合并以共享输入。
  - 轻量级路由网络根据所选模式分发数据。
  - TAU 将 RFA 输出和 npot Hadamard tiles 的二进制部分分配给 Hadamard Accumulator Unit (HAU)。
  - HAU 通过融合 FP16 Hadamard 和动态量化器的缩放因子，实现无 MAC 累加。

![](images/f4a3c9d1bcf4ad90a834be1e07d1967bc6f8bca553aa9c2333a8a212f00885e6.jpg)

---

**硬件架构与参数设置**

- **核心组件**：TAU、RFA、HAU。
- **RFA 配置范围**：支持 $2^1$ 至 $2^6$ 深度的 FWHT。
- **FWHT 最大深度**：6-depth。
- **量化精度**：W4A8 (Weight 4-bit, Activation 8-bit)。
- **面积节省**：相比全局旋转，节省 **92.7%** 的面积。

---

**输入输出关系与整体作用**

- **输入**：TLM 的 token features。
- **处理过程**：token features 经过两阶段局部旋转，消除 activation outliers，随后进行动态量化。
- **输出**：旋转且动态量化后的 W4A8 token，缩放因子被旁路至 Tile-Fused Tensor Engine (TFTE) 用于后续层量化。
- **整体作用**：
  - 解决了低比特 Post-Training Quantization (PTQ) 因 activation outliers 导致的严重精度下降问题。
  - 避免了传统 FWHT 方法带来的巨大面积开销。
  - 相比 BF16 Speculative Decoding (SD)，实现了 **3.82-to-3.93×** 的加速。

---

**性能与精度对比**

| TLM Model | BF16 | W4A8 | W4A8 w/ GR (Global Rotation) | W4A8 w/ LRU (This Work) |
| :--- | :--- | :--- | :--- | :--- |
| Vicuna-1B | 9.18 | 10.34 | 9.43 | **9.41** |
| LLaMA2-7B | 5.47 | 8.57 | 5.68 | **5.68** |
| LLaMA3-8B | 6.14 | 7.54 | 6.70 | **6.71** |

- **Perplexity (↓) 分析**：直接使用 W4A8 量化会导致精度大幅下降；引入 LRU 后，Perplexity 与 Global Rotation 效果相当，逼近 BF16 基线。

### 2. ReRAM-stacked Process-Near-Memory (RS-PNM) with Blockwise Vector Quantization (BVQ)

**技术背景与核心动机**
- 在边缘加速器上，有限的片上存储容量无法缓存所有 Draft LLM (DLM) 权重，导致频繁的 External Memory Access (EMA)，受限于外部带宽从而加剧延迟开销。
- 为解决此问题，系统采用基于 bumping 的 **ReRAM-on-logic stacking** 技术设计 **ReRAM-stacked Process-Near-Memory (RS-PNM)** 架构，并协同设计 **Blockwise Vector Quantization (BVQ)** 算法。

![](images/3b0e66f5354f2e35897d0d77f0d4a63bb57d425d98a22069e68b01a57a98d1b7.jpg) *Figure 31.1.4: ReRAM-stacked processing-near-memory (RS-PNM) architecture with blockwise vector quantization (BVQ) to avoid draft LLM external memory access (EMA).*

**BVQ 算法原理与流程**
- **算法核心**：将 DLM 权重聚类为 block-level codebooks (CBs) 存储于高密度 ReRAM 中，通过高带宽 stacking interface 检索 CBs 重建权重。
- **训练与量化机制**：
  - 联合学习 blockwise CBs 与 INT4 Quantization-Aware Training (QAT)。
  - 使用 **Gumbel softmax** 重参数化学习 block indices。
- **架构优势**：相比传统 Vector Quantization (VQ) 方法，BVQ 避免了 index buffers 和 multi-port decoders 带来的巨大面积开销，仅需轻量级 ISA decoder 即可检索 CBs。

**RS-PNM 硬件架构与数据流**
- **存储与加载机制**：
  - MCU 通过 SPI 接口将 DLM CBs 存入堆叠的 ReRAM dies。
  - Codebook Fetcher Unit (CFU) 触发 ReRAM controller 与 ReRAM Load Interface (RLI)，将 CBs 从 ReRAM 加载至 weight buffer。
- **时钟与跨时钟域处理**：
  - RLI 采用双倍时钟速率 (**200MHz**) 稳定读取数据。
  - 数据随后传输至 asynchronous FIFO groups，确保可靠的 clock domain crossing。
- **CB 映射策略**：
  - 采用 **vertical CB mapping** 替代 horizontal mapping，消除有限时钟频率下的数据拥塞。
  - 每个 CB 内的 block dimensions 受限于 per-die ReRAM bank width，以最大化带宽利用率。
- **Tile Fusion 优化**：
  - Vertical mapping 会导致权重重建时出现冗余 CB 访问。
  - Tile Fusion Unit (TFU) 融合共享相同 CB entry 的 token tiles，确保每个 CB 仅被获取一次，将 CB 读取延迟减半。
  - TFUs 独立执行 token fusion，促进 intra- 和 inter-layer parallelism。

**硬件参数与规格**
| 参数类别 | 规格详情 |
| --- | --- |
| **堆叠技术** | Bumping-based face-to-face ReRAM-on-logic stacking |
| **ReRAM Dies 数量** | 4 |
| **Bump 数量** | 2912 (Data: 2048, Ctrl.: 864) |
| **Bump 直径** | 40μm |
| **存储容量** | 8MB (单芯片), 32MB (4-chip 系统) |
| **带宽性能** | 25.6GB/s @ 100MHz (单芯片), 102.4GB/s (4-chip 系统) |
| **ReRAM 功耗** | 49.54mW @ 1.1V (每个 die) |

![](images/647cf3ea756a0760bcca765ccbca7eb51e6e189e7d7fb8bf98e9c6d7e7074531.jpg)

**输入输出关系与系统级作用**
- **输入**：DLM 的 INT4 QAT 权重及通过 Gumbel softmax 生成的 block indices。
- **处理过程**：权重以 CBs 形式紧凑存储于 ReRAM，RLI 高速读取，TFU 融合去重并重建完整权重。
- **输出**：重建的 DLM 权重，供后续计算单元使用。
- **整体作用**：
  - 彻底消除 DLM 的 EMA 开销，突破边缘设备外部带宽瓶颈。
  - 相比带有 LRU 的 W4A8 Speculative Decoding (SD)，RS-PNM 结合 INT4 BVQ 实现了 **1.1-to-1.46×** 的加速。
  - 在 4-chip 系统中，32MB ReRAM 足以存储所有 DLM CBs，大幅提升解码吞吐量。

### 3. Tile Fusion Unit (TFU)

**核心背景与挑战**
- 在 **ReRAM-stacked process-near-memory (RS-PNM)** 架构中，为避免有限时钟频率下水平 **Codebook (CB)** 映射导致的数据拥塞，系统采用 **Vertical CB mapping**。
- **Vertical CB mapping** 将块维度限制在单个 **ReRAM** bank 宽度内以最大化带宽利用率，但在片上完整重构权重时，会导致严重的 **Redundant CB access** 问题。
- 这种冗余访问产生额外的延迟开销，成为限制 **Draft LLM (DLM)** 推理性能的瓶颈。

![](images/f98bc50120253aedac614d0f349b77c963add39794e73276053d0d6e48d5eece.jpg) *Issue: Redundant Codebook ReRAM Access*

---

**实现原理与算法流程**
- **Tile Fusion Unit (TFU)** 的核心原理是识别并合并共享相同 **CB** 条目的 **Token tiles**。
- 算法流程如下：
  - 识别具有相同 **CB** 索引的 **Token tiles**。
  - 在数据加载和计算阶段对这些 **Token tiles** 进行融合操作。
  - 确保每个 **CB** 条目仅需从 **ReRAM** 中获取一次。
  - 利用融合后的数据直接进行后续的权重重构与计算。

**输入输出关系**
- 输入：
  - 来自 **ReRAM** 的 **CB** 索引请求。
  - 多个待处理的 **Token tiles** 数据。
- 输出：
  - 去重后的 **CB** 获取指令。
  - 融合后的计算数据流，直接输送至 **Tile-fused tensor engine (TFTE)** 进行权重重构。

---

**在整体架构中的作用**
- **延迟优化**：通过消除冗余访问，直接将 **CB** 读取延迟减半。
- **并行计算增强**：**TFU** 独立执行 **Token** 融合，促进 **Intra-layer parallelism** 和 **Inter-layer parallelism**。
- **系统级加速**：配合 **INT4 BVQ** 算法，在包含 **LRU** 的 **W4A8 SD** 基础上，实现 **1.1-to-1.46×** 的系统级加速。

![](images/f4a3c9d1bcf4ad90a834be1e07d1967bc6f8bca553aa9c2333a8a212f00885e6.jpg)

---

**性能指标与参数对比**

| 特性维度 | 无 TFU 架构 | 引入 TFU 架构 |
| :--- | :--- | :--- |
| **CB Access 模式** | 冗余访问 | 唯一访问 |
| **CB Read Latency** | 基准延迟 | **减半** |
| **并行支持** | 受限 | **Intra/Inter-layer parallelism** |
| **系统级加速比** | 基准 | **1.1-to-1.46×** (over W4A8 SD with LRU) |

### 4. Adaptive Parallel Speculative Decoding (APSD)

**核心原理**

- 传统 Speculative Decoding (SD) 面临 TLM 和 DLM 协同瓶颈：长 Draft Length (DL) 虽能减少 TLM 的 weight EMA，但会增加 DLM 延迟，且长 DL 下超过 90% 的 draft tokens 会被 TLM 拒绝。
- 现有并行 SD 方法（如 inter-chip parallel draft-and-verify）虽隔离了工作负载，但慢速的 TLM 验证导致 DLM 严重 idle，浪费 ReRAM 带宽。
- **Adaptive Parallel Speculative Decoding (APSD)** 动态适应 drafting 策略，结合短 DL 的**低拒绝率**和长 DL 的**高 accepted token yield**，从根本上缓解 DLM idleness。

---

**算法流程与参数设置**

- **初始阶段**：APSD 以**非并行短 DL drafting** 起步。
- **并行阶段**：随后进入**并行 draft-and-verify** 模式。
- **动态适应逻辑**：基于 TLM verification 的反馈进行策略切换。
  - **继续并行条件**：TLM 接受所有先前的 draft tokens，且其最新生成的 token 与并发 DLM drafting 产生的第一个 draft token 匹配。
  - **回退条件**：若上述条件不满足，draft tokens 被丢弃，APSD 回退至**非并行 DLM drafting**。
- **硬件协同与参数设置**：
  - 设计 **Workload-Decoupled Out-of-order Scheduler (WDOS)**，包含 4 个并行指令队列，与 APSD workloads 解耦，避免并行 draft-and-verify 中的资源竞争。
  - 采用 **CB-interleaved intra-layer mapping (CILM)**，将 intra-layer CBs 均匀分配跨芯片，并在每个 DLM block 内交错，确保加载时充分利用 ReRAM 带宽。
  - 4 个指令队列分别为：inter-chip transceiver, compute, ReRAM load, EMAC。
  - Intra-queue decoders 提取 dependency markers 发送至 inter-queue synchronizers，共同维护 synchronous counter matrix 追踪就绪状态。
  - 当指令的 parent queues 准备就绪时发射指令，并通知其 daughter queues。

---

**输入输出关系与系统作用**

- **输入**：TLM verification 反馈（包括 draft tokens 的接受/拒绝状态，以及 TLM 最新生成的 token）。
- **输出**：下一轮的 drafting 策略指令（继续并行 draft-and-verify 或回退至非并行 DLM drafting）。
- **整体作用**：在 LLM accelerator 架构中，APSD 实现了 **intra-chip parallel draft-and-verify**，最大化资源与带宽利用率，解决了传统 SD 中 DLM 空转和内存接口无法跨工作负载共享的问题。

---

**性能指标**

- 相比于带有 LRU 的 RS-PNM 基线，APSD 实现了显著的性能提升与延迟降低。

| 指标 | 性能表现 |
| --- | --- |
| **Speedup** | **1.1-to-1.29×** |
| **Rejected DLM Latency Reduction** | **10-to-14%** |

![](images/e91dc4a6d3187e74220e2b1c432d25c936e3984be1155107aa9c012d7313da76.jpg)

### 5. Workload-Decoupled Out-of-Order Scheduler (WDOS)

**核心定位与系统作用**
- **Workload-Decoupled Out-of-Order Scheduler (WDOS)** 是 **Adaptive Parallel Speculative Decoding (APSD)** 的底层硬件执行引擎。
- 解决传统 inter-chip parallelism 导致的 **DLM idle** 和 **ReRAM/DRAM** 带宽浪费问题。
- 通过解耦工作负载实现 **intra-chip parallel draft-and-verify**，避免资源竞争，最大化资源与带宽利用率。

---

**架构设计与队列解耦**
- WDOS 将 APSD workloads 简化并解耦为 **4 个并行 instruction queues**：
  - **inter-chip transceiver** 队列：处理芯片间通信。
  - **compute** 队列：执行张量计算任务。
  - **ReRAM load** 队列：管理近存计算架构的权重加载。
  - **EMAC (External Memory Access Controller)** 队列：控制外部内存访问。
- 配合 **CB-interleaved intra-layer mapping (CILM)** 策略，将 intra-layer codebooks (CBs) 均匀分配至各芯片并在每个 DLM block 内交错，确保加载时充分利用 **ReRAM** 带宽。

---

**依赖感知同步机制与算法流程**
- **输入**：APSD 产生的混合指令流（包含短 DL drafting 和长 DL parallel draft-and-verify 指令）。
- **处理流程**：
  - **intra-queue decoders** 从各队列指令中提取 **dependency markers**。
  - 将 markers 发送至 **inter-queue synchronizers**。
  - 同步器共同维护一个 **synchronous counter matrix**，用于实时追踪指令的就绪状态。
  - 当某条指令的 **parent queues** 全部就绪时，该指令被发射执行。
  - 执行完毕后，通知其 **daughter queues** 更新状态。
- **输出**：经过依赖关系重排的乱序执行指令流，确保无死锁且流水线不断流。

---

**性能收益与指标**
- 相比仅使用 RS-PNM 的系统，WDOS 带来显著的性能提升：

| 评估指标 | 性能表现 |
|---|---|
| **Speedup** (对比 RS-PNM) | **1.1-to-1.29×** |
| **Rejected DLM Latency Reduction** | **10-to-14%** |

![](images/e91dc4a6d3187e74220e2b1c432d25c936e3984be1155107aa9c012d7313da76.jpg)


---

## 4. 实验方法与实验结果

**实验设置**

- 硬件平台：基于 **55nm** 工艺制造，采用 bumping-based face-to-face **ReRAM-on-logic stacking** 技术。
- 逻辑Die参数：供电电压 **0.89-1.40V**，运行频率 **62.5-285MHz**，面积 **55.98 mm²**，集成 **3.43MB SRAM**，峰值性能 **2.33TOPS**。
- ReRAM Die参数：供电电压 **1.1V**，运行频率 **100MHz**，单Die容量 **2MB**（4 Die共 **8MB**），读取功耗 **49.54mW**。
- 多芯片系统：采用 **4-chip system**，ReRAM总容量扩展至 **32MB**，带宽达 **102.4GB/s**。
- 测试模型组合：
  - **Vicuna-1B** (TLM) & **LLaMA-160M** (DLM)
  - **LLaMA2-7B** (TLM) & **LLaMA-160M** (DLM)
  - **LLaMA3-8B** (TLM) & **LLaMA-296M** (DLM)
- 量化精度：TLM 采用 **W4A8**，DLM 采用 **W4A8**（结合 **BVQ** 实现平均 **2bit/value**）。
- 评估数据集：使用 **Wikitext-2** 评估 Perplexity，使用 **MT-Bench** 评估系统级吞吐量与能耗。

![](images/689be0a96b8fba5d2fe8e5b216718f0705478276414c1ed3c7098595dd0aa93e.jpg)

---

**结果数据**

- 整体性能：实现 **14.08-to-135.69Token/s** 的解码吞吐量，相比 BF16 SD baseline 实现 **4.46-to-7.17×** 加速，能耗节省 **3.74-to-4.85×**。
- 内存访问优化：平均 EMA 节省 **4.79×至6.67×**。
- 系统级吞吐量与能耗对比：

| TLM & DLM 组合 | 解码吞吐量 | 加速比 | 能耗 | 能耗节省 |
| :--- | :--- | :--- | :--- | :--- |
| Vicuna-1B & LLaMA-160M | **135.69 Token/s** | **7.17×** | **18.26 mJ/Token** | **4.85×** |
| LLaMA2-7B & LLaMA-160M | **17.82 Token/s** | **4.46×** | **123.41 mJ/Token** | **3.74×** |
| LLaMA3-8B & LLaMA-296M | **14.08 Token/s** | **5.33×** | **151.59 mJ/Token** | **3.95×** |

- 与 SOTA 工作对比：在 LLaMA2-7B 模型上，本工作达到 **17.82 Token/s** 吞吐量与 **123.41 mJ/Token** 能耗，显著优于其他基于 28nm 工艺的 ISSCC/VLSI 加速器（如 [4] 的 5.63 Token/s / 218.25 mJ/Token，[7] 的 6.76 Token/s / 181.48 mJ/Token）。

| 工作 | 工艺节点 | 内存容量 | LLaMA2-7B 吞吐量 | LLaMA2-7B 能耗 |
| :--- | :--- | :--- | :--- | :--- |
| VLSI'25 [6] | 28nm | 24KB SRAM | 5.46 Token/s | 223.69 mJ/Token |
| VLSI'25 [7] | 28nm | 272KB SRAM | 6.76 Token/s | 181.48 mJ/Token |
| ISSCC'25 [4] | 28nm | 384KB SRAM | 5.63 Token/s | 218.25 mJ/Token |
| **This Work** | **55nm + ReRAM** | **3.43MB SRAM + 8MB ReRAM** | **17.82 Token/s** | **123.41 mJ/Token** |

![](images/f4d39f2876e6eb226b282f9701b8c76d6e5d82de20a6ca7509c7944bc336c449.jpg)

---

**消融实验**

- **Local Rotation Unit (LRU)** 消融：
  - 精度对比：在未使用 LRU 时，W4A8 量化导致 Perplexity 严重下降（LLaMA2-7B 达到 8.57）。引入 LRU 后，W4A8 w/ LRU 的 Perplexity 显著恢复（LLaMA2-7B 降至 5.68），与 BF16 基线（5.47）接近。
  - 硬件开销与收益：相比全局旋转，LRU 节省 **92.7%** 面积，并实现 **3.82-to-3.93×** 加速。

| TLM 模型 | BF16 | W4A8 | W4A8 w/ GR | W4A8 w/ LRU |
| :--- | :--- | :--- | :--- | :--- |
| Vicuna-1B | 9.18 | 10.34 | 9.43 | **9.41** |
| LLaMA2-7B | 5.47 | 8.57 | 5.68 | **5.68** |
| LLaMA3-8B | 6.14 | 7.54 | 6.70 | **6.71** |

- **RS-PNM with BVQ** 消融：
  - 机制效果：通过将 DLM 权重聚类为 block-level codebooks 存储于高密度 ReRAM，避免了 DLM 的外部内存访问（EMA）。
  - 性能收益：在 LRU 的基础上，RS-PNM with INT4 BVQ 进一步实现 **1.1-to-1.46×** 加速。
- **Adaptive Parallel SD (APSD) with WDOS** 消融：
  - 机制效果：结合短 Draft Length (DL) 的低拒绝率和长 DL 的高接受率，动态切换 drafting 策略。
  - 性能收益：在 RS-PNM 基础上，APSD 实现 **1.1-to-1.29×** 加速，并将 rejected token ratio 降低 **10-to-14%**。

![](images/8d98fc348c2192be50b13ed830308a24ca0388f5e6f7b35120799051f30bd216.jpg)

---

