import http.server, json, os

STATE_FILE = 'state.json'

DEFAULT_STATE = {
    "p1Name": "", "p1Deck": "",
    "p2Name": "", "p2Deck": "",
    "tournamentName": "", "roundName": "",
    "scoreLeft": 0, "scoreRight": 0,
    "timerSeconds": 2400, "timerRunning": False,
    "leftImg1": "", "leftImg2": "",
    "rightImg1": "", "rightImg2": "",
    "p1CardImg": "", "p2CardImg": ""
}

def read_state():
    try:
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            state = DEFAULT_STATE.copy()
            state.update(json.load(f))
            return state
    except:
        return DEFAULT_STATE.copy()

def write_state(data):
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)

class Handler(http.server.SimpleHTTPRequestHandler):

    def do_GET(self):
        path = self.path.split('?')[0]
        if path == '/state':
            data = json.dumps(read_state(), ensure_ascii=False).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', len(data))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            self.wfile.write(data)
        else:
            super().do_GET()

    def do_POST(self):
        path = self.path.split('?')[0]

        if path == '/state':
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length)
            try:
                data = json.loads(body.decode('utf-8'))
                write_state(data)
                resp = b'{"ok":true}'
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', len(resp))
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(resp)
            except Exception as e:
                self.send_response(500)
                self.end_headers()

        elif path == '/upload':
            # multipart/form-data 파일 업로드 처리
            try:
                content_type = self.headers.get('Content-Type', '')
                length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(length)

                # boundary 파싱
                boundary = None
                for part in content_type.split(';'):
                    part = part.strip()
                    if part.startswith('boundary='):
                        boundary = part[9:].strip()
                        break

                if not boundary:
                    raise Exception('boundary not found')

                # 파일 추출
                delimiter = ('--' + boundary).encode()
                parts = body.split(delimiter)
                saved_filename = None

                for part in parts:
                    if b'Content-Disposition' not in part:
                        continue
                    header_end = part.find(b'\r\n\r\n')
                    if header_end == -1:
                        continue
                    header = part[:header_end].decode('utf-8', errors='ignore')
                    file_data = part[header_end+4:]
                    if file_data.endswith(b'\r\n'):
                        file_data = file_data[:-2]

                    # 파일명 추출
                    filename = None
                    for h in header.split('\r\n'):
                        if 'filename=' in h:
                            fname_start = h.find('filename="') + 10
                            fname_end = h.find('"', fname_start)
                            filename = h[fname_start:fname_end]
                            break

                    if filename and file_data:
                        filename = os.path.basename(filename.replace('\\', '/')).strip()
                    if filename and file_data:
                        # images 폴더에 저장
                        os.makedirs('images', exist_ok=True)
                        save_path = os.path.join('images', filename)
                        with open(save_path, 'wb') as f:
                            f.write(file_data)
                        saved_filename = 'images/' + filename
                        break

                if saved_filename:
                    resp = json.dumps({'ok': True, 'path': saved_filename}).encode('utf-8')
                else:
                    resp = json.dumps({'ok': False, 'error': 'no file'}).encode('utf-8')

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', len(resp))
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(resp)

            except Exception as e:
                resp = json.dumps({'ok': False, 'error': str(e)}).encode('utf-8')
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', len(resp))
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(resp)
        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def log_message(self, format, *args):
        pass

if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    os.makedirs('images', exist_ok=True)
    if not os.path.exists(STATE_FILE):
        write_state(DEFAULT_STATE.copy())
    port = 8000
    print(f'[마린포드] 서버 시작: http://localhost:{port}')
    print(f'  오버레이: http://localhost:{port}/overlay.html')
    print(f'  컨트롤:   http://localhost:{port}/control.html')
    print(f'  종료하려면 Ctrl+C')
    http.server.HTTPServer(('', port), Handler).serve_forever()
