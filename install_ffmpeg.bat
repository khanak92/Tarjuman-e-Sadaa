@echo off
echo ========================================
echo FFmpeg Installation Helper for MSTUTS
echo ========================================
echo.

REM Check for admin privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo WARNING: This script requires Administrator privileges.
    echo Please right-click and select "Run as Administrator"
    echo.
    pause
    exit /b 1
)

echo Step 1: Downloading FFmpeg...
echo This will download FFmpeg from the official source.
echo.

set "FFMPEG_DIR=C:\ffmpeg"
set "DOWNLOAD_URL=https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
set "TEMP_ZIP=%TEMP%\ffmpeg.zip"

echo Downloading to: %TEMP_ZIP%
echo This may take a few minutes...
echo.

powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%DOWNLOAD_URL%' -OutFile '%TEMP_ZIP%'}"

if not exist "%TEMP_ZIP%" (
    echo ERROR: Download failed!
    echo Please download manually from: https://www.gyan.dev/ffmpeg/builds/
    pause
    exit /b 1
)

echo.
echo Step 2: Extracting FFmpeg...
if exist "%FFMPEG_DIR%" (
    echo %FFMPEG_DIR% already exists.
    set /p OVERWRITE="Overwrite? (y/n): "
    if /i not "%OVERWRITE%"=="y" (
        echo Installation cancelled.
        pause
        exit /b 1
    )
    rmdir /s /q "%FFMPEG_DIR%"
)

powershell -Command "Expand-Archive -Path '%TEMP_ZIP%' -DestinationPath '%TEMP%\ffmpeg_extract' -Force"

REM Find the extracted folder
for /d %%i in ("%TEMP%\ffmpeg_extract\*") do (
    if exist "%%i\bin\ffmpeg.exe" (
        move "%%i" "%FFMPEG_DIR%" >nul 2>&1
        goto :found
    )
)

:found
if not exist "%FFMPEG_DIR%\bin\ffmpeg.exe" (
    echo ERROR: Extraction failed or structure unexpected.
    echo Please extract manually to: %FFMPEG_DIR%
    pause
    exit /b 1
)

echo Extracted to: %FFMPEG_DIR%
echo.

echo Step 3: Adding to system PATH...
setx PATH "%PATH%;%FFMPEG_DIR%\bin" /M

if %errorLevel% equ 0 (
    echo.
    echo ========================================
    echo Installation Complete!
    echo ========================================
    echo.
    echo FFmpeg has been installed to: %FFMPEG_DIR%
    echo.
    echo IMPORTANT: Please close and reopen your terminal/command prompt
    echo for PATH changes to take effect.
    echo.
    echo Then verify installation by running:
    echo   ffmpeg -version
    echo.
) else (
    echo.
    echo WARNING: Could not add to PATH automatically.
    echo Please add manually:
    echo   %FFMPEG_DIR%\bin
    echo.
    echo Steps:
    echo 1. Press Win + X, select "System"
    echo 2. Click "Advanced system settings"
    echo 3. Click "Environment Variables"
    echo 4. Under "System variables", select "Path" and click "Edit"
    echo 5. Click "New" and add: %FFMPEG_DIR%\bin
    echo 6. Click OK on all dialogs
    echo.
)

echo Cleaning up temporary files...
del "%TEMP_ZIP%" >nul 2>&1
rmdir /s /q "%TEMP%\ffmpeg_extract" >nul 2>&1

pause

