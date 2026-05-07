#!/usr/bin/env python3
"""
生成文章汇总静态页面
- 左侧：分类标签 + 文章列表（侧边栏）
- 中间：iframe 直接展示文章内容
- 文章按发布日期从近到远排序
"""

import os
import re
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(BASE_DIR, "index.html")

CATEGORIES = [
    ("01美元资产", "美元资产"),
    ("02投资心得", "投资心得"),
    ("03其他",     "其他"),
]
DEFAULT_CATEGORY = "投资心得"

DATE_PATTERN = re.compile(
    r'<em[^>]*id="publish_time"[^>]*>'
    r'(\d{4})年(\d{2})月(\d{2})日'
)


def extract_title(folder_name):
    return os.path.basename(folder_name).rstrip("_").strip()


def extract_date(index_file):
    try:
        with open(index_file, "r", encoding="utf-8", errors="ignore") as f:
            head = "".join(f.readline() for _ in range(200))
        m = DATE_PATTERN.search(head)
        if m:
            return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except Exception:
        pass
    return None


def find_articles(category_path):
    articles = []
    if not os.path.isdir(category_path):
        return articles
    for entry in sorted(os.listdir(category_path)):
        d = os.path.join(category_path, entry)
        if not os.path.isdir(d):
            continue
        idx = os.path.join(d, "index.html")
        if not os.path.isfile(idx):
            continue
        pub = extract_date(idx)
        rel = os.path.relpath(idx, BASE_DIR).replace("\\", "/")
        articles.append({
            "title": extract_title(entry),
            "path": rel,
            "date": pub,
        })
    articles.sort(
        key=lambda x: x["date"] or datetime(1970, 1, 1),
        reverse=True,
    )
    return articles


