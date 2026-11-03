from __future__ import annotations
import json, os, queue, uuid, shutil, subprocess, sys, tempfile, threading, time, webbrowser
from pathlib import Path
if getattr(sys,'frozen',False):
    # Tcl caches library directories when _tkinter is first imported.
    os.chdir(sys._MEIPASS)
    os.environ['TCL_LIBRARY']='_tcl_data';os.environ['TK_LIBRARY']='_tk_data'
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from canva_studio.core import VERSION, load_transcript, read_script, make_plan, atomic_json, valid_canva, align_script
from canva_studio.bridge import Engine, serve, compatible_extension, MIN_EXTENSION_VERSION
from canva_studio.editorial import add_title_cards,render_titles,neighboring_script
from canva_studio.browser import open_chrome,chrome_path
from canva_studio.batches import probe_duration, prepare_parts, cached_transcript
from canva_studio import updater
from canva_studio.storage import data_dir, migrate_legacy
from canva_studio.storage import application_dir
from canva_studio.companion import companion_status
from canva_studio.recognizer import paths as recognizer_paths,ensure_recognizer,command as recognition_command,convert_output

BASE=Path(getattr(sys,'_MEIPASS',Path(__file__).resolve().parent.parent))
DATA=data_dir()
NO_WINDOW=0x08000000 if os.name=='nt' else 0

