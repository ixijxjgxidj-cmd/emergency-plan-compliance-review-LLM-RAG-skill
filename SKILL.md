---
name: emergency-plan-compliance-review
description: 对任意类型应急预案（政府总体/专项/部门预案、企业综合/专项预案、现场处置方案、重大活动保障方案）做逐条法律法规合规审查。先识别预案类型与适用法规基线，再基于用户提供的法规文件构建知识库，然后以规则快筛与 LLM 深度审查双轨并行、交叉审计查缺补漏，输出可追溯的问题清单、批注版预案与汇总报告。
---

# 应急预案合规审查 Skill（通用版）

## 0. 本 Skill 如何被加载

本文件是 **包根目录下的 `SKILL.md`**，任何支持 skill / agent 包的运行环境都应能直接识别：

```
emergency-plan-compliance-review/   ← 上传/打包这一层（zip 根目录内直接含 SKILL.md）
├── SKILL.md          ← 入口（本文件）
├── AGENTS.md         ← Codex / 通用 agent 入口，内容指向本文件
├── CLAUDE.md         ← Claude Code 入口，内容指向本文件
├── references/       ← 预案类型-法规基线矩阵、问题类型清单
├── prompts/          ← 各阶段 Agent prompt（含 L0_original/ 的原始 5A、5C、5D、8）
├── scripts/          ← 打包与校验脚本
├── laws/             ← 用户提供的法规/标准/规范文件
├── plan/             ← 待审预案
└── output/           ← 全部产出
```

若运行环境不支持自动加载 skill，直接把本文件当普通提示词读入即可，流程完全一致。
打包上传前执行 `python scripts/package_skill.py`，它会校验"SKILL.md 是否位于压缩包根目录"并生成 `dist/emergency-plan-compliance-review.zip`。

**不要**把 SKILL.md 放进 `skills/<中文名>/` 之类的嵌套目录，也不要出现同名目录套同名目录——这是"上传后提示未找到 SKILL.md"的唯一常见原因。

---

## 1. 适用范围

适用于**所有类型**的应急预案审核，不限于危险化学品：

| 大类 | 具体类型 |
|------|----------|
| 政府及部门预案 | 总体应急预案、专项应急预案、部门应急预案 |
| 单位与基层组织预案 | 企业事业单位综合应急预案、专项应急预案、现场处置方案、村（居）民委员会预案 |
| 重大活动 | 重大活动保障方案 |
| 事件类别 | 自然灾害、事故灾难（含危化品、矿山、交通、火灾、环境等）、公共卫生事件、社会安全事件 |
| 编制层级 | 国家、省、市、县（区）、乡镇（街道）、企业事业单位 |

预案类型决定"适用法规基线"和"必备要素清单"，由 Agent0 在流程开始时判定，详见 `references/plan_type_matrix.md`。

---

## 2. 绝对边界

### 2.1 只审法律法规问题

严禁纳入：实操可行性、资源配置是否合理、PPE 是否合理、疏散距离是否科学、地方适配性、事故案例经验、专家经验判断，以及任何非法律法规性质的评价。

### 2.2 知识库只能来自用户提供的法规文件

知识库唯一合法来源是用户放入 `./laws/`（含子目录）的法规/标准/规范文件。

**不得**凭模型记忆生成任何法规条文；`references/plan_type_matrix.md` 中的法规清单只是"应当去找什么"的检索线索，**不是**可直接引用的依据，其文号与年份必须在 `./laws/` 中有对应文件落实后，才能作为审查依据。基线清单中本地缺失的法规，只记录为"依据缺口"事实，不得据此凭记忆写出条文。

### 2.3 联网核验的边界

- 核验阶段（Agent7）只核验已发现问题，不得新增问题、补查漏检、扩大范围、改变编号。
- 核验不到就记 `unverified`，**禁止编造条文或结论**。

### 2.4 每条款独立审查

每一条款独立检查；每一个问题可追溯到具体条款 + 具体法规条文；禁止"略""同上""类似问题统一处理"；禁止抽样或代表性检查。

---

## 2.5 执行方式：每阶段一个子智能体

**每个阶段派发一个独立子智能体执行**，它读自己那份 prompt、干完、落盘、回报统计后结束。主流程只编排与校验，不亲自做阶段的活。

唯一例外：**5B 且用户提供了模型 key（模式 B）**，该阶段直接按 `model_config.json` 调用外部 API，不派子智能体。

