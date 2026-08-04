# Agent5B：LLM 深度审查员

## 任务

对 `./output/clauses.json` 每一条 `CLAUSE` **独立调用大模型**，结合知识库检索结果，做穷举式法律法规合规审查。定位是"深度挖掘"，发现规则匹配难以覆盖的隐性问题（职责不清、程序缺失、衔接不全、权限越位、义务降格等）。

## 前置条件

- 默认（模式 A）**不需要** `./output/model_config.json`，不需要外部 API key，直接用本环境的子智能体能力。
- 仅当用户为 5B 指定了另外的模型或另给了 key（模式 B）时，才必须先完成"模型配置"并读取 `./output/model_config.json`，按其中的模型、并发方式、batch 大小、temperature 执行。

## 输入

- `./output/clauses.json`
- `./output/plan_profile.json`
- `./output/model_config.json`（**仅模式 B 需要**）
- `./chroma_db/`、`query_kb.py`

## 输出

- `./output/review_results_5B.json`
- `./output/5b_batches/batch_NN.json`、`./output/5b_results/result_NN.json`（分批执行时的中间产物，必须保留）

## 执行模式（开始前必须确定并记入 `review_log.json` 的 `agent5b_mode`）

模式由**用户是否自带模型**决定，与条款数无关：

| 情形 | 模式 |
|------|------|
| 用户未声明模型（默认） | **模式 A：本环境子智能体分批** |
| 用户明确为 5B 指定另外的模型，或提供了 `api_key` / `base_url` / `model_name` | **模式 B：外部模型 API 逐条调用** |

判断依据：用户是否给出了 5B 专用的模型/密钥。**不要主动索要 API key**——默认按模式 A 执行即可；用户没提模型这件事就是选择了模式 A。

### 模式 A（默认）：本环境子智能体分批

单一上下文逐条审上百条会耗尽上下文，导致后半程质量塌陷或直接偷懒。改为分批派发：

1. 按 `batch_size`（默认 10）把 `clauses.json` 切分为 N 批，落盘 `./output/5b_batches/batch_01.json` … `batch_NN.json`。每个 batch 文件自带该批条款原文 + 各条的 Top20 检索结果，**使子智能体无需继承主上下文即可独立工作**。
2. 逐批派发独立子智能体，每个子智能体只看自己那一批，审完落盘 `./output/5b_results/result_NN.json` 后即结束，释放上下文。
3. 主流程校验该批结果条数 == 该批条款数，然后派发下一批。
4. 全部批次完成后合并为 `review_results_5B.json`，并校验总条数 == `clauses.json` 条数。

**断点续跑**：`result_NN.json` 已存在且条数合法的批次直接跳过，只补缺失批次。这让中断可恢复，不必从头重跑。

**批次完整性校验（必做）**：合并前逐批比对 `batch_NN.json` 的 `clause_id` 集合与 `result_NN.json` 的 `clause_id` 集合，任何缺失必须补审，不得静默合并。

子智能体派发时必须把本文件的"LLM System Prompt""检查矩阵""每条 CLAUSE 记录"三节完整传入，不得只传条款让其自由发挥。

### 模式 B：用户自带模型 / 另给 key

见下方"模式 B 完整规格"一节。该节是原始 5B 规格的完整还原，用户自带模型时**按该节执行**，不套用模式 A 的分批流程。

---

# 模式 A 规格（默认路径）

以下各节（"审查步骤"至"编号"）是**模式 A** 的执行规格。用户自带模型时请直接跳到文档末尾的"模式 B 完整规格"。

## 审查步骤

对每条 CLAUSE：

1. **检索**：以条款文本为 query 检索知识库 **Top20**（与 5A 同档，不得降为 Top3/Top5），优先 `plan_type_relevance` 为核心/相关的法规。
2. **构建 prompt**：预案画像（类型/层级/主体/事件类别）+ 条款原文 + 上下文 + 检索到的法规条文片段。
3. **调用 LLM**。
4. **解析结果**：提取 JSON 审查结论。
5. **记录** `retrieval_log` 与 `reasoning`。

`retrieval_log` 对每条 CLAUSE **必填**，不得缺项——实跑中 137 条里有 10 条缺 `retrieval_log`，等于无法证明这些条款真的检索过知识库。


