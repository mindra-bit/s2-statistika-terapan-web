import fs from "fs";
import path from "path";

const rootDir = process.cwd();
const materialsDir = path.join(rootDir, "@Materi Kuliah");
const enhancementEnd = "<!-- END UNPAD MATERIAL ENHANCEMENT -->";
const legacyMathJaxPattern = /<!-- dynamically load mathjax for compatibility with self-contained -->\s*<script>[\s\S]*?mathjax\.rstudio\.com\/latest\/MathJax\.js\?config=TeX-AMS-MML_HTMLorMML[\s\S]*?<\/script>\s*/gi;

const standardStyle = `<style>
html, body {
  background: linear-gradient(135deg, #f8fbfd 0%, #fffdf8 48%, #f3f6ee 100%) !important;
  color: #172033 !important;
}
body {
  font-family: "Segoe UI", Arial, sans-serif !important;
  font-size: 17px !important;
  line-height: 1.72 !important;
  margin: 0 !important;
  overflow-x: hidden !important;
}
.main-container {
  max-width: 1180px !important;
  margin-top: 18px !important;
  margin-bottom: 38px !important;
  padding: 34px 46px 54px !important;
  background: rgba(255, 253, 248, 0.98) !important;
  border: 1px solid #d7e2ea !important;
  border-radius: 8px !important;
  box-shadow: 0 18px 42px rgba(23, 57, 92, 0.12) !important;
  overflow-x: hidden !important;
}
h1, h2, h3, h4 {
  color: #17395c !important;
  font-weight: 800 !important;
  letter-spacing: 0 !important;
  line-height: 1.24 !important;
}
h1.title {
  color: #17395c !important;
  -webkit-text-fill-color: #17395c !important;
  background: none !important;
  border-bottom: 4px solid #f2a51a !important;
  padding-bottom: 14px !important;
}
h2 {
  margin-top: 46px !important;
  padding: 12px 18px !important;
  border-left: 8px solid #f2a51a !important;
  border-radius: 8px !important;
  background: linear-gradient(90deg, #eef8f6, #fff8e7) !important;
}
.unpad-cover h2 {
  color: #111827 !important;
  -webkit-text-fill-color: #111827 !important;
  background: #fffdf8 !important;
  border-left: 8px solid #f2a51a !important;
  border-bottom: 0 !important;
}
h3 {
  margin-top: 30px !important;
}
a {
  color: #0b5c86 !important;
}
img, svg {
  max-width: 100% !important;
  height: auto !important;
}
table {
  width: 100% !important;
  border-collapse: collapse !important;
  margin: 18px 0 26px !important;
  border: 1px solid #d7e2ea !important;
  border-radius: 8px !important;
}
.s2-table-scroll {
  width: 100% !important;
  max-width: 100% !important;
  overflow-x: auto !important;
  margin: 18px 0 26px !important;
  border: 1px solid #d7e2ea !important;
  border-radius: 8px !important;
}
.s2-table-scroll table {
  min-width: 680px !important;
  margin: 0 !important;
  border: 0 !important;
  border-radius: 0 !important;
}
th {
  background: #17395c !important;
  color: #ffffff !important;
  padding: 10px 12px !important;
}
td {
  background: #fffdf8 !important;
  border: 1px solid #d7e2ea !important;
  padding: 10px 12px !important;
  vertical-align: top !important;
}
.main-container p, .main-container li, td, th {
  overflow-wrap: anywhere !important;
}
pre {
  overflow: auto !important;
  padding: 16px !important;
  background: #eef5f8 !important;
  border: 1px solid #d7e2ea !important;
  border-radius: 8px !important;
  color: #111827 !important;
}
code {
  background: #eef5f8 !important;
  border-radius: 6px !important;
  color: #111827 !important;
  padding: 2px 5px !important;
}
span.math.display, .math.display, .MathJax_Display, .MathJax, mjx-container {
  display: block !important;
  max-width: 100% !important;
  overflow-x: auto !important;
  overflow-y: hidden !important;
}
blockquote {
  margin: 22px 0 !important;
  padding: 16px 20px !important;
  background: #fff8e7 !important;
  border-left: 8px solid #0f766e !important;
  border-radius: 0 8px 8px 0 !important;
}
#TOC, .tocify {
  background: #ffffff !important;
  border: 1px solid #d7e2ea !important;
  border-radius: 8px !important;
  box-shadow: 0 12px 28px rgba(23, 57, 92, 0.10) !important;
}
.tocify {
  max-height: calc(100vh - 40px) !important;
}
.tocify .active, #TOC .active {
  background: linear-gradient(90deg, #17395c, #0f766e) !important;
  color: #ffffff !important;
  border-radius: 6px !important;
}
#TOC a, .tocify a {
  color: #17395c !important;
  text-decoration: none !important;
}
#TOC a:hover, .tocify a:hover {
  color: #0f766e !important;
  text-decoration: underline !important;
}
.hero, .rps-box, .rpsbox, .info-card, .card,
.callout, .note, .casebox, .case-box, .examplebox, .exercise-box,
.learning-box, .activitybox, .activity, .practice-box, .praktik-box,
.praktikum, .tujuan, .interpretasi, .refleksi, .warning, .warningbox,
.warning-box, .tip, .idea-box, .mathbox, .formula-box, .rumus-box,
.contoh-box, .rubric-box {
  margin: 22px 0 !important;
  padding: 20px 24px !important;
  background: #fffdf8 !important;
  border: 1px solid #d7e2ea !important;
  border-left: 8px solid #0f766e !important;
  border-radius: 8px !important;
  box-shadow: 0 10px 24px rgba(23, 57, 92, 0.10) !important;
  color: #172033 !important;
}
.hero {
  background: linear-gradient(135deg, #17395c 0%, #0f766e 62%, #f2a51a 100%) !important;
  color: #ffffff !important;
  border-left: 0 !important;
}
.hero h1, .hero h2, .hero h3, .hero h4, .hero p, .hero strong {
  color: #ffffff !important;
  -webkit-text-fill-color: #ffffff !important;
}
.warning, .warningbox, .warning-box {
  border-left-color: #b45309 !important;
  background: #fff8e7 !important;
}
.rps-box, .rpsbox, .rubric-box {
  border-left-color: #f2a51a !important;
  background: linear-gradient(135deg, #fffdf8, #fff8e7) !important;
}
.mathbox, .formula-box, .rumus-box {
  border-left-color: #17395c !important;
  background: #eef5f8 !important;
}
.badge {
  display: inline-block !important;
  padding: 4px 10px !important;
  border-radius: 999px !important;
  background: #17395c !important;
  color: #ffffff !important;
  font-weight: 700 !important;
  font-size: 0.85em !important;
}
.grid-2, .grid-3 {
  display: grid !important;
  gap: 18px !important;
}
.grid-2 {
  grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
}
.grid-3 {
  grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
}
hr {
  border: 0 !important;
  height: 2px !important;
  background: linear-gradient(90deg, transparent, #d7e2ea, transparent) !important;
  margin: 34px 0 !important;
}
@media (max-width: 980px) {
  #TOC, .tocify {
    position: relative !important;
    width: auto !important;
    max-height: 360px !important;
    margin: 12px !important;
  }
  .main-container {
    margin: 12px !important;
    padding: 24px !important;
  }
  .grid-2, .grid-3 {
    grid-template-columns: 1fr !important;
  }
}
</style>`;

