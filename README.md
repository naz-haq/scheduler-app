# Scheduler App — Penjadwalan Kuliah Farmasi

Aplikasi lokal generator jadwal kuliah & praktikum berbasis Python + Flask.

## Fitur
- Master Data: Angkatan, Ruang (kuliah/lab), Dosen, Mata Kuliah.
- **Generate dari Data**: jadwal dari master data, cegah bentrok kelas/dosen/ruang,
  tiap MK praktikum bisa diikat ke lab tertentu.
- **Generate Manual**: parameter cepat lewat grid isian (matriks angkatan × lab).
- Aturan blok: kuliah pagi ⟺ praktikum siang (pasangan kelas berbagi blok).
- Edit manual sel jadwal + panel deteksi konflik.
- Export **Excel** & **PDF**.
- Mode desktop: jendela aplikasi native (fallback ke browser).

## Menjalankan (mode pengembangan)
```bash
pip install -r requirements.txt
python app.py
```
Buka: http://127.0.0.1:5001

## Build aplikasi desktop

PyInstaller **tidak bisa cross-compile** — build harus dijalankan di OS target.

### macOS
```bash
./build_macos.sh
```
Hasil: `dist/Jadwal Farmasi.app` (dobel-klik untuk menjalankan).

### Windows
Jalankan di mesin Windows (Python 3 + WebView2 Runtime; sudah tersedia di Windows 11):
```bat
build_windows.bat
```
Hasil: `dist\app\app.exe` (dobel-klik untuk menjalankan). Jika jendela native gagal,
aplikasi otomatis membuka lewat browser.

