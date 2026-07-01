#!/usr/bin/env bash
# ============================================================
#  Build aplikasi desktop macOS (Jadwal Farmasi)
#  Menghasilkan: dist/Jadwal Farmasi.app
# ============================================================
set -e
cd "$(dirname "$0")"

echo "[1/3] Menyiapkan dependency..."
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

echo
echo "[2/3] Membangun aplikasi (onedir + .app bundle)..."
python3 -m PyInstaller --noconfirm --clean app.spec

echo
echo "[3/3] Selesai."
echo "Hasil: dist/Jadwal Farmasi.app  (dobel-klik untuk menjalankan)"
