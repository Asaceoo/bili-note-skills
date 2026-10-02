# bilibili-subtitle / vCaptions 扩展与 bili-note 的协同

本文件说明如何把浏览器扩展 **bilibili-subtitle（曾用名「哔哔君」，现品牌 vCaptions）** 与 bili-note 协同使用，并把该扩展导出的字幕纳入 bili-note 的笔记管线。

## 这个扩展是什么

- 开源仓库：`github.com/IndieKKY/bilibili-subtitle`（MIT 许可，1170+ stars，TypeScript，持续维护）。
- 功能：在 B站（及 YouTube）视频页显示**字幕列表**，支持点击跳转到对应时间点、复制 / 下载字幕（srt、vtt）、字幕翻译、AI 总结与字幕问答。
- AI 能力由用户自己配置后端：OpenAI 兼容接口、Gemini，或本地 Ollama（`http://localhost:11434`）。

## 与 bili-note 的关系

bili-note 默认走**服务端**抓字幕（B站公开接口、浏览器自动化通道的登录态、必要时本地 ASR）。扩展则运行在**用户浏览器**里，两者的互补点：

- 当服务端接口拿不到字幕（例如某些只有 AI 字幕、登录态强校验的页面），扩展仍能在已登录的页面里把字幕**下载成 srt/vtt**。
- bili-note 的笔记管线（归档、证据索引、`note_budget.json` 定标、评分）只认标准的结构化目录。**本 skill 提供一个桥接脚本 `scripts/import_subtitles.py`**，把扩展导出的 srt/vtt 转成 bili-note 的提取目录，并复用 `archive_bili_materials.py` 生成完整归档。
- 这样，扩展负责「在浏览器里把字幕掏出来」，bili-note 负责「把字幕变成可检索、可评分的学习笔记」。

## 安全审计结论（已审源码 1.14.1）

| 项目 | 结论 |
|---|---|
| 权限（MV3） | 仅 `sidePanel`、`storage`；**无** `tabs` / `cookies` / `history` / `<all_urls>` |
| 注入范围 | content script 仅匹配 `https://*.bilibili.com/*` |
| 对外请求 | AI 功能只向**用户自行配置**的端点发请求（默认 OpenAI、或 Gemini、或本地 `localhost` Ollama）；源码中**无硬编码外发地址** |
| 数据外发 | 字幕文本仅在用户启用 AI 总结时发往上述自配端点；不存在静默上传 |
| 许可证 | MIT，可审计、可自由集成 |

**安装来源建议**：优先从**官方 Chrome 应用店 / Edge 外接程序**安装，或从上方 GitHub 源码自行构建。注意：你最初给的 `crxsoso.com` 镜像页是第三方重打包的「vCaptions」版本（宣称支持任意网站 + YouTube），而 GitHub MIT 源码 `1.14.1` 的 content script 仅匹配 bilibili.com。两者核心能力一致，但**镜像构建的出处未经本机验证，不建议直接下载其 CRX 安装**。对 bili-note 的 B站场景，GitHub 源码版本已完全够用。

## 协同工作流

1. 在 Chrome/Edge 安装并打开扩展，播放目标 B站视频。
2. 用扩展把字幕**导出为 srt 或 vtt**（支持多 P 时逐个导出）。
3. 运行桥接脚本，把导出文件导入 bili-note 的归档目录：

```powershell
$skill = "<改成你的 bili-note 目录绝对路径>"   # 例如 ~/.workbuddy/skills/bili-note 或 ~/.claude/skills/bili-note
$py = "python"
& $py "$skill\scripts\import_subtitles.py" `
  --input "路径\字幕1.srt" "路径\字幕2.vtt" `
  --bvid "BVxxxx" `
  --part "视频短标题" `
  --archive-dir "D:\knowledge\知识库\Rag技术\原始材料\BVxxxx_视频短标题"
```

4. 脚本会写出 `subtitles/{srt,txt,json}`、`indexes/字幕全集.*`、`indexes/字幕证据索引.*`、`metadata/note_budget.json` 和 `README.md`——与 bili-note 直接抓取的产物完全一致。
5. 之后照常写笔记，并用 `score_bili_note.py` 验收（证据引用计数、压缩比、推荐字数均按 `note_budget.json` 计算）。

## 桥接脚本要点

- 纯标准库实现，零第三方依赖，与 bili-note 默认路线一致。
- 自动识别 SRT 与 VTT（`00:00:01,000` 与 `00:00:01.000` 两种时间格式都支持），跳过 VTT 的 `NOTE`/`STYLE`/`REGION` 注释行。
- 多文件 = 多分 P（`--input` 可传多个）；`--duration` 可覆盖总时长；缺时长时按最后一条 cue 的时间戳推算。
- `--no-archive` 只生成提取目录（供你手动检查），不调用归档逻辑。

## 边界与局限

- 扩展运行在用户浏览器，本 skill 不会、也无法自动驱动扩展；「导入」这一步由你把导出的 srt/vtt 交给桥接脚本来完成。
- 若希望让 bili-note 自动获得字幕，**优先用 `run_bili_note.py` 的服务端路线**；仅当该路线失败时，才用扩展导出 + 桥接脚本作为补充源。
- `note_budget.json` 的互动质量倍率依赖 `metadata/metadata.json`（播放、点赞等）。纯外部导入时该文件缺失，倍率回退为 1.0；如需精确倍率，可先用 `run_bili_note.py` 把元数据抓进同一归档目录，再导入字幕。
