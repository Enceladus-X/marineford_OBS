# Marineford OBS Overlay

TCG 매장 방송 송출용 OBS 브라우저 오버레이입니다. 운영자는 `control.html`에서 선수명, 점수, 타이머, 이미지를 조작하고, OBS는 `overlay.html`을 브라우저 소스로 읽어 실시간으로 표시합니다.

## 실행

```powershell
python server.py
```

서버가 켜지면 아래 주소를 사용합니다.

- 컨트롤 패널: http://localhost:8000/control.html
- OBS 오버레이: http://localhost:8000/overlay.html
- 상태 API: http://localhost:8000/state

OBS 브라우저 소스 설정은 URL `http://localhost:8000/overlay.html`, 너비 `1920`, 높이 `1080`을 기준으로 합니다.

## 파일 구성

- `server.py`: 로컬 HTTP 서버, 상태 API, 이미지 업로드 처리
- `control.html`: 방송 운영자용 컨트롤 패널
- `overlay.html`: OBS 브라우저 소스용 오버레이
- `images/`: 방송 이미지 에셋
- `state.example.json`: 새 상태 파일 예시
- `인수인계서.md`: 운영 인수인계 문서

`state.json`은 실행 중 자동 생성되는 런타임 파일이라 Git에는 올리지 않습니다. 상태를 초기화하려면 서버를 끈 뒤 `state.json`을 삭제하고 다시 실행하면 됩니다.
