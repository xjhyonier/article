#!/usr/bin/env python3
"""
改造 index.html：添加 GitHub API 层 + Token 设置 + 云端收藏/评论功能
- 收藏：localStorage 本地 + GitHub Reactions API 云端同步
- 评论：GitHub Comments API（公开可见）
- 笔记：保留 localStorage 本地笔记（仅自己可见）
- Token 设置：localStorage 存储，设置面板输入
"""

import re

HTML_FILE = "index.html"

with open(HTML_FILE, "r", encoding="utf-8") as f:
    content = f.read()

# ── 1. 添加新 CSS（在 </style> 前插入）──
new_css = """
        /* ── 收藏数徽章 ── */
        .fav-count-badge {
            font-size: 0.65rem;
            color: #f5a623;
            font-weight: 600;
            margin-left: -2px;
            opacity: 0;
            transition: opacity 0.2s;
        }
        .fav-count-badge.show { opacity: 1; }

        /* ── 设置按钮（顶栏齿轮） ── */
        .settings-btn {
            margin-left: auto;
            background: none;
            border: none;
            color: rgba(255,255,255,0.5);
            font-size: 1.1rem;
            cursor: pointer;
            padding: 6px 10px;
            transition: all 0.2s;
            flex-shrink: 0;
        }
        .settings-btn:hover { color: rgba(255,255,255,0.9); transform: rotate(45deg); }

        /* ── 设置面板 ── */
        .settings-overlay {
            display: none;
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0,0,0,0.35);
            z-index: 1000;
            align-items: center;
            justify-content: center;
        }
        .settings-overlay.show { display: flex; }
        .settings-panel {
            background: #fff;
            border-radius: 16px;
            padding: 28px;
            width: 400px;
            max-width: 90vw;
            box-shadow: 0 20px 60px rgba(0,0,0,0.2);
        }
        .settings-panel h3 {
            font-size: 1.05rem;
            margin-bottom: 16px;
            color: #1a1a2e;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .settings-panel label {
            font-size: 0.85rem;
            color: #5a6474;
            display: block;
            margin-bottom: 6px;
        }
        .settings-panel input[type="text"] {
            width: 100%;
            padding: 10px 14px;
            border: 1.5px solid #e0e4ea;
            border-radius: 8px;
            font-size: 0.88rem;
            outline: none;
            transition: border-color 0.2s;
        }
        .settings-panel input[type="text"]:focus { border-color: #4a6fa5; }
        .settings-panel .hint {
            font-size: 0.75rem;
            color: #9aa3b3;
            margin-top: 6px;
            line-height: 1.5;
        }
        .settings-panel .actions {
            display: flex;
            gap: 10px;
            margin-top: 20px;
            justify-content: flex-end;
        }
        .settings-panel .btn {
            padding: 8px 20px;
            border: none;
            border-radius: 8px;
            font-size: 0.85rem;
            cursor: pointer;
            transition: all 0.2s;
        }
        .settings-panel .btn-primary {
            background: linear-gradient(135deg, #1a1a2e, #4a6fa5);
            color: #fff;
        }
        .settings-panel .btn-primary:hover { filter: brightness(1.1); }
        .settings-panel .btn-secondary {
            background: #f0f2f5;
            color: #5a6474;
        }
        .settings-panel .btn-secondary:hover { background: #e8ecf0; }
        .settings-status {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 0.8rem;
            margin-top: 10px;
            padding: 8px 12px;
            border-radius: 8px;
            background: #f7f9fc;
        }
        .settings-status .dot {
            width: 8px; height: 8px;
            border-radius: 50%;
            flex-shrink: 0;
        }
        .settings-status .dot.ok { background: #52c41a; }
        .settings-status .dot.no { background: #ff4d4f; }

        /* ── 评论区 ── */
        .comments-panel {
            display: none;
            flex-direction: column;
            height: 240px;
            border-top: 1px solid #e8ecf0;
            background: #f7f9fc;
            flex-shrink: 0;
        }
        .comments-panel.show { display: flex; }
        .comments-list {
            flex: 1;
            overflow-y: auto;
            padding: 10px 16px;
        }
        .comments-list::-webkit-scrollbar { width: 4px; }
        .comments-list::-webkit-scrollbar-thumb { background: #d0d5de; border-radius: 4px; }
        .comment-item {
            padding: 8px 0;
            border-bottom: 1px solid #eef1f5;
            font-size: 0.85rem;
            line-height: 1.5;
            animation: fadeIn 0.3s;
        }
        @keyframes fadeIn { from { opacity:0; transform:translateY(4px); } to { opacity:1; transform:translateY(0); } }
        .comment-item:last-child { border-bottom: none; }
        .comment-meta {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 4px;
        }
        .comment-nick {
            font-weight: 600;
            color: #1a1a2e;
            font-size: 0.82rem;
        }
        .comment-time {
            font-size: 0.7rem;
            color: #b0b8c8;
        }
        .comment-text {
            color: #3a3f4b;
            word-break: break-word;
        }
        .comments-empty {
            text-align: center;
            color: #c0c5ce;
            font-size: 0.85rem;
            padding: 30px 0;
        }
        .comments-input-area {
            display: flex;
            gap: 8px;
            padding: 10px 16px;
            border-top: 1px solid #e8ecf0;
            background: #eef1f7;
        }
        .comments-input-area input {
            width: 80px;
            padding: 8px 10px;
            border: 1.5px solid #e0e4ea;
            border-radius: 8px;
            font-size: 0.82rem;
            outline: none;
            flex-shrink: 0;
            transition: border-color 0.2s;
        }
        .comments-input-area input:focus { border-color: #4a6fa5; }
        .comments-input-area input[type="text"]:last-of-type {
            flex: 1;
            width: auto;
        }
        .comments-input-area button {
            padding: 8px 16px;
            background: linear-gradient(135deg, #1a1a2e, #4a6fa5);
            color: #fff;
            border: none;
            border-radius: 8px;
            font-size: 0.82rem;
            cursor: pointer;
            flex-shrink: 0;
            transition: all 0.2s;
        }
        .comments-input-area button:hover { filter: brightness(1.1); }
        .comments-input-area button:disabled { opacity: 0.5; cursor: not-allowed; }

        /* ── 评论区切换按钮 ── */
        .comments-toggle-btn {
            display: none;
            align-items: center;
            gap: 6px;
            padding: 8px 18px;
            border: none;
            background: linear-gradient(135deg, #0f3460 0%, #4a6fa5 100%);
            color: #fff;
            font-size: 0.82rem;
            cursor: pointer;
            transition: all 0.2s;
            border-radius: 8px 8px 0 0;
            flex-shrink: 0;
            font-weight: 500;
        }
        .comments-toggle-btn.show { display: flex; }
        .comments-toggle-btn:hover { filter: brightness(1.1); transform: translateY(-1px); }
        .comments-toggle-btn.active { background: linear-gradient(135deg, #4a6fa5, #0f3460); }

        /* ── 移动端适配 ── */
        @media (max-width: 700px) {
            .comments-toggle-btn#commentsToggleBtn {
                display: none !important;
            }
            .comments-toggle-btn#commentsToggleBtnBottom {
                width: 100%;
                border-radius: 0;
                display: none;
                justify-content: center;
            }
            .comments-toggle-btn#commentsToggleBtnBottom.show {
                display: flex !important;
            }
            .comments-panel {
                height: 280px;
                max-height: 40vh;
            }
            .comments-input-area {
                flex-wrap: wrap;
            }
            .comments-input-area input:first-of-type {
                width: 80px;
            }
            .settings-panel {
                margin: 16px;
            }
        }
"""

