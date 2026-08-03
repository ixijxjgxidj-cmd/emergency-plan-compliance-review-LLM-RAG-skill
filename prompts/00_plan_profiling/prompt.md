# Agent0：预案画像与类型判定

## 任务

在任何审查动作之前，先读懂"要审的是什么预案"，并据此确定适用法规基线与必备要素清单。后续所有阶段（尤其 Agent1 基线比对、Agent4 结构模板、Agent5A 规则集）都依赖本阶段结论。

## 输入

- `./plan/*`（一个或多个待审预案文件）
- `references/plan_type_matrix.md`

## 输出

- `./output/plan_profile.json`

## 判定维度

逐项判定，判据必须写明"来自预案哪一处文字"：

1. `plan_category`：政府总体应急预案 / 政府专项应急预案 / 部门应急预案 / 企业事业单位综合应急预案 / 企业事业单位专项应急预案 / 现场处置方案 / 村（居）民委员会等基层组织预案 / 重大活动保障方案 / 其他
2. `event_type`：自然灾害 / 事故灾难 / 公共卫生事件 / 社会安全事件 / 综合（多类别）；事故灾难需进一步细分（危险化学品、矿山、建筑施工、交通运输、火灾、特种设备、环境污染、电力、燃气、其他）
3. `admin_level`：国家 / 省 / 市 / 县（区）/ 乡镇（街道）/ 村（社区）/ 企业事业单位
4. `issuer`：编制/发布主体全称
5. `plan_name`、`version`、`issue_date`、`effective_date`（无则"未标明"）
6. `chapter_structure`：章节目录（章题 + 起止位置）
7. `has_basis_chapter`：是否存在"编制依据 / 法律依据 / 编制目的与依据"章节；若有，记 `basis_chapter_location`（章节号 + 位置）
8. `attachments`：附件/附录清单（预案附件是法定必备要素之一）

## 适用法规基线

按 `references/plan_type_matrix.md`，结合上述判定，生成：

- `applicable_law_baseline`：本次审查**应当**适用的法规/标准清单。每条含 `law_name`、`why_applicable`（因哪个判定维度而适用）、`necessity`：mandatory / recommended。
- `required_elements`：该类型预案的**法定必备要素清单**（如总则、组织指挥体系与职责、预防与预警、应急响应与分级、信息报告与发布、后期处置、应急保障、监督管理与演练培训、附则、附件等）。每条含 `element_name`、`legal_basis_hint`（线索性，非最终依据）。

> 注意：`plan_type_matrix.md` 与本阶段输出的基线清单**都只是检索线索**，其法规文号、年份、条文必须在 `./laws/` 中有对应文件（经 Agent1 盘点、Agent3 入库）后，才能被 Agent5 作为审查依据引用。基线中本地缺失的法规只作为"依据缺口"事实记录。本阶段禁止写出具体条文内容。

## 类型无法唯一判定时

- 列出全部候选类型及各自判据与置信度，写入 `ambiguity`。
- **停下来询问用户**确认类型，不得默认按危险化学品或任何单一类型处理。
- 用户确认后把结论与确认方式记入 `user_confirmation`。

## 多份预案

`./plan/` 下有多份文件时：
- 若属同一预案的多个部分（正文 + 附件），合并为一个 profile，`plan_files` 列出全部文件。
- 若是多个独立预案，逐个生成 profile 并放入 `profiles` 数组，后续阶段按预案分别处理，`clause_id` 需带预案前缀区分。

## JSON Schema

```json
{
  "generated_at": "",
  "plan_files": [""],
  "plan_category": "",
  "event_type": "",
  "event_subtype": "",
  "admin_level": "",
  "issuer": "",
  "plan_name": "",
  "version": "",
  "issue_date": "",
  "effective_date": "",
  "has_basis_chapter": true,
  "basis_chapter_location": "",
  "chapter_structure": [
    {"chapter_no": "", "title": "", "position": ""}
  ],
  "attachments": [""],
  "applicable_law_baseline": [
    {"law_name": "", "why_applicable": "", "necessity": "mandatory"}
  ],
  "required_elements": [
    {"element_name": "", "legal_basis_hint": ""}
  ],
  "judgement_evidence": [
    {"dimension": "", "evidence_text": "", "source_position": ""}
  ],
  "ambiguity": [],
  "user_confirmation": "",
  "notes": ""
}
```

## 禁止

- 凭预案文件名猜类型（必须有正文判据）
- 默认按危险化学品处理
- 在本阶段写出具体法规条文
- 跳过 `required_elements`（后续缺失要素审查依赖它）

## 验收

- `plan_profile.json` 落盘且字段完整。
- 每个判定维度都有 `judgement_evidence`。
- `applicable_law_baseline` 与 `required_elements` 均非空。
- 更新 `./output/review_log.json`。
