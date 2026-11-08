"""Keep manually edited cuts and compensate in unfinished scenes."""
import math

def compensate(scenes,done,frames,minimum=.1):
    if not isinstance(frames,list) or not frames or len(frames)>len(scenes):raise ValueError('Chưa đọc đủ các cảnh đã sửa trên Canva.')
    cursor=0.
    for frame in frames:
        try:a,b=float(frame['start']),float(frame['end'])
        except (KeyError,TypeError,ValueError):raise ValueError('Mốc timeline không hợp lệ.')
        if not math.isfinite(a) or not math.isfinite(b) or abs(a-cursor)>.12 or b<=a:raise ValueError('Timeline có khoảng trống hoặc cảnh chồng lấn; hãy giữ các cảnh nối liền nhau.')
        cursor=b
    finished=set(done);prefix=0
    for scene in scenes:
        if scene['id'] not in finished:break
        prefix+=1
    if prefix!=len(finished) or prefix>len(frames):raise ValueError('Chưa đủ cảnh phía trước để tiếp tục, không thể bỏ qua một khoảng trống.')
    anchors=[s.get('voice_end',s['start']+s['duration']) for s in scenes]
    total=anchors[-1];cursor=float(frames[prefix-1]['end']) if prefix else 0.
    remaining=len(scenes)-prefix
    if remaining and cursor+remaining*minimum>total+.06:raise ValueError('Các cảnh đã sửa dài quá phần voice còn lại để bù. Rút ngắn một cảnh đã sửa rồi xác nhận lại; không cần căn từng phần trăm giây.')
    if not remaining and abs(cursor-total)>.12:raise ValueError('Đây là cảnh cuối, không còn cảnh sau để bù. Hãy đặt đoạn cuối gần điểm hết voice rồi xác nhận lại.')
    updates=[]
    for i,scene in enumerate(scenes):
        if i<prefix:
            a,b=float(frames[i]['start']),float(frames[i]['end'])
        else:
            a=cursor;b=min(max(anchors[i],a+minimum),total-(len(scenes)-i-1)*minimum)
            if b-a<minimum-.001:raise ValueError('Không đủ thời lượng voice để chia các cảnh còn lại.')
        update=dict(start=round(a,6),duration=round(b-a,6),voice_end=anchors[i],manual_timing_adjusted=True)
        if scene.get('warning_output'):update.update(warning_start=a,warning_end=b)
        if 'source_start' in scene:update['source_start']=round(scene['source_start']-scene['start']+a,6)
        updates.append(update)
        cursor=b
    return updates
