# Attention Is All You Need 论文解析

## 0. 论文基本信息

**作者 (Authors)**: Ashish Vaswani, Noam Shazeer, Niki Parmar, et al.

**发表期刊/会议 (Journal/Conference)**: NeurIPS

**发表年份 (Publication Year)**: 2017

**研究机构 (Affiliations)**: Google Brain, Google Research, University of Toronto

---

## 1. 摘要

**目的**
- 提出全新的神经网络架构 **Transformer**，完全基于 **Attention** 机制，彻底摒弃传统的 **RNN** 和 **CNN** 结构。
- 解决传统 **RNN** 模型固有的顺序计算瓶颈，大幅提升模型训练的并行化能力。
- 缩短网络中长距离依赖的路径长度，降低计算复杂度，从而显著减少训练时间并提升序列转导任务的质量。

---

**方法**
- 整体采用 **Encoder-Decoder** 架构，两侧均由 $N=6$ 个相同的层堆叠而成。
- **Encoder** 结构：
  - 每层包含两个子层：**Multi-Head Self-Attention** 和 **Position-wise Feed-Forward Network**。
  - 每个子层均使用 **Residual Connection** 和 **Layer Normalization**。
- **Decoder** 结构：
  - 在 Encoder 的两个子层基础上，插入第三个子层用于执行 **Encoder-Decoder Attention**。
  - **Self-Attention** 子层引入 **Masking** 机制，防止当前位置关注后续位置，确保自回归特性。
- **Scaled Dot-Product Attention**：
  - 计算 Query 与 Key 的点积，除以 $\sqrt{d_k}$ 进行缩放，再通过 **Softmax** 计算权重。
  - 公式：$Attention(Q, K, V) = softmax(\frac{QK^T}{\sqrt{d_k}})V$。
- **Multi-Head Attention**：
  - 将 Q, K, V 通过不同的线性投影映射到 $h=8$ 个子空间并行计算 Attention。
  - 将结果 Concat 后再次进行线性投影，使模型能同时关注不同表示子空间的信息。
- **Positional Encoding**：
  - 使用不同频率的 **Sine** 和 **Cosine** 函数生成位置编码，与 **Embedding** 相加，为无序模型注入序列位置信息。
- 模型架构图：
  ![](images/f7896a22ff43c1f81531754bb9c3f1e738ea4cf8f64eb0a2e62ca12ec9f973de.jpg) *Figure 1: The Transformer - model architecture.*

---

**结果**
- **机器翻译任务**：
  - 在 WMT 2014 English-to-German 任务中，**Transformer (big)** 取得 **28.4 BLEU**，超越当时最佳集成模型 **2.0 BLEU** 以上。
  - 在 WMT 2014 English-to-French 任务中，创下单模型 SOTA 记录 **41.8 BLEU**，训练成本仅为当时最佳模型的 **1/4**。
  - 训练耗时：在 8 个 NVIDIA P100 GPU 上仅需 **3.5 天**。
- 性能与计算成本对比：
  | Model | EN-DE BLEU | EN-FR BLEU | EN-DE Training Cost (FLOPs) | EN-FR Training Cost (FLOPs) |
  | :--- | :--- | :--- | :--- | :--- |
  | ConvS2S Ensemble | 26.36 | 41.29 | $7.7 \cdot 10^{19}$ | $1.2 \cdot 10^{21}$ |
  | GNMT + RL Ensemble | 26.30 | 41.16 | $1.8 \cdot 10^{20}$ | $1.1 \cdot 10^{21}$ |
  | **Transformer (base)** | 27.3 | 38.1 | **$3.3 \cdot 10^{18}$** | - |
  | **Transformer (big)** | **28.4** | **41.8** | $2.3 \cdot 10^{19}$ | - |
- **English Constituency Parsing**：
  - 在 Wall Street Journal (WSJ) 数据集上，**Transformer (4 layers)** 取得 **91.3 F1** 分数，超越 BerkeleyParser。
  - 在半监督设置下达到 **92.1 F1**，证明模型具备强大的跨任务泛化能力。

---

**结论**
- **Transformer** 是首个完全依赖 **Attention** 的序列转导模型，成功替代了传统的 **RNN** 和 **CNN** 层。
- 相比传统架构，**Transformer** 训练速度显著提升，并在多项机器翻译任务中达到 SOTA。
- 模型不仅限于文本任务，未来可扩展至图像、音频、视频等模态。
- 未来研究方向包括探索局部受限的 **Attention** 机制以高效处理大尺度输入输出，以及减少生成过程的顺序依赖。

---

## 2. 背景知识与核心贡献

**研究背景**

