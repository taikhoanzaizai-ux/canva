"""Run in the user's local Whisper environment, never upload speech."""
import json,sys,whisper
if __name__=='__main__':
    audio,out,model=sys.argv[1:4]
    net=whisper.load_model(model,device='cpu')
    value=net.transcribe(audio,language='vi',word_timestamps=True,fp16=False,verbose=False)
    with open(out,'w',encoding='utf8') as f:json.dump(value,f,ensure_ascii=False)
