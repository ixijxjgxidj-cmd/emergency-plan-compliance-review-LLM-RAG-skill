# 审查严格度挡位（Strictness Levels）

问题数的收敛来自**四个相互独立的机制**。挡位就是这四个开关的组合，不是一个模糊的"松紧旋钮"。

选定后写入 `./output/review_config.json`，全流程各阶段据此执行，并在 `summary_report.md` 中声明本次所用挡位。

## 四个开关

| 开关 | 作用位置 | `off` | `annotate` | `filter` |
|------|----------|-------|------------|----------|
| `cross_clause_aggregation` | 5A 聚合 / 5C Step4 第二层 | 每条款各自成一个问题编号 | — | 同因命中归并为一条，`affected_clauses` 列全部条款 |
| `basis_gate_a` | 5C Step3 A 级（依据合法性） | 不查 | 保留问题，标 `basis_outside_kb` | 移出清单，入 `rejected_problems.json` |
| `basis_gate_b` | 5C Step3 B 级（字段完备性） | 不查 | 保留问题，标 `incomplete_fields` 并列出缺哪些 | 重跑检索补齐，补不齐才移出 |
| `fulltext_crosscheck` | 5C2 全文反证 | 不执行本阶段 | 执行并标 `refuted_by` / `partial_coverage`，但不移出 | `refuted` 移出，`downgraded` 降档 |

`cross_clause_aggregation` 只有 `off` / `filter` 两态——归并不产生"标注"这种中间状态。

## 四个预设挡位

| 挡位 | 聚合 | A 级门禁 | B 级门禁 | 全文反证 | 定位 |
|------|------|----------|----------|----------|------|
| **L0 原始** | off | off | off | off | **5A/5C/5D/8 换用原始 prompt**，完全复现 52 条；批注仍用四字段模板 |
| **L1 去重** | filter | off | off | off | 只解决"同一缺陷被拆成 N 个编号" |
| **L2 标注**（默认） | filter | annotate | annotate | annotate | 一条不删，但把每条的依据状态与反证结论如实标出 |
| **L3 严格** | filter | filter | filter | filter | 只留可直接交付评审的问题 |

## L0：替换 5A / 5C / 5D / Agent8，目标是完全复现 52 条

```
L0：  Agent0 → 1 → 2 → 3 → 4 → [模型配置]                        ← 增强版
        → 5A  读 prompts/L0_original/05A_rule_screening/prompt.md ← 原始
        → 5B                                                      ← 增强版
        → 5C  读 prompts/L0_original/05C_cross_audit/prompt.md    ← 原始
        →（跳过 5C2）
        → 5D  读 prompts/L0_original/05D_recheck/prompt.md        ← 原始
        → 5E → 6 → 7                                              ← 增强版
        → 8   读 prompts/L0_original/08_result_summary/prompt.md  ← 原始
              但批注格式改用增强版四字段模板（唯一刻意偏离）

L1/L2/L3： 全程读 prompts/ 下的增强版，四个开关按挡位取值
```

`review_config.json` 记：

```json
{ "strictness_level": "L0",
  "reproduce_original": true,
  "agent5a_prompt": "prompts/L0_original/05A_rule_screening/prompt.md",
  "agent5c_prompt": "prompts/L0_original/05C_cross_audit/prompt.md",
  "agent5d_prompt": "prompts/L0_original/05D_recheck/prompt.md",
  "agent8_prompt":  "prompts/L0_original/08_result_summary/prompt.md",
  "cross_clause_aggregation": "off",
  "basis_gate_a": "off",
  "basis_gate_b": "off",
  "fulltext_crosscheck": "off",
  "annotation_template": "prompts/08_result_summary/prompt.md#批注正文模板" }
```

### 为什么必须连 5A 一起换

52 条中有 34 条的依据是《危险化学品安全管理条例》《GB/T 29639》《GB 30077》《突发环境事件应急管理办法》——这四部**都不在 `laws/` 里**。它们能出现，是因为**原始 5A 的规则库自带法规名**，且没有"依据落实门禁"。

