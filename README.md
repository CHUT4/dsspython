# SPK PIP — Versi Python (Desktop)
Sistem Penunjang Keputusan Penerima Program Indonesia Pintar — SMK Kesehatan Sekawan
Metode: Hybrid AHP-SAW. Hasil akhir berupa laporan **PDF**.

Konversi dari versi web (PHP/HTML/JS) `stateless-dss`. Fitur & alurnya sama, tetap **tanpa database** (stateless).

## Cara menjalankan
```
python main.py
```
- Butuh Python 3.8+ (Tkinter sudah ikut di instalasi Python Windows/macOS;
  di Linux: `sudo apt install python3-tk`).
- Tidak ada library tambahan yang wajib. (Opsional: `pip install pillow` supaya logo sekolah tampil di navbar.)

## Menu
| Menu | Fungsi (padanan file PHP) |
|------|---------------------------|
| Beranda | Info 5 kriteria SAW, skala, bobot, rumus (`index.php`) |
| Kalkulator AHP | Bobot kriteria via perbandingan berpasangan + uji konsistensi CR (`ahp.php`) |
| Hitung SAW | Unduh template Excel → isi → unggah → ranking → PDF (`hitung.php`, `download-template.php`) |
| Custom SPK | Input manual, kriteria & skala fleksibel, bobot bisa dari AHP (`custom.php`) |

**Output PDF:** tombol *Download Laporan PDF* / *Download PDF* di halaman hasil → pilih lokasi simpan
(nama default `SPK_PIP_YYYYMMDD_HHMMSS.pdf`) → file langsung bisa dibuka.

## Struktur
```
main.py              ← jalankan ini
lib/saw.py           ← kalkulasi SAW + kriteria default   (saw.php)
lib/xlsx_reader.py   ← pembaca .xlsx tanpa library         (xlsx.php)
lib/pdf_report.py    ← generator PDF tanpa library         (pdf.php)
ui/                  ← halaman: beranda, ahp, hitung, custom
template/Template_SPK_PIP.xlsx
assets/images/logo-smk.jpg
```
