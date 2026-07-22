# Marineford OBS Preview Embed

이 폴더는 기존 웹 페이지에 Marineford OBS 송출 화면 미리보기를 붙이기 위한 정적 배포물입니다.

## 구조

- `panel.html`: 컨트롤, 태블릿, 편집 로그 화면의 안전한 정적 데모
- `overlay.html`: iframe 안에서 보이는 OBS 송출 화면 정적 데모
- `embed.js`: 기존 웹 페이지에 붙이는 동적 위젯 스크립트
- `index.html`: 데모 위젯을 단독으로 확인하는 페이지
- `version.json`: GitHub Pages 캐시 무효화를 위한 최신 커밋 메타데이터
- `WEB_EMBED_PROMPT.md`: 별도 웹 작업 대화에 전달할 프롬프트

## 기존 웹 페이지에 붙이는 최소 코드

```html
<div id="marineford-preview"></div>
<script src="https://enceladus-x.github.io/marineford_OBS/preview/embed.js"></script>
```

`embed.js`는 자동으로 `version.json`을 읽고 iframe URL에 `v=` 값을 붙입니다. 화면 탭에서 컨트롤 패널, 태블릿 패널, OBS 오버레이, 편집 로그를 전환할 수 있고, OBS 오버레이에서는 경기 상태를 다시 선택할 수 있습니다. 따라서 이 저장소에서 미리보기 화면을 수정하고 `main`에 push하면 기존 웹 페이지는 같은 스크립트 URL을 유지하면서 최신 정적 데모를 보여줍니다.

## 옵션

스크립트 태그의 `data-*` 속성으로 일부 값을 바꿀 수 있습니다.

```html
<div id="marineford-preview"></div>
<script
  src="https://enceladus-x.github.io/marineford_OBS/preview/embed.js"
  data-target="#marineford-preview"
  data-default-screen="control"
  data-default-demo="duel"
  data-title="Marineford OBS"
  data-description="TCG 매장 방송 송출용 컨트롤 패널입니다."
  data-show-steps="true">
</script>
```

지원 속성:

- `data-target`: 위젯을 넣을 CSS selector
- `data-base-url`: `overlay.html`과 `version.json`이 있는 기준 URL
- `data-default-screen`: `control`, `tablet`, `overlay`, `editor`
- `data-default-demo`: `duel`, `side`, `judge`, `standby`
- `data-download-url`: 실행 파일 다운로드 URL
- `data-release-url`: 릴리스 노트 URL
- `data-title`: 섹션 제목
- `data-description`: 설명 문구
- `data-show-steps`: `false`이면 사용 흐름 카드 숨김
- `data-auto-mount`: `false`이면 자동 렌더링하지 않고 JS API로 직접 mount

## 직접 mount

```html
<div id="custom-preview"></div>
<script src="https://enceladus-x.github.io/marineford_OBS/preview/embed.js" data-auto-mount="false"></script>
<script>
  MarinefordOBSPreview.mount("#custom-preview", {
    defaultScreen: "overlay",
    defaultDemo: "judge",
    showSteps: false
  });
</script>
```

## 자동 버전 갱신

`.github/workflows/preview-version.yml`은 `docs/preview/**`가 main에 push될 때 `scripts/write_preview_version.py`를 실행해 `version.json`을 갱신합니다.

## 주의

- 실제 로컬 서버, `state.json`, 덱 프리셋, 업로드 이미지, 백업 파일은 웹에 올리지 않습니다.
- 기존 웹 페이지에 CSP가 있으면 `script-src`와 `frame-src`에 `https://enceladus-x.github.io`를 허용해야 합니다.
- GitHub Pages 배포 소스는 저장소의 `docs/` 폴더로 설정되어 있어야 합니다.