class App:
    def __init__(self,root):
        self.root=root;root.title('SKST Canva Studio • Bản thử '+VERSION);root.geometry('1130x820');root.minsize(940,700)
        legacy=Path(os.environ.get('LOCALAPPDATA',Path.home()))/'SKST Canva Studio'
        imported=0
        if '--self-test' not in sys.argv:
            try:imported=migrate_legacy(DATA,legacy)
            except (OSError,ValueError) as e:messagebox.showwarning('Dữ liệu cũ',str(e)+'\nDữ liệu gốc vẫn được giữ. Bạn có thể chuyển lại sau.')
        self.engine=Engine(DATA); self.server=serve(self.engine,int(os.environ.get('SKST_PORT','8766')));self.tasks=queue.Queue();self.worker_busy=False;self.process=None
        self.segments=None;self.plan=None;self.settings={};self.prepared_voice='';self.update_busy=False;self.analyze_then_run=False
        try:self.settings=json.loads((DATA/'settings.json').read_text(encoding='utf8'))
        except (OSError,ValueError):pass
        style=ttk.Style();style.theme_use('clam');style.configure('.',font=('Segoe UI',10));style.configure('TFrame',background='#f3f5fa');style.configure('TLabel',background='#f3f5fa',foreground='#18243b');style.configure('TButton',padding=(12,7));style.configure('Accent.TButton',background='#196c68',foreground='white');style.configure('Treeview',rowheight=31)
        outer=ttk.Frame(root,padding=20);outer.pack(fill='both',expand=True)
        header=ttk.Frame(outer);header.pack(fill='x')
        ttk.Label(header,text='SKST  /  Canva Studio',font=('Segoe UI',23,'bold')).pack(side='left')
        self.update_button=ttk.Button(header,text='Kiểm tra cập nhật',command=self.check_update);self.update_button.pack(side='right')
        ttk.Label(outer,text='Voice của bạn → cảnh ngắn sát lời đọc → dựng trong kho Canva',foreground='#55657c').pack(anchor='w',pady=(2,16))
        tabs=ttk.Notebook(outer);tabs.pack(fill='both',expand=True)
        build=ttk.Frame(tabs,padding=14);settings=ttk.Frame(tabs,padding=18);help_tab=ttk.Frame(tabs,padding=18)
        tabs.add(build,text='  Dựng video  ');tabs.add(settings,text='  Kết nối & công cụ  ');tabs.add(help_tab,text='  Hướng dẫn  ')
        self.voice=tk.StringVar(value=self.settings.get('voice',''));self.script_path=tk.StringVar();self.transcript=tk.StringVar(value=self.settings.get('transcript',''))
        for label,var,command in [('Voice MP3 / WAV',self.voice,self.choose_voice),('Kịch bản DOCX / TXT',self.script_path,self.choose_script),('Lời đọc có thời gian (tùy chọn)',self.transcript,self.choose_transcript)]:
            row=ttk.Frame(build);row.pack(fill='x',pady=3);ttk.Label(row,text=label,width=29).pack(side='left');ttk.Entry(row,textvariable=var).pack(side='left',fill='x',expand=True);ttk.Button(row,text='Chọn…',command=command).pack(side='left',padx=(8,0))
        self.script=tk.Text(build,height=3,wrap='word',font=('Segoe UI',10),relief='flat',padx=8,pady=7);self.script.pack(fill='x',pady=7)
        self.script.insert('1.0','')
        row=ttk.Frame(build);row.pack(fill='x',pady=6)
        self.start=tk.StringVar(value='0');self.end=tk.StringVar(value='');self.opening=tk.StringVar(value='35')
        for label,var in [('Từ giây',self.start),('Đến giây (trống = hết)',self.end),('Mở đầu dựng kỹ (giây)',self.opening)]:
            ttk.Label(row,text=label).pack(side='left',padx=(0,6));ttk.Entry(row,textvariable=var,width=8).pack(side='left',padx=(0,15))
        self.plan_button=ttk.Button(row,text='1. Phân tích & chia cảnh',style='Accent.TButton',command=self.analyze);self.plan_button.pack(side='right')
        self.notice=tk.StringVar(value='Video/ảnh đúng chủ đề • Tự chia 50 cảnh/phần • Để trống Đến giây để dựng hết voice gốc.')
        ttk.Label(build,textvariable=self.notice,foreground='#85601d',wraplength=1000).pack(anchor='w',pady=5)
        frame=ttk.Frame(build);frame.pack(fill='both',expand=True)
        self.tree=ttk.Treeview(frame,columns=('time','text','query'),show='headings',selectmode='browse',height=4)
        for name,title,width in [('time','Thời gian',125),('text','Lời đọc',480),('query','Từ khóa Canva',300)]:self.tree.heading(name,text=title);self.tree.column(name,width=width)
        self.tree.pack(side='left',fill='both',expand=True);sb=ttk.Scrollbar(frame,orient='vertical',command=self.tree.yview);sb.pack(side='right',fill='y');self.tree.configure(yscrollcommand=sb.set)
        self.tree.bind('<Double-1>',self.edit_scene)
        row=ttk.Frame(build);row.pack(fill='x',pady=9)
        ttk.Button(row,text='Sửa từ khóa cảnh',command=self.edit_scene).pack(side='left');ttk.Button(row,text='Lưu danh sách cảnh',command=self.export_plan).pack(side='left',padx=6);ttk.Button(row,text='Nạp danh sách cảnh',command=self.import_plan).pack(side='left');ttk.Button(row,text='Mẫu Nhón gót chân',command=self.load_demo).pack(side='right')
        row=ttk.Frame(build);row.pack(fill='x',pady=3);ttk.Label(row,text='Link Canva (trống = tự tạo)').pack(side='left');self.target=tk.StringVar(value=self.engine.state['target']);ttk.Entry(row,textvariable=self.target).pack(side='left',fill='x',expand=True,padx=8);ttk.Button(row,text='Mở Canva',command=self.open_canva).pack(side='right')
        row=ttk.Frame(build);row.pack(fill='x',pady=7)
        ttk.Button(row,text='2. Bắt đầu / Tiếp tục tự động',style='Accent.TButton',command=self.run).pack(side='left');ttk.Button(row,text='Tạm dừng',command=self.engine.pause).pack(side='left',padx=8);ttk.Button(row,text='Xử lý cảnh bị dở',command=self.recover).pack(side='left');ttk.Button(row,text='Dự án mới',command=self.new_project).pack(side='right');ttk.Button(row,text='Các phần đã dựng',command=self.show_parts).pack(side='right',padx=6)
        self.progress=ttk.Progressbar(build,maximum=100);self.progress.pack(fill='x',pady=6)
        self.status=tk.StringVar();ttk.Label(outer,textvariable=self.status,wraplength=1060).pack(fill='x',pady=(10,0))
        self.connection=tk.StringVar(value='Chưa có kết nối trình duyệt');ttk.Label(settings,textvariable=self.connection,font=('Segoe UI',12,'bold')).pack(anchor='w',pady=8)
        ttk.Label(settings,text='Ghép nối tiện ích một lần. Mã được giữ trên máy để tự kết nối những lần sau.').pack(anchor='w')
        self.token_var=tk.StringVar(value=self.engine.token)
        token=ttk.Frame(settings);token.pack(fill='x',pady=8)
        self.token_entry=ttk.Entry(token,width=48,state='readonly',textvariable=self.token_var);self.token_entry.pack(side='left')
        ttk.Button(token,text='Sao chép mã',command=self.copy_token).pack(side='left',padx=8)
        ttk.Button(settings,text='Mở thư mục tiện ích để cài',command=self.extension_folder).pack(anchor='w',pady=8)
        ttk.Button(settings,text='Cập nhật ứng dụng + tiện ích từ GitHub',command=self.check_update).pack(anchor='w',pady=3)
        ttk.Button(settings,text='Kiểm tra tiện ích Chrome đang dùng',command=self.inspect_companion).pack(anchor='w',pady=3)
        ttk.Label(settings,text='Cập nhật GitHub bao gồm tiện ích trong TienIch_Canva. Cài thư mục này một lần; các bản sau tiện ích tự nạp lại khi không dựng.',wraplength=950).pack(anchor='w',pady=5)
        ttk.Label(settings,text='Thư mục dữ liệu portable: '+str(DATA),wraplength=950).pack(anchor='w',pady=5)
        ttk.Button(settings,text='Mở thư mục dữ liệu',command=lambda:os.startfile(str(DATA))).pack(anchor='w',pady=3)
        ttk.Button(settings,text='Xem danh sách lỗi dựng',command=self.show_errors).pack(anchor='w',pady=3)
        ttk.Label(settings,text='Nhận diện voice trên máy bằng Whisper',font=('Segoe UI',13,'bold')).pack(anchor='w',pady=(20,8))
        self.python=tk.StringVar(value=self.settings.get('python',self.detect_python()));self.model=tk.StringVar(value=self.settings.get('model',self.detect_model()));self.ffmpeg=tk.StringVar(value=self.settings.get('ffmpeg',self.detect_ffmpeg()))
        for label,var in [('Python cũ (tùy chọn)',self.python),('Mô hình (tự tải máy mới)',self.model),('FFmpeg (.exe)',self.ffmpeg)]:
            r=ttk.Frame(settings);r.pack(fill='x',pady=5);ttk.Label(r,text=label,width=25).pack(side='left');ttk.Entry(r,textvariable=var).pack(side='left',fill='x',expand=True);ttk.Button(r,text='Chọn…',command=lambda v=var:self.choose_tool(v)).pack(side='left',padx=8)
        ttk.Button(settings,text='Lưu cấu hình',command=self.save_settings).pack(anchor='w',pady=12)
        ttk.Label(settings,text='Máy mới tự tải bộ nhận diện và mô hình tiếng Việt khi bấm Phân tích lần đầu (cần Internet, khoảng 152 MB). Không cần cài Python. Các lần sau chạy trên máy, không gửi voice ra ngoài.',wraplength=950).pack(anchor='w',pady=6)
        guide=(BASE/'HUONG_DAN.txt').read_text(encoding='utf8') if (BASE/'HUONG_DAN.txt').exists() else 'Xem HUONG_DAN.txt trong gói tải về.'
        ht=tk.Text(help_tab,wrap='word',font=('Segoe UI',11),relief='flat',padx=12,pady=12);ht.pack(fill='both',expand=True);ht.insert('1.0',guide);ht.configure(state='disabled')
        if self.engine.state['scenes']:
            self.plan=dict(scenes=self.engine.state['scenes'],parts=self.engine.state.get('parts',[]));self.populate();self.voice.set(self.engine.state.get('original_voice',self.engine.state['voice']));self.prepared_voice=self.engine.state['voice']
        self.display_part=self.engine.state.get('part_index',0)
        self.root.protocol('WM_DELETE_WINDOW',self.close);self.root.after(350,self.tick)
        if imported:self.engine.log('Đã sao chép dữ liệu cũ vào '+str(DATA))
        if os.environ.get('SKST_UPDATE_HEALTH'):
            atomic_json(os.environ['SKST_UPDATE_HEALTH'],dict(version=VERSION,ready=True))
    def check_update(self):
        if self.update_busy:return
        self.update_busy=True;self.update_button.configure(state='disabled',text='Đang kiểm tra…')
        def work():
            try:self.tasks.put(('update_available',updater.check_latest(VERSION)))
            except Exception as e:self.tasks.put(('update_error',str(e)))
        threading.Thread(target=work,daemon=True).start()
    def update_event(self,kind,value):
        if kind=='update_progress':
            self.update_button.configure(text=f'Đang tải {int(100*value[0]/max(1,value[1]))}%');return
        self.update_busy=False;self.update_button.configure(state='normal',text='Kiểm tra cập nhật')
        if kind=='update_error':messagebox.showerror('Cập nhật chưa hoàn tất',str(value));return
        if kind=='update_available':
            if value is None:messagebox.showinfo('Cập nhật','Bạn đang dùng bản mới nhất đã phát hành: '+VERSION);return
            if self.worker_busy or self.engine.state['mode']=='running':messagebox.showinfo('Có bản mới','Có phiên bản '+value['version']+'. Hãy hoàn tất hoặc tạm dừng dựng video trước khi cập nhật.');return
            if not getattr(sys,'frozen',False):messagebox.showinfo('Có bản mới','Bản EXE mới đã có trên GitHub: '+value['version']+'\nhttps://github.com/'+updater.REPOSITORY+'/releases/latest');return
            if not messagebox.askyesno('Có bản cập nhật '+value['version'], 'Phiên bản hiện tại: '+VERSION+'\nPhiên bản mới: '+value['version']+'\n\n'+value['notes'][:1800]+'\n\nTải bản mới từ GitHub? Cấu hình và tiến độ sẽ được giữ lại.'):return
            self.update_busy=True;self.update_button.configure(state='disabled',text='Đang tải…')
            def download():
                try:
                    folder=DATA/'Updates'/(value['version']+'-'+str(time.time_ns()))
                    staged=updater.download_update(value,folder,lambda n,total:self.tasks.put(('update_progress',(n,total))))
                    self.tasks.put(('update_ready',(str(staged),value['version'])))
                except Exception as e:self.tasks.put(('update_error',str(e)))
            threading.Thread(target=download,daemon=True).start();return
        if kind=='update_ready':
            if self.worker_busy or self.engine.state['mode']=='running':messagebox.showinfo('Đã tải bản mới','Tệp đã tải xong. Dừng dựng rồi kiểm tra cập nhật lại để cài.');return
            if not messagebox.askyesno('Sẵn sàng cập nhật','Đã kiểm tra tệp tải về. Ứng dụng sẽ đóng, thay bản mới và mở lại.\nNếu tiện ích được thay đổi, hãy tải lại tiện ích và tab Canva sau khi cập nhật.\n\nCài ngay?'):return
            try:
                self.engine.pause();self.save_settings();updater.launch_installer(value[0],DATA,value[1])
            except Exception as e:messagebox.showerror('Chưa cài được cập nhật',str(e));return
            self.close()
    def choose_tool(self,v):
        p=filedialog.askopenfilename();
        if p:v.set(p)
    def detect_python(self):
        return '' # Existing custom Python remains in settings; new PCs use native setup.
    def detect_model(self):
        for p in [recognizer_paths(DATA)[1],Path.home()/'.cache/whisper/base.pt']:
            if p.exists():return str(p)
        return ''
    def detect_ffmpeg(self):
        bundled=Path(sys.executable).parent/'CongCu/ffmpeg.exe'
        return str(bundled) if bundled.is_file() else shutil.which('ffmpeg') or ''
    def copy_token(self):self.root.clipboard_clear();self.root.clipboard_append(self.engine.token)
    def inspect_companion(self):
        info=companion_status(application_dir())
        text='Tiện ích đi kèm: '+info['version']+'\nThư mục cố định:\n'+info['folder']
        if not info['registrations']:text+='\n\nChưa tìm thấy bản SKST đăng ký trong Chrome/Cốc Cốc/Edge. Cài thư mục trên một lần.'
        for item in info['registrations']:
            text+='\n\n'+item['browser']+' ('+item['profile']+') đang nạp:\n'+item['path']
        if info['mismatches']:text+='\n\nCó bản đang nạp từ thư mục khác nên không nhận tệp cập nhật ở đây. Gỡ bản cũ và chọn đúng thư mục cố định trên một lần.'
        messagebox.showinfo('Tiện ích đi kèm và tự cập nhật',text)
    def choose_voice(self):
        p=filedialog.askopenfilename(filetypes=[('Voice','*.mp3 *.wav *.m4a *.aac *.flac'),('Tất cả','*.*')]);
        if p:self.voice.set(p);self.end.set('');self.prepared_voice='';self.plan=None;self.tree.delete(*self.tree.get_children())
    def choose_script(self):
        p=filedialog.askopenfilename(filetypes=[('Kịch bản','*.docx *.txt')]);
        if not p:return
        try:self.plan=None;self.script_path.set(p);self.script.delete('1.0','end');self.script.insert('1.0',read_script(p))
        except Exception as e:messagebox.showerror('Không đọc được kịch bản',str(e))
    def choose_transcript(self):
        p=filedialog.askopenfilename(filetypes=[('Mốc lời đọc','*.json *.srt *.vtt')]);
        if p:self.transcript.set(p)
    def save_settings(self):
        self.settings={k:v.get() for k,v in [('python',self.python),('model',self.model),('ffmpeg',self.ffmpeg),('voice',self.voice),('transcript',self.transcript)]};atomic_json(DATA/'settings.json',self.settings)
    def analyze(self):
        if self.worker_busy:return
        if self.engine.state['mode']=='running':return messagebox.showinfo('Đang dựng','Hãy tạm dừng trước khi chia lại cảnh.')
        try:
            if not Path(self.voice.get()).is_file():raise ValueError('Chọn tệp voice có sẵn trên máy.')
            if not Path(self.ffmpeg.get()).is_file():raise ValueError('Chọn FFmpeg trong Kết nối & công cụ.')
            a=float(self.start.get());b=float(self.end.get()) if self.end.get().strip() else probe_duration(self.ffmpeg.get(),self.voice.get());o=float(self.opening.get())
            if not 0<=a<b:raise ValueError('Mốc thời gian không hợp lệ.')
        except Exception as e:return messagebox.showerror('Chưa đủ dữ liệu',str(e))
        try:
            if not self.script.get('1.0','end').strip():
                nearby=neighboring_script(self.voice.get())
                if nearby:
                    self.script_path.set(str(nearby));self.script.insert('1.0',read_script(nearby))
        except Exception as e:return messagebox.showerror('Không đọc được kịch bản',str(e))
        self.save_settings();self.worker_busy=True;self.plan_button.configure(state='disabled');self.notice.set('Đang nhận diện voice trên máy. Có thể mất vài phút…')
        inputs=dict(a=a,b=b,o=o,voice=self.voice.get(),ffmpeg=self.ffmpeg.get(),python=self.python.get(),model=self.model.get(),transcript=self.transcript.get(),script=self.script.get('1.0','end').strip())
        threading.Thread(target=self.analyze_worker,args=(inputs,),daemon=True).start()
    def analyze_worker(self,c):
        try:
            native=not c['transcript'] and (not Path(c['python']).is_file() or not Path(c['model']).is_file() or Path(c['model']).suffix.lower()=='.bin')
            if native:
                exe,model=ensure_recognizer(DATA,lambda message:self.tasks.put(('setup_progress',message)))
                c.update(cpp=str(exe),model=str(model))
                self.tasks.put(('recognizer_ready',str(model)))
            job=DATA/'Projects'/uuid.uuid4().hex;job.mkdir(parents=True)
            clip=job/'recognition.wav'
            probe=Path(c['ffmpeg']).with_name('ffprobe.exe' if os.name=='nt' else 'ffprobe')
            if probe.is_file():
                duration=float(subprocess.check_output([str(probe),'-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',c['voice']],creationflags=NO_WINDOW))
                if c['b']>duration+.1:raise ValueError(f'Voice dài {duration:.2f} giây. Chọn điểm kết thúc trong khoảng đó.')
            subprocess.run([c['ffmpeg'],'-v','error','-y','-ss',str(c['a']),'-i',c['voice'],'-t',str(c['b']-c['a']),'-vn','-ar','16000','-ac','1','-c:a','pcm_s16le',str(clip)],check=True,creationflags=NO_WINDOW,capture_output=True)
            if c['transcript']:
                seg=load_transcript(c['transcript']);seg,aligned=align_script(seg,c['script']);plan=make_plan(seg,c['a'],c['b'],c['o'])
            else:
                out=job/'transcript.json'
                cached=cached_transcript(DATA/'Projects',clip)
                if cached:shutil.copy2(cached,out)
                else:
                    log=(DATA/'whisper.log').open('w',encoding='utf8')
                    env=os.environ.copy();env['PATH']=str(Path(c['ffmpeg']).parent)+os.pathsep+env.get('PATH','')
                    args=recognition_command(c['cpp'],c['model'],clip,job/'native') if native else [c['python'],str(BASE/'canva_studio/transcribe_worker.py'),str(clip),str(out),c['model']]
                    self.process=subprocess.Popen(args,stdout=log,stderr=log,env=env,cwd=job,creationflags=NO_WINDOW)
                    code=self.process.wait();log.close();self.process=None
                    if code:
                        detail='Không mở được tệp âm thanh nội bộ. ' if code==2 and native else ''
                        raise ValueError(detail+'Bộ nhận diện dừng với mã '+str(code)+'. Xem Data/whisper.log trong thư mục ứng dụng.')
                    if native:convert_output(job/'native.json',out)
                seg=load_transcript(out);seg,aligned=align_script(seg,c['script']);plan=make_plan(seg,0,c['b']-c['a'],c['o'])
                plan['source_start']=c['a']
                for scene in plan['scenes']:scene['source_start']=round(scene['source_start']+c['a'],3)
            plan=add_title_cards(plan,seg,c['script'],timing_offset=0 if c['transcript'] else c['a'])
            render_titles(plan,c['ffmpeg'],job)
            parts=prepare_parts(plan,c['voice'],c['ffmpeg'],job)
            plan={**parts[0], 'parts':parts,'original_voice':c['voice'],'script_aligned':aligned,'approximate':plan.get('approximate',False),'title_count':plan.get('title_count',0)}
            self.tasks.put(('plan',(plan,parts[0]['voice'])))
        except Exception as e:self.tasks.put(('error',str(e)))
    def populate(self):
        self.tree.delete(*self.tree.get_children())
        for s in self.plan['scenes']:
            self.tree.insert('','end',iid=str(s['id']),values=(f'{s["start"]:.2f} → {s["start"]+s["duration"]:.2f}',s['text'],s['queries'][0]))
    def edit_scene(self,event=None):
        if not self.plan or not self.tree.selection():return
        if self.engine.state['mode']=='running':return messagebox.showinfo('Đang dựng','Tạm dừng trước khi sửa từ khóa.')
        s=next(s for s in self.plan['scenes'] if str(s['id'])==self.tree.selection()[0])
        if s['id'] in self.engine.state['done']:return messagebox.showinfo('Cảnh đã dựng','Sửa cảnh này trực tiếp trong Canva để giữ timeline.')
        value=simpledialog.askstring('Từ khóa cảnh',s['text']+'\nMỗi từ khóa một dòng:',initialvalue='\n'.join(s['queries']))
        if value and value.strip():s['queries']=[q.strip() for q in value.splitlines() if q.strip()];s['review']=False;s['requires_review']=False;s['manual_queries']=True;s.pop('subjects',None);s.pop('actions',None);self.populate();self.engine.state['scenes']=self.plan['scenes'];self.engine.save()
    def export_plan(self):
        if not self.plan:return
        p=filedialog.asksaveasfilename(defaultextension='.json',filetypes=[('Danh sách cảnh','*.json')]);
        if p:atomic_json(p,self.plan)
    def import_plan(self):
        if self.engine.state['mode']=='running':return
        p=filedialog.askopenfilename(filetypes=[('Danh sách cảnh','*.json')]);
        if not p:return
        try:
            plan=json.loads(Path(p).read_text(encoding='utf8')); scenes=plan['scenes'];at=0
            if not scenes or len(scenes)>50:raise ValueError('Danh sách cần từ 1 đến 50 cảnh.')
            for i,s in enumerate(scenes,1):
                if s['id']!=i or abs(s['start']-at)>.05 or not .1<=s['duration']<=5.05 or not s['queries']:raise ValueError('Danh sách cảnh không liên tục hoặc quá 5 giây.')
                at=s['start']+s['duration']
            self.plan=plan;self.prepared_voice='';self.populate();self.engine.state.update(scenes=scenes,done=[],used=[],phase={},voice_done=False,target='',voice='',mode='ready');self.engine.save();self.target.set('');self.notice.set('Đã nạp danh sách. Chọn đúng voice đã cắt theo độ dài danh sách này.')
        except Exception as e:messagebox.showerror('Không nạp được',str(e))
    def load_demo(self):
        if self.engine.state['mode']=='running':return
        folder=Path(sys.executable).parent/'Mau_DungThu' if getattr(sys,'frozen',False) else BASE/'examples'
        try:
            self.plan=json.loads((folder/'Danh_sach_canh.json').read_text(encoding='utf8'))
            voice=folder/'Voice_Nhon_got.mp3'
            if not voice.is_file():
                selected=filedialog.askopenfilename(title='Chọn voice đã cắt 2 phút 46 giây cho mẫu Nhón gót chân',filetypes=[('Voice','*.mp3 *.wav')])
                if not selected:return
                voice=Path(selected)
            self.voice.set(str(voice));self.prepared_voice=str(voice);self.start.set('0');self.end.set('166.65');self.populate();self.target.set('')
            self.engine.state.update(scenes=[],done=[],used=[],phase={},target='',voice='',voice_done=False,export_done=False,mode='ready');self.engine.save()
            self.notice.set('Mẫu 50 cảnh theo bản dựng vừa làm. Mở một thiết kế Canva video ngang TRỐNG rồi dán link bên dưới.')
        except Exception as e:messagebox.showerror('Không mở được mẫu',str(e))
    def open_canva(self):
        try:
            u=self.target.get().strip()
            if valid_canva(u):open_chrome(u)
            else:self.run()
        except Exception as e:messagebox.showerror('Chưa mở được Chrome',str(e))
    def extension_folder(self):
        path=Path(sys.executable).parent/'TienIch_Canva' if getattr(sys,'frozen',False) else BASE/'extension'
        if path.exists():os.startfile(str(path))
        else:messagebox.showinfo('Tiện ích','Giải nén toàn bộ gói, giữ thư mục TienIch_Canva bên cạnh ứng dụng.')
    def run(self):
        try:
            if self.worker_busy:return
            if self.engine.state['mode'] in ('opening','opening_resume'):
                self.notice.set('Chrome đang mở thiết kế. Không bấm lặp; tiện ích sẽ tự bắt đầu khi trang sẵn sàng.');return
            if not self.plan:
                self.analyze();self.analyze_then_run=self.worker_busy;return
            if not Path(self.voice.get()).is_file():raise ValueError('Chọn voice trước.')
            u=self.target.get().strip();st=self.engine.state
            if u and not valid_canva(u):raise ValueError('Link thiết kế chưa đúng. Để trống để phần mềm tự tạo Video khổ ngang.')
            if not u or st['scenes']!=self.plan['scenes'] or st['target']!=u:
                chosen=self.prepared_voice or self.voice.get()
                actual=probe_duration(self.ffmpeg.get(),chosen)
                expected=self.plan['scenes'][-1]['start']+self.plan['scenes'][-1]['duration']
                if abs(actual-expected)>.12:raise ValueError(f'Voice dài {actual:.3f} giây, hình cần {expected:.3f} giây. Chọn voice gốc và phân tích lại.')
                if not u:
                    if st.get('bootstrap_nonce') and st['scenes']==self.plan['scenes']:
                        self.engine.wait_for_created_tab();return
                    chrome_path()
                    address=self.engine.bootstrap(self.plan,chosen)
                    try:open_chrome(address)
                    except Exception:
                        self.engine.pause();raise
                    return
                self.engine.configure(self.plan,u,chosen)
            connection=self.engine.connection_status(u)
            if connection['ready']:self.engine.start()
            else:
                chrome_path();self.engine.resume_in_chrome()
                try:open_chrome(u)
                except Exception:
                    self.engine.pause();raise
        except Exception as e:messagebox.showerror('Chưa thể bắt đầu',str(e))
    def recover(self):
        self.engine.pause()
        stage=self.engine.state['phase'].get('stage','')
        if stage=='insert_intent':
            v=messagebox.askyesnocancel('Kiểm tra Canva','Cảnh đang dở đã xuất hiện ở cuối timeline chưa?\nCó: tiếp tục cắt cảnh đó.\nKhông: chỉ chọn sau khi đã xóa phần chèn dở trong Canva.\nHủy: giữ nguyên để kiểm tra thêm.')
            if v is not None:self.engine.recover('inserted' if v else 'not_inserted')
        elif stage in ('upload_intent','export_intent','title_uploading'):
            if messagebox.askyesno('Kiểm tra Canva','Chỉ đặt lại sau khi đã xóa voice tải dở khỏi thiết kế, hoặc đã hủy lần xuất đang dở. Đặt lại thao tác này?'):self.engine.recover('not_inserted')
        else:messagebox.showinfo('Tiếp tục','Đã giữ tiến độ. Kiểm tra lại Canva rồi bấm Tiếp tục.')
    def show_errors(self):
        rows=self.engine.state.get('errors',[])
        if not rows:messagebox.showinfo('Lỗi dựng','Chưa ghi nhận lỗi trong dự án này.');return
        window=tk.Toplevel(self.root);window.title('Các vị trí cần sửa sau khi dựng');window.geometry('850x460')
        field=tk.Text(window,wrap='word',font=('Segoe UI',11),padx=12,pady=12);field.pack(fill='both',expand=True)
        for row in rows:
            stamp=f"{row['start']:.2f} giây" if row.get('start') is not None else 'Tác vụ chung'
            field.insert('end',f"Phần {row['part']} • Cảnh/tác vụ {row['id']} • {stamp}\nBước: {row['stage']}\n{row['message']}\n\n")
        field.configure(state='disabled')

    def show_parts(self):
        st=self.engine.state;history=st.get('history',[])
        rows=[f"Phần {i+1} • voice gốc {p['source_start']:.3f} → {p['source_start']+p['duration']:.3f} giây\n{p['target']}" for i,p in enumerate(history)]
        if st.get('target'):rows.append(f"Phần hiện tại {st.get('part_index',0)+1}\n{st['target']}")
        messagebox.showinfo('Các phần đã dựng','\n\n'.join(rows) or 'Chưa có phần nào.')
    def new_project(self):
        if not messagebox.askyesno('Dự án mới','Xóa tiến độ dựng trong ứng dụng để chuẩn bị dự án mới? Thiết kế Canva hiện tại vẫn được giữ.'):return
        self.engine.pause();self.engine.state.update(scenes=[],done=[],phase={},used=[],usage={},last_asset='',target='',voice='',voice_done=False,export_done=False,mode='idle');self.engine.running=None;self.engine.save();self.plan=None;self.tree.delete(*self.tree.get_children());self.target.set('')
    def tick(self):
        while not self.tasks.empty():
            kind,value=self.tasks.get()
            if kind.startswith('update_'):self.update_event(kind,value);continue
            if kind=='setup_progress':self.notice.set(value);continue
            if kind=='recognizer_ready':self.model.set(value);self.save_settings();continue
            self.worker_busy=False;self.plan_button.configure(state='normal')
            if kind=='error':self.analyze_then_run=False;self.notice.set('Phân tích chưa thành công.');messagebox.showerror('Chưa phân tích được',value)
            else:
                if self.engine.state.get('scenes'):
                    archive=DATA/'Projects'/'Previous';archive.mkdir(parents=True,exist_ok=True)
                    atomic_json(archive/(uuid.uuid4().hex+'.json'),self.engine.state)
                self.plan,clip=value;self.prepared_voice=clip;self.populate();self.target.set('')
                self.engine.state.update(scenes=[],done=[],used=[],phase={},target='',voice='',voice_done=False,export_done=False,mode='ready');self.engine.save()
                n=len(self.plan['scenes']);note=f'Đã chia {n} cảnh phần đầu; {self.plan.get("title_count",0)} tiêu đề nền đen. Nhấp đúp để sửa từ khóa.'
                if self.plan.get('approximate'):note+=' Mốc từ được ước lượng từ phụ đề; nên duyệt phần mở đầu.'
                if self.script.get('1.0','end').strip() and not self.plan.get('script_aligned'):note+=' Chưa khớp chắc chắn kịch bản: đang dùng lời nhận diện từ voice.'
                if self.plan.get('parts'):note+=f' Tổng {len(self.plan["parts"])} phần, tối đa 50 cảnh/phần; voice đã kiểm tra đủ thời lượng.'
                self.notice.set(note)
                if self.analyze_then_run:
                    self.analyze_then_run=False;self.root.after(0,self.run)
        self.engine.watchdog()
        st=self.engine.state
        if st.get('part_index',0)!=self.display_part:
            self.display_part=st.get('part_index',0);self.plan=dict(scenes=st['scenes'],parts=st.get('parts',[]));self.prepared_voice=st['voice'];self.target.set(st['target']);self.populate()
        if st.get('auto_start') and st.get('target') and st['mode'] in ('running','opening_resume'):
            self.target.set(st['target'])
        n=len(st['scenes']);done=len(st['done']);self.progress['value']=100*done/max(1,n)
        self.status.set(f'Phần {st.get("part_index",0)+1}/{max(1,len(st.get("parts",[])))} • {done}/{n} cảnh  •  '+st['message'])
        self.connection.set(self.engine.connection_status()['message'])
        self.root.after(500,self.tick)
    def close(self):
        self.engine.pause();self.save_settings()
        if self.process:self.process.terminate()
        self.server.shutdown();self.root.destroy()

