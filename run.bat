@echo off
REM ============================================
REM hwp-skill · Windows wrapper
REM 사용법: run.bat input.md output.hwpx [--template X]
REM ============================================

setlocal

REM python 또는 python3 시도
where python >nul 2>nul
if %errorlevel% equ 0 (
    set "PY=python"
) else (
    where python3 >nul 2>nul
    if %errorlevel% equ 0 (
        set "PY=python3"
    ) else (
        echo [ERROR] Python not found. Install from https://python.org
        exit /b 1
    )
)

REM 스크립트 경로 (현재 디렉토리 기준)
set "SCRIPT=%~dp0md_to_hwpx.py"

if not exist "%SCRIPT%" (
    echo [ERROR] md_to_hwpx.py not found in %~dp0
    exit /b 1
)

echo [hwp-skill] %PY% "%SCRIPT%" %*
%PY% "%SCRIPT%" %*
exit /b %errorlevel%