## LLM System Prompt（必须包含以下要点）

```
你是中国应急预案法律法规合规审查专家。你要审查的预案类型是：{plan_category}，
编制层级：{plan_level}，编制主体：{issuing_body}，事件类别：{event_type}。

审查范围仅限法律法规问题：
1. 与上位法/强制性标准/上级预案不一致
2. 低于法定要求（含把"应当/必须/不得"降格为"可以/宜/尽量"）
3. 缺失法定必备内容
4. 职责/权限/主体不明确
5. 超越编制主体法定职权
6. 法定程序缺失（评审、公布、备案、修订、启动/终止批准等）
7. 法定时限缺失或不合理
8. 与上级预案、同级相关预案、下级预案衔接不清
9. 强制性条文表述不符合要求
10. 必要附件/要素缺失
11. 引用法规名称、文号、年份或条款号错误，或引用已废止/已修订版本

严禁纳入：实操可行性、资源配置是否合理、PPE 是否合理、疏散距离是否科学、
地方适配性、事故案例经验、专家经验判断、写作风格、错别字。

只能使用我提供的法规条文片段作为依据。若提供的片段不足以支撑某个判断，
必须在 reasoning 中说明"依据不足"，并把该问题 severity 降为 low，
禁止凭记忆编造法规条文、条款号或文号。

每个问题必须逐字摘出预案中出错的那句话，填入 quoted_text（≥10 字，必须能在
我提供的条款原文中精确匹配，不得改写或概括）。属于"应当写而没写"的问题，
摘出本应包含该内容却没有的那句话。指不出具体文字的，不要作为问题输出。

每个问题必须给出 suggestion：依法应当如何表述或补充，指向具体的法定表述或
法定要素。禁止写实操、资源配置、技术参数类建议。

输出严格 JSON。
```

## 允许判定的问题类型

必须取自 `references/issue_types.md` 的清单，不得自造类型名。

## 反"一律通过"偏置

实跑数据：137 条中 5B 判 pass 132 条、fail 仅 5 条，而 5A 在同一批条款上命中 34 条，其中 32 条是 5B 完全没发现的。**5B 的实际召回率远低于设计预期**，双轨里的"深度"那一轨接近失效。

根因是审查动作太单薄：模型只被要求"看这条有没有问题"，于是宣示性、原则性条款一律 pass。补以下强制动作：

### 每条 CLAUSE 必须逐项过一遍检查矩阵

不允许整体扫一眼给结论。对每条条款，**逐项**回答并写入 `checks`：

| 检查维度 | 必答问题 |
|----------|----------|
| 义务强度 | 本条有无"应当/必须/不得"义务？检索到的条文是否有更强的义务表述被本条弱化？ |
| 主体明确性 | 本条提到的每个动作，是否都有明确的责任主体？有无"有关部门""相关单位"这类无主体表述？ |
| 程序完整性 | 本条涉及的程序（启动/终止/批准/报告/备案/评审/修订）是否载明了触发条件、决定权限、时限？ |
| 时限量化 | 有无"及时/尽快/立即"等定性表述本应量化？检索结果中是否存在对应的法定时限？ |
| 要素完整性 | 本条对应的 `element_tag` 要素，法定必备内容是否齐备？ |
| 衔接性 | 本条涉及与上下级、同级预案衔接时，衔接对象与方式是否明确？ |
| 引用准确性 | 本条引用的法规名称/文号/条款号，与知识库中的记录是否一致？ |

任一维度答"存在缺漏"且能在 Top20 中找到支撑条文 → 生成 issue。

### pass 必须给出理由

判 pass 时，`reasoning` 必须写明"逐项检查后为何不构成法规问题"，且**不得**只写"本条为原则性表述"。宣示性条款也要说明：检索到的条文对该事项有无具体法定要求。

**若某条款判 pass 而 5A 在同一条款命中了规则，5C 会强制送 5D 复核**——所以 pass 的理由必须站得住。

### 允许"依据不足"，不允许"没看出问题"

若怀疑有问题但知识库无条文支撑，**不要**判 pass。写入 `suspected_issues`（不占 `P2-` 编号、不计 fail），含怀疑点与所需法规主题，由 Agent8 汇入依据缺口一并告知用户。这与 5A 的 `kb_gap_report` 是同一设计意图：把"审不了"和"审了没问题"严格区分开。

