# Paxos 共识算法原理

> Summary: Paxos 围绕提案编号、两阶段决议和多数派交集保证一致性，并通过 Leader 化的 Multi-Paxos 将单值决议扩展到日志复制场景。

## Overview
- Paxos 关注分布式系统中的一致性问题。
- 它要在节点故障、网络分区、消息延迟或丢失时，让多个节点仍能对同一个值达成一致。

## 核心角色
- **Proposer**：提出提案并推动决议。
- **Acceptor**：对提案投票并决定是否接受。
- **Learner**：学习最终通过的决议。
- 一个节点可以同时承担多个角色。

## 两阶段决议流程
- 阶段一是 `Prepare(n) -> Promise`。Acceptor 只会对更高编号的 Prepare 作出承诺，并返回已接受的最高编号提案。
- 阶段二是 `Accept(n, v) -> Accepted`。只有在未承诺过更高编号 Prepare 的前提下，Acceptor 才会接受当前提案。
- 一旦提案被接受，值不可更改。

## 安全性约束
- 提案编号必须全局唯一且单调递增。
- 如果阶段一已经返回已接受提案，后续阶段二不能自由选择值，而必须继承其中编号最高的那个值。
- 这个值继承规则保证一旦某个值被多数派接受，后续提案仍会延续同一个值。

## 多数派机制
- 对于 `N` 个 Acceptor，超过半数即 `⌊N/2⌋ + 1` 构成多数派。
- 任意两个多数派必有交集，因此两个不同的值不能同时获得多数派接受。

## 活锁与常见优化
- 多个 Proposer 并发竞争时，Prepare 编号可能不断上升并彼此覆盖，形成活锁。
- 原文给出的缓解方式包括随机退避，以及通过 Leader 选举让系统只保留一个主导 Proposer。

## Multi-Paxos
- 原始 Paxos 只解决单个值的一致性。
- Multi-Paxos 在稳定 Leader 存在时可以跳过阶段一，直接执行阶段二，从而把单次决议扩展到连续日志条目的复制与提交。
- 只有 Leader 变化时，才重新走完整两阶段。

## 与 Raft 的关系
- 原文把 Paxos 与 Raft 并列比较：Paxos 更偏数学抽象，Raft 更偏工程导向且强调强 Leader。
- 原文还直接指出，Raft 本质上可以看作 Multi-Paxos 的一种更易理解的工程化实现。

## Sources
- paxos-chunk-01
- paxos-chunk-02
- paxos-chunk-03
- paxos-chunk-04
- paxos-chunk-05
- paxos-chunk-06
- paxos-chunk-07
- paxos-chunk-08
