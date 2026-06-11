from __future__ import annotations

import base64
import html
import math
import re
from collections import Counter
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
DATA_FILE = ROOT / "Data.xlsx"
UNPAD_LOGO = ROOT / "assets" / "logo_unpad.png"
SDG4_LOGO = ROOT / "assets" / "sdg4.png"
REPORT_YEARS = [2022, 2023, 2024, 2025]

COLS = {
    "timestamp": "Timestamp",
    "angkatan": "Angkatan",
    "name": "1. Nama Lengkap",
    "email": "Email Address",
    "education": "3. Pendidikan terakhir",
    "grad_year": "4. Tahun lulus S2/S3",
    "s3_field": "5. Jika lulus S3, mohon informasikan bidang ilmu yang ditempuh",
    "company": "1.\tNama Instansi/Perusahaan tempat berkerja",
    "division": "2.\tNama divisi/bagian/departemen tempat bekerja",
    "office": "3.\tAlamat Kantor",
    "role": "4.\tTugas dan tanggung jawab Anda di divisi/bagian/departemen tersebut?",
    "worked_before": "1.\tApakah Anda telah bekerja sebelum lulus Magister Statistika Terapan?",
    "wait_raw": "2.\tJika tidak, Berapa lama waktu tunggu Anda untuk memperoleh pekerjaan yang pertama setelah lulus Magister Statistika Terapan? (Mohon sampaikan dalam satuan bulan)",
    "workplace_type": "3.\tDimana tempat anda bekerja setelah lulus Magister Statistika Terapan?",
    "obstacle": "4.\tKendala apakah yang dihadapi dalam memperoleh pekerjaan pertama? ",
    "job_moves": "5.\tFrekuensi pindah kerja ",
    "move_reason": "6.\tJika pernah pindah kerja, apa alasan anda pindah kerja?",
    "stats_use": "7.\tPenerapan dari pengetahuan dan keterampilan Statistika dalam pekerjaan Anda saat ini? ",
    "job_satisfaction": "8.\tSecara umum, bagaimana penilaian Anda terhadap pekerjaan yang dijalani saat ini:",
    "first_income": "9.   Besarnya penghasilan per bulan saat pertama kali bekerja ",
    "current_income": "10.\tBesarnya penghasilan perbulan dari pekerjaan saat ini (apabila berbeda dari pertanyaan no. 9) :",
    "umr": "11.  Pendapatan anda perbulan saat ini bila dibandingkan dengan UMR",
    "feedback": "12.\tMasukan mengenai proses pembelajaran di Program Studi S2 Magister Statistika Terapan FMIPA Unpad untuk menghasilkan lulusan kedepan yang berkualitas: ",
}

STOPWORDS = {
    "yang",
    "dan",
    "di",
    "ke",
    "dari",
    "untuk",
    "dengan",
    "atau",
    "pada",
    "dalam",
    "agar",
    "lebih",
    "sudah",
    "sangat",
    "baik",
    "program",
    "studi",
    "statistika",
    "terapan",
    "magister",
    "unpad",
    "fmipa",
    "lulusan",
    "pembelajaran",
    "kuliah",
    "mahasiswa",
    "dosen",
    "mata",
    "ada",
    "perlu",
    "bisa",
    "karena",
    "ini",
    "itu",
    "serta",
    "dapat",
    "akan",
    "diberikan",
    "menjadi",
    "secara",
    "saat",
    "saya",
    "kami",
    "juga",
    "tidak",
    "belum",
    "mengenai",
    "proses",
    "menghasilkan",
    "kedepan",
    "berkualitas",
}


def clean_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    text = re.sub(r"\s+", " ", text)
    return text


def is_blankish(value: object) -> bool:
    text = clean_text(value).lower()
    return text in {"", "-", "--", "_", ".", "nan", "none", "null"}


def normalize_answer(value: object) -> str:
    text = clean_text(value)
    return text if text else "Tidak tersedia"


def parse_wait_months(wait_value: object, worked_before: object) -> float:
    worked = clean_text(worked_before).lower()
    raw = clean_text(wait_value).lower().replace(",", ".")

    if worked == "ya":
        return 0.0

    if is_blankish(raw):
        return np.nan

    if any(term in raw for term in ["langsung", "sudah bekerja", "tidak ada", "sudah", "sebelum lulus"]):
        return 0.0

    match = re.search(r"(\d+(?:\.\d+)?)", raw)
    if not match:
        return np.nan

    value = float(match.group(1))
    if "tahun" in raw:
        value *= 12
    return value


def wait_band(months: object) -> str:
    if pd.isna(months):
        return "Tidak diketahui"
    value = float(months)
    if value <= 0:
        return "0 bulan"
    if value <= 3:
        return ">0-3 bulan"
    if value <= 6:
        return ">3-6 bulan"
    if value <= 12:
        return ">6-12 bulan"
    return ">12 bulan"


def fmt_int(value: object) -> str:
    if pd.isna(value):
        return "-"
    return f"{int(round(float(value))):,}".replace(",", ".")


def fmt_float(value: object, digits: int = 1) -> str:
    if pd.isna(value):
        return "-"
    return f"{float(value):,.{digits}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_pct(value: object, digits: int = 1) -> str:
    if pd.isna(value):
        return "-"
    return f"{fmt_float(value, digits)}%"


def img_data_uri(path: Path) -> str:
    mime = "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def esc(value: object) -> str:
    return html.escape(clean_text(value), quote=True)