- 主导序列转换模型（如机器翻译）主要依赖复杂的 **RNN** 或 **CNN**，包含 **Encoder** 和 **Decoder** 结构。
- 表现最优的模型通常通过 **Attention** 机制连接 **Encoder** 和 **Decoder**。
- **Self-attention**（自注意力）机制已在阅读理解、文本摘要等任务中取得初步成功。

**研究动机**

- **RNN 的固有限制**：计算沿输入输出序列的符号位置逐步进行，生成隐藏状态 $h_t$ 依赖前一状态 $h_{t-1}$。这种序列化特性阻碍了训练样本内部的并行化计算，在长序列下内存限制进一步影响 batching 效率。
- **CNN 的远距离依赖问题**：基于卷积的模型（如 ConvS2S, ByteNet）关联远距离位置的操作数随距离线性或对数增长，增加了学习长距离依赖的难度。
- 现有 **Attention** 机制多与 **RNN** 结合使用，未能彻底解决序列计算的瓶颈。

**核心贡献**

- 提出 **Transformer** 架构：完全摒弃 **RNN** 和 **CNN**，仅依赖 **Attention** 机制（特别是 **Self-attention**）来提取输入输出间的全局依赖关系。
- 设计核心组件：
  - **Scaled Dot-Product Attention**：通过缩放因子 $\frac{1}{\sqrt{d_k}}$ 解决高维下 softmax 梯度消失问题。
  - **Multi-Head Attention**：将 Query、Key、Value 投影到不同子空间并行计算，增强模型捕捉不同表征子空间信息的能力。
- 极高的并行化能力与训练效率：在 8 个 P100 GPU 上仅需 3.5 天即可完成大模型训练。

![](images/f7896a22ff43c1f81531754bb9c3f1e738ea4cf8f64eb0a2e62ca12ec9f973de.jpg) *Figure 1: The Transformer - model architecture.*

- 在机器翻译任务上刷新 SOTA 记录：

| 任务 | 模型 | BLEU 分数 | 训练成本 |
| :--- | :--- | :--- | :--- |
| WMT 2014 English-to-German | **Transformer (big)** | **28.4** | 3.5天 (8 P100 GPUs) |
| WMT 2014 English-to-French | **Transformer (big)** | **41.8** | 远低于文献最优模型 |

- 强大的泛化能力：在 English constituency parsing 任务中，无论数据量大小，均表现出色，甚至超越特定任务调优的 RNN 序列模型。

---

## 3. 核心技术和实现细节

### 0. 技术架构概览

**核心架构概述**
- **Transformer** 是一种基于 **Encoder-Decoder** 架构的序列转换模型。
- 完全摒弃了传统的 **RNN** 和 **CNN** 结构，**仅依赖 Attention 机制**处理输入和输出序列间的全局依赖关系。
- 允许高度并行化计算，显著减少训练时间。

![](images/f7896a22ff43c1f81531754bb9c3f1e738ea4cf8f64eb0a2e62ca12ec9f973de.jpg) *Figure 1: The Transformer - model architecture.*

---

**Encoder 结构**
- 由 **N=6** 个相同的层堆叠而成。
- 每层包含两个核心 Sub-layer：
  - **Multi-Head Self-Attention** 机制。
  - **Position-wise Feed-Forward Network** (FFN)。
- 每个 Sub-layer 均采用 **Residual Connection** 和 **Layer Normalization**，公式为 $LayerNorm(x + Sublayer(x))$。
- 所有 Sub-layer 及 Embedding 层的输出维度均为 **$d_{model} = 512$**。

---

**Decoder 结构**
- 同样由 **N=6** 个相同的层堆叠而成。
- 每层包含三个 Sub-layer：
  - **Masked Multi-Head Self-Attention**：通过 Masking 防止当前位置关注后续位置，确保位置 $i$ 的预测仅依赖于位置小于 $i$ 的已知输出，维持 **Auto-regressive** 特性。
  - **Encoder-Decoder Attention**：Query 来自前一 Decoder 层，Key 和 Value 来自 Encoder 输出，实现解码器对编码器全局信息的提取。
  - **Position-wise Feed-Forward Network** (FFN)。
- 同样应用 **Residual Connection** 和 **Layer Normalization**。

---

**核心组件：Attention 机制**
- **Scaled Dot-Product Attention**：
  - 输入为 Query (Q)、Key (K) 和 Value (V)。
  - 计算公式：$Attention(Q, K, V) = softmax(\frac{QK^T}{\sqrt{d_k}})V$。
  - 引入缩放因子 **$\frac{1}{\sqrt{d_k}}$** 抵消大维度下点积过大导致的 Softmax 梯度消失问题。
- **Multi-Head Attention**：
  - 将 Q、K、V 通过线性投影映射到 **h=8** 个不同的表示子空间并行计算。
  - 每个头的维度 **$d_k = d_v = d_{model}/h = 64$**。
  - 将各头结果 Concat 后再次进行线性投影，使模型能联合关注不同位置的不同表示子空间信息。

