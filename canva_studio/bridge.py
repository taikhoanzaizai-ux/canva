"""Authenticated loopback bridge. Stores no Canva cookies or passwords."""
import base64, hashlib, json, secrets, threading, time
from urllib.parse import urlsplit,parse_qs
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from .core import atomic_json, valid_canva, VERSION, repair_pending_keywords, describe
MIN_EXTENSION_VERSION='0.3.1'

def canonical_url(value):return str(value or '').split('?')[0].split('#')[0]

def compatible_extension(value):
    try:return tuple(int(p) for p in value.split('.'))>=tuple(int(p) for p in MIN_EXTENSION_VERSION.split('.'))
    except (AttributeError,ValueError):return False

class Engine:
    def __init__(self, folder):
        self.folder=Path(folder);self.folder.mkdir(parents=True,exist_ok=True)
        self.lock=threading.RLock()
        token_path=self.folder/'pairing.json'
        try:
            self.token=json.loads(token_path.read_text(encoding='utf8'))['token']
            if not isinstance(self.token,str) or len(self.token)<30:raise ValueError('Invalid pairing token')
        except (OSError,ValueError,KeyError,TypeError):
            self.token=secrets.token_urlsafe(24);atomic_json(token_path,dict(token=self.token))
        self.state=dict(mode='idle',message='Chọn voice để bắt đầu.',scenes=[],done=[],phase={},used=[],target='',voice='',voice_done=False,export_done=False)
        self.browser={}; self.peers={};self.running=None;self.last_activity=0;self.last_diagnostic=0
        self.events=[]
        self.path=self.folder/'project.json'
        if self.path.exists():
            try:
                self.state.update(json.loads(self.path.read_text(encoding='utf8')))
                repair_pending_keywords(self.state)
                self.state['mode']='paused'; self.state['message']='Đã khôi phục dự án. Kiểm tra đúng thiết kế Canva trước khi tiếp tục.'
            except (ValueError,OSError):pass

    def save(self): atomic_json(self.path,self.state)
    def log(self,text):
        with self.lock:
            self.events.append(time.strftime('%H:%M:%S')+'  '+text);self.events=self.events[-250:]
            self.state['message']=text;self.save()
    def configure(self, plan, target, voice,allow_empty=False):
        with self.lock:
            if self.state['mode']=='running':raise ValueError('Hãy tạm dừng trước khi đổi dự án.')
            if not valid_canva(target) and not (allow_empty and target==''):raise ValueError('Dán đường dẫn chỉnh sửa Canva hợp lệ.')
            self.state=dict(mode='ready',message='Đã sẵn sàng. Mở thiết kế video ngang trống trong Canva.',scenes=plan['scenes'],done=[],phase={},used=[],target=target,voice=str(voice),voice_done=False,export_done=False)
            self.state['parts']=plan.get('parts',[]);self.state['part_index']=0;self.state['history']=[];self.state['audit_done']=False
            self.state['original_voice']=plan.get('original_voice',str(voice))
            for scene in self.state['scenes']:scene.update(real_people_only=True)
            self.running=None;self.save()
    def bootstrap(self,plan,voice):
        from .browser import CREATE_VIDEO
        with self.lock:
            if self.state['mode']=='opening':raise ValueError('Chrome đang tạo thiết kế; không bấm lặp để tránh tạo trùng.')
            if not plan.get('scenes') or len(plan['scenes'])>50:raise ValueError('Cần phân tích và chia phần tối đa 50 cảnh trước.')
            self.configure(plan,'',voice,allow_empty=True)
            nonce=secrets.token_urlsafe(18)
            self.state.update(mode='opening',bootstrap_nonce=nonce,bootstrap_deadline=time.time()+120,auto_start=True)
            self.log('Đang mở Chrome và tạo Video khổ ngang. Chờ tiện ích nhận thiết kế mới…')
            return CREATE_VIDEO+'#skst_start='+nonce

    def wait_for_created_tab(self):
        with self.lock:
            if not self.state.get('bootstrap_nonce') or self.state.get('target'):raise ValueError('Không có tab đang chờ.')
            self.state.update(mode='opening',bootstrap_deadline=time.time()+120)
            self.log('Đang chờ lại tab Canva đã tạo. Giữ tab đó mở và kết nối tiện ích; không tạo thêm tab trùng.')

    def resume_in_chrome(self):
        with self.lock:
            self.start()
            self.state.update(mode='opening_resume',bootstrap_deadline=time.time()+120,auto_start=True)
            self.log('Đang mở lại đúng thiết kế trong Chrome để tiếp tục tiến độ…')

    def pause(self):
        with self.lock:self.state['mode']='paused';self.log('Đã tạm dừng. Thao tác đang thực hiện sẽ dừng ở điểm kiểm tra tiếp theo.')
    def start(self):
        with self.lock:
            if not self.state['scenes']:raise ValueError('Chưa có danh sách cảnh.')
            if len(self.state['scenes'])>50:raise ValueError('Bản thử hỗ trợ tối đa 50 cảnh mỗi dự án. Hãy chọn đoạn ngắn hơn.')
            if self.state['phase'].get('stage') in ('insert_intent','upload_intent','export_intent','create_intent'):
                raise ValueError('Lần trước dừng giữa thao tác. Kiểm tra Canva rồi dùng nút Xử lý cảnh bị dở; ứng dụng sẽ không tự chèn trùng.')
            self.running=None;self.last_activity=time.time();self.state['mode']='running';self.log('Đang chờ tiện ích kết nối đúng thiết kế Canva…')
    def connection_status(self,target=None):
        with self.lock:
            now=time.time();fresh=[p for p in self.peers.values() if now-p.get('seen',0)<12]
            url=canonical_url(target or self.state['target'])
            matching=[p for p in fresh if not url or canonical_url(p.get('url'))==url]
            ready=next((p for p in sorted(matching,key=lambda p:p['seen'],reverse=True) if compatible_extension(p.get('extension_version'))),None)
            if ready:return dict(ready=True,code='ready',message='Đã kết nối tab Canva • '+ready.get('title',''),peer=ready)
            if matching:return dict(ready=False,code='outdated',message='Tiện ích đang cũ. Bấm Cập nhật tiện ích để nạp SKST '+MIN_EXTENSION_VERSION+' rồi kết nối lại.')
            if fresh:return dict(ready=False,code='wrong_design',message='Tiện ích đang ở thiết kế khác. Mở đúng link trong ứng dụng rồi bấm Kết nối Canva trên tiện ích.')
            return dict(ready=False,code='disconnected',message='Chưa có tín hiệu từ tab Canva. Mở tiện ích SKST trên tab Canva, dán mã của phiên này và bấm Kết nối Canva.')
    def watchdog(self,now=None):
        with self.lock:
            now=time.time() if now is None else now
            if self.state['mode'] in ('opening','opening_resume') and now>self.state.get('bootstrap_deadline',0):
                self.state['mode']='attention'
                self.log('Chưa nhận được tab mới. Kiểm tra Chrome đã đăng nhập Canva, tiện ích đã bật và ghép nối. Giữ tab mới để thử lại bằng link; không tự tạo thêm tab.')
            if self.state['mode']=='running' and now-self.last_activity>25:
                self.state['mode']='attention'
                self.log('Mất tín hiệu từ tiện ích Canva. Bấm Kết nối Canva trên tiện ích rồi Bắt đầu/Tiếp tục; tiến độ đã được giữ.')
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
            now=time.time()
            if body.get('client') and valid_canva(canonical_url(body.get('url'))):
                self.peers={k:v for k,v in self.peers.items() if now-v['seen']<60}
                self.peers[body['client']]={**body,'seen':now}
                if now-self.last_diagnostic>5:
                    atomic_json(self.folder/'connection.json',dict(seen=now,url=body.get('url'),extension_version=body.get('extension_version'),mode=self.state['mode']))
                    self.last_diagnostic=now
            if self.state['mode']=='opening':
                marker=parse_qs(urlsplit(body.get('url','')).fragment).get('skst_start',[''])[0]
                if marker!=self.state.get('bootstrap_nonce') or not marker:return dict(task=None,mode='waiting_new_design')
                if not compatible_extension(body.get('extension_version')):return dict(task=None,mode='extension_outdated')
                if not body.get('blank_video') or not valid_canva(canonical_url(body.get('url'))):return dict(task=None,mode='waiting_empty_video')
                self.state.update(target=canonical_url(body['url']),mode='running',bootstrap_nonce='')
                self.last_activity=now;self.log('Đã nhận Video khổ ngang mới. Bắt đầu tải voice và dựng cảnh.')
            if canonical_url(body.get('url'))!=canonical_url(self.state['target']):return dict(task=None,mode='wrong_design')
            if not compatible_extension(body.get('extension_version')):
                message='Cần cài tiện ích SKST '+MIN_EXTENSION_VERSION+' từ thư mục TienIch_Canva cạnh ứng dụng, rồi kết nối lại trên tab Canva.'
                if self.state['mode']=='running' and self.state['message']!=message:self.log(message)
                return dict(task=None,mode='extension_outdated')
            if self.state['mode']=='opening_resume':
                self.state['mode']='running';self.last_activity=now;self.log('Đã nối lại Chrome. Tiếp tục tiến độ đã lưu.')
            if self.state['mode']!='running':return dict(task=None,mode=self.state['mode'])
            old=self.browser
            if old and old.get('client')!=body.get('client') and time.time()-old.get('seen',0)<15:
                return dict(task=None,mode='other_client')
            self.browser={**body,'seen':time.time()}
            if self.running and self.running['client']!=body.get('client'):return dict(task=None,mode='busy')
            if not self.state['voice_done']: task=dict(id='voice',kind='voice',name='SKST_Voice.mp3')
            else:
                scene=next((s for s in self.state['scenes'] if s['id'] not in self.state['done']),None)
                if scene:task=dict(id=str(scene['id']),kind='scene',scene=scene,used=self.state['used'])
                elif not self.state.get('audit_done'):task=dict(id='audit',kind='audit',count=len(self.state['scenes']),duration=round(self.state['scenes'][-1]['start']+self.state['scenes'][-1]['duration'],3))
                elif self.state.get('part_index',0)+1<len(self.state.get('parts',[])):task=dict(id='next_design',kind='next_design')
                elif not self.state['export_done']:task=dict(id='export',kind='export')
                else:return dict(task=None,mode='complete')
            task['phase']=self.state['phase'] if self.state['phase'].get('id')==task['id'] else {}
            self.running=dict(id=task['id'],client=body.get('client'))
            self.last_activity=now
            return dict(task=task,mode='running')
    def check(self, body):
        with self.lock:
            if not self.running or self.running['id']!=str(body.get('id')) or self.running['client']!=body.get('client'):raise ValueError('Phiên thao tác không còn hợp lệ.')
            if self.state['mode']!='running':return dict(continue_=False)
            self.last_activity=time.time()
            if body.get('client') in self.peers:self.peers[body['client']]['seen']=self.last_activity
            if self.browser.get('client')==body.get('client'):self.browser['seen']=self.last_activity
            stage=body.get('stage')
            if stage in ('create_intent','create_open') and str(body.get('id'))!='next_design':raise ValueError('Không có lệnh mở thiết kế tiếp theo.')
            if stage:
                self.state['phase']={**body,'id':str(body['id'])}; self.save()
            return dict(continue_=True)
    def result(self, body):
        with self.lock:
            if not self.running or self.running['id']!=str(body.get('id')) or self.running['client']!=body.get('client'):raise ValueError('Kết quả không thuộc phiên đang chạy.')
            if body.get('error'):
                self.state['mode']='attention';self.running=None;self.log('Cần kiểm tra: '+str(body['error'])[:1200]);return dict(ok=True)
            key=str(body['id'])
            if key=='audit':
                scenes=self.state['scenes'];duration=round(scenes[-1]['start']+scenes[-1]['duration'],3)
                if len(self.state['done'])!=len(scenes) or body.get('verified_count')!=len(scenes) or abs(float(body.get('verified_duration',-1))-duration)>.12:raise ValueError('Chưa xác nhận đủ cảnh và voice phần hiện tại.')
                self.state['audit_done']=True;msg='Đã kiểm tra đủ cảnh và thời lượng voice.'
            elif key=='next_design':
                target=body.get('new_target','')
                if not valid_canva(target) or canonical_url(target)==canonical_url(self.state['target']):raise ValueError('Thiết kế tiếp theo không hợp lệ.')
                if not self.state.get('audit_done'):raise ValueError('Chưa kiểm tra xong phần hiện tại.')
                index=self.state.get('part_index',0)+1
                if index>=len(self.state.get('parts',[])):raise ValueError('Không còn voice tiếp theo.')
                self.state.setdefault('history',[]).append(dict(target=self.state['target'],voice=self.state['voice'],scenes=self.state['scenes'],source_start=self.state['parts'][index-1]['source_start'],duration=self.state['parts'][index-1]['duration']))
                part=self.state['parts'][index]
                self.state.update(part_index=index,target=target,voice=part['voice'],scenes=part['scenes'],done=[],voice_done=False,export_done=False,audit_done=False)
                self.browser={};msg=f'Chuyển phần {index+1}: voice gốc từ giây {part["source_start"]:.3f}.'
            elif key=='voice':self.state['voice_done']=True;msg='Đã đặt voice trên timeline.'
            elif key=='export':self.state['export_done']=True;self.state['mode']='complete';msg='Đã gửi lệnh xuất MP4 trong Canva. Theo dõi tải xuống trong trình duyệt.'
            else:
                i=int(key)
                if i not in self.state['done']:self.state['done'].append(i)
                asset=body.get('asset')
                if asset and asset not in self.state['used']:self.state['used'].append(asset)
                msg=f'Đã dựng cảnh {i}/{len(self.state["scenes"])}: '+str(body.get('title',''))
            self.state['phase']={};self.running=None;self.log(msg);return dict(ok=True,handoff=key=='next_design',target=self.state['target'])

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
                    payload=path.read_bytes();suffix=path.suffix.lower()
                    mime={'.mp3':'audio/mpeg','.wav':'audio/wav','.m4a':'audio/mp4','.aac':'audio/aac','.flac':'audio/flac'}.get(suffix,'audio/mpeg')
                    v=dict(name='SKST_voice_'+hashlib.sha256(payload).hexdigest()[:16]+suffix,mime=mime,data=base64.b64encode(payload).decode())
                elif self.path=='/companion/update':
                    from .companion import update_manifest
                    from .storage import application_dir
                    with engine.lock:
                        if engine.state['mode']=='running' or engine.running:raise ValueError('Hãy chờ tác vụ kết thúc hoặc tạm dừng trước khi cập nhật tiện ích.')
                        v=dict(manifest=update_manifest(application_dir(),body.get('extension_id')),mode=engine.state['mode'],active_task=False)
                elif self.path=='/ping':v=dict(ok=True,version=VERSION,mode=engine.state['mode'],active_task=bool(engine.running),message=engine.state['message'],target=engine.state['target'],connection=engine.connection_status())
                else:return self.send(404,dict(error='Không tìm thấy'))
                self.send(200,v)
            except Exception as exc:self.send(400,dict(error=str(exc)))
    server=ThreadingHTTPServer(('127.0.0.1',port),Handler)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    return server
