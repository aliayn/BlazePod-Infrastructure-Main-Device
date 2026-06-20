#!/usr/bin/env python3
"""
build_farsi_pdf.py — Professional Farsi (RTL) PDF from Blazepod research + BOM.

WHAT IT DOES
    Reads .tmp/blazepod_research.json and .tmp/iran_parts.json, builds a
    professional right-to-left Farsi HTML document, and renders it to a
    vector PDF via headless Chromium (Playwright).

USAGE
    python3 tools/build_farsi_pdf.py \
        --research .tmp/blazepod_research.json \
        --parts    .tmp/iran_parts.json \
        --out      export/blazepod-clone-fa.pdf

OUTPUT
    export/blazepod-clone-fa.pdf — A4, ~10-15 pages, selectable text.
"""

import argparse
import html as _html
import json
import sys
from datetime import datetime
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sys.stderr.write(
        "Playwright not installed. Run:\n"
        "  pip install playwright && python -m playwright install chromium\n"
    )
    raise


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def esc(text):
    """HTML-escape a string."""
    return _html.escape(str(text)) if text is not None else ""


def ltr(term):
    """Wrap an LTR (English/number) token so it renders correctly inside RTL text."""
    return f'<span dir="ltr">{esc(term)}</span>'


# Confidence → Farsi label + color
CONFIDENCE = {
    "confirmed": ("تأییدشده", "#1B7A43", "#D4EDDA"),
    "inferred": ("احتمالی", "#B86A00", "#FFF3CD"),
    "unknown": ("نامشخص", "#A11D1D", "#F8D7DA"),
}


def badge(confidence):
    if not confidence or confidence not in CONFIDENCE:
        confidence = "unknown"
    label, fg, bg = CONFIDENCE[confidence]
    return (
        f'<span class="badge" style="color:{fg};background:{bg};">'
        f'سطح اطمینان: {label}</span>'
    )


def md_to_html(text):
    """Very small markdown-ish renderer: blank lines → paragraphs, '- ' → bullets."""
    if not text:
        return "<p class=\"muted\">(اطلاعاتی موجود نیست)</p>"
    import re
    # escape first
    text = esc(text)
    blocks = re.split(r"\n\s*\n", text)
    out = []
    for block in blocks:
        lines = [ln for ln in block.splitlines() if ln.strip()]
        if not lines:
            continue
        if all(ln.lstrip().startswith(("-", "*")) for ln in lines):
            items = "".join(
                f"<li>{ln.lstrip().lstrip('-*').strip()}</li>" for ln in lines
            )
            out.append(f"<ul>{items}</ul>")
        else:
            joined = " ".join(ln.strip() for ln in lines)
            out.append(f"<p>{joined}</p>")
    return "\n".join(out)


def status_badge(part):
    if not part:
        return ("یافت نشد", "#A11D1D", "#F8D7DA")
    results = part.get("results", [])
    priced = [r for r in results if r.get("price_toman")]
    if priced:
        return ("قیمت تأییدشده", "#1B7A43", "#D4EDDA")
    if results:
        return ("نیازمند تأیید", "#B86A00", "#FFF3CD")
    return ("یافت نشد", "#A11D1D", "#F8D7DA")


