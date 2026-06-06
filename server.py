import csv
import io
import json
import os
import socket
import sys
import threading
import uuid
import webbrowser
from datetime import datetime
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

PORT = 8000


def is_packaged():
    return bool(getattr(sys, "frozen", False))


def asset_dir():
    if is_packaged():
        return getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(sys.executable)))
    return os.path.dirname(os.path.abspath(__file__))


def data_dir():
    if is_packaged():
        return os.path.dirname(os.path.abspath(sys.executable))
    return asset_dir()


ASSET_DIR = asset_dir()
DATA_DIR = data_dir()
STATE_FILE = os.path.join(DATA_DIR, "state.json")
EVENTS_FILE = os.path.join(DATA_DIR, "events.jsonl")

MATCH_FIELDS = [
    "matchId",
    "phase",
    "currentSet",
    "matchTarget",
    "scoreLeft",
    "scoreRight",
    "timerSeconds",
    "timerRunning",
    "duelStartedAt",
    "duelEndedAt",
    "recordingStartedAt",
    "updatedAt",
]

DEFAULT_STATE = {
    "p1Name": "",
    "p1Deck": "",
    "p2Name": "",
    "p2Deck": "",
    "tournamentName": "",
    "roundName": "",
    "scoreLeft": 0,
    "scoreRight": 0,
    "timerSeconds": 2400,
    "timerRunning": False,
    "leftImg1": "",
    "leftImg2": "",
    "rightImg1": "",
    "rightImg2": "",
    "p1CardImg": "",
    "p2CardImg": "",
    "matchId": "",
    "phase": "idle",
    "currentSet": 1,
    "matchTarget": 2,
    "duelStartedAt": "",
    "duelEndedAt": "",
    "recordingStartedAt": "",
    "updatedAt": "",
}


def now_iso():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def new_match_id():
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"match-{stamp}-{uuid.uuid4().hex[:6]}"


def get_lan_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            if ip and not ip.startswith("127."):
                return ip
    except OSError:
        pass

    try:
        for ip in socket.gethostbyname_ex(socket.gethostname())[2]:
            if ip and not ip.startswith("127.") and not ip.startswith("169.254."):
                return ip
    except OSError:
        pass

    return "127.0.0.1"


def normalize_state(data):
    state = DEFAULT_STATE.copy()
    if isinstance(data, dict):
        state.update(data)

    for key in ("scoreLeft", "scoreRight", "timerSeconds", "currentSet", "matchTarget"):
        try:
            state[key] = int(state.get(key, DEFAULT_STATE[key]))
        except (TypeError, ValueError):
            state[key] = DEFAULT_STATE[key]

    state["scoreLeft"] = max(0, state["scoreLeft"])
    state["scoreRight"] = max(0, state["scoreRight"])
    state["currentSet"] = max(1, state["currentSet"])
    state["matchTarget"] = max(1, state["matchTarget"])
    state["timerRunning"] = bool(state.get("timerRunning", False))

    if state.get("phase") not in {"idle", "dueling", "sideboarding", "finished"}:
        state["phase"] = "idle"

    return state


def read_state():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return normalize_state(json.load(f))
    except Exception:
        return normalize_state({})


def write_state(data):
    state = normalize_state(data)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    return state


