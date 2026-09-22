# hwp-skill — Markdown to 한글 HWPX 변환기

마크다운 문서를 한글(HWPX) 파일로 변환하는 크로스플랫폼 Python 도구.

## 특징

- **표준 라이브러리만** 사용 (zipfile, re, argparse) — 추가 설치 불요
- **크로스플랫폼** — macOS / Linux / Windows / WSL 모두 동작
- **HWPX 표준** (한글 신버전) — 한글, MS Word, Google Docs에서 열기 가능
- **템플릿 기반** — 기존 한글 문서를 템플릿으로 사용 (스타일/이미지/페이지 유지)
- **자동 템플릿 탐색** — `~/Downloads/아카이브/제안요청서_.hwpx` 등 흔한 위치 자동 검색

## 설치

### macOS / Linux / WSL

```bash
git clone https://github.com/jinwoo1225/hwp-skill.git
cd hwp-skill
chmod +x md_to_hwpx.py run.sh
```

### Windows (PowerShell / cmd)

```powershell
git clone https://github.com/jinwoo1225/hwp-skill.git
cd hwp-skill
```

> **Python 필수**: [python.org](https://www.python.org/downloads/) 에서 3.9+ 설치. 설치 시 "Add Python to PATH" 체크.

### 의존성

표준 라이브러리만 사용 — **추가 pip install 불요**.

## 사용법

### macOS / Linux / WSL

```bash
# 직접 호출
python3 md_to_hwpx.py input.md output.hwpx

# wrapper 사용
./run.sh input.md output.hwpx
```

### Windows

```powershell
# 직접 호출 (python 또는 py 명령)
python md_to_hwpx.py input.md output.hwpx
py md_to_hwpx.py input.md output.hwpx

# wrapper 사용
run.bat input.md output.hwpx
```

### 템플릿 지정 (모든 OS)

```bash
python3 md_to_hwpx.py input.md output.hwpx --template my_template.hwpx
```

### Windows 인코딩 주의

Windows 기본 콘솔 인코딩(CP949)으로 한글 경로/내용이 깨지면:

```powershell
# PowerShell — UTF-8 강제
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"
python md_to_hwpx.py input.md output.hwpx
```

```cmd
# cmd
set PYTHONIOENCODING=utf-8
python md_to_hwpx.py input.md output.hwpx
```

## CI/CD

GitHub Actions에서 **Ubuntu / macOS / Windows × Python 3.9/3.11/3.12** matrix 자동 테스트:

- ✅ ZIP 무결성 검증
- ✅ section0.xml 파싱 검증
- ✅ Preview/PrvText.txt 검증
- ✅ HWPX 아티팩트 업로드

[`.github/workflows/test.yml`](.github/workflows/test.yml) 참조.

## 지원 마크다운

| 입력 | 변환 결과 |
|---|---|
| `# 제목` | 큰 글씨 paragraph (charPrIDRef=1) |
| `## 부제목` | 중간 글씨 (charPrIDRef=2) |
| `### 소제목` | 작은 글씨 (charPrIDRef=3) |
| `- 리스트` | 들여쓴 paragraph (charPrIDRef=13) |
| `1. 번호` | 번호 리스트 paragraph |
| `> 인용` | 인용 paragraph (charPrIDRef=11) |
| ` ```코드``` ` | 코드 블록 paragraph (charPrIDRef=10) |
| `\| 표 \| 셀 \|` | 평문 paragraph로 (셀을 `  \|  `로 join) |
| 일반 단락 | 기본 paragraph (charPrIDRef=0) |
| `<span style="color:red">...</span>` | HTML 태그 제거 + 텍스트만 |
| `**볼드**` | 그대로 텍스트 (한글 일부 버전은 자동 인식) |

## 예제

```bash
# examples/example.md → examples/example.hwpx
python3 md_to_hwpx.py examples/example.md examples/example.hwpx

# 다른 md 파일 변환
python3 md_to_hwpx.py my_proposal.md my_proposal.hwpx
```

## 사용 사례

- **입찰 제안서** — 마크다운으로 작성 → 한글 최종본
- **과업지시서** — 기술 문서를 한글 형식으로
- **회의록 / 보고서** — md 템플릿 → 한글 변환
- **기존 HWPX 템플릿 + 새 내용** — 폰트/이미지/스타일 유지하면서 본문만 교체

## 한계 / 알려진 제약

1. **볼드/이탤릭** — 마크다운 `**...**`, `*...*` 그대로 텍스트로 박힘. 한글 일부 버전은 자동 인식하지만 보장 안 됨.
2. **HTML 인라인** — `<span style="...">...</span>` 색상/스타일 정보 손실.
3. **표** — HWPX 표 구조(`<hp:tbl>`) 대신 평문 paragraph로.
4. **이미지** — `![alt](url)` 미지원.
5. **코드 블록** — 모노스페이스 글꼴 자동 적용 안 됨.

## 로드맵

- [ ] **A. 볼드/이탤릭** → HWPX `<hp:charPr bold="1">` 글자속성 매핑
- [ ] **B. 색상** → `<span style="color:red">` → `<hp:charPr color="FF0000">`
- [ ] **C. 표** → HWPX `<hp:tbl>` 진짜 표 구조
- [ ] **D. 이미지** — `![alt](url)` → HWPX `<hp:pic>`
- [ ] **E. 코드 블록** — 모노스페이스 글꼴 매핑
- [ ] **F. 양방향** — HWPX → md 변환 (역방향)

## 라이선스

MIT — 자세한 내용 [LICENSE](LICENSE) 참조.

## 기여

이슈 / PR 환영. 특히 한국어 HWPX 표준 관련 PR.
