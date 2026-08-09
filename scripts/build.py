#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sivas Etkilesim - statik site ureticisi.
data/articles.json dosyasini okuyup index.html, /haberler/<id>/index.html,
sitemap.xml ve robots.txt uretir. Build adimi gerektirmez; uretilen dosyalar
dogrudan Netlify tarafindan statik olarak sunulur.
"""
import json
import os
import html
import datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(ROOT)
DATA_FILE = os.path.join(REPO, "data", "articles.json")
SITE_URL = "https://sivas-etkilesim.netlify.app"
SITE_NAME = "Sivas Etkileşim"

CATEGORY_COLORS = {
    "Gündem":  {"a": "#7A2331", "b": "#4A1620"},
    "Spor":    {"a": "#1F4E5F", "b": "#123038"},
    "Yaşam":   {"a": "#B8860B", "b": "#7A5900"},
    "Ekonomi": {"a": "#3B4252", "b": "#232833"},
    "Kültür":  {"a": "#5B3256", "b": "#391F36"},
}
DEFAULT_COLOR = {"a": "#7A2331", "b": "#4A1620"}

MONTHS_TR = ["Ocak","Şubat","Mart","Nisan","Mayıs","Haziran","Temmuz","Ağustos","Eylül","Ekim","Kasım","Aralık"]


def esc(s):
    return html.escape(s, quote=True)


def fmt_date(iso_str):
    dt = datetime.datetime.fromisoformat(iso_str)
    return f"{dt.day} {MONTHS_TR[dt.month-1]} {dt.year}, {dt.hour:02d}:{dt.minute:02d}"


def cover_svg(category, seed):
    c = CATEGORY_COLORS.get(category, DEFAULT_COLOR)
    h = sum(ord(ch) for ch in seed)
    x1 = 40 + (h % 120)
    y1 = 30 + ((h * 7) % 90)
    r1 = 60 + (h % 50)
    x2 = 300 - (h % 100)
    y2 = 140 + ((h * 3) % 60)
    r2 = 40 + ((h * 5) % 60)
    safe_seed = "".join(ch for ch in seed if ch.isalnum())
    return f'''<svg viewBox="0 0 600 320" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{esc(category)} kapak görseli">
  <defs>
    <linearGradient id="g-{safe_seed}" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{c['a']}"/>
      <stop offset="100%" stop-color="{c['b']}"/>
    </linearGradient>
  </defs>
  <rect width="600" height="320" fill="url(#g-{safe_seed})"/>
  <circle cx="{x1}" cy="{y1}" r="{r1}" fill="#ffffff" opacity="0.08"/>
  <circle cx="{x2}" cy="{y2}" r="{r2}" fill="#ffffff" opacity="0.10"/>
  <line x1="0" y1="260" x2="600" y2="220" stroke="#ffffff" stroke-opacity="0.15" stroke-width="2"/>
  <line x1="0" y1="280" x2="600" y2="300" stroke="#ffffff" stroke-opacity="0.10" stroke-width="1"/>
  <text x="30" y="270" font-family="Georgia, serif" font-size="26" fill="#ffffff" opacity="0.9">{esc(category.upper())}</text>
</svg>'''


def page_shell(title, description, canonical_path, body, extra_head=""):
    canonical = f"{SITE_URL}{canonical_path}"
    return f'''<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{canonical}">
<meta property="og:site_name" content="{SITE_NAME}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{canonical}">
<meta name="twitter:card" content="summary">
<link rel="stylesheet" href="/style.css">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
{extra_head}
</head>
<body>
<header class="site-header">
  <div class="wrap">
    <a class="logo" href="/">Sivas <span>Etkileşim</span></a>
    <p class="tagline">Sivas'tan haberler, kısa özetler ve yorum</p>
  </div>
</header>
{body}
<footer class="site-footer">
  <div class="wrap">
    <p><strong>Sivas Etkileşim</strong> otomatik güncellenen bir haber-yorum sitesidir. Haber özetleri, ilgili kaynaklardan derlenip yeniden yazılmış ve yorumlanmıştır; her haberin altında orijinal kaynağa bağlantı bulunur. Kapak görselleri fotoğraf değildir, kod ile üretilen soyut illüstrasyonlardır.</p>
  </div>
</footer>
</body>
</html>'''


def article_card(a, featured=False):
    cls = "card card-featured" if featured else "card"
    return f'''<a class="{cls}" href="/haberler/{esc(a['id'])}/">
  <div class="card-cover">{cover_svg(a['category'], a['id'])}</div>
  <div class="card-body">
    <span class="badge">{esc(a['category'])}</span>
    <h2>{esc(a['title'])}</h2>
    <p>{esc(a['summary'])}</p>
    <time datetime="{esc(a['published_at'])}">{fmt_date(a['published_at'])}</time>
  </div>
</a>'''


def build_index(articles):
    ordered = sorted(articles, key=lambda a: a["published_at"], reverse=True)
    featured, rest = ordered[0], ordered[1:]
    cards = "\n".join(article_card(a) for a in rest)
    body = f'''<main class="wrap">
  <section class="hero">
    {article_card(featured, featured=True)}
  </section>
  <section class="grid">
    {cards}
  </section>
</main>'''
    return page_shell(
        f"{SITE_NAME} — Sivas Haber ve Yorum",
        "Sivas'tan gündem, spor, yaşam ve ekonomi haberleri; kısa özetler ve bağımsız yorumlarla, her 3 saatte bir güncellenir.",
        "/",
        body,
    )


def build_article(a):
    body_html = "\n".join(f"<p>{esc(p)}</p>" for p in a["body"])
    body = f'''<main class="wrap article">
  <span class="badge">{esc(a['category'])}</span>
  <h1>{esc(a['title'])}</h1>
  <time datetime="{esc(a['published_at'])}">{fmt_date(a['published_at'])}</time>
  <div class="article-cover">{cover_svg(a['category'], a['id'])}</div>
  <div class="article-body">
    {body_html}
  </div>
  <div class="source-box">
    <p>Kaynak: <a href="{esc(a['source_url'])}" rel="nofollow noopener" target="_blank">{esc(a['source_name'])}</a></p>
  </div>
  <p><a class="back-link" href="/">&larr; Tüm haberler</a></p>
</main>'''
    return page_shell(
        f"{a['title']} — {SITE_NAME}",
        a["summary"],
        f"/haberler/{a['id']}/",
        body,
    )


def build_sitemap(articles):
    urls = [f"{SITE_URL}/"] + [f"{SITE_URL}/haberler/{a['id']}/" for a in articles]
    body = "\n".join(f"  <url><loc>{u}</loc></url>" for u in urls)
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{body}
</urlset>'''


def main():
    with open(DATA_FILE, encoding="utf-8") as f:
        articles = json.load(f)

    with open(os.path.join(REPO, "index.html"), "w", encoding="utf-8") as f:
        f.write(build_index(articles))

    for a in articles:
        d = os.path.join(REPO, "haberler", a["id"])
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "index.html"), "w", encoding="utf-8") as f:
            f.write(build_article(a))

    with open(os.path.join(REPO, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(build_sitemap(articles))

    with open(os.path.join(REPO, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n")

    print(f"Uretildi: {len(articles)} haber")


if __name__ == "__main__":
    main()
