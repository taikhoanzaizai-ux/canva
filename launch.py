import sys
if __name__=='__main__':
    from canva_studio.storage import configure_runtime
    configure_runtime()
    if len(sys.argv)==3 and sys.argv[1]=='--apply-update':
        from canva_studio.updater import apply_manifest
        raise SystemExit(apply_manifest(sys.argv[2]))
    from canva_studio.main import main
    main()