content = content.replace("</style>", new_css + "\n    </style>")

# ── 2. 在顶部标签栏添加设置按钮 ──
setting_html = """        <button class="settings-btn" onclick="toggleSettings()" title="设置">⚙️</button>
    </div>
</div>

<!-- 设置面板 -->
<div class="settings-overlay" id="settingsOverlay" onclick="if(event.target===this)toggleSettings()">
    <div class="settings-panel">
        <h3>⚙️ 云端同步设置</h3>
        <label for="ghTokenInput">GitHub Personal Access Token</label>
        <input type="text" id="ghTokenInput" placeholder="ghp_xxxx 或 github_pat_xxxx" autocomplete="off">
        <div class="hint">
            配置 Token 后可使用云端收藏和评论功能。<br>
            创建方式：GitHub → Settings → Developer settings → Personal access tokens → Fine-grained token → 仅勾选 Issues 读写权限。<br>
            不配置 Token 仍可浏览他人的收藏和评论，但无法自己收藏/评论。
        </div>
        <div class="settings-status" id="settingsStatus">
            <span class="dot no" id="settingsDot"></span>
            <span id="settingsMsg">未配置 Token</span>
        </div>
        <div class="actions">
            <button class="btn btn-secondary" onclick="toggleSettings()">取消</button>
            <button class="btn btn-primary" onclick="saveSettings()">保存</button>
        </div>
    </div>
</div>

<!-- 手机端展开/收起索引按钮 -->"""

