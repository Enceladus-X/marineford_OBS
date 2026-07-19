# 기존 웹 페이지에 Marineford OBS 미리보기 섹션 추가 프롬프트

아래 지시를 웹 작업 대화에 그대로 전달하세요.

```text
기존 웹 페이지에 "Marineford OBS" 다운로드 및 송출 화면 미리보기 섹션을 추가해줘.

목표:
- 단순 다운로드 버튼이 아니라, 사용자가 실제 OBS 송출 화면이 어떤 형태인지 웹에서 미리 볼 수 있어야 한다.
- 실제 프로그램 서버를 웹에 띄우면 안 된다. 웹 미리보기는 정적 데모 iframe만 사용한다.
- 실행 파일은 웹 서버에 직접 올리지 말고 GitHub Releases 최신 파일로 연결한다.

사용할 정적 미리보기:
- 전체 데모 페이지: https://enceladus-x.github.io/marineford_OBS/preview/
- iframe용 송출 화면: https://enceladus-x.github.io/marineford_OBS/preview/overlay.html?demo=duel

다운로드 링크:
- Windows 실행 파일: https://github.com/Enceladus-X/marineford_OBS/releases/latest/download/Marineford_OBS.exe
- 릴리스 노트: https://github.com/Enceladus-X/marineford_OBS/releases/latest

필수 UI:
- 섹션 제목: Marineford OBS
- 짧은 설명: TCG 매장 방송 송출용 컨트롤 패널, OBS 오버레이, 태블릿 진행 패널을 제공한다.
- 16:9 송출 화면 iframe 미리보기
- 상태 전환 버튼 4개:
  - 듀얼중 -> /preview/overlay.html?demo=duel
  - 사이드 교체중 -> /preview/overlay.html?demo=side
  - 저지 호출 -> /preview/overlay.html?demo=judge
  - 다음 라운드 대기 -> /preview/overlay.html?demo=standby
- 다운로드 버튼과 릴리스 노트 링크
- 간단한 사용 흐름:
  1. 송출컴에서 실행 파일을 켠다.
  2. 컨트롤 패널에서 OBS URL과 태블릿 QR을 확인한다.
  3. OBS에 overlay URL을 브라우저 소스로 추가한다.
  4. 태블릿에서 듀얼 시작, 승패 보고, 저지 호출을 조작한다.

iframe 기본 코드:
<iframe
  src="https://enceladus-x.github.io/marineford_OBS/preview/overlay.html?demo=duel"
  title="Marineford OBS 송출 화면 미리보기"
  style="width:100%;aspect-ratio:16/9;border:0;border-radius:8px;background:#050506;"
  loading="lazy">
</iframe>

디자인 방향:
- 기존 웹사이트의 톤을 우선 유지한다.
- 단, 이 섹션은 방송 도구 느낌이 나도록 어두운 패널, 16:9 프리뷰, 명확한 다운로드 CTA를 사용한다.
- 너무 장황한 랜딩 페이지처럼 만들지 말고, 사용자가 "미리보기 확인 -> 다운로드"까지 바로 가게 구성한다.
- 모바일에서는 iframe이 화면 너비에 맞고, 상태 전환 버튼은 줄바꿈되어도 깨지지 않아야 한다.

주의:
- 실제 매장 프리셋, state.json, deck_presets.json, 업로드 이미지, 백업 파일을 웹에 올리지 않는다.
- iframe 출처가 차단되지 않도록 CSP가 있다면 frame-src에 https://enceladus-x.github.io 를 허용한다.
- GitHub Pages 주소가 바뀌면 /preview/ 경로만 실제 배포 주소에 맞게 조정한다.

검증:
- 데스크톱과 모바일 폭에서 iframe 비율이 16:9로 유지되는지 확인한다.
- 4개 상태 버튼이 iframe src를 바꾸는지 확인한다.
- 다운로드 버튼이 GitHub Releases 최신 실행 파일로 연결되는지 확인한다.
- 릴리스 노트 링크가 latest release로 연결되는지 확인한다.
```