派发时必须交给子智能体六项：阶段 prompt 路径、`SKILL.md` 第 2 节（绝对边界）、`review_config.json`（挡位）、输入路径清单、输出路径清单、回报格式（只回统计，**不回传产出内容**）。

主流程在阶段之间必须：核对该阶段"验收"节的每一项 → 更新 `review_log.json` → 不通过则最多重派一次，仍不通过就停止，**不得跳过阶段**。

两处需要二级派发：**5B 模式 A**（按 batch 切分，每批一个子智能体）、**5C2 路径 2**（预案 > 30000 字时每个待查主张一个子智能体）。二级派发由该阶段的子智能体自己完成。

理由：单一上下文串 15 个阶段会在中途质量塌陷——实跑那次 5B 单上下文审 137 条，pass 率 96.4%，后半程等于没审。每阶段独立上下文是唯一解法，顺带换来可续跑（输出已存在且通过校验的阶段直接跳过）。

详见 `prompts/master.md` 的"执行方式"一节。

## 3. 工作流总览

```
Agent0  预案画像与类型判定
   ↓
挡位选择（默认 L2 标注档）
   ↓
Agent1  本地法规盘点
   ↓
Agent2  法规分类（含与预案类型的相关性标注）
   ↓
Agent3  知识库构建
   ↓
Agent4  预案条款拆分（按预案类型选结构模板）
   ↓
模型配置（仅当用户自带模型时；默认跳过）
   ↓
Agent5A 规则快筛（通用规则 + 类型专属规则，不调用 LLM）
   ↓
Agent5B LLM 深度审查（逐条调用大模型 + 知识库 Top20）
   ↓
Agent5C 交叉对比审计（5A vs 5B，查缺补漏）
   ↓
Agent5C2 全文反证（缺失类主张放到全文范围复核，剔误报）
   ↓
Agent5D 交叉审计复核
   ↓
Agent5E 最终审计
   ↓
Agent6  法规依据复核
   ↓
Agent7  联网核验（只核验已发现问题）
   ↓
Agent8  成果汇总
```

每阶段的完整要求见对应 prompt：

| 阶段 | Prompt |
|------|--------|
| Agent0 | `prompts/00_plan_profiling/prompt.md` |
| Agent1 | `prompts/01_law_inventory/prompt.md` |
| Agent2 | `prompts/02_law_classification/prompt.md` |
| Agent3 | `prompts/03_kb_build/prompt.md` |
| Agent4 | `prompts/04_clause_split/prompt.md` |
| Agent5A | `prompts/05A_rule_screening/prompt.md` |
| Agent5B | `prompts/05B_llm_deep_review/prompt.md` |
| Agent5C | `prompts/05C_cross_audit/prompt.md` |
| Agent5C2 | `prompts/05C2_fulltext_crosscheck/prompt.md` |
| Agent5D | `prompts/05D_recheck/prompt.md` |
| Agent5E | `prompts/05E_final_audit/prompt.md` |
| Agent6 | `prompts/06_missing_basis_review/prompt.md` |
| Agent7 | `prompts/07_web_verification/prompt.md` |
| Agent8 | `prompts/08_result_summary/prompt.md` |
| 总控 | `prompts/master.md` |

---

## 4. 阶段要点

### Agent0 预案画像与类型判定

读取 `./plan/*`，判定：预案大类、事件类别、编制层级、编制主体、预案名称/版本/发布日期、章节结构。
据 `references/plan_type_matrix.md` 生成"适用法规基线清单"与"必备要素清单"。
输出 `./output/plan_profile.json`。类型无法唯一判定时列出候选并询问用户，不得默认按危化品处理。

### 挡位选择（Agent0 之后，默认 L2）

问题数的收敛来自四个独立开关：跨条款聚合、A 级依据门禁（依据是否在库）、B 级字段完备性、5C2 全文反证。挡位即这四个开关的组合，完整定义见 `references/strictness_levels.md`。

| 挡位 | 聚合 | A 级 | B 级 | 全文反证 | 实跑数据上的输出 |
|------|------|------|------|----------|------------------|
| L0 原始 | off | off | off | off | **52 条**（5A/5C/5D/8 换用原始 prompt，完全复现） |
| L1 去重 | filter | off | off | off | 17 条主张 |
| **L2 标注**（默认） | filter | annotate | annotate | annotate | 17 条，11 条带警示标记 |
| L3 严格 | filter | filter | filter | filter | 6 条 |

