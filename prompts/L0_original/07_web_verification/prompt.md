# Agent7：联网核验员

## 任务

对已发现问题通过 **LLM 联网搜索** 进行核验。

## 输入

- `./output/problems_all.json`
- `./output/model_config.json`

## 输出

- `./output/verified_results.json`

## 模型自动识别与联网搜索

### Step 1：读取模型配置

从 `./output/model_config.json` 读取 `model_name`、`base_url`、`api_key`。

### Step 2：探测实际可用模型

向 API 发送一个轻量请求，确认当前配置的模型是否可用，同时探测是否有联网搜索能力：

```python
# 1. 读取配置
config = load_json("./output/model_config.json")
client = OpenAI(base_url=config["base_url"], api_key=config["api_key"])
model = config["model_name"]

# 2. 发送探测请求：询问模型自身信息
probe = client.chat.completions.create(
    model=model,
    messages=[{"role": "user", "content": "你是什么模型？你是否支持联网搜索？请简短回答。"}],
    max_tokens=200,
    temperature=0
)
model_info = probe.choices[0].message.content
# 从回复中判断：模型名称、是否支持联网搜索
```

### Step 3：根据探测结果选择联网搜索策略

**策略判断逻辑：**

```python
# 根据探测回复判断联网搜索方式
model_info_lower = model_info.lower()

if "支持联网" in model_info or "web search" in model_info_lower or "联网搜索" in model_info:
    # 模型明确表示支持联网搜索 → 直接在 prompt 中要求联网
    search_strategy = "prompt_instruction"
    
elif "tool" in model_info_lower or "function" in model_info_lower:
    # 模型支持 tool/function calling → 尝试传 tools 参数
    search_strategy = "tools_param"
    
else:
    # 无法确定 → 先尝试 prompt 指令方式，如果回复中无搜索结果则标记 search_failed
    search_strategy = "prompt_instruction_fallback"
```

### Step 4：执行联网核验

根据选择的策略调用 API：

**方式A：prompt 指令（prompt_instruction）**
```python
system = "你是一个法规核验助手。请使用你的联网搜索功能验证以下法规信息。基于搜索结果回答，搜不到请明确说明。"
user = f"请联网核验：\n法规：{reference_law}\n条款：{article_ref}\n问题：{description}\n\n请搜索验证：1.该法规是否现行有效 2.条款号是否准确 3.条文是否一致"

response = client.chat.completions.create(
    model=model,
    messages=[{"role":"system","content":system},{"role":"user","content":user}],
    temperature=config.get("temperature", 0.3),
    max_tokens=1000
)
```

**方式B：tools 参数（tools_param）**
```python
response = client.chat.completions.create(
    model=model,
    messages=[{"role":"system","content":system},{"role":"user","content":user}],
    tools=[{"type": "web_search"}],
    temperature=config.get("temperature", 0.3),
    max_tokens=1000
)
```

**方式C：兜底（prompt_instruction_fallback）**
与方式A相同，但在输出中标记 `search_method: "unverified_prompt_only"`，说明未确认模型是否真正联网。

### Step 5：判断回复是否包含真实搜索结果

```python
result = response.choices[0].message.content

# 判断是否真的做了联网搜索
if any(kw in result for kw in ["根据搜索", "搜索结果显示", "据查询", "目前现行", "search", "最新版本"]):
    verification = "verified"  # 或 "partially_verified" / "unverified"
else:
    verification = "search_failed"
    notes = "模型回复中未体现联网搜索结果，可能不支持联网"
```

## 允许结论

- **verified**：联网确认法规现行有效，引用准确
- **partially_verified**：法规存在但有细微出入
- **unverified**：搜索不到或法规已废止/修订
- **search_failed**：API 失败、模型不支持联网、或搜索无结果

## 禁止

- 新增问题
- 补查漏检
- 扩大审查范围
- 改变问题编号
- 搜索不到时编造结论

## 输出格式

```json
{
  "issue_id": "P-001",
  "clause_id": "CLAUSE-003",
  "reference_law": "危险化学品安全管理条例",
  "article_ref": "第二十三条",
  "verification_status": "verified",
  "search_summary": "搜索结果显示该法规2011年修订，现行有效...",
  "discrepancies": [],
  "model_used": "mimo-v2.5-pro",
  "search_method": "prompt_instruction",
  "model_supports_search": true
}
```

## 调用参数

- temperature：从 model_config.json 读取（默认 0.3）
- max_tokens：1000
- 重试：失败重试 2 次，间隔 3 秒
- 限流：每条间隔 1 秒

## 验收

- 问题编号必须来自 problems_all.json
- 不得新增问题
- 每条必须有 search_summary、model_used、search_method
- 必须更新 review_log.json