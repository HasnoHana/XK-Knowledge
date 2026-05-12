# Paxos 算法技术实现原理

## 一、核心问题

Paxos 解决的是**分布式系统中的一致性问题**：在存在节点故障、网络分区、消息延迟/丢失的情况下，如何让多个节点对某个值达成一致。

---

## 二、核心角色

| 角色 | 职责 |
|------|------|
| **Proposer（提议者）** | 提出提案（Proposal），推动决议通过 |
| **Acceptor（接受者）** | 对提案进行投票，决定是否接受 |
| **Learner（学习者）** | 获取最终通过的决议，不参与投票 |

> 一个节点可以同时担任多个角色。

---

## 三、算法核心：两阶段提交

Paxos 的核心是 **Prepare → Promise → Propose → Accept** 的两阶段流程。

### 阶段一：Prepare & Promise

```
Proposer → Acceptor:  Prepare(n)   // n 是全局递增的提案编号
Acceptor → Proposer: Promise(n, [已接受的最高编号提案])
```

**Acceptor 的 Promise 规则：**
- 如果 `n` 大于该 Acceptor 之前承诺过的所有 Prepare 编号，则**承诺不再接受编号小于 n 的提案**，并返回已接受的最高编号提案
- 否则拒绝

### 阶段二：Propose & Accept

```
Proposer → Acceptor:  Accept(n, v)  // v 是提案值
Acceptor → Proposer: Accepted(n, v)
```

**Acceptor 的 Accept 规则：**
- 只有在**没有承诺过更高编号的 Prepare** 时，才接受该提案
- 一旦接受，不可更改

---

## 四、关键约束与安全性

### 1. 提案编号规则
- 编号 `n` 必须全局唯一且单调递增
- 通常由 `(轮次, 节点ID)` 组合生成，确保唯一性和可比较性

### 2. 值的选择策略（关键！）
Proposer 在阶段二发送 `Accept(n, v)` 时，**`v` 不能随意选择**：

> **如果阶段一中 Acceptor 返回了已接受的提案，Proposer 必须使用其中编号最高的那个值作为 `v`**

这保证了：**一旦某个值被多数派接受，后续所有提案都必须使用这个值**。

---

## 五、多数派（Quorum）机制

Paxos 的正确性依赖于**多数派原则**：

- 假设有 `N` 个 Acceptor，**超过半数**（即 `⌊N/2⌋ + 1`）构成多数派
- 任意两个多数派之间**必有交集**
- 因此，不可能存在两个不同的值同时被多数派接受

```
示例：5 个 Acceptor，多数派 = 3
┌─────────┐    ┌─────────┐
│ A1 A2 A3│    │ A3 A4 A5│  ← 两个多数派必有交集（A3）
│ 接受值=X │    │ 接受值=X │    保证一致性
└─────────┘    └─────────┘
```

---

## 六、活锁问题与优化

### 活锁（Livelock）
多个 Proposer 同时发起提案，编号不断递增相互覆盖，导致无法完成：

```
P1: Prepare(1) → OK
P2: Prepare(2) → OK  ← P1 的 Promise 失效
P1: Prepare(3) → OK  ← P2 的 Promise 失效
... 无限循环
```

### 解决方案
1. **随机退避**：失败后随机等待一段时间再重试
2. **Leader 选举**：选出一个唯一的 Proposer（如 Multi-Paxos），避免竞争

---

## 七、Multi-Paxos：从单次决议到日志复制

原始 Paxos 只解决**单个值**的一致性问题。实际系统（如 Raft、Chubby）需要**连续多个值**（日志条目）。

**Multi-Paxos 优化：**
- 选举一个稳定的 Leader（唯一 Proposer）
- Leader 直接执行阶段二（跳过阶段一），批量提交提案
- 只有 Leader 变更时才需要重新走完整两阶段

```
Leader 稳定时：
Client → Leader:  请求写入 value
Leader → Acceptor: 直接 Accept(n, value)  // 跳过 Prepare
Acceptor → Leader: Accepted
Leader → Learner:  广播已提交的日志
```

---

## 八、与 Raft 的关系

| 特性 | Paxos | Raft |
|------|-------|------|
| 可理解性 | 数学抽象，较难理解 | 工程导向，更易理解 |
| Leader | 无强制 Leader | 强 Leader 机制 |
| 日志复制 | Multi-Paxos 扩展 | 原生设计 |
| 工程实现 | Chubby, ZooKeeper | etcd, TiKV, Consul |

> **Raft 本质上是 Multi-Paxos 的一种工程化、易理解的实现**，核心思想一致。

---

## 九、总结

```
┌─────────────────────────────────────────┐
│           Paxos 核心思想                 │
├─────────────────────────────────────────┤
│ 1. 两阶段提交：Prepare + Accept           │
│ 2. 多数派保证：任何两个多数派必有交集      │
│ 3. 值继承规则：已接受的值必须被后续提案继承  │
│ 4. 编号递增：用全局唯一编号推进进度        │
│ 5. Leader 优化：Multi-Paxos 提升效率      │
└─────────────────────────────────────────┘
```

Paxos 是分布式一致性算法的**理论基石**，虽然原始论文抽象难懂，但其思想影响了后续所有共识算法的设计。
