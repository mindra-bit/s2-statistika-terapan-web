import fs from "fs";
import os from "os";
import path from "path";
import { execFileSync } from "child_process";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const rootDir = path.resolve(__dirname, "..");
const dataDir = path.join(rootDir, "data");
const outputPath = path.join(dataDir, "thesis_guides.json");
const chunksPath = path.join(dataDir, "knowledge_chunks.json");

const guides = [
  {
    id: "panduan-penulisan-tesis",
    title: "Panduan Penulisan Tesis",
    description: "Pedoman struktur naskah, format penulisan, sitasi, bagian awal, bagian utama, bagian akhir, dan kelengkapan lampiran tesis.",
    href: "dokumen/panduan-penulisan-tesis-s2-statistika-terapan.pdf",
    sourceFile: "Buku Panduan Penulisan Tesis S2 Statistika Terapan Tahun Akademik 2026:2027.pdf",
    topics: [
      "Struktur naskah tesis",
      "Format penulisan",
      "Bagian awal, utama, dan akhir",
      "Sitasi dan daftar pustaka",
      "Lampiran dan kelengkapan administrasi"
    ]
  },
  {
    id: "panduan-pelaksanaan-tesis",
    title: "Panduan Pelaksanaan Tesis SUR, SKR, dan SAM",
    description: "Pedoman alur pelaksanaan Seminar Usulan Riset, Seminar Kemajuan Riset, Sidang Akhir Magister, pembimbingan, penilaian, dan administrasi tesis.",
    href: "dokumen/panduan-pelaksanaan-tesis-sur-skr-sam-s2-statistika-terapan.pdf",
    sourceFile: "Buku Pelaksanaan Tesis SUR SKR SAM S2 Statistika Terapan Tahun Akademik 2026:2027.pdf",
    topics: [
      "Seminar Usulan Riset",
      "Seminar Kemajuan Riset",
      "Sidang Akhir Magister",
      "Pembimbingan dan pengujian",
      "Administrasi dan penilaian tesis"
    ]
  }
];

function normalizeText(value) {
  return String(value || "")
    .replace(/Tahun\s+Akademik\s+20\d{2}\s*[:/-]\s*20\d{2}/gi, "")
    .replace(/\bTA\s+20\d{2}\s*[:/-]\s*20\d{2}\b/gi, "")
    .replace(/\b20\d{2}\s*[:/-]\s*20\d{2}\b/g, "")
    .replace(/[ \t]+/g, " ")
    .replace(/\n{3,}/g, "\n\n")
    .replace(/\s+/g, " ")
    .trim();
}

function readPdfInfo(pdfPath) {
  const info = execFileSync("pdfinfo", [pdfPath], { encoding: "utf8" });
  const pages = Number(info.match(/^Pages:\s+(\d+)/m)?.[1] || 0);
  const size = fs.statSync(pdfPath).size;
  return { pages, sizeKb: Math.round(size / 1024) };
}

function pageChunks(guide, pages) {
  const chunks = [];
  pages.forEach((pageText, index) => {
    const cleaned = normalizeText(pageText);
    if (cleaned.length < 120) return;

    const words = cleaned.split(" ");
    for (let start = 0, part = 1; start < words.length; start += 170, part += 1) {
      const snippet = words.slice(start, start + 210).join(" ").trim();
      if (snippet.length < 120) continue;
      chunks.push({
        id: `thesis-guide-${guide.id}-p${String(index + 1).padStart(3, "0")}-${String(part).padStart(2, "0")}`,
        page: index + 1,
        sourceTitle: guide.title,
        sourceUrl: guide.href,
        text: `${guide.title}, halaman ${index + 1}: ${snippet}`
      });
    }
  });
  return chunks;
}

function extractGuide(guide, tempDir) {
  const pdfPath = path.join(rootDir, guide.href);
  if (!fs.existsSync(pdfPath)) {
    throw new Error(`PDF panduan tidak ditemukan: ${pdfPath}`);
  }

  const textPath = path.join(tempDir, `${guide.id}.txt`);
  execFileSync("pdftotext", ["-layout", pdfPath, textPath], { stdio: "inherit" });
  const rawText = fs.readFileSync(textPath, "utf8");
  const pages = rawText.split("\f");
  const info = readPdfInfo(pdfPath);

  return {
    metadata: {
      id: guide.id,
      title: guide.title,
      description: guide.description,
      href: guide.href,
      pages: info.pages || pages.length,
      sizeKb: info.sizeKb,
      topics: guide.topics
    },
    chunks: [
      {
        id: `thesis-guide-${guide.id}-overview`,
        sourceTitle: guide.title,
        sourceUrl: guide.href,
        text: `${guide.title}. ${guide.description} Topik utama: ${guide.topics.join(", ")}. Dokumen tersedia di ${guide.href}.`
      },
      ...pageChunks(guide, pages)
    ]
  };
}

fs.mkdirSync(dataDir, { recursive: true });

const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), "s2-thesis-guides-"));
try {
  const extracted = guides.map((guide) => extractGuide(guide, tempDir));
  const manifest = {
    source: "Panduan Tesis",
    generatedAt: new Date().toISOString(),
    total: extracted.length,
    guides: extracted.map((item) => item.metadata)
  };

  fs.writeFileSync(outputPath, `${JSON.stringify(manifest, null, 2)}\n`);

  if (fs.existsSync(chunksPath)) {
    const chunks = JSON.parse(fs.readFileSync(chunksPath, "utf8"));
    const retained = chunks.filter((chunk) => !String(chunk.id || "").startsWith("thesis-guide-"));
    const guideChunks = extracted.flatMap((item) => item.chunks);
    fs.writeFileSync(chunksPath, `${JSON.stringify([...retained, ...guideChunks], null, 2)}\n`);
    console.log(`Berhasil membuat ${manifest.total} panduan tesis dan ${guideChunks.length} chunk panduan tesis.`);
  } else {
    console.log(`Berhasil membuat ${manifest.total} panduan tesis.`);
  }
} finally {
  fs.rmSync(tempDir, { recursive: true, force: true });
}