def date_str(dt):
    return dt.strftime("%Y-%m-%d") if dt else ""


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def main():
    all_articles = {}
    for folder, name in CATEGORIES:
        path = os.path.join(BASE_DIR, folder)
        arts = find_articles(path)
        all_articles[name] = arts
        print("[%s] 找到 %d 篇" % (name, len(arts)))

    total = sum(len(v) for v in all_articles.values())

    # ── 构建侧边栏分类标签 ──
    tab_html = []
    for _, name in CATEGORIES:
        cnt = len(all_articles.get(name, []))
        active = " active" if name == DEFAULT_CATEGORY else ""
        tab_html.append(
            '<button class="tab-btn%s" onclick="switchCat(this,\'%s\')">%s'
            '<span class="tab-count">%d</span></button>'
            % (active, name, name, cnt)
        )
    tabs_html = "\n            ".join(tab_html)

    # ── 构建侧边栏文章列表（全部分类，用于 JS 切换） ──
    sidebar_articles_html = []
    for _, name in CATEGORIES:
        arts = all_articles.get(name, [])
        display = "block" if name == DEFAULT_CATEGORY else "none"
        parts = ['<div class="sidebar-list" id="list-%s" style="display:%s">' % (name, display)]
        for art in arts:
            ds = date_str(art["date"])
            title_esc = esc(art["title"])
            if ds:
                date_badge = '<span class="art-date">%s</span>' % ds
            else:
                date_badge = '<span class="art-date unknown">--</span>'
            parts.append(
                '<a class="sidebar-link" href="#" '
                'onclick="openArticle(this, \'%s\'); return false;" '
                'title="%s">%s%s</a>'
                % (art["path"], title_esc, date_badge, title_esc)
            )
        parts.append('</div>')
        sidebar_articles_html.append("\n                ".join(parts))
    sidebar_html = "\n\n                ".join(sidebar_articles_html)

    # ── 第一个文章的路径（默认加载） ──
    default_arts = all_articles.get(DEFAULT_CATEGORY, [])
    first_path = default_arts[0]["path"] if default_arts else ""

    # ── 完整 HTML ──
    html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>文章汇总</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI",
                         "PingFang SC", "Microsoft YaHei", sans-serif;
            height: 100vh;
            overflow: hidden;
        }

        /* ── 顶部标签栏 ── */
        .top-bar {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            color: white;
            display: flex;
            align-items: flex-end;
            padding: 0 20px;
            height: 56px;
            gap: 4px;
            flex-shrink: 0;
        }
        .top-bar h1 {
            font-size: 1.05rem;
            letter-spacing: 1px;
            margin-right: 24px;
            white-space: nowrap;
            opacity: 0.85;
            align-self: center;
        }
        .tab-btn {
            padding: 10px 20px 10px;
            border: none;
            border-radius: 8px 8px 0 0;
            background: rgba(255,255,255,0.13);
            color: rgba(255,255,255,0.65);
            font-size: 0.88rem;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 6px;
            white-space: nowrap;
        }
        .tab-btn:hover { background: rgba(255,255,255,0.25); color: white; }
        .tab-btn.active {
            background: #f5f5f5;
            color: #1a1a2e;
            font-weight: 600;
        }
        .tab-count {
            font-size: 0.72rem;
            background: rgba(0,0,0,0.12);
            padding: 0 6px;
            border-radius: 8px;
            line-height: 1.6;
        }
        .tab-btn.active .tab-count {
            background: #1a1a2e;
            color: white;
        }

        /* ── 主体：左侧边栏 + 右侧内容 ── */
        .main {
            display: flex;
            height: calc(100vh - 56px);
        }

        /* ── 侧边栏 ── */
        .sidebar {
            width: 320px;
            min-width: 320px;
            background: #fafafa;
            border-right: 1px solid #e8e8e8;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        .sidebar-header {
            padding: 14px 16px 10px;
            border-bottom: 1px solid #eee;
        }
        .sidebar-search {
            width: 100%;
            padding: 9px 12px;
            border: 1.5px solid #ddd;
            border-radius: 8px;
            font-size: 0.88rem;
            outline: none;
            transition: border-color 0.2s;
        }
        .sidebar-search:focus { border-color: #1a1a2e; }
        .sidebar-list-scroll {
            flex: 1;
            overflow-y: auto;
            padding: 8px 0;
        }
        /* 文章列表（每个分类一个，JS 切换 display） */
        .sidebar-list {
            display: flex;
            flex-direction: column;
        }
        .sidebar-link {
            display: flex;
            align-items: baseline;
            gap: 8px;
            padding: 10px 16px;
            text-decoration: none;
            color: #333;
            font-size: 0.88rem;
            transition: background 0.15s;
            line-height: 1.4;
            border-left: 3px solid transparent;
        }
        .sidebar-link:hover {
            background: #eee;
        }
        .sidebar-link.active {
            background: #e8eeff;
            border-left-color: #1a1a2e;
            color: #1a1a2e;
            font-weight: 500;
        }
        .art-date {
            flex-shrink: 0;
            font-size: 0.75rem;
            color: #666;
            background: #eee;
            padding: 1px 6px;
            border-radius: 4px;
            font-family: "SF Mono", Consolas, "Menlo", monospace;
            white-space: nowrap;
        }
        .art-date.unknown {
            color: #bbb;
            background: transparent;
        }
        .sidebar-no-result {
            padding: 30px 16px;
            color: #999;
            font-size: 0.88rem;
            text-align: center;
            display: none;
        }

        /* ── 右侧内容区 ── */
        .content {
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        .content-header {
            padding: 12px 20px;
            border-bottom: 1px solid #eee;
            font-size: 0.88rem;
            color: #666;
            display: none;
            align-items: center;
            gap: 10px;
            background: #fafafa;
            flex-shrink: 0;
        }
        .content-header.show { display: flex; }
        .content-header span { color: #999; font-size: 0.82rem; }
        .content-frame {
            flex: 1;
            border: none;
            width: 100%;
        }
        .welcome {
            flex: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #bbb;
            font-size: 1.1rem;
            flex-direction: column;
            gap: 12px;
        }
        .welcome span { font-size: 3rem; }

        /* ── 响应式：小屏幕侧边栏收起 ── */
        @media (max-width: 700px) {
            .sidebar { width: 100%; min-width: unset; height: 45vh; }
            .main { flex-direction: column; }
            .content { height: 55vh; }
        }
    </style>
</head>
<body>

<!-- 顶部标签栏 -->
<div class="top-bar">
    <h1>📚 文章汇总</h1>
    <div style="display:flex; gap:4px; overflow-x:auto;">
        """ + tabs_html + """
    </div>
</div>

<!-- 主体 -->
<div class="main">

    <!-- 左侧边栏 -->
    <div class="sidebar">
        <div class="sidebar-header">
            <input class="sidebar-search"
                   type="text"
                   id="sidebarSearch"
                   placeholder="搜索文章..."
                   oninput="filterSidebar()">
        </div>
        <div class="sidebar-list-scroll">
            """ + sidebar_html + """
            <div class="sidebar-no-result" id="sidebarNoResult">没有找到匹配的文章</div>
        </div>
    </div>

    <!-- 右侧内容区 -->
    <div class="content">
        <div class="content-header" id="contentHeader">
            <strong id="contentTitle"></strong>
            <span id="contentDate"></span>
            <a href="#" id="contentOpenLink" target="_blank"
               style="margin-left:auto; font-size:0.82rem; color:#1a1a2e; display:none;">
               在新窗口打开 ↗</a>
        </div>
        <div class="welcome" id="welcome">
            <span>📖</span>
            从左侧选择一篇文章开始阅读
        </div>
        <iframe class="content-frame" id="contentFrame" style="display:none;"></iframe>
    </div>

</div>

<script>
    let activeCategory = '""" + DEFAULT_CATEGORY + """';
    let activeLink = null;

    // 切换分类
    function switchCat(btn, catName) {
        // 切换标签按钮
        document.querySelectorAll('.tab-btn').forEach(
            b => b.classList.remove('active')
        );
        btn.classList.add('active');
        // 切换侧边栏列表
        document.querySelectorAll('.sidebar-list').forEach(
            d => d.style.display = 'none'
        );
        document.getElementById('list-' + catName).style.display = 'flex';
        activeCategory = catName;
        // 清空搜索
        document.getElementById('sidebarSearch').value = '';
        resetSidebarLinks(catName);
        // 清除当前选中
        if (activeLink) {
            activeLink.classList.remove('active');
            activeLink = null;
        }
        // 自动打开本分类下第一篇文章
        var firstLink = document.querySelector('#list-' + catName + ' .sidebar-link');
        if (firstLink) {
            firstLink.click();
        } else {
            document.getElementById('welcome').style.display = 'flex';
            document.getElementById('contentFrame').style.display = 'none';
            document.getElementById('contentHeader').classList.remove('show');
        }
    }

    // 打开文章
    function openArticle(linkEl, path) {
        if (activeLink) activeLink.classList.remove('active');
        linkEl.classList.add('active');
        activeLink = linkEl;
        const iframe = document.getElementById('contentFrame');
        iframe.src = path;
        iframe.style.display = 'block';
        document.getElementById('welcome').style.display = 'none';
        // 更新 header 信息
        const header = document.getElementById('contentHeader');
        header.classList.add('show');
        document.getElementById('contentTitle').textContent = linkEl.title || linkEl.textContent;
        document.getElementById('contentDate').textContent =
            (linkEl.querySelector('.art-date') || {}).textContent || '';
        const openLink = document.getElementById('contentOpenLink');
        openLink.href = path;
        openLink.style.display = 'inline';
    }

    // 侧边栏搜索过滤
    function filterSidebar() {
        const keyword = document.getElementById('sidebarSearch')
                          .value.trim().toLowerCase();
        const list = document.getElementById('list-' + activeCategory);
        const links = list.querySelectorAll('.sidebar-link');
        let visible = 0;
        links.forEach(link => {
            if (!keyword || link.textContent.toLowerCase().includes(keyword)) {
                link.style.display = '';
                visible++;
            } else {
                link.style.display = 'none';
            }
        });
        document.getElementById('sidebarNoResult').style.display =
            visible === 0 ? 'block' : 'none';
    }

    // 重置侧边栏链接可见性
    function resetSidebarLinks(catName) {
        const list = document.getElementById('list-' + catName);
        list.querySelectorAll('.sidebar-link').forEach(
            a => a.style.display = ''
        );
        document.getElementById('sidebarNoResult').style.display = 'none';
    }

    // 自动打开默认分类的第一篇文章
    document.addEventListener('DOMContentLoaded', function() {
        var firstLink = document.querySelector('#list-' + activeCategory + ' .sidebar-link');
        if (firstLink) {
            firstLink.click();
        }
    });
</script>

</body>
</html>"""

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)

    print("\n[OK] 汇总页面已生成：%s" % OUTPUT_FILE)
    print("   共 %d 篇文章，默认选中「%s」分类" % (total, DEFAULT_CATEGORY))


if __name__ == "__main__":
    main()
