"""Use the signed-in Antigravity CLI through its documented JSON stream."""
import json
import os
import re
import shutil
import subprocess
import tempfile
import threading
from contextlib import suppress
from pathlib import Path

INSTALL_URL = 'https://antigravity.google/docs/install?tab=cli'
NO_WINDOW = 0x08000000 if os.name == 'nt' else 0
NEW_CONSOLE = 0x00000010 if os.name == 'nt' else 0
MAX_EVENT = 512 * 1024
SAFE_ENV = {
    'SYSTEMROOT', 'WINDIR', 'SYSTEMDRIVE', 'COMSPEC', 'PATH', 'PATHEXT', 'USERPROFILE',
    'HOMEDRIVE', 'HOMEPATH', 'APPDATA', 'LOCALAPPDATA', 'PROGRAMDATA', 'PROGRAMFILES',
    'PROGRAMFILES(X86)', 'TEMP', 'TMP', 'LANG',
}


def cli_executable(selected=''):
    path = Path(selected) if selected else Path(shutil.which('agy.exe') or Path.home()/'.local/bin/agy.exe')
    if path.name.casefold() != 'agy.exe' or not path.is_file():
        raise ValueError('Cài Google Antigravity CLI, rồi chọn tệp agy.exe trong Từ khóa AI.')
    return path.resolve()


def cli_environment():
    # Use the account that Google manages in its keyring, without API keys or custom endpoints.
    return {key:value for key,value in os.environ.items() if key.upper() in SAFE_ENV}


def open_sign_in(executable, folder):
    folder.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.Popen([str(executable)], cwd=folder, env=cli_environment(), creationflags=NEW_CONSOLE)
    except OSError:
        raise ValueError('Không mở được Antigravity CLI. Kiểm tra lại tệp agy.exe.') from None


def read_event(stream):
    line = stream.readline(MAX_EVENT + 1)
    if not line:
        return None
    if len(line) > MAX_EVENT:
        raise ValueError('Phản hồi Gemini vượt giới hạn kích thước.')
    try:
        event = json.loads(line)
        if isinstance(event, dict):
            return event
    except (UnicodeError, ValueError):
        pass
    raise ValueError('Antigravity CLI chưa trả đúng định dạng. Hãy cập nhật CLI của Google.')


def result_rows(result):
    if not isinstance(result, dict):
        raise ValueError('Gemini trả kết quả chưa hợp lệ.')
    if result.get('status') != 'SUCCESS':
        error = str(result.get('error', '')).casefold()
        if any(word in error for word in ('quota', 'rate limit', '429', 'resource_exhausted')):
            raise ValueError('Antigravity đang chạm hạn mức của tài khoản Google. Hãy thử lại sau.')
        if 'model' in error and ('invalid' in error or 'not recognized' in error):
            raise ValueError('Model Gemini chưa khả dụng. Để trống ô Model để dùng lựa chọn của Antigravity.')
        raise ValueError('Antigravity chưa phân tích được. Mở CLI để kiểm tra tài khoản và model.')
    structured = result.get('structured_output')
    if not isinstance(structured, dict) or not isinstance(structured.get('scenes'), list):
        raise ValueError('Gemini chưa trả danh sách từ khóa hợp lệ.')
    return structured['scenes']


def request_keywords(executable, folder, model, prompt, schema):
    if model and not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_.-]{0,99}', model):
        raise ValueError('Mã model Antigravity không hợp lệ.')
    folder.mkdir(parents=True, exist_ok=True)
    args = [
        str(executable), '--input-format', 'stream-json', '--output-format', 'stream-json',
        '--disable-slash-commands', '--print-timeout', '60s', '--json-schema', json.dumps(schema),
    ]
    if model:
        args += ['--model', model]
    with tempfile.TemporaryDirectory(prefix='keyword-', dir=folder) as work:
        try:
            with subprocess.Popen(args, cwd=work, env=cli_environment(), stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                  creationflags=NO_WINDOW) as process:
                timer = threading.Timer(75, process.kill)
                timer.daemon = True
                timer.start()
                try:
                    first = read_event(process.stdout)
                    if first is None or first.get('event') != 'init':
                        raise ValueError('Antigravity chưa sẵn sàng. Mở CLI và đăng nhập Google trước.')
                    # In headless mode Strict requires approval for every tool and none can be approved here.
                    if first.get('init', {}).get('permission_mode') != 'strict':
                        raise ValueError('Trong Antigravity CLI, mở /config, đặt Tool Permission thành Strict, rồi thử lại.')
                    message = {'event':'user','message':{'content':prompt}}
                    process.stdin.write((json.dumps(message, ensure_ascii=False)+'\n').encode('utf8'))
                    process.stdin.close()
                    for _ in range(2000):
                        event = read_event(process.stdout)
                        if event is None:
                            break
                        if event.get('event') == 'step_update' and event.get('step_update', {}).get('step_type') == 'tool':
                            raise ValueError('Gemini đã yêu cầu công cụ ngoài bước phân tích văn bản. Cảnh được giữ để duyệt.')
                        if event.get('event') == 'result':
                            rows = result_rows(event.get('result'))
                            with suppress(subprocess.TimeoutExpired):
                                process.wait(timeout=3)
                            return rows
                    raise ValueError('Antigravity chưa trả xong từ khóa hoặc đã hết thời gian chờ.')
                finally:
                    timer.cancel()
                    if process.poll() is None:
                        with suppress(OSError):
                            process.kill()
        except OSError:
            raise ValueError('Không chạy được Antigravity CLI. Kiểm tra cài đặt và đăng nhập Google.') from None