增强版 5A 恰恰堵掉了这两点：规则不得自带法规名，取不到库内条文就记 `advisory` 不生成 issue。所以只要 5A 用增强版，那 34 条根本不会产生，52 条无从复现。**要复现 52 条，5A 必须换回原始版。**

原始 5A 的 10 条规则：法定时限、应急预案编制（GB/T 29639）、演练频次、重大危险源、危化品许可、消防设施、环境监测、物资配备标准（GB 30077）、引用法规准确性、事故分级标准。issue 只有 `type`/`description`/`reference`/`severity`/`rule_id` 五个字段。

### L0 的批注：唯一一处刻意偏离原样

原始 Agent8 对批注只有三句话要求（保留原文、在对应条款位置插入批注、能定位回原条款），实跑出来就是"挂整段、无条款号、无修订建议、夹带流程元数据"。**L0 要复现的是 52 条命中，不是那个批注质量。**

所以 L0 的 Agent8：问题清单、统计、报告结构按原始 prompt（含 `chapter2A_issue_list.docx` 原始文件名）；**批注与问题清单的取材、格式、锚定规则改用 `prompts/08_result_summary/prompt.md` 的"plan_annotated.docx 必须"整节**——四字段 + 判定标签行、锚定 `quoted_text` 精确字符区间、禁止流程元数据、真批注三件套自检。

原始 5A 不产出 `quoted_text` / `article` / `clause_text` / `suggestion`，L0 的 Agent8 必须补齐并逐条标记：

| 缺失字段 | 补齐方式 | 标记 |
|----------|----------|------|
| `quoted_text` | 从该 `clause_id` 条款原文中**逐字摘取**最能体现该问题的一句（≥10 字），必须能在预案中精确匹配 | `derived.quoted_text: true` |
| `article` + `clause_text` | 用 `reference` + 问题描述重跑知识库 Top20，定位具体条号与原文（≥30 字） | `derived.article: true` |
| `suggestion` | 依据已定法条写出法律层面修订方向 | `derived.suggestion: true` |

补不到时如实退化，**禁止编造**：`reference` 不在库内（L0 有 34 条属此类）→ 依据行只写《法规全称》，另起一行写"条款号未能在本地知识库中定位"，记 `basis_not_in_kb: true`；`quoted_text` 摘不出 → 锚定整段，记 `anchor_fallback: paragraph`；`suggestion` 写不出 → 写"需补充该主题法规后方可给出依法修订方向"。

`annotation_log.json` 必须统计批注总数、`derived.*` 各项、`basis_not_in_kb`、`anchor_fallback` 条数——这几个数字就是 L0 结果可信度的量化说明。

### 原始 5C/5D 与增强版的实际差异

| 机制 | 原始 5C/5D | 增强版 5C/5D |
|------|------------|--------------|
| 决策矩阵（fail/fail 保留等 8 种组合） | 有，完全相同 | 有 |
| A 级依据门禁（依据不在库则剔除） | **无** | 有 |
| B 级字段完备性（缺 article/quoted_text/suggestion 则退回补齐） | **无** | 有 |
| 跨条款同因归并 | **无**（只在同一条款内按 type 去重） | 有 |
| `challenged_citation` 分流 | **无** | 有 |
| 上游违约告警 | **无** | 有 |
| 5D 字段级复核（`field_check`） | **无**（只做 `citation_check`） | 有 |
| 法规引用是否在库 | 只作为格式核查项，**不产生剔除动作** | 硬门禁 |

所以 L0 的效果是：**5C/5D 一条问题都不删**，只做裁定、同条款去重、置信度标注、编号连续性核查。

### 选 L0 必须知道的三件事