## Temperature

从 `model_config.json` 读取；为空或缺失时默认 **0.3**（推荐 0.1~0.5）。

## 并发与容错

- 串行：逐条调用，每条间隔 0.5 秒。
- 并发：按 `batch_size` 批量发送，每批间隔 1 秒。
- API 失败重试 3 次，间隔递增 3s / 6s / 9s；仍失败标 `status: error` 并继续，不得中断全局。
- 每 10 条输出进度，每 20 条写入 `review_log.json`。
- LLM 返回非法 JSON：重试 1 次并在 prompt 中强调格式；仍失败标 `error` 并保存原始返回文本。

## 每条 CLAUSE 记录至少包括

- `clause_id`
- `status`：pass / fail / error
- `issue_count`
- `issues`，每项**必须**含：
  - `issue_id`（`P2-001` 起）
  - `type`
  - `description`：说清"预案怎么写的 / 法定怎么要求的 / 差在哪"
  - `quoted_text`：**错误原文**，从本条款正文逐字摘出的出错文字（≥10 字），必须能在条款原文中精确匹配。"没写"类问题摘出本应包含该内容却没有的那句。指不出具体文字则不得生成 issue
  - `reference`：**支撑本发现的库内依据**法规全称，不得缩写
  - `challenged_citation`：仅 `引用法规或条款错误` 类型填，预案中被质疑的那个引用；不参与依据门禁
  - `article`：具体条款号
  - `clause_text`：法规条文原文摘录（≥30 字）
  - `suggestion`：依法应当如何表述或补充（禁止留空，禁止实操/资源/技术参数类建议）
  - `severity`：high / medium / low
  - `basis_sufficiency`：sufficient / insufficient
- `evidence`：Top20 前 3 条
- `retrieval_log`：query + top_hits（**必填**）
- `reasoning`：模型分析过程
- `checked_dimensions`：本条实际比对过的检查维度清单（见"pass 的举证责任"）
- `pass_justification`：判 pass 时必填，说明"哪几部/哪几条法规条文支持本条无问题"
- `suspected_issues`：怀疑有问题但知识库无条文支撑的事项数组（无则填 `[]`），每项含 `suspicion`（怀疑点）、`needed_law_topic`（所需法规主题，只写主题不写文号）、`checked_dimension`（对应检查维度）
- `raw_response`（仅 error 时保留）

## 法规引用强制要求

| 字段 | 要求 |
|------|------|
| `reference` | 法规全称，如"生产安全事故应急条例" |
| `article` | 具体条款号，如"第二十三条" |
| `clause_text` | 条文原文摘录 ≥30 字 |

- 禁止只写法规名不写条款号；禁止只写条款号不写条文原文。
- 无法确定条款号时在 `reasoning` 说明，`severity` 降为 low，`basis_sufficiency` 标 `insufficient`。

## 编号

`P2-001` 起全局连续，与 Agent5A 的 `P-` 体系**独立**，由 Agent5C 统一重排。

---

# 模式 B 完整规格（用户自带模型 / 另给 key 时按此执行）

本节完整还原原始 5B 规格。触发后**必须调用 LLM API**，逐条发送条款 + 知识库检索结果，由模型进行语义级法律分析，不套用模式 A 的子智能体分批流程。

### 前置条件

- 必须先完成"模型配置"步骤，读取 `./output/model_config.json`。
- 必须按配置中的模型、并发方式、batch 大小执行。

### 输入

- `./output/clauses.json`
- `./output/model_config.json`
- `./chroma_db/`
- `query_kb.py`

### 输出

- `./output/review_results_5B.json`

### 审查步骤

对每条 CLAUSE 执行：

1. **检索**：用条款内容作为 query，检索知识库 Top-K（默认 **Top15**）
2. **构建 prompt**：将条款原文 + 检索到的法规片段作为上下文
3. **调用 LLM**：发送 system prompt（审查规则）+ user prompt（条款+法规上下文）
4. **解析结果**：提取 LLM 返回的 JSON 格式审查结论
5. **记录**：保存 retrieval_log + LLM reasoning

### LLM System Prompt（必须包含）

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

### 允许判定问题类型

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

### Temperature 设置

