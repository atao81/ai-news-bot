# 🤖 AI动向早晚报

自动抓取 AI 领域新闻，每天 9:00 / 21:00 推送到微信。

## 信息源

| 源 | 类型 | 内容 |
|----|------|------|
| HackerNews | API | 全球科技热点 |
| 36氪 | API | 国内科技快讯 |

## 推送方式

- **Server酱** → 微信推送（推荐，免费）
- 报告同时存档到 `archive/` 目录

## 配置步骤

### 1. Fork 或创建此仓库

### 2. 配置 Server酱 Key
1. 访问 [sct.ftqq.com](https://sct.ftqq.com/) 用微信扫码登录
2. 获取 SendKey
3. 在 GitHub 仓库 → Settings → Secrets → Actions → 添加 `SCT_KEY`

### 3. 手动触发测试
在 Actions 页面点击 "Run workflow"，选择 morning 或 evening 模式。

## 本地运行

```bash
python3 scripts/fetch_ai_news.py --morning   # 早报
python3 scripts/fetch_ai_news.py --evening   # 晚报
```

## 自动调度

| 时间 | 模式 |
|------|------|
| 09:00 CST | 早报 |
| 21:00 CST | 晚报 |

## 自定义

- 编辑 `scripts/fetch_ai_news.py` 中的 `AI_KEYWORDS` 调整关注关键词
- 编辑 `CATEGORIES` 调整分类规则
- 编辑 `SOURCES` 添加新的信息源
