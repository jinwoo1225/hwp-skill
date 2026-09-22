#!/usr/bin/env bash
# ============================================
# hwp-skill · 설치 스크립트 (macOS / Linux / WSL)
# 다른 에이전트(Claude Code, Codex, Hermes 등)에서 사용 가능하도록 등록.
# ============================================
set -e

REPO="https://github.com/jinwoo1225/hwp-skill.git"
INSTALL_DIR="${HWP_SKILL_DIR:-$HOME/.local/share/hwp-skill}"
AGENTS="${HWP_AGENTS:-claude-code,codex,hermes}"  # comma-separated

echo "[hwp-skill] 설치 위치: $INSTALL_DIR"

# 1. clone (이미 있으면 update)
if [ -d "$INSTALL_DIR" ]; then
  echo "[hwp-skill] 기존 설치 발견 — 업데이트"
  git -C "$INSTALL_DIR" pull --ff-only
else
  echo "[hwp-skill] clone 중..."
  mkdir -p "$(dirname "$INSTALL_DIR")"
  git clone --depth 1 "$REPO" "$INSTALL_DIR"
fi

chmod +x "$INSTALL_DIR/md_to_hwpx.py"
chmod +x "$INSTALL_DIR/run.sh"

# 2. PATH 등록 안내
SHELL_NAME=$(basename "$SHELL")
RC_FILE="$HOME/.${SHELL_NAME}rc"
EXPORT_LINE="export PATH=\"\$HOME/.local/share/hwp-skill:\$PATH\""
if ! grep -qF "hwp-skill" "$RC_FILE" 2>/dev/null; then
  echo "" >> "$RC_FILE"
  echo "# hwp-skill" >> "$RC_FILE"
  echo "$EXPORT_LINE" >> "$RC_FILE"
  echo "[hwp-skill] PATH 등록: $RC_FILE (터미널 재시작 또는 'source $RC_FILE')"
else
  echo "[hwp-skill] PATH 이미 등록됨"
fi

# 3. 에이전트별 skill 등록
IFS=',' read -ra AGENT_LIST <<< "$AGENTS"
for agent in "${AGENT_LIST[@]}"; do
  case "$agent" in
    claude-code|claude)
      DEST="$HOME/.claude/skills/hwp-skill"
      echo "[hwp-skill] Claude Code skill 등록: $DEST"
      mkdir -p "$DEST"
      cat > "$DEST/SKILL.md" <<'SKILL'
# hwp-skill

마크다운 → 한글 HWPX 변환 도구. 다른 에이전트가 호출할 수 있도록 등록됨.

## 사용법

```
python3 md_to_hwpx.py input.md output.hwpx [--template template.hwpx]
```

## 옵션
- `--template PATH`: 사용자 한글 템플릿 사용 (스타일/이미지 유지)
- 위치: `~/.local/share/hwp-skill/md_to_hwpx.py`

## 마크다운 확장
- `**RED:텍스트**`, `**BLUE:텍스트**`, ... → 색상 매핑
- `<span style="color:red">...</span>` → 색상 매핑
- `**#FF0000:텍스트**` → 16진수 색상

## 자세한 내용
https://github.com/jinwoo1225/hwp-skill
SKILL
      ln -sf "$INSTALL_DIR/md_to_hwpx.py" "$DEST/md_to_hwpx.py"
      ln -sf "$INSTALL_DIR/run.sh" "$DEST/run.sh"
      ln -sf "$INSTALL_DIR/run.bat" "$DEST/run.bat"
      ;;

    codex)
      DEST="$HOME/.codex/skills/hwp-skill"
      echo "[hwp-skill] Codex skill 등록: $DEST"
      mkdir -p "$DEST"
      cat > "$DEST/SKILL.md" <<'SKILL'
# hwp-skill

마크다운 → 한글 HWPX 변환 도구.

## 사용법
`python3 ~/.local/share/hwp-skill/md_to_hwpx.py input.md output.hwpx`
SKILL
      ln -sf "$INSTALL_DIR/md_to_hwpx.py" "$DEST/md_to_hwpx.py"
      ;;

    hermes)
      DEST="$HOME/.hermes/skills/hwp-skill"
      echo "[hwp-skill] Hermes skill 등록: $DEST"
      mkdir -p "$DEST"
      cat > "$DEST/SKILL.md" <<'SKILL'
# hwp-skill

마크다운 → 한글 HWPX 변환 도구.

## 사용법
`python3 ~/.local/share/hwp-skill/md_to_hwpx.py input.md output.hwpx`
SKILL
      ln -sf "$INSTALL_DIR/md_to_hwpx.py" "$DEST/md_to_hwpx.py"
      ;;

    *)
      echo "[hwp-skill] 알 수 없는 에이전트: $agent (skip)"
      ;;
  esac
done

echo ""
echo "[hwp-skill] ✅ 설치 완료!"
echo "  - 사용법: md_to_hwpx.py input.md output.hwpx"
echo "  - 템플릿: --template /path/to/template.hwpx"
echo "  - 문서: https://github.com/jinwoo1225/hwp-skill"