def slug_id(label: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")


def value_counts(df: pd.DataFrame, col: str, order: list[str] | None = None, top: int | None = None) -> pd.DataFrame:
    if col not in df:
        return pd.DataFrame(columns=["Kategori", "Jumlah", "Persentase"])
    series = df[col].map(normalize_answer)
    series = series[series.ne("Tidak tersedia")]
    counts = series.value_counts()
    if order:
        ordered = [(label, int(counts.get(label, 0))) for label in order if int(counts.get(label, 0)) > 0]
        remaining = [(idx, int(val)) for idx, val in counts.items() if idx not in order]
        rows = ordered + remaining
    else:
        rows = [(idx, int(val)) for idx, val in counts.items()]
    if top:
        rows = rows[:top]
    total = sum(count for _, count in rows)
    return pd.DataFrame(
        {
            "Kategori": [label for label, _ in rows],
            "Jumlah": [count for _, count in rows],
            "Persentase": [(count / total * 100) if total else 0 for _, count in rows],
        }
    )


def wait_stats(df: pd.DataFrame) -> dict[str, float]:
    wait = df["wait_months"].dropna()
    n = len(df)
    valid = len(wait)
    worked_before = (df["worked_before_clean"].str.lower() == "ya").sum()
    return {
        "n": n,
        "valid_wait": valid,
        "worked_before": worked_before,
        "worked_before_pct": worked_before / n * 100 if n else np.nan,
        "median": wait.median() if valid else np.nan,
        "mean": wait.mean() if valid else np.nan,
        "min": wait.min() if valid else np.nan,
        "max": wait.max() if valid else np.nan,
        "zero": (wait <= 0).sum(),
        "zero_pct": (wait <= 0).sum() / valid * 100 if valid else np.nan,
        "within_3": (wait <= 3).sum(),
        "within_3_pct": (wait <= 3).sum() / valid * 100 if valid else np.nan,
        "within_6": (wait <= 6).sum(),
        "within_6_pct": (wait <= 6).sum() / valid * 100 if valid else np.nan,
        "over_6": (wait > 6).sum(),
        "over_6_pct": (wait > 6).sum() / valid * 100 if valid else np.nan,
        "unknown": n - valid,
        "unknown_pct": (n - valid) / n * 100 if n else np.nan,
    }


def first_nonempty(series: pd.Series) -> str:
    for value in series:
        text = clean_text(value)
        if text and not is_blankish(text):
            return text
    return "-"


def html_table(df: pd.DataFrame, classes: str = "data-table", max_rows: int | None = None) -> str:
    if max_rows is not None:
        df = df.head(max_rows)
    rows = []
    headers = "".join(f"<th>{esc(col)}</th>" for col in df.columns)
    for _, row in df.iterrows():
        cells = []
        for col, value in row.items():
            if isinstance(value, (float, np.floating)) and ("Persentase" in col or "%" in col):
                text = fmt_pct(value)
            elif isinstance(value, (float, np.floating)):
                text = fmt_float(value)
            elif isinstance(value, (int, np.integer)):
                text = fmt_int(value)
            else:
                text = clean_text(value)
            cells.append(f"<td>{esc(text)}</td>")
        rows.append(f"<tr>{''.join(cells)}</tr>")
    return f"<div class=\"table-wrap\"><table class=\"{classes}\"><thead><tr>{headers}</tr></thead><tbody>{''.join(rows)}</tbody></table></div>"


def metric_cards(items: list[tuple[str, str, str]]) -> str:
    cards = []
    for label, value, note in items:
        cards.append(
            f"""
            <article class="metric-card">
              <span>{esc(label)}</span>
              <strong>{esc(value)}</strong>
              <small>{esc(note)}</small>
            </article>
            """
        )
    return f"<div class=\"metric-grid\">{''.join(cards)}</div>"


def horizontal_bar_chart(
    df: pd.DataFrame,
    title: str,
    subtitle: str = "",
    max_items: int = 10,
    color: str = "#245a8d",
    accent: str = "#f2b705",
) -> str:
    if df.empty:
        return empty_note("Data tidak tersedia untuk grafik ini.")

    chart_df = df.head(max_items).copy()
    max_count = max(chart_df["Jumlah"].max(), 1)
    rows = []
    for i, row in chart_df.iterrows():
        width = float(row["Jumlah"]) / max_count * 100
        pct = row.get("Persentase", 0)
        rows.append(
            f"""
            <div class="bar-row">
              <div class="bar-label" title="{esc(row['Kategori'])}">{esc(row['Kategori'])}</div>
              <div class="bar-track">
                <div class="bar-fill" style="width:{width:.2f}%; background:{color if i % 2 == 0 else accent};"></div>
              </div>
              <div class="bar-value">{fmt_int(row['Jumlah'])} <span>{fmt_pct(pct, 1)}</span></div>
            </div>
            """
        )
    return (
        f"<section class=\"chart-card\"><header><h4>{esc(title)}</h4>"
        f"<p>{esc(subtitle)}</p></header><div class=\"bar-chart\">{''.join(rows)}</div></section>"
    )


def empty_note(text: str) -> str:
    return f"<div class=\"empty-note\">{esc(text)}</div>"


def wait_distribution_chart(counts: pd.DataFrame) -> str:
    order_colors = {
        "0 bulan": "#0e7c66",
        ">0-3 bulan": "#245a8d",
        ">3-6 bulan": "#f2b705",
        ">6-12 bulan": "#d66b2a",
        ">12 bulan": "#b33a3a",
        "Tidak diketahui": "#7a8794",
    }
    counts = counts.copy()
    if counts.empty:
        return empty_note("Data waktu tunggu tidak tersedia.")
    max_count = max(counts["Jumlah"].max(), 1)
    blocks = []
    for _, row in counts.iterrows():
        height = 36 + (float(row["Jumlah"]) / max_count) * 150
        color = order_colors.get(row["Kategori"], "#245a8d")
        blocks.append(
            f"""
            <div class="hist-col">
              <div class="hist-value">{fmt_int(row['Jumlah'])}</div>
              <div class="hist-bar" style="height:{height:.0f}px;background:{color};"></div>
              <div class="hist-label">{esc(row['Kategori'])}</div>
              <div class="hist-pct">{fmt_pct(row['Persentase'])}</div>
            </div>
            """
        )
    return f"""
    <section class="chart-card hero-chart">
      <header>
        <h4>Distribusi Waktu Tunggu Pekerjaan Pertama</h4>
        <p>Kategori bulan setelah dinyatakan lulus. Alumni yang telah bekerja sebelum lulus dikategorikan 0 bulan.</p>
      </header>
      <div class="histogram">{''.join(blocks)}</div>
    </section>
    """


def year_distribution(df: pd.DataFrame) -> pd.DataFrame:
    counts = df["grad_year_num"].dropna().astype(int).value_counts().sort_index()
    total = counts.sum()
    return pd.DataFrame(
        {
            "Tahun Lulus": counts.index.astype(str),
            "Jumlah": counts.values,
            "Persentase": [count / total * 100 if total else 0 for count in counts.values],
        }
    )


def wait_by_year(df: pd.DataFrame) -> pd.DataFrame:
    grouped = []
    for year, sub in df.dropna(subset=["grad_year_num"]).groupby(df["grad_year_num"].astype(int)):
        stats = wait_stats(sub)
        grouped.append(
            {
                "Tahun Lulus": str(year),
                "Respons": int(stats["n"]),
                "Median Waktu Tunggu (bulan)": fmt_float(stats["median"]),
                "Rata-rata (bulan)": fmt_float(stats["mean"]),
                "<= 3 Bulan": fmt_pct(stats["within_3_pct"]),
                "> 6 Bulan": fmt_pct(stats["over_6_pct"]),
            }
        )
    return pd.DataFrame(grouped)


def keyword_summary(series: pd.Series, top: int = 18) -> pd.DataFrame:
    words = []
    for text in series.dropna().map(clean_text):
        if is_blankish(text):
            continue
        for token in re.findall(r"[A-Za-zÀ-ÿ0-9]+", text.lower()):
            if len(token) < 4:
                continue
            if token in STOPWORDS:
                continue
            words.append(token)
    counts = Counter(words).most_common(top)
    return pd.DataFrame({"Kata Kunci": [w for w, _ in counts], "Frekuensi": [c for _, c in counts]})


def representative_quotes(series: pd.Series, limit: int = 6) -> list[str]:
    candidates = []
    for value in series.dropna().map(clean_text):
        if is_blankish(value):
            continue
        if len(value) < 12:
            continue
        candidates.append(value)
    candidates = sorted(set(candidates), key=lambda x: (-len(x), x.lower()))
    return candidates[:limit]


def top_text_table(df: pd.DataFrame, col: str, label: str, top: int = 10) -> pd.DataFrame:
    counts = value_counts(df, col, top=top)
    counts = counts.rename(columns={"Kategori": label})
    return counts


def preprocess() -> pd.DataFrame:
    df = pd.read_excel(DATA_FILE, sheet_name="Form Responses 1")
    df["timestamp_dt"] = pd.to_datetime(df[COLS["timestamp"]], errors="coerce")
    df["grad_year_num"] = pd.to_numeric(df[COLS["grad_year"]], errors="coerce")
    df["worked_before_clean"] = df[COLS["worked_before"]].map(normalize_answer)
    df["wait_months"] = [
        parse_wait_months(wait, worked)
        for wait, worked in zip(df[COLS["wait_raw"]], df[COLS["worked_before"]], strict=False)
    ]
    df["wait_band"] = df["wait_months"].map(wait_band)
    for key, col in COLS.items():
        if col in df.columns:
            df[f"{key}_clean"] = df[col].map(normalize_answer)
    return df


def analysis_for_year(df: pd.DataFrame, target_year: int) -> dict[str, object]:
    filtered = df[df["grad_year_num"].le(target_year)].copy()
    invalid_years = int(df["grad_year_num"].isna().sum())
    stats = wait_stats(filtered)
    wait_order = ["0 bulan", ">0-3 bulan", ">3-6 bulan", ">6-12 bulan", ">12 bulan", "Tidak diketahui"]
    wait_counts = value_counts(filtered, "wait_band", order=wait_order)
    wait_counts = wait_counts.set_index("Kategori").reindex(wait_order, fill_value=0).reset_index()
    total_wait_rows = wait_counts["Jumlah"].sum()
    wait_counts["Persentase"] = wait_counts["Jumlah"] / total_wait_rows * 100 if total_wait_rows else 0

    worked_counts = value_counts(filtered, "worked_before_clean", order=["Ya", "Tidak"])
    workplace_counts = value_counts(filtered, "workplace_type_clean", top=10)
    stats_use_counts = value_counts(
        filtered,
        "stats_use_clean",
        order=["Sangat diterapkan", "Diterapkan", "Kurang diterapkan", "Tidak diterapkan sama sekali"],
    )
    satisfaction_counts = value_counts(
        filtered,
        "job_satisfaction_clean",
        order=["Sangat Memuaskan", "Memuaskan", "Cukup Memuaskan", "Kurang Memuaskan"],
    )
    umr_counts = value_counts(filtered, "umr_clean", order=["Lebih besar atau sama dengan UMR", "Kurang dari UMR"])
    move_counts = value_counts(filtered, "job_moves_clean", order=["Belum pernah", "1 kali", "2 kali", "> 2 kali"])
    first_income_order = [
        "< Rp. 1,5 juta",
        "Rp. 1,5 juta - < 2,5 juta",
        "Rp. 2,5 juta - < 3,5 juta",
        "Rp. 3,5 juta - < 4,5 juta",
        ">= 4,5 juta",
    ]
    current_income_order = ["< Rp. 3 jt", "Rp. 3 jt - < 6 jt", "Rp. 6 jt - < 9 jt", "Rp. 9 jt - < 12 jt", ">=12 jt"]
    first_income_counts = value_counts(filtered, "first_income_clean", order=first_income_order)
    current_income_counts = value_counts(filtered, "current_income_clean", order=current_income_order)
    education_counts = value_counts(filtered, "education_clean", top=8)
    year_counts = year_distribution(filtered)

    company_counts = top_text_table(filtered, "company_clean", "Instansi/Perusahaan", top=12)
    division_counts = top_text_table(filtered, "division_clean", "Divisi/Bagian", top=10)
    role_counts = keyword_summary(filtered["role_clean"], top=14)
    obstacle_counts = keyword_summary(filtered["obstacle_clean"], top=14)
    feedback_keywords = keyword_summary(filtered["feedback_clean"], top=18)
    feedback_quotes = representative_quotes(filtered["feedback_clean"], limit=6)
    obstacle_quotes = representative_quotes(filtered["obstacle_clean"], limit=5)

    return {
        "target_year": target_year,
        "df": filtered,
        "invalid_years": invalid_years,
        "stats": stats,
        "wait_counts": wait_counts,
        "worked_counts": worked_counts,
        "workplace_counts": workplace_counts,
        "stats_use_counts": stats_use_counts,
        "satisfaction_counts": satisfaction_counts,
        "umr_counts": umr_counts,
        "move_counts": move_counts,
        "first_income_counts": first_income_counts,
        "current_income_counts": current_income_counts,
        "education_counts": education_counts,
        "year_counts": year_counts,
        "wait_by_year": wait_by_year(filtered),
        "company_counts": company_counts,
        "division_counts": division_counts,
        "role_keywords": role_counts,
        "obstacle_keywords": obstacle_counts,
        "feedback_keywords": feedback_keywords,
        "feedback_quotes": feedback_quotes,
        "obstacle_quotes": obstacle_quotes,
    }


def period_label(df: pd.DataFrame) -> str:
    dates = df["timestamp_dt"].dropna()
    if dates.empty:
        return "Tidak tersedia"
    start = dates.min().strftime("%d/%m/%Y")
    end = dates.max().strftime("%d/%m/%Y")
    return f"{start} - {end}"


def sentence_wait_priority(stats: dict[str, float]) -> str:
    return (
        f"Indikator utama laporan ini adalah waktu tunggu pekerjaan pertama. "
        f"Dari {fmt_int(stats['valid_wait'])} respons valid, median waktu tunggu adalah "
        f"{fmt_float(stats['median'])} bulan dengan rata-rata {fmt_float(stats['mean'])} bulan. "
        f"Sebanyak {fmt_pct(stats['within_3_pct'])} lulusan memperoleh pekerjaan dalam waktu paling lama "
        f"3 bulan, termasuk {fmt_pct(stats['zero_pct'])} yang sudah bekerja saat lulus atau tidak memiliki waktu tunggu."
    )


def insights_list(analysis: dict[str, object]) -> str:
    stats = analysis["stats"]
    df = analysis["df"]
    top_workplace = first_nonempty(analysis["workplace_counts"]["Kategori"] if not analysis["workplace_counts"].empty else pd.Series([]))
    top_company = first_nonempty(analysis["company_counts"]["Instansi/Perusahaan"] if not analysis["company_counts"].empty else pd.Series([]))
    applied = 0
    stats_use = analysis["stats_use_counts"]
    if not stats_use.empty:
        applied = stats_use[stats_use["Kategori"].isin(["Sangat diterapkan", "Diterapkan"])]["Jumlah"].sum()
        applied_pct = applied / stats_use["Jumlah"].sum() * 100 if stats_use["Jumlah"].sum() else np.nan
    else:
        applied_pct = np.nan
    satisfied = 0
    satisfaction = analysis["satisfaction_counts"]
    if not satisfaction.empty:
        satisfied = satisfaction[satisfaction["Kategori"].isin(["Sangat Memuaskan", "Memuaskan"])]["Jumlah"].sum()
        satisfied_pct = satisfied / satisfaction["Jumlah"].sum() * 100 if satisfaction["Jumlah"].sum() else np.nan
    else:
        satisfied_pct = np.nan
    return f"""
    <ul class="insight-list">
      <li><strong>Transisi kerja cepat.</strong> Median waktu tunggu {fmt_float(stats['median'])} bulan; {fmt_pct(stats['within_3_pct'])} respons valid berada pada kategori paling lama 3 bulan.</li>
      <li><strong>Basis kerja kuat sebelum lulus.</strong> {fmt_pct(stats['worked_before_pct'])} responden telah bekerja sebelum menyelesaikan studi.</li>
      <li><strong>Sebaran institusi luas.</strong> Kategori tempat kerja terbesar adalah {esc(top_workplace)}, dengan instansi yang paling sering muncul: {esc(top_company)}.</li>
      <li><strong>Relevansi akademik tinggi.</strong> {fmt_pct(applied_pct)} responden menyatakan pengetahuan dan keterampilan statistika diterapkan atau sangat diterapkan dalam pekerjaan.</li>
      <li><strong>Kepuasan kerja positif.</strong> {fmt_pct(satisfied_pct)} responden menilai pekerjaan saat ini memuaskan atau sangat memuaskan.</li>
    </ul>
    """


def recommendation_list(analysis: dict[str, object]) -> str:
    stats = analysis["stats"]
    over_6 = stats["over_6_pct"]
    feedback_keywords = set(analysis["feedback_keywords"]["Kata Kunci"].head(12).str.lower()) if not analysis["feedback_keywords"].empty else set()
    ai_note = "ai" in feedback_keywords or "data" in feedback_keywords or "coding" in feedback_keywords
    recommendations = [
        (
            "Penguatan transisi karier",
            "Bangun mekanisme career readiness sejak semester awal: klinik CV, simulasi wawancara, portofolio analitik, dan kanal informasi lowongan yang terkurasi untuk menjaga waktu tunggu tetap singkat.",
        ),
        (
            "Kurikulum berbasis kebutuhan kerja",
            "Perkuat mata kuliah berbasis proyek nyata, pemrograman statistik, pengelolaan basis data, visualisasi, big data, dan machine learning agar kompetensi lulusan semakin langsung dipakai di institusi kerja.",
        ),
        (
            "Kemitraan pengguna lulusan",
            "Kembangkan jejaring dengan BPS, pemerintah daerah, perguruan tinggi, industri data, dan perusahaan nasional untuk magang, kuliah tamu, proyek bersama, serta rekrutmen lulusan.",
        ),
        (
            "Pelacakan outcome berkelanjutan",
            "Standarkan instrumen tracer tahunan agar waktu tunggu, gaji pertama, gaji saat ini, kesesuaian bidang, dan kompetensi dapat dibandingkan lintas tahun tanpa kehilangan konsistensi definisi.",
        ),
        (
            "Forum alumni dan mentoring",
            "Aktifkan alumni sebagai mentor karier, narasumber praktik industri, dan penghubung peluang kerja agar mahasiswa mendapat gambaran peran statistik di berbagai sektor.",
        ),
    ]
    if over_6 > 10:
        recommendations.insert(
            1,
            (
                "Intervensi untuk kelompok waktu tunggu panjang",
                "Identifikasi lulusan dengan waktu tunggu di atas 6 bulan dan lakukan pendampingan terarah melalui konseling karier, pelatihan teknis singkat, serta referral ke jejaring pengguna lulusan.",
            ),
        )
    if ai_note:
        recommendations.insert(
            2,
            (
                "Akselerasi kompetensi data modern",
                "Masukan alumni menunjukkan kebutuhan pada data modern, coding, database, dan AI; materi ini perlu ditempatkan sebagai kompetensi inti terapan, bukan sekadar pengayaan.",
            ),
        )
    items = "".join(
        f"<li><strong>{esc(title)}.</strong> {esc(body)}</li>"
        for title, body in recommendations
    )
    return f"<ol class=\"recommendations\">{items}</ol>"


def quote_block(title: str, quotes: list[str]) -> str:
    if not quotes:
        return empty_note("Tidak ada kutipan teks yang cukup informatif.")
    items = "".join(f"<blockquote>{esc(q)}</blockquote>" for q in quotes)
    return f"<section class=\"quote-card\"><h4>{esc(title)}</h4>{items}</section>"


def render_report(analysis: dict[str, object], unpad_uri: str, sdg4_uri: str) -> str:
    year = analysis["target_year"]
    df = analysis["df"]
    stats = analysis["stats"]
    prepared = date(2026, 6, 11).strftime("%d/%m/%Y")
    n = len(df)
    valid_year_min = int(df["grad_year_num"].min()) if n else year
    valid_year_max = int(df["grad_year_num"].max()) if n else year
    toc_sections = [
        "Executive Summary",
        "Pendahuluan",
        "Tujuan",
        "Metodologi dan Cakupan",
        "Hasil Utama",
        "Waktu Tunggu Kerja Pertama",
        "Profil dan Sebaran Lulusan",
        "Relevansi Kompetensi",
        "Mobilitas dan Pendapatan",
        "Kendala dan Masukan",
        "Kesimpulan",
        "Rekomendasi",
        "Lampiran",
    ]
    toc = "".join(f"<a href=\"#{slug_id(s)}\">{esc(s)}</a>" for s in toc_sections)

    metrics = metric_cards(
        [
            ("Respons dianalisis", fmt_int(n), f"Tahun lulus <= {year}"),
            ("Median waktu tunggu", f"{fmt_float(stats['median'])} bulan", "Pekerjaan pertama"),
            ("<= 3 bulan", fmt_pct(stats["within_3_pct"]), f"{fmt_int(stats['within_3'])} dari {fmt_int(stats['valid_wait'])} valid"),
            ("Sudah bekerja sebelum lulus", fmt_pct(stats["worked_before_pct"]), f"{fmt_int(stats['worked_before'])} responden"),
        ]
    )

    methodology_table = pd.DataFrame(
        [
            {"Aspek": "Sumber data", "Keterangan": "Data.xlsx, sheet Form Responses 1"},
            {"Aspek": "Unit analisis", "Keterangan": "Baris respons tracer dengan tahun lulus valid"},
            {"Aspek": "Filter laporan", "Keterangan": f"Kolom Tahun lulus S2/S3 <= {year}"},
            {"Aspek": "Tahun lulus tercakup", "Keterangan": f"{valid_year_min}-{valid_year_max}"},
            {"Aspek": "Periode respons", "Keterangan": period_label(df)},
            {"Aspek": "Tahun lulus tidak valid di sumber", "Keterangan": f"{fmt_int(analysis['invalid_years'])} baris tidak disertakan dalam filter tahunan"},
            {
                "Aspek": "Aturan waktu tunggu",
                "Keterangan": "Jawaban bulan/tahun dikonversi ke bulan; responden yang bekerja sebelum lulus dikategorikan 0 bulan.",
            },
        ]
    )

    wait_summary = pd.DataFrame(
        [
            {"Indikator": "Respons valid waktu tunggu", "Nilai": fmt_int(stats["valid_wait"])},
            {"Indikator": "Tidak diketahui", "Nilai": f"{fmt_int(stats['unknown'])} ({fmt_pct(stats['unknown_pct'])})"},
            {"Indikator": "Median", "Nilai": f"{fmt_float(stats['median'])} bulan"},
            {"Indikator": "Rata-rata", "Nilai": f"{fmt_float(stats['mean'])} bulan"},
            {"Indikator": "Minimum", "Nilai": f"{fmt_float(stats['min'])} bulan"},
            {"Indikator": "Maksimum", "Nilai": f"{fmt_float(stats['max'])} bulan"},
            {"Indikator": "0 bulan", "Nilai": f"{fmt_int(stats['zero'])} ({fmt_pct(stats['zero_pct'])})"},
            {"Indikator": "<= 6 bulan", "Nilai": f"{fmt_int(stats['within_6'])} ({fmt_pct(stats['within_6_pct'])})"},
            {"Indikator": "> 6 bulan", "Nilai": f"{fmt_int(stats['over_6'])} ({fmt_pct(stats['over_6_pct'])})"},
        ]
    )

    charts_block = f"""
      <div class="two-col">
        {wait_distribution_chart(analysis["wait_counts"])}
        {horizontal_bar_chart(analysis["worked_counts"], "Status Bekerja Sebelum Lulus", "Dasar interpretasi waktu tunggu.", 6, "#0e7c66", "#245a8d")}
      </div>
    """

    html_doc = f"""<!doctype html>
<html lang="id">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Laporan Tracer Study {year} | Magister Statistika Terapan FMIPA Unpad</title>
  <style>
    :root {{
      --ink: #17212b;
      --muted: #667485;
      --line: #dfe6ee;
      --paper: #ffffff;
      --soft: #f4f7fa;
      --blue: #245a8d;
      --blue-dark: #163c62;
      --gold: #f2b705;
      --green: #0e7c66;
      --red: #c5192d;
      --orange: #d66b2a;
      --shadow: 0 18px 45px rgba(23, 33, 43, .10);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Inter, "Segoe UI", Arial, sans-serif;
      color: var(--ink);
      background: #edf2f6;
      line-height: 1.65;
    }}
    a {{ color: var(--blue); }}
    .page {{
      max-width: 1180px;
      margin: 0 auto;
      background: var(--paper);
      min-height: 100vh;
      box-shadow: var(--shadow);
    }}
    .hero {{
      position: relative;
      padding: 42px 54px 34px;
      color: #fff;
      background:
        linear-gradient(135deg, rgba(18, 55, 88, .96), rgba(36, 90, 141, .92) 56%, rgba(14, 124, 102, .92)),
        radial-gradient(circle at 78% 18%, rgba(242,183,5,.42), transparent 24%);
      overflow: hidden;
    }}
    .hero:after {{
      content: "";
      position: absolute;
      right: -150px;
      bottom: -170px;
      width: 420px;
      height: 420px;
      border: 1px solid rgba(255,255,255,.20);
      border-radius: 50%;
    }}
    .brand-row {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 24px;
      position: relative;
      z-index: 1;
    }}
    .brand-left, .brand-right {{
      display: flex;
      align-items: center;
      gap: 16px;
    }}
    .logo-unpad {{
      width: 82px;
      height: 82px;
      object-fit: contain;
      background: rgba(255,255,255,.96);
      border-radius: 8px;
      padding: 8px;
    }}
    .logo-sdg {{
      width: 88px;
      height: 88px;
      object-fit: contain;
      border-radius: 4px;
      box-shadow: 0 10px 24px rgba(0,0,0,.18);
    }}
    .brand-text strong, .sdg-text strong {{
      display: block;
      font-size: 13px;
      letter-spacing: .08em;
      text-transform: uppercase;
    }}
    .brand-text span, .sdg-text span {{
      display: block;
      color: rgba(255,255,255,.82);
      font-size: 13px;
    }}
    .hero-main {{
      position: relative;
      z-index: 1;
      max-width: 920px;
      padding: 54px 0 36px;
    }}
    .eyebrow {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 6px 10px;
      border: 1px solid rgba(255,255,255,.32);
      color: rgba(255,255,255,.92);
      border-radius: 999px;
      font-size: 12px;
      letter-spacing: .08em;
      text-transform: uppercase;
    }}
    h1 {{
      margin: 18px 0 14px;
      font-size: clamp(34px, 5vw, 58px);
      line-height: 1.03;
      letter-spacing: 0;
    }}
    .hero-lead {{
      max-width: 780px;
      color: rgba(255,255,255,.88);
      font-size: 18px;
      margin: 0;
    }}
    .hero-meta {{
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      margin-top: 28px;
    }}
    .hero-meta span {{
      border: 1px solid rgba(255,255,255,.28);
      border-radius: 6px;
      padding: 8px 11px;
      color: rgba(255,255,255,.9);
      font-size: 13px;
      background: rgba(255,255,255,.08);
    }}
    nav.toc {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      padding: 18px 54px;
      border-bottom: 1px solid var(--line);
      background: #fff;
      position: sticky;
      top: 0;
      z-index: 3;
    }}
    nav.toc a {{
      text-decoration: none;
      color: var(--blue-dark);
      font-size: 12px;
      font-weight: 700;
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 7px 10px;
      background: #fff;
    }}
    main {{
      padding: 34px 54px 64px;
    }}
    section.report-section {{
      padding: 24px 0 10px;
      border-bottom: 1px solid var(--line);
    }}
    section.report-section:last-child {{ border-bottom: none; }}
    .section-head {{
      display: flex;
      align-items: flex-end;
      justify-content: space-between;
      gap: 18px;
      margin-bottom: 18px;
    }}
    .section-kicker {{
      color: var(--blue);
      text-transform: uppercase;
      letter-spacing: .09em;
      font-size: 12px;
      font-weight: 800;
      margin: 0 0 6px;
    }}
    h2 {{
      margin: 0;
      font-size: 28px;
      line-height: 1.2;
      letter-spacing: 0;
    }}
    h3 {{
      margin: 22px 0 12px;
      font-size: 20px;
      letter-spacing: 0;
    }}
    h4 {{
      margin: 0 0 4px;
      font-size: 16px;
      letter-spacing: 0;
    }}
    p {{ margin: 0 0 13px; }}
    .lead {{
      color: #3d4c5d;
      font-size: 17px;
    }}
    .muted {{ color: var(--muted); }}
    .metric-grid {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 14px;
      margin: 22px 0;
    }}
    .metric-card {{
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 16px;
      background: linear-gradient(180deg, #fff, #f8fafc);
    }}
    .metric-card span {{
      display: block;
      color: var(--muted);
      font-size: 12px;
      font-weight: 800;
      letter-spacing: .05em;
      text-transform: uppercase;
      min-height: 34px;
    }}
    .metric-card strong {{
      display: block;
      font-size: 28px;
      line-height: 1.1;
      margin: 8px 0 6px;
      color: var(--blue-dark);
    }}
    .metric-card small {{ color: var(--muted); }}
    .insight-list, .recommendations {{
      margin: 14px 0 0;
      padding-left: 22px;
    }}
    .insight-list li, .recommendations li {{
      margin-bottom: 10px;
    }}
    .two-col {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
      gap: 18px;
      margin: 18px 0;
    }}
    .chart-card, .quote-card {{
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 18px;
      background: #fff;
    }}
    .chart-card header {{
      margin-bottom: 14px;
    }}
    .chart-card header p {{
      color: var(--muted);
      font-size: 13px;
      margin: 0;
    }}
    .bar-chart {{
      display: grid;
      gap: 10px;
    }}
    .bar-row {{
      display: grid;
      grid-template-columns: minmax(150px, 1.1fr) minmax(160px, 2fr) 92px;
      gap: 10px;
      align-items: center;
    }}
    .bar-label {{
      color: #263747;
      font-size: 13px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}
    .bar-track {{
      height: 15px;
      background: #edf2f6;
      border-radius: 999px;
      overflow: hidden;
    }}
    .bar-fill {{
      height: 100%;
      border-radius: 999px;
    }}
    .bar-value {{
      font-size: 13px;
      font-weight: 800;
      text-align: right;
      color: var(--blue-dark);
    }}
    .bar-value span {{
      display: block;
      font-weight: 500;
      color: var(--muted);
      font-size: 11px;
    }}
    .histogram {{
      min-height: 260px;
      display: grid;
      grid-template-columns: repeat(6, minmax(0, 1fr));
      gap: 12px;
      align-items: end;
      padding-top: 10px;
    }}
    .hist-col {{
      display: grid;
      align-items: end;
      justify-items: center;
      gap: 6px;
      text-align: center;
    }}
    .hist-value {{
      font-size: 13px;
      font-weight: 800;
      color: var(--blue-dark);
    }}
    .hist-bar {{
      width: 100%;
      max-width: 52px;
      border-radius: 6px 6px 0 0;
      min-height: 20px;
    }}
    .hist-label {{
      min-height: 38px;
      font-size: 12px;
      font-weight: 700;
      color: #27394c;
    }}
    .hist-pct {{
      color: var(--muted);
      font-size: 11px;
    }}
    .table-wrap {{
      overflow-x: auto;
      margin: 14px 0 22px;
      border: 1px solid var(--line);
      border-radius: 8px;
    }}
    table {{
      border-collapse: collapse;
      width: 100%;
      min-width: 620px;
      background: #fff;
    }}
    th {{
      background: var(--blue-dark);
      color: #fff;
      text-align: left;
      font-size: 12px;
      letter-spacing: .04em;
      text-transform: uppercase;
      padding: 10px 12px;
    }}
    td {{
      border-top: 1px solid var(--line);
      padding: 10px 12px;
      vertical-align: top;
      font-size: 13px;
    }}
    tbody tr:nth-child(even) td {{ background: #f8fafc; }}
    .callout {{
      border-left: 5px solid var(--gold);
      background: #fff9e6;
      padding: 16px 18px;
      border-radius: 0 8px 8px 0;
      margin: 18px 0;
    }}
    .callout strong {{ color: #7a5600; }}
    .sdg-panel {{
      display: grid;
      grid-template-columns: 116px 1fr;
      gap: 18px;
      align-items: center;
      border: 1px solid #f0c4cb;
      background: #fff6f7;
      border-radius: 8px;
      padding: 18px;
      margin: 18px 0;
    }}
    .sdg-panel img {{
      width: 104px;
      height: 104px;
      object-fit: contain;
      border-radius: 4px;
    }}
    .quote-card blockquote {{
      margin: 12px 0;
      padding: 12px 14px;
      border-left: 4px solid var(--blue);
      background: #f6f9fc;
      color: #2b3f53;
      border-radius: 0 6px 6px 0;
      font-size: 13px;
    }}
    .empty-note {{
      border: 1px dashed var(--line);
      border-radius: 8px;
      padding: 18px;
      color: var(--muted);
      background: #fafbfc;
    }}
    .appendix-grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 18px;
    }}
    footer {{
      padding: 24px 54px 36px;
      background: #132d48;
      color: rgba(255,255,255,.78);
      font-size: 12px;
    }}
    footer strong {{ color: #fff; }}
    @media (max-width: 860px) {{
      .hero, main, nav.toc, footer {{ padding-left: 22px; padding-right: 22px; }}
      .brand-row, .section-head {{ align-items: flex-start; flex-direction: column; }}
      .metric-grid, .two-col, .appendix-grid {{ grid-template-columns: 1fr; }}
      .bar-row {{ grid-template-columns: 1fr; }}
      .bar-value {{ text-align: left; }}
      .histogram {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .sdg-panel {{ grid-template-columns: 1fr; }}
      nav.toc {{ position: static; }}
    }}
    @media print {{
      body {{ background: #fff; }}
      .page {{ box-shadow: none; max-width: none; }}
      nav.toc {{ position: static; }}
      section.report-section {{ break-inside: avoid; }}
      .chart-card, .metric-card, .quote-card, .table-wrap {{ break-inside: avoid; }}
    }}
  </style>
</head>
<body>
  <div class="page">
    <header class="hero">
      <div class="brand-row">
        <div class="brand-left">
          <img class="logo-unpad" src="{unpad_uri}" alt="Logo Universitas Padjadjaran">
          <div class="brand-text">
            <strong>Universitas Padjadjaran</strong>
            <span>Program Studi S2 Magister Statistika Terapan FMIPA</span>
          </div>
        </div>
        <div class="brand-right">
          <div class="sdg-text">
            <strong>SDG 4</strong>
            <span>Quality Education</span>
          </div>
          <img class="logo-sdg" src="{sdg4_uri}" alt="Logo SDG 4 Quality Education">
        </div>
      </div>
      <div class="hero-main">
        <span class="eyebrow">Tracer Study {year}</span>
        <h1>Laporan Tracer Study Lulusan</h1>
        <p class="hero-lead">Analisis kumulatif lulusan dengan tahun lulus S2/S3 sampai dengan {year}, berfokus pada waktu tunggu pekerjaan pertama, relevansi kompetensi statistika, mobilitas karier, dan masukan pengembangan kurikulum.</p>
        <div class="hero-meta">
          <span>Disusun: {prepared}</span>
          <span>Respons dianalisis: {fmt_int(n)}</span>
          <span>Tahun lulus: <= {year}</span>
          <span>Periode respons: {esc(period_label(df))}</span>
        </div>
      </div>
    </header>

    <nav class="toc" aria-label="Daftar isi">
      {toc}
    </nav>

    <main>
      <section class="report-section" id="executive-summary">
        <div class="section-head">
          <div>
            <p class="section-kicker">Ringkasan Eksekutif</p>
            <h2>Executive Summary</h2>
          </div>
        </div>
        {metrics}
        <p class="lead">{esc(sentence_wait_priority(stats))}</p>
        <p>Secara umum, hasil tracer menunjukkan bahwa lulusan Program Studi S2 Magister Statistika Terapan FMIPA Unpad memiliki integrasi yang kuat dengan dunia kerja. Banyak responden telah bekerja sebelum lulus, dan kelompok yang mencari pekerjaan setelah lulus cenderung memperoleh pekerjaan dalam periode yang relatif singkat. Temuan ini mendukung posisi program studi sebagai penyedia kompetensi statistik terapan yang relevan dengan kebutuhan sektor publik, pendidikan tinggi, dan industri.</p>
        {insights_list(analysis)}
      </section>

      <section class="report-section" id="pendahuluan">
        <div class="section-head">
          <div>
            <p class="section-kicker">Konteks</p>
            <h2>Pendahuluan</h2>
          </div>
        </div>
        <p>Tracer study merupakan instrumen penting untuk menilai keterhubungan antara proses pendidikan tinggi dan kebutuhan dunia kerja. Melalui pelacakan pengalaman alumni, program studi dapat memahami pola transisi lulusan, bidang kerja yang dimasuki, tingkat pemanfaatan kompetensi, kecukupan kurikulum, serta area pengembangan yang perlu diperkuat.</p>
        <p>Laporan ini disusun untuk memberikan gambaran komprehensif mengenai outcome lulusan Program Studi S2 Magister Statistika Terapan FMIPA Universitas Padjadjaran. Fokus utamanya adalah waktu tunggu mendapatkan pekerjaan pertama setelah lulus, karena indikator ini memberi sinyal langsung mengenai daya serap lulusan, kesiapan kerja, dan relevansi kompetensi yang dibangun selama studi.</p>
        <div class="sdg-panel">
          <img src="{sdg4_uri}" alt="Logo SDG 4 Quality Education">
          <div>
            <h3>Keterkaitan dengan SDG 4</h3>
            <p>Tracer study mendukung peningkatan mutu pendidikan tinggi melalui pemantauan relevansi pembelajaran, penguatan keterampilan kerja, dan perbaikan berkelanjutan berbasis bukti. Dengan demikian, laporan ini menjadi bagian dari upaya program studi untuk memperkuat kontribusi pada pendidikan berkualitas dan pembelajaran sepanjang hayat.</p>
          </div>
        </div>
      </section>

      <section class="report-section" id="tujuan">
        <div class="section-head">
          <div>
            <p class="section-kicker">Arah Analisis</p>
            <h2>Tujuan</h2>
          </div>
        </div>
        <ol class="recommendations">
          <li>Mengukur waktu tunggu lulusan dalam memperoleh pekerjaan pertama setelah dinyatakan lulus.</li>
          <li>Memetakan status kerja sebelum lulus, jenis tempat kerja, instansi, dan sebaran peran profesional alumni.</li>
          <li>Menilai relevansi pengetahuan dan keterampilan statistika terhadap pekerjaan saat ini.</li>
          <li>Menggambarkan kepuasan kerja, mobilitas kerja, pendapatan pertama, pendapatan saat ini, dan posisi pendapatan terhadap UMR.</li>
          <li>Mengidentifikasi kendala memperoleh pekerjaan pertama dan masukan alumni untuk pengembangan kurikulum serta layanan akademik.</li>
        </ol>
      </section>

      <section class="report-section" id="metodologi-dan-cakupan">
        <div class="section-head">
          <div>
            <p class="section-kicker">Data</p>
            <h2>Metodologi dan Cakupan</h2>
          </div>
        </div>
        <p>Analisis menggunakan data respons tracer pada berkas <strong>Data.xlsx</strong>. Untuk laporan tahun {year}, data disaring berdasarkan kolom <strong>Tahun lulus S2/S3 <= {year}</strong>. Baris dengan tahun lulus tidak valid atau kosong tidak masuk ke dalam cakupan laporan tahunan.</p>
        {html_table(methodology_table)}
        <div class="callout"><strong>Catatan interpretasi:</strong> karena sumber data berbentuk respons survei, jumlah yang ditampilkan dibaca sebagai jumlah respons valid pada cakupan tahun terkait. Jawaban teks bebas dibersihkan seperlunya untuk standardisasi kategori, tanpa mengubah substansi respons.</div>
      </section>

      <section class="report-section" id="hasil-utama">
        <div class="section-head">
          <div>
            <p class="section-kicker">Ikhtisar</p>
            <h2>Hasil Utama</h2>
          </div>
        </div>
        <div class="two-col">
          {horizontal_bar_chart(analysis["year_counts"].rename(columns={"Tahun Lulus": "Kategori"}), "Sebaran Tahun Lulus", f"Respons dengan tahun lulus sampai {year}.", 18, "#245a8d", "#0e7c66")}
          {horizontal_bar_chart(analysis["education_counts"], "Pendidikan Terakhir", "Profil pendidikan responden.", 8, "#0e7c66", "#f2b705")}
        </div>
        {charts_block}
      </section>

      <section class="report-section" id="waktu-tunggu-kerja-pertama">
        <div class="section-head">
          <div>
            <p class="section-kicker">Indikator Prioritas</p>
            <h2>Waktu Tunggu Kerja Pertama</h2>
          </div>
        </div>
        <p class="lead">{esc(sentence_wait_priority(stats))}</p>
        <p>Waktu tunggu dibaca dalam satuan bulan. Jawaban seperti “1 bulan”, “4 Bulan”, angka langsung, dan “2 tahun” dikonversi menjadi nilai numerik; responden yang telah bekerja sebelum lulus diperlakukan sebagai 0 bulan karena tidak mengalami jeda memasuki pekerjaan setelah kelulusan.</p>
        <div class="two-col">
          <div>
            <h3>Ringkasan Statistik Waktu Tunggu</h3>
            {html_table(wait_summary)}
          </div>
          <div>
            <h3>Distribusi Kategori Waktu Tunggu</h3>
            {html_table(analysis["wait_counts"])}
          </div>
        </div>
        <h3>Waktu Tunggu Menurut Tahun Lulus</h3>
        {html_table(analysis["wait_by_year"])}
      </section>

      <section class="report-section" id="profil-dan-sebaran-lulusan">
        <div class="section-head">
          <div>
            <p class="section-kicker">Peta Alumni</p>
            <h2>Profil dan Sebaran Lulusan</h2>
          </div>
        </div>
        <p>Responden tersebar pada berbagai institusi, terutama sektor pemerintahan/statistik, pendidikan tinggi, dan perusahaan/instansi nasional maupun lokal. Keragaman lokasi kerja ini menunjukkan bahwa kompetensi statistika terapan memiliki ruang pemanfaatan yang luas.</p>
        <div class="two-col">
          {horizontal_bar_chart(analysis["workplace_counts"], "Jenis Tempat Kerja", "Kategori tempat bekerja setelah lulus.", 10, "#245a8d", "#d66b2a")}
          {horizontal_bar_chart(analysis["company_counts"].rename(columns={"Instansi/Perusahaan": "Kategori"}), "Instansi/Perusahaan Teratas", "Nama instansi yang paling sering muncul.", 12, "#0e7c66", "#f2b705")}
        </div>
        <h3>Divisi/Bagian/Departemen Teratas</h3>
        {html_table(analysis["division_counts"])}
        <h3>Kata Kunci Tugas dan Peran Profesional</h3>
        {html_table(analysis["role_keywords"])}
      </section>

      <section class="report-section" id="relevansi-kompetensi">
        <div class="section-head">
          <div>
            <p class="section-kicker">Kualitas Pembelajaran</p>
            <h2>Relevansi Kompetensi</h2>
          </div>
        </div>
        <p>Relevansi kompetensi diukur dari penerapan pengetahuan dan keterampilan statistika dalam pekerjaan serta penilaian umum terhadap pekerjaan yang dijalani saat ini. Indikator ini memberi gambaran apakah kurikulum dan pengalaman belajar memiliki kegunaan praktis setelah lulus.</p>
        <div class="two-col">
          {horizontal_bar_chart(analysis["stats_use_counts"], "Penerapan Statistika dalam Pekerjaan", "Tingkat pemanfaatan kompetensi statistika.", 8, "#0e7c66", "#245a8d")}
          {horizontal_bar_chart(analysis["satisfaction_counts"], "Penilaian terhadap Pekerjaan Saat Ini", "Kepuasan umum responden.", 8, "#245a8d", "#f2b705")}
        </div>
      </section>

      <section class="report-section" id="mobilitas-dan-pendapatan">
        <div class="section-head">
          <div>
            <p class="section-kicker">Outcome Karier</p>
            <h2>Mobilitas dan Pendapatan</h2>
          </div>
        </div>
        <p>Bagian ini merangkum frekuensi pindah kerja dan indikator pendapatan. Interpretasi pendapatan menggunakan kategori jawaban survei, sehingga hasil dibaca sebagai distribusi kelas, bukan nilai rupiah individual.</p>
        <div class="two-col">
          {horizontal_bar_chart(analysis["move_counts"], "Frekuensi Pindah Kerja", "Mobilitas karier responden.", 8, "#245a8d", "#0e7c66")}
          {horizontal_bar_chart(analysis["umr_counts"], "Pendapatan Saat Ini Dibandingkan UMR", "Posisi pendapatan relatif terhadap UMR.", 4, "#0e7c66", "#c5192d")}
        </div>
        <div class="two-col">
          {horizontal_bar_chart(analysis["first_income_counts"], "Penghasilan Bulanan Pertama", "Kategori penghasilan saat pertama kali bekerja.", 8, "#d66b2a", "#245a8d")}
          {horizontal_bar_chart(analysis["current_income_counts"], "Penghasilan Bulanan Saat Ini", "Kategori penghasilan pekerjaan saat ini.", 8, "#245a8d", "#0e7c66")}
        </div>
      </section>

      <section class="report-section" id="kendala-dan-masukan">
        <div class="section-head">
          <div>
            <p class="section-kicker">Umpan Balik</p>
            <h2>Kendala dan Masukan</h2>
          </div>
        </div>
        <p>Jawaban teks bebas dianalisis secara ringkas melalui kata kunci dominan dan kutipan representatif. Hasilnya digunakan untuk membaca pola kebutuhan alumni, bukan untuk menilai responden individual.</p>
        <div class="two-col">
          <div>
            <h3>Kata Kunci Kendala Kerja Pertama</h3>
            {html_table(analysis["obstacle_keywords"])}
          </div>
          <div>
            <h3>Kata Kunci Masukan Pembelajaran</h3>
            {html_table(analysis["feedback_keywords"])}
          </div>
        </div>
        <div class="two-col">
          {quote_block("Kutipan Kendala yang Sering Muncul", analysis["obstacle_quotes"])}
          {quote_block("Kutipan Masukan Alumni", analysis["feedback_quotes"])}
        </div>
      </section>

      <section class="report-section" id="kesimpulan">
        <div class="section-head">
          <div>
            <p class="section-kicker">Sintesis</p>
            <h2>Kesimpulan</h2>
          </div>
        </div>
        <p>Berdasarkan {fmt_int(n)} respons pada cakupan tahun lulus sampai {year}, lulusan Magister Statistika Terapan FMIPA Unpad menunjukkan outcome ketenagakerjaan yang positif. Waktu tunggu pekerjaan pertama relatif singkat, dengan median {fmt_float(stats['median'])} bulan dan {fmt_pct(stats['within_3_pct'])} respons valid memperoleh pekerjaan dalam waktu paling lama 3 bulan.</p>
        <p>Kompetensi statistika yang diperoleh selama studi terbukti relevan dengan pekerjaan alumni, tercermin dari dominannya jawaban “diterapkan” dan “sangat diterapkan”. Selain itu, sebaran instansi yang luas menunjukkan bahwa lulusan mampu memasuki berbagai sektor kerja, terutama instansi pemerintah/statistik, pendidikan, dan organisasi nasional maupun lokal.</p>
        <p>Masukan alumni mengarah pada kebutuhan penguatan materi yang lebih aplikatif, pemanfaatan perangkat analitik modern, coding, database, big data, AI/machine learning, serta perluasan jejaring karier. Temuan ini dapat menjadi dasar pengembangan kurikulum, layanan karier, dan kemitraan pengguna lulusan.</p>
      </section>

      <section class="report-section" id="rekomendasi">
        <div class="section-head">
          <div>
            <p class="section-kicker">Tindak Lanjut</p>
            <h2>Rekomendasi</h2>
          </div>
        </div>
        {recommendation_list(analysis)}
      </section>

      <section class="report-section" id="lampiran">
        <div class="section-head">
          <div>
            <p class="section-kicker">Rincian</p>
            <h2>Lampiran</h2>
          </div>
        </div>
        <div class="appendix-grid">
          <div>
            <h3>Distribusi Tahun Lulus</h3>
            {html_table(analysis["year_counts"])}
          </div>
          <div>
            <h3>Status Bekerja Sebelum Lulus</h3>
            {html_table(analysis["worked_counts"])}
          </div>
          <div>
            <h3>Jenis Tempat Kerja</h3>
            {html_table(analysis["workplace_counts"])}
          </div>
          <div>
            <h3>Penghasilan Saat Ini</h3>
            {html_table(analysis["current_income_counts"])}
          </div>
        </div>
      </section>
    </main>

    <footer>
      <strong>Laporan Tracer Study {year}</strong><br>
      Program Studi S2 Magister Statistika Terapan FMIPA Universitas Padjadjaran. Dibangun dari Data.xlsx dengan filter tahun lulus S2/S3 <= {year}.
    </footer>
  </div>
</body>
</html>"""
    return html_doc


def write_reports() -> list[Path]:
    df = preprocess()
    unpad_uri = img_data_uri(UNPAD_LOGO)
    sdg4_uri = img_data_uri(SDG4_LOGO)
    outputs = []
    for year in REPORT_YEARS:
        analysis = analysis_for_year(df, year)
        report = render_report(analysis, unpad_uri, sdg4_uri)
        output_dir = ROOT / f"Tracer Studi {year}"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"laporan_tracer_studi_{year}.html"
        output_path.write_text(report, encoding="utf-8")
        outputs.append(output_path)
    return outputs


if __name__ == "__main__":
    paths = write_reports()
    for path in paths:
        print(path)