# ---------------------------------------------------------------------------
# Component map (mirrors build_bom.py COMPONENT_MAP)
# ---------------------------------------------------------------------------
COMPONENT_MAP = {
    "mcu": ("پردازنده (میکروکنترلر)", "مغز پاد", "Nordic nRF51822", "ESP32-C3"),
    "leds": ("ال‌ای‌دی‌ها (نور)", "نور رنگی پاد", "۹ عدد LED مجزا (نسخه FCC)", "حلقه WS2812B"),
    "battery": ("باتری", "ذخیره انرژی", "Li-Po 3.7V 600mAh", "باتری لیپو ۶۰۰mAh با محافظ"),
    "charger": ("مدار شارژ", "شارژ امن باتری", "پایه شارژ استک‌پذیر micro-USB", "ماژول TP4056 USB-C"),
    "touch_sensor": ("سنسور لمسی/ضربه", "تشخیص ضربه ورزشکار", "احتمالاً خازنی یا فشاری", "ماژول TTP223 خازنی"),
    "ble": ("بلوتوث (BLE)", "ارتباط بی‌سیم با موبایل", "BLE 4.0 (داخل nRF51822)", "داخل ESP32-C3 (بدون قطعه اضافه)"),
    "housing": ("قاب (پوسته)", "نگه‌داری قطعات و مقاومت", "ABS/پلی‌کربنات + لبه سیلیکونی", "چاپ سه‌بعدی PETG"),
    "diffuser": ("دیفیوزر (پخش‌کننده نور)", "پخش یکنواخت نور", "روپوش نیمه‌شفاف", "آکریلیک مات یا چاپ نیمه‌شفاف"),
}


# ---------------------------------------------------------------------------
# HTML assembly
# ---------------------------------------------------------------------------
CSS = """
@import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@300;400;500;600;700;800&display=swap');

* { box-sizing: border-box; }

html { font-family: 'Vazirmatn', 'Segoe UI', Tahoma, sans-serif; }
body {
  font-family: 'Vazirmatn', 'Segoe UI', Tahoma, sans-serif;
  font-size: 11pt;
  line-height: 1.95;
  color: #1a1a1a;
  margin: 0;
  direction: rtl;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}

@page { size: A4; margin: 18mm 16mm 20mm 16mm; }

/* ---------- Cover ---------- */
.cover {
  page-break-after: always;
  height: 245mm;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  text-align: center;
  background: linear-gradient(135deg, #0f1e3d 0%, #1b4e9e 100%);
  color: #fff;
  margin: -18mm -16mm 0 -16mm;
  padding: 40mm 20mm;
}
.cover h1 { font-size: 30pt; font-weight: 800; margin: 0 0 8mm 0; line-height: 1.4; }
.cover h2 { font-size: 14pt; font-weight: 400; color: #b8d4f0; margin: 0 0 20mm 0; }
.cover .meta { font-size: 10pt; color: #8fb3d9; line-height: 2.2; }
.cover .accent { width: 60mm; height: 4px; background: #4d9fff; margin: 8mm auto; border-radius: 2px; }

/* ---------- Headings ---------- */
h2.section {
  font-size: 18pt;
  font-weight: 700;
  color: #0f1e3d;
  border-right: 5px solid #1b4e9e;   /* RTL: accent on right */
  padding-right: 10px;
  margin: 0 0 6mm 0;
  page-break-before: always;
  page-break-after: avoid;
}
h3.sub {
  font-size: 13.5pt;
  font-weight: 600;
  color: #1b4e9e;
  margin: 7mm 0 3mm 0;
  page-break-after: avoid;
}
h4 { font-size: 11.5pt; font-weight: 600; color: #2a2a2a; margin: 4mm 0 2mm 0; page-break-after: avoid; }

/* ---------- Text ---------- */
p { margin: 0 0 3mm 0; text-align: justify; }
ul, ol { margin: 0 4mm 3mm 0; padding-right: 0; }
li { margin-bottom: 2mm; }
.muted { color: #888; font-style: italic; }
.label { font-weight: 700; color: #0f1e3d; }

/* ---------- Badges ---------- */
.badge {
  display: inline-block;
  font-size: 8.5pt;
  font-weight: 600;
  padding: 1px 8px;
  border-radius: 10px;
  margin-bottom: 2mm;
}

/* ---------- Cards ---------- */
.card {
  background: #f7f9fc;
  border: 1px solid #e1e8f0;
  border-radius: 6px;
  padding: 4mm 5mm;
  margin-bottom: 5mm;
  page-break-inside: avoid;
}
.card .row { margin-bottom: 2.5mm; }
.card .row:last-child { margin-bottom: 0; }

/* ---------- Table ---------- */
table {
  width: 100%;
  border-collapse: collapse;
  margin: 3mm 0 6mm 0;
  font-size: 9.5pt;
  page-break-inside: auto;
}
thead { display: table-header-group; }
tr { page-break-inside: avoid; }
th {
  background: #1b4e9e;
  color: #fff;
  font-weight: 600;
  padding: 6px 5px;
  text-align: right;
  border: 1px solid #1b4e9e;
}
td {
  padding: 6px 5px;
  border: 1px solid #d8e0ea;
  vertical-align: top;
  line-height: 1.6;
}
tbody tr:nth-child(even) { background: #f5f8fc; }
.warn-row { background: #FFF9E6 !important; }
.ok-row td:last-child { color: #1B7A43; font-weight: 600; }

/* ---------- TOC ---------- */
.toc { page-break-after: always; }
.toc h2 { font-size: 18pt; color: #0f1e3d; border: none; padding: 0; }
.toc ol { list-style: none; padding: 0; counter-reset: toc; }
.toc li {
  counter-increment: toc;
  padding: 3mm 0;
  border-bottom: 1px dotted #cdd6e0;
  font-size: 11pt;
}
.toc li::before {
  content: counter(toc) ". ";
  color: #1b4e9e;
  font-weight: 700;
  margin-left: 6px;
}

/* ---------- Steps ---------- */
.step { page-break-inside: avoid; margin-bottom: 5mm; }
.step-num {
  display: inline-block;
  width: 9mm; height: 9mm;
  background: #1b4e9e; color: #fff;
  border-radius: 50%;
  text-align: center; line-height: 9mm;
  font-weight: 700; font-size: 11pt;
  margin-left: 3mm;
}
.step h4 { display: inline; color: #0f1e3d; }

/* ---------- Footer ---------- */
.footnote { font-size: 9pt; color: #666; margin-top: 6mm; }
a { color: #1a4e9e; text-decoration: none; }
a:hover { text-decoration: underline; }

/* ---------- Pitfalls ---------- */
.pitfall { border-right: 4px solid #d9534f; background: #fcf0f0; }
.pitfall-ok { border-right: 4px solid #1B7A43; background: #f0f9f4; }
"""