def read_events():
    events = []
    if not os.path.exists(EVENTS_FILE):
        return events
    with open(EVENTS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return events


def write_events(events):
    with open(EVENTS_FILE, "w", encoding="utf-8") as f:
        for event in events:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")


def append_event(event):
    with open(EVENTS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def snapshot_match(state):
    return {key: state.get(key, DEFAULT_STATE.get(key)) for key in MATCH_FIELDS}


def apply_action(payload):
    action = payload.get("action")
    state = read_state()
    before = snapshot_match(state)
    timestamp = now_iso()
    event = None

    if not state.get("matchId"):
        state["matchId"] = new_match_id()

    if action == "start_duel":
        next_set = state["scoreLeft"] + state["scoreRight"] + 1
        auto_recording_start = not state.get("recordingStartedAt")
        state.update(
            {
                "phase": "dueling",
                "currentSet": max(1, next_set),
                "duelStartedAt": timestamp,
                "duelEndedAt": "",
                "timerRunning": True,
                "updatedAt": timestamp,
            }
        )
        if auto_recording_start:
            state["recordingStartedAt"] = timestamp
        event = {
            "type": "duel_start",
            "set": state["currentSet"],
            "time": timestamp,
            "scoreLeft": state["scoreLeft"],
            "scoreRight": state["scoreRight"],
        }
        if auto_recording_start:
            event["recordingStartedAt"] = timestamp

    elif action == "set_win":
        winner = payload.get("winner")
        if winner not in {"left", "right"}:
            raise ValueError("winner must be left or right")

        set_number = state.get("currentSet") or (state["scoreLeft"] + state["scoreRight"] + 1)
        if winner == "left":
            state["scoreLeft"] += 1
        else:
            state["scoreRight"] += 1

        finished = state["scoreLeft"] >= state["matchTarget"] or state["scoreRight"] >= state["matchTarget"]
        state.update(
            {
                "phase": "finished" if finished else "sideboarding",
                "currentSet": set_number,
                "duelEndedAt": timestamp,
                "timerRunning": False,
                "updatedAt": timestamp,
            }
        )
        event = {
            "type": "set_end",
            "set": set_number,
            "winner": winner,
            "time": timestamp,
            "scoreLeft": state["scoreLeft"],
            "scoreRight": state["scoreRight"],
            "phase": state["phase"],
        }

    elif action == "mark_recording_start":
        state.update({"recordingStartedAt": timestamp, "updatedAt": timestamp})
        event = {
            "type": "recording_start",
            "time": timestamp,
            "scoreLeft": state["scoreLeft"],
            "scoreRight": state["scoreRight"],
        }

    elif action == "undo":
        events = read_events()
        if not events:
            return state, {"ok": True, "state": state, "event": None}
        last = events.pop()
        previous = last.get("before")
        if isinstance(previous, dict):
            for key, value in previous.items():
                if key in MATCH_FIELDS:
                    state[key] = value
            state["updatedAt"] = timestamp
        write_events(events)
        return write_state(state), {"ok": True, "state": state, "undone": last}

    elif action in {"reset_match", "prepare_next_round"}:
        keep = {
            "tournamentName": state.get("tournamentName", ""),
            "matchTarget": state.get("matchTarget", DEFAULT_STATE["matchTarget"]),
        }
        state = normalize_state(keep)
        state.update(
            {
                "matchId": new_match_id(),
                "phase": "idle",
                "currentSet": 1,
                "scoreLeft": 0,
                "scoreRight": 0,
                "timerSeconds": DEFAULT_STATE["timerSeconds"],
                "timerRunning": False,
                "duelStartedAt": "",
                "duelEndedAt": "",
                "recordingStartedAt": "",
                "updatedAt": timestamp,
            }
        )
        event = {
            "type": "next_round_prepare" if action == "prepare_next_round" else "match_reset",
            "time": timestamp,
        }

    elif action == "finish_match":
        state.update({"phase": "finished", "timerRunning": False, "updatedAt": timestamp})
        event = {
            "type": "match_finished",
            "time": timestamp,
            "scoreLeft": state["scoreLeft"],
            "scoreRight": state["scoreRight"],
        }

    else:
        raise ValueError("unknown action")

    after = snapshot_match(state)
    state = write_state(state)
    if event:
        event.update({"id": uuid.uuid4().hex, "matchId": state["matchId"], "before": before, "after": after})
        append_event(event)

    return state, {"ok": True, "state": state, "event": event}


def parse_time(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def seconds_between(start, end):
    start_dt = parse_time(start)
    end_dt = parse_time(end)
    if not start_dt or not end_dt:
        return 0
    return max(0, int((end_dt - start_dt).total_seconds()))


def format_hms(total_seconds):
    total_seconds = max(0, int(total_seconds))
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def qr_svg(text, scale=10, border=4):
    matrix = build_qr_matrix(text.encode("ascii"))
    size = len(matrix)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size + border * 2} {size + border * 2}" shape-rendering="crispEdges">',
        '<rect width="100%" height="100%" fill="#fff"/>',
    ]
    for y, row in enumerate(matrix):
        x = 0
        while x < size:
            if not row[x]:
                x += 1
                continue
            start = x
            while x < size and row[x]:
                x += 1
            parts.append(f'<rect x="{start + border}" y="{y + border}" width="{x - start}" height="1" fill="#000"/>')
    parts.append("</svg>")
    return "\n".join(parts)


def build_qr_matrix(data):
    # Fixed QR Version 3-L is enough for the local tablet URL and keeps the
    # generator dependency-free for field PCs.
    version = 3
    size = 17 + version * 4
    data_codewords = 55
    ecc_codewords = 15
    if len(data) > 53:
        raise ValueError("QR text is too long")

    bits = [0, 1, 0, 0]
    bits.extend([(len(data) >> i) & 1 for i in range(7, -1, -1)])
    for byte in data:
        bits.extend([(byte >> i) & 1 for i in range(7, -1, -1)])

    capacity = data_codewords * 8
    bits.extend([0] * min(4, capacity - len(bits)))
    while len(bits) % 8:
        bits.append(0)

    codewords = []
    for i in range(0, len(bits), 8):
        value = 0
        for bit in bits[i : i + 8]:
            value = (value << 1) | bit
        codewords.append(value)
    for pad in (0xEC, 0x11):
        if len(codewords) < data_codewords:
            codewords.append(pad)
    while len(codewords) < data_codewords:
        codewords.extend([0xEC, 0x11])
    codewords = codewords[:data_codewords]
    all_codewords = codewords + rs_remainder(codewords, ecc_codewords)

    modules = [[None for _ in range(size)] for _ in range(size)]
    draw_finder(modules, 0, 0)
    draw_finder(modules, size - 7, 0)
    draw_finder(modules, 0, size - 7)
    draw_alignment(modules, 22, 22)

    for i in range(8, size - 8):
        bit = i % 2 == 0
        modules[6][i] = bit
        modules[i][6] = bit

    reserve_format(modules)
    modules[size - 8][8] = True

    data_bits = []
    for codeword in all_codewords:
        data_bits.extend([(codeword >> i) & 1 for i in range(7, -1, -1)])

    bit_index = 0
    upward = True
    col = size - 1
    while col > 0:
        if col == 6:
            col -= 1
        rows = range(size - 1, -1, -1) if upward else range(size)
        for row in rows:
            for c in (col, col - 1):
                if modules[row][c] is not None:
                    continue
                bit = bit_index < len(data_bits) and data_bits[bit_index] == 1
                modules[row][c] = bit ^ qr_mask(0, row, c)
                bit_index += 1
        upward = not upward
        col -= 2

    draw_format_bits(modules, 0)
    return modules


def draw_finder(modules, x, y):
    size = len(modules)
    for dy in range(-1, 8):
        for dx in range(-1, 8):
            xx = x + dx
            yy = y + dy
            if xx < 0 or yy < 0 or xx >= size or yy >= size:
                continue
            dark = (
                0 <= dx <= 6
                and 0 <= dy <= 6
                and (dx in {0, 6} or dy in {0, 6} or (2 <= dx <= 4 and 2 <= dy <= 4))
            )
            modules[yy][xx] = dark


def draw_alignment(modules, cx, cy):
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            modules[cy + dy][cx + dx] = max(abs(dx), abs(dy)) != 1


def reserve_format(modules):
    size = len(modules)
    for i in range(9):
        if i != 6:
            modules[8][i] = False
            modules[i][8] = False
    for i in range(8):
        modules[8][size - 1 - i] = False
        modules[size - 1 - i][8] = False


def draw_format_bits(modules, mask):
    size = len(modules)
    bits = format_bits(mask)
    for i in range(6):
        modules[8][i] = ((bits >> i) & 1) == 1
    modules[8][7] = ((bits >> 6) & 1) == 1
    modules[8][8] = ((bits >> 7) & 1) == 1
    modules[7][8] = ((bits >> 8) & 1) == 1
    for i in range(9, 15):
        modules[14 - i][8] = ((bits >> i) & 1) == 1
    for i in range(8):
        modules[size - 1 - i][8] = ((bits >> i) & 1) == 1
    for i in range(8, 15):
        modules[8][size - 15 + i] = ((bits >> i) & 1) == 1
    modules[size - 8][8] = True


def format_bits(mask):
    data = (1 << 3) | mask  # Error correction L, mask pattern 0.
    rem = data
    for _ in range(10):
        rem = (rem << 1) ^ (((rem >> 9) & 1) * 0x537)
    return ((data << 10) | rem) ^ 0x5412


def qr_mask(mask, row, col):
    if mask != 0:
        raise ValueError("only QR mask 0 is supported")
    return (row + col) % 2 == 0


def rs_remainder(data, degree):
    generator = [1]
    for i in range(degree):
        generator = poly_multiply(generator, [1, gf_pow(2, i)])

    result = [0] * degree
    for byte in data:
        factor = byte ^ result.pop(0)
        result.append(0)
        if factor:
            for i in range(degree):
                result[i] ^= gf_multiply(generator[i + 1], factor)
    return result


def poly_multiply(a, b):
    result = [0] * (len(a) + len(b) - 1)
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            result[i + j] ^= gf_multiply(x, y)
    return result


def gf_multiply(x, y):
    z = 0
    while y:
        if y & 1:
            z ^= x
        x <<= 1
        if x & 0x100:
            x ^= 0x11D
        y >>= 1
    return z


def gf_pow(x, power):
    result = 1
    for _ in range(power):
        result = gf_multiply(result, x)
    return result


def build_segments(events):
    starts = {}
    segments = []
    for event in events:
        if event.get("type") == "duel_start":
            starts[event.get("set")] = event
        elif event.get("type") == "set_end":
            set_number = event.get("set")
            start = starts.pop(set_number, None)
            if not start:
                continue
            duration = seconds_between(start.get("time"), event.get("time"))
            segments.append(
                {
                    "set": set_number,
                    "start": start.get("time", ""),
                    "end": event.get("time", ""),
                    "winner": event.get("winner", ""),
                    "scoreLeft": event.get("scoreLeft", ""),
                    "scoreRight": event.get("scoreRight", ""),
                    "durationSeconds": duration,
                }
            )
    return segments


def build_cuts_csv(segments):
    out = io.StringIO()
    writer = csv.DictWriter(
        out,
        fieldnames=["set", "start", "end", "winner", "scoreLeft", "scoreRight", "durationSeconds"],
    )
    writer.writeheader()
    writer.writerows(segments)
    return out.getvalue()


def build_chapters(segments):
    lines = []
    cursor = 0
    for segment in segments:
        lines.append(f"{format_hms(cursor)} {segment['set']}세트")
        cursor += segment["durationSeconds"]
    return "\n".join(lines) + ("\n" if lines else "")


def build_ffmpeg_notes(segments, state):
    base = state.get("recordingStartedAt") or (segments[0]["start"] if segments else "")
    base_dt = parse_time(base)
    lines = [
        "# Recording-cut notes",
        "# Set recordingStartedAt from the tablet/editor for accurate original-video offsets.",
        "# Replace input.mp4 with the OBS recording file name.",
        "",
    ]
    concat_entries = []
    for index, segment in enumerate(segments, start=1):
        start_dt = parse_time(segment["start"])
        end_dt = parse_time(segment["end"])
        if base_dt and start_dt and end_dt:
            start_offset = max(0, int((start_dt - base_dt).total_seconds()))
            end_offset = max(0, int((end_dt - base_dt).total_seconds()))
            start_text = format_hms(start_offset)
            end_text = format_hms(end_offset)
        else:
            start_text = segment["start"]
            end_text = segment["end"]
        filename = f"set{index:02d}.mp4"
        concat_entries.append(filename)
        lines.append(f'ffmpeg -i input.mp4 -ss {start_text} -to {end_text} -c copy "{filename}"')
    if concat_entries:
        lines.extend(["", "# concat_list.txt"])
        lines.extend([f"file '{name}'" for name in concat_entries])
        lines.extend(["", 'ffmpeg -f concat -safe 0 -i concat_list.txt -c copy "duel-only.mp4"'])
    return "\n".join(lines) + "\n"


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ASSET_DIR, **kwargs)

    def translate_path(self, path):
        parsed = urlparse(path)
        clean_path = parsed.path.lstrip("/").replace("/", os.sep)
        if clean_path.startswith("images" + os.sep):
            runtime_path = os.path.abspath(os.path.join(DATA_DIR, clean_path))
            runtime_images = os.path.abspath(os.path.join(DATA_DIR, "images"))
            if runtime_path.startswith(runtime_images) and os.path.exists(runtime_path):
                return runtime_path
        return super().translate_path(path)

    def send_json(self, data, status=HTTPStatus.OK):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(body)

    def send_text(self, text, content_type="text/plain; charset=utf-8", filename=None):
        body = text.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-cache")
        if filename:
            self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.end_headers()
        self.wfile.write(body)

    def read_json_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if length <= 0:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        if path in {"/state", "/api/state"}:
            self.send_json(read_state())
            return
        if path == "/api/connect-info":
            host = get_lan_ip()
            base = f"http://{host}:{PORT}"
            self.send_json(
                {
                    "host": host,
                    "port": PORT,
                    "tabletUrl": f"{base}/tablet.html",
                    "controlUrl": f"http://127.0.0.1:{PORT}/control.html",
                    "overlayUrl": f"http://127.0.0.1:{PORT}/overlay.html",
                    "editorUrl": f"http://127.0.0.1:{PORT}/editor.html",
                }
            )
            return
        if path == "/api/qr.svg":
            query = parse_qs(parsed.query)
            text = query.get("text", [""])[0]
            if not text:
                self.send_json({"ok": False, "error": "text is required"}, HTTPStatus.BAD_REQUEST)
                return
            try:
                self.send_text(qr_svg(text), "image/svg+xml; charset=utf-8")
            except Exception as e:
                self.send_json({"ok": False, "error": str(e)}, HTTPStatus.BAD_REQUEST)
            return
        if path == "/api/events":
            events = read_events()
            self.send_json({"events": events, "segments": build_segments(events)})
            return
        if path.startswith("/api/export/"):
            events = read_events()
            state = read_state()
            segments = build_segments(events)
            export_name = path.rsplit("/", 1)[-1]
            if export_name == "cuts.csv":
                self.send_text(build_cuts_csv(segments), "text/csv; charset=utf-8", "cuts.csv")
                return
            if export_name == "chapters.txt":
                self.send_text(build_chapters(segments), "text/plain; charset=utf-8", "chapters.txt")
                return
            if export_name == "ffmpeg.txt":
                self.send_text(build_ffmpeg_notes(segments, state), "text/plain; charset=utf-8", "ffmpeg.txt")
                return
            self.send_json({"ok": False, "error": "unknown export"}, HTTPStatus.NOT_FOUND)
            return
        super().do_GET()

    def do_POST(self):
        path = urlparse(self.path).path

        if path in {"/state", "/api/state"}:
            try:
                data = self.read_json_body()
                data["updatedAt"] = now_iso()
                self.send_json({"ok": True, "state": write_state(data)})
            except Exception as e:
                self.send_json({"ok": False, "error": str(e)}, HTTPStatus.INTERNAL_SERVER_ERROR)
            return

        if path == "/api/action":
            try:
                _, response = apply_action(self.read_json_body())
                self.send_json(response)
            except Exception as e:
                self.send_json({"ok": False, "error": str(e)}, HTTPStatus.BAD_REQUEST)
            return

        if path == "/upload":
            self.handle_upload()
            return

        self.send_response(HTTPStatus.NOT_FOUND)
        self.end_headers()

    def handle_upload(self):
        try:
            content_type = self.headers.get("Content-Type", "")
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)

            boundary = None
            for part in content_type.split(";"):
                part = part.strip()
                if part.startswith("boundary="):
                    boundary = part[9:].strip()
                    break
            if not boundary:
                raise ValueError("boundary not found")

            delimiter = ("--" + boundary).encode()
            saved_filename = None

            for part in body.split(delimiter):
                if b"Content-Disposition" not in part:
                    continue
                header_end = part.find(b"\r\n\r\n")
                if header_end == -1:
                    continue
                header = part[:header_end].decode("utf-8", errors="ignore")
                file_data = part[header_end + 4 :]
                if file_data.endswith(b"\r\n"):
                    file_data = file_data[:-2]

                filename = None
                for header_line in header.split("\r\n"):
                    if "filename=" in header_line:
                        fname_start = header_line.find('filename="') + 10
                        fname_end = header_line.find('"', fname_start)
                        filename = header_line[fname_start:fname_end]
                        break

                if filename and file_data:
                    filename = os.path.basename(filename.replace("\\", "/")).strip()
                    os.makedirs(os.path.join(DATA_DIR, "images"), exist_ok=True)
                    save_path = os.path.join(DATA_DIR, "images", filename)
                    with open(save_path, "wb") as f:
                        f.write(file_data)
                    saved_filename = "images/" + filename
                    break

            if saved_filename:
                self.send_json({"ok": True, "path": saved_filename})
            else:
                self.send_json({"ok": False, "error": "no file"})
        except Exception as e:
            self.send_json({"ok": False, "error": str(e)}, HTTPStatus.INTERNAL_SERVER_ERROR)

    def do_OPTIONS(self):
        self.send_response(HTTPStatus.OK)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def log_message(self, format, *args):
        pass


if __name__ == "__main__":
    os.chdir(DATA_DIR)
    os.makedirs(os.path.join(DATA_DIR, "images"), exist_ok=True)
    if not os.path.exists(STATE_FILE):
        write_state(DEFAULT_STATE.copy())

    port = PORT
    lan_ip = get_lan_ip()
    print(f"[Marineford] server: http://localhost:{port}")
    print(f"  overlay : http://localhost:{port}/overlay.html")
    print(f"  control : http://localhost:{port}/control.html")
    print(f"  tablet  : http://{lan_ip}:{port}/tablet.html")
    print(f"  editor  : http://localhost:{port}/editor.html")
    print("  stop    : Ctrl+C")

    if is_packaged():
        threading.Timer(0.8, lambda: webbrowser.open(f"http://127.0.0.1:{port}/control.html")).start()

    ThreadingHTTPServer(("", port), Handler).serve_forever()
