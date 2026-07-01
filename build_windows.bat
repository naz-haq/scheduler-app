@echo off
REM ============================================================
REM  Build aplikasi desktop Windows (Jadwal Farmasi)
REM  JALANKAN DI WINDOWS -- PyInstaller tidak bisa cross-compile
REM  dari macOS/Linux, jadi .exe harus dibuat di mesin Windows.
REM ============================================================
setlocal

echo [1/3] Menyiapkan dependency...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 goto :error

echo.
echo [2/3] Membangun aplikasi (onedir)...
python -m PyInstaller --noconfirm --clean app.spec
if errorlevel 1 goto :error

echo.
echo [3/3] Selesai.
echo Hasil: dist\app\app.exe  (dobel-klik untuk menjalankan)
echo.
pause
exit /b 0

:error
echo.
echo GAGAL build. Periksa pesan error di atas.
pause
exit /b 1