def cover_block(data):
    title = esc(data.get("title_fa") or "بلِیزپاد — راهنمای کامل ساخت نمونه ایرانی")
    subtitle = "بررسی فنی سخت‌افزار و نرم‌افزار + راهنمای گام‌به‌گام ساخت با قطعات بازار ایران"
    date = data.get("generated_at", "")[:10]
    return f"""
    <section class="cover">
      <h1>{title}</h1>
      <div class="accent"></div>
      <h2>{esc(subtitle)}</h2>
      <div class="meta">
        تاریخ تهیه: {esc(date)}<br>
        منبع تحقیق: مستندات FCC + دفترچه راهنمای رسمی + منابع مستقل<br>
        خروجی سیستم: WAT Framework
      </div>
    </section>
    """


def toc_block():
    return """
    <section class="toc">
      <h2>فهرست مطالب</h2>
      <ol>
        <li>مقدمه و مرور کلی</li>
        <li>بخش اول: سخت‌افزار — نحوه کار قطعات (به زبان ساده)</li>
        <li>بخش دوم: نرم‌افزار — نحوه کار سیستم</li>
        <li>بخش سوم: نحوه ساخت یک نمونه در ایران</li>
        <li>بخش چهارم: قطعات و قیمت‌ها (BOM)</li>
        <li>بخش پنجم: منابع و مآخذ</li>
      </ol>
    </section>
    """