L3 = L2 中无任何标记的那部分，两者是严格包含关系。写入 `./output/review_config.json`，各阶段据此执行。

**L0 替换 5A / 5C / 5D / Agent8 四个阶段**，读 `prompts/L0_original/` 下逐字节保留的原始 prompt，并跳过 5C2。目标是**完全复现 52 条**。

连 5A 一起换是必要条件：52 条里 34 条的依据是《危险化学品安全管理条例》《GB/T 29639》《GB 30077》《突发环境事件应急管理办法》，四部都不在 `laws/` 里。它们能出现是因为**原始 5A 规则库自带法规名**且无依据落实门禁；增强版 5A 恰好堵掉这两点，所以 5A 不换回原始版就复现不出 52 条。

**唯一刻意偏离原样的是批注格式**：L0 要复现的是 52 条命中，不是原始那个批注质量（挂整段、无条款号、无修订建议）。所以问题清单与报告结构按原始 prompt，批注一律按四字段 + 判定标签行模板；原始 5A 不产出的 `quoted_text`/`article`/`clause_text`/`suggestion` 由 Agent8 补齐并逐条标 `derived.*`，补不到时如实退化（写"条款号未能在本地知识库中定位"、锚定退化为整段），禁止编造。

三点须知：约 34/52 条依据不在库内；52 条去重后只有约 10 个不同缺陷（最重复的出现 19 次）；**L0 的 10 条规则全部围绕危化品，非危化品预案请用 L1 以上**。

**知识库越不全，越该用 L2。** 实跑那次 `laws/` 只有 9 部可用法规，A 级剔除率 24%，其中"未参照装备配备标准"一条经全文反证判定成立，却因本地缺该标准而被剔。

**批注恒按 L3 标准取材**——带标记的问题只进候选问题附录，不进 `plan_annotated.docx`。分析产物全量，交付产物严格。

### Agent1 本地法规盘点

扫描 `./laws/`（含子目录），逐个盘点，文件总数**动态统计**、不得写死。读取失败重试 3 次，仍失败记入 `failed_files` 并继续。输出 `./output/law_inventory.json`。

同时与 `plan_profile.json` 的基线清单比对，把"基线要求但本地无对应文件"的法规记入 `baseline_missing`（只记事实，不产生审查结论，也不得凭记忆补写条文）。

### Agent2 法规分类

对全部本地法规做效力层级、类别、有效状态、优先级标注，并新增 `plan_type_relevance`（与本次预案类型的相关性：核心 / 相关 / 参考 / 不适用）。输出 `./output/law_metadata.json`。

### Agent3 知识库构建

解析全文，按"章-节-条-款"优先切片（chunk ≤ 1500 字，禁止跨条款合并），构建 `./chroma_db/`。输出 `./output/kb_summary.json`、`build_kb.py`、`query_kb.py`、`README_KB.md`。默认检索 Top20。

### Agent4 预案条款拆分

按 `plan_profile.json` 选用结构模板，把 `./plan/*` 拆为 `CLAUSE-001` 起连续编号的最小可审查单元。输出 `./output/clauses.json`。

### 模型配置（仅模式 B 需要）

**默认不需要，也不要向用户索要 API key。** Agent5B 默认走模式 A（本环境子智能体分批），无需外部模型。

仅当用户主动为 5B 指定另外的模型或主动提供 key 时，才确认：`api_key`+`base_url`+`model_name`、并发方式（串行 / 并发）、batch 大小（3/5/10，仅并发）、temperature（未回答默认 **0.3**），写入 `./output/model_config.json`。

### Agent5A 规则快筛

知识库 Top20 检索 + 规则/模式匹配，**不调用 LLM**。规则库分层加载：通用规则 `R-COM-*` 全预案适用，类型专属规则按 `plan_profile.json` 动态启用。

两条硬约束：
- **规则不得自带法规名**。规则只写检查点与触发特征；`reference`/`article`/`clause_text` 只能从本次检索结果中摘取，且 `reference` 必须能在 `law_metadata.json` 中精确匹配。取不到依据 → 记 `advisory` + 写入 `kb_gap_report.json`，不生成问题。
- **同一规则命中多条款时按规则聚合**为一条问题，`affected_clauses` 列出全部条款，不得每条款各发一个编号。

输出 `./output/review_results_5A.json`、`./output/kb_gap_report.json`，问题编号 `P-001` 起连续。

