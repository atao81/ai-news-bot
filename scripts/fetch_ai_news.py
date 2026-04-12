#!/usr/bin/env python3
"""
AI动向新闻抓取器
- 从 HackerNews、36氪等源抓取 AI 相关新闻
- 生成中文摘要报告
- 支持多种推送方式（Server酱、邮件等）
"""

import json
import urllib.request
import urllib.parse
import os
import sys
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
    "sora", "midjourney", "stable diffusion", "人工智能", "大模型", "智能体",
]

CATEGORIES = {
    "🔥 模型发布与升级": ["release", "launch", "announce", "new model", "upgrade", "发布", "上线"],
    "🏢 公司动态": ["acquire", "join", "fund", "invest", "ipo", "收购", "融资", "加入"],
    "📊 基准与评估": ["benchmark", "eval", "test", "rank", "score", "基线", "评测", "排名"],
    "🔧 工具与框架": ["tool", "framework", "sdk", "api", "library", "工具", "框架"],
    "⚡ 技术突破": ["breakthrough", "novel", "first", "record", "突破", "首次"],
    "🛡️ 安全与治理": ["safety", "align", "regulate", "ban", "policy", "安全", "治理", "监管"],
}

# ============ 抓取 ============
def fetch_json(url, timeout=15):
    """抓取 JSON API"""
    req = urllib.request.Request(url, headers={"User-Agent": "AI-News-Bot/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"  [WARN] fetch failed: {url} -> {e}", file=sys.stderr)
        return None


def fetch_hackernews():
    """从 HackerNews 抓取新闻"""
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

    # 按热度排序
    ai_items.sort(key=lambda x: x["score"], reverse=True)
    return ai_items


def fetch_36kr():
    """从36氪快讯抓取（通过公开API）"""
    items = []
    try:
        url = "https://36kr.com/api/newsflash"
        data = fetch_json(url)
        if data and isinstance(data, dict):
            for item in data.get("data", {}).get("items", [])[:20]:
                title = item.get("title", "")
                if any(kw in title.lower() for kw in AI_KEYWORDS + ["人工智能", "大模型", "AI"]):
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
    """按类别分组"""
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

    # 移除空分类
    result = {k: v for k, v in categorized.items() if v}
    if uncategorized:
        result["📌 其他AI动态"] = uncategorized
    return result


# ============ 生成报告 ============
def generate_report(items, is_morning=True):
    """生成 Markdown 报告"""
    tz = timezone(timedelta(hours=8))
    now = datetime.now(tz)
    period = "早报" if is_morning else "晚报"

    lines = [
        f"# 🤖 AI动向{period} · {now.strftime('%Y年%m月%d日')}",
        "",
        f"> 自动生成于 {now.strftime('%H:%M')} | 共 {len(items)} 条AI相关资讯",
        "",
    ]

    if not items:
        lines.append("今日暂无重大AI动态，风平浪静 🌊")
        return "\n".join(lines)

    # 分类
    categorized = categorize(items)

    # Top 3 热门
    top3 = sorted(items, key=lambda x: x["score"], reverse=True)[:3]
    lines.append("## 🔥 今日热条")
    lines.append("")
    for i, item in enumerate(top3, 1):
        score_str = f"（{item['score']}🔥）" if item["score"] > 0 else ""
        lines.append(f"**{i}. {item['title']}**{score_str}")
        if item["url"]:
            lines.append(f"   🔗 {item['url']}")
        lines.append("")

    # 按分类输出
    if categorized:
        lines.append("---")
        lines.append("")
        for cat, cat_items in categorized.items():
            lines.append(f"## {cat}")
            lines.append("")
            for item in cat_items[:5]:  # 每类最多5条
                score_str = f" `{item['score']}pts`" if item["score"] > 0 else ""
                source_str = f" [{item['source']}]" if item.get("source") else ""
                lines.append(f"- {item['title']}{score_str}{source_str}")
                if item["url"]:
                    lines.append(f"  {item['url']}")
            lines.append("")

    # 一句话总结
    lines.append("---")
    lines.append("")
    lines.append("*由 AI News Bot 自动生成，数据来自 HackerNews / 36氪等公开源*")

    return "\n".join(lines)


# ============ 推送 ============
def push_serverchan(content, title="AI动向"):
    """通过 Server酱 推送到微信"""
    sct_key = os.environ.get("SCT_KEY", "")
    if not sct_key:
        print("[WARN] SCT_KEY not set, skip ServerChan push", file=sys.stderr)
        return False

    url = f"https://sctapi.ftqq.com/{sct_key}.send"
    data = urllib.parse.urlencode({
        "title": title,
        "desp": content,
    }).encode()

    req = urllib.request.Request(url, data=data, headers={"User-Agent": "AI-News-Bot/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            result = json.loads(r.read())
            if result.get("code") == 0:
                print("[OK] ServerChan push success")
                return True
            else:
                print(f"[ERR] ServerChan push failed: {result}", file=sys.stderr)
                return False
    except Exception as e:
        print(f"[ERR] ServerChan push error: {e}", file=sys.stderr)
        return False


def push_email(content, title="AI动向"):
    """邮件推送（预留接口）"""
    # 可通过 GitHub Actions 发邮件，或调用外部 API
    print("[INFO] Email push not implemented yet", file=sys.stderr)
    return False


# ============ 主流程 ============
def main():
    is_morning = "--morning" in sys.argv
    is_evening = "--evening" in sys.argv
    if not is_morning and not is_evening:
        # 默认根据时间判断
        hour = datetime.now(timezone(timedelta(hours=8))).hour
        is_morning = hour < 14

    print("=== AI News Bot ===")
    print(f"Mode: {'早报' if is_morning else '晚报'}")

    # 抓取
    print("\n[1/3] Fetching HackerNews...")
    hn_items = fetch_hackernews()
    print(f"  Got {len(hn_items)} AI items from HackerNews")

    print("[1/3] Fetching 36kr...")
    kr_items = fetch_36kr()
    print(f"  Got {len(kr_items)} AI items from 36kr")

    all_items = hn_items + kr_items
    # 去重（按标题相似度）
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

    # 保存
    tz = timezone(timedelta(hours=8))
    now = datetime.now(tz)
    filename = f"ai_news_{now.strftime('%Y%m%d_%H%M')}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"  Saved to {filename}")

    # 推送
    print("\n[3/3] Pushing...")
    period = "早报" if is_morning else "晚报"
    title = f"🤖 AI动向{period} · {now.strftime('%m/%d')}"

    push_serverchan(report, title)

    # 输出到 stdout 供 GitHub Actions 使用
    print("\n=== REPORT ===")
    print(report)


if __name__ == "__main__":
    main()
