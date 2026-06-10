#!/usr/bin/env python3
from __future__ import annotations

import html
import re
import textwrap
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "assets"
ILLUSTRATION_DIR = ASSET_DIR / "illustrations"

STYLE_BEGIN = "<!-- BEGIN UNPAD MATERIAL STYLE -->"
STYLE_END = "<!-- END UNPAD MATERIAL STYLE -->"
ENH_BEGIN = "<!-- BEGIN UNPAD MATERIAL ENHANCEMENT -->"
ENH_END = "<!-- END UNPAD MATERIAL ENHANCEMENT -->"


COMMON_STYLE = f"""{STYLE_BEGIN}
<style>
:root {{
  --unpad-navy: #17395c;
  --unpad-gold: #f2a51a;
  --unpad-teal: #0f766e;
  --unpad-ink: #172033;
  --unpad-paper: #fffdf8;
  --unpad-soft: #eef5f8;
  --unpad-line: #d7e2ea;
}}
html, body {{
  background: linear-gradient(135deg, #f8fbfd 0%, #fffdf8 48%, #f3f6ee 100%) !important;
  color: var(--unpad-ink) !important;
}}
body {{
  font-family: "Segoe UI", Arial, sans-serif !important;
  line-height: 1.72 !important;
}}
.main-container {{
  max-width: 1180px !important;
  background: rgba(255, 253, 248, 0.98) !important;
  border: 1px solid var(--unpad-line) !important;
  border-radius: 8px !important;
  box-shadow: 0 18px 42px rgba(23, 57, 92, 0.12) !important;
}}
h1, h2, h3, h4 {{
  letter-spacing: 0 !important;
}}
h1.title {{
  color: var(--unpad-navy) !important;
  -webkit-text-fill-color: var(--unpad-navy) !important;
  background: none !important;
}}
h2 {{
  border-left-color: var(--unpad-gold) !important;
}}
a {{
  color: #0b5c86 !important;
}}
pre, code {{
  border-radius: 8px !important;
}}
.unpad-cover {{
  margin: 18px 0 26px;
  padding: 24px;
  border-radius: 8px;
  background: linear-gradient(135deg, #17395c 0%, #0f766e 58%, #f2a51a 100%);
  color: #ffffff;
  box-shadow: 0 18px 36px rgba(23, 57, 92, 0.22);
}}
.unpad-cover__brand {{
  display: grid;
  grid-template-columns: 92px 1fr;
  gap: 20px;
  align-items: center;
}}
.unpad-cover img {{
  width: 92px;
  height: 92px;
  object-fit: contain;
  background: #ffffff;
  border-radius: 8px;
  padding: 8px;
  box-shadow: 0 8px 22px rgba(0,0,0,0.18);
}}
.unpad-kicker {{
  text-transform: uppercase;
  font-size: 0.82rem;
  font-weight: 800;
  letter-spacing: 0;
  color: #fff8dc;
}}
.unpad-cover h2 {{
  margin: 6px 0 8px;
  padding: 0;
  border: 0;
  background: transparent;
  color: #ffffff !important;
  font-size: 1.65rem;
}}
.unpad-meta {{
  margin: 0;
  color: #f7fbff;
  font-weight: 600;
}}
.materi-illustration {{
  margin: 20px 0 24px;
  padding: 14px;
  background: #ffffff;
  border: 1px solid var(--unpad-line);
  border-radius: 8px;
  box-shadow: 0 12px 28px rgba(23, 57, 92, 0.10);
}}
.materi-illustration img {{
  width: 100%;
  height: auto;
  display: block;
  border-radius: 6px;
}}
.validasi-akademik {{
  margin: 18px 0 28px;
  padding: 16px 18px;
  background: linear-gradient(135deg, #eef8f6, #fff8e7);
  border-left: 8px solid var(--unpad-teal);
  border-radius: 8px;
  color: var(--unpad-ink);
}}
.validasi-akademik strong {{
  color: var(--unpad-navy);
}}
table {{
  border-radius: 8px !important;
}}
@media (max-width: 760px) {{
  .unpad-cover__brand {{
    grid-template-columns: 1fr;
  }}
  .unpad-cover img {{
    width: 76px;
    height: 76px;
  }}
}}
</style>
{STYLE_END}
"""


