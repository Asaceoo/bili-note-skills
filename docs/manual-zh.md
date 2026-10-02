# Bili Note Skills 通用手册（中文版）

**版本**：v1.1.0（通用版 / Universal Edition）
**适用**：任何 AI 智能体（Claude Code、Cursor、Codex CLI、WPS AI、WorkBuddy、Cline、Gemini CLI…）以及不使用智能体的纯手工场景
**许可证**：MIT

---

## 1. 这套技能解决什么

B 站上的长课程、技术讲解、图文长文，**看完就忘、检索不到、追问无据**。本仓库提供两个前后衔接的技能：

| 阶段 | 技能 | 输入 | 输出 |
|------|------|------|------|
| ① 提取 | `bili-note` | B 站视频/图文链接 | 带时间戳的转录稿 + 完整原始材料归档 + 笔记预算 |
| ② 增强 | `bili-content-enhance` | 转录稿 Markdown | 6 类学习物料组成的学习包（含质量门禁） |

```
B站链接 ──[bili-note]──→ 转录稿.md ──[bili-content-enhance]──→ 学习包/（6 份物料）
             字幕/ASR/评论/证据索引          摘要/术语/导图/动画/补充/深读
```

两个技能**可独立使用**：只想要转录稿就装 bili-note；手上已有转录稿就装 bili-content-enhance。

---

## 2. 通用性设计（关键）

| 维度 | 约束 | 具体实现 |
|------|------|---------|
| 入口 | 不绑定平台 | 每个技能只有一个入口 `SKILL.md`，标准 frontmatter（`name` + `description`），正文是纯 Markdown 指令 |
| 依赖 | 零第三方库 | bili-note 全部脚本只用 **Python 3.10+ 标准库**；bili-content-enhance 门禁 `validate.js` 只用 **Node 内置模块** |
| 浏览器 | 不绑定工具 | 登录态路线只要求「一个 CDP 代理暴露 `GET /targets` 与 `GET /eval?target=<id>`」，默认基址 `http://localhost:3456`，可用 `--cdp-base` 覆盖。WorkBuddy 的 `web-access` 只是其中一种实现 |
| 网络/密钥 | 无外部 API | 不调用任何付费接口，无需 API Key（仅可选本地 ASR 需下载开源模型） |
| 无智能体 | 可手工执行 | 脚本可直接命令行运行；提示词规范 `references/ai_learning_prompts.md` 可人工照做 |

---

## 3. 安装：按你的平台选一行

| 平台 / 形态 | 放到哪里 | 备注 |
|---|---|---|
| WorkBuddy / CodeBuddy | `~/.workbuddy/skills/<技能名>/` | 触发词自动生效 |
| Claude Code / Claude Desktop | `~/.claude/skills/<技能名>/` | 同上 |
| Codex CLI | `~/.codex/skills/<技能名>/` | 同上 |
| Cursor / Cline / Roo Code / Continue | 项目 `.cursor/skills/` 或等价规则目录 | 把 `SKILL.md` 加进上下文规则 |
| Gemini CLI / OpenHands / Aider | 项目规则 / 自定义指令 | 引入 `SKILL.md` 全文 |
| WPS AI / 豆包 / 通义 / 不支持技能目录的助手 | — | 把 `SKILL.md` 全文贴进系统提示词，或作为上下文文件随素材一起发给模型 |
| 纯手工 | 任意目录 | 命令行跑脚本或照提示词执行 |

```bash
git clone https://github.com/Asaceoo/bili-note-skills.git
cp -r bili-note-skills/skills/bili-note ~/.claude/skills/                # 换成你的平台目录
cp -r bili-note-skills/skills/bili-content-enhance ~/.claude/skills/
```

只取一个技能：

```bash
git clone --filter=blob:none --sparse https://github.com/Asaceoo/bili-note-skills.git
cd bili-note-skills && git sparse-checkout set skills/bili-content-enhance
```

**环境要求**：Python 3.10+（bili-note）、Node 14+（bili-content-enhance 门禁，可选）、Windows / macOS / Linux 均可。
Windows 命令示例用 PowerShell，macOS/Linux 用 bash；路径分隔符按平台用 `\` 或 `/`。

---

## 4. 技能一：bili-note（提取转录稿）

### 4.1 路线选择（由脚本判断，无需猜）

| 路线 | 触发条件 | 需要 |
|------|---------|------|
| 公开字幕/图文（默认） | 视频有公开字幕，或目标是图文/动态 | Python 标准库 + 能访问 B 站公开接口 |
| 网页 AI 字幕 | 接口只返回 `ai-zh` 且 `subtitle_url` 为空 | 已登录 B 站的真实浏览器页面 + 一个 CDP 代理 |
| 音频转写（兜底） | 字幕与 AI 字幕都不可得 | `ffmpeg` + Qwen3-ASR（中文）/ Whisper 系（外语） |

先跑环境检查，再决定路线：

```powershell
# PowerShell：自动探测技能目录
$skill = @("$env:USERPROFILE\.workbuddy\skills\bili-note", "$env:USERPROFILE\.claude\skills\bili-note",
           "$env:USERPROFILE\.codex\skills\bili-note", ".\skills\bili-note") | Where-Object { Test-Path $_ } | Select-Object -First 1
