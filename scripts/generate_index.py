#!/usr/bin/env python3
"""Generate index.html listing all maladaptive daydreaming daily reports."""

import glob
import os
from datetime import datetime

html_files = sorted(glob.glob("docs/md-report-*.html"), reverse=True)
links = ""
for f in html_files[:60]:
    name = os.path.basename(f)
    date = name.replace("md-report-", "").replace(".html", "")
    try:
        d = datetime.strptime(date, "%Y-%m-%d")
        date_display = f"{d.year}年{d.month}月{d.day}日"
    except Exception:
        date_display = date
    weekday_names = ["一", "二", "三", "四", "五", "六", "日"]
    weekday = ""
    if len(date) == 10:
        try:
            weekday = weekday_names[datetime.strptime(date, "%Y-%m-%d").weekday()]
        except ValueError:
            pass
    links += f'<li><a href="{name}">💭 {date_display}（週{weekday}）</a></li>\n'

total = len(html_files)

index = """<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>MD Research Daily &middot; 失功能白日夢文獻日報</title>
<style>
  :root { --bg: #f6f1e8; --surface: #fffaf2; --line: #d8c5ab; --text: #2b2118; --muted: #766453; --accent: #8c4f2b; --accent-soft: #ead2bf; }
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: radial-gradient(circle at top, #fff6ea 0, var(--bg) 55%, #ead8c6 100%); color: var(--text); font-family: "Noto Sans TC", "PingFang TC", "Helvetica Neue", Arial, sans-serif; min-height: 100vh; }
  .container { position: relative; z-index: 1; max-width: 640px; margin: 0 auto; padding: 80px 24px; }
  .logo { font-size: 48px; text-align: center; margin-bottom: 16px; }
  h1 { text-align: center; font-size: 24px; color: var(--text); margin-bottom: 8px; }
  .subtitle { text-align: center; color: var(--accent); font-size: 14px; margin-bottom: 12px; }
  .description { text-align: center; color: var(--muted); font-size: 13px; margin-bottom: 48px; max-width: 480px; margin-left: auto; margin-right: auto; line-height: 1.7; }
  .count { text-align: center; color: var(--muted); font-size: 13px; margin-bottom: 32px; }
  ul { list-style: none; }
  li { margin-bottom: 8px; }
  a { color: var(--text); text-decoration: none; display: block; padding: 14px 20px; background: var(--surface); border: 1px solid var(--line); border-radius: 12px; transition: all 0.2s; font-size: 15px; }
  a:hover { background: var(--accent-soft); border-color: var(--accent); transform: translateX(4px); }
  .footer-links { margin-top: 40px; }
  .footer-link-card { display: flex; align-items: center; gap: 14px; padding: 16px 20px; background: var(--surface); border: 1px solid var(--line); border-radius: 14px; text-decoration: none; color: var(--text); transition: all 0.2s; margin-bottom: 8px; }
  .footer-link-card:hover { background: var(--accent-soft); border-color: var(--accent); transform: translateX(4px); }
  .footer-icon { font-size: 24px; flex-shrink: 0; }
  .footer-name { font-size: 14px; font-weight: 600; }
  .footer-desc { font-size: 11px; color: var(--muted); margin-top: 2px; }
  footer { margin-top: 56px; text-align: center; font-size: 12px; color: var(--muted); }
  footer a { display: inline; padding: 0; background: none; border: none; color: var(--muted); }
  footer a:hover { color: var(--accent); }
</style>
</head>
<body>
<div class="container">
  <div class="logo">💭</div>
  <h1>MD Research Daily</h1>
  <p class="subtitle">失功能白日夢研究文獻日報 &middot; 每日自動更新</p>
  <p class="description">自動追蹤 PubMed 上關於失功能白日夢（Maladaptive Daydreaming）的最新研究，由 AI 分析彙整，提供繁體中文摘要與臨床實用性評估。</p>
  <p class="count">共 """ + str(total) + """ 份報告</p>
  <ul>""" + links + """</ul>
  <div class="footer-links">
    <a href="https://www.leepsyclinic.com/" class="footer-link-card" target="_blank" rel="noopener noreferrer">
      <span class="footer-icon">🏥</span>
      <div>
        <div class="footer-name">李政洋身心診所</div>
        <div class="footer-desc">專業身心科診所，守護您的心理健康</div>
      </div>
    </a>
    <a href="https://blog.leepsyclinic.com/" class="footer-link-card" target="_blank" rel="noopener noreferrer">
      <span class="footer-icon">📨</span>
      <div>
        <div class="footer-name">訂閱電子報</div>
        <div class="footer-desc">接收最新的心理健康資訊與研究動態</div>
      </div>
    </a>
    <a href="https://buymeacoffee.com/CYlee" class="footer-link-card" target="_blank" rel="noopener noreferrer">
      <span class="footer-icon">☕</span>
      <div>
        <div class="footer-name">Buy Me a Coffee</div>
        <div class="footer-desc">支持我們繼續整理失功能白日夢研究文獻</div>
      </div>
    </a>
  </div>
  <footer>
    <p>Powered by PubMed + Zhipu AI &middot; <a href="https://github.com/u8901006/maladaptive-daydreaming">GitHub</a></p>
  </footer>
</div>
</body>
</html>"""

with open("docs/index.html", "w", encoding="utf-8") as f:
    f.write(index)
print("Index page generated")