def main():
    root=tk.Tk()
    try:app=App(root)
    except OSError as e:messagebox.showerror('Không mở được ứng dụng','Có thể ứng dụng đang mở ở cửa sổ khác.\n'+str(e));root.destroy();return
    if '--self-test' in sys.argv:
        import gc
        root.withdraw()
        folder=Path(sys.executable).parent/'Mau_DungThu' if getattr(sys,'frozen',False) else BASE/'examples'
        if (folder/'Danh_sach_canh.json').is_file():
            app.plan=json.loads((folder/'Danh_sach_canh.json').read_text(encoding='utf8'));app.populate()
        root.update_idletasks();gc.collect()
        token_visible=app.token_entry.get()==app.engine.token and len(app.token_entry.get())>=20
        app.copy_token();root.update_idletasks();copy_ok=root.clipboard_get()==app.engine.token
        report=dict(version=VERSION,ui_opened=True,demo_scenes=len(app.tree.get_children()) if app.plan else 0,ffmpeg_found=Path(app.ffmpeg.get()).is_file(),whisper_found=Path(app.python.get()).is_file(),model_found=Path(app.model.get()).is_file(),pairing_code_visible=token_visible,pairing_copy_ok=copy_ok,update_button=app.update_button.cget('text')=='Kiểm tra cập nhật',portable_data=str(DATA),portable_temp=tempfile.gettempdir(),runtime_extracts_to_temp=bool(getattr(sys,'frozen',False) and Path(sys._MEIPASS).name!='_internal'),canva_live_tested=False)
        if not token_visible or not copy_ok:raise RuntimeError('Pairing-code regression check failed')
        atomic_json(DATA/'self-test.json',report);app.close();return
    root.mainloop()

if __name__=='__main__':main()
