# Marineford OBS Overlay

TCG 매장 방송 송출용 OBS 브라우저 오버레이입니다. 운영자는 `control.html`에서 선수명, 점수, 타이머, 이미지를 조작하고, OBS는 `overlay.html`을 브라우저 소스로 읽어 실시간으로 표시합니다.

## 실행

```powershell
python server.py
```

현장에서는 `start_marineford.bat`을 더블클릭하면 서버를 켜고 송출컴/태블릿 접속 주소를 자동으로 표시합니다.
배치파일 실행 후 열리는 `connect.html` 화면의 QR 코드를 태블릿으로 스캔하면 태블릿 패널에 바로 접속할 수 있습니다.

GitHub ZIP 또는 릴리스 파일로 받은 경우에는 압축을 먼저 푼 뒤 `start_marineford.bat`을 실행합니다. 압축 파일 안에서 바로 실행하면 이미지와 상태 파일 경로가 꼬일 수 있습니다.

서버가 켜지면 아래 주소를 사용합니다.

- 컨트롤 패널: http://localhost:8000/control.html
- 태블릿 연결 QR: http://localhost:8000/connect.html
- 태블릿 패널: http://localhost:8000/tablet.html
- 편집 보조 패널: http://localhost:8000/editor.html
- OBS 오버레이: http://localhost:8000/overlay.html
- 상태 API: http://localhost:8000/api/state

OBS 브라우저 소스 설정은 URL `http://localhost:8000/overlay.html`, 너비 `1920`, 높이 `1080`을 기준으로 합니다.

태블릿은 송출 PC와 같은 Wi-Fi에 연결한 뒤 `http://송출PC_IP:8000/tablet.html`로 접속합니다.

## 파일 구성

- `server.py`: 로컬 HTTP 서버, 상태 API, 태블릿 액션, 이벤트 로그, 이미지 업로드 처리
- `control.html`: 방송 운영자용 컨트롤 패널
- `connect.html`: 태블릿 접속용 QR 코드 안내 페이지
- `tablet.html`: 현장 태블릿용 세트 스코어/듀얼 상태 패널
- `editor.html`: 듀얼 구간 확인 및 편집 보조 export 패널
- `overlay.html`: OBS 브라우저 소스용 오버레이
- `images/`: 방송 이미지 에셋
- `state.example.json`: 새 상태 파일 예시
- `인수인계서.md`: 운영 인수인계 문서

`state.json`과 `events.jsonl`은 실행 중 자동 생성되는 런타임 파일이라 Git에는 올리지 않습니다. 상태를 초기화하려면 서버를 끈 뒤 두 파일을 삭제하고 다시 실행하면 됩니다.

## 태블릿 액션 흐름

- 경기 시작 전: 각 플레이어가 태블릿의 좌/우 패널을 터치해 닉네임과 덱 이름을 입력합니다. 덱 이름은 경기 중 패널과 OBS 오버레이에 표시되지 않습니다.
- `듀얼 시작`: 현재 세트를 `dueling` 상태로 바꾸고, 첫 시작이라면 편집 export 기준점도 자동으로 기록합니다.
- `승패 보고`: 세트가 끝났을 때 승자를 선택합니다. 버튼에는 좌/우 대신 입력한 닉네임이 표시됩니다.
- `마지막 보고 취소`: 마지막 태블릿 이벤트를 되돌립니다.
- `다음 듀얼 시작`: 사이드덱 교체 후 다음 세트 시작점을 기록합니다.
- `다음 라운드 준비`: 매치 종료 후 점수와 듀얼 상태를 초기화하고, 이전 플레이어의 닉네임과 덱 이름을 비워 새 착석 입력 화면으로 돌아갑니다.

## 편집 export

- `/api/export/cuts.csv`: 듀얼 구간 목록
- `/api/export/chapters.txt`: 유튜브 챕터 초안
- `/api/export/ffmpeg.txt`: 원본 녹화 파일에서 듀얼 구간만 자르는 ffmpeg 명령 초안