### Agent5B LLM 深度审查

逐条调用大模型 + 知识库 **Top20**（与 5A 同档），做语义级合规分析，穷举隐性问题（职责不清、程序缺失、衔接不全等）。必须记录 `retrieval_log` 与 `reasoning`。

条款数 > 40 时**强制**用子智能体分批模式：batch 文件自带条款原文 + 检索结果，子智能体独立审完落盘即释放上下文，支持断点续跑。判 pass 也必须写明"逐项核对了哪些法定要求"，禁止只写"属原则性条款"。输出 `./output/review_results_5B.json`，编号 `P2-001` 起，与 5A 体系独立。

### Agent5C 交叉对比审计

**Step 0 依据合法性门禁（先于一切裁定）**：逐个问题校验 `reference` 能否在 `law_metadata.json` 中精确匹配。匹配不上的一律**剔除**（转入 `kb_gap_report.json`），不占编号、不进入 5D/5E/6/7/8。依据在知识库外的问题不是问题，是知识库缺口。

再按下表裁定，合并去重、标注置信度与来源，输出 `./output/review_results.json` 与 `./output/cross_audit_log.json`。

| 5A | 5B | 决策 |
|----|----|------|
| fail | fail | 保留（高置信度） |
| fail | pass | 标记待复核（疑规则误报） |
| pass | fail | 保留（LLM 独有隐性问题） |
| pass | pass | 通过 |
| fail | error | 保留 5A |
| error | fail | 保留 5B |
| error | pass | 标记待复核 |
| error | error | 标记失败 |

### Agent5C2 全文反证

对 5C 输出的"缺失/不明确"类问题逐条做全文反证：查该法定要素是否已在预案别处落实。三判定——`refuted`（误报剔除）/ `downgraded`（部分落实，降一档）/ `upheld`（成立，并收敛到"依法应当写在哪一条"）。

**判误报的举证责任重于判成立**：必须给出落实位置的逐字原文，且通过三要件测试（同一要素 / 有约束力表述 / 法定最小内容齐备）。缺一只能降级。被剔问题移入 `refuted_problems.json` 保留可追溯，误报率 > 60% 触发告警。

必须排在 5D 之前——本阶段会改锚点（`affected_clauses` 收敛），5D 才是校验锚点的那一步。输出 `./output/fulltext_crosscheck.json`。

### Agent5D 交叉审计复核

逐条复核 5C 裁定，重跑 Top20 检索验证依据，对"标记待复核"给出最终裁定。输出 `./output/review_results_5D.json`。

### Agent5E 最终审计

核查条款数一致性、编号连续性、字段完整性、法规引用准确性、置信度与来源标注。输出 `./output/review_results_final.json`。

### Agent6 法规依据复核

只补强已有问题的遗漏依据，禁止新增问题或编号。输出 `./output/missing_basis.json`。

### Agent7 联网核验

对已发现问题逐条核验：法规是否现行有效、条款号是否准确、条文内容是否一致。优先使用运行环境自带的联网搜索能力；无则按 `model_config.json` 调用具备联网能力的模型。输出 `./output/verified_results.json`。

### Agent8 成果汇总

输出问题总表、汇总报告、批注版预案、问题清单。报告须含：预案类型与适用基线、基线落实情况（本地已有 / 本地缺失）、5A 独有 / 5B 独有 / 共同问题数、审计裁定统计、置信度分布、本次审查的能力边界（哪些检查点因知识库缺依据未能形成结论）。

**批注版预案的批注锚定在"出错的那句话"上**（`quoted_text` 在正文中的精确字符区间），不锚在章节标题或目录上。批注正文为"四字段 + 判定标签行"结构，不得夹带流程元数据：

```
问题：{问题类型}——{预案怎么写的 / 法定怎么要求的 / 差在哪}

错误原文：{从预案正文逐字摘出的出错文字}

依据：《{法规全称}》第X条
{该条文原文，≥30 字，逐字来自知识库}

改进建议：{依法应当如何表述或补充}

——————————
严重度：{高|中|低}　置信度：{高|中|低}　联网核验：{已核验|部分核验|未核验|核验失败}
```

判定标签必须用中文值（禁止输出 `high`/`medium`/`unverified` 等英文枚举原值），放在末尾并用分隔线与正文隔开。禁止写入 `origin`、`source`、`chunk_id`、检索日志、阶段代号，以及"依据来源存疑"这类自我否定表述。

