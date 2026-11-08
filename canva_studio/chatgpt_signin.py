"""Sign in with ChatGPT for the Windows desktop app."""
import base64
import ctypes as ct
import hashlib
import json
import os
import re
import secrets
import struct
import time
import uuid
import webbrowser
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlencode, urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError

from .core import atomic_json
from . import credentials

ISSUER = 'https://auth.openai.com'
RESOURCE = 'https://api.openai.com/v1'
USAGE_SCOPE = 'chatgpt.tokens.use.direct'
SCOPES = 'openid profile email offline_access resource.invoke ' + USAGE_SCOPE
CALLBACK = '/auth/callback'
CLIENT_ID = re.compile(r'oaiapp_[A-Za-z0-9_-]{1,200}\Z')


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class RefreshRejected(ValueError):
    pass


def api_json(url, form=None, token=None):
    headers = {'Accept': 'application/json'}
    if form:
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
    if token:
        headers['Authorization'] = 'Bearer ' + token
    request = Request(url, data=urlencode(form).encode('ascii') if form else None, headers=headers)
    try:
        with build_opener(NoRedirect()).open(request, timeout=20) as response:
            value = json.loads(response.read(1024 * 1024))
    except HTTPError as error:
        if form and form.get('grant_type') == 'refresh_token':
            try:
                reason = json.loads(error.read(8192)).get('error')
                if isinstance(reason,dict):reason = reason.get('code')
            except (OSError,ValueError,AttributeError):
                reason = None
            if reason in ('invalid_grant','invalid_refresh_token','token_expired','refresh_token_expired',
                          'refresh_token_invalidated','refresh_token_reused'):
                raise RefreshRejected('Phiên ChatGPT đã hết hiệu lực. Hãy đăng nhập lại.') from None
        if error.code == 403:
            raise ValueError('Tài khoản hoặc workspace chưa được cấp quyền dùng gói ChatGPT trong SKST.') from None
        raise ValueError(f'Đăng nhập ChatGPT chưa hoàn tất (HTTP {error.code}). Thử đăng nhập lại.') from None
    except (OSError, ValueError):
        raise ValueError('Chưa kết nối được với OpenAI hoặc phản hồi không hợp lệ.') from None
    if not isinstance(value, dict):
        raise ValueError('OpenAI trả dữ liệu đăng nhập không hợp lệ.')
    return value


def base64url(value):
    if not re.fullmatch(r'[A-Za-z0-9_-]+', value):
        raise ValueError('Base64url không hợp lệ.')
    return base64.urlsafe_b64decode(value + '=' * (-len(value) % 4))


def verify_rsa_sha256(modulus, exponent, message, signature):
    """Verify using Windows CNG. The blob holds big-endian RSA public parameters."""
    if not 256 <= len(modulus) <= 1024 or not 1 <= len(exponent) <= 8 or len(signature) != len(modulus):
        return False
    bcrypt = ct.WinDLL('bcrypt')
    pointer = ct.c_void_p
    ulong = ct.c_ulong
    for name, types in {
        'BCryptOpenAlgorithmProvider': [ct.POINTER(pointer), ct.c_wchar_p, ct.c_wchar_p, ulong],
        'BCryptImportKeyPair': [pointer, pointer, ct.c_wchar_p, ct.POINTER(pointer), ct.c_char_p, ulong, ulong],
        'BCryptVerifySignature': [pointer, pointer, ct.c_char_p, ulong, ct.c_char_p, ulong, ulong],
        'BCryptDestroyKey': [pointer],
        'BCryptCloseAlgorithmProvider': [pointer, ulong],
    }.items():
        getattr(bcrypt, name).argtypes = types
        getattr(bcrypt, name).restype = ct.c_long
    algorithm = pointer()
    if bcrypt.BCryptOpenAlgorithmProvider(ct.byref(algorithm), 'RSA', None, 0):
        return False
    key = pointer()
    try:
        blob = struct.pack('<6I', 0x31415352, len(modulus) * 8, len(exponent), len(modulus), 0, 0)
        blob += exponent + modulus
        if bcrypt.BCryptImportKeyPair(algorithm, None, 'RSAPUBLICBLOB', ct.byref(key), blob, len(blob), 0):
            return False
        padding = ct.c_wchar_p('SHA256')
        digest = hashlib.sha256(message).digest()
        return bcrypt.BCryptVerifySignature(key, ct.byref(padding), digest, len(digest),
                                            signature, len(signature), 2) == 0
    finally:
        if key:
            bcrypt.BCryptDestroyKey(key)
        bcrypt.BCryptCloseAlgorithmProvider(algorithm, 0)