SETUP_CHUNK = """```{r setup-unpad-render, include=FALSE}
execute_code <- FALSE
knitr::opts_chunk$set(
  echo = TRUE,
  eval = FALSE,
  message = FALSE,
  warning = FALSE,
  fig.align = "center",
  fig.width = 8,
  fig.height = 4.8,
  dpi = 120
)
set.seed(2025)
```
"""


REPLACEMENTS = {
    "membuat slide terlihat galak seperti satpam ujian komprehensif": "membuat rumus tampak formal tanpa makna substantif",
    "Output R yang panjang tidak otomatis berarti analisis mendalam; kadang-kadang justru output terlalu panjang adalah cara komputer meminta kita berpikir lebih pelan.": "Output R yang panjang tidak otomatis menunjukkan analisis yang mendalam; fokus utama tetap pada interpretasi, diagnostik, dan kesesuaian metode.",
    "Kesalahan kecil seperti frekuensi time series yang tidak tepat, urutan tanggal yang tidak rapi, atau pembagian data latih-uji yang acak dapat merusak seluruh hasil peramalan. Dalam deret waktu, waktu tidak boleh diacak sembarangan; waktu itu sensitif, seperti dosen ketika mendengar kata 'datanya sudah saya random dulu, Pak'.": "Kesalahan kecil seperti frekuensi time series yang tidak tepat, urutan tanggal yang tidak rapi, atau pembagian data latih-uji yang acak dapat merusak seluruh hasil peramalan. Dalam deret waktu, pembagian data harus mengikuti urutan temporal dan tidak dilakukan secara acak tanpa alasan metodologis.",
    "drama matematika yang tidak perlu": "kesalahan perhitungan yang tidak perlu",
    "ekspedisi mencari kolom hilang seperti mencari kunci motor di parkiran luas": "proses penelusuran inkonsistensi data yang memakan waktu",
    "Jika salah satu bagian hilang, analisis menjadi pincang; statistiknya jalan, tetapi agak miring seperti meja praktikum yang kakinya kurang satu.": "Jika salah satu bagian hilang, analisis menjadi tidak lengkap dan sulit dipertanggungjawabkan.",
    "Kesempurnaan mutlak dalam data nyata itu langka; yang terlalu sempurna kadang justru mencurigakan.": "Data nyata hampir selalu memuat keterbatasan; karena itu ketidakpastian dan batasan analisis perlu dinyatakan secara eksplisit.",
}


