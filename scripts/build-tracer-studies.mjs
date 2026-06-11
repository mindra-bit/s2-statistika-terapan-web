import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const rootDir = path.resolve(__dirname, "..");
const tracerDirName = "@Tracer Study";
const tracerDir = path.join(rootDir, tracerDirName);
const outputPath = path.join(rootDir, "data", "tracer_studies.json");
const chunksPath = path.join(rootDir, "data", "knowledge_chunks.json");

function normalizeText(value) {
  return String(value || "")
    .replace(/<script[\s\S]*?<\/script>/gi, " ")
    .replace(/<style[\s\S]*?<\/style>/gi, " ")
    .replace(/<[^>]*>/g, " ")
    .replace(/&nbsp;/g, " ")
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/\s+/g, " ")
    .trim();
}

function slugify(value) {
  return normalizeText(value)
    .toLowerCase()
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}

function extractTitle(html, fallback) {
  const titleMatch = html.match(/<title[^>]*>([\s\S]*?)<\/title>/i);
  const h1Match = html.match(/<h1[^>]*>([\s\S]*?)<\/h1>/i);
  return normalizeText(titleMatch?.[1] || h1Match?.[1] || fallback)
    .replace(/\s*\|\s*Magister.*$/i, "")
    .trim();
}

function extractMetric(text, pattern, fallback = "-") {
  return text.match(pattern)?.[1]?.trim() || fallback;
}

function extractSummary(text) {
  const indicatorIndex = text.toLowerCase().indexOf("indikator utama laporan ini");
  if (indicatorIndex >= 0) {
    const snippet = text.slice(indicatorIndex, indicatorIndex + 420).replace(/\s+/g, " ").trim();
    const sentences = snippet.match(/[^.]+(?:\.)/g);
    if (sentences?.length) return sentences.slice(0, 2).join(" ").trim();
    return snippet;
  }
  const idx = text.toLowerCase().indexOf("ringkasan eksekutif");
  return (idx >= 0 ? text.slice(idx, idx + 420) : text.slice(0, 420)).replace(/\s+/g, " ").trim();
}

if (!fs.existsSync(tracerDir)) {
  throw new Error(`Folder tracer study tidak ditemukan: ${tracerDir}`);
}

const reports = fs.readdirSync(tracerDir, { withFileTypes: true })
  .filter((entry) => entry.isDirectory() && /^Tracer Studi 20\d{2}$/i.test(entry.name))
  .map((entry) => {
    const year = entry.name.match(/20\d{2}/)?.[0];
    const folderPath = path.join(tracerDir, entry.name);
    const preferredFile = path.join(folderPath, `laporan_tracer_studi_${year}.html`);
    const htmlFile = fs.existsSync(preferredFile)
      ? preferredFile
      : fs.readdirSync(folderPath)
        .find((file) => file.toLowerCase().endsWith(".html"));

    if (!htmlFile) return null;

    const filePath = path.isAbsolute(htmlFile) ? htmlFile : path.join(folderPath, htmlFile);
    const html = fs.readFileSync(filePath, "utf8");
    const text = normalizeText(html);
    const title = extractTitle(html, `Tracer Studi ${year}`);
    const stat = fs.statSync(filePath);
    const relativePath = path.relative(rootDir, filePath);
    const href = relativePath.split(path.sep).map(encodeURIComponent).join("/");

    return {
      id: `tracer-studi-${year}`,
      year,
      title: `Tracer Studi ${year}`,
      reportTitle: title,
      folder: entry.name,
      file: path.basename(filePath),
      href,
      sizeKb: Math.round(stat.size / 1024),
      metrics: {
        responses: extractMetric(text, /Respons dianalisis\s+(\d+)/i),
        medianWait: extractMetric(text, /Median waktu tunggu\s+([0-9,.]+\s+bulan)/i),
        firstJobUnder3Months: extractMetric(text, /Pekerjaan pertama\s+<=\s+3 bulan\s+([0-9,.]+%)/i),
        workingBeforeGraduation: extractMetric(text, /Sudah bekerja sebelum lulus\s+([0-9,.]+%)/i)
      },
      summary: extractSummary(text),
      source: tracerDirName
    };
  })
  .filter(Boolean)
  .sort((a, b) => Number(a.year) - Number(b.year));

const manifest = {
  source: tracerDirName,
  generatedAt: new Date().toISOString(),
  total: reports.length,
  years: reports.map((report) => report.year),
  reports
};

fs.writeFileSync(outputPath, `${JSON.stringify(manifest, null, 2)}\n`);

if (fs.existsSync(chunksPath)) {
  const chunks = JSON.parse(fs.readFileSync(chunksPath, "utf8"));
  const retained = chunks.filter((chunk) => !String(chunk.id || "").startsWith("tracer-study-"));
  const tracerChunks = reports.map((report) => ({
    id: `tracer-study-${slugify(report.year)}`,
    title: report.title,
    sourceTitle: report.title,
    sourceUrl: report.href,
    text: `${report.title} tersedia sebagai laporan HTML pada folder ${report.folder}. Link: ${report.href}. Respons dianalisis: ${report.metrics.responses}. Median waktu tunggu kerja pertama: ${report.metrics.medianWait}. Pekerjaan pertama <= 3 bulan: ${report.metrics.firstJobUnder3Months}. Sudah bekerja sebelum lulus: ${report.metrics.workingBeforeGraduation}. Ringkasan: ${report.summary}`
  }));
  fs.writeFileSync(chunksPath, `${JSON.stringify([...retained, ...tracerChunks], null, 2)}\n`);
}

console.log(`Berhasil membuat katalog ${reports.length} laporan tracer study.`);