content = content.replace(
    '    </div>\n</div>\n\n<!-- 手机端展开/收起索引按钮 -->',
    setting_html
)

# ── 3. 替换笔记面板区域为「评论区 + 笔记面板」──
old_notes_html = """        <!-- 笔记面板 -->
        <button class="notes-toggle-btn" id="notesToggleBtnBottom" onclick="toggleNotes()" title="打开笔记">📝 笔记</button>
        <div class="notes-panel" id="notesPanel">
            <div class="notes-panel-header">
                <span>📝 阅读笔记（仅自己可见）</span>
                <span class="saved-msg" id="notesSavedMsg">已保存</span>
                <button class="notes-clear-btn" onclick="clearNote()">清空</button>
            </div>
            <textarea class="notes-textarea" id="notesTextarea" oninput="onNoteInput()" placeholder="在这里写笔记、感想、摘要..."></textarea>
        </div>"""

new_panel_html = """        <!-- 评论区切换按钮（底部） -->
        <button class="comments-toggle-btn" id="commentsToggleBtnBottom" onclick="toggleComments()" title="打开评论区">💬 评论</button>
        <!-- 评论区面板 -->
        <div class="comments-panel" id="commentsPanel">
            <div class="comments-list" id="commentsList">
                <div class="comments-empty">暂无评论，来抢沙发吧 🎉</div>
            </div>
            <div class="comments-input-area">
                <input type="text" id="commentNick" placeholder="昵称" maxlength="20">
                <input type="text" id="commentText" placeholder="写下你的评论..." maxlength="500" onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();submitComment();}">
                <button onclick="submitComment()" id="commentSubmitBtn">发送</button>
            </div>
        </div>
        <!-- 笔记面板（保留，仅自己可见） -->
        <button class="notes-toggle-btn" id="notesToggleBtnBottom" onclick="toggleNotes()" title="打开笔记">📝 笔记</button>
        <div class="notes-panel" id="notesPanel">
            <div class="notes-panel-header">
                <span>📝 私人笔记（仅自己可见）</span>
                <span class="saved-msg" id="notesSavedMsg">已保存</span>
                <button class="notes-clear-btn" onclick="clearNote()">清空</button>
            </div>
            <textarea class="notes-textarea" id="notesTextarea" oninput="onNoteInput()" placeholder="在这里写笔记、感想、摘要..."></textarea>
        </div>"""

content = content.replace(old_notes_html, new_panel_html)

# ── 4. 在 content-header 中添加评论区切换按钮 ──
content = content.replace(
    '<button class="notes-toggle-btn" id="notesToggleBtn" onclick="toggleNotes()" title="打开笔记">📝 笔记</button>',
    '<button class="comments-toggle-btn" id="commentsToggleBtn" onclick="toggleComments()" title="打开评论区">💬 评论</button>\n            <button class="notes-toggle-btn" id="notesToggleBtn" onclick="toggleNotes()" title="打开笔记">📝 笔记</button>'
)

# ── 5. 替换整个 <script> 部分 ──
script_match = re.search(r'<script>\n(.*?)\n</script>', content, re.DOTALL)
if not script_match:
    print("ERROR: Cannot find <script> tag")
    exit(1)

