@echo off
setlocal enabledelayedexpansion

:: Set console title and color
title Web Masjid Al Huda - Launcher
color 0A

echo ======================================================================
echo           M E N J A L A N K A N   W E B   M A S J I D
echo ======================================================================
echo.

:: 1. Periksa apakah Python terinstal
python --version >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python tidak terdeteksi di komputer ini.
    echo.
    echo Aplikasi Web-Masjid Al Huda membutuhkan Python untuk dijalankan.
    echo.
    echo Cara Menginstal Python:
    echo 1. Unduh installer Python terbaru dari:
    echo    https://www.python.org/downloads/
    echo 2. PENTING: Centang kotak "Add Python.exe to PATH" di bagian bawah
    echo    layar installer sebelum mengklik "Install Now".
    echo 3. Setelah selesai instalasi, buka kembali file ini.
    echo.
    echo Membuka halaman unduhan Python di browser Anda...
    start https://www.python.org/downloads/
    echo.
    pause
    exit /b
)

:: 2. Pindah ke direktori tempat file batch ini berada
cd /d "%~dp0"

:: 3. Periksa dan atur Virtual Environment (venv)
if not exist "venv" goto build_venv

:: Tes apakah venv valid dan bisa mengeksekusi python
venv\Scripts\python.exe -c "import sys" >nul 2>nul
if %errorlevel%==0 goto activate_venv

echo [INFO] Virtual environment lama terdeteksi tidak kompatibel.
echo        Menghapus dan membuat ulang venv baru...
echo.
rd /s /q venv

:build_venv
echo ======================================================================
echo               MENYIAPKAN APLIKASI UNTUK PERTAMA KALI
echo   Proses ini membutuhkan koneksi internet dan waktu beberapa menit
echo ======================================================================
echo.
echo [1/4] Membuat Virtual Environment baru...
python -m venv venv
if %errorlevel% neq 0 (
    echo [ERROR] Gagal membuat Virtual Environment.
    pause
    exit /b
)

echo [2/4] Mengaktifkan Virtual Environment...
call venv\Scripts\activate

echo [3/4] Menginstal library pendukung seperti Django, Pandas, dll...
python -m pip install --upgrade pip
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Gagal menginstal library. 
    echo         Pastikan komputer terhubung ke internet lalu coba lagi.
    pause
    exit /b
)

echo [4/4] Melakukan migrasi database...
python manage.py migrate

echo.
echo [SUKSES] Persiapan awal selesai!
echo ======================================================================
timeout /t 3 >nul
goto check_shortcut

:activate_venv
echo [INFO] Mengaktifkan lingkungan aplikasi...
call venv\Scripts\activate

:check_shortcut
:: 4. Cek dan buat Shortcut Desktop jika belum ada
if exist "%USERPROFILE%\Desktop\Web Masjid Al Huda.lnk" goto start_server

echo.
echo ----------------------------------------------------------------------
echo PINTASAN DESKTOP [SHORTCUT] BELUM DIBUAT
echo ----------------------------------------------------------------------
set /p "make_shortcut=Apakah Anda ingin membuat pintasan aplikasi di Desktop? [y/n]: "
if /i not "!make_shortcut!"=="y" goto start_server

echo Membuat pintasan di Desktop...

:: Membuat script VBScript sementara untuk membuat shortcut
echo Set oWS = WScript.CreateObject("WScript.Shell") > "%temp%\CreateShortcut.vbs"
echo sLinkFile = oWS.SpecialFolders("Desktop") ^& "\Web Masjid Al Huda.lnk" >> "%temp%\CreateShortcut.vbs"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%temp%\CreateShortcut.vbs"
echo oLink.TargetPath = "%~dp0Mulai_Web_Masjid.bat" >> "%temp%\CreateShortcut.vbs"
echo oLink.WorkingDirectory = "%~dp0" >> "%temp%\CreateShortcut.vbs"
echo oLink.Description = "Menjalankan Web Masjid Al Huda" >> "%temp%\CreateShortcut.vbs"
echo oLink.Save >> "%temp%\CreateShortcut.vbs"

cscript /nologo "%temp%\CreateShortcut.vbs"
del "%temp%\CreateShortcut.vbs"
echo [SUKSES] Pintasan telah berhasil dibuat di Desktop Anda!
echo.
timeout /t 2 >nul

:start_server
:: 5. Jalankan Server dan buka browser otomatis
cls
echo ======================================================================
echo           APLIKASI WEB MASJID AL HUDA BERHASIL DIJALANKAN!
echo ======================================================================
echo.
echo  * Server lokal aktif di: http://127.0.0.1:8000
echo  * Browser Anda akan terbuka otomatis dalam 3 detik...
echo.
echo ----------------------------------------------------------------------
echo PENTING:
echo JANGAN MENUTUP JENDELA INI selama menggunakan Web Masjid.
echo Untuk mematikan aplikasi, Anda cukup menutup jendela ini langsung.
echo ----------------------------------------------------------------------
echo.

:: Menjalankan pembukaan browser di latar belakang (background) setelah 3 detik
start /b cmd /c "timeout /t 3 /nobreak >nul && start http://127.0.0.1:8000"

:: Jalankan server Django
python manage.py runserver

pause