def validate_identity(token, client_id, nonce):
    try:
        head, body, signature = token.split('.')
        header = json.loads(base64url(head))
        if header.get('alg') != 'RS256' or not header.get('kid'):
            raise ValueError
        keys = api_json(ISSUER + '/.well-known/jwks.json')['keys']
        key = next(k for k in keys if k.get('kid') == header['kid'] and k.get('kty') == 'RSA'
                   and k.get('alg', 'RS256') == 'RS256' and k.get('use', 'sig') == 'sig')
        if not verify_rsa_sha256(base64url(key['n']), base64url(key['e']),
                                 (head + '.' + body).encode('ascii'), base64url(signature)):
            raise ValueError
        claims = json.loads(base64url(body))
        audience = claims['aud']
        audience_ok = audience == client_id or (
            isinstance(audience, list) and client_id in audience
            and (len(audience) == 1 or claims.get('azp') == client_id))
        now = time.time()
        if (claims['iss'] != ISSUER or not audience_ok or claims['nonce'] != nonce
                or type(claims['exp']) is not int or claims['exp'] <= now
                or type(claims['iat']) is not int or claims['iat'] > now + 5
                or ('nbf' in claims and (type(claims['nbf']) is not int or claims['nbf'] > now + 5))
                or not isinstance(claims['sub'], str) or not claims['sub']):
            raise ValueError
        return claims
    except (AttributeError, KeyError, TypeError, ValueError, StopIteration, OSError):
        raise ValueError('Không xác minh được tài khoản ChatGPT. Hãy đăng nhập lại.') from None


class CallbackServer(HTTPServer):
    result = None

    def get_request(self):
        connection, address = super().get_request()
        connection.settimeout(2)
        return connection, address


class CallbackHandler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # Callback URLs include one-time credentials.

    def do_GET(self):
        path = urlsplit(self.path)
        values = parse_qs(path.query)
        states = values.get('state', [])
        if path.path != CALLBACK or len(states) != 1 or not secrets.compare_digest(
            states[0].encode('utf8'), self.server.state.encode('ascii')
        ):
            self.send_error(400, 'Invalid authorization callback')
            return
        self.server.result = values
        body = 'Đã nhận phản hồi đăng nhập. Quay lại SKST Canva Studio để xem kết quả.'.encode()
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)


@dataclass
class Session:
    token: str = field(repr=False)
    expires_at: float
    models: tuple
    refresh: str = field(default='', repr=False)
    client_id: str = ''
    account: str = ''
    folder: object = field(default=None, repr=False)

    def access_token(self):
        if self.expires_at <= time.time() + 5:
            resumed = restore_session(self.folder) if self.folder else None
            if resumed is None:
                raise ValueError('Phiên ChatGPT đã hết hạn. Chọn Sign in with ChatGPT để kết nối lại.')
            self.token, self.expires_at, self.refresh = resumed.token, resumed.expires_at, resumed.refresh
        return self.token


def remember_session(folder, session):
    if not session.refresh:
        return False
    credentials.save(folder/'chatgpt-session.json', {
        'token': session.token, 'expires_at': session.expires_at, 'models': session.models,
        'refresh': session.refresh, 'client_id': session.client_id, 'account': session.account,
    })
    session.folder = folder
    return True


def forget_session(folder):
    credentials.save(folder/'chatgpt-session.json', {})


def restore_session(folder, cancelled=None):
    path = folder/'chatgpt-session.json'
    if not path.is_file():
        return None
    # Windows releases the lock on process exit, even after an interrupted update.
    with (folder/'chatgpt-session.lock').open('a+b') as lock:
        if os.name == 'nt':
            import msvcrt
            lock.seek(0)
            try:
                msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError:
                raise ValueError('Một cửa sổ SKST khác đang khôi phục ChatGPT. Thử lại sau.') from None
        saved = credentials.load(path)
        if not saved or (cancelled and cancelled.is_set()):
            return None
        try:
            session = Session(**saved, folder=folder)
            if not CLIENT_ID.fullmatch(session.client_id) or not session.refresh or not session.models:
                raise ValueError
            if session.token and session.expires_at > time.time() + 5:
                return session
        except (TypeError, ValueError):
            raise ValueError('Không đọc được phiên ChatGPT đã lưu. Hãy đăng nhập lại.') from None
        try:
            token = api_json(ISSUER + '/api/accounts/oauth/token', form={
                'grant_type': 'refresh_token', 'client_id': session.client_id,
                'refresh_token': session.refresh, 'resource': RESOURCE,
            })
        except RefreshRejected:
            forget_session(folder)
            raise
        access, expires = token_access(token)
        refresh = token.get('refresh_token')
        if not isinstance(refresh, str) or not refresh:
            raise ValueError('ChatGPT chưa trả mã gia hạn mới. Hãy đăng nhập lại.')
        if cancelled and cancelled.is_set():
            return None
        session.token, session.expires_at, session.refresh = access, expires, refresh
        remember_session(folder, session)
        return session