`issue_list.docx` 的"错误原文""依据""改进建议"三列与同一 `problem_id` 的批注逐字一致，"严重程度""置信度""核验状态"三列与标签行的中文值一致。

---

## 5. 输出文件

| 文件 | 说明 |
|------|------|
| `./output/review_config.json` | 审查严格度挡位配置 |
| `./output/plan_profile.json` | 预案画像与适用法规基线 |
| `./output/law_inventory.json` | 本地法规盘点 |
| `./output/law_metadata.json` | 法规分类标注 |
| `./output/kb_summary.json` | 知识库构建摘要 |
| `./output/clauses.json` | 预案条款拆分（含 `element_tag` / `uncovered_elements`） |
| `./output/model_config.json` | 模型配置 |
| `./output/review_results_5A.json` | 规则快筛结果 |
| `./output/kb_gap_report.json` | 依据缺口报告（规则命中但知识库无条文） |
| `./output/review_results_5B.json` | LLM 深度审查结果 |
| `./output/review_results.json` | 交叉审计结果 |
| `./output/cross_audit_log.json` | 交叉审计日志 |
| `./output/rejected_problems.json` | 依据不合法被移出的候选问题 |
| `./output/fulltext_crosscheck.json` | 全文反证裁定 |
| `./output/refuted_problems.json` | 全文反证判为误报移出的问题 |
| `./output/review_results_5D.json` | 审计复核结果 |
| `./output/review_results_final.json` | 最终审计结果 |
| `./output/missing_basis.json` | 依据补强 |
| `./output/verified_results.json` | 联网核验结果 |
| `./output/problems_all.json` | 全部问题汇总 |
| `./output/summary_report.md` | 汇总报告 |
| `./output/plan_annotated.docx` | 批注版预案 |
| `./output/issue_list.docx` | 问题清单 |
| `./output/review_log.json` | 全程审查日志 |

附带：`./chroma_db/`、`build_kb.py`、`query_kb.py`、`README_KB.md`。

分批执行 5B 时另有中间产物 `./output/5b_batches/batch_NN.json`、`./output/5b_results/result_NN.json`，**必须保留**（断点续跑与漏审自查的依据）。

---

## 6. 质量标准

必须做到：

1. `processed_files + failed_files` 等于本地法规文件实际总数。
2. `plan_profile.json` 基线清单中的每条法规都有落实状态（本地已有 / 本地缺失），缺失项记入 `baseline_missing`。
3. 每个法规至少 1 个 chunk，或记录明确失败原因。
4. 每个条款 5A、5B 各审一遍，每条都有 **Top20** 检索记录，无一条缺 `retrieval_log`。
5. 每个问题都有法规名称 + 条款号 + 条文原文摘录（≥30 字）+ `chunk_id`，且 `reference` 能在 `law_metadata.json` 中精确匹配。
6. **最终交付的问题中，引用知识库外法规的数量必须为 0**（此类命中应在 5A 记入 `kb_gap_report.json`，在 5C 被 `rejected_no_kb_basis` 拦下）。
7. **无重复问题**：同一 `type` + 同一 `reference`+`article` 的问题在最终结果中只出现一次，多条款共性问题用 `affected_clauses` 表达。
8. 每个问题都有非空 `suggestion`（法律层面修订方向）。
9. 问题编号连续；5A、5B 原始结果完整保留，不被 5C 覆盖。
10. 5C 输出交叉审计日志；5D 对"标记待复核"全部裁定；5E 完成编号/格式/引用/一致性终审。
11. Agent6、Agent7 均不新增问题。
12. `summary_report.md` 必须单列"依据缺口"一节，如实告知哪些检查点因知识库缺文件而未能形成结论。

不允许：漏文件、漏条款、无依据判断、非法律法规评价、联网新增问题、跳号、把多个问题并成一条、**把同一问题按条款拆成多个编号**、**用知识库外的法规名充当依据**、**把"审不了"包装成低置信度问题**、口头完成但不落盘。

---

## 7. 防偷懒约束

- 每阶段落盘 `./output/review_log.json`（成功条数、失败条数、重试次数）。
- 每 20 条 `CLAUSE` 输出一次中间小结。
- 每阶段生成结构化结果文件；全部完成前不得输出"任务结束"。
- Agent7 联网核验每条记录检索来源与时间戳，核验失败必须显式记录，不得静默跳过。
