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
    if ident in state.get('done',[]):
        if scene.get('fallback_warning'):
            detail='Nhãn sẽ hiện trong MP4 hoàn chỉnh.' if scene.get('warning_output') else scene.get('overlay_error') or scene['fallback_warning']
            return ('Video thay thế','review',detail)
        if scene.get('fallback_source',{}).get('kind')=='text_card':
            return ('Thẻ chữ dự phòng','review','Chưa chọn được tư liệu phù hợp cho cảnh này.')
        return ('Đã dựng','done','')
    if scene.get('missing_stock'):return ('Thiếu tư liệu','review',scene['missing_stock'])
    if scene.get('overlay_pending'):return ('Kiểm tra chữ','review',scene['overlay_pending'])
    if state.get('phase',{}).get('id')==str(ident):return ('Đang dựng' if state.get('mode')=='running' else 'Đang dở','review','')
    if scene.get('context_only'):return ('Tư liệu theo ngữ cảnh','','Chưa có lời nhận diện trong khoảng này; giữ nguyên voice.')
    if scene.get('keyword_review') and not scene.get('manual_queries'):
        return ('Duyệt từ khóa','review',scene['keyword_review'])
    if scene.get('keyword_provider') and not scene.get('manual_queries'):
        return ('Từ khóa AI','','Căn cứ: '+scene.get('keyword_evidence',''))
    return ('Chưa dựng','','')
