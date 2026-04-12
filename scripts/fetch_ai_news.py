#!/usr/bin/env python3
"""
AI动向新闻抓取器
- 从 HackerNews 抓取 AI 相关新闻
- 生成中文摘要报告
- 通过 QQ邮箱 SMTP 推送
"""

import json
import smtplib
import urllib.request
import urllib.parse
import os
import sys
import email.mime.text
import email.mime.multipart
import email.header
from datetime import datetime, timezone, timedelta

# ============ 配置 ============
SOURCES = {
    "hackernews_top": "https://hn.algolia.com/api/v1/search?tags=front_page&hitsPerPage=30",
    "hackernews_ai": "https://hn.algolia.com/api/v1/search?query=AI+LLM+GPT+Claude+Gemini+DeepSeek&tags=story&hitsPerPage=20",
}

AI_KEYWORDS = [
    "ai", "gpt", "claude", "gemini", "deepseek", "llm", "openai", "anthropic",
    "model", "neural", "transformer", "agent", "copilot", "mistral", "qwen",
    "diffusion", "multimodal", "rag", "fine-tun", "instruct", "chatbot",
    "sora", "midjourney", "stable diffusion", "artificial intelligence",
    "machine learning", "large language", "foundation model",
]

CATEGORIES = {
    "🔥 模型发布与升级": ["release", "launch", "announce", "new model", "upgrade", "debut"],
    "🏢 公司动态": ["acquire", "join", "fund", "invest", "ipo", "partnership", "ceo"],
    "📊 基准与评测": ["benchmark", "eval", "test", "rank", "score", "perf"],
    "🔧 工具与框架": ["tool", "framework", "sdk", "api", "library", "open source"],
    "⚡ 技术突破": ["breakthrough", "novel", "first", "record", "sota", "discover"],
    "🛡️ 安全与治理": ["safety", "align", "regulate", "ban", "policy", "risk"],
}


# ============ 抓取 ============
def fetch_json(url, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": "AI-News-Bot/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"  [WARN] fetch failed: {url} -> {e}", file=sys.stderr)
        return None


def fetch_hackernews():
    items = []
    seen = set()
    for name, url in SOURCES.items():
        data = fetch_json(url)
        if not data:
            continue
        for h in data.get("hits", []):
            title = h.get("title", "")
            objectID = h.get("objectID", "")
            if objectID in seen or not title:
                continue
            seen.add(objectID)
            items.append({
                "title": title,
                "url": h.get("url", f"https://news.ycombinator.com/item?id={objectID}"),
                "score": h.get("points", 0),
                "date": h.get("created_at", "")[:10],
                "source": "HackerNews",
            })

    # 过滤 AI 相关
    ai_items = []
    for item in items:
        title_lower = item["title"].lower()
        if any(kw in title_lower for kw in AI_KEYWORDS):
            ai_items.append(item)

    ai_items.sort(key=lambda x: x["score"], reverse=True)
    return ai_items


def fetch_36kr():
    """从36氪快讯抓取（备用渠道）"""
    items = []
    try:
        url = "https://36kr.com/api/newsflash"
        data = fetch_json(url)
        if data and isinstance(data, dict):
            for item in data.get("data", {}).get("items", [])[:20]:
                title = item.get("title", "")
                if any(kw in title.lower() for kw in ["人工智能", "大模型", "ai"]):
                    items.append({
                        "title": title,
                        "url": item.get("news_url", item.get("web_url", "")),
                        "score": 0,
                        "date": item.get("published_at", "")[:10],
                        "source": "36氪",
                    })
    except Exception as e:
        print(f"  [WARN] 36kr fetch failed: {e}", file=sys.stderr)
    return items


# ============ 分类 ============
def categorize(items):
    categorized = {cat: [] for cat in CATEGORIES}
    uncategorized = []
    for item in items:
        title_lower = item["title"].lower()
        matched = False
        for cat, keywords in CATEGORIES.items():
            if any(kw in title_lower for kw in keywords):
                categorized[cat].append(item)
                matched = True
                break
        if not matched:
            uncategorized.append(item)
    result = {k: v for k, v in categorized.items() if v}
    if uncategorized:
        result["📌 其他AI动态"] = uncategorized
    return result


