---
name: url-favorites
description: 自动将用户发送的 URL、PDF 或 YouTube 视频收藏到 Obsidian。使用浏览器获取页面内容（支持 JavaScript 渲染），提取并下载图片资源，将页面转换为 Markdown 格式，生成中文摘要后保存。PDF 文件转为文字保存，YouTube 视频生成中文摘要。触发条件：当用户发送 HTTP/HTTPS URL、PDF 文件或 YouTube 链接时自动执行。
---

# URL 收藏技能

当用户发送 HTTP/HTTPS URL、PDF 文件或 YouTube 链接时，自动执行以下流程：

## 1. 获取内容

**URL 场景**：
```bash
browser(action=snapshot, url="<URL>", compact=true)
```
- 使用 `compact=true` 减少无关内容
- 如果页面需要登录或 JavaScript 渲染失败，fallback 到 `web_fetch`

**PDF 场景**：
- 下载 PDF 文件
- 使用 `pdftotext` 提取文字内容
- 如果提取失败，使用 OCR 工具（如 `tesseract`）

**YouTube 场景**：
- 使用 browser 工具获取视频页面
- 提取：视频标题、频道名、发布时间、描述内容
- 尝试获取字幕（如果有的话）
- 如果无法获取字幕，从描述和页面内容提取关键信息

## 2. 提取并保存页面资源

**图片提取与下载**：
- 从页面快照中解析 HTML，提取所有 `<img>` 标签的 `src` 属性
- 包括常见的延迟加载属性：`data-src`, `data-lazy-src` 等
- 创建基于日期和页面标题的独立资源目录：`resources/图库/YYYY-MM-DD-title/`
- 下载图片到本地资源目录（jpg, jpeg, png, gif, webp, svg, bmp 等格式）
- 生成本地图片引用映射表

## 3. 转换为 Markdown

**HTML to Markdown 转换**：
- 将页面内容转换为标准 Markdown 格式
- 保持主要页面结构（标题、段落、列表等）
- 将远程图片链接替换为本地图片路径引用
- 过滤掉装饰性图片（广告、追踪像素等），保留内容相关图片

**语言检测与翻译**：
- 检测页面语言（通过字符占比判断：中文 > 50% 视为中文页面）
- 如果是**中文页面**：标题和摘要保持原样
- 如果是**非中文页面**：将标题翻译成中文，摘要翻译成中文

**翻译工具**：使用模型能力直接翻译（无需额外工具）

## 4. 保存到 Obsidian

**数据存储结构**：
```
Obsidian Vault/
├── 收藏夹/                        # 收藏笔记位置
│   └── YYYY-MM-DD-title.md
└── resources/                    # 存储各种资源
    └── 图库/                     # 存储图片资源
        └── YYYY-MM-DD-title/     # 按页面创建独立目录
            ├── image1.jpg        # 页面中的图片资源
            ├── image2.png
            └── ...              # 其他图片资源
```

**保存路径**：通过命令行参数 `--output-dir` 或 `-o` 配置

**文件名规则**：`YYYY-MM-DD-slug-format.md`
- 日期：使用收藏当天的日期（YYYY-MM-DD）
- slug 生成规则：
  - 从标题提取关键词
  - 英文标题：小写，空格用连字符替换，移除特殊字符
  - 中文标题：保持中文或使用拼音
  - 示例：`2026-03-15-intro-to-rust.md` 或 `2026-03-15-rust 入门.md`

**文件模板（标准格式）**:
```markdown
---
date: <YYYY-MM-DD>
source: <URL>
type: url
tags: [收藏夹]
---

# <中文标题>

**来源**: <URL>

**作者**: <作者/发布者>（如果有）

**发布时间**: <发布时间>（如果有）

---

<页面完整 Markdown 内容>

---

*收藏时间：YYYY-MM-DD HH:mm*
```

**文件模板（详细文章格式）**:
对于内容丰富的文章，可使用更详细的格式：
```markdown
---
date: <YYYY-MM-DD>
source: <URL>
type: url
tags: [收藏夹]
---

# <中文标题>

## 摘要
> <中文摘要，概括页面核心内容>

---

## 核心内容

<页面完整 Markdown 内容>

---

*收藏时间：YYYY-MM-DD HH:mm*
*原文链接: <URL>*
```

## 5. 写入文件

**必须使用 Write 工具写入文件**：

```markdown
Write(
  file_path="<output-dir>/<filename>.md",
  content="<文件内容>"
)
```

- `output-dir`：通过命令行参数 `--output-dir` 或 `-o` 传入
- 文件名格式：`YYYY-MM-DD-slug-format.md`
- 文件内容：使用上述模板格式

**示例**：
```
-o /Users/xuandao/Obsidian/收藏夹
```

生成文件：
```
/Users/xuandao/Obsidian/收藏夹/2026-03-15-intro-to-rust.md
```

## 6. 验收检查（必做）

保存文件后，必须验证以下内容：

1. **内容完整性检查**：
   - 读取保存的文件
   - 确认核心内容已提取并保存
   - 如果内容被截断或丢失，需要重新获取并保存

2. **摘要存在性检查**：
   - 确认文件包含中文摘要（以 `>` 开始的引用块或"核心观点"部分）
   - 摘要应该能概括页面主要内容
   - 如果缺少摘要，需要补充生成

3. **图片引用完整性检查**：
   - 确认 Markdown 中的图片链接已正确替换为本地引用
   - 验证资源目录中存在相应的图片文件
   - 检查图片是否正确显示在 Obsidian 中

4. **文件结构检查**：
   - 确认 frontmatter 完整（date, source, type, tags）
   - 确认标题、来源、收藏时间等字段齐全

如果任何检查项失败，修复后重新保存。

## 7. 配置

- **输出目录**：通过命令行参数 `--output-dir` 或 `-o` 配置
- **资源目录**：通过命令行参数 `--resources-dir` 配置（可选，默认为 output-dir/../resources/图库）
- PDF 文字提取：需要系统安装 `poppler`（提供 pdftotext）
  - macOS: `brew install poppler`
  - Linux: `sudo apt install poppler-utils`
- OCR 备选：需要系统安装 `tesseract`
  - macOS: `brew install tesseract`
  - Linux: `sudo apt install tesseract`
- **HTML to Markdown 转换**：需要安装 `html2text` 和 `beautifulsoup4`
  - `pip install html2text beautifulsoup4`
