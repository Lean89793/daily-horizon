# Daily Horizon

每日 08:00 / 20:00 自动生成双语学习包并邮件推送，配套 Apple 小组件风格学习面板。
**跑在云端，电脑关机也照发。**

---

## 1. 它每天做什么

```
云端定时（08:00 / 20:00 北京时间）
  → 抓取白名单素材（英语新闻 + 财经 / 旅游 / 消费品）
  → 去重库比对，跳过已推过的素材
  → DeepSeek 生成：英译中、生词注释、行业泛读/精读
  → 拼装学习包 Markdown + HTML 邮件
  → SMTP 发送到你的邮箱
  → 回写去重库与周统计 → 重建面板 → 自动提交回仓库
```

面板链接固定（GitHub Pages），打开即最新数据。

---

## 2. 规则落点

| 需求 | 代码位置 |
|---|---|
| 英语三段式（原文→整段翻译→生词，无音标） | `src/prompts.py` → `ENGLISH_SYSTEM` |
| 财经/旅游/消费品 各自的角度、篇幅、注释详略 | `src/prompts.py` → `SECTOR_SPECS` |
| 早晚素材不重复 | `src/state.py` 去重库 + `src/fetch.py` 过滤已推素材 |
| 板块轮换（主攻板块交替、顺序隔周换） | `src/rotation.py` |
| 英语 1h / 行业合计 1.5h | `src/rotation.py` + `main.py` 计时口径 |
| 邮件标题模板 | `config.json` → `mail.subject` |
| 本周进度总览 | `src/package.py` → `_progress_card` |
| 面板四项指标 + 进度条 + 跳转 | `src/panel.py` |
| 周一自动重置周统计 | `src/state.py` → `week_stats` 按 ISO 周计算，无需清零 |
| 不生成练习题 | 三条 Prompt 里均写死排除项 |

---

## 3. 本地试跑（不联网、不发信）

```bash
python main.py --mock --no-mail --force
```

生成后会得到：

- `data/packs/YYYY-MM-DD-morning.md` —— 学习包 Markdown
- `docs/packs/YYYY-MM-DD-morning.html` —— 网页版存档
- `docs/index.html` —— 学习面板（双击即可在浏览器打开）

## 4. 本地真实跑一场

先配好环境变量（PowerShell 示例）：

```powershell
$env:DEEPSEEK_API_KEY="sk-xxxx"
$env:SMTP_USER="你的QQ邮箱@qq.com"
$env:SMTP_PASS="SMTP授权码"
$env:MAIL_TO="你的QQ邮箱@qq.com"
python main.py --slot morning
```

常用参数：

| 参数 | 作用 |
|---|---|
| `--slot morning\|evening` | 指定场次，缺省按当前时间判断 |
| `--date 2026-10-30` | 指定日期（补生成历史） |
| `--no-mail` | 只生成不发信 |
| `--force` | 已有记录也重跑（手动补发） |
| `--mock` | 用样刊内容，不联网不调模型 |

---

## 5. 部署到 GitHub（一次性）

### 5.1 建仓库

私有仓库即可（私有仓库同样能用 Pages，但 Pages 需要仓库为 Public 或使用 GitHub Pro；
若 Pages 打不开，把仓库设为 Public 不影响任何密钥安全——密钥只在 Secrets 里）。

把本目录全部文件推上去。

### 5.2 配 Secrets（Settings → Secrets and variables → Actions）

| 名称 | 值 |
|---|---|
| `DEEPSEEK_API_KEY` | DeepSeek 控制台创建的 API Key |
| `SMTP_USER` | 发件邮箱地址 |
| `SMTP_PASS` | 邮箱 **SMTP 授权码**（不是登录密码） |
| `MAIL_TO` | 收件邮箱，多个用英文逗号分隔 |

### 5.3 配变量（同页面 Variables 标签）

| 名称 | 值 |
|---|---|
| `PANEL_URL` | `https://<用户名>.github.io/<仓库名>/` |

### 5.4 开 Pages

Settings → Pages → Source 选 `Deploy from a branch` → 分支 `main`，目录 `/docs` → Save。
几分钟后 `PANEL_URL` 即可访问，此链接永久固定。

### 5.5 验证

Actions 页面 → Daily Horizon → Run workflow：
- `slot` 选 `morning`，`force` 勾上
- 跑完检查：邮箱是否收到、Pages 面板是否刷新