def overview_block(data):
    text = data.get("overview_fa") or data.get("overview", "")
    return f"""
    <h2 class="section" id="overview">۱. مقدمه و مرور کلی</h2>
    {md_to_html(text)}
    <div class="card">
      <div class="row"><span class="label">چیپ اصلی دستگاه اصلی:</span> {ltr("Nordic nRF51822")} (تأییدشده از مستندات {ltr("FCC")})</div>
      <div class="row"><span class="label">نسخه بلوتوث:</span> {ltr("BLE 4.0")} — مدولاسیون {ltr("GFSK")}، سرعت ۱ مگابیت بر ثانیه</div>
      <div class="row"><span class="label">قطعه پیشنهادی جایگزین:</span> {ltr("ESP32-C3")} (ارزان‌تر، در دسترس‌تر در ایران، بلوتوث ۵ داخلی)</div>
      <div class="row"><span class="label">هزینه تخمینی هر پاد:</span> حدود ۴۰۰٬۰۰۰ تا ۵۵۰٬۰۰۰ تومان</div>
    </div>
    """


def hardware_block(data):
    parts = [f'<h2 class="section" id="hardware">۲. سخت‌افزار — نحوه کار قطعات (به زبان ساده)</h2>']
    parts.append(
        '<p>در این بخش هر قطعه از پاد بلیزپاد را به زبان ساده توضیح می‌دهیم، '
        'طوری که نیازی به دانش قبلی الکترونیک نداشته باشید. '
        'برای هر قطعه: مشخصات اصلی، توضیح ساده، و قطعه‌ای که می‌توانید برای ساخت نمونه ایرانی استفاده کنید.</p>'
    )
    for i, hw in enumerate(data.get("hardware", []), start=1):
        parts.append(f'<h3 class="sub" id="hw-{i}">۲.{i} {esc(hw.get("subsystem", ""))}</h3>')
        parts.append(badge(hw.get("confidence")))
        if hw.get("blazepod_spec"):
            parts.append(f'<h4>مشخصات بلیزپاد:</h4>')
            parts.append(md_to_html(hw["blazepod_spec"]))
        if hw.get("plain_explanation"):
            parts.append(f'<h4>به زبان ساده:</h4>')
            parts.append(md_to_html(hw["plain_explanation"]))
        if hw.get("clone_part"):
            parts.append(f'<h4>قطعه پیشنهادی برای ساخت:</h4>')
            parts.append(md_to_html(hw["clone_part"]))
    return "\n".join(parts)


def software_block(data):
    parts = [f'<h2 class="section" id="software">۳. نرم‌افزار — نحوه کار سیستم</h2>']
    parts.append(
        '<p>این بخش مهم‌ترین قسمت برای شماست: چگونه نرم‌افزار، سخت‌افزار را کنترل می‌کند '
        'و سیستم در عمل چگونه رفتار می‌کند.</p>'
    )
    for i, sw in enumerate(data.get("software", []), start=1):
        parts.append(f'<h3 class="sub" id="sw-{i}">۳.{i} {esc(sw.get("topic", ""))}</h3>')
        parts.append(badge(sw.get("confidence")))
        parts.append(md_to_html(sw.get("explanation", "")))
    return "\n".join(parts)


