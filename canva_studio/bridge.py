"""Authenticated loopback bridge. Stores no Canva cookies or passwords."""
import base64, hashlib, json, math, secrets, threading, time
from urllib.parse import urlsplit,parse_qs
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from .editorial import refine_queries,repair_scene_texts
from .downloads import verify_download
from .core import atomic_json, valid_canva, VERSION, repair_pending_keywords, describe,repair_tiny_scenes,project_title
MIN_EXTENSION_VERSION='0.14.5'

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
                repair_tiny_scenes(self.state.get('scenes',[]),self.state.get('done',[]))
                for part in self.state.get('parts',[])[self.state.get('part_index',0)+1:]:repair_tiny_scenes(part['scenes'])
                for row in self.state.get('scenes',[]):row.update(allow_all_media=True,real_people_only=False,negative=[])
                repair_scene_texts(self.state)
                repair_pending_keywords(self.state)
                refine_queries(self.state.get('scenes',[]),max([*self.state.get('done',[]),int(self.state.get('phase',{}).get('id',0)) if str(self.state.get('phase',{}).get('id','')).isdigit() else 0]))
                self.state['mode']='paused'; self.state['message']='Đã khôi phục dự án. Kiểm tra đúng thiết kế Canva trước khi tiếp tục.'
            except (ValueError,OSError):pass

    def save(self): atomic_json(self.path,self.state)
    def archive_project(self):
        with self.lock:
            if not self.state.get('scenes'):
                return
            folder=self.folder/'Projects'/'Previous'
            folder.mkdir(parents=True,exist_ok=True)
            atomic_json(folder/(secrets.token_hex(16)+'.json'),self.state)

    def latest_linked_archive(self):
        folder=self.folder/'Projects'/'Previous'
        for path in sorted(folder.glob('*.json'),key=lambda p:p.stat().st_mtime_ns,reverse=True):
            try:
                state=json.loads(path.read_text(encoding='utf8'))
                if (isinstance(state,dict) and isinstance(state.get('scenes'),list) and state['scenes']
                        and state.get('voice_done') and state.get('voice') and isinstance(state.get('target'),str)
                        and valid_canva(state['target'])):
                    return state
            except (OSError,ValueError,TypeError):
                continue
        raise ValueError('Chưa có bản lưu dự án đã liên kết với Canva.')

    def restore_linked_archive(self,state):
        with self.lock:
            if self.running or self.state['mode'] in ('running','opening','opening_resume'):
                raise ValueError('Tạm dừng và chờ thao tác Canva hiện tại kết thúc trước khi khôi phục.')
            self.archive_project()
            restored={**state,'mode':'paused','message':'Đã khôi phục bản dựng. Kiểm tra đúng thiết kế Canva trước khi tiếp tục.'}
            restored.pop('manual_review',None)
            atomic_json(self.path,restored)
            self.state=restored
            self.browser={}
            self.running=None

    def log(self,text):
        with self.lock:
            self.events.append(time.strftime('%H:%M:%S')+'  '+text);self.events=self.events[-250:]
            self.state['message']=text;self.save()
    def configure(self, plan, target, voice,allow_empty=False):
        with self.lock:
            name=project_title(plan.get('project_name',''))
            if self.state['mode']=='running':raise ValueError('Hãy tạm dừng trước khi đổi dự án.')
            if not valid_canva(target) and not (allow_empty and target==''):raise ValueError('Dán đường dẫn chỉnh sửa Canva hợp lệ.')
            self.state=dict(mode='ready',message='Đã sẵn sàng. Mở thiết kế video ngang trống trong Canva.',scenes=plan['scenes'],done=[],phase={},used=[],usage={},last_asset='',target=target,voice=str(voice),voice_done=False,export_done=False)
            self.state['parts']=plan.get('parts',[]);self.state['part_index']=0;self.state['history']=[];self.state['audit_done']=False
            self.state['original_voice']=plan.get('original_voice',str(voice))
            self.state['project_name']=name;self.state['named_title']=''
            for scene in self.state['scenes']:scene.update(real_people_only=False,allow_all_media=True,negative=[])
            refine_queries(self.state['scenes'])
            self.running=None;self.save()
    def set_project_name(self,name):
        with self.lock:
            name=project_title(name)
            if name==self.state.get('project_name',''):return
            if self.state['mode'] in ('running','opening','opening_resume'):raise ValueError('Tạm dừng dựng trước khi đổi tên dự án.')
            self.state['project_name']=name;self.state['named_title']='';self.state.pop('rename_failed_title',None);self.state.pop('rename_final_title',None);self.state.pop('rename_warning',None);self.save()
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

    def editor_status(self):
        from .browser import CREATE_VIDEO
        with self.lock:
            nonce=self.state.get('bootstrap_nonce','')
            return dict(create_url=CREATE_VIDEO+'#skst_start='+nonce if nonce and not self.state['target'] else '',bootstrap_nonce=nonce)
    def prepare_editor(self):
        with self.lock:
            if self.state.get('bootstrap_nonce') and not self.state['target'] and self.state['mode']=='attention':
                self.wait_for_created_tab()
            return dict(ok=True,target=self.state['target'],mode=self.state['mode'],**self.editor_status())

    def pause(self):
        with self.lock:self.state.pop('extension_resume_mode',None);self.state['mode']='paused';self.log('Đã tạm dừng. Thao tác đang thực hiện sẽ dừng ở điểm kiểm tra tiếp theo.')
    def start(self):
        with self.lock:
            if not self.state['scenes']:raise ValueError('Chưa có danh sách cảnh.')
            if len(self.state['scenes'])>50:raise ValueError('Bản thử hỗ trợ tối đa 50 cảnh mỗi dự án. Hãy chọn đoạn ngắn hơn.')
            if self.state.get('manual_edit_scene'):
                if not self.state.get('manual_review'):self.request_manual_review(self.state['manual_edit_scene'])
                else:
                    self.running=None;self.last_activity=time.time();self.state['mode']='running';self.log('Tiếp tục kiểm tra cảnh bạn đã tự sửa trên Canva…')
                return
            phase=self.state['phase'];scene=next((s for s in self.state['scenes'] if str(s['id'])==phase.get('id')),None)
            if scene and scene.get('error_card'):scene['error_card_attempts']=0
            if phase.get('stage') in ('insert_intent','rollback_intent') and scene:
                scene.setdefault('error_card',dict(message='Lần trước dừng giữa thao tác chèn cảnh; thay bằng ảnh báo lỗi để tiếp tục.',start=scene['start']))
                scene['error_recovery']=dict(phase);scene['error_card_attempts']=0;self.state['phase']={}
            elif phase.get('stage') in ('upload_intent','create_intent'):
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
    def begin_manual_edit(self,scene_id):
        with self.lock:
            self.pause()
            scene=next((s for s in self.state['scenes'] if s['id']==scene_id),None)
            if not scene or not self.state.get('voice_done') or not valid_canva(self.state['target']):raise ValueError('Chọn cảnh của dự án đang dựng, đã có voice.')
            pending=next((s['id'] for s in self.state['scenes'] if s['id'] not in self.state['done']),None)
            if scene_id not in self.state['done'] and scene_id!=pending:raise ValueError('Chọn cảnh đã dựng hoặc cảnh đang dở; chưa thể tự sửa một cảnh chưa đến lượt dựng.')
            self.state['manual_edit_scene']=scene_id;self.state.pop('manual_review',None);self.state.pop('manual_review_error',None)
            self.running=None;self.log(f'Đang chờ bạn tự sửa cảnh {scene_id} trên Canva. Sửa xong bấm Đã sửa trên Canva — tiếp tục.')
    def request_manual_review(self,scene_id):
        with self.lock:
            if self.state['mode'] in ('running','opening','opening_resume'):raise ValueError('Tạm dừng trước khi xác nhận cảnh tự sửa.')
            scene=next((s for s in self.state['scenes'] if s['id']==scene_id),None)
            if not scene or not self.state.get('voice_done') or not valid_canva(self.state['target']):raise ValueError('Chọn một cảnh trong dự án Canva đang dựng, đã có voice.')
            pending=next((s['id'] for s in self.state['scenes'] if s['id'] not in self.state['done']),None)
            if scene_id not in self.state['done'] and scene_id!=pending:raise ValueError('Cần hoàn tất các cảnh trước đoạn này, không bỏ qua khoảng trống.')
            self.state['manual_review']=dict(scene_id=scene_id,token=secrets.token_hex(12))
            self.state['manual_edit_scene']=scene_id
            self.state.pop('manual_review_error',None);self.running=None
            self.state['mode']='running';self.last_activity=time.time()
            self.log(f'Đang kiểm tra cảnh {scene_id} bạn đã sửa trên Canva; đạt yêu cầu sẽ tự dựng tiếp.')
    def next_task(self, body):
        with self.lock:
            now=time.time()
            if body.get('client') and valid_canva(canonical_url(body.get('url'))):
                self.peers={k:v for k,v in self.peers.items() if now-v['seen']<60}
                self.peers[body['client']]={**body,'seen':now}
                if now-self.last_diagnostic>5:
                    atomic_json(self.folder/'connection.json',dict(seen=now,url=body.get('url'),extension_version=body.get('extension_version'),mode=self.state['mode']))
                    self.last_diagnostic=now
            marker=parse_qs(urlsplit(body.get('url','')).fragment).get('skst_start',[''])[0]
            pending=self.state.get('extension_resume_mode')
            opening=self.state['mode'] in ('opening','opening_resume')
            exact=(bool(marker) and marker==self.state.get('bootstrap_nonce')) if (self.state['mode']=='opening' or pending=='opening') else bool(self.state['target']) and canonical_url(body.get('url'))==canonical_url(self.state['target'])
            if opening and exact and not compatible_extension(body.get('extension_version')):
                self.state['extension_resume_mode']=self.state['mode']
                self.state['mode']='attention'
                self.log('Canva đang chạy tiện ích '+str(body.get('extension_version','không rõ'))+'; đang chờ nạp bản '+MIN_EXTENSION_VERSION+' từ thư mục ứng dụng. Giữ nguyên tab; không tạo lại thiết kế.')
                return dict(task=None,mode='extension_outdated',message=self.state['message'])
            if pending and self.state['mode']=='attention' and exact and compatible_extension(body.get('extension_version')):
                self.state['mode']=self.state.pop('extension_resume_mode')
                self.state['bootstrap_deadline']=now+120
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
            if self.state['mode']!='running':return dict(task=None,mode=self.state['mode'],message=self.state['message'])
            old=self.browser
            if old and old.get('client')!=body.get('client') and time.time()-old.get('seen',0)<15:
                return dict(task=None,mode='other_client')
            self.browser={**body,'seen':time.time()}
            if self.running and self.running['client']!=body.get('client'):return dict(task=None,mode='busy')
            title=project_title(self.state.get('project_name',''),self.state.get('part_index',0))
            manual=self.state.get('manual_review')
            if manual:
                scene=next(s for s in self.state['scenes'] if s['id']==manual['scene_id'])
                counts={max([scene['id'],*self.state['done']])}
                phase=self.state.get('phase',{})
                if str(phase.get('id','')).isdigit() and phase.get('stage') in ('insert_intent','inserted','trimmed','muted'):
                    counts.add(max(max(counts),int(phase['id'])))
                name=self.state.get('voice_name','')
                if not name and Path(self.state['voice']).is_file():
                    with Path(self.state['voice']).open('rb') as file:name='SKST_voice_'+hashlib.file_digest(file,'sha256').hexdigest()[:16]+Path(self.state['voice']).suffix.lower()
                manual.update(allowed_counts=sorted(counts),voice_name=name)
                task=dict(id=f'manual:{scene["id"]}',kind='manual_review',review_token=manual['token'],scene=scene,allowed_counts=sorted(counts),voice_name=name,voice_duration=self.state['scenes'][-1]['start']+self.state['scenes'][-1]['duration'])
            elif title and self.state.get('named_title')!=title and (self.state.get('rename_failed_title')!=title or self.state.get('audit_done') and self.state.get('rename_final_title')!=title):task=dict(id='rename',kind='rename',design_name=title)
            elif not self.state['voice_done']: task=dict(id='voice',kind='voice',name='SKST_Voice.mp3')
            else:
                scene=next((s for s in self.state['scenes'] if s['id'] not in self.state['done']),None)
                if scene:task=dict(id=str(scene['id']),kind='scene',scene=scene,used=self.state['used'],usage=self.state.get('usage',{}),last_asset=self.state.get('last_asset',''),previous_scene=next((s for s in self.state['scenes'] if s['id']==scene['id']-1),None))
                elif not self.state.get('audit_done'):
                    name=self.state.get('voice_name','')
                    if not name and Path(self.state['voice']).is_file():
                        with Path(self.state['voice']).open('rb') as file:name='SKST_voice_'+hashlib.file_digest(file,'sha256').hexdigest()[:16]+Path(self.state['voice']).suffix.lower()
                        self.state['voice_name']=name;self.save()
                    task=dict(id='audit',kind='audit',voice_name=name,count=len(self.state['scenes']),duration=round(self.state['scenes'][-1]['start']+self.state['scenes'][-1]['duration'],3))
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
            if str(body.get('id')).startswith('manual:') and body.get('review_token')!=self.state.get('manual_review',{}).get('token'):raise ValueError('Yêu cầu kiểm tra tự sửa đã được thay thế.')
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
            if str(body.get('id')).startswith('manual:') and body.get('review_token')!=self.state.get('manual_review',{}).get('token'):raise ValueError('Yêu cầu kiểm tra tự sửa đã được thay thế.')
            if body.get('error'):
                if str(body['id']).startswith('manual:'):
                    detail=str(body['error'])[:600];self.state.update(mode='attention',manual_review_error=detail);self.running=None
                    self.log('Cảnh tự sửa chưa đạt: '+detail+' Sửa lại trên Canva rồi bấm Đã sửa trên Canva — tiếp tục.');return dict(ok=True)
                key=str(body['id']);scene=next((s for s in self.state['scenes'] if str(s['id'])==key),None)
                phase=self.state.get('phase',{});stage=phase.get('stage','chưa chèn cảnh')
                detail=str(body['error'])[:600]
                record=dict(id=key,part=self.state.get('part_index',0)+1,start=scene.get('source_start',scene['start']) if scene else None,duration=scene.get('duration') if scene else None,stage=stage,message=detail,target=self.state['target'])
                self.state.setdefault('errors',[]).append(record)
                atomic_json(self.folder/'Errors.json',self.state['errors'])
                # A missing/search/UI failure before insertion can be replaced safely.
                # Never mark a gap complete, or retry a click with an uncertain outcome.
                safe=scene and self.state['mode']=='running'
                cancelled=any(t in detail.lower() for t in ('đã tạm dừng','phiên thao tác','mã kết nối','đã ngắt'))
                if safe and not cancelled:
                    if not scene.get('error_card'):
                        scene['error_card']=record
                        scene['error_recovery']=dict(phase)
                        scene['error_card_attempts']=0
                        scene.pop('fallback_path',None);scene.pop('fallback_source',None)
                        self.state['phase']={}
                    else:scene['error_card_attempts']=scene.get('error_card_attempts',0)+1
                    self.running=None
                    if scene.get('error_card_attempts',0)<3:
                        self.log(f'Cảnh {key} lỗi. Đang thay bằng một ảnh báo lỗi đúng thời lượng; sau đó chuyển cảnh tiếp theo.')
                        return dict(ok=True,continuing=True)
                    self.state['mode']='attention'
                    self.log(f'Không thể thao tác timeline để đặt ảnh lỗi cảnh {key} sau 3 lần phục hồi: {detail}. Tiến độ và voice được giữ nguyên.')
                    return dict(ok=True)
                self.state['mode']='paused' if cancelled else 'attention';self.running=None
                self.log(f'Cảnh/tác vụ {key} • bước {stage}: {detail}. Chưa thể chèn thẻ lỗi vì chưa xác nhận được trạng thái timeline.' if not cancelled else detail)
                return dict(ok=True)
            key=str(body['id'])
            if key.startswith('manual:'):
                review=self.state.get('manual_review',{});scene=next((s for s in self.state['scenes'] if s['id']==review.get('scene_id')),None)
                if not scene or key!=f'manual:{scene["id"]}' or body.get('manual_verified') is not True:raise ValueError('Chưa xác nhận đúng cảnh tự sửa.')
                values=[float(body.get(k,-1)) for k in ('verified_start','verified_end','verified_voice_start','verified_voice_end')]
                total=self.state['scenes'][-1]['start']+self.state['scenes'][-1]['duration']
                if not all(map(math.isfinite,values)) or values[1]<=values[0]:raise ValueError('Chưa đọc được khoảng thời gian cảnh tự sửa.')
                if body.get('verified_count') not in review.get('allowed_counts',[]) or not review.get('voice_name') or body.get('voice_name')!=review['voice_name'] or abs(values[2])>.12 or abs(values[3]-total)>.12:raise ValueError('Số cảnh hoặc voice đã thay đổi; chưa thể tiếp tục.')
                from .manual_timing import compensate
                frames=body.get('frames',[])
                if len(frames)!=body['verified_count']:raise ValueError('Chưa đọc đủ mốc các cảnh trên timeline.')
                selected=frames[scene['id']-1]
                if abs(float(selected['start'])-values[0])>.001 or abs(float(selected['end'])-values[1])>.001:raise ValueError('Mốc cảnh tự sửa không thống nhất; hãy xác nhận lại.')
                completed=set(self.state['done'])|{scene['id']}
                updates=compensate(self.state['scenes'],completed,frames)
                for item,update in zip(self.state['scenes'],updates):item.update(update)
                scene['manual_verified']=True;scene['manual_asset']=str(body.get('asset','manual:'+str(scene['id'])));scene['manual_actual_start']=values[0];scene['manual_actual_end']=values[1]
                if scene['id'] not in self.state['done']:self.state['done'].append(scene['id']);self.state['done'].sort()
                if self.state['phase'].get('id')==str(scene['id']):self.state['phase']={}
                self.state.pop('manual_review',None);self.state.pop('manual_review_error',None);self.state.pop('manual_edit_scene',None)
                self.state['audit_done']=False;self.state['export_done']=False
                asset=scene['manual_asset']
                if asset not in self.state['used']:self.state['used'].append(asset)
                self.running=None;self.log(f'Đã giữ thời lượng cảnh {scene["id"]} bạn tự sửa; phần chênh lệch được bù vào các cảnh dựng tiếp theo.');return dict(ok=True)
            if key=='rename':
                expected=project_title(self.state.get('project_name',''),self.state.get('part_index',0))
                if not expected or body.get('design_name')!=expected:raise ValueError('Tên Canva chưa khớp tên phần hiện tại.')
                if body.get('rename_warning'):
                    warning=str(body['rename_warning'])[:400]
                    if self.state.get('audit_done'):self.state['rename_final_title']=expected
                    self.state['rename_failed_title']=expected;self.state['rename_warning']=warning;self.running=None
                    self.log('Chưa đổi được tên Canva; vẫn tiếp tục dựng. '+warning);return dict(ok=True)
                self.state.pop('rename_warning',None);self.state.pop('rename_failed_title',None);self.state.pop('rename_final_title',None)
                self.state['named_title']=expected;self.running=None
                self.log('Đã đặt tên Canva: '+expected)
                # Renaming must not erase the checkpoint of an interrupted scene.
                return dict(ok=True)
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
                refine_queries(part['scenes'])
                self.state.update(part_index=index,target=target,voice=part['voice'],voice_name='',named_title='',scenes=part['scenes'],done=[],voice_done=False,export_done=False,audit_done=False)
                self.state.pop('rename_warning',None);self.state.pop('rename_failed_title',None);self.state.pop('rename_final_title',None)
                repair_scene_texts(self.state);refine_queries(self.state['scenes'])
                self.browser={};msg=f'Chuyển phần {index+1}: voice gốc từ giây {part["source_start"]:.3f}.'
            elif key=='voice':
                self.state['voice_done']=True;self.state['voice_name']=body.get('voice_name','');msg='Đã đặt voice trên timeline.'
            elif key=='export':
                if body.get('download_complete') is not True or type(body.get('download_id')) is not int or body['download_id']<0:raise ValueError('Chưa xác nhận MP4 tải xuống hoàn tất.')
                from .storage import application_dir
                try:settings=json.loads((self.folder/'settings.json').read_text(encoding='utf8'))
                except (OSError,ValueError):settings={}
                expected=self.state['scenes'][-1]['start']+self.state['scenes'][-1]['duration']
                self.state['download_verified']=verify_download(body.get('download_path',''),settings.get('ffmpeg') or application_dir()/'CongCu/ffmpeg.exe',expected)
                self.state['export_done']=True;self.state['mode']='complete';self.state['download_id']=body['download_id'];msg='Đã xác nhận MP4 tải xuống hoàn tất.'
            else:
                i=int(key)
                if i not in self.state['done']:self.state['done'].append(i)
                completed=next((s for s in self.state['scenes'] if s['id']==i),{})
                asset=body.get('asset') or completed.get('fallback_source',{}).get('id')
                if completed.get('fallback_source'):
                    sources=self.state.setdefault('sources',[])
                    if completed['fallback_source'] not in sources:sources.append(completed['fallback_source'])
                    atomic_json(self.folder/'Sources.json',sources)
                if asset:
                    usage=self.state.setdefault('usage',{})
                    usage[asset]=usage.get(asset,1 if asset in self.state['used'] else 0)+1
                    self.state['last_asset']=asset
                    if asset not in self.state['used']:self.state['used'].append(asset)
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
                elif self.path=='/fallback':
                    from .fallback import begin_fallback
                    engine.check(body)
                    scene=next((s for s in engine.state['scenes'] if str(s['id'])==str(body.get('id'))),None)
                    if engine.state['mode']!='running' or not scene:raise ValueError('Không có lệnh chuẩn bị tư liệu.')
                    if scene.get('error_card'):
                        error=scene['error_card']
                        v=dict(error_text=f"LỖI CẢNH {scene['id']} • {scene['start']:.2f}–{scene['start']+scene['duration']:.2f} giây\n{error['message'][:600]}\nLời đọc: {scene['text'][:400]}",name=f"SKST_error_{scene['id']}_{hashlib.sha256(str(error).encode()).hexdigest()[:12]}.png",asset_id=f"error:{scene['id']}")
                        self.send(200,v);return
                    with engine.lock:status=begin_fallback(engine,scene,retry=body.get('retry') is True)
                    if status.get('error'):raise ValueError(status['error'])
                    if status.get('pending'):v=dict(pending=True)
                    else:
                        path=Path(scene['fallback_path']).resolve()
                        if not path.is_relative_to((engine.folder/'Projects').resolve()) or path.suffix not in ('.mp4','.png') or path.stat().st_size>30*1024*1024:raise ValueError('Tệp tư liệu không hợp lệ.')
                        v=dict(name=path.name,mime='image/png' if path.suffix=='.png' else 'video/mp4',data=base64.b64encode(path.read_bytes()).decode(),asset_id=scene['fallback_source']['id'])
                elif self.path=='/title':
                    engine.check(body)
                    scene=next((s for s in engine.state['scenes'] if str(s['id'])==str(body.get('id'))),None)
                    if engine.state['mode']!='running' or not scene or scene.get('kind')!='title':raise ValueError('Không có lệnh tải tiêu đề.')
                    path=Path(scene['title_path']).resolve();root=(engine.folder/'Projects').resolve()
                    if not path.is_relative_to(root) or path.suffix.lower()!='.mp4' or path.stat().st_size>12*1024*1024:raise ValueError('Tệp tiêu đề không hợp lệ.')
                    payload=path.read_bytes();v=dict(name=path.name,mime='video/mp4',data=base64.b64encode(payload).decode())
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
                elif self.path=='/prepare_editor':v=engine.prepare_editor()
                elif self.path=='/ping':v=dict(ok=True,version=VERSION,mode=engine.state['mode'],active_task=bool(engine.running),message=engine.state['message'],target=engine.state['target'],connection=engine.connection_status(),**engine.editor_status())
                else:return self.send(404,dict(error='Không tìm thấy'))
                self.send(200,v)
            except Exception as exc:self.send(400,dict(error=str(exc)))
    server=ThreadingHTTPServer(('127.0.0.1',port),Handler)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    return server
