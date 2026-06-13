import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const rootDir = path.resolve(__dirname, "..");
const sourceDirName = "@RPS 2026";
const sourceDir = path.join(rootDir, sourceDirName);
const outputPath = path.join(rootDir, "data", "rps_docs.json");
const chunksPath = path.join(rootDir, "data", "knowledge_chunks.json");
const syllabusPath = path.join(rootDir, "data", "syllabus.json");

function encodeHref(filePath) {
  return filePath.split(path.sep).map(encodeURIComponent).join("/");
}

function normalize(value) {
  return String(value || "")
    .toLowerCase()
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9\s]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function slugify(value) {
  return normalize(value).replace(/\s+/g, "-").replace(/^-|-$/g, "");
}

function titleCase(value) {
  const preserved = new Set(["dan", "di", "ke", "dari"]);
  return String(value || "")
    .replace(/_/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .split(" ")
    .map((word, index) => {
      const lower = word.toLowerCase();
      if (index > 0 && preserved.has(lower)) return lower;
      if (/^\d+$/.test(word)) return word;
      return `${lower.charAt(0).toUpperCase()}${lower.slice(1)}`;
    })
    .join(" ");
}

function rpsTitleFromFile(fileName, fallbackFolder) {
  return titleCase(fileName.replace(/\.pdf$/i, "").replace(/^RPS\s+/i, "") || fallbackFolder);
}

function groupFromFolder(folderName) {
  return /pilihan/i.test(folderName) ? "Pilihan" : "Wajib";
}

function groupEn(group) {
  return group === "Pilihan" ? "Elective" : "Required";
}

const courseEnglishTitles = new Map([
  ["statistika inferensial", "Inferential Statistics"],
  ["komputasi statistik dan optimasi", "Statistical Computing and Optimization"],
  ["analisis multivariat tingkat lanjut", "Advanced Multivariate Analysis"],
  ["analisis regresi tingkat lanjut", "Advanced Regression Analysis"],
  ["proses stokastik tingkat lanjut", "Advanced Stochastic Processes"],
  ["analisis deret waktu tingkat lanjut", "Advanced Time Series Analysis"],
  ["tinjauan literatur sistematis", "Systematic Literature Review"],
  ["asistensi perkuliahan", "Teaching Assistance"],
  ["statistika nonparametrik dan pemodelan fleksibel", "Nonparametric Statistics and Flexible Modeling"],
  ["penambangan data dan kecerdasan buatan", "Data Mining and Artificial Intelligence"],
  ["pemodelan persamaan struktural", "Structural Equation Modeling"],
  ["analisis spasial", "Spatial Analysis"],
  ["analisis multilevel dan longitudinal", "Multilevel and Longitudinal Analysis"],
  ["model linear generalisasi", "Generalized Linear Models"],
  ["matematika keuangan", "Financial Mathematics"],
  ["desain eksperimen", "Experimental Design"],
  ["teori antrian", "Queueing Theory"],
  ["matematika aktuaria 1", "Actuarial Mathematics I"],
  ["matematika aktuaria 2", "Actuarial Mathematics II"],
  ["analisis survival", "Survival Analysis"],
  ["teori risiko", "Risk Theory"],
  ["epidemiologi", "Epidemiology"],
  ["pembelajaran mesin", "Machine Learning"],
  ["analisis citra", "Image Analysis"],
  ["analisis teks", "Text Analytics"],
  ["basis data", "Database"],
  ["sampling survey", "Sampling Survey"],
  ["seminar usulan riset", "Research Proposal Seminar"],
  ["seminar usulan riset sur", "Research Proposal Seminar"],
  ["seminar kemajuan riset", "Research Progress Seminar"],
  ["seminar kemajuan riset skr", "Research Progress Seminar"],
  ["sidang akhir magister", "Master's Thesis Defense"],
  ["sidang akhir magister tesis", "Master's Thesis Defense"]
]);

function courseTitleEn(title) {
  return courseEnglishTitles.get(normalize(title)) || title;
}

function displayCourseTitle(fileTitle, meta) {
  const normalized = normalize(fileTitle);
  if (normalized === "seminar usulan riset") return "Seminar Usulan Riset (SUR)";
  if (normalized === "seminar kemajuan riset") return "Seminar Kemajuan Riset (SKR)";
  if (normalized === "sidang akhir magister") return "Sidang Akhir Magister (Tesis)";
  return meta?.title || fileTitle;
}

function courseTitleAliases(title) {
  const aliases = {
    "analisis image": "analisis citra",
    "model persamaan struktural": "pemodelan persamaan struktural",
    "statistik inferensial": "statistika inferensial",
    "seminar usulan riset": "seminar usulan riset sur",
    "seminar kemajuan riset": "seminar kemajuan riset skr",
    "sidang akhir magister": "sidang akhir magister tesis"
  };
  const normalized = normalize(title);
  return [normalized, aliases[normalized]].filter(Boolean);
}

function findCourseMeta(title, syllabus) {
  const aliases = courseTitleAliases(title);
  return syllabus.find((entry) => aliases.includes(normalize(entry.title)))
    || syllabus.find((entry) => aliases.some((alias) => normalize(entry.title).startsWith(alias)))
    || null;
}

function walkRpsFiles(groupDir, groupName, syllabus) {
  const baseDir = path.join(sourceDir, groupDir);
  return fs.readdirSync(baseDir, { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .flatMap((folder) => {
      const courseDir = path.join(baseDir, folder.name);
      return fs.readdirSync(courseDir, { withFileTypes: true })
        .filter((file) => file.isFile() && file.name.toLowerCase().endsWith(".pdf"))
        .map((file) => {
          const fullPath = path.join(courseDir, file.name);
          const relativePath = path.relative(rootDir, fullPath);
          const stat = fs.statSync(fullPath);
          const fileTitle = rpsTitleFromFile(file.name, folder.name);
          const meta = findCourseMeta(fileTitle, syllabus) || findCourseMeta(folder.name, syllabus);
          const courseTitle = displayCourseTitle(fileTitle, meta);
          const englishTitle = courseTitleEn(courseTitle);
          const id = `rps-${slugify(groupName)}-${slugify(courseTitle)}`;

          return {
            id,
            title: `RPS ${courseTitle}`,
            titleId: `RPS ${courseTitle}`,
            titleEn: `Course Plan ${englishTitle}`,
            courseTitle,
            courseTitleEn: englishTitle,
            code: meta?.code || "",
            credits: meta?.credits || 3,
            group: groupName,
            groupEn: groupEn(groupName),
            description: `Dokumen Rencana Pembelajaran Semester untuk mata kuliah ${courseTitle} pada Kurikulum OBE 2026.`,
            descriptionId: `Dokumen Rencana Pembelajaran Semester untuk mata kuliah ${courseTitle} pada Kurikulum OBE 2026.`,
            descriptionEn: `Semester Learning Plan document for ${meta?.titleEn || courseTitle} in the 2026 OBE curriculum.`,
            file: file.name,
            folder: folder.name,
            href: encodeHref(relativePath),
            sizeKb: Math.round(stat.size / 1024),
            source: sourceDirName
          };
        });
    });
}

if (!fs.existsSync(sourceDir)) {
  throw new Error(`Folder RPS tidak ditemukan: ${sourceDir}`);
}

const syllabus = fs.existsSync(syllabusPath)
  ? JSON.parse(fs.readFileSync(syllabusPath, "utf8"))
  : [];

const groupDirs = fs.readdirSync(sourceDir, { withFileTypes: true })
  .filter((entry) => entry.isDirectory() && /matakuliah/i.test(entry.name))
  .map((entry) => ({
    dir: entry.name,
    group: groupFromFolder(entry.name)
  }))
  .sort((a, b) => (a.group === "Wajib" ? -1 : 1) - (b.group === "Wajib" ? -1 : 1));

const documents = groupDirs
  .flatMap(({ dir, group }) => walkRpsFiles(dir, group, syllabus))
  .sort((a, b) => {
    if (a.group !== b.group) return a.group === "Wajib" ? -1 : 1;
    return a.courseTitle.localeCompare(b.courseTitle, "id");
  });

const groups = ["Wajib", "Pilihan"].map((group) => ({
  id: slugify(group),
  label: `Mata Kuliah ${group}`,
  labelId: `Mata Kuliah ${group}`,
  labelEn: `${groupEn(group)} Courses`,
  total: documents.filter((doc) => doc.group === group).length
}));

const manifest = {
  source: sourceDirName,
  generatedAt: new Date().toISOString(),
  total: documents.length,
  groups,
  documents
};

fs.writeFileSync(outputPath, `${JSON.stringify(manifest, null, 2)}\n`);

if (fs.existsSync(chunksPath)) {
  const chunks = JSON.parse(fs.readFileSync(chunksPath, "utf8"));
  const retained = chunks.filter((chunk) => !String(chunk.id || "").startsWith("rps-doc-"));
  const rpsChunks = documents.map((doc) => ({
    id: `rps-doc-${doc.id}`,
    title: doc.title,
    sourceTitle: doc.title,
    sourceUrl: doc.href,
    text: `${doc.title} tersedia sebagai dokumen Rencana Pembelajaran Semester atau RPS 2026. Mata kuliah ${doc.courseTitle} termasuk kelompok ${doc.group}, ${doc.credits} SKS${doc.code ? `, kode ${doc.code}` : ""}. Link PDF RPS: ${doc.href}. ${doc.descriptionId} ${doc.descriptionEn}`
  }));
  fs.writeFileSync(chunksPath, `${JSON.stringify([...retained, ...rpsChunks], null, 2)}\n`);
}

console.log(`Berhasil membuat katalog ${documents.length} dokumen RPS 2026.`);
