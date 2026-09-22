# AGENTS.md — 다른 AI 에이전트용 통합 가이드

`hwp-skill`은 다양한 AI 에이전트 시스템에서 호출할 수 있도록 설계되었습니다. 이 문서는 각 에이전트가 자체적으로 skill을 인식하고 호출하는 방법을 안내합니다.

---

## 지원 에이전트

| 에이전트 | 자동 인식 | 수동 등록 위치 | 비고 |
|---|---|---|---|
| **Claude Code** | ✅ (SKILL.md 자동) | `~/.claude/skills/hwp-skill/` | Anthropic 공식 |
| **Codex** | ✅ (AGENTS.md 자동) | `~/.codex/skills/hwp-skill/` | OpenAI |
| **Hermes** | ✅ (skill 디렉토리) | `~/.hermes/skills/hwp-skill/` | MiniMax |
| **Cursor** | ⚠️ 수동 | `~/.cursor/rules/` | |
| **Continue** | ⚠️ 수동 | `~/.continue/config.json` | |
| **Aider** | ⚠️ 수동 | `.aider.conf.yml` | |
| **Custom agent** | ✅ (호출 API) | 자체 시스템에 통합 | |

---

## 빠른 호출 (모든 에이전트 공통)

```bash
python3 md_to_hwpx.py input.md output.hwpx
```

표준 라이브러리만 사용 — pip install 불요.

---

## 에이전트별 통합 패턴

### 1. Claude Code (Anthropic)

**자동**: repo의 `SKILL.md`가 Claude Code가 자동으로 인식.

```
사용자: "내 보고서를 한글로 변환해줘"
Claude Code: [SKILL.md 자동 로드] → md_to_hwpx.py 호출
```

**수동 등록** (skill 디렉토리에 복사):

```bash
mkdir -p ~/.claude/skills/hwp-skill
cp SKILL.md ~/.claude/skills/hwp-skill/
ln -sf $(pwd)/md_to_hwpx.py ~/.claude/skills/hwp-skill/
```

**호출 프롬프트 예시**:

```
사용자 → Claude Code:
  "/Users/jinwoo/report.md 파일을 한글 HWPX로 변환해줘"

Claude Code 액션:
  1. SKILL.md 로드
  2. python3 md_to_hwpx.py /Users/jinwoo/report.md /tmp/report.hwpx
  3. "report.hwpx를 /tmp에 생성했습니다. 한컴 한글에서 확인하세요."
```

### 2. Codex (OpenAI)

**자동**: repo의 `AGENTS.md` 또는 `AGENT.md` 파일 자동 인식 (Codex 0.x+).

```bash
# 등록
mkdir -p ~/.codex/skills/hwp-skill
cp AGENTS.md ~/.codex/skills/hwp-skill/
ln -sf $(pwd)/md_to_hwpx.py ~/.codex/skills/hwp-skill/
```

**호출 도구 정의** (Codex 시스템 프롬프트에 포함):

```json
{
  "type": "function",
  "function": {
    "name": "md_to_hwpx",
    "description": "마크다운을 한글 HWPX 파일로 변환",
    "parameters": {
      "type": "object",
      "properties": {
        "input_md": {"type": "string"},
        "output_hwpx": {"type": "string"},
        "template_hwpx": {"type": "string"}
      },
      "required": ["input_md", "output_hwpx"]
    }
  }
}
```

### 3. Hermes (MiniMax)

**수동 등록** (`~/.hermes/skills/hwp-skill/`):

```bash
mkdir -p ~/.hermes/skills/hwp-skill
cp SKILL.md ~/.hermes/skills/hwp-skill/
ln -sf $(pwd)/md_to_hwpx.py ~/.hermes/skills/hwp-skill/
```

Hermes 시스템이 자동으로 skill을 인식하고 `md_to_hwpx.py` 호출.

### 4. Cursor / Continue / Aider

