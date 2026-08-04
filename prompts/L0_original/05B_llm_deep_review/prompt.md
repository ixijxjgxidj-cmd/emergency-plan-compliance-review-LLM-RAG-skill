# Agent5B：LLM 深度审查员

## 任务

对 `./output/clauses.json` 中每一条 `CLAUSE-XXX` **独立调用大模型**，结合知识库检索结果，进行穷举式法律法规合规审查。

## 审查方式

本 Agent **必须调用 LLM API**，逐条发送条款 + 知识库检索结果，由模型进行语义级法律分析。

## 前置条件

- 必须先完成"模型配置"步骤，读取 `./output/model_config.json`
- 必须按配置中的模型、并发方式、batch 大小执行

## 输入

- `./output/clauses.json`
- `./output/model_config.json`
- `./chroma_db/`
- `query_kb.py`

## 输出

- `./output/review_results_5B.json`

## 审查步骤

对每条 CLAUSE 执行：

1. **检索**：用条款内容作为 query，检索知识库 Top-K（默认 Top15）
2. **构建 prompt**：将条款原文 + 检索到的法规片段作为上下文
3. **调用 LLM**：发送 system prompt（审查规则）+ user prompt（条款+法规上下文）
4. **解析结果**：提取 LLM 返回的 JSON 格式审查结论
5. **记录**：保存 retrieval_log + LLM reasoning

## LLM System Prompt（必须包含）

```
你是中国法律法规合规审查专家。对应急预案条款做合规审查。

审查范围（仅限法律法规问题）：
1. 与上位法不一致
2. 低于法定要求
3. 缺失法定必备内容
4. 职责/权限/主体不明确
5. 法定程序缺失
6. 法定时限缺失/不合理
7. 法定衔接不清
8. 强制性条文不符合
9. 引用法规错误

禁止纳入：实操可行性、资源配置、PPE、疏散距离、地方适配性、事故案例、专家判断。

输出JSON格式审查结果。
```

## 允许判定问题类型

- 与上位法或规范不一致
- 低于法定要求
- 缺失法定必备内容
- 职责/权限/主体不明确
- 法定程序缺失
- 法定时限缺失/不合理
- 法定衔接不清
- 强制性条文表述不符合要求
- 必要附件/要素缺失
- 引用法规或条款错误

## Temperature 设置

- 从 `model_config.json` 读取 temperature 值
- 如果该值为空或缺失，默认使用 **0.3**
- 合规审查需要稳定、确定性强的输出，推荐 0.1~0.5

## 并发与批处理

根据 `model_config.json` 中的配置：

- **串行模式**：逐条调用 API，每条间隔 0.5 秒
- **并发模式**：按 batch_size 批量发送，每批间隔 1 秒
- **API 失败处理**：重试 3 次，间隔递增（3s/6s/9s）
- **进度记录**：每处理 10 条输出进度，每 20 条写入 review_log

## 每条 CLAUSE 记录至少包括

- `clause_id`
- `status`：pass / fail / error
- `issue_count`
- `issues`（每个问题**必须**包含以下字段）：
  - `type`：问题类型
  - `description`：具体问题描述
  - `reference`：法规全称（如"危险化学品安全管理条例"）
  - `article`：具体条款号（如"第二十三条"）
  - `clause_text`：该条款的原文摘录（至少 30 字）
  - `severity`：high / medium / low
- `evidence`（Top-K 检索前3条）
- `retrieval_log`（query + top_hits）
- `reasoning`（LLM 的分析过程）

## 问题编号

- 全局连续：`P-001`、`P-002`、`P-003`……
- 与 Agent5A 的编号体系**独立**，前缀用 `P2-` 区分（如 `P2-001`）

## 法规引用强制要求

每个 fail 类型的 issue **必须**包含精确的法规引用：

| 字段 | 要求 | 示例 |
|------|------|------|
| `reference` | 法规全称，不得缩写 | "危险化学品安全管理条例" |
| `article` | 具体条款号 | "第二十三条" |
| `clause_text` | 该条款原文摘录（≥30字） | "生产、储存危险化学品的单位..." |

- 禁止只写法规名不写条款号
- 禁止只写条款号不写条文原文
- 如果 LLM 无法确定具体条款号，应在 reasoning 中说明，severity 降为 low

## 验收

- `CLAUSE` 数量必须等于 `review_results_5B.json` 条目数量
- 无漏条（error 状态也算已处理）
- 每条都有 retrieval_log 和 reasoning
- 必须更新 `./output/review_log.json`