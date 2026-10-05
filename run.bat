@echo off
setlocal enabledelayedexpansion

:: Proje dizinini al ve sonundaki ters egik cizgiyi temizle
set "PROJ_DIR=%~dp0"
if "%PROJ_DIR:~-1%"=="\" set "PROJ_DIR=%PROJ_DIR:~0,-1%"

set "IN=%~1"
if "%IN%"=="" set /p "IN=Foto klasorunun tam yolu (ornek C:\Fotolar): "
set "IN=%IN:"=%"
if "%IN:~-1%"=="\" set "IN=%IN:~0,-1%"
if not exist "%IN%\" (
  echo Klasor bulunamadi: %IN%
  pause
  exit /b 1
)
set "OUT=%IN%_sonuc"

echo.
echo Girdi : %IN%
echo Cikti : %OUT%
echo.
echo 1 = TEST    (hicbir dosyaya dokunmaz, sadece report.html uretir)
echo 2 = KOPYALA (orijinaller yerinde kalir, duzenlenmis kopya olusur)
echo 3 = TASI    (dosyalar cikti klasorune tasinir)
choice /c 123 /n /m "Seciminiz [1/2/3]: "
if errorlevel 3 (set "MODE=move") else if errorlevel 2 (set "MODE=copy") else (set "MODE=dry")

:: Docker build temiz yol ile tetikleniyor
docker build -t foto-duplicate "%PROJ_DIR%"
if errorlevel 1 (
  echo Docker build basarisiz. Docker Desktop acik mi?
  pause
  exit /b 1
)
docker run --rm -v "%IN%":/data/input -v "%OUT%":/data/output -e MODE=%MODE% foto-duplicate

echo.
echo Rapor: %OUT%\report.html
if exist "%OUT%\report.html" start "" "%OUT%\report.html"
pause
