# Luogu Record Scraper & Analyzer

这是一个用于抓取洛谷（Luogu OJ）用户做题记录并生成精美 Excel 统计报表的工具集。

## ✨ 主要功能

- **数据抓取**：根据提供的 UID 列表，批量抓取用户的通过记录（AC记录）。支持按日期过滤。
- **数据分析**：自动统计每位用户的 AC 数量。
- **报表生成**：生成包含两个工作表的 Excel 文件：
  - **做题统计**：包含排名、姓名、UID、总 AC 数量。
  - **详细记录**：包含每一道题的详细信息（题号、题目名称、提交时间）。
- **隐私安全**：Cookie 仅在内存中使用，程序结束后立即销毁，不在本地保存文件。

## 📂 目录结构

```text
.
├── json/                 # 存放抓取到的用户原始数据 (JSON格式，自动生成)
├── opt/                  # 存放最终生成的 Excel 报表 (自动生成)
├── src/
│   ├── analyze_records.py # 数据分析与导出脚本
│   ├── config.py          # 配置文件
│   ├── luogu_scraper.py   # 爬虫脚本
│   └── utils.py           # 通用工具函数
├── uids.xlsx             # (用户输入) 需手动创建，包含待查询的用户 UID 与姓名
├── requirements.txt      # Python 依赖列表
└── README.md             # 说明文档
```

## 🛠️ 环境配置

1. **安装 Python**：建议使用 Python 3.9 或更高版本。

2. **创建并激活虚拟环境**（推荐）：
   ```bash
   python -m venv venv
   # Windows (PowerShell):
   .\venv\Scripts\Activate
   # Linux/Mac:
   source venv/bin/activate
   ```

3. **安装依赖**：
   ```bash
   pip install -r requirements.txt
   ```

## 🚀 使用流程

### 第一步：准备用户名单 (`uids.xlsx`)

在项目根目录下创建一个名为 **`uids.xlsx`** 的 Excel 文件。
文件必须包含以下两列（第一行为表头，推荐使用小写）：
- **name**: 用户真实姓名
- **uid**: 洛谷用户数字 ID

**示例内容：**
| name | uid    |
| :--- | :----- |
| 张三 | 123456 |
| 李四 | 654321 |

---

### 第二步：运行爬虫 (`src/luogu_scraper.py`)

该脚本负责从洛谷网站抓取数据。

```bash
python src/luogu_scraper.py
```

**操作说明：**
1. **输入 Cookie**：程序启动后会要求手动输入 `__client_id` 和 `_uid`。
   - *如何获取？* 登录洛谷 -> 按 `F12` 打开开发者工具 -> `Application` 标签页 -> 左侧 `Cookies` -> 点击 `https://www.luogu.com.cn` -> 复制对应的值。
   - *注意*：Cookie 仅用于本次会话，程序关闭后需重新输入。
2. **输入日期**：根据提示输入 `YYYY-MM-DD` 格式的日期，程序将只保留该日期之后的记录。直接回车则抓取所有历史记录。
3. **完成**：抓取的数据会保存在 `json/` 目录下。

---

### 第三步：生成报表 (`src/analyze_records.py`)

该脚本读取 `json/` 目录下的数据并生成汇总报表。

```bash
python src/analyze_records.py
```

**输出结果：**
- 文件路径：`opt/luogu_analysis.xlsx`
- 包含两个 Sheet：
  1. **做题统计**：按刷题量降序排列的汇总表。
  2. **详细记录**：所有被统计的题目明细，按时间排序。

## 📝 注意事项

1. **API 限制**：为避免对洛谷服务器造成压力，爬虫脚本内置了延时等待，请勿私自移除。
2. **Cookie 有效性**：如果程序提示无法获取数据或重定向到登录页，请检查您的 Cookie 是否已过期，尝试重新登录洛谷并获取最新的 Cookie。
3. **数据去重**：生成的报表中，对于同一题目的多次 AC 记录，程序默认只保留最早的一次（按通过时间去重）。
