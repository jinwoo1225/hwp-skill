@echo off
REM ============================================
REM hwp-skill · Windows 설치 스크립트
REM 다른 에이전트(Claude Code, Codex, Hermes 등)에서 사용 가능하도록 등록.
REM ============================================
setlocal

set "REPO=https://github.com/jinwoo1225/hwp-skill.git"
set "INSTALL_DIR=%USERPROFILE%\.local\share\hwp-skill"
set "AGENTS=claude-code,codex,hermes"

echo [hwp-skill] 설치 위치: %INSTALL_DIR%

REM 1. git clone (또는 update)
if exist "%INSTALL_DIR%" (
    echo [hwp-skill] 기존 설치 발견 - 업데이트
    git -C "%INSTALL_DIR%" pull --ff-only
) else (
    echo [hwp-skill] clone 중...
    mkdir "%INSTALL_DIR%\.." 2>nul
    git clone --depth 1 "%REPO%" "%INSTALL_DIR%"
)

if errorlevel 1 (
    echo [ERROR] git clone 실패. Git for Windows 설치 확인.
    exit /b 1
)

REM 2. PATH 등록 안내 (수동)
echo.
echo [hwp-skill] PATH 추가 안내:
echo   - 시스템 속성 ^> 환경 변수 ^> Path ^> 추가: %INSTALL_DIR%
echo   - 또는 PowerShell: $env:Path += ";%INSTALL_DIR%"
echo.

REM 3. 에이전트별 skill 등록
for %%A in ("claude-code" "codex" "hermes") do (
    set "AGENT=%%~A"
    call :register_skill "%%~A"
)

echo [hwp-skill] ✅ 설치 완료!
echo   - 사용법: md_to_hwpx.py input.md output.hwpx
echo   - 템플릿: --template C:\path\to\template.hwpx
echo   - 문서: https://github.com/jinwoo1225/hwp-skill
exit /b 0

:register_skill
set "AGENT_NAME=%~1"
if "%AGENT_NAME%"=="claude-code" goto :register_claude
if "%AGENT_NAME%"=="codex" goto :register_codex
if "%AGENT_NAME%"=="hermes" goto :register_hermes
goto :eof

:register_claude
set "DEST=%USERPROFILE%\.claude\skills\hwp-skill"
echo [hwp-skill] Claude Code skill 등록: %DEST%
mkdir "%DEST%" 2>nul
(
    echo # hwp-skill
    echo.
    echo 마크다운 → 한글 HWPX 변환 도구.
    echo.
    echo ## 사용법
    echo python "%INSTALL_DIR%\md_to_hwpx.py" input.md output.hwpx
) > "%DEST%\SKILL.md"
copy /Y "%INSTALL_DIR%\md_to_hwpx.py" "%DEST%\" >nul
copy /Y "%INSTALL_DIR%\run.bat" "%DEST%\" >nul
goto :eof

:register_codex
set "DEST=%USERPROFILE%\.codex\skills\hwp-skill"
echo [hwp-skill] Codex skill 등록: %DEST%
mkdir "%DEST%" 2>nul
(
    echo # hwp-skill
    echo.
    echo python "%INSTALL_DIR%\md_to_hwpx.py" input.md output.hwpx
) > "%DEST%\SKILL.md"
copy /Y "%INSTALL_DIR%\md_to_hwpx.py" "%DEST%\" >nul
goto :eof

:register_hermes
set "DEST=%USERPROFILE%\.hermes\skills\hwp-skill"
echo [hwp-skill] Hermes skill 등록: %DEST%
mkdir "%DEST%" 2>nul
(
    echo # hwp-skill
    echo.
    echo python "%INSTALL_DIR%\md_to_hwpx.py" input.md output.hwpx
) > "%DEST%\SKILL.md"
copy /Y "%INSTALL_DIR%\md_to_hwpx.py" "%DEST%\" >nul
goto :eof