& python "$skill\scripts\check_environment.py"
```

```bash
# bash / zsh
SKILL_DIR="$(ls -d "$HOME"/.workbuddy/skills/bili-note "$HOME"/.claude/skills/bili-note "$HOME"/.codex/skills/bili-note ./skills/bili-note 2>/dev/null | head -1)"
python "$SKILL_DIR/scripts/check_environment.py"
```

### 4.2 一键提取与归档

```bash
python "$SKILL_DIR/scripts/run_bili_note.py" "https://www.bilibili.com/video/BVxxxx/" \
  --work-dir "./tmp_bili_extract" \
  --archive-dir "./知识库/原始材料/BVxxxx_视频短标题" \
  --comments
```

常用参数：`--comments`（抓评论）、`--no-download-images`（图文不下载图片）、`--browser-target <CDP_TARGET_ID>`（走 AI 字幕路线）、`--download-audio --transcribe --asr-backend auto`（音频转写兜底）。

### 4.3 网页 AI 字幕（通用 CDP 路线）

1. 用你的浏览器自动化通道打开**已登录**的 B 站视频页（Chrome / Edge / Firefox 均可），确认页面加载完成。
2. 取 target id：`curl -s http://localhost:3456/targets`（端口不同就换成你的 `cdp-base`）。
3. 下载：`python "$SKILL_DIR/scripts/fetch_browser_ai_subtitles.py" --target <ID> --out ./tmp_bili_extract --cdp-base http://localhost:3456`

脚本只让已登录页面自己请求字幕接口，**不读取、不导出、不保存 Cookie / localStorage / profile / token**。没有可用登录态时跳过本路线并说明覆盖范围。

### 4.4 归档产物

`--archive-dir` 下会生成：`subtitles/{txt,srt,json}`、`articles/`、`images/`、`comments/`、`indexes/`（全文 + 证据索引 `.jsonl`）、`metadata/`（含 `note_budget.json` 笔记预算）。
写笔记前**必须**读 `metadata/note_budget.json`（推荐字数、写作粒度、质量倍率、画面依赖提示），写后用 `score_bili_note.py` 验收。

---

## 5. 技能二：bili-content-enhance（6 类学习物料）

输入一份带 `[mm:ss]` 时间戳的转录稿，输出学习包：

| # | 物料 | 文件 |
|---|------|------|
| ① | 智能摘要（3–8 章节，600–1200 字） | `①智能摘要.md` |
| ② | 术语表（8–15 条，四列：术语/定义/类比/出处） | `②术语表与通俗解释.md` |
| ③ | 知识导图（mermaid mindmap ≤20 节点 + 层级大纲） | `③知识导图.md` |
| ④ | 动画表达（self-contained HTML，无外链） | `④动画表达.html` |
| ⑤ | 补充知识（背景/延伸/误区/实践，📹➕ 来源标注） | `⑤补充知识.md` |
| ⑥ | 深度理解（自检/心智模型/自测题/费曼/迁移） | `⑥深度学习与理解文档.md` |

质量门禁（未通过不得落盘）：

```bash
node scripts/validate.js <学习包目录>
```

校验项：mermaid 语法与节点数、HTML 无 `http(s)` 外链且内联 JS 语法可编译、② 表 4 列 8–15 行非空、① 章节 3–8、⑤/⑥ 章节齐全。无 Node 时按上述规则人工核对。

落盘位置：转录稿所在视频目录下 → 同级 `学习包/`；否则源 md 同级 `学习包/`。二选一，不自造路径。

---

## 6. 无智能体的手工用法

1. 转录稿：`python "$SKILL_DIR/scripts/run_bili_note.py" "<链接>" --archive-dir "<归档目录>"`。
2. 学习包：打开 `skills/bili-content-enhance/references/ai_learning_prompts.md`，按 6 类提示词依次让任意模型（或自己）产出物料。
3. 门禁：`node scripts/validate.js <学习包目录>`，按报错修到全 PASS。

---

## 7. 排错

| 现象 | 原因 | 处理 |
|------|------|------|
| `check_environment.py` 报 CDP 不可达 | 浏览器通道没起 / 端口不是 3456 | 启动通道，用 `--cdp-url` / `--cdp-base` 指定真实基址 |
| 只有 `ai-zh` 没有 `subtitle_url` | B 站普通接口不返回 AI 字幕地址 | 走 §4.3 的 CDP 路线，或用 `import_subtitles.py` 导入浏览器扩展导出的 srt/vtt |
| 长视频字幕极少 | 核心信息在画面 | 读 `note_budget.json` 的 `visual_dependency`；补关键帧/OCR/多模态理解，或标注「有限整理」 |
| ASR 术语识别错（RAG→RG 等） | 语音识别同音误识 | 结合分 P 标题与技术语境校正，并在补充知识里澄清 |
| `validate.js` 报 mermaid 节点含禁用字符 | 节点里出现 `[ ] ( ) " '` | 去掉这些字符，时间戳放到层级大纲 |
| `validate.js` 报 HTML 外链 | 引入了 CDN | 全部内联，或去掉该资源 |
| Windows 路径报错 | 示例用了 `\` | macOS/Linux 换 `/`；`$env:USERPROFILE` 换 `$HOME` |

---

## 8. 隐私与合规

- 登录态仅用于让已登录页面自己请求字幕，脚本不碰 Cookie / token / profile。
- 不强制结束用户浏览器进程。
- 产出笔记与学习包保存在**你自己的本地目录**，不上传任何服务。
- 内容版权归原作者所有；归档材料仅供个人学习与检索使用。

---

## 9. 版本

| 版本 | 变更 |
|------|------|
| v1.0.0 | 首发：bili-content-enhance + bili-note 两个技能 |
| v1.1.0 | **通用版**：去除平台绑定（路径自动探测、浏览器通道抽象为通用 CDP 接口、文案与测试去品牌化），新增中英通用手册 |
