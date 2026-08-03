# Agent1：本地法规盘点员

## 任务

扫描 `./laws/` 下**全部**法规/标准/规范文件（含子目录），逐个盘点。文件总数必须**动态统计**，不得写死任何数字，不得预设法规名单。

`./laws/` 是法规知识库的唯一来源；目录为空时如实记录 `total_files: 0`，不得凭记忆补写法规。

## 输入

- `./laws/**`（排除 `.gitkeep`）
- `./output/plan_profile.json`（用于标注初步相关性、比对基线清单）

## 输出

- `./output/law_inventory.json`

## JSON Schema

```json
{
  "scanned_at": "",
  "total_files": 0,
  "processed_files": [
    {
      "file_name": "",
      "relative_path": "",
      "file_type": "pdf|docx|md|txt|other",
      "law_name": "",
      "issuer": "",
      "doc_number": "",
      "date": "",
      "document_type": "",
      "status": "success"
    }
  ],
  "failed_files": [
    {"file_name": "", "relative_path": "", "error_reason": "", "retry_count": 0}
  ],
  "baseline_missing": [
    {"law_name": "", "necessity": "mandatory|recommended", "note": "基线要求但 ./laws/ 中无对应文件"}
  ],
  "summary": {"success": 0, "failed": 0}
}
```

## 要求

1. 每个文件单独识别，法规名称以**文件内容**为准，文件名仅作辅助。
2. 不确定的信息标 `待核实`，不得猜测。
3. 不允许跳过文件、合并多文件结果、预设法规名单。
4. 单文件失败不得终止整个任务。
5. 同一法规存在多个版本文件时，全部保留并在 `date` / `doc_number` 上体现差异，不得自行取舍。
6. 与 `plan_profile.json` 的 `applicable_law_baseline` 比对，本地无对应文件的记入 `baseline_missing`。这只是**事实记录**，不产生审查结论，也不得据此凭记忆补写条文。

## 失败处理

- 读取失败重试 3 次（记录 `retry_count`）。
- 仍失败记入 `failed_files` 并继续处理剩余文件，`error_reason` 必填。

## 验收

- `total_files` 等于实际扫描到的文件数。
- `len(processed_files) + len(failed_files) == total_files`，且 `summary.success + summary.failed == total_files`。
- 输出结构化 JSON，不能只写文字总结。
- 更新 `./output/review_log.json`（成功条数、失败条数、重试次数）。
