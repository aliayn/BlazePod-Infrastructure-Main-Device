# Workflow — Blazepod Clone Research

**Goal:** Produce two deliverables that let the user build a hardware clone of the
[Blazepod](https://www.blazepod.com/) reaction-light training pod, with parts
sourced from the Iranian electronics market:

1. `export/blazepod-deep-dive.docx` — the hardware explained for a reader with
   **no** hardware knowledge, plus how the software works (app, drill logic,
   BLE protocol, metrics).
2. `export/blazepod-clone-bom.xlsx` — a Bill of Materials mapping each subsystem
   to a buildable part, with **live Iranian shop pricing**.

---

## Inputs

- The target product: https://www.blazepod.com/
- (Optional) `tools/` already built: `iran_parts.py`, `build_doc.py`, `build_bom.py`
- `.env` for optional shop-endpoint overrides / proxy (see `.env.example`).

No other inputs required. The agent gathers everything else from the web.

---

## Steps

### 1. Research the hardware

Gather the physical spec of a Blazepod pod. Use `WebSearch` / `WebFetch`.
Priority sources:

- **FCC filing `FCC ID 2AQTQBLAZEPOD`** — internal photos reveal the exact
  microcontroller, LED board, battery, antenna, and sensor. This is the single
  most authoritative source for the hardware clone.
- **blazepod.com** product pages and the Getting Started guide.
- **Teardown / repair videos** (e.g. "Blazepod opening and pin repair").
- **Independent reviews** for battery life, charging, materials, dimensions.

Catalog every subsystem with its confirmed spec and a confidence level
(`confirmed` / `inferred` / `unknown`):

- Battery — chemistry, capacity (mAh), voltage, replaceability.
- LEDs — type, count, color depth, brightness, diffuser.
- Touch / tap sensor — capacitive vs. force vs. accelerometer.
- Bluetooth — BLE version, range, max paired pods, topology.
- Microcontroller — exact SoC if the FCC photos reveal it.
- Charging — connector (micro-USB base), stackable mechanism.
- Housing — materials, IP rating, dimensions, mounting.

**Rule:** never fabricate a spec. If a source doesn't confirm it, mark
`inferred` (with reasoning) or `unknown`.

### 2. Research the software — THIS IS THE PRIORITY

The user most wants to understand the software and how the hardware behaves
under control. Read the **official BlazePod App User Manual** (search returns
several hosted PDF copies — e.g. gymbiz.nl, manusionline.ro). Document:

- **Pairing & topology** — how pods connect to the phone, how many at once.
- **Command model** — how the app tells a pod to light up, change color, turn
  off. Note the BLE GATT services/characteristics if any reverse-engineering
  write-up exists; otherwise describe the *behavior* precisely (latency,
  on/off/color commands).
- **Drill / activity types** — the categories of drills the app supports.
- **Color-coded logic** — target colors (tap when lit) vs. avoid colors
  (don't tap), and how drills use color to add cognitive load.
- **Metrics** — reaction time, hits, misses, and how sessions are scored.
- **Cloud / sync** — multi-user, sessions, leaderboards.

### 3. Map clone components

For each Blazepod subsystem, choose a buildable, Iran-sourcable equivalent:

| Blazepod subsystem | Clone part |
|---|---|
| Microcontroller + BLE | ESP32-C3 (RISC-V, BLE 5 built-in) |
| LEDs | WS2812B addressable RGB ring (8–12 LEDs) |
| Battery | 3.7V 600–800 mAh Li-Po with protection |
| Charging | TP4056 USB-C module (+ pogo pins for stackable) |
| Tap sensor | TTP223 capacitive module, or FSR-402 force sensor |
| Housing | 3D-printed PETG/ABS disc + TPU edge ring |
| Diffuser | Translucent 3D print / frosted acrylic |

These choices are encoded as the `COMPONENT_MAP` inside `tools/build_bom.py`.

### 4. Write the part queries file

Create `.tmp/part_queries.json` — one entry per component id used by
`COMPONENT_MAP`:

```json
[
  {"id": "mcu",          "query": "ESP32-C3",         "aliases": ["esp32 c3", "ایس‌پی ۳۲"]},
  {"id": "leds",         "query": "WS2812B",          "aliases": ["neopixel", "آدرس‌پذیر"]},
  {"id": "battery",      "query": "باتری لیتیوم پلیمر", "aliases": ["LiPo 3.7V", "لیپو"]},
  {"id": "charger",      "query": "TP4056 USB-C",     "aliases": ["شارژر لیتیوم", "tp4056 type-c"]},
  {"id": "touch_sensor", "query": "TTP223",           "aliases": ["خازنی", "capacitive touch"]},
  {"id": "ble",          "query": "ESP32-C3",         "aliases": []},
  {"id": "housing",      "query": "فیلامنت PETG",      "aliases": ["PETG filament"]},
  {"id": "diffuser",     "query": "پلکسی گلاس مات",    "aliases": ["frosted acrylic"]}
]
```

Include Persian aliases — Iranian shops index in both scripts.

### 5. Run `iran_parts.py`

```bash
python tools/iran_parts.py --queries .tmp/part_queries.json --out .tmp/iran_parts.json
```

This queries aftabrayaneh / ECA / dicca / makerir and writes one result row
per shop attempt. **Failures are flagged `NEEDS_CONFIRMATION`, never
invented.** If a shop is unreachable from outside Iran, set `IRAN_FETCH_PROXY`
in `.env`.

### 6. Write the research JSON

Compile steps 1–3 into `.tmp/blazepod_research.json` matching the schema
expected by `tools/build_doc.py`:

```json
{
  "title": "Blazepod — Deep Dive (for a hardware clone)",
  "generated_at": "<ISO timestamp>",
  "sources": [{"label": "...", "url": "..."}],
  "overview": "...",
  "hardware": [
    {"subsystem": "Battery", "blazepod_spec": "...",
     "plain_explanation": "...", "clone_part": "...", "confidence": "confirmed"}
  ],
  "software": [
    {"topic": "How pods pair", "explanation": "...", "confidence": "confirmed"}
  ],
  "build_notes": [{"subsystem": "...", "text": "..."}]
}
```

### 7. Run the document builders

```bash
python tools/build_doc.py --research .tmp/blazepod_research.json --out export/blazepod-deep-dive.docx
python tools/build_bom.py  --parts   .tmp/iran_parts.json           --out export/blazepod-clone-bom.xlsx
python tools/build_farsi_pdf.py \
    --research .tmp/blazepod_research.json \
    --parts    .tmp/iran_parts.json \
    --out      export/blazepod-clone-fa.pdf \
    --html-cache .tmp/farsi.html
```

### 8. Report

Tell the user:

- The two file paths in `export/`.
- How many BOM rows have prices vs. how many need manual confirmation, and
  list the IDs that need confirmation.
- The single most important open question (e.g. exact MCU from FCC photos).

---

## Tools used

| Tool | Purpose |
|---|---|
| `WebSearch` / `WebFetch` | Gather hardware + software research, read the manual PDF |
| `tools/iran_parts.py` | Live Iranian shop pricing → `.tmp/iran_parts.json` |
| `tools/build_doc.py` | Render deep-dive `.docx` from research JSON |
| `tools/build_bom.py` | Render BOM `.xlsx` from parts JSON |
| `tools/build_farsi_pdf.py` | Render professional Farsi (RTL) `.pdf` via Playwright |

Before building any new tool, check `tools/` first (per `claude.md`).

---

## Error handling

- **Shop fetch fails** (rate-limit / geo-block / markup change):
  `iran_parts.py` records `NEEDS_CONFIRMATION` and moves on. Surface these to
  the user; do not fabricate prices. If repeated, set `IRAN_FETCH_PROXY`.
- **A spec can't be confirmed:** mark `inferred`/`unknown` in the research
  JSON. The `.docx` renders it with a colored confidence tag so the reader
  knows what's solid.
- **`iran_parts.py` finds no result for a component:** that row becomes
  `NOT_FOUND` in the BOM. Suggest broadening the query aliases and re-running
  (this doesn't cost API credits — safe to retry).
- **Re-running a paid step** (e.g. a future search API that bills per call):
  get the user's approval first, per `claude.md`.

After resolving any issue, record the cause + limitation back into this
workflow so it doesn't recur.

---

## Notes

- Deliverables are local `.docx` / `.xlsx`. `claude.md` prefers cloud output
  (Google Docs/Sheets), but no `credentials.json` / `token.json` exist yet.
  The tools are structured so the export target can be swapped to Google
  later without rewriting the research step.
- All intermediate files live in `.tmp/` and are disposable/regeneratable.

---

## Run log — 2026-06-20 (first run)

### What worked
- **FCC internal photos** (fccid.io) were gold: the MCU chip is confirmed as **Nordic nRF51822** from silkscreen markings on PCB revision CYT_POD_A2. Test report confirms BLE 4.0 / GFSK / 1Mbps.
- **WebSearch** found real Iranian prices via torob.com and peno.ir for 3 of 8 components (WS2812B, LiPo 600mAh, TP4056).
- `build_doc.py` and `build_bom.py` ran cleanly and produced valid deliverables.

### What didn't work
- **`iran_parts.py` shop scrapers returned zero results.** Aftabrayaneh uses OpenCart with JS-rendered search (anti-bot). ECA and dicca were unreachable (HTTP 000). Maker.ir returned only course listings, no shop products. The tool needs a rewrite to either: (a) use a headless browser (Playwright/Selenium), or (b) delegate to `WebSearch` with site-specific queries instead of direct scraping.
- The BOM has `estimated_price_toman` fields that `build_bom.py` doesn't read yet — they were added manually to the JSON. Update `build_bom.py` to fall back to estimates when no live price exists.
- FCC internal photos are pure images with no OCR text — we used vision analysis instead. For future runs, install `tesseract` + `pytesseract` for offline OCR.

### Rows needing manual confirmation (5 of 8)
`mcu`, `touch_sensor`, `ble` (zero cost), `housing`, `diffuser`. The user should verify ESP32-C3 pricing on aftabrayaneh.com and TTP223 on jamtronic.com.

### Open question
The FCC photos show 9 discrete (single-color?) LEDs in a 3x3 grid on rev A2, yet the app renders multiple colors. Either production pods use different LEDs, or color comes from a different mechanism. This does not block the clone (WS2812B gives full color regardless).
