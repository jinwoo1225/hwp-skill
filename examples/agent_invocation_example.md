# 에이전트 호출 예시

다양한 AI 에이전트 시스템에서 `hwp-skill`을 호출하는 실전 예시.

---

## 1. Claude Code (Anthropic)

### 사용자 요청

> "내 마크다운 보고서를 한글 파일로 변환해줘"

### Claude Code 액션 (자동)

```python
# Claude Code가 SKILL.md 자동 인식 → 도구로 wrapping
{
  "tool": "Bash",
  "command": "python3 ~/.local/share/hwp-skill/md_to_hwpx.py ~/Documents/report.md ~/Documents/report.hwpx"
}
```

### Claude Code 응답

> ✅ `~/Documents/report.hwpx` 생성 완료 (312 KB).
> 한컴 한글, MS Word, Google Docs 어디서나 열 수 있습니다.

---

## 2. Codex (OpenAI)

### 도구 정의 (config)

```json
{
  "tools": [{
    "type": "function",
    "function": {
      "name": "md_to_hwpx",
      "description": "마크다운을 한글 HWPX 파일로 변환합니다.",
      "parameters": {
        "type": "object",
        "properties": {
          "input_md": {"type": "string", "description": "입력 .md 파일 경로"},
          "output_hwpx": {"type": "string", "description": "출력 .hwpx 파일 경로"},
          "template_hwpx": {"type": "string", "description": "(선택) 한글 템플릿"}
        },
        "required": ["input_md", "output_hwpx"]
      }
    }
  }]
}
```

### Codex 호출

```
사용자: "/Users/jinwoo/meeting_notes.md를 한글 파일로 만들어줘"

Codex 액션:
  tool_call: md_to_hwpx(input_md="/Users/jinwoo/meeting_notes.md", output_hwpx="/Users/jinwoo/meeting_notes.hwpx")

Codex 응답:
  "완료: /Users/jinwoo/meeting_notes.hwpx 생성됨"
```

---

## 3. Hermes (MiniMax)

### Skill 등록

```bash
mkdir -p ~/.hermes/skills/hwp-skill
cp SKILL.md ~/.hermes/skills/hwp-skill/
ln -sf $(pwd)/md_to_hwpx.py ~/.hermes/skills/hwp-skill/
```

### Hermes 호출 (MCP 도구)

Hermes가 자동 인식 후 시스템 프롬프트에 추가되는 호출:

```json
{
  "name": "md_to_hwpx",
  "description": "마크다운을 한글 HWPX로 변환",
  "input_schema": {
    "type": "object",
    "properties": {
      "input_md": {"type": "string"},
      "output_hwpx": {"type": "string"},
      "template_hwpx": {"type": "string"}
    }
  }
}
```

---

## 4. Python SDK (자체 에이전트)

```python
# agent/tools.py
import subprocess
from pathlib import Path

def md_to_hwpx(
    input_md: str,
    output_hwpx: str,
    template_hwpx: str = None,
) -> dict:
    """마크다운을 한글 HWPX로 변환."""
    input_path = Path(input_md).resolve()
    output_path = Path(output_hwpx).resolve()

    if not input_path.exists():
        return {"success": False, "error": f"Input not found: {input_path}"}

    cmd = [
        "python3",
        str(Path.home() / ".local/share/hwp-skill/md_to_hwpx.py"),
        str(input_path),
        str(output_path),
    ]
    if template_hwpx:
        cmd.extend(["--template", str(Path(template_hwpx).resolve())])

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=60,
        env={"PATH": "/usr/local/bin:/usr/bin:/bin", "PYTHONIOENCODING": "utf-8"},
    )

    return {
        "success": result.returncode == 0,
        "output": str(output_path),
        "stdout": result.stdout,
        "stderr": result.stderr,
        "size_bytes": output_path.stat().st_size if output_path.exists() else None,
    }
```

### 에이전트 도구 등록

```python
# OpenAI-style function calling
tools = [{
    "type": "function",
    "function": {
        "name": "md_to_hwpx",
        "description": "Convert markdown to Korean HWPX file",
        "parameters": {
            "type": "object",
            "properties": {
                "input_md": {"type": "string", "description": "Input .md path"},
                "output_hwpx": {"type": "string", "description": "Output .hwpx path"},
                "template_hwpx": {"type": "string", "description": "Optional template"},
            },
            "required": ["input_md", "output_hwpx"],
        },
    },
    "function_callable": md_to_hwpx,
}]
```

---

## 5. Cursor / Continue / Aider

### Cursor (.cursorrules)

```
You have access to a tool `md_to_hwpx`. Use it when the user asks to convert markdown to Korean HWPX format.

Tool invocation:
{
  "name": "md_to_hwpx",
  "input": {
    "input_md": "<path>",
    "output_hwpx": "<path>",
    "template_hwpx": "<optional>"
  }
}

The tool runs: python3 md_to_hwpx.py <input_md> <output_hwpx> [--template <template_hwpx>]
```

### Aider (.aider.conf.yml)

```yaml
commands:
  - name: "convert-to-hwpx"
    description: "마크다운을 한글 HWPX로 변환"
    cmd: "python3 ~/.local/share/hwp-skill/md_to_hwpx.py $ARG1 $ARG2"
    args:
      - name: "input_md"
        description: "입력 마크다운"
      - name: "output_hwpx"
        description: "출력 HWPX"
```

---

## 호출 결과 검증

모든 에이전트 공통 — 변환 후:

```python
import zipfile
from pathlib import Path

def verify(output_hwpx: str) -> bool:
    p = Path(output_hwpx)
    if not p.exists() or p.stat().st_size < 1000:
        return False
    try:
        with zipfile.ZipFile(p) as zf:
            if zf.testzip() is not None:
                return False
            if "Contents/section0.xml" not in zf.namelist():
                return False
        return True
    except zipfile.BadZipFile:
        return False
```

검증 실패 시 사용자에게 명확한 메시지:

> "변환은 성공했지만 HWPX 파일이 손상된 것 같습니다. 템플릿 한글 파일을 확인해주세요."