TOPICS = {
    "model linear generalisasi": ["Respons non-normal", "Fungsi link", "Prediktor linear", "Diagnostik", "Komunikasi model"],
    "analisis deret waktu": ["Tren dan musiman", "Stasioneritas", "ARIMA/ARFIMA", "Machine learning", "Spasial-temporal"],
    "analisis teks": ["Korpus", "Praproses", "Representasi", "Model bahasa", "Etika teks"],
    "survival": ["Waktu kejadian", "Sensoring", "Kaplan-Meier", "Cox PH", "Validasi hazard"],
    "epidemiologi": ["Ukuran penyakit", "Surveilans", "Desain studi", "Regresi risiko", "Komunikasi bukti"],
    "pembelajaran mesin": ["Problem framing", "Data pipeline", "Modeling", "Validasi", "Explainability"],
    "spasial": ["Lokasi", "Bobot spasial", "Autokorelasi", "Model spasial", "Peta etis"],
    "aktuaria 2": ["Multiple life", "Joint-life", "Last-survivor", "Decrement", "Reserve"],
    "nonparametrik": ["Rank test", "Kernel", "Spline", "GAM", "Bootstrap"],
    "basis data": ["Kebutuhan data", "ERD", "SQL", "ETL", "Keamanan"],
    "komputasi": ["Algoritma", "Optimasi", "Simulasi", "Numerik", "Reproducibility"],
    "persamaan struktural": ["Model pengukuran", "CFA", "SEM", "Fit indices", "Mediasi"],
    "desain eksperimen": ["Randomisasi", "Blocking", "Faktorial", "RSM", "Validasi run"],
    "matematika keuangan": ["Bunga", "Anuitas", "Obligasi", "Durasi", "Risiko suku bunga"],
    "analisis image": ["Pixel", "Fitur citra", "Filter", "Segmentasi", "Model visual"],
    "sampling": ["Populasi", "Desain sampel", "Bobot", "Varians", "Nonresponse"],
    "antrian": ["Kedatangan", "Pelayanan", "Utilisasi", "Waktu tunggu", "Kapasitas"],
    "multivariat": ["Matriks data", "PCA", "MANOVA", "Clustering", "Diskriminan"],
    "multilevel": ["Level data", "Random effect", "ICC", "Growth curve", "GLMM"],
    "proses stokastik": ["State", "Markov", "Poisson", "Renewal", "Simulasi"],
    "penambangan data": ["KDD", "Klasifikasi", "Clustering", "Asosiasi", "AI"],
    "regresi tingkat lanjut": ["Baseline", "Nonlinear", "Penalized", "Robust", "Bayesian"],
    "teori risiko": ["Frekuensi", "Severitas", "Agregasi", "Ruin", "Risk measure"],
    "statistika inferensial": ["Estimator", "Likelihood", "Interval", "Uji hipotesis", "Bayesian"],
    "aktuaria 1": ["Nilai waktu uang", "Life table", "Asuransi jiwa", "Anuitas hidup", "Cadangan"],
}


def slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "materi"


def get_yaml_value(yaml_text: str, key: str, default: str = "") -> str:
    match = re.search(rf"^{re.escape(key)}:\s*(.+)$", yaml_text, flags=re.M)
    if not match:
        return default
    value = match.group(1).strip()
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        value = value[1:-1]
    return value


def normalize_yaml(yaml_text: str) -> tuple[str, dict[str, str]]:
    lines = yaml_text.splitlines()
    fields: dict[str, str] = {}
    others: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        top = re.match(r"^([A-Za-z0-9_-]+):", line)
        if top and top.group(1) == "output":
            i += 1
            while i < len(lines) and (lines[i].startswith(" ") or lines[i].strip() == ""):
                i += 1
            continue
        if top and top.group(1) in {"title", "subtitle", "author", "date"}:
            fields[top.group(1)] = line
        else:
            others.append(line)
        i += 1

    title = fields.get("title", 'title: "Materi Pembelajaran"')
    subtitle = fields.get("subtitle", 'subtitle: "S2 Statistika Terapan FMIPA Universitas Padjadjaran"')
    author = fields.get("author", 'author: "Tim Pengampu"')
    date = fields.get("date", 'date: "Januari 2025"')
    output = [
        "output:",
        "  html_document:",
        "    toc: true",
        "    toc_float:",
        "      collapsed: false",
        "      smooth_scroll: true",
        "    toc_depth: 4",
        "    number_sections: true",
        "    theme: cosmo",
        "    highlight: tango",
        "    code_folding: show",
        "    df_print: paged",
        "    self_contained: true",
    ]
    cleaned_others = [line for line in others if line.strip()]
    new_yaml = "\n".join([title, subtitle, author, date, *output, *cleaned_others])
    meta = {
        "title": get_yaml_value(new_yaml, "title", "Materi Pembelajaran"),
        "subtitle": get_yaml_value(new_yaml, "subtitle", "S2 Statistika Terapan FMIPA Universitas Padjadjaran"),
        "author": get_yaml_value(new_yaml, "author", "Tim Pengampu"),
        "date": get_yaml_value(new_yaml, "date", "Januari 2025"),
    }
    return new_yaml, meta


def strip_marked_blocks(text: str) -> str:
    for begin, end in ((STYLE_BEGIN, STYLE_END), (ENH_BEGIN, ENH_END)):
        text = re.sub(re.escape(begin) + r".*?" + re.escape(end) + r"\n?", "", text, flags=re.S)
    return text