---

**Positional Encoding**
- 由于模型无 RNN/CNN，需额外注入序列的绝对或相对位置信息。
- 采用不同频率的 **Sine** 和 **Cosine** 函数生成位置编码：
  - $PE_{(pos, 2i)} = sin(pos / 10000^{2i/d_{model}})$
  - $PE_{(pos, 2i+1)} = cos(pos / 10000^{2i/d_{model}})$
- 位置编码与 Embedding 维度相同，直接相加注入模型，使模型能轻松学习相对位置关系。

---

**模型基础参数规格**

| 参数 | 值 |
|---|---|
| 层数 (N) | 6 |
| 模型维度 ($d_{model}$) | 512 |
| 前馈网络维度 ($d_{ff}$) | 2048 |
| Attention 头数 (h) | 8 |
| 每头维度 ($d_k, d_v$) | 64 |
| Dropout 概率 ($P_{drop}$) | 0.1 |
| Label Smoothing ($\epsilon_{ls}$) | 0.1 |

### 1. Scaled Dot-Product Attention

**核心概念与原理**

- **Scaled Dot-Product Attention** 是一种将 **Query** 和一组 **Key-Value** 对映射到输出的注意力机制。
- 输出是对 **Values** 的加权求和。
- 权重通过 Query 与对应 Key 的兼容性函数计算得出。

![](images/da0cb167628b8c102175cfb8905c35ca892193b2792f27c2ecc67f25752338a5.jpg) *Figure 2: (left) Scaled Dot-Product Attention. (right) Multi-Head Attention consists of several attention layers running in parallel.*

---

**算法流程与公式**

- 计算点积：Query 与所有 Keys 进行点积运算。
- 缩放处理：每个点积结果除以 $\sqrt{d_k}$。
- 归一化：应用 **softmax** 函数将结果转化为概率分布，获得权重。
- 加权求和：将权重与对应的 Values 相乘并求和，得到最终输出。
- 核心公式：$Attention(Q, K, V) = softmax(\frac{QK^T}{\sqrt{d_k}})V$

---

**参数设置与矩阵化实现**

- **Queries** 和 **Keys** 的维度设为 $d_k$。
- **Values** 的维度设为 $d_v$。
- 并行计算：将多个 Queries 打包为矩阵 $Q$，Keys 和 Values 打包为矩阵 $K$ 和 $V$。
- 利用高度优化的矩阵乘法代码实现并行计算，提升速度和空间效率。

---

**缩放因子的必要性**

- 当 $d_k$ 较小时，Dot-Product Attention 与 Additive Attention 性能相当。
- 当 $d_k$ 较大时，点积结果数值幅度变大，将 softmax 函数推入梯度极小的区域。
- 除以 $\sqrt{d_k}$ 抵消大数值效应，防止梯度消失，稳定训练过程。

---

**输入输出关系与整体作用**

- 输入：矩阵 $Q$ (Queries)、$K$ (Keys)、$V$ (Values)。
- 输出：维度为 $d_v$ 的注意力加权表示矩阵。
- 在 Transformer 中的作用：
  - 作为 **Multi-Head Attention** 的基础并行计算单元。
  - 在 **Encoder-Decoder Attention** 中，Query 来自前一层 Decoder，Key 和 Value 来自 Encoder 输出，实现跨序列交互。
  - 在 **Self-Attention** 中，Q, K, V 均来自同一序列的前一层输出，捕获序列内部的全局依赖关系。
  - 在 Decoder 的 Self-Attention 中，通过 Masking 机制屏蔽后续位置，保证自回归特性。

---

**对比分析**

| 特性 | Scaled Dot-Product Attention | Additive Attention |
| :--- | :--- | :--- |
| **兼容性计算** | 矩阵点积 | 单隐藏层前馈网络 |
| **计算速度** | 快 (基于矩阵乘法优化) | 较慢 |
| **空间效率** | 高 | 较低 |
| **大 $d_k$ 表现** | 需缩放因子，否则性能下降 | 表现稳定 |

### 2. Multi-Head Attention

**核心观点**
- **Multi-Head Attention** 打破了单头注意力机制的限制，允许模型在不同的位置联合关注来自不同表示子空间的信息。
- 单一注意力头通过平均化操作会抑制模型捕捉多样化特征的能力，而多头机制通过并行投影有效缓解了这一问题。

---