def token_access(token):
    scopes = token.get('scope')
    access = token.get('access_token')
    expires = token.get('expires_in')
    if (not isinstance(scopes, str) or not {USAGE_SCOPE, 'resource.invoke'}.issubset(scopes.split())
            or not isinstance(access, str) or not access or str(token.get('token_type','')).lower() != 'bearer'
            or type(expires) is not int or expires <= 5):
        raise ValueError('Chưa cấp quyền dùng lượt AI theo gói ChatGPT. Kiểm tra gói và quyền đã chọn.')
    return access, time.time() + expires


def sign_in(folder, cancelled):
    registration_path = folder/'chatgpt-registration.json'
    try:
        saved = json.loads(registration_path.read_text(encoding='utf8'))
    except (OSError, ValueError):
        saved = {}
    if not isinstance(saved, dict):
        saved = {}
    try:
        host = uuid.UUID(saved.get('host', ''))
    except (ValueError, AttributeError, TypeError):
        host = uuid.uuid4()
        saved = {'host': str(host)}
        atomic_json(registration_path, saved)
    registered = saved.get('client_id', '')
    if not isinstance(registered, str) or not CLIENT_ID.fullmatch(registered):
        registered = ''
    verifier = secrets.token_urlsafe(48)
    nonce = secrets.token_urlsafe(32)
    with CallbackServer(('127.0.0.1', 0), CallbackHandler) as listener:
        listener.timeout = .25
        listener.state = secrets.token_urlsafe(32)
        redirect = f'http://127.0.0.1:{listener.server_port}{CALLBACK}'
        params = {
            'client_id': registered or 'dynamic_agent_client', 'ext_agent_host_id': host.urn,
            'response_type': 'code', 'redirect_uri': redirect, 'scope': SCOPES,
            'resource': RESOURCE, 'state': listener.state, 'nonce': nonce, 'code_challenge_method': 'S256',
            'code_challenge': base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip('='),
        }
        if not registered:
            params['agent_name_hint'] = 'SKST Canva Studio'
        if not webbrowser.open_new_tab(ISSUER + '/api/accounts/authorize?' + urlencode(params)):
            raise ValueError('Không mở được trình duyệt để đăng nhập ChatGPT.')
        deadline = time.monotonic() + 180
        while listener.result is None and not cancelled.is_set() and time.monotonic() < deadline:
            listener.handle_request()
        callback = listener.result
    if cancelled.is_set() or not callback or callback.get('error'):
        raise ValueError('Đăng nhập ChatGPT đã hủy, bị từ chối hoặc hết thời gian chờ.')
    codes = callback.get('code', [])
    clients = callback.get('client_id', [registered])
    if (len(codes) != 1 or not codes[0] or len(clients) != 1 or not CLIENT_ID.fullmatch(clients[0])
            or (registered and clients[0] != registered)):
        raise ValueError('OpenAI chưa trả đăng ký hợp lệ. Hãy đăng nhập lại.')
    client_id = clients[0]
    token = api_json(ISSUER + '/api/accounts/oauth/token', form={
        'grant_type': 'authorization_code', 'client_id': client_id, 'code': codes[0],
        'code_verifier': verifier, 'redirect_uri': redirect, 'resource': RESOURCE,
    })
    claims = validate_identity(token.get('id_token', ''), client_id, nonce)
    if registered and saved.get('subject') != claims['sub']:
        raise ValueError('Tài khoản ChatGPT không khớp bản đăng ký SKST.')
    if cancelled.is_set():
        raise ValueError('Đăng nhập ChatGPT đã hủy.')
    # Keep registration metadata separate from protected credentials.
    atomic_json(registration_path, {'host': str(host), 'client_id': client_id, 'subject': claims['sub']})
    access, expires_at = token_access(token)
    catalog = api_json(RESOURCE + '/models', token=access).get('models')
    models = tuple((m['slug'], m['display_name']) for m in (catalog if isinstance(catalog,list) else [])
                   if isinstance(m,dict) and m.get('visibility')=='list' and isinstance(m.get('slug'),str)
                   and m['slug'] and isinstance(m.get('display_name'),str) and m['display_name'])
    if not models:
        raise ValueError('Tài khoản ChatGPT này chưa có model khả dụng cho SKST.')
    refresh = token.get('refresh_token')
    account = claims.get('email') or claims.get('name') or ''
    return Session(access, expires_at, models, refresh if isinstance(refresh,str) else '', client_id,
                   account if isinstance(account,str) else '')