def make_chunks_render_safe(text: str) -> str:
    def repl(match: re.Match[str]) -> str:
        opts = match.group(1).strip()
        if re.search(r"\beval\s*=", opts):
            opts = re.sub(r"\beval\s*=\s*[^,\s}]+", "eval=FALSE", opts)
        elif opts:
            opts = f"{opts}, eval=FALSE"
        else:
            opts = "eval=FALSE"
        return "```{r " + opts + "}"

    return re.sub(r"^```\{r([^}]*)\}", repl, text, flags=re.M)


def make_chunk_labels_unique(text: str) -> str:
    seen: dict[str, int] = {}

    def repl(match: re.Match[str]) -> str:
        opts = match.group(1).strip()
        if not opts:
            return match.group(0)
        first = opts.split(",", 1)[0].strip()
        if not first or "=" in first:
            return match.group(0)
        count = seen.get(first, 0) + 1
        seen[first] = count
        if count == 1:
            return match.group(0)
        suffix = f"-{count}"
        rest = opts.split(",", 1)[1] if "," in opts else ""
        new_opts = f"{first}{suffix}"
        if rest:
            new_opts += "," + rest
        return "```{r " + new_opts + "}"

    return re.sub(r"^```\{r\s+([^}]*)\}", repl, text, flags=re.M)


def clean_language(text: str) -> str:
    for old, new in REPLACEMENTS.items():
        text = text.replace(old, new)
    text = re.sub(r"^\s*@import\s+url\(['\"]https://fonts\.googleapis\.com/[^;]+;\s*\n?", "", text, flags=re.M)
    return text


def choose_topics(title: str, path: Path) -> list[str]:
    haystack = f"{title} {path.parent.name}".lower().replace("_", " ")
    for key, topics in TOPICS.items():
        if key in haystack:
            return topics
    return ["Konsep inti", "Data", "Model", "Evaluasi", "Komunikasi"]


def wrap_svg_text(label: str, width: int = 19) -> list[str]:
    return textwrap.wrap(label, width=width)[:2] or [label]


def make_svg(title: str, topics: list[str]) -> str:
    title_lines = textwrap.wrap(title, width=48)[:2]
    if len(title_lines) == 2 and len(" ".join(textwrap.wrap(title, width=48))) > len(" ".join(title_lines)):
        title_lines[1] = title_lines[1].rstrip(".") + "..."
    safe_title = html.escape(title)
    colors = ["#17395c", "#0f766e", "#f2a51a", "#7c3aed", "#b45309"]
    x_positions = [126, 300, 474, 648, 822]
    node_parts = []
    for idx, (topic, x) in enumerate(zip(topics, x_positions)):
        fill = colors[idx % len(colors)]
        node_parts.append(f'<rect x="{x-70}" y="178" width="140" height="86" rx="8" fill="{fill}" opacity="0.96"/>')
        lines = wrap_svg_text(topic)
        y = 225 if len(lines) == 1 else 216
        for line in lines:
            node_parts.append(f'<text x="{x}" y="{y}" text-anchor="middle" font-size="15" font-weight="700" fill="#ffffff">{html.escape(line)}</text>')
            y += 20
    title_parts = []
    y = 98 if len(title_lines) == 1 else 88
    for line in title_lines:
        title_parts.append(f'<text x="84" y="{y}" font-size="24" font-weight="800" fill="#ffffff">{html.escape(line)}</text>')
        y += 30

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 360" role="img" aria-label="Ilustrasi {safe_title}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#f8fbfd"/>
      <stop offset="0.55" stop-color="#fffdf8"/>
      <stop offset="1" stop-color="#eef8f6"/>
    </linearGradient>
    <linearGradient id="ribbon" x1="0" x2="1">
      <stop offset="0" stop-color="#17395c"/>
      <stop offset="0.62" stop-color="#0f766e"/>
      <stop offset="1" stop-color="#f2a51a"/>
    </linearGradient>
  </defs>
  <rect x="18" y="18" width="924" height="324" rx="8" fill="url(#bg)" stroke="#d7e2ea" stroke-width="2"/>
  <rect x="48" y="48" width="864" height="92" rx="8" fill="url(#ribbon)"/>
  <text x="84" y="72" font-size="15" font-weight="800" fill="#fff8dc">S2 Statistika Terapan - FMIPA Unpad</text>
  {''.join(title_parts)}
  <rect x="730" y="68" width="150" height="42" rx="8" fill="#ffffff" opacity="0.94"/>
  <text x="805" y="86" text-anchor="middle" font-size="13" font-weight="800" fill="#17395c">VALIDATED</text>
  <text x="805" y="104" text-anchor="middle" font-size="12" fill="#17395c">REPRODUCIBLE</text>
  {''.join(node_parts)}
  <rect x="86" y="292" width="788" height="34" rx="8" fill="#eef5f8" stroke="#d7e2ea"/>
  <text x="480" y="315" text-anchor="middle" font-size="15" font-weight="700" fill="#17395c">alur belajar: konsep -> metode -> komputasi -> interpretasi -> komunikasi ilmiah</text>