**实现原理与算法流程**
- **线性投影**：不直接在 $d_{\text{model}}$ 维度上执行单一 Attention，而是将 **Query**、**Key** 和 **Value** 分别使用不同的学习参数矩阵线性投影 $h$ 次。
- **并行计算**：在每个投影后的子空间中并行执行 **Scaled Dot-Product Attention**，产生 $h$ 个维度为 $d_v$ 的输出。
- **特征拼接**：将这 $h$ 个注意力头的输出在特征维度上进行 **Concat** 操作。
- **最终线性映射**：将拼接后的结果乘以输出权重矩阵 $W^O$，得到最终的注意力输出。
- **公式表达**：
  - $\text{MultiHead}(Q, K, V) = \text{Concat}(\text{head}_1, ..., \text{head}_h) W^O$
  - $\text{head}_i = \text{Attention}(Q W_i^Q, K W_i^K, V W_i^V)$

![](images/da0cb167628b8c102175cfb8905c35ca892193b2792f27c2ecc67f25752338a5.jpg) *Figure 2: (left) Scaled Dot-Product Attention. (right) Multi-Head Attention consists of several attention layers running in parallel.*

---

**参数设置与维度计算**
- 论文中采用 $h = 8$ 个并行注意力头。
- 每个头的维度设为 $d_k = d_v = d_{\text{model}} / h = 64$。
- 由于每个头的维度降低，多头机制的总计算成本与单头全维度 Attention 基本一致。
- **核心参数矩阵维度**：

| 参数矩阵 | 维度 | 说明 |
| :--- | :--- | :--- |
| $W_i^Q$ | $\mathbb{R}^{d_{\text{model}} \times d_k}$ | Query 的第 $i$ 个投影矩阵 |
| $W_i^K$ | $\mathbb{R}^{d_{\text{model}} \times d_k}$ | Key 的第 $i$ 个投影矩阵 |
| $W_i^V$ | $\mathbb{R}^{d_{\text{model}} \times d_v}$ | Value 的第 $i$ 个投影矩阵 |
| $W^O$ | $\mathbb{R}^{h d_v \times d_{\text{model}}}$ | 最终输出的线性映射矩阵 |

---

**输入输出关系**
- **输入**：统一的 **Query** ($Q$)、**Key** ($K$) 和 **Value** ($V$) 矩阵，基础维度均为 $d_{\text{model}} = 512$。
- **中间态**：$h$ 组维度为 $64$ 的子空间注意力输出。
- **输出**：维度为 $d_{\text{model}} = 512$ 的融合表示矩阵，直接传递给后续的 Feed-Forward Network 或下一层 Encoder/Decoder。

---

**在整体架构中的作用**
- **Encoder-Decoder Attention**：
  - **Query** 来自前一个 Decoder 层的输出。
  - **Key** 和 **Value** 来自 Encoder 堆栈的最终输出。
  - 作用：使 Decoder 的每个位置都能关注到输入序列的所有位置。
- **Encoder Self-Attention**：
  - **Query**、**Key**、**Value** 均来自前一 Encoder 层的输出。
  - 作用：允许 Encoder 中的每个位置关注前一层的所有位置，捕捉全局依赖。
- **Decoder Self-Attention**：
  - **Query**、**Key**、**Value** 均来自前一 Decoder 层的输出。
  - 作用：允许 Decoder 关注当前位置及之前的位置。
  - 特殊机制：引入 **Masking** 操作，将 softmax 输入中对应非法连接（未来位置）的值设为 $-\infty$，确保自回归特性，防止向左信息流。

### 3. Positional Encoding

**核心动机与整体作用**

- Transformer 架构完全摒弃了 RNN 和 CNN，这种设计虽然带来了极高的并行化能力，但也导致模型本身失去了捕捉序列顺序的能力。
- 为了使模型能够利用序列的顺序信息，必须在输入端注入 token 的相对或绝对位置信息。
- Positional Encoding 与 Input Embedding 具有相同的维度（**$d_{model} = 512$**），两者直接相加，将语义信息与位置信息融合后作为 encoder 和 decoder 堆栈底部的输入。

![](images/f7896a22ff43c1f81531754bb9c3f1e738ea4cf8f64eb0a2e62ca12ec9f973de.jpg) *Figure 1: The Transformer - model architecture.*

---

**实现原理与算法流程**

- 论文采用不同频率的 sine 和 cosine 函数来生成固定的 Positional Encoding，而非通过训练学习的参数。
- 具体的数学公式如下：
  - $PE_{(pos, 2i)} = sin(pos / 10000^{2i / d_{model}})$
  - $PE_{(pos, 2i+1)} = cos(pos / 10000^{2i / d_{model}})$
- 公式参数说明：

| 参数 | 含义 | 说明 |
| :--- | :--- | :--- |
| **pos** | Position | token 在序列中的绝对位置，取值范围为 $[0, L-1]$ |
| **i** | Dimension | 维度的索引，取值范围为 $[0, d_{model}/2 - 1]$ |
| **$d_{model}$** | Model Dimension | 模型隐藏层维度，本文设定为 **512** |

