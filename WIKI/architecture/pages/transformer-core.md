# Transformer 核心原理

> Summary: Transformer 通过自注意力、位置编码、多头机制与稳定训练设计，替代 RNN 的顺序建模范式，并成为 BERT、GPT 等模型的基础架构。

## 核心问题与总体架构
- Transformer 试图解决 RNN 顺序计算无法并行以及长距离依赖难以稳定保留的问题。
- 它采用编码器-解码器堆叠结构，编码器负责上下文化表示，解码器在因果掩码约束下自回归生成输出。
- 每层围绕注意力子层与前馈网络组织，并配合残差连接和层归一化。

## 关键机制
- 位置编码为自注意力补充顺序信息。
- 自注意力通过 Q、K、V 计算位置间相关性，并用 sqrt(d_k) 缩放稳定 softmax。
- 多头注意力让模型并行学习不同关系模式；未来掩码与 padding 掩码分别用于防止标签泄露和忽略无意义位置。
- 逐位置前馈网络提供非线性变换，编码器-解码器注意力支持跨序列检索。

## 优势、限制与演进
- Transformer 让远距离信息以更短路径交互，因此更适合建模长距离依赖。
- 标准注意力的代价是复杂度随序列长度平方增长。
- BERT、GPT、Transformer XL 以及 Longformer、BigBird 等都可以视为在这一基础架构上的不同方向演进。

## Sources
- transformer-core-chunk-1
- transformer-core-chunk-2
- transformer-core-chunk-3
- transformer-core-chunk-4
- transformer-core-chunk-5
