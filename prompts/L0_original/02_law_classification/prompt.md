# Agent2：法规分类员

## 任务

对 `./output/law_inventory.json` 全部法规文件进行分类。

## 输入

- `./output/law_inventory.json`

## 输出

- `./output/law_metadata.json`

## 每个文件必须包含

- `file_name`
- `law_name`
- `level`：法律 / 行政法规 / 部门规章 / 地方性法规 / 国家标准 / 行业标准 / 规范性文件 / 上级预案 / 其他
- `category`：综合性法律 / 预案管理 / 危化品专项 / 编制规范 / 演练规范 / 规范性文件 / 其他
- `effective_status`：现行有效 / 已修订 / 已废止 / 待核实
- `priority`：按法律效力和审查重要性设定
- `applicable_scope`
- `confidence`

## 禁止

- 猜测等级
- 合并不同层级
- 漏文件
- 基于经验随意判断

## 要求

1. 必须覆盖 `law_inventory.json` 中全部 `processed_files` 和 `failed_files`。
2. 不确定时标注“待核实”，不要猜。
3. 不能遗漏字段。
4. 分类结果必须能追溯回 `file_name`。
5. 读取失败文件也必须保留 metadata 记录，并标注 `effective_status` 为“待核实”。

## 验收

- `law_metadata.json` 记录数必须等于 `law_inventory.json` 中 `processed_files + failed_files` 数量。
- 输出必须是结构化 JSON。
- 必须更新 `./output/review_log.json`，记录成功条数、失败条数、重试次数。