- 波长特性：每个维度对应一个正弦波，波长的范围形成从 $2\pi$ 到 $10000 \cdot 2\pi$ 的几何级数。
- 算法流程：
  - 针对输入序列的每个位置 **pos**，计算其对应的正弦和余弦值。
  - 偶数维度使用 sin 函数计算，奇数维度使用 cos 函数计算。
  - 生成一个与 Input Embedding 形状完全一致的 Positional Encoding 矩阵。

---

**输入输出关系**

- 输入：
  - Input Embedding：通过查表得到的 token 语义向量表示，维度为 $[L, d_{model}]$。
  - Positional Encoding：根据位置公式计算出的位置向量表示，维度为 $[L, d_{model}]$。
- 处理：执行逐元素相加操作（$Embedding + PE$）。
- 输出：融合了语义与位置信息的最终输入向量，维度保持 $[L, d_{model}]$ 不变，直接送入后续的 Multi-Head Attention 层。

---

**设计优势与实验对比**

- 相对位置表达能力：作者假设这种正弦/余弦形式能让模型轻松学习到相对位置信息。因为对于任何固定的偏移量 $k$，$PE_{pos+k}$ 都可以表示为 $PE_{pos}$ 的线性函数。
- 长度外推能力：由于正弦和余弦函数的连续性，模型在理论上可以处理比训练时遇到的序列长度更长的输入。
- 实验验证：
  - 论文在 Table 3 的 row (E) 中对比了 learned positional embeddings。
  - 实验结果表明，learned 版本与 sinusoidal 版本产生了几乎相同的结果。
  - 最终选择 sinusoidal 版本的核心考量在于其对未知长度的外推潜力。

### 4. Position-wise Feed-Forward Networks

**核心概念与原理**

- Position-wise Feed-Forward Networks (FFN) 是 Transformer 架构中 Encoder 和 Decoder 的核心组件之一。
- **Position-wise** 意味着该网络对输入序列的每个 position 独立且相同地处理。
- 该模块不涉及跨 position 的信息交互，序列中各 token 的特征提取完全并行。
- 结构上等价于两个 kernel size 为 1 的卷积层。

---

**算法流程与公式**

- FFN 由两次 Linear Transformation 和一个非线性激活函数组成。
- 核心计算公式为：
  - **FFN(x) = max(0, xW₁ + b₁)W₂ + b₂**
- 算法步骤拆解：
  - **第一层映射**：输入向量 x 乘以权重矩阵 **W₁** 并加上偏置 **b₁**，将维度从 **d_model** 映射到 **d_ff**。
  - **非线性激活**：通过 **ReLU** 激活函数 (max(0, ·)) 引入非线性能力。
  - **第二层映射**：将激活后的结果乘以权重矩阵 **W₂** 并加上偏置 **b₂**，将维度从 **d_ff** 恢复为 **d_model**。

---

**参数设置与维度变换**

- 输入与输出维度保持一致，确保残差连接 的顺利进行。
- 内部隐藏层维度 **d_ff** 通常远大于模型维度 **d_model**，形成先升维、后降维的瓶颈结构，以提取更高维度的特征表达。
- 参数共享特性：
  - 同一层内，所有 position 共享相同的 **W₁, b₁, W₂, b₂** 参数。
  - 不同层之间（例如 Encoder 的第1层与第2层），FFN 的参数完全独立。

| 组件 | 输入维度 | 权重矩阵维度 | 输出维度 | 激活函数 |
| :--- | :--- | :--- | :--- | :--- |
| 第一层 Linear | **d_model** (512) | **d_model × d_ff** (512×2048) | **d_ff** (2048) | **ReLU** |
| 第二层 Linear | **d_ff** (2048) | **d_ff × d_model** (2048×512) | **d_model** (512) | 无 |

---

**在整体架构中的作用**

![](images/f7896a22ff43c1f81531754bb9c3f1e738ea4cf8f64eb0a2e62ca12ec9f973de.jpg) *Figure 1: The Transformer - model architecture.*

- **输入输出关系**：
  - 接收上一个子层（Multi-Head Attention 或 Masked Multi-Head Attention）经过残差连接和 LayerNorm 处理后的输出。
  - 输出维度相同的特征矩阵，继续传递给下一个残差连接和 LayerNorm 模块。
- **功能定位**：
  - **Attention 机制**负责捕捉序列中 token 之间的全局依赖关系（跨 position 交互）。
  - **FFN** 负责对每个 position 的特征向量进行深度非线性变换，增强模型的表征能力。
  - 两者交替堆叠，使得 Transformer 既能理解上下文语境，又能提取丰富的局部特征。

### 5. Residual Connection and Layer Normalization

**核心概念解析**

