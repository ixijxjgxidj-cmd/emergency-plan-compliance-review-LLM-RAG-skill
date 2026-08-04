# Agent1：法规盘点员

## 任务

扫描 `./laws/` 下全部 43 个文件，逐个盘点。

## 输入

- `./laws/*`

## 输出

- `./output/law_inventory.json`

## JSON Schema

```json
{
  "total_files": 43,
  "processed_files": [
    {
      "file_name": "",
      "law_name": "",
      "issuer": "",
      "date": "",
      "document_type": "",
      "status": "success"
    }
  ],
  "failed_files": [
    {
      "file_name": "",
      "error_reason": ""
    }
  ],
  "summary": {
    "success": 0,
    "failed": 0
  }
}
```

## 要求

1. 每个文件都必须单独识别。
2. 不确定的信息标记为“待核实”。
3. 不允许跳过文件。
4. 不允许预设法规名单。
5. 不允许合并多个文件结果。
6. 不得因单个文件失败终止整个任务。

## 失败处理

- 读取失败重试 3 次。
- 仍失败则记录到 `failed_files`，继续处理剩余文件。
- 失败记录必须包含 `file_name` 和 `error_reason`。

## 验收

- `processed_files + failed_files` 数量必须等于 43。
- `summary.success + summary.failed` 必须等于 43。
- 输出必须是结构化 JSON，不能只写文字总结。
- 必须更新 `./output/review_log.json`，记录成功条数、失败条数、重试次数。
