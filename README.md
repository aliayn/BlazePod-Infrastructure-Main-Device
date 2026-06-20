# Blazepod Clone Research Workspace

<div align="center">

**English** &nbsp;•&nbsp; **فارسی**

A WAT (Workflows · Agents · Tools) workspace that researches the [Blazepod](https://www.blazepod.com/)
reaction-light training pod and produces a complete, buildable hardware clone —
with parts sourced and priced from the Iranian electronics market.

یک فضای کاری مبتنی بر چارچوب **WAT** (گردش‌کار · عامل · ابزارها) برای تحقیق
دربارهٔ پادهای آموزشی واکنش‌نور **Blazepod** و تولید یک کلون سخت‌افزاری قابل‌ساخت،
با قطعات تأمین‌شده و قیمت‌گذاری‌شده از بازار قطعات الکترونیک ایران.

</div>

---

## 📑 Table of Contents · فهرست

| English | فهرست |
|---|---|
| [What This Is](#what-this-is) | [این پروژه چیست](#این-پروژه-چیست) |
| [Deliverables](#deliverables) | [خروجی‌ها](#خروجی‌ها) |
| [Architecture (WAT)](#architecture-wat) | [معماری (WAT)](#معماری-wat) |
| [Project Structure](#project-structure) | [ساختار پروژه](#ساختار-پروژه) |
| [Requirements](#requirements) | [پیش‌نیازها](#پیشنیازها) |
| [Quick Start](#quick-start) | [شروع سریع](#شروع-سریع) |
| [CLI Reference](#cli-reference) | [مرجع خط فرمان](#مرجع-خط-فرمان) |
| [Environment Variables](#environment-variables) | [متغیرهای محیطی](#متغیرهای-محیطی) |
| [Tools](#tools) | [ابزارها](#ابزارها) |
| [Error Handling & Honesty](#error-handling--honesty) | [مدیریت خطا و صداقت داده](#مدیریت-خطا-و-صداقت-داده) |
| [License](#license) | [مجوز](#مجوز) |

---

# English

## What This Is

This workspace reverse-engineers the Blazepod reaction-light training pod and
produces everything you need to build your own equivalent device from parts
available in the Iranian electronics market.

The brain of the project is the **WAT framework** (defined in
[`claude.md`](./claude.md)):

- **Workflows** — plain-language Markdown files describing the goal, inputs,
  expected output, and error-handling rules for a task.
- **Agents** — an AI coordinator (you, when running this) that reads the
  workflow, makes decisions, and orchestrates the tools.
- **Tools** — reliable, deterministic Python scripts that do the actual work
  (API calls, file rendering, pricing).

The key idea: **AI decides, code executes.** Decisions belong to the agent;
side effects (HTTP fetches, file generation) belong to deterministic tools.
This keeps each step testable and the overall pipeline trustworthy.

## Deliverables

Running `python main.py` produces three files in [`export/`](./export):

| File | Description |
|---|---|
| `export/blazepod-deep-dive.docx` | A deep-dive Word document explaining the Blazepod hardware and software for a reader with **no** hardware background. |
| `export/blazepod-clone-bom.xlsx` | A Bill of Materials mapping every subsystem to an Iran-sourcable part, with live shop pricing in Toman. |
| `export/blazepod-clone-fa.pdf` | A professional **Farsi (RTL)** PDF combining the research and BOM. |

## Architecture (WAT)

```text
┌─────────────────────────────────────────────────────────────┐
│  workflows/blazepod-clone-research.md   ←  THE PLAN          │
│  Goal, inputs, steps, tools, error rules                     │
└───────────────────────────┬─────────────────────────────────┘
                            │  reads & orchestrates
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  AGENT  (main.py / claude.md)    ←  DECIDES                  │
│  Parses workflow, runs tools in order, handles errors        │
└───────────────────────────┬─────────────────────────────────┘
                            │  calls deterministically
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  tools/*.py   ←  EXECUTES                                   │
│  iran_parts.py · build_doc.py · build_bom.py · build_farsi_pdf.py │
└───────────────────────────┬─────────────────────────────────┘
                            ▼
                     export/  (final outputs)
```

## Project Structure

```text
.
├── main.py                  # Entry point — runs the full pipeline
├── requirements.txt         # Python dependencies
├── claude.md                # WAT framework guidelines for the agent
├── README.md                # This file
│
├── .env.example             # Template for environment variables (copy → .env)
│
├── workflows/               # Layer 1 — the plan
│   └── blazepod-clone-research.md
│
├── tools/                   # Layer 3 — deterministic executors
│   ├── iran_parts.py        # Live Iranian shop pricing
│   ├── build_doc.py         # Renders the English .docx
│   ├── build_bom.py         # Renders the BOM .xlsx
│   └── build_farsi_pdf.py   # Renders the Farsi PDF (Playwright/Chromium)
│
├── export/                  # Final deliverables (.docx / .xlsx / .pdf)
│
└── .tmp/                    # Intermediate files (gitignored, disposable)
    ├── part_queries.json    # Component search queries
    ├── iran_parts.json      # Pricing results from iran_parts.py
    ├── blazepod_research.json
    └── farsi.html           # Cached HTML before PDF render
```

> **Note:** `.env`, `.tmp/`, `credentials.json`, `token.json`, and `__pycache__/`
> are all gitignored — see [`.gitignore`](./.gitignore).

## Requirements

- **Python 3.9+**
- **Chromium** (installed automatically by Playwright — see below)
- (Optional) A proxy if fetching Iranian shops from outside Iran

Install Python dependencies:

```bash
pip install -r requirements.txt
python -m playwright install chromium   # only needed for the Farsi PDF
```

Dependencies: `python-docx`, `openpyxl`, `requests`, `beautifulsoup4`,
`python-dotenv`, `playwright`.

## Quick Start

```bash
# 1. Clone & enter the repo
git clone <this-repo>
cd "Sample Workflow"

# 2. Set up the environment
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium

# 3. Configure secrets (optional — defaults work out of the box)
cp .env.example .env
#   edit .env to add IRAN_FETCH_PROXY if you're outside Iran

# 4. Ensure the .tmp/ input files exist
#    (.tmp/part_queries.json and .tmp/blazepod_research.json)
#    These are normally produced by the agent during the workflow.

# 5. Run the full pipeline
python main.py
```

Deliverables land in [`export/`](./export).

## CLI Reference

`main.py` orchestrates every step. Useful flags:

```bash
python main.py                          # full pipeline (live pricing + all docs)
python main.py --use-existing-parts     # skip live shop fetch, reuse .tmp/iran_parts.json
python main.py --skip-pdf               # skip the Farsi PDF
python main.py --skip-bom               # skip the BOM XLSX
python main.py --skip-docx              # skip the English DOCX
python main.py --timeout 20 --delay 2   # slower, more polite shop fetching
```

You can also run each tool directly — see the headers of the scripts in
[`tools/`](./tools) for their exact CLI.

## Environment Variables

All variables are **optional** with sensible defaults. Copy
[`.env.example`](./.env.example) to `.env` and edit:

| Variable | Purpose |
|---|---|
| `AFTABRAYANEH_SEARCH_URL` | Override the Aftabrayaneh shop search endpoint. |
| `ECA_SEARCH_URL` | Override the ECA shop search endpoint. |
| `DICCA_SEARCH_URL` | Override the Dicca shop search endpoint. |
| `MAKERIR_SEARCH_URL` | Override the Maker.ir shop search endpoint. |
| `IRAN_FETCH_PROXY` | Proxy used when fetching Iranian shops from outside Iran (format: `http://user:pass@host:port`). |
| `HTTP_USER_AGENT` | User-agent string for HTTP requests to shop sites. |

## Tools

| Tool | Purpose | Reads | Writes |
|---|---|---|---|
| [`iran_parts.py`](./tools/iran_parts.py) | Live Iranian shop pricing | `.tmp/part_queries.json` | `.tmp/iran_parts.json` |
| [`build_doc.py`](./tools/build_doc.py) | Renders the English deep-dive DOCX | `.tmp/blazepod_research.json` | `export/blazepod-deep-dive.docx` |
| [`build_bom.py`](./tools/build_bom.py) | Renders the BOM spreadsheet | `.tmp/iran_parts.json` | `export/blazepod-clone-bom.xlsx` |
| [`build_farsi_pdf.py`](./tools/build_farsi_pdf.py) | Renders the Farsi RTL PDF via headless Chromium | research + parts JSON | `export/blazepod-clone-fa.pdf` |

### Clone component choices

The clone uses off-the-shelf parts mapped in `COMPONENT_MAP` inside
[`tools/build_bom.py`](./tools/build_bom.py):

| Blazepod subsystem | Clone part |
|---|---|
| Microcontroller + BLE | ESP32-C3 (RISC-V, BLE 5) |
| LEDs | WS2812B addressable RGB ring |
| Battery | 3.7V 600–800 mAh Li-Po with protection |
| Charging | TP4056 USB-C module (+ pogo pins) |
| Tap sensor | TTP223 capacitive module / FSR-402 |
| Housing | 3D-printed PETG/ABS disc + TPU edge ring |
| Diffuser | Translucent 3D print / frosted acrylic |

## Error Handling & Honesty

This workspace is built on a non-negotiable principle: **never fabricate data.**

- **Shop fetch fails** (rate-limit, geo-block, markup change): the component is
  flagged `NEEDS_CONFIRMATION` and surfaced to the user. No invented prices.
- **Unconfirmed spec**: marked `inferred` / `unknown` and rendered with a
  colored confidence tag in the DOCX so the reader knows what's solid.
- **Re-running a paid step**: the agent must ask for approval first, per
  [`claude.md`](./claude.md).

Every error is an opportunity to improve — the cause and limitation are
recorded back into the workflow so a given problem happens only once.

---

# فارسی

## این پروژه چیست

این فضای کاری، پاد آموزشی واکنش‌نور **Blazepod** را مهندسی معکوس می‌کند و
هر آنچه برای ساخت یک دستگاه معادل با قطعاتِ در دسترس در بازار الکترونیک
ایران نیاز دارید، تولید می‌کند.

مغزِ پروژه چارچوب **WAT** است (در [`claude.md`](./claude.md) تعریف شده):

- **Workflows (گردش‌کار)** — فایل‌های Markdown به زبان ساده که هدف، ورودی‌ها،
  خروجی مورد انتظار و قواعد مدیریت خطا را شرح می‌دهند.
- **Agents (عامل)** — یک هماهنگ‌کنندهٔ هوش مصنوعی که گردش‌کار را می‌خواند،
  تصمیم می‌گیرد و ابزارها را رهبری می‌کند.
- **Tools (ابزارها)** — اسکریپت‌های پایتونِ قابل‌اعتماد و قطعی که کار واقعی
  را انجام می‌دهند (فراخوانی API، تولید فایل، قیمت‌گذاری).

ایدهٔ کلیدی: **هوش مصنوعی تصمیم می‌گیرد، کد اجرا می‌کند.** تصمیم‌گیری
بر عهدهٔ عامل است و اثرات جانبی (دریافت از شبکه، تولید فایل) بر عهدهٔ
ابزارهای قطعی. این جداسازی هر مرحله را قابل‌آزمایش و کل مسیر را قابل‌اعتماد
می‌کند.

## خروجی‌ها

اجرای `python main.py` سه فایل در پوشهٔ [`export/`](./export) تولید می‌کند:

| فایل | توضیح |
|---|---|
| `export/blazepod-deep-dive.docx` | یک سند ورد جامع که سخت‌افزار و نرم‌افزار Blazepod را برای خواننده‌ای **بدون** پیش‌زمینهٔ سخت‌افزاری توضیح می‌دهد. |
| `export/blazepod-clone-bom.xlsx` | فهرست قطعات (BOM) که هر زیرسیستم را به قطعه‌ای قابل‌تأمین از ایران، با قیمت زندهٔ فروشگاه‌ها به تومان، نگاشت می‌کند. |
| `export/blazepod-clone-fa.pdf` | یک PDF حرفه‌ای **فارسی (راست‌چین)** که تحقیق و فهرست قطعات را در یک سند ترکیب می‌کند. |

## معماری (WAT)

```text
┌─────────────────────────────────────────────────────────────┐
│  workflows/blazepod-clone-research.md   ←  طرح کار            │
│  هدف، ورودی‌ها، مراحل، ابزارها، قواعد خطا                      │
└───────────────────────────┬─────────────────────────────────┘
                            │  می‌خواند و هماهنگ می‌کند
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  عامل  (main.py / claude.md)         ←  تصمیم‌گیرد             │
│  گردش‌کار را می‌فهمد، ابزارها را به ترتیب اجرا، خطاها را مدیریت می‌کند │
└───────────────────────────┬─────────────────────────────────┘
                            │  به‌صورت قطعی فراخوانی می‌کند
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  tools/*.py   ←  اجرا می‌کند                                  │
│  iran_parts.py · build_doc.py · build_bom.py · build_farsi_pdf.py │
└───────────────────────────┬─────────────────────────────────┘
                            ▼
                     export/  (خروجی‌های نهایی)
```

## ساختار پروژه

```text
.
├── main.py                  # نقطهٔ ورود — اجرای کل خط لوله
├── requirements.txt         # وابستگی‌های پایتون
├── claude.md                # راهنمای چارچوب WAT برای عامل
├── README.md                # همین فایل
│
├── .env.example             # قالب متغیرهای محیطی (کپی کنید → .env)
│
├── workflows/               # لایهٔ ۱ — طرح
│   └── blazepod-clone-research.md
│
├── tools/                   # لایهٔ ۳ — اجراکننده‌های قطعی
│   ├── iran_parts.py        # قیمت زندهٔ فروشگاه‌های ایرانی
│   ├── build_doc.py         # ساخت فایل انگلیسی .docx
│   ├── build_bom.py         # ساخت فایل BOM با .xlsx
│   └── build_farsi_pdf.py   # ساخت PDF فارسی (Playwright/Chromium)
│
├── export/                  # خروجی‌های نهایی (.docx / .xlsx / .pdf)
│
└── .tmp/                    # فایل‌های واسط (نادیده‌گرفته‌شده در git، دورریز)
    ├── part_queries.json    # جستارهای جست‌وجوی قطعات
    ├── iran_parts.json      # نتایج قیمت‌گذاری از iran_parts.py
    ├── blazepod_research.json
    └── farsi.html           # HTML کش‌شده پیش از تولید PDF
```

> **نکته:** `.env`, `.tmp/`, `credentials.json`, `token.json` و `__pycache__/`
> همگی در git نادیده گرفته می‌شوند — ببینید [`.gitignore`](./.gitignore).

## پیش‌نیازها

- **پایتون ۳.۹ به بالا**
- **Chromium** (توسط Playwright به‌صورت خودکار نصب می‌شود — زیر را ببینید)
- (اختیاری) یک پروکسی برای دریافت صفحات فروشگاه‌های ایرانی از خارج ایران

نصب وابستگی‌های پایتون:

```bash
pip install -r requirements.txt
python -m playwright install chromium   # فقط برای PDF فارسی لازم است
```

وابستگی‌ها: `python-docx`, `openpyxl`, `requests`, `beautifulsoup4`,
`python-dotenv`, `playwright`.

## شروع سریع

```bash
# ۱. گرفتن مخزن و ورود به آن
git clone <this-repo>
cd "Sample Workflow"

# ۲. آماده‌سازی محیط
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium

# ۳. پیکربندی اسرار (اختیاری — پیش‌فرض‌ها بدون تنظیم کار می‌کنند)
cp .env.example .env
#   اگر خارج از ایران هستید، IRAN_FETCH_PROXY را در .env اضافه کنید

# ۴. اطمینان از وجود فایل‌های ورودی در .tmp/
#    (.tmp/part_queries.json و .tmp/blazepod_research.json)
#    این فایل‌ها معمولاً توسط عامل در طول گردش‌کار ساخته می‌شوند.

# ۵. اجرای کل خط لوله
python main.py
```

خروجی‌ها در پوشهٔ [`export/`](./export) قرار می‌گیرند.

## مرجع خط فرمان

`main.py` همهٔ مراحل را هماهنگ می‌کند. پرچم‌های پرکاربرد:

```bash
python main.py                          # کل خط لوله (قیمت زنده + همهٔ اسناد)
python main.py --use-existing-parts     # نادیده‌گرفتن قیمت زنده، استفادهٔ مجدد از .tmp/iran_parts.json
python main.py --skip-pdf               # نادیده‌گرفتن PDF فارسی
python main.py --skip-bom               # نادیده‌گرفتن BOM
python main.py --skip-docx              # نادیده‌گرفتن DOCX انگلیسی
python main.py --timeout 20 --delay 2   # دریافت آرام‌تر و مؤدبانه‌تر از فروشگاه‌ها
```

همچنین می‌توانید هر ابزار را مستقیماً اجرا کنید — سرآغاز اسکریپت‌های
[`tools/`](./tools) را برای خط فرمان دقیقِ هرکدام ببینید.

## متغیرهای محیطی

همهٔ متغیرها **اختیاری** هستند و پیش‌فرض‌های معقولی دارند. فایل
[`.env.example`](./.env.example) را به `.env` کپی کرده و ویرایش کنید:

| متغیر | کاربرد |
|---|---|
| `AFTABRAYANEH_SEARCH_URL` | بازنویسی نشانی جست‌وجوی فروشگاه آفتاب رایانه. |
| `ECA_SEARCH_URL` | بازنویسی نشانی جست‌وجوی فروشگاه ECA. |
| `DICCA_SEARCH_URL` | بازنویسی نشانی جست‌وجوی فروشگاه دیکا. |
| `MAKERIR_SEARCH_URL` | بازنویسی نشانی جست‌وجوی Maker.ir. |
| `IRAN_FETCH_PROXY` | پروکسی برای دریافت صفحات فروشگاه‌های ایرانی از خارج ایران (قالب: `http://user:pass@host:port`). |
| `HTTP_USER_AGENT` | رشتهٔ User-Agent برای درخواست‌های HTTP به سایت‌های فروشگاهی. |

## ابزارها

| ابزار | کاربرد | ورودی | خروجی |
|---|---|---|---|
| [`iran_parts.py`](./tools/iran_parts.py) | قیمت زندهٔ فروشگاه‌های ایرانی | `.tmp/part_queries.json` | `.tmp/iran_parts.json` |
| [`build_doc.py`](./tools/build_doc.py) | ساخت سند جامع انگلیسی DOCX | `.tmp/blazepod_research.json` | `export/blazepod-deep-dive.docx` |
| [`build_bom.py`](./tools/build_bom.py) | ساخت صفحه گستردهٔ BOM | `.tmp/iran_parts.json` | `export/blazepod-clone-bom.xlsx` |
| [`build_farsi_pdf.py`](./tools/build_farsi_pdf.py) | ساخت PDF فارسی راست‌چین با Chromium بدون واسط | JSON تحقیق + قطعات | `export/blazepod-clone-fa.pdf` |

### انتخاب قطعات برای کلون

کلون از قطعات آماده‌ای استفاده می‌کند که در `COMPONENT_MAP` داخل
[`tools/build_bom.py`](./tools/build_bom.py) نگاشت شده‌اند:

| زیرسیستم Blazepod | قطعهٔ کلون |
|---|---|
| میکروکنترلر + BLE | ESP32-C3 (RISC-V، BLE 5) |
| LEDها | حلقهٔ RGB آدرس‌پذیر WS2812B |
| باتری | لیتیوم-پلیمر ۳.۷ ولت ۶۰۰ تا ۸۰۰ میلی‌آمپر-ساعت با محافظ |
| شارژ | ماژول TP4056 USB-C (+ پین‌های pogo برای انباشتنی) |
| حسگر لمس | ماژول خازنی TTP223 / FSR-402 |
| قاب | دیسک PETG/ABS چاپ سه‌بعدی + لبهٔ TPU |
| پخش‌کنندهٔ نور | چاپ سه‌بعدی نیمه‌شفاف / اکریلیک مات |

## مدیریت خطا و صداقت داده

این فضای کاری بر یک اصل غیرقابل‌مذاکره بنا شده: **هرگز داده نسازید.**

- **شکست در دریافت از فروشگاه** (محدودیت نرخ، مسدودسازی جغرافیایی، تغییر
  نشانی صفحه): قطعه با `NEEDS_CONFIRMATION` علامت‌گذاری و به کاربر گزارش
  می‌شود. هیچ قیمتی جعل نمی‌شود.
- **مشخصهٔ تأییدنشده**: با `inferred` / `unknown` علامت‌گذاری و در DOCX با یک
  برچسب رنگیِ سطح اطمینان نمایش داده می‌شود تا خواننده بداند چه چیزی محکم است.
- **اجرای مجدد یک مرحلهٔ پولی**: عامل باید پیش از اجرا تأیید بگیرد، طبق
  [`claude.md`](./claude.md).

هر خطا فرصتی برای بهبود است — علت و محدودیت دوباره در گردش‌کار ثبت می‌شوند
تا یک مشکلِ مشخص فقط یک‌بار رخ دهد.

---

## License · مجوز

This workspace is provided as-is for research and educational purposes.
The Blazepod name and product are trademarks of their respective owner; this
project is an independent clone study and is not affiliated with Blazepod.

این فضای کاری صرفاً برای اهداف پژوهشی و آموزشی ارائه می‌شود. نام و محصول
Blazepod متعلق به دارانِ مربوطه است؛ این پروژه یک مطالعهٔ مستقل برای ساخت
کلون است و به Blazepod وابسته نیست.