- **Residual Connection**（残差连接）：借鉴自 ResNet 的核心思想，通过建立跨层的直接连接，允许梯度在反向传播时绕过非线性变换层，直接流向网络底层。
- **Layer Normalization**（层归一化）：对同一个样本的所有特征维度进行均值为0、方差为1的标准化处理，独立于 batch size，有效稳定深层网络的训练过程。

---

**算法流程与数学表达**

在 Transformer 的每一个 Sub-layer（包括 Multi-Head Attention 和 Feed-Forward Network）中，数据流转严格遵循以下顺序：

- **输入接收**：接收上一层的输出向量 $x$。
- **Sub-layer 计算**：将 $x$ 送入当前 Sub-layer 执行核心运算，得到中间输出 $Sublayer(x)$。
- **残差相加**：将原始输入 $x$ 与 Sub-layer 的输出进行逐元素相加，公式为 $x + Sublayer(x)$。
- **层归一化**：对相加后的结果应用 Layer Normalization，最终输出表达式为：
  - $Output = LayerNorm(x + Sublayer(x))$

在模型架构图（Figure 1）中，这一组合操作被直观地标记为 **Add & Norm** 模块。

![](images/f7896a22ff43c1f81531754bb9c3f1e738ea4cf8f64eb0a2e62ca12ec9f973de.jpg) *Figure 1: The Transformer - model architecture.*

---

**参数设置与维度约束**

为了确保残差连接中的逐元素加法（$x + Sublayer(x)$）在数学上成立，模型对内部特征维度进行了严格的统一约束：

| 组件名称 | 维度参数 | 说明 |
| :--- | :--- | :--- |
| **Embedding 层** | $d_{model} = 512$ | 输入序列转换为连续表示的基准维度 |
| **Encoder Sub-layers** | $d_{model} = 512$ | Multi-Head Attention 与 FFN 的输出维度 |
| **Decoder Sub-layers** | $d_{model} = 512$ | Masked Attention 与 Cross-Attention 的输出维度 |
| **Add & Norm 输入/输出** | $d_{model} = 512$ | 保证 $x$ 与 $Sublayer(x)$ 维度一致 |

- 所有 Sub-layer 以及 Embedding 层的输出维度均被强制设为 **$d_{model} = 512$**。
- 这种统一的维度设计避免了引入额外的投影矩阵，简化了网络结构并降低了计算开销。

---

**输入输出关系及在整体中的作用**

**输入输出关系**

- **输入**：前一层的输出张量 $x$（维度为 $[batch\_size, seq\_len, d_{model}]$）。
- **输出**：经过归一化的同维度张量 $Output$（维度保持为 $[batch\_size, seq\_len, d_{model}]$）。
- **特性**：无论 Sub-layer 内部（如 Attention 矩阵计算或 FFN 的 2048 维扩展）如何复杂，**Add & Norm** 模块始终维持输入输出张量的形状和维度不变。

**在整体架构中的作用**

- **支撑深层堆叠**：Transformer 的 Encoder 和 Decoder 各自堆叠了 $N=6$ 个相同的层。Residual Connection 确保了信息能够无损地穿透 6 层结构，避免了深层网络中的梯度消失和退化问题。
- **稳定训练过程**：Self-Attention 机制对输入向量的尺度极其敏感。Layer Normalization 将激活值的分布稳定在合理范围内，防止 Softmax 函数进入梯度极小的饱和区，使得模型能够使用较大的学习率进行快速收敛。
- **保留位置信息**：由于 Transformer 完全摒弃了 RNN，序列的顺序信息仅由 Positional Encoding 提供。残差连接确保了底层的 Positional Encoding 信号能够直接传递到高层的 Attention 计算中，防止位置信息在网络加深时被稀释或覆盖。


---

## 4. 实验方法与实验结果

**实验设置**

- **训练数据**：
  - **WMT 2014 English-German**：包含约 **450万** 句子对，使用 byte-pair encoding，共享词表大小约 **37,000** tokens。
  - **WMT 2014 English-French**：包含 **3600万** 句子对，word-piece 词表大小为 **32,000** tokens。
  - **Batching 策略**：按近似序列长度分批，每个 training batch 包含约 **25,000** 个 source tokens 和 **25,000** 个 target tokens。
- **硬件与耗时**：
  - 硬件配置：单机搭载 **8 张 NVIDIA P100 GPUs**。
  - **Base model**：训练 **100,000** 步，耗时约 **12 小时**（单步约 0.4 秒）。
  - **Big model**：训练 **300,000** 步，耗时约 **3.5 天**（单步约 1.0 秒）。
- **优化器与学习率**：
  - 采用 **Adam optimizer**，参数设为 $\beta_1 = 0.9$, $\beta_2 = 0.98$, $\epsilon = 10^{-9}$。
  - 学习率调度公式：$lrate = d_{model}^{-0.5} \cdot \min(step\_num^{-0.5}, step\_num \cdot warmup\_steps^{-1.5})$。
  - **Warmup 阶段**：前 **4,000** 步线性增加学习率，之后按步数倒数的平方根比例衰减。
