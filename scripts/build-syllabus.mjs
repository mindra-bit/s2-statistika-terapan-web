import { execFileSync } from "child_process";
import fs from "fs";
import os from "os";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const rootDir = path.resolve(__dirname, "..");
const pdfPath = path.join(rootDir, "KURIKULUM S2 STATISTIKA 2025 - lengkap1.pdf");
const tempTextPath = path.join(os.tmpdir(), "s2-statistika-kurikulum-2025.txt");
const syllabusPath = path.join(rootDir, "data", "syllabus.json");
const chunksPath = path.join(rootDir, "data", "knowledge_chunks.json");

const courseMeta = new Map([
  [1, { credits: 3, group: "Wajib" }],
  [2, { credits: 3, group: "Wajib" }],
  [3, { credits: 3, group: "Wajib" }],
  [4, { credits: 3, group: "Wajib" }],
  [5, { credits: 3, group: "Wajib" }],
  [6, { credits: 3, group: "Wajib" }],
  [7, { credits: 6, group: "By Research" }],
  [8, { credits: 3, group: "By Research" }],
  [9, { credits: 3, group: "Pilihan" }],
  [10, { credits: 3, group: "Pilihan" }],
  [11, { credits: 3, group: "Pilihan" }],
  [12, { credits: 3, group: "Pilihan" }],
  [13, { credits: 3, group: "Pilihan" }],
  [14, { credits: 3, group: "Pilihan" }],
  [15, { credits: 3, group: "Pilihan" }],
  [16, { credits: 3, group: "Pilihan" }],
  [17, { credits: 3, group: "Pilihan" }],
  [18, { credits: 3, group: "Pilihan" }],
  [19, { credits: 3, group: "Pilihan" }],
  [20, { credits: 3, group: "Pilihan" }],
  [21, { credits: 3, group: "Pilihan" }],
  [22, { credits: 3, group: "Pilihan" }],
  [23, { credits: 3, group: "Pilihan" }],
  [24, { credits: 3, group: "Pilihan" }],
  [25, { credits: 3, group: "Pilihan" }],
  [26, { credits: 3, group: "Pilihan" }],
  [27, { credits: 3, group: "Pilihan" }],
  [28, { credits: 3, group: "By Research" }],
  [29, { credits: 3, group: "Riset" }],
  [30, { credits: 3, group: "Riset" }],
  [31, { credits: 6, group: "Riset" }],
  [32, { credits: 9, group: "Riset" }],
  [33, { credits: 9, group: "Riset" }]
]);