1. **约 34 / 52 条的依据不在 `laws/` 内**（原始 5A 规则自带的四部法规本地没有）。这些问题在本系统的证据体系内不成立，批注会如实标注"条款号未能在本地知识库中定位"。
2. **52 条里只有约 10 个不同缺陷**，最重复的一条出现 19 次（同一规则在 19 个条款各发一个编号）。L0 不做跨条款聚合，数量虚高是预期行为，不是缺陷。
3. **L0 是危化品专用的**：原始 5A 的 10 条规则全部围绕危化品，审其他类型预案会大面积漏检。非危化品预案请用 L1 以上。

## 在实跑数据上的预期输出

用那份区级危化品预案（137 条款 / 12622 字 / 原始 52 个问题）标定：

| 挡位 | 输出 | 构成 |
|------|------|------|
| L0 | **52 条问题** | 完全复现实跑原始结果；其中 34 条依据不在 `laws/`，去重后只有约 10 个不同缺陷 |
| L1 | **17 条主张** | 52 条去重后的不同缺陷数；最重复的一条原本出现 19 次 |
| L2 | **17 条主张**，其中 11 条带警示标记、6 条干净 | 标记构成见下 |
| L3 | **6 条主张** | 即 L2 中那 6 条干净的 |

L2 的 11 条标记（按主张计，有重叠）：

- `basis_outside_kb` 4 条 —— 依据是《危险化学品安全管理条例》《GB/T 29639》《GB 30077》《突发环境事件应急管理办法》，均不在 `laws/`
- `citation_unverifiable` 3 条 —— `引用法规或条款错误` 类型，被质疑的是本地没有的上级预案，无从核验
- `refuted_by` 7 条 —— 全文反证发现该要素已在预案别处落实

L2 与 L3 的输出集合关系是严格包含：**L3 = L2 中无任何标记的那部分**。所以从 L2 切到 L3 不会改变任何一条问题的内容，只是把带标记的隐去。

## 挡位不改变的东西

无论哪个挡位，以下一律不变：

1. **`summary_report.md` 必须完整披露漏斗**：`52 → 17 → 10 → 6` 每一级的数量与减少原因。低挡位不等于可以不告诉用户"如果按严格标准会剩多少"。
2. **法规依据仍只能来自 `./laws/`**。L0 的 `basis_gate_a: off` 只是不因"依据在库外"而移出问题，**不代表允许凭记忆编造条文**——依据文本仍必须逐字来自知识库或如实标为取不到。
3. **`kb_gap_report.json` 照常产出**。哪些检查点因缺法规未能形成结论，与挡位无关。
4. **`plan_annotated.docx` 与 `issue_list.docx` 恒按 L3 标准取材**。带 `basis_outside_kb` / `citation_unverifiable` / `refuted_by` 标记的问题不进批注——批注是给评审专家看的交付件，放进依据站不住的条目就会重演实跑那次"52 条批注里 34 条依据不在库、还写着依据来源存疑"的结果。这些问题在 `problems_all.json`、`summary_report.md` 与 `issue_list.docx` 的**候选问题附录**中完整呈现。

第 4 条是本设计的关键：**分析产物全量，交付产物严格。** 挡位控制的是"分析结果保留多少"，不是"批注里塞多少"。

## 怎么选

| 场景 | 建议挡位 |
|------|----------|
| 复现原始 52 条命中、与增强链做对照（**仅危化品预案**） | L0 |
| 想知道"到底有几个不同缺陷" | L1 |
| 预案修订自查、要尽量不漏、能接受自己甄别 | **L2** |
| 出正式审查意见、交评审专家 | L3 |
| `laws/` 里法规不全（少于 10 部或缺主要上位法） | L2 —— 此时 A 级门禁会大量误剔，不宜用 L3 |

最后一条是实跑教训：那次 `laws/` 只有 9 部可用法规，A 级剔除率 24%，其中至少 C-04（装备配备标准）经全文反证判定为 `upheld`，主张可能成立却因本地缺标准而被剔。**知识库越不全，越该用 L2 而不是 L3。**
