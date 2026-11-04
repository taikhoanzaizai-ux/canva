"""Project-scoped scene status for the desktop table."""
def scene_status(scene,state):
    ident=scene['id'];part=state.get('part_index',0)+1
    review=state.get('manual_review',{}).get('scene_id')==ident
    if review:
        reason=state.get('manual_review_error','')
        return ('Cần sửa lại' if reason else 'Đang kiểm tra tự sửa','error' if reason else 'review',reason)
    if state.get('manual_edit_scene')==ident:return ('Đang tự sửa trên Canva','review',scene.get('error_card',{}).get('message',''))
    if scene.get('manual_verified'):return ('Đã tự sửa trên Canva','manual','')
    records=[r for r in state.get('errors',[]) if str(r.get('id'))==str(ident) and r.get('part',1)==part and not any(w in str(r.get('message','')).lower() for w in ('đã tạm dừng','phiên thao tác','đã ngắt'))]
    error=scene.get('error_card') or (records[-1] if records else {})
    if error:return ('Lỗi — đã chèn ảnh' if ident in state.get('done',[]) else 'Lỗi — cần sửa','error',error.get('message','Không có mô tả lỗi'))
    if ident in state.get('done',[]):return ('Đã dựng','done','')
    if state.get('phase',{}).get('id')==str(ident):return ('Đang dựng' if state.get('mode')=='running' else 'Đang dở','review','')
    return ('Chưa dựng','','')