const standardBehavior = `<script>
window.MathJax = {
  tex: {
    inlineMath: [["\\\\(", "\\\\)"], ["$", "$"]],
    displayMath: [["\\\\[", "\\\\]"], ["$$", "$$"]],
    processEscapes: true,
    processEnvironments: true,
    tags: "ams"
  },
  options: {
    skipHtmlTags: ["script", "noscript", "style", "textarea", "pre", "code"],
    ignoreHtmlClass: "tex2jax_ignore"
  },
  chtml: {
    fontURL: "../../assets/vendor/mathjax/output/chtml/fonts/woff-v2"
  },
  startup: {
    typeset: true
  }
};

(function () {
  var script = document.createElement("script");
  script.src = "../../assets/vendor/mathjax/tex-mml-chtml.js";
  script.async = true;
  script.onerror = function () {
    var fallback = document.createElement("script");
    fallback.src = "https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js";
    fallback.async = true;
    document.head.appendChild(fallback);
  };
  document.head.appendChild(script);
})();

document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll("table").forEach(function (table) {
    if (table.parentElement && table.parentElement.classList.contains("s2-table-scroll")) return;
    var wrapper = document.createElement("div");
    wrapper.className = "s2-table-scroll";
    table.parentNode.insertBefore(wrapper, table);
    wrapper.appendChild(table);
  });
});
</script>`;

function walk(dir) {
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  return entries.flatMap((entry) => {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) return walk(fullPath);
    if (entry.isFile() && entry.name.endsWith(".html")) return [fullPath];
    return [];
  });
}

function standardizeFile(filePath) {
  const original = fs.readFileSync(filePath, "utf8");
  if (!original.includes(enhancementEnd)) {
    throw new Error(`Missing enhancement marker: ${filePath}`);
  }

  let html = original
    .replace(/<html(?:\s[^>]*)?>/i, '<html lang="id" xml:lang="id">')
    .replace(legacyMathJaxPattern, "");
  const markerPattern = new RegExp(
    `${enhancementEnd.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\s*(?:<style[\\s\\S]*?<\\/style>\\s*)?(?:<script>[\\s\\S]*?<\\/script>\\s*)?`,
    "i",
  );
  html = html.replace(markerPattern, () => `${enhancementEnd}\n${standardStyle}\n${standardBehavior}\n`);

  if (html !== original) {
    fs.writeFileSync(filePath, html);
    return true;
  }
  return false;
}

const files = walk(materialsDir).sort();
let changed = 0;

for (const file of files) {
  if (standardizeFile(file)) changed += 1;
}

console.log(`Standardized ${changed} of ${files.length} material HTML files.`);
