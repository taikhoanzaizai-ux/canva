import sys
if __name__=='__main__':
    from canva_studio.storage import configure_runtime
    configure_runtime()
    if len(sys.argv)==3 and sys.argv[1]=='--recognizer-self-test':
        import subprocess
        from pathlib import Path
        from canva_studio.storage import data_dir
        from canva_studio.recognizer import ensure_recognizer,command,convert_output,NO_WINDOW
        from canva_studio.core import atomic_json
        data=data_dir();exe,model=ensure_recognizer(data)
        out=data/'recognizer-check'
        with (data/'recognizer-check.log').open('w',encoding='utf8') as log:
            subprocess.run(command(exe,model,Path(sys.argv[2]).resolve(),out),stdout=log,stderr=log,check=True,creationflags=NO_WINDOW)
        rows=convert_output(out.with_suffix('.json'),data/'recognizer-check-transcript.json')
        atomic_json(data/'recognizer-check-report.json',dict(ready=True,segments=len(rows),words=sum(len(s.get('words',[])) for s in rows),python_required=False,model=str(model),runtime=str(exe)))
        raise SystemExit(0)
    if len(sys.argv)==3 and sys.argv[1]=='--apply-update':
        from canva_studio.updater import apply_manifest
        raise SystemExit(apply_manifest(sys.argv[2]))
    from canva_studio.main import main
    main()
