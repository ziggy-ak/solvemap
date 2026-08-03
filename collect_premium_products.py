#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Generate Premium Pages for SolveMap
Reads premium.txt (YAML blocks) and bundles.yaml, creates HTML pages for guides and bundles.
Run: python generate_premium_pages.py
"""
import re
import yaml
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import xml.etree.ElementTree as ET

# ============================================================
# НАСТРОЙКИ
# ============================================================
SITE_NAME = "SolveMap"
SITE_TAGLINE = "a library of solutions"
SITE_OUTPUT = Path("site_output")
PREMIUM_DIR = SITE_OUTPUT / "premium"
GUIDES_DIR = PREMIUM_DIR / "guides"
BUNDLES_DIR = PREMIUM_DIR / "bundles"
PREMIUM_DATA_FILE = "premium.txt"
BUNDLES_FILE = "bundles.yaml"
SUBSCRIBE_URL = "https://script.google.com/macros/s/AKfycbwKzazGv4KsmpHuwRLcF7hod3tXJq9anPnKzRjvEqaaHUOKzn_8zAgSNkF0kxX-U2Mn/exec"

# ============================================================
# БЭКЕНД ДЛЯ ЗАКАЗОВ (Google Apps Script)
# ============================================================
APP_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwfqj5baN3EJCiV6a-CgANOJtG1cClOhcjTatOGQJ9WfUlgCklRXYq8UHeS5eNY5Igc/exec"
WALLET_ADDRESS = "0xB66A7655f83Ed60Fc85973c2df7F5e447d52B3bd"

# ============================================================
# ПЛАТЁЖНЫЕ ССЫЛКИ (Card2Crypto) - уже есть
# ============================================================
PAYMENT_LINKS = {
  "ai-bundle": "https://pay.card2crypto.org/process-payment.php?address=bA29BVXjDktdlSPIA0Hm5aiMANi4hk%2FIdJlRwD2cZ2hHI67hODGPH9Es5cun89046hpJkgC31Nz%2Bx2oAwFQyeQ%3D%3D&amount=29&provider=stripe&email=alexkudrbisines17539%40gmail.com&currency=USD",
  # ... (остальные ссылки, которые мы создали ранее, остаются)
  # Для работы новой системы мы будем генерировать ссылки динамически, но старые ссылки можно оставить как запасной вариант.
}

# ============================================================
# КОНФИГУРАЦИЯ КАТЕГОРИЙ И ЦВЕТОВ
# ============================================================
COLORS = {
    'health': {'primary': '#1e40af', 'accent': '#3b82f6'},
    'fitness': {'primary': '#1e3a8a', 'accent': '#f59e0b'},
    'finance': {'primary': '#065f46', 'accent': '#10b981'},
    'technology': {'primary': '#0f172a', 'accent': '#06b6d4'},
    'nutrition': {'primary': '#78350f', 'accent': '#eab308'},
    'career': {'primary': '#1e293b', 'accent': '#94a3b8'},
    'study': {'primary': '#4c1d95', 'accent': '#8b5cf6'},
    'travel': {'primary': '#0f172a', 'accent': '#f97316'},
    'relationships': {'primary': '#9d174d', 'accent': '#f472b6'},
    'productivity': {'primary': '#1e293b', 'accent': '#8b5cf6'},
}

ALL_CATEGORIES = [
    {"id": "fitness", "icon": "🏋️", "title": "Fitness"},
    {"id": "finance", "icon": "💰", "title": "Finance"},
    {"id": "health", "icon": "🩺", "title": "Health"},
    {"id": "nutrition", "icon": "🥗", "title": "Nutrition"},
    {"id": "career", "icon": "💼", "title": "Career"},
    {"id": "study", "icon": "📚", "title": "Study"},
    {"id": "technology", "icon": "💻", "title": "Technology"},
    {"id": "travel", "icon": "✈️", "title": "Travel"},
    {"id": "relationships", "icon": "💕", "title": "Relationships"},
    {"id": "productivity", "icon": "⏰", "title": "Productivity"}
]

SOCIALS = {
    "pinterest": "https://pinterest.com/solvemap/",
    "tiktok": "https://www.tiktok.com/@solvemap",
    "youtube": "https://www.youtube.com/@solvemap_top",
    "telegram": "https://t.me/solvemap"
}

# ============================================================
# ФУНКЦИИ ПОДПИСКИ И ПРОЧЕЕ (без изменений)
# ============================================================
def get_subscribe_styles():
    return """
    .footer-subscribe {
        display: flex;
        align-items: center;
        gap: 10px 16px;
        flex-wrap: wrap;
        width: 100%;
        padding: 8px 0 12px;
        border-bottom: 1px solid #eef2f0;
        margin-bottom: 10px;
    }
    .footer-subscribe .label {
        font-size: 14px;
        font-weight: 500;
        color: #0f172a;
        white-space: nowrap;
    }
    .footer-subscribe .subscribe-form {
        display: flex;
        align-items: center;
        gap: 8px;
        flex: 0 1 auto;
    }
    .footer-subscribe .subscribe-form input[type="email"] {
        width: 200px;
        height: 32px;
        padding: 4px 12px;
        font-size: 14px;
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        outline: none;
        font-family: 'Inter', sans-serif;
        transition: border-color 0.2s;
        box-sizing: border-box;
    }
    .footer-subscribe .subscribe-form input[type="email"]:focus {
        border-color: #1e3a8a;
    }
    .footer-subscribe .subscribe-form button {
        height: 32px;
        padding: 4px 18px;
        font-size: 14px;
        font-weight: 600;
        background: #1e3a8a;
        color: #ffffff;
        border: none;
        border-radius: 6px;
        cursor: pointer;
        font-family: 'Inter', sans-serif;
        white-space: nowrap;
        transition: background 0.2s;
        box-sizing: border-box;
    }
    .footer-subscribe .subscribe-form button:hover {
        background: #2563eb;
    }
    .footer-subscribe .subscribe-message {
        font-size: 13px;
        padding: 2px 10px;
        border-radius: 4px;
        display: none;
        flex-basis: 100%;
    }
    .footer-subscribe .subscribe-message.success {
        display: block;
        color: #166534;
    }
    .footer-subscribe .subscribe-message.error {
        display: block;
        color: #991b1b;
    }
    @media (max-width: 600px) {
        .footer-subscribe {
            flex-direction: column;
            align-items: stretch;
            gap: 6px;
        }
        .footer-subscribe .subscribe-form {
            flex-direction: column;
            align-items: stretch;
            gap: 6px;
        }
        .footer-subscribe .subscribe-form input[type="email"],
        .footer-subscribe .subscribe-form button {
            width: 100%;
            height: 38px;
            font-size: 15px;
        }
        .footer-subscribe .subscribe-form input[type="email"] {
            width: 100%;
        }
        .footer-subscribe .label {
            font-size: 15px;
        }
    }
    """

def get_subscribe_script():
    return f"""
    <script>
    (function() {{
        const SUBSCRIBE_URL = "{SUBSCRIBE_URL}";
        
        function handleSubscribeForm(form) {{
            const emailInput = form.querySelector('input[type="email"]');
            const messageDiv = form.parentElement.querySelector('.subscribe-message');
            const email = emailInput.value.trim();
            
            if (!email || !email.includes('@')) {{
                showMessage(messageDiv, 'Please enter a valid email.', 'error');
                return;
            }}
            
            const source = form.dataset.source || 'unknown';
            const url = SUBSCRIBE_URL + '?email=' + encodeURIComponent(email) + '&source=' + encodeURIComponent(source);
            
            fetch(url)
            .then(response => response.text())
            .then(text => {{
                try {{
                    return JSON.parse(text);
                }} catch (e) {{
                    if (response.ok) {{
                        return {{ success: true, message: 'Subscribed!' }};
                    }} else {{
                        return {{ success: false, error: 'Server error' }};
                    }}
                }}
            }})
            .then(data => {{
                if (data.success) {{
                    showMessage(messageDiv, '✅ You are subscribed!', 'success');
                    emailInput.value = '';
                }} else {{
                    let errorMsg = data.message || data.error || 'Something went wrong.';
                    showMessage(messageDiv, '❌ ' + errorMsg, 'error');
                }}
            }})
            .catch(error => {{
                console.error('Subscribe error:', error);
                showMessage(messageDiv, '✅ You are subscribed!', 'success');
                emailInput.value = '';
            }});
        }}
        
        function showMessage(container, text, type) {{
            if (!container) return;
            container.textContent = text;
            container.className = 'subscribe-message ' + type;
            container.style.display = 'block';
            clearTimeout(container._timeout);
            container._timeout = setTimeout(() => {{
                container.style.display = 'none';
            }}, 5000);
        }}
        
        document.addEventListener('DOMContentLoaded', function() {{
            document.querySelectorAll('.subscribe-form').forEach(function(form) {{
                form.addEventListener('submit', function(e) {{
                    e.preventDefault();
                    handleSubscribeForm(form);
                }});
            }});
        }});
    }})();
    </script>
    """

def render_footer_with_form(source="unknown"):
    social_icons = {
        'pinterest': '<svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12c0 4.23 2.66 7.86 6.45 9.21-.09-.78-.17-1.98.03-2.83.18-.76 1.15-4.88 1.15-4.88s-.29-.58-.29-1.44c0-1.35.78-2.36 1.76-2.36.83 0 1.23.62 1.23 1.37 0 .84-.53 2.09-.81 3.25-.23.97.49 1.76 1.44 1.76 1.73 0 3.06-1.82 3.06-4.45 0-2.33-1.67-3.95-4.06-3.95-2.77 0-4.39 2.08-4.39 4.23 0 .84.32 1.74.72 2.23.08.1.09.18.06.28-.07.29-.23.91-.26 1.04-.04.18-.14.22-.33.13-1.24-.58-2.02-2.38-2.02-3.83 0-3.12 2.27-5.99 6.54-5.99 3.43 0 6.1 2.45 6.1 5.72 0 3.41-2.15 6.16-5.14 6.16-1 0-1.94-.52-2.26-1.13 0 0-.49 1.88-.61 2.34-.22.85-.82 1.92-1.22 2.57.92.28 1.9.44 2.92.44 5.52 0 10-4.48 10-10S17.52 2 12 2z"/></svg>',
        'tiktok': '<svg viewBox="0 0 24 24"><path d="M16.6 5.82s.51.5 0 0A4.278 4.278 0 0 1 15.54 3h-3.09v12.4a2.592 2.592 0 0 1-2.59 2.5c-1.42 0-2.6-1.16-2.6-2.6 0-1.44 1.18-2.6 2.6-2.6.26 0 .51.04.75.12v-3.1a5.7 5.7 0 0 0-5.16 5.63c0 3.11 2.5 5.63 5.6 5.63 3.1 0 5.6-2.52 5.6-5.63V8.3c1.13.77 2.48 1.2 3.9 1.2V6.24c-.68 0-1.35-.24-1.9-.67z"/></svg>',
        'youtube': '<svg viewBox="0 0 24 24"><path d="M21.58 7.19c-.23-.86-.91-1.54-1.77-1.77C18.25 5 12 5 12 5s-6.25 0-7.81.42c-.86.23-1.54.91-1.77 1.77C2 8.75 2 12 2 12s0 3.25.42 4.81c.23.86.91 1.54 1.77 1.77C5.75 19 12 19 12 19s6.25 0 7.81-.42c.86-.23 1.54-.91 1.77-1.77C22 15.25 22 12 22 12s0-3.25-.42-4.81zM10 15.5v-7l6 3.5-6 3.5z"/></svg>',
        'telegram': '<svg viewBox="0 0 24 24"><path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/></svg>'
    }
    form_html = f"""
    <div class="footer-subscribe">
        <span class="label">📬 Get free guides</span>
        <form class="subscribe-form" data-source="{source}">
            <input type="email" placeholder="Your email address" required />
            <button type="submit">Subscribe</button>
        </form>
        <div class="subscribe-message"></div>
    </div>
    """
    html = f'<footer class="footer">'
    html += form_html
    html += f'<div style="display:flex;flex-wrap:wrap;justify-content:space-between;align-items:center;width:100%;gap:12px;">'
    html += f'<span>{SITE_NAME} — {SITE_TAGLINE}</span>'
    html += f'<div class="socials"><span class="label">Follow us:</span>'
    for key, url in SOCIALS.items():
        icon = social_icons.get(key, '')
        html += f'<a href="{url}" title="{key.capitalize()}">{icon}</a>'
    html += '</div></div></footer>'
    return html

# ============================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================
def get_category_colors(category_id):
    return COLORS.get(category_id, COLORS['productivity'])

def get_category_icon(category_id):
    for cat in ALL_CATEGORIES:
        if cat['id'] == category_id:
            return cat['icon']
    return '📄'

def slugify(text):
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')

def load_premium_guides(filepath):
    if not Path(filepath).exists():
        print(f"⚠️ File not found: {filepath}")
        return []
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    blocks = [b.strip() for b in content.split('---') if b.strip()]
    guides = []
    for block in blocks:
        try:
            doc = yaml.safe_load(block)
            if doc and isinstance(doc, dict):
                sections = doc.get('sections', [])
                for sec in sections:
                    if sec.get('type') == 'cover':
                        badge = sec.get('badge', '')
                        match = re.search(r'\$(\d+)', badge)
                        if match:
                            doc['price'] = int(match.group(1))
                        break
                guides.append(doc)
        except Exception as e:
            print(f"⚠️ YAML parsing error in block: {e}")
    return guides

def load_bundles(filepath):
    if not Path(filepath).exists():
        print(f"⚠️ Bundles file not found: {filepath}")
        return []
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    blocks = [b.strip() for b in content.split('---') if b.strip()]
    if len(blocks) > 1:
        bundles = []
        for block in blocks:
            doc = yaml.safe_load(block)
            if doc:
                bundles.append(doc)
        return bundles
    else:
        docs = yaml.safe_load(content)
        if isinstance(docs, list):
            return docs
        elif isinstance(docs, dict):
            return [docs]
        return []

# ============================================================
# ФУНКЦИИ ХЕДЕРА И МОБИЛЬНОГО МЕНЮ
# ============================================================
def build_header_cats(root_prefix, active_id=None):
    html = f'<a href="{root_prefix}premium/" style="color:#f59e0b;font-weight:700;">⭐ Premium</a>'
    html += f'<a href="{root_prefix}services/">Services</a>'
    for c in ALL_CATEGORIES:
        active = 'active' if c['id'] == active_id else ''
        html += f'<a href="{root_prefix}premium/{c["id"]}/" class="{active}">{c["title"]}</a>'
    return html

def build_mobile_menu(root_prefix, home_prefix, active_id=None):
    html = f'<div class="menu-back" onclick="window.location.href=\'{home_prefix}index.html\'">← Home</div>'
    html += f'<a href="{root_prefix}premium/" style="color:#f59e0b;font-weight:700;">⭐ Premium</a>'
    html += f'<a href="{root_prefix}services/">🛠️ Services</a>'
    for cat in ALL_CATEGORIES:
        active = 'active' if cat['id'] == active_id else ''
        html += f'<a href="{root_prefix}premium/{cat["id"]}/" class="{active}">{cat["title"]}</a>'
    return html

def build_logo_with_badge():
    return f'{SITE_NAME} <span>solutions</span> <span style="background:#f59e0b;color:#0f172a;font-size:11px;font-weight:700;padding:2px 10px;border-radius:40px;margin-left:6px;">Premium</span>'

def build_premium_sidebar(category_id, bundles, guides_dict, active_bundle_slug=None, active_guide_slug=None, root_prefix="../"):
    cat_bundles = [b for b in bundles if b.get('category') == category_id]
    if not cat_bundles:
        return '<div class="sidebar">No bundles</div>'

    html = '<div class="sidebar">'
    html += '<div class="sidebar-title">📁 Bundles</div>'
    html += f'<div class="back-link" onclick="window.location.href=\'{root_prefix}premium/\'">← All Premium</div>'
    html += '<ul>'

    for b in cat_bundles:
        b_slug = b.get('slug') or slugify(b.get('title', ''))
        is_active_bundle = (b_slug == active_bundle_slug)
        bundle_url = f"{root_prefix}premium/bundles/{b_slug}/"
        active_class = 'active' if is_active_bundle else ''
        html += f'<li class="{active_class}" onclick="window.location.href=\'{bundle_url}\'">{b.get("title", "Bundle")}</li>'

        if is_active_bundle:
            html += '<ul style="list-style:none;padding-left:20px;">'
            guide_names = b.get('guides', [])
            for g_name in guide_names:
                guide = None
                for g in guides_dict:
                    if g.get('title', '').lower() == g_name.lower():
                        guide = g
                        break
                if guide:
                    g_slug = slugify(guide.get('title', 'untitled'))
                    is_active_guide = (g_slug == active_guide_slug)
                    g_active_class = 'active' if is_active_guide else ''
                    guide_url = f"{root_prefix}premium/guides/{g_slug}/"
                    html += f'<li class="file-item {g_active_class}" onclick="window.location.href=\'{guide_url}\'">{guide.get("title", "Untitled")}</li>'
            html += '</ul>'

    html += '</ul></div>'
    return html

# ============================================================
# ГЕНЕРАЦИЯ СТРАНИЦ
# ============================================================

def generate_guide_page(guide, output_dir, all_guides=None, all_bundles=None, guide_to_bundle=None):
    title = guide.get('title', 'Untitled')
    subtitle = guide.get('subtitle', '')
    category = guide.get('category', 'productivity')
    subcategory = guide.get('subcategory', '')
    price = guide.get('price', 5)
    what_you_get = guide.get('what_you_get', [])
    sections = guide.get('sections', [])

    slug = slugify(title)
    colors = get_category_colors(category)
    primary = colors['primary']
    accent = colors['accent']
    icon = get_category_icon(category)

    root_prefix = "../../../"
    home_prefix = "../../../"
    logo_html = build_logo_with_badge()

    # ---- Сайдбар ----
    bundle = None
    if guide_to_bundle:
        bundle = guide_to_bundle.get(title.lower())
    active_bundle_slug = bundle.get('slug') if bundle else None
    sidebar_html = build_premium_sidebar(
        category_id=category,
        bundles=all_bundles,
        guides_dict=all_guides,
        active_bundle_slug=active_bundle_slug,
        active_guide_slug=slug,
        root_prefix=root_prefix
    )

    # ---- Хлебные крошки ----
    if bundle:
        bundle_slug = bundle.get('slug') or slugify(bundle.get('title', 'bundle'))
        breadcrumbs = f'''
        <nav class="breadcrumbs" style="font-size:14px;color:#64748b;margin-bottom:20px;padding:8px 0;border-bottom:1px solid #f1f4f9;">
            <a href="../../../index.html" style="color:#1e3a8a;text-decoration:none;font-weight:500;">Home</a>
            <span style="margin:0 6px;color:#94a3b8;">→</span>
            <a href="../../index.html" style="color:#1e3a8a;text-decoration:none;font-weight:500;">Premium</a>
            <span style="margin:0 6px;color:#94a3b8;">→</span>
            <a href="../../{category}/" style="color:#1e3a8a;text-decoration:none;font-weight:500;">{category.capitalize()}</a>
            <span style="margin:0 6px;color:#94a3b8;">→</span>
            <a href="../../bundles/{bundle_slug}/" style="color:#1e3a8a;text-decoration:none;font-weight:500;">{bundle.get('title', 'Bundle')}</a>
            <span style="margin:0 6px;color:#94a3b8;">→</span>
            <span style="color:#0f172a;font-weight:600;">{title}</span>
        </nav>
        '''
    else:
        breadcrumbs = f'''
        <nav class="breadcrumbs" style="font-size:14px;color:#64748b;margin-bottom:20px;padding:8px 0;border-bottom:1px solid #f1f4f9;">
            <a href="../../../index.html" style="color:#1e3a8a;text-decoration:none;font-weight:500;">Home</a>
            <span style="margin:0 6px;color:#94a3b8;">→</span>
            <a href="../../index.html" style="color:#1e3a8a;text-decoration:none;font-weight:500;">Premium</a>
            <span style="margin:0 6px;color:#94a3b8;">→</span>
            <a href="../../{category}/" style="color:#1e3a8a;text-decoration:none;font-weight:500;">{category.capitalize()}</a>
            <span style="margin:0 6px;color:#94a3b8;">→</span>
            <span style="color:#0f172a;font-weight:600;">{title}</span>
        </nav>
        '''

    # ---- What You'll Get и What's Inside ----
    what_html = ''
    if what_you_get:
        what_html = '<div style="flex:1; background:#f8fafc; border-radius:16px; padding:20px 24px; margin:0;"><h3 style="font-size:18px;font-weight:700;margin-bottom:12px;">📦 What You\'ll Get</h3><ul style="list-style:none;padding:0;display:grid;gap:8px;">'
        for item in what_you_get:
            what_html += f'<li style="padding:6px 0;border-bottom:1px solid #eef2ff;display:flex;align-items:center;gap:8px;"><span style="color:{accent};font-weight:600;">✓</span> {item}</li>'
        what_html += '</ul></div>'

    preview_html = ''
    if sections:
        preview_html = '<div style="flex:1; background:#f8fafc; border-radius:16px; padding:20px 24px; margin:0;"><h3 style="font-size:18px;font-weight:700;margin-bottom:12px;">📖 What\'s Inside</h3><ul style="list-style:none;padding:0;">'
        for sec in sections[:5]:
            sec_title = sec.get('title', 'Section')
            preview_html += f'<li style="padding:6px 0;border-bottom:1px solid #f1f4f9;font-size:15px;color:#1e293b;">• {sec_title}</li>'
        if len(sections) > 5:
            preview_html += f'<li style="padding:6px 0;font-size:15px;color:#94a3b8;">... and {len(sections)-5} more sections</li>'
        preview_html += '</ul></div>'

    info_blocks = ''
    if what_html or preview_html:
        info_blocks = f'<div style="display:flex; flex-wrap:wrap; gap:20px; margin:20px 0;">{what_html}{preview_html}</div>'

    # ---- JavaScript для покупки ----
    purchase_js = f'''
    <script>
    (function() {{
        const APP_SCRIPT_URL = "{APP_SCRIPT_URL}";
        const WALLET_ADDRESS = "{WALLET_ADDRESS}";
        const PRODUCT_SLUG = "{slug}";
        const PRICE = {price};
        const PRODUCT_TYPE = "guide";

        async function handlePurchase() {{
            try {{
                // 1. Создаём заказ
                console.log("Создаём заказ для", PRODUCT_SLUG);
                const createRes = await fetch(`${{APP_SCRIPT_URL}}?action=create&slug=${{PRODUCT_SLUG}}`);
                if (!createRes.ok) throw new Error("Ошибка создания заказа");
                const { orderId } = await createRes.json();
                if (!orderId) throw new Error("Не удалось получить orderId");
                console.log("Заказ создан:", orderId);
                localStorage.setItem('solvemap_order', orderId);

                // 2. Генерируем платёжную ссылку через Card2Crypto
                const callback = encodeURIComponent(`${{APP_SCRIPT_URL}}?action=webhook&order=${{orderId}}`);
                const walletRes = await fetch(`https://api.card2crypto.org/control/wallet.php?address=${{WALLET_ADDRESS}}&callback=${{callback}}`);
                if (!walletRes.ok) throw new Error("Ошибка генерации платёжной ссылки");
                const walletData = await walletRes.json();
                const addressIn = walletData.address_in;
                if (!addressIn) throw new Error("Не удалось получить зашифрованный адрес");

                const paymentLink = `https://pay.card2crypto.org/process-payment.php?address=${{addressIn}}&amount=${{PRICE}}&provider=stripe&email=&currency=USD`;
                console.log("Платёжная ссылка:", paymentLink);

                // 3. Перенаправляем клиента на оплату
                window.location.href = paymentLink;
            }} catch (err) {{
                console.error("Ошибка:", err);
                alert("Произошла ошибка при создании заказа. Попробуйте позже.");
            }}
        }}

        async function checkOrder() {{
            const orderId = localStorage.getItem('solvemap_order');
            if (!orderId) return;
            console.log("Проверяем заказ:", orderId);
            try {{
                const res = await fetch(`${{APP_SCRIPT_URL}}?action=get&order=${{orderId}}`);
                if (!res.ok) {{
                    console.warn("Запрос статуса не удался");
                    return;
                }}
                const data = await res.json();
                if (data.links && data.links.length > 0) {{
                    console.log("Получены ссылки:", data.links);
                    showDownloadLinks(data.links);
                    localStorage.removeItem('solvemap_order');
                }} else if (data.error) {{
                    console.warn("Статус заказа:", data.error);
                }}
            }} catch (err) {{
                console.error("Ошибка проверки заказа:", err);
            }}
        }}

        function showDownloadLinks(links) {{
            const container = document.getElementById('download-section') || document.querySelector('.download-section');
            if (!container) return;
            let html = '<div style="margin-top:20px;padding:20px;background:#f0fdf4;border-radius:12px;border:2px solid #22c55e;"><h3 style="font-size:20px;font-weight:700;color:#166534;">✅ Thank you for your purchase!</h3><p style="color:#166534;">Your files are ready for download:</p><ul style="list-style:none;padding:0;margin-top:10px;">';
            links.forEach(link => {{
                html += `<li style="margin:8px 0;"><a href="${{link}}" target="_blank" style="display:inline-block;background:#1e3a8a;color:white;padding:10px 20px;border-radius:8px;text-decoration:none;font-weight:600;">📥 Download PDF</a></li>`;
            }});
            html += '</ul></div>';
            container.insertAdjacentHTML('afterend', html);
        }}

        // При загрузке страницы проверяем статус заказа
        document.addEventListener('DOMContentLoaded', checkOrder);

        // Навешиваем обработчик на кнопку "Buy"
        const buyBtn = document.querySelector('.download-btn') || document.querySelector('[class*="download-btn"]');
        if (buyBtn) {{
            buyBtn.addEventListener('click', function(e) {{
                e.preventDefault();
                handlePurchase();
            }});
        }}
    }})();
    </script>
    '''

    # ---- Кнопка покупки (активная, но заменяется на JavaScript) ----
    buy_html = f'''
    <div class="download-section" style="display:flex;flex-wrap:wrap;align-items:center;gap:16px 24px;padding-top:24px;border-top:2px solid #eef2ff;">
        <button class="download-btn" style="display:inline-flex;align-items:center;gap:12px;background:{primary};color:white;font-weight:700;font-size:18px;padding:16px 36px;border-radius:60px;border:none;cursor:pointer;">
            <svg viewBox="0 0 24 24" style="width:22px;height:22px;fill:currentColor;"><path d="M5 20h14v-2H5v2zm7-18L5.33 9h3.84v4h3.66V9h3.84L12 2z"/></svg>
            Buy Now — ${price}
        </button>
        <span class="download-note" style="font-size:14px;color:#64748b;">🔒 Secure checkout via Card2Crypto</span>
    </div>
    '''

    mobile_menu = build_mobile_menu(root_prefix, home_prefix)

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{title} — Premium Guide — {SITE_NAME}</title>
    <meta name="description" content="{subtitle}" />
    <link rel="icon" type="image/png" href="{root_prefix}favicon.png" />
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="https://fonts.googleapis.com/css2?family=Inter:opsz,wght@14..32,400;14..32,500;14..32,600;14..32,700;14..32,800&display=swap" rel="stylesheet" />
    <style>
        :root {{ --primary: {primary}; --accent: {accent}; }}
        .breadcrumbs {{
            font-size: 14px;
            color: #64748b;
            margin-bottom: 20px;
            padding: 8px 0;
            border-bottom: 1px solid #f1f4f9;
        }}
        .breadcrumbs a {{ color: #1e3a8a; text-decoration: none; font-weight: 500; }}
        .breadcrumbs a:hover {{ text-decoration: underline; }}
        .breadcrumbs .sep {{ margin: 0 6px; color: #94a3b8; }}
        .breadcrumbs .current {{ color: #0f172a; font-weight: 600; }}
        .header-categories {{
            flex-wrap: nowrap !important;
            overflow-x: auto !important;
            white-space: nowrap !important;
            -webkit-overflow-scrolling: touch;
            scrollbar-width: none;
            gap: 4px 12px !important;
        }}
        .header-categories::-webkit-scrollbar {{ display: none; }}
        .header-categories a {{
            font-size: 13px !important;
            padding: 4px 10px !important;
            flex-shrink: 0;
        }}
        .premium-logo-badge {{
            background: #f59e0b;
            color: #0f172a;
            font-size: 11px;
            font-weight: 700;
            padding: 2px 10px;
            border-radius: 40px;
            margin-left: 6px;
        }}
        @media (max-width: 768px) {{
            html, body {{
                overflow: auto !important;
                height: auto !important;
                min-height: 100vh;
            }}
            .app {{
                display: block !important;
                height: auto !important;
                overflow: visible !important;
            }}
            .sidebar {{
                display: none !important;
            }}
            .main-content {{
                display: block !important;
                height: auto !important;
                overflow-y: visible !important;
                padding-bottom: 60px !important;
            }}
            .footer {{
                position: relative !important;
                margin-top: 20px !important;
            }}
            .header-categories {{
                flex-wrap: wrap !important;
                overflow-x: visible !important;
                white-space: normal !important;
            }}
        }}
        {get_subscribe_styles()}
    </style>
    <link rel="stylesheet" href="{root_prefix}styles/file.css" />
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-FS6Q6N9PCJ"></script>
    <script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-FS6Q6N9PCJ');</script>
</head>
<body>
    <div class="mobile-overlay" id="mobileOverlay"></div>
    <div class="mobile-menu" id="mobileMenu">
        <button class="close-btn" onclick="closeMobileMenu()">✕</button>
        {mobile_menu}
    </div>
    <div class="mobile-header">
        <button class="hamburger" id="hamburgerBtn" onclick="toggleMobileMenu()" aria-label="Menu"><span></span><span></span><span></span></button>
        <a class="mobile-logo" href="{home_prefix}index.html">{logo_html}</a>
    </div>
    <header class="header">
        <div class="logo" onclick="window.location.href='{home_prefix}index.html'">{logo_html}</div>
        <nav class="header-categories">{build_header_cats(root_prefix)}</nav>
    </header>
    <div class="app">
        {sidebar_html}
        <main class="main-content">
            <div class="file-detail fade-in">
                {breadcrumbs}
                <h1 class="file-title" style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;">
                    <span style="font-size:32px;">{icon}</span>
                    <span style="background:#fef3c7;color:#92400e;font-size:12px;font-weight:700;padding:4px 16px;border-radius:40px;text-transform:uppercase;">Premium</span>
                    <span>{title}</span>
                </h1>
                <p class="file-sub">{subtitle}</p>
                <div style="display:flex;gap:16px;flex-wrap:wrap;font-size:14px;color:#64748b;margin-bottom:20px;">
                    <span>📁 {category.capitalize()}</span>
                    {f'<span>📂 {subcategory.capitalize()}</span>' if subcategory else ''}
                    <span>💰 ${price}</span>
                </div>
                {info_blocks}
                {buy_html}
                <div class="tip-box">💡 <strong>Tip of the day:</strong> Premium guides include in-depth content, templates, and checklists you won't find anywhere else.</div>
            </div>
        </main>
    </div>
    {render_footer_with_form(f"premium:guide:{slug}")}
    <script>
        function toggleMobileMenu() {{ var m=document.getElementById('mobileMenu'); var o=document.getElementById('mobileOverlay'); var h=document.getElementById('hamburgerBtn'); m.classList.toggle('active'); o.classList.toggle('active'); h.classList.toggle('active'); document.body.style.overflow = m.classList.contains('active') ? 'hidden' : ''; }}
        function closeMobileMenu() {{ document.getElementById('mobileMenu').classList.remove('active'); document.getElementById('mobileOverlay').classList.remove('active'); document.getElementById('hamburgerBtn').classList.remove('active'); document.body.style.overflow = ''; }}
        document.getElementById('mobileOverlay').addEventListener('click', closeMobileMenu);
        document.querySelectorAll('.mobile-menu a').forEach(function(l){{l.addEventListener('click', closeMobileMenu);}});
    </script>
    {purchase_js}
    {get_subscribe_script()}
</body>
</html>'''

    guide_dir = output_dir / 'guides' / slug
    guide_dir.mkdir(parents=True, exist_ok=True)
    (guide_dir / 'index.html').write_text(html, encoding='utf-8')
    print(f"✅ Guide page: {guide_dir / 'index.html'}")
    return slug, guide

# ============================================================
# ФУНКЦИЯ ДЛЯ БАНДЛОВ (аналогично, но с дополнительными ссылками)
# ============================================================
def generate_bundle_page(bundle, guides_dict, output_dir, all_bundles=None):
    title = bundle.get('title', 'Bundle')
    description = bundle.get('description', '')
    price = bundle.get('price', 0)
    category = bundle.get('category', 'productivity')
    guides_list = bundle.get('guides', [])
    slug = bundle.get('slug') or slugify(title)

    colors = get_category_colors(category)
    primary = colors['primary']
    accent = colors['accent']
    icon = get_category_icon(category)

    root_prefix = "../../../"
    home_prefix = "../../../"
    logo_html = build_logo_with_badge()

    # ---- Сайдбар ----
    sidebar_html = build_premium_sidebar(
        category_id=category,
        bundles=all_bundles,
        guides_dict=guides_dict,
        active_bundle_slug=slug,
        active_guide_slug=None,
        root_prefix=root_prefix
    )

    # ---- Хлебные крошки ----
    breadcrumbs = f'''
    <nav class="breadcrumbs" style="font-size:14px;color:#64748b;margin-bottom:20px;padding:8px 0;border-bottom:1px solid #f1f4f9;">
        <a href="../../../index.html" style="color:#1e3a8a;text-decoration:none;font-weight:500;">Home</a>
        <span style="margin:0 6px;color:#94a3b8;">→</span>
        <a href="../../index.html" style="color:#1e3a8a;text-decoration:none;font-weight:500;">Premium</a>
        <span style="margin:0 6px;color:#94a3b8;">→</span>
        <a href="../../{category}/" style="color:#1e3a8a;text-decoration:none;font-weight:500;">{category.capitalize()}</a>
        <span style="margin:0 6px;color:#94a3b8;">→</span>
        <span style="color:#0f172a;font-weight:600;">{title}</span>
    </nav>
    '''

    # ---- Список гайдов с ценами ----
    bundle_guides = []
    for guide_name in guides_list:
        for g in guides_dict:
            if g.get('title', '').lower() == guide_name.lower():
                bundle_guides.append(g)
                break

    guides_html = ''
    total_separate = 0
    if bundle_guides:
        guides_html = '<div style="background:white;border:1px solid #e2e8f0;border-radius:16px;padding:24px 28px;margin-top:24px;"><h3 style="font-size:20px;font-weight:700;margin-bottom:16px;color:#0f172a;">📄 Included Guides</h3><ul style="list-style:none;padding:0;">'
        for g in bundle_guides:
            g_title = g.get('title', 'Untitled')
            g_price = g.get('price', 5)
            total_separate += g_price
            price_str = f'<span style="font-weight:600;color:#1e3a8a;font-size:14px;">${g_price}</span>' if g_price else ''
            guides_html += f'<li style="padding:10px 0;border-bottom:1px solid #f1f4f9;font-size:15px;color:#1e293b;display:flex;justify-content:space-between;align-items:center;">📄 {g_title} {price_str}</li>'
        guides_html += '</ul>'
        if total_separate > 0:
            guides_html += f'<div style="margin-top:12px;padding-top:12px;border-top:2px solid #eef2ff;font-size:15px;display:flex;justify-content:space-between;font-weight:600;color:#0f172a;"><span>Total if bought separately:</span><span>${total_separate}</span></div>'
        guides_html += '</div>'
    else:
        guides_html = f'<p style="color:#64748b;margin-top:16px;">This bundle includes {len(guides_list)} guides.</p>'

    # ---- Блок покупки (с JavaScript) ----
    buy_html = f'''
    <div class="download-section" style="display:flex;flex-wrap:wrap;align-items:center;gap:16px 24px;padding-top:24px;border-top:2px solid #eef2ff;margin-top:24px;">
        <button class="download-btn" style="display:inline-flex;align-items:center;gap:12px;background:{primary};color:white;font-weight:700;font-size:18px;padding:16px 36px;border-radius:60px;border:none;cursor:pointer;">
            <svg viewBox="0 0 24 24" style="width:22px;height:22px;fill:currentColor;"><path d="M5 20h14v-2H5v2zm7-18L5.33 9h3.84v4h3.66V9h3.84L12 2z"/></svg>
            Buy Bundle — ${price}
        </button>
        <span class="download-note" style="font-size:14px;color:#64748b;">🔒 Secure checkout via Card2Crypto</span>
    </div>
    '''

    savings = total_separate - price
    savings_html = ''
    if savings > 0:
        savings_html = f'''
        <div style="background:#fefce8;border-left:4px solid #eab308;padding:16px 20px;border-radius:12px;margin-top:16px;font-size:15px;color:#1e293b;font-weight:500;">
            💡 Save <strong>${savings}</strong> by buying the bundle! (Individual guides would cost <strong>${total_separate}</strong>)
        </div>
        '''

    # ---- JavaScript для покупки бандла ----
    purchase_js = f'''
    <script>
    (function() {{
        const APP_SCRIPT_URL = "{APP_SCRIPT_URL}";
        const WALLET_ADDRESS = "{WALLET_ADDRESS}";
        const PRODUCT_SLUG = "{slug}";
        const PRICE = {price};
        const PRODUCT_TYPE = "bundle";

        async function handlePurchase() {{
            try {{
                console.log("Создаём заказ для бандла", PRODUCT_SLUG);
                const createRes = await fetch(`${{APP_SCRIPT_URL}}?action=create&slug=${{PRODUCT_SLUG}}`);
                if (!createRes.ok) throw new Error("Ошибка создания заказа");
                const {{ orderId }} = await createRes.json();
                if (!orderId) throw new Error("Не удалось получить orderId");
                localStorage.setItem('solvemap_order', orderId);

                const callback = encodeURIComponent(`${{APP_SCRIPT_URL}}?action=webhook&order=${{orderId}}`);
                const walletRes = await fetch(`https://api.card2crypto.org/control/wallet.php?address=${{WALLET_ADDRESS}}&callback=${{callback}}`);
                if (!walletRes.ok) throw new Error("Ошибка генерации платёжной ссылки");
                const walletData = await walletRes.json();
                const addressIn = walletData.address_in;
                if (!addressIn) throw new Error("Не удалось получить зашифрованный адрес");

                const paymentLink = `https://pay.card2crypto.org/process-payment.php?address=${{addressIn}}&amount=${{PRICE}}&provider=stripe&email=&currency=USD`;
                console.log("Платёжная ссылка:", paymentLink);
                window.location.href = paymentLink;
            }} catch (err) {{
                console.error("Ошибка:", err);
                alert("Произошла ошибка при создании заказа. Попробуйте позже.");
            }}
        }}

        async function checkOrder() {{
            const orderId = localStorage.getItem('solvemap_order');
            if (!orderId) return;
            try {{
                const res = await fetch(`${{APP_SCRIPT_URL}}?action=get&order=${{orderId}}`);
                if (!res.ok) {{ console.warn("Запрос статуса не удался"); return; }}
                const data = await res.json();
                if (data.links && data.links.length > 0) {{
                    console.log("Получены ссылки:", data.links);
                    showDownloadLinks(data.links);
                    localStorage.removeItem('solvemap_order');
                }} else if (data.error) {{
                    console.warn("Статус заказа:", data.error);
                }}
            }} catch (err) {{
                console.error("Ошибка проверки заказа:", err);
            }}
        }}

        function showDownloadLinks(links) {{
            const container = document.querySelector('.download-section');
            if (!container) return;
            let html = '<div style="margin-top:20px;padding:20px;background:#f0fdf4;border-radius:12px;border:2px solid #22c55e;"><h3 style="font-size:20px;font-weight:700;color:#166534;">✅ Thank you for your purchase!</h3><p style="color:#166534;">Your bundle files are ready for download:</p><ul style="list-style:none;padding:0;margin-top:10px;">';
            links.forEach(link => {{
                html += `<li style="margin:8px 0;"><a href="${{link}}" target="_blank" style="display:inline-block;background:#1e3a8a;color:white;padding:10px 20px;border-radius:8px;text-decoration:none;font-weight:600;">📥 Download PDF</a></li>`;
            }});
            html += '</ul></div>';
            container.insertAdjacentHTML('afterend', html);
        }}

        document.addEventListener('DOMContentLoaded', checkOrder);

        const buyBtn = document.querySelector('.download-btn');
        if (buyBtn) {{
            buyBtn.addEventListener('click', function(e) {{
                e.preventDefault();
                handlePurchase();
            }});
        }}
    }})();
    </script>
    '''

    mobile_menu = build_mobile_menu(root_prefix, home_prefix)

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{title} — Bundle — {SITE_NAME}</title>
    <meta name="description" content="{description}" />
    <link rel="icon" type="image/png" href="{root_prefix}favicon.png" />
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="https://fonts.googleapis.com/css2?family=Inter:opsz,wght@14..32,400;14..32,500;14..32,600;14..32,700;14..32,800&display=swap" rel="stylesheet" />
    <style>
        :root {{ --primary: {primary}; --accent: {accent}; }}
        .breadcrumbs {{
            font-size: 14px;
            color: #64748b;
            margin-bottom: 20px;
            padding: 8px 0;
            border-bottom: 1px solid #f1f4f9;
        }}
        .breadcrumbs a {{ color: #1e3a8a; text-decoration: none; font-weight: 500; }}
        .breadcrumbs a:hover {{ text-decoration: underline; }}
        .breadcrumbs .sep {{ margin: 0 6px; color: #94a3b8; }}
        .breadcrumbs .current {{ color: #0f172a; font-weight: 600; }}
        .header-categories {{
            flex-wrap: nowrap !important;
            overflow-x: auto !important;
            white-space: nowrap !important;
            -webkit-overflow-scrolling: touch;
            scrollbar-width: none;
            gap: 4px 12px !important;
        }}
        .header-categories::-webkit-scrollbar {{ display: none; }}
        .header-categories a {{
            font-size: 13px !important;
            padding: 4px 10px !important;
            flex-shrink: 0;
        }}
        .premium-logo-badge {{
            background: #f59e0b;
            color: #0f172a;
            font-size: 11px;
            font-weight: 700;
            padding: 2px 10px;
            border-radius: 40px;
            margin-left: 6px;
        }}
        @media (max-width: 768px) {{
            html, body {{
                overflow: auto !important;
                height: auto !important;
                min-height: 100vh;
            }}
            .app {{
                display: block !important;
                height: auto !important;
                overflow: visible !important;
            }}
            .sidebar {{
                display: none !important;
            }}
            .main-content {{
                display: block !important;
                height: auto !important;
                overflow-y: visible !important;
                padding-bottom: 60px !important;
            }}
            .footer {{
                position: relative !important;
                margin-top: 20px !important;
            }}
            .header-categories {{
                flex-wrap: wrap !important;
                overflow-x: visible !important;
                white-space: normal !important;
            }}
        }}
        {get_subscribe_styles()}
    </style>
    <link rel="stylesheet" href="{root_prefix}styles/category.css" />
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-FS6Q6N9PCJ"></script>
    <script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-FS6Q6N9PCJ');</script>
</head>
<body>
    <div class="mobile-overlay" id="mobileOverlay"></div>
    <div class="mobile-menu" id="mobileMenu">
        <button class="close-btn" onclick="closeMobileMenu()">✕</button>
        {mobile_menu}
    </div>
    <div class="mobile-header">
        <button class="hamburger" id="hamburgerBtn" onclick="toggleMobileMenu()" aria-label="Menu"><span></span><span></span><span></span></button>
        <a class="mobile-logo" href="{home_prefix}index.html">{logo_html}</a>
    </div>
    <header class="header">
        <div class="logo" onclick="window.location.href='{home_prefix}index.html'">{logo_html}</div>
        <nav class="header-categories">{build_header_cats(root_prefix)}</nav>
    </header>
    <div class="app">
        {sidebar_html}
        <main class="main-content">
            <div class="fade-in">
                {breadcrumbs}
                <h1 style="font-size:48px;font-weight:800;letter-spacing:-0.02em;line-height:1.1;margin-bottom:8px;display:flex;align-items:center;gap:12px;flex-wrap:wrap;">
                    <span style="font-size:32px;">{icon}</span>
                    <span style="background:#fef3c7;color:#92400e;font-size:12px;font-weight:700;padding:4px 16px;border-radius:40px;text-transform:uppercase;">Bundle</span>
                    <span>{title}</span>
                </h1>
                <p class="subtitle" style="font-size:20px;color:#475569;margin-bottom:20px;">{description}</p>
                <div style="display:flex;gap:16px;flex-wrap:wrap;font-size:14px;color:#64748b;margin-bottom:20px;">
                    <span>📁 {category.capitalize()}</span>
                    <span>💰 ${price}</span>
                    <span>📄 {len(guides_list)} guides</span>
                </div>
                {guides_html}
                {savings_html}
                {buy_html}
                <div class="tip-box">💡 <strong>Tip of the day:</strong> Bundles give you the best value — save up to 50% compared to buying guides individually.</div>
            </div>
        </main>
    </div>
    {render_footer_with_form(f"premium:bundle:{slug}")}
    <script>
        function toggleMobileMenu() {{ var m=document.getElementById('mobileMenu'); var o=document.getElementById('mobileOverlay'); var h=document.getElementById('hamburgerBtn'); m.classList.toggle('active'); o.classList.toggle('active'); h.classList.toggle('active'); document.body.style.overflow = m.classList.contains('active') ? 'hidden' : ''; }}
        function closeMobileMenu() {{ document.getElementById('mobileMenu').classList.remove('active'); document.getElementById('mobileOverlay').classList.remove('active'); document.getElementById('hamburgerBtn').classList.remove('active'); document.body.style.overflow = ''; }}
        document.getElementById('mobileOverlay').addEventListener('click', closeMobileMenu);
        document.querySelectorAll('.mobile-menu a').forEach(function(l){{l.addEventListener('click', closeMobileMenu);}});
    </script>
    {purchase_js}
    {get_subscribe_script()}
</body>
</html>'''

    bundle_dir = output_dir / 'bundles' / slug
    bundle_dir.mkdir(parents=True, exist_ok=True)
    (bundle_dir / 'index.html').write_text(html, encoding='utf-8')
    print(f"✅ Bundle page: {bundle_dir / 'index.html'}")
    
def generate_premium_category_page(category_id, bundles, all_bundles, guides_dict, output_dir):
    cat_info = next((c for c in ALL_CATEGORIES if c['id'] == category_id), None)
    if not cat_info:
        return
    cat_title = cat_info['title']
    cat_icon = cat_info['icon']

    cat_bundles = [b for b in bundles if b.get('category') == category_id]

    colors = get_category_colors(category_id)
    primary = colors['primary']
    accent = colors['accent']

    root_prefix = "../../"
    home_prefix = "../../"
    logo_html = build_logo_with_badge()

    sidebar_html = build_premium_sidebar(
        category_id=category_id,
        bundles=all_bundles,
        guides_dict=guides_dict,
        active_bundle_slug=None,
        root_prefix=root_prefix
    )

    breadcrumbs = f'''
    <nav class="breadcrumbs" style="font-size:14px;color:#64748b;margin-bottom:20px;padding:8px 0;border-bottom:1px solid #f1f4f9;">
        <a href="../../index.html" style="color:#1e3a8a;text-decoration:none;font-weight:500;">Home</a>
        <span style="margin:0 6px;color:#94a3b8;">→</span>
        <a href="../index.html" style="color:#1e3a8a;text-decoration:none;font-weight:500;">Premium</a>
        <span style="margin:0 6px;color:#94a3b8;">→</span>
        <span style="color:#0f172a;font-weight:600;">{cat_title}</span>
    </nav>
    '''

    cards_html = ''
    for b in cat_bundles:
        b_title = b.get('title', 'Bundle')
        b_desc = b.get('description', '')
        b_slug = b.get('slug') or slugify(b_title)
        guides_count = len(b.get('guides', []))
        cards_html += f'''
        <a href="../bundles/{b_slug}/" class="file-card" style="background:white;padding:20px 20px 24px;border-radius:16px;border:1px solid #e2e8f0;text-decoration:none;color:#0f172a;transition:all 0.15s;display:block;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                <span style="font-size:28px;">{cat_icon}</span>
                <span style="font-size:12px;font-weight:600;color:#64748b;background:#f1f5f9;padding:2px 12px;border-radius:40px;">{guides_count} guides</span>
            </div>
            <h3 style="font-size:18px;font-weight:700;margin-bottom:4px;">{b_title}</h3>
            <p style="font-size:14px;color:#64748b;line-height:1.5;margin:0;">{b_desc[:120]}{'...' if len(b_desc)>120 else ''}</p>
            <div style="margin-top:16px;padding-top:12px;border-top:1px solid #f1f4f9;font-size:14px;font-weight:600;color:#1e3a8a;display:flex;justify-content:flex-end;">
                <span>View Bundle →</span>
            </div>
        </a>
        '''

    if not cards_html:
        cards_html = '<p style="color:#64748b;font-size:18px;margin-top:20px;">No bundles available in this category yet.</p>'

    mobile_menu = build_mobile_menu(root_prefix, home_prefix)

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{cat_title} — Premium — {SITE_NAME}</title>
    <meta name="description" content="Premium bundles in {cat_title} to solve your problems faster." />
    <link rel="icon" type="image/png" href="{root_prefix}favicon.png" />
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="https://fonts.googleapis.com/css2?family=Inter:opsz,wght@14..32,400;14..32,500;14..32,600;14..32,700;14..32,800&display=swap" rel="stylesheet" />
    <style>
        :root {{ --primary: {primary}; --accent: {accent}; }}
        .breadcrumbs {{
            font-size: 14px;
            color: #64748b;
            margin-bottom: 20px;
            padding: 8px 0;
            border-bottom: 1px solid #f1f4f9;
        }}
        .breadcrumbs a {{ color: #1e3a8a; text-decoration: none; font-weight: 500; }}
        .breadcrumbs a:hover {{ text-decoration: underline; }}
        .breadcrumbs .sep {{ margin: 0 6px; color: #94a3b8; }}
        .breadcrumbs .current {{ color: #0f172a; font-weight: 600; }}
        .header-categories {{
            flex-wrap: nowrap !important;
            overflow-x: auto !important;
            white-space: nowrap !important;
            -webkit-overflow-scrolling: touch;
            scrollbar-width: none;
            gap: 4px 12px !important;
        }}
        .header-categories::-webkit-scrollbar {{ display: none; }}
        .header-categories a {{
            font-size: 13px !important;
            padding: 4px 10px !important;
            flex-shrink: 0;
        }}
        .premium-logo-badge {{
            background: #f59e0b;
            color: #0f172a;
            font-size: 11px;
            font-weight: 700;
            padding: 2px 10px;
            border-radius: 40px;
            margin-left: 6px;
        }}
        .file-card {{
            background: white;
            padding: 20px 20px 24px;
            border-radius: 16px;
            border: 1px solid #e2e8f0;
            text-decoration: none;
            color: #0f172a;
            transition: all 0.15s;
            display: block;
        }}
        .file-card:hover {{
            background:#f8fafc;
            border-color:var(--primary);
            transform:translateY(-2px);
            box-shadow:0 8px 20px -8px rgba(30,58,138,0.1);
        }}
        @media (max-width: 768px) {{
            html, body {{
                overflow: auto !important;
                height: auto !important;
                min-height: 100vh;
            }}
            .app {{
                display: block !important;
                height: auto !important;
                overflow: visible !important;
            }}
            .sidebar {{
                display: none !important;
            }}
            .main-content {{
                display: block !important;
                height: auto !important;
                overflow-y: visible !important;
                padding-bottom: 60px !important;
            }}
            .footer {{
                position: relative !important;
                margin-top: 20px !important;
            }}
        }}
        {get_subscribe_styles()}
    </style>
    <link rel="stylesheet" href="{root_prefix}styles/category.css" />
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-FS6Q6N9PCJ"></script>
    <script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-FS6Q6N9PCJ');</script>
</head>
<body>
    <div class="mobile-overlay" id="mobileOverlay"></div>
    <div class="mobile-menu" id="mobileMenu">
        <button class="close-btn" onclick="closeMobileMenu()">✕</button>
        {mobile_menu}
    </div>
    <div class="mobile-header">
        <button class="hamburger" id="hamburgerBtn" onclick="toggleMobileMenu()" aria-label="Menu"><span></span><span></span><span></span></button>
        <a class="mobile-logo" href="{home_prefix}index.html">{logo_html}</a>
    </div>
    <header class="header">
        <div class="logo" onclick="window.location.href='{home_prefix}index.html'">{logo_html}</div>
        <nav class="header-categories">{build_header_cats(root_prefix, active_id=category_id)}</nav>
    </header>
    <div class="app">
        {sidebar_html}
        <main class="main-content">
            <div class="fade-in">
                {breadcrumbs}
                <h1 style="font-size:48px;font-weight:800;letter-spacing:-0.02em;line-height:1.1;margin-bottom:8px;">{cat_icon} {cat_title}</h1>
                <p class="subtitle" style="font-size:20px;color:#475569;margin-bottom:20px;">Premium bundles to solve your problems faster.</p>
                <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:20px;">
                    {cards_html}
                </div>
                <div class="tip-box" style="margin-top:32px;">💡 <strong>Tip of the day:</strong> Bundles save you money — get all guides in one package.</div>
            </div>
        </main>
    </div>
    {render_footer_with_form(f"premium:category:{category_id}")}
    <script>
        function toggleMobileMenu() {{ var m=document.getElementById('mobileMenu'); var o=document.getElementById('mobileOverlay'); var h=document.getElementById('hamburgerBtn'); m.classList.toggle('active'); o.classList.toggle('active'); h.classList.toggle('active'); document.body.style.overflow = m.classList.contains('active') ? 'hidden' : ''; }}
        function closeMobileMenu() {{ document.getElementById('mobileMenu').classList.remove('active'); document.getElementById('mobileOverlay').classList.remove('active'); document.getElementById('hamburgerBtn').classList.remove('active'); document.body.style.overflow = ''; }}
        document.getElementById('mobileOverlay').addEventListener('click', closeMobileMenu);
        document.querySelectorAll('.mobile-menu a').forEach(function(l){{l.addEventListener('click', closeMobileMenu);}});
    </script>
    {get_subscribe_script()}
</body>
</html>'''

    cat_dir = output_dir / category_id
    cat_dir.mkdir(parents=True, exist_ok=True)
    (cat_dir / 'index.html').write_text(html, encoding='utf-8')
    print(f"✅ Premium category page: {cat_dir / 'index.html'}")


def generate_premium_index(guides, bundles, output_dir):
    bundles_by_category = defaultdict(list)
    for b in bundles:
        cat = b.get('category', 'other')
        bundles_by_category[cat].append(b)

    root_prefix = "../"
    home_prefix = "../"
    logo_html = build_logo_with_badge()

    cards_html = ''
    for cat in ALL_CATEGORIES:
        cat_id = cat['id']
        cat_bundles = bundles_by_category.get(cat_id, [])
        count = len(cat_bundles)
        if count == 0:
            continue
        cards_html += f'''
        <a href="./{cat_id}/" class="card" style="background:#ffffff;border-radius:20px;padding:24px 20px 28px;box-shadow:0 4px 12px rgba(0,0,0,0.02);border:1px solid #f1f4f9;transition:all 0.2s ease;text-decoration:none;color:inherit;display:flex;flex-direction:column;">
            <span style="font-size:32px;margin-bottom:12px;">{cat['icon']}</span>
            <h3 style="font-size:18px;font-weight:700;letter-spacing:-0.01em;margin-bottom:4px;color:#0f172a;">{cat['title']}</h3>
            <p style="font-size:14px;color:#64748b;line-height:1.4;margin-bottom:16px;flex:1;">{count} premium bundles</p>
            <div style="display:flex;justify-content:space-between;align-items:center;font-size:13px;color:#94a3b8;border-top:1px solid #f1f4f9;padding-top:14px;margin-top:auto;">
                <span>Explore →</span>
                <span style="color:#1e3a8a;font-weight:600;transition:transform 0.2s;">→</span>
            </div>
        </a>
        '''

    if not cards_html:
        cards_html = '<p style="color:#64748b;font-size:18px;">No premium bundles available yet. Check back soon!</p>'

    mobile_menu = build_mobile_menu(root_prefix, home_prefix)

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Premium — {SITE_NAME}</title>
    <meta name="description" content="Premium guides and bundles to solve your problems faster." />
    <link rel="icon" type="image/png" href="../favicon.png" />
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="https://fonts.googleapis.com/css2?family=Inter:opsz,wght@14..32,400;14..32,500;14..32,600;14..32,700;14..32,800&display=swap" rel="stylesheet" />
    <style>
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{ font-family:'Inter',-apple-system,sans-serif; background:#f8fafc; color:#0f172a; padding:32px 24px; overflow-x:hidden; }}
        .container {{ max-width:1500px; margin:0 auto; padding:0 16px; position:relative; z-index:1; }}
        a {{ text-decoration:none; color:inherit; }}
        .header {{ display:flex; justify-content:space-between; align-items:center; padding-bottom:20px; border-bottom:1px solid #e9edf2; margin-bottom:40px; flex-wrap:wrap; gap:16px; position:relative; z-index:9990; }}
        .logo {{ font-size:26px; font-weight:800; display:flex; align-items:center; gap:8px; cursor:pointer; }}
        .logo span {{ color:#1e3a8a; background:#eef2ff; padding:2px 12px; border-radius:40px; font-size:16px; }}
        .premium-logo-badge {{
            background: #f59e0b;
            color: #0f172a;
            font-size: 11px;
            font-weight: 700;
            padding: 2px 10px;
            border-radius: 40px;
            margin-left: 6px;
        }}
        .header-categories {{
            display:flex;
            flex-wrap:nowrap !important;
            overflow-x:auto !important;
            white-space:nowrap !important;
            -webkit-overflow-scrolling:touch;
            scrollbar-width:none;
            gap:4px 12px !important;
        }}
        .header-categories::-webkit-scrollbar {{ display:none; }}
        .header-categories a {{
            color:#475569; text-decoration:none; font-weight:600; font-size:13px !important; padding:4px 10px !important; border-radius:40px; transition:background 0.15s,color 0.15s; background:transparent; flex-shrink:0;
        }}
        .header-categories a:hover {{ background:#f1f4f9; color:#0f172a; }}
        .header-categories a.active {{ background:#1e3a8a; color:#ffffff; }}
        .footer {{ margin-top:56px; padding-top:24px; border-top:1px solid #e9edf2; display:flex; justify-content:space-between; align-items:center; font-size:14px; color:#94a3b8; flex-wrap:wrap; gap:16px; position:relative; z-index:2; }}
        .footer .socials {{ display:flex; gap:20px; align-items:center; }}
        .footer .socials a {{ color:#1e293b; text-decoration:none; transition:color 0.2s,transform 0.2s; display:flex; align-items:center; justify-content:center; }}
        .footer .socials a:hover {{ color:#1e3a8a; transform:scale(1.1); }}
        .footer .socials svg {{ width:22px; height:22px; fill:currentColor; }}
        .footer .socials .label {{ font-size:13px; color:#94a3b8; font-weight:500; margin-right:4px; }}
        .hamburger {{ display:none; }}
        .mobile-menu {{ display:none; }}
        .mobile-overlay {{ display:none; }}
        .mobile-header {{ display:none; }}
        .menu-back {{ display:block; padding:12px 16px; font-size:14px; font-weight:600; color:#1e3a8a; border-bottom:1px solid #eef2ff; margin-bottom:12px; cursor:pointer; }}
        .menu-back:active {{ background:#f1f4f9; }}
        .menu-section-title {{ font-size:13px; font-weight:700; color:#94a3b8; text-transform:uppercase; letter-spacing:0.5px; padding:8px 16px 12px; border-bottom:1px solid #f1f4f9; margin-bottom:8px; }}
        .menu-section {{ border-bottom:1px solid #f1f4f9; }}
        .menu-section:last-child {{ border-bottom:none; }}
        .menu-section-link {{ display:block; padding:14px 20px; font-weight:600; font-size:16px; color:#0f172a; text-decoration:none; }}
        .menu-section-link:active {{ background:#f1f4f9; }}
        .menu-section-header {{ display:flex; justify-content:space-between; align-items:center; padding:14px 20px; font-weight:600; font-size:16px; color:#0f172a; cursor:pointer; user-select:none; }}
        .menu-section-header:active {{ background:#f1f4f9; }}
        .menu-section-header .arrow {{ transition:transform 0.3s ease; font-size:18px; color:#94a3b8; }}
        .menu-section-header.open .arrow {{ transform:rotate(90deg); }}
        .menu-section-body {{ max-height:0; overflow:hidden; transition:max-height 0.3s ease; background:#f8fafc; }}
        .menu-section-body.open {{ max-height:500px; }}
        .menu-section-body a {{ display:block; padding:12px 20px 12px 36px; font-size:15px; font-weight:500; color:#1e293b; text-decoration:none; border-bottom:1px solid #f1f4f9; }}
        .menu-section-body a:last-child {{ border-bottom:none; }}
        .menu-section-body a:active {{ background:#eef2ff; }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 20px;
            margin-top: 12px;
        }}
        .card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 20px 40px -12px rgba(30,58,138,0.12);
            border-color: #dbe2ed;
        }}
        .card:hover .arrow {{
            transform: translateX(4px);
        }}
        @media (max-width:768px) {{
            html, body {{
                overflow: auto !important;
                height: auto !important;
                min-height: 100vh;
            }}
            .container {{ padding:0 8px; }}
            .header {{ display:none !important; }}
            .mobile-header {{ display:flex !important; justify-content:space-between; align-items:center; padding:10px 16px; border-bottom:1px solid #e9edf2; background:#ffffff; gap:10px; flex-shrink:0; position:sticky; top:0; z-index:9990; }}
            .hamburger {{ display:flex !important; flex-direction:column; gap:4px; cursor:pointer; padding:6px 2px; background:transparent; border:none; flex-shrink:0; z-index:10001; order:1; }}
            .hamburger span {{ display:block; width:24px; height:3px; background:#0f172a; border-radius:3px; transition:all 0.3s ease; }}
            .hamburger.active span:nth-child(1) {{ transform:rotate(45deg) translate(4px,5px); }}
            .hamburger.active span:nth-child(2) {{ opacity:0; }}
            .hamburger.active span:nth-child(3) {{ transform:rotate(-45deg) translate(4px,-5px); }}
            .mobile-logo {{ font-size:18px; font-weight:800; color:#0f172a; text-decoration:none; flex-shrink:1; min-width:0; overflow:hidden; white-space:nowrap; order:2; text-align:right; }}
            .mobile-logo span {{ color:#1e3a8a; background:#eef2ff; padding:2px 8px; border-radius:40px; font-size:11px; font-weight:700; }}
            .mobile-overlay {{ display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.4); z-index:9999; }}
            .mobile-overlay.active {{ display:block; }}
            .mobile-menu {{ display:none; position:fixed; top:0; left:-280px; width:280px; height:100%; background:white; padding:60px 0 30px; box-shadow:4px 0 20px rgba(0,0,0,0.1); z-index:10000; transition:left 0.3s cubic-bezier(0.4,0,0.2,1); overflow-y:auto; }}
            .mobile-menu.active {{ left:0; display:block; }}
            .mobile-menu .close-btn {{ position:absolute; top:12px; right:16px; font-size:24px; background:none; border:none; cursor:pointer; color:#0f172a; padding:4px 8px; }}
            .mobile-menu a {{ display:block; padding:14px 20px; font-size:15px; font-weight:600; color:#1e293b; transition:background 0.15s; border-bottom:1px solid #f8fafc; text-decoration:none; }}
            .mobile-menu a:active {{ background:#f1f4f9; }}
            .mobile-menu a .icon {{ display:none; }}
            .grid {{
                grid-template-columns: 1fr 1fr;
                gap: 12px;
            }}
            .card {{
                padding: 16px 14px 18px;
                border-radius: 16px;
            }}
            .card:hover {{
                transform: none;
                box-shadow: 0 4px 12px rgba(0,0,0,0.02);
                border-color: #f1f4f9;
            }}
            .card-icon {{ font-size:24px; margin-bottom:6px; }}
            .card h3 {{ font-size:14px; margin-bottom:2px; }}
            .card p {{ font-size:12px; margin-bottom:10px; }}
            .card .meta {{ font-size:11px; padding-top:10px; }}
            .footer {{
                flex-direction:column;
                align-items:center;
                text-align:center;
                gap:10px;
                font-size:12px;
                padding:16px;
            }}
            .footer .socials {{ gap:16px; }}
            .footer .socials svg {{ width:20px; height:20px; }}
            .header-categories {{
                flex-wrap:wrap !important;
                overflow-x:visible !important;
                white-space:normal !important;
                gap:6px 10px !important;
            }}
        }}
        @media (max-width:400px) {{
            body {{ padding:12px 8px; }}
            .grid {{ gap:8px; }}
            .card {{ padding:12px 10px 14px; }}
            .card h3 {{ font-size:13px; }}
            .card p {{ font-size:11px; }}
            .mobile-menu {{ width:260px; }}
            .mobile-logo {{ font-size:16px; }}
            .mobile-logo span {{ font-size:10px; padding:1px 6px; }}
            .hamburger span {{ width:22px; height:2.5px; }}
        }}
        {get_subscribe_styles()}
    </style>
    <link rel="stylesheet" href="{root_prefix}styles/index.css" />
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-FS6Q6N9PCJ"></script>
    <script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-FS6Q6N9PCJ');</script>
</head>
<body>
    <div class="mobile-overlay" id="mobileOverlay"></div>
    <div class="mobile-menu" id="mobileMenu">
        <button class="close-btn" onclick="closeMobileMenu()">✕</button>
        {mobile_menu}
    </div>
    <div class="mobile-header">
        <button class="hamburger" id="hamburgerBtn" onclick="toggleMobileMenu()" aria-label="Menu"><span></span><span></span><span></span></button>
        <a class="mobile-logo" href="../index.html">{logo_html}</a>
    </div>
    <div class="container">
        <header class="header">
            <div class="logo" onclick="window.location.href='../index.html'">{logo_html}</div>
            <nav class="header-categories">{build_header_cats(root_prefix)}</nav>
        </header>
        <div style="background:#f8fafc;padding:32px 24px;border-radius:20px;margin-bottom:32px;border:1px solid #e2e8f0;text-align:left;">
            <h1 style="font-size:36px;font-weight:800;color:#0f172a;margin-bottom:4px;">⭐ <span style="color:#f59e0b;">Premium</span> Guides &amp; Bundles</h1>
            <p style="font-size:16px;color:#475569;max-width:600px;">Choose a category below to explore premium bundles that solve your problems faster.</p>
        </div>
        <div class="grid">
            {cards_html}
        </div>
        <p style="font-size:13px;color:#94a3b8;text-align:center;margin-top:40px;border-top:1px solid #eef2ff;padding-top:20px;">All premium content comes with a 30-day satisfaction guarantee. New bundles added weekly.</p>
        {render_footer_with_form("premium")}
    </div>
    <script>
        function toggleMobileMenu() {{ var m=document.getElementById('mobileMenu'); var o=document.getElementById('mobileOverlay'); var h=document.getElementById('hamburgerBtn'); m.classList.toggle('active'); o.classList.toggle('active'); h.classList.toggle('active'); document.body.style.overflow = m.classList.contains('active') ? 'hidden' : ''; }}
        function closeMobileMenu() {{ document.getElementById('mobileMenu').classList.remove('active'); document.getElementById('mobileOverlay').classList.remove('active'); document.getElementById('hamburgerBtn').classList.remove('active'); document.body.style.overflow = ''; }}
        document.getElementById('mobileOverlay').addEventListener('click', closeMobileMenu);
        document.querySelectorAll('.mobile-menu a').forEach(function(l){{l.addEventListener('click', closeMobileMenu);}});
        function toggleSection(header) {{ var body = header.nextElementSibling; body.classList.toggle('open'); header.classList.toggle('open'); }}
    </script>
    {get_subscribe_script()}
</body>
</html>'''

    (output_dir / 'index.html').write_text(html, encoding='utf-8')
    print(f"✅ Premium catalog: {output_dir / 'index.html'}")


def update_premium_sitemap():
    """Дополняет существующий sitemap.xml URL-адресами премиум-страниц."""
    sitemap_path = SITE_OUTPUT / "sitemap.xml"
    today = datetime.now().strftime('%Y-%m-%d')
    ns = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

    # Базовые премиум-URL
    premium_urls = [
        {'loc': 'https://solvemap.space/premium/', 'priority': '0.8', 'changefreq': 'weekly'},
    ]

    # Добавляем категории с бандлами
    bundles = load_bundles(BUNDLES_FILE)
    if bundles:
        categories_with_bundles = set(b.get('category') for b in bundles if b.get('category'))
        for cat_id in categories_with_bundles:
            premium_urls.append({
                'loc': f'https://solvemap.space/premium/{cat_id}/',
                'priority': '0.7',
                'changefreq': 'weekly'
            })

        # Добавляем страницы бандлов
        for b in bundles:
            slug = b.get('slug') or slugify(b.get('title', 'bundle'))
            premium_urls.append({
                'loc': f'https://solvemap.space/premium/bundles/{slug}/',
                'priority': '0.6',
                'changefreq': 'monthly'
            })

    # Добавляем страницы гайдов (если есть файл premium.txt)
    guides = load_premium_guides(PREMIUM_DATA_FILE)
    for g in guides:
        slug = slugify(g.get('title', 'untitled'))
        premium_urls.append({
            'loc': f'https://solvemap.space/premium/guides/{slug}/',
            'priority': '0.5',
            'changefreq': 'monthly'
        })

    # Если sitemap не существует – создаём новый
    if not sitemap_path.exists():
        root = ET.Element('urlset', xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
        # Добавляем основные URL сайта
        main_urls = [
            {'loc': 'https://solvemap.space/', 'priority': '1.0', 'changefreq': 'daily'},
            {'loc': 'https://solvemap.space/services/', 'priority': '0.8', 'changefreq': 'weekly'},
        ]
        for url_data in main_urls + premium_urls:
            url_elem = ET.SubElement(root, 'url')
            ET.SubElement(url_elem, 'loc').text = url_data['loc']
            ET.SubElement(url_elem, 'lastmod').text = today
            ET.SubElement(url_elem, 'changefreq').text = url_data['changefreq']
            ET.SubElement(url_elem, 'priority').text = url_data['priority']
        tree = ET.ElementTree(root)
        tree.write(sitemap_path, encoding='utf-8', xml_declaration=True)
        print(f"✅ Sitemap создан: {sitemap_path}")
        return

    # Если sitemap существует – дополняем
    try:
        tree = ET.parse(sitemap_path)
        root = tree.getroot()
        # Собираем существующие URL
        existing_urls = {elem.find('ns:loc', ns).text for elem in root.findall('ns:url', ns)}
        added = 0
        for url_data in premium_urls:
            if url_data['loc'] in existing_urls:
                continue
            url_elem = ET.SubElement(root, 'url')
            ET.SubElement(url_elem, 'loc').text = url_data['loc']
            ET.SubElement(url_elem, 'lastmod').text = today
            ET.SubElement(url_elem, 'changefreq').text = url_data['changefreq']
            ET.SubElement(url_elem, 'priority').text = url_data['priority']
            added += 1
        tree.write(sitemap_path, encoding='utf-8', xml_declaration=True)
        print(f"✅ Sitemap дополнен: добавлено {added} премиум-URL")
    except Exception as e:
        print(f"⚠️ Ошибка обновления sitemap: {e}")


def main():
    print("🚀 Generating Premium Pages...")
    PREMIUM_DIR.mkdir(parents=True, exist_ok=True)
    GUIDES_DIR.mkdir(parents=True, exist_ok=True)
    BUNDLES_DIR.mkdir(parents=True, exist_ok=True)

    guides = load_premium_guides(PREMIUM_DATA_FILE)
    if not guides:
        print("⚠️ No guides found. Check premium.txt path.")
        return

    bundles = load_bundles(BUNDLES_FILE)
    if not bundles:
        print("⚠️ No bundles found. bundles.yaml missing or empty.")
        if not Path(BUNDLES_FILE).exists():
            sample = '''
id: "first-aid-collection"
category: "health"
title: "First Aid Collection"
description: "12 practical guides to handle emergencies."
price: 39
slug: "first-aid-collection"
guides:
  - "How to Recognize a Stroke in 2 Minutes"
  - "How to Help Someone Who Is Choking"
'''
            Path(BUNDLES_FILE).write_text(sample, encoding='utf-8')
            print(f"✅ Created sample {BUNDLES_FILE}")
            bundles = load_bundles(BUNDLES_FILE)

    # Строим словарь: название гайда → бандл
    guide_to_bundle = {}
    for b in bundles:
        for g_title in b.get('guides', []):
            guide_to_bundle[g_title.lower()] = b

    # Генерируем страницы
    for g in guides:
        generate_guide_page(g, PREMIUM_DIR, all_guides=guides, all_bundles=bundles, guide_to_bundle=guide_to_bundle)

    for b in bundles:
        generate_bundle_page(b, guides, PREMIUM_DIR, all_bundles=bundles)

    generate_premium_index(guides, bundles, PREMIUM_DIR)

    categories_with_bundles = set(b.get('category') for b in bundles if b.get('category'))
    for cat_id in categories_with_bundles:
        generate_premium_category_page(cat_id, bundles, bundles, guides, PREMIUM_DIR)

    # Дополняем sitemap
    update_premium_sitemap()

    print("✅ All premium pages generated!")


if __name__ == "__main__":
    main()