`.cursor/rules/`, `~/.continue/config.json`, `.aider.conf.yml`에 도구 정의 추가:

```yaml
# Aider 예시
commands:
  - name: "convert_md_to_hwpx"
    description: "마크다운을 한글 HWPX로 변환"
    cmd: "python3 md_to_hwpx.py $input_md $output_hwpx"
```

### 5. Custom AI Agent (범용)

어떤 에이전트 시스템에서든:

```python
import subprocess

def convert_md_to_hwpx(input_md: str, output_hwpx: str, template: str = None) -> dict:
    """md → HWPX 변환."""
    cmd = ["python3", "md_to_hwpx.py", input_md, output_hwpx]
    if template:
        cmd.extend(["--template", template])
    result = subprocess.run(cmd, capture_output=True, text=True)
    return {
        "success": result.returncode == 0,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "output": output_hwpx,
    }

# 에이전트 도구로 wrapping
agent.register_tool(
    name="convert_md_to_hwpx",
    func=convert_md_to_hwpx,
    description="마크다운을 한글 HWPX 파일로 변환"
)
```

---

## 에이전트별 호출 시 주의사항

### 1. **경로 처리**

에이전트 시스템마다 cwd가 다를 수 있음. 항상 **절대 경로** 사용:

```python
# 좋은 예
subprocess.run(["python3", "/Users/jinwoo/.local/share/hwp-skill/md_to_hwpx.py",
                "/abs/path/to/input.md", "/abs/path/to/output.hwpx"])

# 나쁜 예 (cwd 의존)
subprocess.run(["python3", "md_to_hwpx.py", "input.md", "output.hwpx"])
```

### 2. **인코딩**

Windows 에이전트는 CP949 이슈 가능. 변환 전 환경변수 설정:

```python
import os
env = os.environ.copy()
env["PYTHONIOENCODING"] = "utf-8"
subprocess.run(cmd, env=env, ...)
```

### 3. **출력 검증**

변환 후 무결성 확인:

```python
import zipfile

def verify_hwpx(path):
    with zipfile.ZipFile(path, 'r') as zf:
        bad = zf.testzip()
        if bad:
            return False, f"corrupt: {bad}"
        if "Contents/section0.xml" not in zf.namelist():
            return False, "section0.xml missing"
    return True, "OK"
```

### 4. **에러 핸들링**

```python
result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
if result.returncode != 0:
    # stderr 파싱하여 사용자에게 친절한 메시지
    if "템플릿" in result.stderr:
        return {"error": "HWPX 템플릿이 없습니다. --template 옵션으로 한글 문서를 지정하세요."}
    return {"error": result.stderr}
```

### 5. **긴 입력 처리**

대용량 md 파일 (10MB+)은 청크 단위 처리 권장. 단, 현재 md_to_hwpx.py는 한 번에 로드 — 개선 가능.

---

## 테스트

각 에이전트에서:

```bash
python3 md_to_hwpx.py examples/example.md /tmp/test.hwpx
```

성공 시: `OK: /tmp/test.hwpx (XXX bytes)` 출력.

---

## 자동 등록 스크립트

다른 에이전트가 사용 시 호출할 수 있는 install 스크립트:

```bash
# mac/Linux/WSL
./install.sh
# 또는 원격에서
curl -fsSL https://raw.githubusercontent.com/jinwoo1225/hwp-skill/master/install.sh | bash

# Windows
install.bat
# 또는
irm https://raw.githubusercontent.com/jinwoo1225/hwp-skill/master/install.bat -outfile install.bat
.\install.bat
```

기본 등록 대상: Claude Code + Codex + Hermes.

`HWP_AGENTS` 환경변수로 선택적 등록:

```bash
# Claude Code만
HWP_AGENTS=claude-code ./install.sh

# Claude + Codex (Hermes 제외)
HWP_AGENTS=claude-code,codex ./install.sh
```

---

## 문제 보고

이슈/PR: https://github.com/jinwoo1225/hwp-skill/issues
