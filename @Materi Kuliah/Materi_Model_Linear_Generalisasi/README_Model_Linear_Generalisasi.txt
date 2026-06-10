# Materi Pembelajaran Model Linear Generalisasi

File ini berisi bahan ajar R Markdown untuk mata kuliah Model Linear Generalisasi, S2 Statistika Terapan FMIPA Universitas Padjadjaran.

## Isi paket

- `Model_Linear_Generalisasi_Materi.Rmd`: file utama R Markdown dengan output HTML, TOC kiri, tema coklat degradasi, rumus, contoh kasus, kode R, latihan, dan sitasi.
- `references_glm.bib`: daftar pustaka BibTeX untuk sitasi otomatis.
- `Model_Linear_Generalisasi_Materi.html`: preview HTML yang dibuat dengan Pandoc.

## Cara render di R

```r
install.packages(c("rmarkdown", "knitr"))
rmarkdown::render("Model_Linear_Generalisasi_Materi.Rmd")
```

Catatan: beberapa contoh kode lanjutan menggunakan paket tambahan seperti MASS, nnet, ordinal, pscl, ggplot2, dplyr, dan broom.

Perkiraan jumlah kata materi naratif (tidak termasuk kode): 48850 kata.