# ============ 生成报告 ============
def generate_report(items, is_morning=True):
    tz = timezone(timedelta(hours=8))
    now = datetime.now(tz)
    period = "早报" if is_morning else "晚报"

    lines = [
        f"# 🤖 AI动向{period} · {now.strftime('%Y年%m月%d日')}",
        f"",
        f"> 自动生成于 {now.strftime('%H:%M')} | 共 {len(items)} 条AI相关资讯",
        f"",
    ]

    if not items:
        lines.append("今日暂无重大AI动态 🌊")
        return "\n".join(lines)

    # Top 3
    top3 = sorted(items, key=lambda x: x["score"], reverse=True)[:3]
    lines.append("## 🔥 今日热条")
    lines.append("")
    for i, item in enumerate(top3, 1):
        score_str = f"（{item['score']}🔥）" if item["score"] > 0 else ""
        lines.append(f"**{i}. {item['title']}**{score_str}")
        if item["url"]:
            lines.append(f"   🔗 {item['url']}")
        lines.append("")

    # 分类
    categorized = categorize(items)
    if categorized:
        lines.append("---")
        lines.append("")
        for cat, cat_items in categorized.items():
            lines.append(f"## {cat}")
            lines.append("")
            for item in cat_items[:5]:
                score_str = f" `{item['score']}pts`" if item["score"] > 0 else ""
                source_str = f" [{item['source']}]" if item.get("source") else ""
                lines.append(f"- {item['title']}{score_str}{source_str}")
                if item["url"]:
                    lines.append(f"  {item['url']}")
            lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("*由 AI News Bot 自动生成，数据来自 HackerNews 等公开源*")

    return "\n".join(lines)


# ============ 邮件推送（SMTP） ============
def push_email_smtp(content, subject="AI动向", to_email=None):
    """通过 SMTP 发送邮件"""
    # 从环境变量读取配置
    smtp_host = os.environ.get("MAIL_SMTP", "smtp.qq.com")
    smtp_port = int(os.environ.get("MAIL_PORT", "587"))
    smtp_user = os.environ.get("MAIL_FROM", "")
    smtp_pass = os.environ.get("MAIL_PASS", "")
    to_addr = os.environ.get("MAIL_TO", to_email or "77193799@qq.com")

    if not smtp_user or not smtp_pass:
        print("[WARN] MAIL_FROM or MAIL_PASS not set, skip email push", file=sys.stderr)
        return False

    try:
        # 构建邮件
        msg = email.mime.multipart.MIMEMultipart("alternative")
        msg["Subject"] = email.header.Header(subject, "utf-8")
        msg["From"] = email.header.Header(f"AI News Bot <{smtp_user}>", "utf-8")
        msg["To"] = to_addr

        # 纯文本版本（兼容所有邮件客户端）
        plain = email.mime.text.MIMEText(content, "plain", "utf-8")
        msg.attach(plain)

        # HTML版本（更好的展示）
        html = email.mime.text.MIMEText(
            f"<html><body>"
            f"<pre style='font-family:sans-serif;white-space:pre-wrap;word-wrap:break-word'>{content}</pre>"
            f"</body></html>",
            "html", "utf-8"
        )
        msg.attach(html)

        # 发送
        if smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_host, smtp_port)
        else:
            server = smtplib.SMTP(smtp_host, smtp_port)
            server.starttls()

        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, [to_addr], msg.as_string())
        server.quit()

        print(f"[OK] Email sent to {to_addr}")
        return True

    except smtplib.SMTPAuthenticationError:
        print("[ERR] SMTP auth failed: check MAIL_FROM / MAIL_PASS", file=sys.stderr)
        return False
    except Exception as e:
        print(f"[ERR] Email send failed: {e}", file=sys.stderr)
        return False


# ============ 主流程 ============
def main():
    is_morning = "--morning" in sys.argv
    is_evening = "--evening" in sys.argv
    if not is_morning and not is_evening:
        hour = datetime.now(timezone(timedelta(hours=8))).hour
        is_morning = hour < 14

    print("=== AI News Bot ===")
    print(f"Mode: {'早报' if is_morning else '晚报'}")

    # 抓取
    print("\n[1/3] Fetching HackerNews...")
    hn_items = fetch_hackernews()
    print(f"  Got {len(hn_items)} AI items")

    print("[1/3] Fetching 36kr...")
    kr_items = fetch_36kr()
    print(f"  Got {len(kr_items)} AI items from 36kr")

    # 合并去重
    all_items = hn_items + kr_items
    seen_titles = set()
    unique_items = []
    for item in all_items:
        key = item["title"].lower()[:30]
        if key not in seen_titles:
            seen_titles.add(key)
            unique_items.append(item)
    all_items = unique_items

    # 生成报告
    print(f"\n[2/3] Generating report ({len(all_items)} items)...")
    report = generate_report(all_items, is_morning=is_morning)

    # 保存到 latest_report.md（供 archive 步骤使用）
    with open("latest_report.md", "w", encoding="utf-8") as f:
        f.write(report)
    print("  Saved to latest_report.md")

    # 发送邮件
    print("\n[3/3] Sending email...")
    period = "早报" if is_morning else "晚报"
    tz = timezone(timedelta(hours=8))
    now = datetime.now(tz)
    title = f"🤖 AI动向{period} · {now.strftime('%Y年%m月%d日')}"
    push_email_smtp(report, title)

    # 打印报告
    print("\n=== REPORT ===")
    print(report)


if __name__ == "__main__":
    main()
