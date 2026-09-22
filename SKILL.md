---
name: hwp-skill
description: 마크다운(.md)을 한글 HWPX 파일로 변환합니다. 한컴 한글, MS Word, Google Docs에서 열 수 있는 .hwpx 출력. 표준 라이브러리만 사용 — 추가 pip install 불요.
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
---

# hwp-skill — Markdown to 한글 HWPX 변환

마크다운 문서를 한글(HWPX) 파일로 변환합니다. 한컴 한글, MS Word, Google Docs 어디서나 열기 가능.

## 호출법

다른 에이전트(Claude Code, Codex, Hermes 등)가 이 skill을 사용하는 방법:

### 가장 빠른 호출

```bash
python3 md_to_hwpx.py <input.md> <output.hwpx>
```

### 템플릿 지정 (스타일/이미지/페이지 유지)

```bash
python3 md_to_hwpx.py <input.md> <output.hwpx> --template <template.hwpx>
```

### wrapper 사용

```bash
# macOS/Linux/WSL
./run.sh input.md output.hwpx

# Windows
run.bat input.md output.hwpx
```

## 에이전트 통합 패턴

### 1. 직접 호출

가장 단순 — 에이전트가 Bash tool로 직접 호출:

```
[에이전트 액션]
python3 ~/local/share/hwp-skill/md_to_hwpx.py proposal.md proposal.hwpx

[사용자에게 보고]
proposal.hwpx를 생성했습니다. 한컴 한글에서 열어 확인하세요.
```

### 2. 도구로 wrapping

에이전트 시스템에서 `convert_to_hwpx` 같은 도구 정의:

```json
{
  "name": "convert_to_hwpx",
  "description": "Convert markdown to Korean HWPX file",
  "input_schema": {
    "type": "object",
    "properties": {
      "input_md": {"type": "string", "description": "입력 마크다운 파일 경로"},
      "output_hwpx": {"type": "string", "description": "출력 HWPX 파일 경로"},
      "template_hwpx": {"type": "string", "description": "선택적 한글 템플릿"}
    },
    "required": ["input_md", "output_hwpx"]
  }
}
```

### 3. SKILL.md 자동 인식

Claude Code는 이 repo의 `SKILL.md`를 자동으로 인식하여 skill로 등록합니다. 별도 설치 불요.

## 마크다운 확장 (v0.2+)

### 색상 매핑

```markdown
**RED:중요한 경고**              ← 빨간색
**BLUE:참고 사항**               ← 파란색
**GREEN:성공 메시지**             ← 초록색
**#FF6600:주황 강조**             ← 16진수 색상 직접
<span style="color:red">HTML 색상</span>  ← HTML inline
```

### 지원 색상 이름
red, blue, green, yellow, orange, purple, cyan, magenta, gray/grey, black, white, pink

### 지원 마크다운

| 입력 | 변환 |
|---|---|
| `# 제목` | 큰 글씨 (H1) |
| `## 부제` | 중간 글씨 (H2) |
| `### 소제` | 작은 글씨 (H3) |
| `- 리스트` | 들여쓴 단락 |
| `1. 번호` | 번호 리스트 |
| `> 인용` | 인용 단락 |
| ` ```코드``` ` | 코드 블록 |
| `\| 표 \| 셀 \|` | 평문 표 (셀 join) |

## 출력 위치

기본 HWPX 파일 구조 (변환 후):

```
output.hwpx  (ZIP 컨테이너)
├── mimetype
├── version.xml
├── contents.xml
├── Contents/
│   ├── content.hpf
│   ├── header.xml          ← 템플릿에서 복사
│   └── section0.xml         ← md 내용으로 교체
├── META-INF/
└── Preview/
    └── PrvText.txt          ← md 평문 미리보기
```

## 트러블슈팅

### "한글에서 색상이 안 보여요"
- 원인 1: inline `<hp:rPr>` 미지원 버전 → v0.3에서 header.xml charPr 정의 방식으로 변경 예정
- 원인 2: 한글 구버전 (2014 이전) → 한글 2018+ 권장
- 임시 해결: 한글에서 직접 색상 적용

### "변환은 됐는데 한글이 안 열려요"
- ZIP 무결성 확인: `python3 -c "import zipfile; zipfile.ZipFile('output.hwpx').testzip()"`
- Contents/section0.xml 유효성: `python3 -c "import xml.etree.ElementTree as ET; ET.parse(open('output.hwpx','rb').read())"`
- 템플릿 HWPX 손상 확인

### "Windows에서 인코딩 깨짐"
- `set PYTHONIOENCODING=utf-8`
- 또는 `chcp 65001` (UTF-8 코드페이지)

## 설치

### 자동 (다른 에이전트용)

```bash
# mac/Linux/WSL
curl -fsSL https://raw.githubusercontent.com/jinwoo1225/hwp-skill/master/install.sh | bash

# Windows
irm https://raw.githubusercontent.com/jinwoo1225/hwp-skill/master/install.bat -outfile install.bat
.\install.bat
```

### 수동

```bash
git clone https://github.com/jinwoo1225/hwp-skill.git ~/.local/share/hwp-skill
export PATH="$HOME/.local/share/hwp-skill:$PATH"
```

자세한 내용: [README.md](README.md), [AGENTS.md](AGENTS.md)

## 라이선스

MIT