function normalizeText(value) {
  return String(value || "")
    .replace(/\u00a0/g, " ")
    .replace(/[\u2010-\u2015]/g, "-")
    .replace(/[\u2018\u2019]/g, "'")
    .replace(/[\u201c\u201d]/g, '"')
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

function cleanupLines(raw) {
  return raw
    .replace(/\f/g, "\n")
    .split("\n")
    .map((line) => line.replace(/\u00a0/g, " "))
    .filter((line) => !/^\s*S2 Statistika Terapan\b/.test(line))
    .filter((line) => !/^\s*\|\s*$/.test(line))
    .filter((line) => !/^\s*\d+\s*$/.test(line));
}

function parseNumberedItems(lines) {
  const items = [];
  let current = null;

  const pushCurrent = () => {
    if (!current) return;
    const subitems = current.subitems.length ? ` (${current.subitems.join("; ")})` : "";
    items.push(normalizeText(`${current.text}${subitems}`));
  };

  for (const line of lines) {
    const trimmed = normalizeText(line);
    if (!trimmed) continue;

    const numbered = trimmed.match(/^(\d+)\.\s*(.+)$/);
    const bullet = trimmed.match(/^(?:o|-)\s+(.+)$/);

    if (numbered) {
      pushCurrent();
      current = { text: numbered[2], subitems: [] };
    } else if (bullet && current) {
      current.subitems.push(bullet[1]);
    } else if (current) {
      current.text = normalizeText(`${current.text} ${trimmed}`);
    } else {
      current = { text: trimmed, subitems: [] };
    }
  }

  pushCurrent();
  return items;
}

function findSection(text, startMarker, endMarker) {
  const start = text.indexOf(startMarker);
  if (start < 0) throw new Error(`Marker awal tidak ditemukan: ${startMarker}`);
  const end = text.indexOf(endMarker, start);
  if (end < 0) throw new Error(`Marker akhir tidak ditemukan: ${endMarker}`);
  return text.slice(start + startMarker.length, end);
}

function parseSyllabus(text) {
  const section = findSection(text, "2.5 Silabus Matakuliah", "2.6 Modul Handbook");
  const blocks = section
    .replace(/\f/g, "\n")
    .split(/(?=^\s*\d+\.\s+140720-)/m)
    .filter((block) => /^\s*\d+\.\s+140720-/m.test(block));

  return blocks.map((block) => {
    const lines = cleanupLines(block);
    const header = lines.find((line) => /^\s*\d+\.\s+140720-/.test(line));
    const headerMatch = header?.match(/^\s*(\d+)\.\s+(140720-[A-Z0-9]+)\s*(?:-| )\s*(.+)$/i);
    if (!headerMatch) {
      throw new Error(`Header silabus tidak dapat dibaca: ${header || block.slice(0, 80)}`);
    }

    const order = Number(headerMatch[1]);
    const code = headerMatch[2].trim();
    const title = normalizeText(headerMatch[3]);
    const bodyLines = lines.slice(lines.indexOf(header) + 1);
    const topicsIndex = bodyLines.findIndex((line) => /^Bahan Kajian\s*$/i.test(line.trim()));
    const referencesIndex = bodyLines.findIndex((line) => /^Referensi\s*$/i.test(line.trim()));
    const descriptionLines = bodyLines.slice(0, topicsIndex >= 0 ? topicsIndex : referencesIndex);
    const topicLines = topicsIndex >= 0
      ? bodyLines.slice(topicsIndex + 1, referencesIndex >= 0 ? referencesIndex : undefined)
      : [];
    const referenceLines = referencesIndex >= 0 ? bodyLines.slice(referencesIndex + 1) : [];
    const meta = courseMeta.get(order) || { credits: null, group: "Lainnya" };

    return {
      id: `${code}-${slugify(title)}`,
      order,
      code,
      title,
      credits: meta.credits,
      group: meta.group,
      description: normalizeText(descriptionLines.join(" ")),
      topics: parseNumberedItems(topicLines),
      references: parseNumberedItems(referenceLines),
      source: "KURIKULUM S2 STATISTIKA 2025 - lengkap1.pdf",
      section: "2.5 Silabus Matakuliah"
    };
  });
}

function buildChunk(entry) {
  const topics = entry.topics.map((topic, index) => `${index + 1}. ${topic}`).join(" ");
  const references = entry.references.map((reference, index) => `${index + 1}. ${reference}`).join(" ");
  return {
    id: `syllabus-${String(entry.order).padStart(2, "0")}-${slugify(entry.title)}`,
    sourceTitle: `Silabus ${entry.title} (Kurikulum 2025, Bagian 2.5)`,
    text: normalizeText([
      `Silabus mata kuliah ${entry.title}.`,
      `Kode mata kuliah ${entry.code}.`,
      entry.credits ? `${entry.credits} SKS.` : "",
      `Kelompok ${entry.group}.`,
      `Deskripsi: ${entry.description}`,
      entry.topics.length ? `Bahan Kajian: ${topics}` : "",
      entry.references.length ? `Referensi: ${references}` : ""
    ].join(" "))
  };
}

if (!fs.existsSync(pdfPath)) {
  throw new Error(`PDF kurikulum tidak ditemukan: ${pdfPath}`);
}

execFileSync("pdftotext", ["-layout", pdfPath, tempTextPath], { stdio: "inherit" });
const text = fs.readFileSync(tempTextPath, "utf8");
const syllabus = parseSyllabus(text);
if (syllabus.length !== 33) {
  throw new Error(`Jumlah silabus terdeteksi ${syllabus.length}, seharusnya 33.`);
}

fs.writeFileSync(syllabusPath, `${JSON.stringify(syllabus, null, 2)}\n`);

const existingChunks = JSON.parse(fs.readFileSync(chunksPath, "utf8"));
const retainedChunks = existingChunks.filter((chunk) => !String(chunk.id || "").startsWith("syllabus-"));
const syllabusChunks = syllabus.map(buildChunk);
fs.writeFileSync(chunksPath, `${JSON.stringify([...retainedChunks, ...syllabusChunks], null, 2)}\n`);

console.log(`Berhasil membuat ${syllabus.length} entri silabus dan ${syllabusChunks.length} chunk knowledge base.`);