- **正则化策略**：
  - **Residual Dropout**：应用于每个 sub-layer 的输出及其输入相加之前，以及 encoder 和 decoder 中的 embeddings 与 positional encodings 之和。Base model 的 dropout 率为 **$P_{drop} = 0.1$**。
  - **Label Smoothing**：设值为 **$\epsilon_{ls} = 0.1$**。此策略会略微损害 perplexity，但能提升 accuracy 和 BLEU score。
- **推理设置**：
  - Base model 平均最后 **5 个** checkpoints（每 10 分钟保存一次），Big model 平均最后 **20 个** checkpoints。
  - 解码采用 **Beam search**，beam size 为 **4**，length penalty $\alpha = 0.6$。
  - 最大输出长度设为输入长度 + 50，并在可能时提前终止。

---

**机器翻译结果数据**

在 WMT 2014 翻译任务中，Transformer 展现了压倒性的性能优势与极低的训练成本。

| Model | EN-DE BLEU | EN-FR BLEU | EN-DE Training Cost (FLOPs) | EN-FR Training Cost (FLOPs) |
| :--- | :--- | :--- | :--- | :--- |
| ByteNet | 23.75 | - | - | - |
| Deep-Att + PosUnk | - | 39.2 | - | $1.0 \cdot 10^{20}$ |
| GNMT + RL | 24.6 | 39.92 | $2.3 \cdot 10^{19}$ | $1.4 \cdot 10^{20}$ |
| ConvS2S | 25.16 | 40.46 | $9.6 \cdot 10^{18}$ | $1.5 \cdot 10^{20}$ |
| MoE | 26.03 | 40.56 | $2.0 \cdot 10^{19}$ | $1.2 \cdot 10^{20}$ |
| GNMT + RL Ensemble | 26.30 | 41.16 | $1.8 \cdot 10^{20}$ | $1.1 \cdot 10^{21}$ |
| ConvS2S Ensemble | 26.36 | 41.29 | $7.7 \cdot 10^{19}$ | $1.2 \cdot 10^{21}$ |
| **Transformer (base model)** | **27.3** | **38.1** | **$3.3 \cdot 10^{18}$** | - |
| **Transformer (big)** | **28.4** | **41.8** | **$2.3 \cdot 10^{19}$** | - |

- **English-to-German 任务**：**Transformer (big)** 取得 **28.4 BLEU**，超越此前最佳模型（包含集成模型）**2.0 BLEU** 以上。即使是 base model 也以极低的计算成本超越了所有此前的单模型甚至集成模型。
- **English-to-French 任务**：**Transformer (big)** 取得 **41.8 BLEU**，确立了新的单模型 SOTA，且训练成本不到此前最佳模型的 **1/4**。

---

**成分句法分析结果数据**

为验证模型的泛化能力，论文在 Wall Street Journal (WSJ) 数据集上进行了 English constituency parsing 实验。

| Parser | Training Setting | WSJ 23 F1 |
| :--- | :--- | :--- |
| Vinyals & Kaiser el al. (2014) | WSJ only, discriminative | 88.3 |
| Petrov et al. (2006) | WSJ only, discriminative | 90.4 |
| Zhu et al. (2013) | WSJ only, discriminative | 90.4 |
| Dyer et al. (2016) | WSJ only, discriminative | 91.7 |
| **Transformer (4 layers)** | **WSJ only, discriminative** | **91.3** |
| Zhu et al. (2013) | semi-supervised | 91.3 |
| Huang & Harper (2009) | semi-supervised | 91.3 |
| McCloskey et al. (2006) | semi-supervised | 92.1 |
| Vinyals & Kaiser el al. (2014) | semi-supervised | 92.1 |
| **Transformer (4 layers)** | **semi-supervised** | **92.1** |
| Luong et al. (2015) | semi-supervised multi-task | 92.7 |
| Dyer et al. (2016) | generative | 93.0 |
| Dyer et al. (2016) | generative | 93.3 |

- 使用 4 层 Transformer（$d_{model} = 1024$），在仅使用 WSJ 40K 句子训练时，达到 **91.3 F1**，超越了此前的 BerkeleyParser。
- 在半监督设置下（17M 句子），达到 **92.1 F1**。
- 尽管缺乏任务特定的调优，Transformer 表现出极强的跨任务泛化能力。

---

**消融实验**

以 base model 在 newstest2013 (EN-DE dev) 上的表现为基准，通过控制变量评估各组件的重要性。

