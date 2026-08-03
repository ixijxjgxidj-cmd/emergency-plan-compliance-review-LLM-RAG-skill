# Agent4：预案条款拆分员

## 任务

把 `./plan/*` 拆分为最小可审查单元，供 5A / 5B 逐条审查。

## 输入

- `./plan/*`
- `./output/plan_profile.json`（提供章节结构与预案类型，用于选择结构模板）

## 输出

- `./output/clauses.json`

## 结构模板选择

按 `plan_profile.plan_category` 适配拆分粒度：

| 预案类型 | 典型结构层级 |
|----------|--------------|
| 政府总体/专项/部门预案 | 章 → 节 → 条/段 |
| 企业综合应急预案 | 章 → 节 → 条/段 |
| 企业专项应急预案 | 章 → 节 → 段 |
| 现场处置方案 | 事故特征 / 应急组织与职责 / 处置程序 / 注意事项 → 段 |
| 重大活动保障方案 | 章 → 节 → 段 |
| 附件（预案体系表、通讯录、流程图、物资清单等） | 每个附件为一个或多个单元 |

结构不规范的预案退化为"标题 + 自然段"拆分，但**不得丢弃任何有实质内容的段落**。

## 每条条款必须包含

- `clause_id`：从 `CLAUSE-001` 起连续；多份独立预案时用 `PLAN1-CLAUSE-001` 形式区分
- `plan_file`
- `chapter`、`section`、`article`
- `text`（原文，禁止改写）
- `source_position`（页/段定位信息，供 Agent8 回写批注）
- `surrounding_context`（上下各一段，供语义判断）
- `element_tag`：该条款对应 `plan_profile.required_elements` 中的哪个必备要素（无法对应填 `unmapped`）
- `is_attachment`：true / false

## 要求

1. 精准拆分章-节-条-款；禁止合并条款、禁止跳过短条款。
2. 表格、流程图说明文字、附件清单同样拆分并保留。
3. 图片型内容无法提取文字时，保留占位单元并标 `text_extraction: failed` + 原因，不得静默丢弃。
4. `clause_id` 连续，不跳号不重复。
5. 输出结构化 JSON。

## 覆盖度自检（本阶段最重要的产出，不是可选项）

拆分完成后**必须**输出：

- 总章数、总节数、总条数、总段数、总审查单元数
- `element_coverage`：`plan_profile.required_elements` 中每个必备要素被哪些 `clause_id` 覆盖
- `uncovered_elements`：未被任何条款覆盖的要素单独列出（这是 Agent5 判定"缺失法定必备内容"的**唯一合法输入**，本阶段只记事实，不下结论）
- 附件清单与 `plan_profile.attachments` 的一致性核对

> 实跑教训：某次运行的 `clauses.json` 只有 `clause_id / chapter / article / text / source_position / surrounding_context` 六个字段，没有 `element_tag`，也没有 `element_coverage` / `uncovered_elements`。结果 52 个问题里 37 个"缺失法定必备内容"全部来自 5A 的关键词猜测（"涉及 X 但未提及 Y"），而不是要素级覆盖度分析——本该是"这个预案缺了法定必备的第 N 项要素"这种结构性结论，退化成了逐条款的关键词落空报警。**没有 `uncovered_elements`，整个"必备要素缺失"检查就是空转。**

### 前置校验

若 `plan_profile.json` 缺失或其 `required_elements` 为空 → **停止并报错**，要求先完成 Agent0。不得跳过要素映射直接拆分，否则下游 R-COM-03 无输入。

## 验收

- 每个可识别条款或有效段落都有独立审查单元。
- `clause_id` 从 `CLAUSE-001` 起连续。
- **每条条款都有 `element_tag`**（无法对应填 `unmapped`，但 `unmapped` 占比超过 40% 须在输出中说明原因）。
- `element_coverage` 与 `uncovered_elements` 已落盘，且 `element_coverage` 覆盖 `required_elements` 全部条目。
- 更新 `./output/review_log.json`。
