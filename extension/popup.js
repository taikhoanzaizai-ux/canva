const token=document.getElementById('token'), status=document.getElementById('status');
document.querySelector('h2').textContent+=' '+chrome.runtime.getManifest().version;
async function probe(){
 status.textContent='Đang kiểm tra kết nối…';
 try{
  const r=await chrome.runtime.sendMessage({type:'probe'});
  if(!r||r.error)throw Error(r?.error||'Tiện ích chưa phản hồi. Hãy tải lại tiện ích và tab Canva.');
  if(r.reloading){status.textContent='Đang tự nạp tiện ích '+r.version+'. Chờ một chút rồi mở lại biểu tượng SKST.';return;}
  if(r.disabled){status.textContent='Chưa bật kết nối.';return;}
  status.textContent='Đã kết nối ứng dụng '+r.version+(r.attached?' và tab Canva. ':'. ')+(r.mode==='running'?'Đang dựng theo lệnh Bắt đầu.':(r.message||'Quay lại ứng dụng và bấm Bắt đầu.'));
 }catch(e){status.textContent=e.message;}
}
chrome.storage.local.get(['token','enabled']).then(v=>{token.value=v.token||'';if(v.enabled)probe();else status.textContent='Chưa bật kết nối.';});
document.getElementById('save').onclick=async()=>{
 if(token.value.trim().length<20){status.textContent='Dán đầy đủ mã từ ứng dụng.';return;}
 await chrome.storage.local.set({token:token.value.trim(),enabled:true});await probe();
};
document.getElementById('stop').onclick=async()=>{await chrome.storage.local.set({enabled:false});status.textContent='Đã ngắt. Thao tác dừng ở điểm kiểm tra kế tiếp.';};