| 变体 | N | $d_{model}$ | $d_{ff}$ | h | $d_k$ | $d_v$ | $P_{drop}$ | $\epsilon_{ls}$ | train steps | PPL (dev) | BLEU (dev) | params ($\times 10^6$) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **base** | 6 | 512 | 2048 | 8 | 64 | 64 | 0.1 | 0.1 | 100K | 4.92 | 25.8 | 65 |
| (A) | | | | 1 | 512 | 512 | | | | 5.29 | 24.9 | |
| (A) | | | | 4 | 128 | 128 | | | | 5.00 | 25.5 | |
| (A) | | | | 16 | 32 | 32 | | | | 4.91 | 25.8 | |
| (A) | | | | 32 | 16 | 16 | | | | 5.01 | 25.4 | |
| (B) | | | | | 16 | 16 | | | | 5.16 | 25.1 | 58 |
| (B) | | | | | 32 | 32 | | | | 5.01 | 25.4 | 60 |
| (C) | 2 | 256 | 1024 | | 32 | 32 | | | | 6.11 | 23.7 | 36 |
| (C) | 4 | 256 | 1024 | | 32 | 32 | | | | 5.19 | 25.3 | 50 |
| (C) | | 1024 | 4096 | | 128 | 128 | | | | 4.88 | 25.5 | 80 |
| (C) | | 1024 | | | 64 | 64 | | | | 5.75 | 24.5 | 168 |
| (D) | | | | | | | 0.0 | | | 4.75 | 26.2 | |
| (D) | | | | | | | 0.2 | | | 5.77 | 24.6 | 90 |
| (D) | | | | | | | | 0.0 | | 4.95 | 25.5 | |
| (D) | | | | | | | | 0.2 | | 4.67 | 25.7 | |
| (E) | \multicolumn{6}{l}{positional embedding instead of sinusoids} | | | | 4.92 | 25.7 | |
| **big** | 6 | 1024 | 4096 | 16 | | | 0.3 | | 300K | 4.33 | 26.4 | 213 |

- **Multi-Head Attention 的影响 (变体 A)**：
  - 保持计算量不变，改变 head 数量 $h$。
  - 单头注意力比最佳设置差 **0.9 BLEU**。
  - head 数量过多（如 32）也会导致质量下降。
  - 结论：合适的 head 数量能让模型在不同表示子空间联合关注信息，多头机制至关重要。
- **Attention Key Size 的影响 (变体 B)**：
  - 减小 $d_k$ 会显著损害模型质量。
  - 结论：判断 compatibility 需要足够的维度，说明 dot product 可能并非总是最优的 compatibility function，更复杂的函数或许有益。
- **模型规模的影响 (变体 C)**：
  - 增大模型维度（$d_{model}$ 从 512 增至 1024）和层数能提升性能。
  - 替换 $d_{ff}$ 会降低效果。
  - 结论：更大的模型表现更好。
- **正则化的影响 (变体 D)**：
  - 移除 Dropout ($P_{drop} = 0.0$) 会导致过拟合，BLEU 略有上升但 PPL 显著恶化。
  - 调整 Label Smoothing 参数表明，适度的 smoothing ($\epsilon_{ls} = 0.1$) 能在 PPL 和 BLEU 间取得最佳平衡。
- **Positional Encoding 的选择 (变体 E)**：
  - 使用 learned positional embeddings 替代 sinusoidal 版本，结果几乎一致。
  - 论文最终采用 sinusoidal 版本，因其具备外推到比训练时更长序列的潜力。

---

**注意力可视化分析**

论文通过可视化 encoder self-attention 的权重分布，证明了 Transformer 不仅性能强，且具备一定的可解释性。

![](images/57e3ad00e7c57fe0dc66b468b013f2fcf447ef78a7d2ee01be8b434fe6ef0669.jpg)

- **长距离依赖捕捉**：在 Layer 5 的 self-attention 中，针对动词 "making" 的注意力头清晰地关注到了远处的 "more difficult"，成功学习了 "making...more difficult" 的句法结构。

![](images/1678a839f4e6f07663c6d0c31aa1125d433138f2e6617aae82d039d1529967ea.jpg) *Figure 4: Two attention heads, also in layer 5 of 6, apparently involved in anaphora resolution. Top: Full attentions for head 5. Bottom: Isolated attentions from just the word ‘its’ for attention heads 5 and 6. Note that the attentions are very sharp for this word.*

- **指代消解**：某些注意力头学会了执行 anaphora resolution。对于单词 "its"，注意力头 5 和 6 展现出了极其尖锐的注意力分布，准确指向了其指代的名词。

![](images/b616696f63c30ad27de5f095b0cac5975742209d1231c70057510010187c1512.jpg)

- **句法结构学习**：不同的注意力头展现出了明显不同的行为模式，某些头的行为与句子的语法结构高度相关，表明模型能够自发学习到潜在的语法规则。

---