new_script = """
<script>
    let activeCategory = '投资心得';
    let activeLink = null;
    let sidebarCollapsed = true;
    let currentNotePath = null;
    let notesDebounceTimer = null;
    let currentCommentsPath = null;

    // ── GitHub API 配置 ──
    const GH = {
        owner: 'xjhyonier',
        repo: 'article',
        base: 'https://api.github.com/repos/xjhyonier/article',
        issuesMap: null,
        token: localStorage.getItem('gh_token') || '',
    };

    function ghHeaders() {
        const h = { 'Accept': 'application/vnd.github.v3+json', 'X-GitHub-Api-Version': '2022-11-28' };
        if (GH.token) h['Authorization'] = 'Bearer ' + GH.token;
        return h;
    }

    async function ghFetch(endpoint, options = {}) {
        const url = endpoint.startsWith('http') ? endpoint : GH.base + endpoint;
        const resp = await fetch(url, Object.assign({}, options, {
            headers: Object.assign({}, ghHeaders(), options.headers || {})
        }));
        if (!resp.ok) throw new Error('GH API ' + resp.status);
        if (resp.status === 204) return null;
        return resp.json();
    }

    async function loadIssuesMap() {
        if (GH.issuesMap) return GH.issuesMap;
        try {
            const resp = await fetch('data/issues.json');
            GH.issuesMap = await resp.json();
        } catch (e) {
            console.warn('Failed to load issues.json:', e);
            GH.issuesMap = {};
        }
        return GH.issuesMap;
    }

    function getIssueNumber(path) {
        return (GH.issuesMap || {})[path] || null;
    }

    // ── 收藏功能（本地 + 云端同步） ──
    const FAV_KEY = 'article_favorites';
    const FAV_COUNTS_KEY = 'article_fav_counts';

    function getFavs() {
        try { return JSON.parse(localStorage.getItem(FAV_KEY)) || []; }
        catch { return []; }
    }
    function setFavs(arr) {
        localStorage.setItem(FAV_KEY, JSON.stringify(arr));
        updateFavCount();
        refreshFavStars();
    }
    function isFav(path) { return getFavs().includes(path); }

    function getFavCounts() {
        try { return JSON.parse(localStorage.getItem(FAV_COUNTS_KEY)) || {}; }
        catch { return {}; }
    }
    function setFavCounts(obj) {
        localStorage.setItem(FAV_COUNTS_KEY, JSON.stringify(obj));
    }

    function updateFavCount() {
        document.getElementById('fav-count').textContent = getFavs().length;
    }

    function refreshFavStars() {
        const favs = getFavs();
        const counts = getFavCounts();
        document.querySelectorAll('.fav-star').forEach(star => {
            const path = star.getAttribute('data-path');
            if (favs.includes(path)) {
                star.classList.add('active');
                star.textContent = '\\u2605';
                star.title = '取消收藏';
            } else {
                star.classList.remove('active');
                star.textContent = '\\u2606';
                star.title = '收藏';
            }
            // 收藏数徽章
            const anchor = star.closest('.sidebar-link');
            if (!anchor) return;
            let badge = anchor.querySelector('.fav-count-badge');
            const cnt = counts[path] || 0;
            if (cnt > 0) {
                if (!badge) {
                    badge = document.createElement('span');
                    badge.className = 'fav-count-badge show';
                    star.after(badge);
                }
                badge.textContent = cnt;
                badge.classList.add('show');
            } else if (badge) {
                badge.classList.remove('show');
            }
        });
    }

    async function toggleFav(e, starEl) {
        e.stopPropagation();
        e.preventDefault();
        const path = starEl.getAttribute('data-path');
        let favs = getFavs();
        const wasFav = favs.includes(path);
        if (wasFav) {
            favs = favs.filter(p => p !== path);
        } else {
            favs.push(path);
        }
        setFavs(favs);

        const issueNum = getIssueNumber(path);
        if (issueNum && GH.token) {
            try {
                const reactions = await ghFetch('/issues/' + issueNum + '/reactions');
                const myLogin = localStorage.getItem('gh_login') || '';
                const existing = reactions.find(r => r.content === '+1' && r.user && r.user.login === myLogin);
                if (wasFav && existing) {
                    await fetch(GH.base + '/reactions/' + existing.id, {
                        method: 'DELETE',
                        headers: ghHeaders()
                    });
                } else if (!wasFav && !existing) {
                    await ghFetch('/issues/' + issueNum + '/reactions', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ content: '+1' })
                    });
                }
                await refreshFavCount(path, issueNum);
            } catch (err) {
                console.warn('Cloud fav sync failed:', err);
            }
        }
        if (activeCategory === '收藏') renderFavList();
    }

    async function refreshFavCount(path, issueNum) {
        try {
            const reactions = await ghFetch('/issues/' + issueNum + '/reactions');
            const counts = getFavCounts();
            counts[path] = reactions.filter(r => r.content === '+1').length;
            setFavCounts(counts);
            refreshFavStars();
        } catch (e) {
            console.warn('Failed to refresh fav count:', e);
        }
    }

    async function refreshAllFavCounts() {
        const map = await loadIssuesMap();
        const counts = getFavCounts();
        const entries = Object.entries(map).slice(0, 30);
        for (const [path, num] of entries) {
            try {
                const reactions = await ghFetch('/issues/' + num + '/reactions');
                counts[path] = reactions.filter(r => r.content === '+1').length;
            } catch (e) {}
        }
        setFavCounts(counts);
        refreshFavStars();
    }

    function renderFavList() {
        const container = document.getElementById('list-收藏');
        const favs = getFavs();
        container.innerHTML = '';
        if (favs.length === 0) {
            container.innerHTML = '<div style="padding:30px 16px;color:#999;font-size:0.88rem;text-align:center;">还没有收藏的文章<br>点击文章旁的 ☆ 即可收藏</div>';
            return;
        }
        favs.forEach(path => {
            const originalLink = document.querySelector('.fav-star[data-path="' + path + '"]');
            if (!originalLink) return;
            const anchor = originalLink.closest('.sidebar-link');
            if (!anchor) return;
            const title = anchor.getAttribute('title');
            const dateSpan = anchor.querySelector('.art-date');
            const dateText = dateSpan ? dateSpan.textContent : '';
            const dateClass = dateSpan ? dateSpan.className : 'art-date';
            const a = document.createElement('a');
            a.className = 'sidebar-link';
            a.href = '#';
            a.title = title;
            a.onclick = function() { openArticle(this, path); return false; };
            a.innerHTML =
                '<span class="fav-star active" onclick="toggleFav(event, this)" data-path="' + path + '" title="取消收藏">\\u2605</span>' +
                '<span class="link-body" onclick="openArticle(this.parentElement, \\'' + path.replace(/'/g, "\\'") + '\\'); return false;">' +
                '<span class="' + dateClass + '">' + dateText + '</span>' + title +
                '</span>';
            container.appendChild(a);
        });
    }

    // ── 笔记功能（localStorage，仅自己可见） ──
    const NOTES_KEY = 'article_notes';

    function getNotesObj() {
        try { return JSON.parse(localStorage.getItem(NOTES_KEY)) || {}; }
        catch { return {}; }
    }
    function saveNotesObj(obj) {
        localStorage.setItem(NOTES_KEY, JSON.stringify(obj));
    }
    function getNote(path) { return getNotesObj()[path] || ''; }
    function saveNote(path, text) {
        const notes = getNotesObj();
        if (text.trim()) { notes[path] = text; } else { delete notes[path]; }
        saveNotesObj(notes);
    }

    function toggleNotes() {
        const panel = document.getElementById('notesPanel');
        const isOpen = panel.classList.toggle('show');
        document.querySelectorAll('.notes-toggle-btn').forEach(btn => {
            btn.classList.toggle('active', isOpen);
            if (currentNotePath) btn.classList.add('show');
        });
        if (isOpen) document.getElementById('notesTextarea').focus();
        if (window.innerWidth <= 700) {
            document.getElementById('contentWrapper').style.flex = isOpen ? '0.5' : '1';
        }
    }

    function loadNote(path) {
        currentNotePath = path;
        document.getElementById('notesTextarea').value = getNote(path);
        document.getElementById('notesToggleBtn').classList.add('show');
        document.getElementById('notesToggleBtnBottom').classList.add('show');
    }

    function onNoteInput() {
        if (!currentNotePath) return;
        const text = document.getElementById('notesTextarea').value;
        saveNote(currentNotePath, text);
        updateNoteIndicator(currentNotePath);
        const msg = document.getElementById('notesSavedMsg');
        if (msg) {
            msg.classList.add('show');
            clearTimeout(notesDebounceTimer);
            notesDebounceTimer = setTimeout(() => msg.classList.remove('show'), 1200);
        }
    }

    function updateNoteIndicator(path) {
        const star = document.querySelector('.fav-star[data-path="' + path + '"]');
        if (!star) return;
        const anchor = star.closest('.sidebar-link');
        if (!anchor) return;
        let dot = anchor.querySelector('.note-dot');
        if (getNote(path).trim()) {
            anchor.classList.add('has-note');
            if (!dot) { dot = document.createElement('span'); dot.className = 'note-dot'; anchor.appendChild(dot); }
        } else {
            anchor.classList.remove('has-note');
            if (dot) dot.remove();
        }
    }

    function clearNote() {
        if (!currentNotePath) return;
        document.getElementById('notesTextarea').value = '';
        saveNote(currentNotePath, '');
        updateNoteIndicator(currentNotePath);
    }

    function refreshNoteIndicators() {
        const notes = getNotesObj();
        document.querySelectorAll('.fav-star').forEach(function(star) {
            const path = star.getAttribute('data-path');
            if (!path) return;
            const anchor = star.closest('.sidebar-link');
            if (!anchor) return;
            if (notes[path] && notes[path].trim()) {
                anchor.classList.add('has-note');
                if (!anchor.querySelector('.note-dot')) {
                    var dot = document.createElement('span');
                    dot.className = 'note-dot';
                    anchor.appendChild(dot);
                }
            }
        });
    }

    // ── 评论功能（GitHub Comments API） ──
    async function toggleComments() {
        const panel = document.getElementById('commentsPanel');
        const isOpen = panel.classList.toggle('show');
        document.querySelectorAll('.comments-toggle-btn').forEach(btn => btn.classList.toggle('active', isOpen));
        if (isOpen && currentCommentsPath) {
            await loadComments(currentCommentsPath);
            document.getElementById('commentText').focus();
        }
        if (window.innerWidth <= 700) {
            const wrapper = document.getElementById('contentWrapper');
            if (isOpen) {
                document.getElementById('notesPanel').classList.remove('show');
                document.querySelectorAll('.notes-toggle-btn').forEach(b => b.classList.remove('active'));
                wrapper.style.flex = '0.5';
            } else {
                wrapper.style.flex = '1';
            }
        }
    }

    async function loadComments(path) {
        currentCommentsPath = path;
        const issueNum = getIssueNumber(path);
        const listEl = document.getElementById('commentsList');
        if (!issueNum) {
            listEl.innerHTML = '<div class="comments-empty">评论区暂未就绪</div>';
            return;
        }
        listEl.innerHTML = '<div class="comments-empty">加载中...</div>';
        try {
            const comments = await ghFetch('/issues/' + issueNum + '/comments');
            if (!comments || comments.length === 0) {
                listEl.innerHTML = '<div class="comments-empty">暂无评论，来抢沙发吧 🎉</div>';
                return;
            }
            listEl.innerHTML = '';
            comments.forEach(c => {
                let data;
                try { data = JSON.parse(c.body); } catch {
                    data = { nick: c.user?.login || '匿名', text: c.body, time: c.created_at };
                }
                const div = document.createElement('div');
                div.className = 'comment-item';
                const timeStr = data.time ? new Date(data.time).toLocaleDateString('zh-CN', {month:'numeric',day:'numeric',hour:'2-digit',minute:'2-digit'}) : '';
                div.innerHTML = '<div class="comment-meta"><span class="comment-nick">' + escHTML(data.nick || '匿名') + '</span>' +
                    (timeStr ? '<span class="comment-time">' + timeStr + '</span>' : '') +
                    '</div><div class="comment-text">' + escHTML(data.text || '') + '</div>';
                listEl.appendChild(div);
            });
            listEl.scrollTop = listEl.scrollHeight;
        } catch (e) {
            listEl.innerHTML = '<div class="comments-empty">加载失败，请稍后重试</div>';
            console.warn('Load comments failed:', e);
        }
    }

    async function submitComment() {
        const nickEl = document.getElementById('commentNick');
        const textEl = document.getElementById('commentText');
        const btn = document.getElementById('commentSubmitBtn');
        const nick = nickEl.value.trim() || '匿名';
        const text = textEl.value.trim();
        if (!text) return;
        const issueNum = getIssueNumber(currentCommentsPath);
        if (!issueNum) { alert('评论区暂未就绪'); return; }
        if (!GH.token) { alert('请先在设置中配置 GitHub Token 才能评论'); toggleSettings(); return; }
        localStorage.setItem('gh_nick', nick);
        btn.disabled = true;
        btn.textContent = '发送中...';
        try {
            const commentData = { nick: nick, text: text, time: new Date().toISOString() };
            await ghFetch('/issues/' + issueNum + '/comments', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ body: JSON.stringify(commentData) })
            });
            textEl.value = '';
            await loadComments(currentCommentsPath);
        } catch (e) {
            alert('评论发送失败：' + e.message);
        } finally {
            btn.disabled = false;
            btn.textContent = '发送';
        }
    }

    function escHTML(s) {
        const div = document.createElement('div');
        div.textContent = s;
        return div.innerHTML;
    }

    // ── 设置面板 ──
    function toggleSettings() {
        const overlay = document.getElementById('settingsOverlay');
        overlay.classList.toggle('show');
        if (overlay.classList.contains('show')) {
            document.getElementById('ghTokenInput').value = GH.token;
            updateSettingsStatus();
        }
    }

    function updateSettingsStatus() {
        const dot = document.getElementById('settingsDot');
        const msg = document.getElementById('settingsMsg');
        if (GH.token) {
            dot.className = 'dot ok';
            msg.textContent = 'Token 已配置';
            ghFetch('/user').then(user => {
                msg.textContent = '已登录：' + (user.login || '未知');
                localStorage.setItem('gh_login', user.login || '');
            }).catch(() => {
                msg.textContent = 'Token 无效或已过期';
                dot.className = 'dot no';
            });
        } else {
            dot.className = 'dot no';
            msg.textContent = '未配置 Token（仅可浏览，不可收藏/评论）';
        }
    }

    function saveSettings() {
        const token = document.getElementById('ghTokenInput').value.trim();
        GH.token = token;
        localStorage.setItem('gh_token', token);
        updateSettingsStatus();
        setTimeout(() => toggleSettings(), 500);
    }

    // ── 通用功能 ──
    function showLoading() { document.getElementById('loadingOverlay').classList.add('show'); }
    function hideLoading() { document.getElementById('loadingOverlay').classList.remove('show'); }

    function toggleSidebar() {
        const sidebar = document.getElementById('sidebar');
        const toggle = document.getElementById('mobileToggle');
        const toggleText = document.getElementById('toggleText');
        if (window.innerWidth <= 700) {
            sidebarCollapsed = !sidebarCollapsed;
            if (sidebarCollapsed) {
                sidebar.classList.add('collapsed');
                toggle.classList.remove('open');
                toggleText.textContent = '📋 文章索引（点击展开）';
            } else {
                sidebar.classList.remove('collapsed');
                toggle.classList.add('open');
                toggleText.textContent = '📋 文章索引（点击收起）';
            }
        }
    }

    window.addEventListener('resize', function() {
        const sidebar = document.getElementById('sidebar');
        const toggle = document.getElementById('mobileToggle');
        if (window.innerWidth > 700) {
            sidebar.classList.remove('collapsed');
            toggle.classList.remove('open');
        }
    });

    function switchCat(btn, catName) {
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        document.querySelectorAll('.sidebar-list').forEach(d => d.style.display = 'none');
        if (catName === '收藏') {
            renderFavList();
            document.getElementById('list-收藏').style.display = 'flex';
        } else {
            document.getElementById('list-' + catName).style.display = 'flex';
        }
        activeCategory = catName;
        document.getElementById('sidebarSearch').value = '';
        if (catName !== '收藏') resetSidebarLinks(catName);
        if (activeLink) { activeLink.classList.remove('active'); activeLink = null; }
        var targetList = catName === '收藏' ? document.getElementById('list-收藏') : document.getElementById('list-' + catName);
        var firstLink = targetList.querySelector('.sidebar-link');
        if (firstLink) firstLink.click();
        else {
            document.getElementById('welcome').style.display = 'flex';
            document.getElementById('contentWrapper').style.display = 'none';
            document.getElementById('contentHeader').classList.remove('show');
        }
    }

    function openArticle(linkEl, path) {
        if (activeLink) activeLink.classList.remove('active');
        linkEl.classList.add('active');
        activeLink = linkEl;
        if (window.innerWidth <= 700 && !sidebarCollapsed) toggleSidebar();
        document.getElementById('welcome').style.display = 'none';
        document.getElementById('contentWrapper').style.display = 'flex';
        showLoading();
        const iframe = document.getElementById('contentFrame');
        iframe.src = path;
        loadNote(path);
        document.getElementById('commentsToggleBtn').classList.add('show');
        document.getElementById('commentsToggleBtnBottom').classList.add('show');
        if (document.getElementById('commentsPanel').classList.contains('show')) {
            loadComments(path);
        }
        currentCommentsPath = path;
        const header = document.getElementById('contentHeader');
        header.classList.add('show');
        document.getElementById('contentTitle').textContent = linkEl.title || linkEl.textContent;
        document.getElementById('contentDate').textContent =
            (linkEl.querySelector('.art-date') || {}).textContent || '';
        const openLink = document.getElementById('contentOpenLink');
        openLink.href = path;
        openLink.style.display = 'inline';
    }

    function filterSidebar() {
        const keyword = document.getElementById('sidebarSearch').value.trim().toLowerCase();
        const listId = activeCategory === '收藏' ? 'list-收藏' : 'list-' + activeCategory;
        const list = document.getElementById(listId);
        const links = list.querySelectorAll('.sidebar-link');
        let visible = 0;
        links.forEach(link => {
            if (!keyword || link.textContent.toLowerCase().includes(keyword)) {
                link.style.display = ''; visible++;
            } else {
                link.style.display = 'none';
            }
        });
        document.getElementById('sidebarNoResult').style.display = visible === 0 ? 'block' : 'none';
    }

    function resetSidebarLinks(catName) {
        const list = document.getElementById('list-' + catName);
        list.querySelectorAll('.sidebar-link').forEach(a => a.style.display = '');
        document.getElementById('sidebarNoResult').style.display = 'none';
    }

    // ── 初始化 ──
    document.addEventListener('DOMContentLoaded', async function() {
        updateFavCount();
        refreshFavStars();
        refreshNoteIndicators();
        const savedNick = localStorage.getItem('gh_nick');
        if (savedNick) document.getElementById('commentNick').value = savedNick;
        await loadIssuesMap();
        console.log('Issues map loaded:', Object.keys(GH.issuesMap).length, 'articles');
        refreshAllFavCounts();
        if (window.innerWidth <= 700) {
            document.getElementById('sidebar').classList.add('collapsed');
        }
        var firstLink = document.querySelector('#list-' + activeCategory + ' .sidebar-link');
        if (firstLink) firstLink.click();
    });
</script>"""

content = content[:script_match.start()] + new_script + content[script_match.end():]

with open(HTML_FILE, "w", encoding="utf-8") as f:
    f.write(content)

print("index.html 改造完成！")
print("新增功能：")
print("  - GitHub API 云端收藏同步")
print("  - 公开评论区（GitHub Comments API）")
print("  - Token 设置面板")
print("  - 收藏数徽章")
print("  - 保留原有私人笔记功能")