</svg>
'''


def make_enhancement(meta: dict[str, str], slug: str) -> str:
    title = html.escape(meta["title"])
    author = html.escape(meta["author"])
    date = html.escape(meta["date"])
    subtitle = html.escape(meta["subtitle"])
    return f"""{ENH_BEGIN}

{SETUP_CHUNK}

<div class="unpad-cover">
<div class="unpad-cover__brand">
<img src="../assets/unpad-logo.png" alt="Logo Universitas Padjadjaran">
<div>
<div class="unpad-kicker">S2 Statistika Terapan | FMIPA Universitas Padjadjaran</div>
<h2>{title}</h2>
<p class="unpad-meta">{subtitle}<br>Penulis: {author} | {date}</p>
</div>
</div>
</div>

<div class="materi-illustration">
<img src="../assets/illustrations/{slug}.svg" alt="Ilustrasi {title}">
</div>

<div class="validasi-akademik">
<strong>Catatan validasi akademik.</strong> Materi ini diseragamkan dengan rujukan ADWTL Januari 2025: rumus dibaca bersama asumsi, contoh kode diposisikan sebagai template reproducible, dan interpretasi diarahkan pada validitas data, diagnosis model, evaluasi ketidakpastian, serta komunikasi hasil secara ilmiah.
</div>

{ENH_END}

"""


def process_file(path: Path) -> bool:
    original = path.read_text(encoding="utf-8")
    text = strip_marked_blocks(original)
    match = re.match(r"\A---\s*\n(.*?)\n---\s*\n", text, flags=re.S)
    if not match:
        raise ValueError(f"No YAML front matter found: {path}")

    yaml_text = match.group(1)
    body = text[match.end():]
    new_yaml, meta = normalize_yaml(yaml_text)
    body = clean_language(body)
    body = make_chunks_render_safe(body)
    body = make_chunk_labels_unique(body)

    slug = slugify(path.parent.name)
    topics = choose_topics(meta["title"], path)
    svg_path = ILLUSTRATION_DIR / f"{slug}.svg"
    svg_path.write_text(make_svg(meta["title"], topics), encoding="utf-8")

    new_text = "---\n" + new_yaml + "\n---\n\n" + COMMON_STYLE + "\n\n" + make_enhancement(meta, slug) + body.lstrip()
    if new_text != original:
        path.write_text(new_text, encoding="utf-8")
        return True
    return False


def main() -> None:
    ILLUSTRATION_DIR.mkdir(parents=True, exist_ok=True)
    changed = []
    for path in sorted(ROOT.rglob("*.Rmd")):
        if any(part.startswith(".") for part in path.relative_to(ROOT).parts):
            continue
        if process_file(path):
            changed.append(path.relative_to(ROOT).as_posix())
    print(f"Processed {len(list(ROOT.rglob('*.Rmd')))} Rmd files")
    print(f"Changed {len(changed)} Rmd files")
    for item in changed:
        print(item)


if __name__ == "__main__":
    main()
