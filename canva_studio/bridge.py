"""Authenticated loopback bridge. Stores no Canva cookies or passwords."""
import base64, json, secrets, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from .core import atomic_json, valid_canva, VERSION

class Engine:
    def __init__(self, folder):
        self.folder=Path(folder);self.folder.mkdir(parents=True,exist_ok=True)
        self.lock=threading.RLock(); self.token=secrets.token_urlsafe(24)
        self.state=dict(mode='idle',message='Chọn voice để bắt đầu.',scenes=[],done=[],phase={},used=[],target='',voice='',voice_done=False,export_done=False)
        self.browser={}; self.running=None
        self.events=[]
        self.path=self.folder/'project.json'
        if self.path.exists():
            try:
                self.state.update(json.loads(self.path.read_text(encoding='utf8')))
                self.state['mode']='paused'; self.state['message']='Đã khôi phục dự án. Kiểm tra đúng thiết kế Canva trước khi tiếp tục.'
            except (ValueError,OSError):pass

    def save(self): atomic_json(self.path,self.state)
    def log(self,text):
        with self.lock:
            self.events.append(time.strftime('%H:%M:%S')+'  '+text);self.events=self.events[-250:]
            self.state['message']=text;self.save()
    def configure(self, plan, target, voice):
        with self.lock:
            if self.state['mode']=='running':raise ValueError('Hãy tạm dừng trước khi đổi dự án.')
            if not valid_canva(target):raise ValueError('Dán đường dẫn chỉnh sửa Canva hợp lệ.')
            self.state=dict(mode='ready',message='Đã sẵn sàng. Mở thiết kế video ngang trống trong Canva.',scenes=plan['scenes'],done=[],phase={},used=[],target=target,voice=str(voice),voice_done=False,export_done=False)
            self.running=None;self.save()
    def pause(self):
        with self.lock:self.state['mode']='paused';self.log('Đã tạm dừng. Thao tác đang thực hiện sẽ dừng ở điểm kiểm tra tiếp theo.')
    def start(self):
        with self.lock:
            if not self.state['scenes']:raise ValueError('Chưa có danh sách cảnh.')
            if len(self.state['scenes'])>50:raise ValueError('Bản thử hỗ trợ tối đa 50 cảnh mỗi dự án. Hãy chọn đoạn ngắn hơn.')
            if self.state['phase'].get('stage') in ('insert_intent','upload_intent','export_intent'):
                raise ValueError('Lần trước dừng giữa thao tác. Kiểm tra Canva rồi dùng nút Xử lý cảnh bị dở; ứng dụng sẽ không tự chèn trùng.')
            self.running=None;self.state['mode']='running';self.log('Đang chờ tiện ích kết nối đúng thiết kế Canva…')
    def recover(self, action):
        with self.lock:
            if self.state['mode']=='running':raise ValueError('Hãy tạm dừng trước.')
            stage=self.state['phase'].get('stage','')
            if stage=='insert_intent' and action=='inserted':self.state['phase']['stage']='inserted'
            elif action=='not_inserted':self.state['phase']={}
            else:raise ValueError('Không thể xác nhận tự động. Kiểm tra và chọn lại trạng thái.')
            self.running=None;self.save()
    def next_task(self, body):
        with self.lock:
            canonical=lambda u:u.split('?')[0].split('#')[0]
            if canonical(body.get('url',''))!=canonical(self.state['target']):return dict(task=None,mode='wrong_design')
            old=self.browser
            if old and old.get('client')!=body.get('client') and time.time()-old.get('seen',0)<15:
                return dict(task=None,mode='other_client')
            self.browser={**body,'seen':time.time()}
            if self.state['mode']!='running':return dict(task=None,mode=self.state['mode'])
            if self.running and self.running['client']!=body.get('client'):return dict(task=None,mode='busy')
            if not self.state['voice_done']: task=dict(id='voice',kind='voice',name='SKST_Voice.mp3')
            else:
                scene=next((s for s in self.state['scenes'] if s['id'] not in self.state['done']),None)
                if scene:task=dict(id=str(scene['id']),kind='scene',scene=scene,used=self.state['used'])
                elif not self.state['export_done']:task=dict(id='export',kind='export')
                else:return dict(task=None,mode='complete')
            task['phase']=self.state['phase'] if self.state['phase'].get('id')==task['id'] else {}
            self.running=dict(id=task['id'],client=body.get('client'))
            return dict(task=task,mode='running')
    def check(self, body):
        with self.lock:
            if not self.running or self.running['id']!=str(body.get('id')) or self.running['client']!=body.get('client'):raise ValueError('Phiên thao tác không còn hợp lệ.')
            if self.state['mode']!='running':return dict(continue_=False)
            stage=body.get('stage')
            if stage:
                self.state['phase']={**body,'id':str(body['id'])}; self.save()
            return dict(continue_=True)
    def result(self, body):
        with self.lock:
            if not self.running or self.running['id']!=str(body.get('id')) or self.running['client']!=body.get('client'):raise ValueError('Kết quả không thuộc phiên đang chạy.')
            if body.get('error'):
                self.state['mode']='attention';self.running=None;self.log('Cần kiểm tra: '+str(body['error'])[:1200]);return dict(ok=True)
            key=str(body['id'])
            if key=='voice':self.state['voice_done']=True;msg='Đã đặt voice trên timeline.'
            elif key=='export':self.state['export_done']=True;self.state['mode']='complete';msg='Đã gửi lệnh xuất MP4 trong Canva. Theo dõi tải xuống trong trình duyệt.'
            else:
                i=int(key)
                if i not in self.state['done']:self.state['done'].append(i)
                asset=body.get('asset')
                if asset and asset not in self.state['used']:self.state['used'].append(asset)
                msg=f'Đã dựng cảnh {i}/{len(self.state["scenes"])}: '+str(body.get('title',''))
            self.state['phase']={};self.running=None;self.log(msg);return dict(ok=True)

def serve(engine,port=8766):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*_):pass
        def send(self,status,value):
            raw=json.dumps(value,ensure_ascii=False).encode();self.send_response(status)
            self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
        def do_POST(self):
            if self.headers.get('Host') not in (f'127.0.0.1:{port}',f'localhost:{port}'):
                return self.send(403,dict(error='Host không hợp lệ'))
            if not secrets.compare_digest(self.headers.get('X-SKST-Token',''),engine.token):return self.send(401,dict(error='Mã kết nối không đúng.'))
            try:
                size=int(self.headers.get('Content-Length','0'))
                if not 0<size<200000:raise ValueError('Yêu cầu quá lớn.')
                body=json.loads(self.rfile.read(size))
                if self.path=='/next':v=engine.next_task(body)
                elif self.path=='/checkpoint':v=engine.check(body)
                elif self.path=='/result':v=engine.result(body)
                elif self.path=='/voice':
                    engine.check(body)
                    if not engine.running or engine.running['id']!='voice' or engine.state['mode']!='running':raise ValueError('Không có lệnh tải voice.')
                    path=Path(engine.state['voice'])
                    if path.stat().st_size>80*1024*1024:raise ValueError('Voice vượt 80 MB. Hãy chọn đoạn ngắn hơn.')
                    v=dict(name=path.name,data=base64.b64encode(path.read_bytes()).decode())
                elif self.path=='/ping':v=dict(ok=True,version=VERSION)
                else:return self.send(404,dict(error='Không tìm thấy'))
                self.send(200,v)
            except Exception as exc:self.send(400,dict(error=str(exc)))
    server=ThreadingHTTPServer(('127.0.0.1',port),Handler)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    return server
