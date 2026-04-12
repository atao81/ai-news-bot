# 🤖 AI动向早晚报

自动抓取 AI 领域新闻，每天 9:00 / 21:00 推送到 QQ 邮箱。

## 信息源

| 源 | 类型 | 内容 |
|----|------|------|
| HackerNews | API | 全球科技热点（英文） |

## 推送方式

- **QQ 邮箱** → 收到邮件推送（用你的 QQ 邮箱发送）
- 报告同时存档到 `archive/` 目录

## 配置步骤（3分钟搞定）

### 1. 创建 GitHub 仓库并推送

```bash
cd ~/.qclaw/workspace/ai-news-bot
~/bin/gh auth login
~/bin/gh repo create ai-news-bot --public --source=. --push
```

### 2. 开启 QQ 邮箱 SMTP

> 注意：需要开启 SMTP 服务才能发邮件，这一步在 QQ 邮箱官网操作。

1. 打开 [mail.qq.com](https://mail.qq.com) → **设置** → **账户**
2. 找到「POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务」
3. 开启 **SMTP 服务**
4. 按提示发送短信，页面会显示一个 **16位授权码**（不是 QQ 密码！）
5. 复制这个授权码，后面用到

### 3. 配置 GitHub Secrets

在 GitHub 仓库 → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**，添加以下 4 个：

| 名称 | 值 | 说明 |
|------|-----|------|
| `MAIL_FROM` | `你的QQ号@qq.com` | 发件人邮箱 |
| `MAIL_PASS` | `刚才的16位授权码` | SMTP 授权码 |
| `MAIL_TO` | `77193799@qq.com` | 收件人邮箱 |
| `MAIL_SMTP` | `smtp.qq.com` | 固定值 |
| `MAIL_PORT` | `587` | 固定值 |

### 4. 测试

在 GitHub 仓库 → **Actions** 页面，点击 "AI动向早晚报" → **Run workflow** → 手动触发一次测试。

## 自动调度

| 时间 | 模式 |
|------|------|
| 09:00 北京时间 | 早报 |
| 21:00 北京时间 | 晚报 |

## 本地运行

```bash
cd ai-news-bot
python3 scripts/fetch_ai_news.py --morning   # 早报
python3 scripts/fetch_ai_news.py --evening   # 晚报
```

## 自定义

- 编辑 `scripts/fetch_ai_news.py` 中的 `AI_KEYWORDS` 调整关键词
- 编辑 `CATEGORIES` 调整分类规则
- 编辑 `SOURCES` 添加新的信息源
