Cara render file Rmd ke HTML di RStudio:

1. Buka file Materi_ADWTL_S2_Statistika_Terapan_Jan2025.Rmd di RStudio.
2. Klik tombol Knit.
3. Pilih Knit to HTML.

Atau jalankan di Console R:

install.packages(c("rmarkdown", "knitr"))
rmarkdown::render("Materi_ADWTL_S2_Statistika_Terapan_Jan2025.Rmd")

Catatan:
- File sudah menggunakan YAML html_document dengan toc_float agar daftar isi tampil di sisi kiri.
- Sebagian chunk paket tambahan diberi eval=FALSE agar dokumen tetap aman dirender meskipun paket belum terpasang.
- Nuansa desain memakai gradasi coklat dan kotak rumus coklat muda dengan tulisan gelap.