def build_guide_block(data):
    guide = data.get("build_guide_iran")
    if not guide:
        return ""
    parts = [
        f'<h2 class="section" id="build">۴. نحوه ساخت یک نمونه در ایران</h2>',
        md_to_html(guide.get("summary", "")),
    ]

    # Tools needed
    tools = guide.get("tools_needed", [])
    if tools:
        parts.append('<h3 class="sub">ابزارها و تجهیزات لازم</h3>')
        items = "".join(f"<li>{md_to_html(t)}</li>" for t in tools)
        parts.append(f"<ul>{items}</ul>")

    # Steps
    steps = guide.get("steps", [])
    if steps:
        parts.append('<h3 class="sub">مراحل ساخت</h3>')
        for i, step in enumerate(steps, start=1):
            parts.append('<div class="step">')
            parts.append(
                f'<span class="step-num">{i}</span>'
                f'<h4>{esc(step.get("title", ""))}</h4>'
            )
            parts.append(md_to_html(step.get("detail", "")))
            parts.append('</div>')

    # Pitfalls
    pitfalls = guide.get("pitfalls", [])
    if pitfalls:
        parts.append('<h3 class="sub">اشتباهات رایج و راه‌حل‌ها</h3>')
        for p in pitfalls:
            parts.append('<div class="card pitfall">')
            parts.append(
                f'<div class="row"><span class="label">خطر:</span> {md_to_html(p.get("risk",""))}</div>'
            )
            parts.append(
                f'<div class="row"><span class="label">راه‌حل:</span> {md_to_html(p.get("fix",""))}</div>'
            )
            parts.append('</div>')

    # Firmware outline
    fw = guide.get("firmware_outline", {})
    if fw:
        parts.append('<h3 class="sub">طرح کلی فیرمویر (Firmware)</h3>')
        libs = fw.get("libraries", [])
        if libs:
            items = "".join(f"<li>{ltr(l)}</li>" for l in libs)
            parts.append(f'<h4>کتابخانه‌های لازم:</h4><ul>{items}</ul>')
        loop = fw.get("core_loop", [])
        if loop:
            items = "".join(f"<li>{md_to_html(s)}</li>" for s in loop)
            parts.append(f'<h4>منطق اصلی برنامه:</h4><ol>{items}</ol>')
        if fw.get("latency_target"):
            parts.append(
                f'<div class="card pitfall-ok"><span class="label">هدف تأخیر:</span> '
                f'{esc(fw["latency_target"])}</div>'
            )
        if fw.get("battery_target"):
            parts.append(
                f'<div class="card pitfall-ok"><span class="label">هدف باتری:</span> '
                f'{esc(fw["battery_target"])}</div>'
            )

    return "\n".join(parts)


def bom_block(parts_data):
    out = [
        f'<h2 class="section" id="bom">۵. قطعات و قیمت‌ها (Bill of Materials)</h2>',
        '<p>جدول کامل قطعات برای ساخت یک پاد. قیمت‌ها به تومان و در زمان تهیه بوده‌اند. '
        'ردیف‌های «نیازمند تأیید» را باید خودتان در فروشگاه تأیید کنید.</p>',
    ]

    # Map parts by id
    by_id = {p["id"]: p for p in parts_data}

    out.append('<table>')
    out.append(
        '<thead><tr>'
        '<th>زیرسیستم</th><th>قطعه پیشنهادی</th><th>مشخصه بلیزپاد</th>'
        '<th>فروشگاه</th><th>قیمت (تومان)</th><th>وضعیت</th>'
        '</tr></thead><tbody>'
    )

    for cid, (fa_name, role, bp_spec, suggested) in COMPONENT_MAP.items():
        part = by_id.get(cid)
        results = part.get("results", []) if part else []
        # pick best priced result
        priced = [r for r in results if r.get("price_toman")]
        best = min(priced, key=lambda r: r["price_toman"]) if priced else (results[0] if results else None)

        shop = best.get("shop", "—") if best else "—"
        price_str = f'{best["price_toman"]:,}' if best and best.get("price_toman") else "—"
        status_label, status_fg, status_bg = status_badge(part)

        row_class = ""
        if status_label == "نیازمند تأیید":
            row_class = "warn-row"
        elif status_label == "قیمت تأییدشده":
            row_class = "ok-row"

        url = best.get("url", "") if best else ""
        shop_cell = f'<a href="{esc(url)}">{esc(shop)}</a>' if url else esc(shop)

        out.append(
            f'<tr class="{row_class}">'
            f'<td><strong>{esc(fa_name)}</strong><br><span class="muted">{esc(role)}</span></td>'
            f'<td>{esc(suggested)}</td>'
            f'<td>{esc(bp_spec)}</td>'
            f'<td>{shop_cell}</td>'
            f'<td>{price_str}</td>'
            f'<td style="color:{status_fg};font-weight:600;">{esc(status_label)}</td>'
            f'</tr>'
        )

    out.append('</tbody></table>')

    # Note on estimates
    out.append(
        '<div class="footnote">'
        '<strong>توضیح:</strong> فروشگاه‌های الکترونیکی ایران اغلب جستجوی خودکار را محدود می‌کنند. '
        'برخی قیمت‌ها از مقایسه‌کننده‌های قیمت (مثل torob.com) یا از تخمین بازار گرفته شده‌اند '
        'و باید قبل از خرید تأیید شوند. تعداد قطعات برای <strong>یک پاد</strong> است — '
        'برای کیت کامل در ۴ یا ۶ برابر ضرب کنید.'
        '</div>'
    )
    return "\n".join(out)