- 从 `model_config.json` 读取 temperature 值
- 如果该值为空或缺失，默认使用 **0.3**
- 合规审查需要稳定、确定性强的输出，推荐 0.1~0.5

### 并发与批处理

根据 `model_config.json` 中的配置：

- **串行模式**：逐条调用 API，每条间隔 0.5 秒
- **并发模式**：按 batch_size 批量发送，每批间隔 1 秒
- **API 失败处理**：重试 3 次，间隔递增（3s/6s/9s）
- **进度记录**：每处理 10 条输出进度，每 20 条写入 review_log

### 每条 CLAUSE 记录至少包括

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
- `evidence`（Top-K 检索前 3 条）
- `retrieval_log`（query + top_hits）
- `reasoning`（LLM 的分析过程）

### 问题编号

- 全局连续：`P2-001`、`P2-002`、`P2-003`……
- 与 Agent5A 的编号体系**独立**，前缀用 `P2-` 区分

### 法规引用强制要求

每个 fail 类型的 issue **必须**包含精确的法规引用：

| 字段 | 要求 | 示例 |
|------|------|------|
| `reference` | 法规全称，不得缩写 | "危险化学品安全管理条例" |
| `article` | 具体条款号 | "第二十三条" |
| `clause_text` | 该条款原文摘录（≥30字） | "生产、储存危险化学品的单位……" |

- 禁止只写法规名不写条款号
- 禁止只写条款号不写条文原文
- 如果 LLM 无法确定具体条款号，应在 reasoning 中说明，severity 降为 low

### 验收

- `CLAUSE` 数量必须等于 `review_results_5B.json` 条目数量
- 无漏条（error 状态也算已处理）
- 每条都有 retrieval_log 和 reasoning
- 必须更新 `./output/review_log.json`

### 下游兼容补充（**必须执行，否则模式 B 的结果会被 5C 全部拒收**）

原始规格成型于 5C 依据门禁之前，其 issue 字段集缺两项现在下游强制要求的字段。模式 B 在保持上述规格不变的前提下，**额外**要求每个 issue 补齐：

- `quoted_text`：从条款正文逐字摘出的出错文字（≥10 字），必须能在条款原文中精确匹配。Agent8 靠它锚定批注位置。
- `suggestion`：依法应当如何表述或补充，指向具体的法定表述/法定要素。

理由：5C 的依据门禁对每个候选问题查五项（`reference` 在库、法规可用、`article` 具体、`quoted_text` 可匹配、`suggestion` 非空），任一不过即移出问题清单。若模式 B 只按原始字段集输出，全部问题会在 5C 被拒收，`review_results.json` 将为空。这两项是交付所必需，不是可选增强。

除此之外，模式 B 不引入模式 A 的 `checks` 检查矩阵、`pass_justification`、`suspected_issues`、`checked_dimensions` 等字段要求；但"pass 率自检"仍适用（见验收节），因为它是对模型系统性宽松的兜底，与执行模式无关。

---

# 验收（两种模式通用）

- `review_results_5B.json` 条目数 == `clauses.json` 条目数（error 也算已处理）。
- `review_log.json` 中已记录 `agent5b_mode`（`A` 或 `B`）；模式 B 还须记录所用 `model_name` 与 `base_url`（**不得记录 api_key**）。
- 每条都有 `retrieval_log`、`reasoning`；模式 A 的另有 `checked_dimensions`，判 pass 的另有 `pass_justification`。
- 模式 A 下：`5b_batches/` 与 `5b_results/` 批次一一对应，每批 `clause_id` 集合完全一致，无缺审。
- 两种模式下每个 issue 都有 `quoted_text` 与 `suggestion`（模式 B 见"下游兼容补充"）。
- **pass 率自检**：若 pass 率 > 90%，必须在 `review_log.json` 写入 `pass_rate_alert`，并对 5A 判 fail 而 5B 判 pass 的条款重审一遍（这批条款是 5B 漏检的高发区），重审结论写入 `recheck_after_alert`。实跑中 5B pass 率 96.4%（132/137），而 5A 在同一批条款上发现 34 条 fail，其中 32 条为 5A 独有——说明 5B 在"必备要素缺失"这类问题上系统性漏检，必须自检。两种模式都适用。
- 更新 `./output/review_log.json`。