> 定时任务在首次推送后自动生效。GitHub 免费版定时可能有几分钟延迟，属正常。

---

## 6. 手动补发

Actions → Daily Horizon → Run workflow → 选场次 → 勾 `force` → Run。
补发会重新采集素材、重新生成、重新发信，并覆盖当天的记录与存档。

---

## 7. 邮箱 SMTP 授权码

**QQ 邮箱**：设置 → 账户 → 开启「POP3/SMTP 服务」→ 生成授权码（16 位）。
配置里 `host` 用 `smtp.qq.com`、`port` 465、`ssl` true。

**163 邮箱**：设置 → POP3/SMTP/IMAP → 开启 SMTP → 获取授权码，`host` 改 `smtp.163.com`。

**Gmail**：需开启两步验证后生成「应用专用密码」，`host` 改 `smtp.gmail.com`、`port` 587、`ssl` false。

---

## 8. 目录结构

```
DailyHorizon/
├── main.py                  主编排：采集→生成→组装→发送→记账→刷面板
├── config.json              非敏感配置（邮件服务器、模型、面板地址）
├── src/
│   ├── config.py            配置合并 + 环境变量注入
│   ├── util.py              HTTP / 时间 / 文本工具
│   ├── sources.py           素材白名单（英语源、行业源、过滤词）
│   ├── fetch.py             RSS 解析、时效过滤、去重、补正文
│   ├── extract.py           新闻正文抽取
│   ├── llm.py               DeepSeek 客户端（OpenAI 兼容协议）
│   ├── prompts.py           全部内容规则（改风格只改这里）
│   ├── rotation.py          板块轮换与时长分配
│   ├── package.py           学习包 Markdown + 邮件 HTML
│   ├── mdhtml.py            Markdown→HTML（自动区分英中排版）
│   ├── panel.py             学习面板渲染
│   ├── mailer.py            SMTP 发送
│   ├── state.py             去重库 + 周统计
│   └── sample.py            样刊内容（仅 --mock 使用）
├── data/
│   ├── state.json           去重库与场次记录（需提交）
│   └── packs/               历史学习包 Markdown
├── docs/                    GitHub Pages 根目录
│   ├── index.html           学习面板
│   ├── data.json            面板数据
│   └── packs/               网页版学习包存档
└── .github/workflows/daily.yml
```

---

## 9. 素材源实测结论（2026-10-29）

部署前把候选源全跑了一遍，结果直接影响白名单：

| 源 | 结果 |
|---|---|
| 中新财经 / 华尔街见闻 / 界面 / 钛媒体 | ✅ 当日更新，正文可抓或摘要足够 |
| 品橙旅游 | ✅ 旅游垂直站，当日更新（多为短讯，会多取几篇凑体量） |
| NPR / BBC / Guardian / The Conversation | ✅ 海外源，需海外节点（GitHub Actions 即可） |
| 新华英文 | ✅ 国内可直连，作为英文兜底 |
| 36氪 / 环球旅讯 / 中国日报 RSS | ❌ 已失效或反爬，已移除 |
| 人民网（财经/旅游/房产）、新华财经 | ⚠️ RSS 是历史归档（最新到 2024），已移除 |
| Google News 关键词聚合 | ✅ 海外节点可用，作为旅游/消费品的补充；链接是跳转壳，代码会自动解析真实地址 |

含义：本地跑真实采集时海外源会失败（属网络环境问题，非代码问题），云端 Actions 全部可用。

## 10. 已知边界

- **素材依赖公开正文**：遇到付费墙或纯 JS 渲染的站点，正文抽取会失败，此时降级为「标题＋摘要」，Prompt 里已要求不得假装读过全文。
- **定时延迟**：GitHub 免费版 `schedule` 可能延迟数分钟至十几分钟，不会漏跑。
- **单篇篇幅**：行业材料由模型综合素材重写而非搬运原文，因此不会有版权问题；但素材只有摘要时，深度会受限。
- **某板块当日无素材**：该板块当天跳过，90 分钟按比例重分配给其余板块，总时长口径不变（日志会打印重分配结果）。
- **改动风格不必动代码**：注释详略、篇幅、语气全部在 `src/prompts.py`，改完下次运行即生效。