def sources_block(data):
    sources = data.get("sources", [])
    if not sources:
        return ""
    out = [
        f'<h2 class="section" id="sources">۶. منابع و مآخذ</h2>',
        '<p>تمام ادعاهای فنی این سند به یکی از منابع زیر استناد می‌کند. '
        'مهم‌ترین منبع، مستندات FCC است که عکس‌های داخلی و مشخصات رادیویی دستگاه اصلی را ارائه می‌دهد.</p>',
    ]
    items = []
    for s in sources:
        label = esc(s.get("label", s.get("url", "")))
        url = esc(s.get("url", ""))
        items.append(f'<li><a href="{url}">{label}</a><br><span class="muted">{url}</span></li>')
    out.append(f"<ul>{''.join(items)}</ul>")
    return "\n".join(out)


def build_html(data, parts_data):
    return f"""<!DOCTYPE html>
<html dir="rtl" lang="fa">
<head>
<meta charset="utf-8">
<title>بلِیزپاد — راهنمای ساخت نمونه ایرانی</title>
<style>{CSS}</style>
</head>
<body>
{cover_block(data)}
{toc_block()}
{overview_block(data)}
{hardware_block(data)}
{software_block(data)}
{build_guide_block(data)}
{bom_block(parts_data)}
{sources_block(data)}
</body>
</html>"""


# ---------------------------------------------------------------------------
# PDF rendering via Playwright
# ---------------------------------------------------------------------------
def render_pdf(html_str, out_path, html_cache=None):
    out_path = Path(out_path).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if html_cache:
        cache = Path(html_cache).resolve()
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(html_str, encoding="utf-8")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(html_str, wait_until="networkidle")
        # Ensure fonts are loaded
        page.evaluate("document.fonts.ready")
        page.pdf(
            path=str(out_path),
            format="A4",
            print_background=True,
            margin={"top": "18mm", "bottom": "20mm", "left": "16mm", "right": "16mm"},
            display_header_footer=True,
            header_template="<div></div>",
            footer_template=(
                '<div style="font-size:8pt; width:100%; text-align:center; '
                'color:#888; font-family: sans-serif; direction:rtl;">'
                'بلِیزپاد — راهنمای ساخت نمونه ایرانی &nbsp;|&nbsp; صفحه '
                '<span class="pageNumber"></span> از <span class="totalPages"></span>'
                '</div>'
            ),
        )
        browser.close()

    sys.stdout.write(f"[build_farsi_pdf] Wrote {out_path}\n")
    return out_path


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    p.add_argument("--research", required=True, help="Path to blazepod_research.json")
    p.add_argument("--parts", required=True, help="Path to iran_parts.json")
    p.add_argument("--out", required=True, help="Output .pdf path")
    p.add_argument(
        "--html-cache",
        default=None,
        help="Optional path to also save the intermediate HTML",
    )
    args = p.parse_args()

    with Path(args.research).open(encoding="utf-8") as f:
        data = json.load(f)
    with Path(args.parts).open(encoding="utf-8") as f:
        parts_data = json.load(f)

    html_str = build_html(data, parts_data)
    render_pdf(html_str, args.out, html_cache=args.html_cache)


if __name__ == "__main__":
    main()
