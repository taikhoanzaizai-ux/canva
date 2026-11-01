const token=document.getElementById('token'), status=document.getElementById('status');
chrome.storage.local.get(['token','enabled']).then(v=>{token.value=v.token||'';status.textContent=v.enabled?'Đã bật kết nối. Mở đúng thiết kế Canva.':'Chưa bật kết nối.';});
document.getElementById('save').onclick=async()=>{
 if(token.value.trim().length<20){status.textContent='Dán đầy đủ mã từ ứng dụng.';return;}
 await chrome.storage.local.set({token:token.value.trim(),enabled:true});status.textContent='Đã bật. Quay lại ứng dụng và bấm Bắt đầu.';
};
document.getElementById('stop').onclick=async()=>{await chrome.storage.local.set({enabled:false});status.textContent='Đã ngắt. Thao tác dừng ở điểm kiểm tra kế tiếp.';};
