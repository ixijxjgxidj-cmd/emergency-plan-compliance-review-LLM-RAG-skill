# Agent2：法规分类员

## 任务

对 Agent1 盘点到的全部本地法规文件做效力层级、类别、有效状态、优先级标注，并标注与本次预案类型的相关性。

## 输入

- `./output/law_inventory.json`
- `./output/plan_profile.json`

## 输出

- `./output/law_metadata.json`

## 每条记录必须包含

- `file_name`、`relative_path`
- `law_name`、`doc_number`
- `level`：法律 / 行政法规 / 部门规章 / 地方性法规 / 地方政府规章 / 国家标准 / 行业标准 / 地方标准 / 规范性文件 / 上级预案 / 其他
- `category`：综合性法律 / 应急管理基础 / 预案管理 / 事件类别专项 / 编制规范 / 演练与培训规范 / 信息报告与发布 / 事故调查处理 / 规范性文件 / 其他
- `effective_status`：现行有效 / 已修订 / 已废止 / 待核实
- `standard_nature`：强制性 / 推荐性 / 不适用（GB 为强制、GB/T 为推荐；非标准填"不适用"）
- `priority`：按效力层级与审查重要性设定（1 最高）
- `applicable_scope`
- `plan_type_relevance`：核心 / 相关 / 参考 / 不适用 —— 依据 `plan_profile` 的类型、事件类别、层级判定
- `relevance_reason`：为何是该相关性
- `confidence`

## 效力层级排序（供 `priority` 与后续"与上位法冲突"判断）

法律 > 行政法规 > 地方性法规 ≈ 部门规章 > 地方政府规章 > 规范性文件；国家标准中强制性标准（GB）具有强制约束力，推荐性标准（GB/T）被预案明确引用后按其自我约束处理。

## 禁止

- 猜测等级、合并不同层级、漏文件
- 凭经验随意判断有效状态（不确定即"待核实"）
- 把读取失败的文件当作已入库法规

## 要求

1. 必须覆盖 `law_inventory.json` 的 `processed_files` + `failed_files` 全部文件。
2. 读取失败的文件也保留 metadata 记录，`effective_status` 标"待核实"，并标 `usable_for_review: false`。
3. 内容不完整（如只有目录、缺条文）的文件标 `usable_for_review: true` 但 `confidence` 降低，并在 `relevance_reason` 中注明"条文不完整，引用时须降置信度"。
4. 分类结果必须可追溯回 `file_name`。

## 验收

- 记录数 == `law_inventory` 的 processed + failed 数（去重后）。
- 每条都有 `plan_type_relevance` 与 `relevance_reason`。
- 输出结构化 JSON；更新 `./output/review_log.json`。
