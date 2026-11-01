const editorURL=value=>/^https:\/\/www\.canva\.com\/design\/[^/]+\/[^/]+\/edit(?:[?#]|$)/.test(value||'');
const canonical=value=>(value||'').split('?')[0].split('#')[0];
let lastBundleCheck=0;
function reloadDecision(installed,disk,state){
  const parse=v=>/^\d+(?:\.\d+){2,3}$/.test(v||'')?v.split('.').map(Number):null;
  const a=parse(installed.version),b=parse(disk.version);
  if(!a||!b||disk.manifest_version!==installed.manifest_version||disk.name!==installed.name)return 'none';
  let newer=false;
  for(let i=0;i<Math.max(a.length,b.length);i++){
    if((b[i]||0)>(a[i]||0)){newer=true;break;}
    if((b[i]||0)<(a[i]||0))return 'none';
  }
  if(!newer)return 'none';
  for(const key of ['permissions','host_permissions','optional_permissions','optional_host_permissions']){
    if(JSON.stringify([...(installed[key]||[])].sort())!==JSON.stringify([...(disk[key]||[])].sort()))return 'permission_change';
  }
  const matches=m=>(m.content_scripts||[]).flatMap(s=>s.matches||[]).sort();
  if(JSON.stringify(matches(installed))!==JSON.stringify(matches(disk)))return 'permission_change';
  if(state.active_task||!['idle','ready','paused','attention','complete'].includes(state.mode))return 'busy';
  return 'reload';
}
async function refreshLocalBundle(token,force){
  if(!force&&Date.now()-lastBundleCheck<8000)return null;
  lastBundleCheck=Date.now();
  const installed=chrome.runtime.getManifest();
  const response=await fetch(chrome.runtime.getURL('manifest.json')+'?skst='+Date.now(),{cache:'no-store'});
  if(!response.ok)return null;
  const disk=await response.json();
  if(disk.version===installed.version)return null;
  const state=await bridgeFetch('ping',{},token);
  const decision=reloadDecision(installed,disk,state);
  if(decision==='permission_change')throw Error('Tiện ích mới cần quyền khác. Tải lại tiện ích trong Chrome và xác nhận quyền trước khi dùng.');
  if(decision!=='reload')return null;
  // Desktop app has already downloaded and verified these local files from
  // GitHub Releases. Never fetch/eval remote JavaScript or interrupt a task.
  setTimeout(()=>chrome.runtime.reload(),300);
  return {reloading:true,version:disk.version};
}
async function bridgeFetch(route,body,token){
  const response=await fetch('http://127.0.0.1:8766/'+route,{
    method:'POST',headers:{'Content-Type':'application/json','X-SKST-Token':token||''},
    body:JSON.stringify(body),signal:AbortSignal.timeout(20000)
  });
  const data=await response.json();if(!response.ok)throw Error(data.error||'Không kết nối được ứng dụng');return data;
}
async function attachController(data){
  const tabs=await chrome.tabs.query({url:'https://www.canva.com/design/*'});
  let candidates=tabs.filter(t=>editorURL(t.url));
  if(data.target)candidates=candidates.filter(t=>canonical(t.url)===canonical(data.target));
  const tab=candidates.find(t=>t.active)||(candidates.length===1?candidates[0]:null);
  if(!tab)throw Error(data.target?'Chưa mở đúng thiết kế trong ứng dụng. Bấm Mở Canva rồi kết nối lại.':'Mở một tab chỉnh sửa Video Canva rồi kết nối lại.');
  await chrome.scripting.executeScript({target:{tabId:tab.id},files:['adapter.js','content.js']});
  const ready=await chrome.tabs.sendMessage(tab.id,{type:'skst_controller_ping'});
  if(!ready?.ready)throw Error('Tab Canva chưa nhận bộ dựng. Tải lại tab rồi kết nối lại.');
  return tab;
}
chrome.runtime.onMessage.addListener((message, sender, respond) => {
  if (!['bridge','probe','update_companion'].includes(message.type)) return;
  const own = sender.id === chrome.runtime.id;
  const popup=['probe','update_companion'].includes(message.type)&&sender.url===chrome.runtime.getURL('popup.html');
  const canva = sender.tab && editorURL(sender.url);
  if (!own || (!canva&&!popup) || (message.type==='update_companion'&&!popup)) { respond({error:'Chỉ nhận yêu cầu từ Canva hoặc cửa sổ kết nối SKST.'}); return; }
  (async () => {
    try {
      const route=popup?'ping':message.route;
      if (!['next','checkpoint','result','voice','ping'].includes(route)) throw Error('Lệnh không hợp lệ');
      const {token,enabled} = await chrome.storage.local.get(['token','enabled']);
      if(message.type==='update_companion'){
        const data=await bridgeFetch('companion/update',{extension_id:chrome.runtime.id},token);
        const current=chrome.runtime.getManifest();
        const decision=reloadDecision(current,data.manifest,data);
        if(decision==='busy')throw Error('Hãy tạm dừng dựng trước khi cập nhật.');
        if(decision==='permission_change')throw Error('Bản mới cần quyền khác. Trình duyệt phải xác nhận quyền trước khi nạp.');
        if(decision!=='reload'){
          if(current.version!==data.manifest.version)throw Error('Không thể hạ phiên bản tiện ích. Hãy cập nhật ứng dụng.');
          respond({current:true,version:current.version});return;
        }
        respond({reloading:true,version:data.manifest.version});
        setTimeout(()=>chrome.runtime.reload(),400);return;
      }
      if (!enabled) {respond({disabled:true});return;}
      if(popup||route==='next'){
        const refresh=await refreshLocalBundle(token,popup);
        if(refresh){respond(refresh);return;}
      }
      let data=await bridgeFetch(route,popup?{}:{...message.body,url:sender.url,extension_version:chrome.runtime.getManifest().version},token);
      if(popup){
        const tab=await attachController(data);
        for(let i=0;i<6;i++){
          data=await bridgeFetch('ping',{},token);
          if(data.connection?.ready)break;
          await new Promise(r=>setTimeout(r,250));
        }
        if(!data.connection?.ready)throw Error(data.connection?.message||'Ứng dụng chưa nhận tín hiệu từ tab Canva.');
        data.attached=true;data.tab_title=tab.title;
      }
      respond(data);
    } catch(e) {respond({error:e.message});}
  })();return true;
});
chrome.runtime.onInstalled.addListener(()=>{
  (async()=>{
    const {token,enabled}=await chrome.storage.local.get(['token','enabled']);
    if(!enabled||!token)return;
    try{const data=await bridgeFetch('ping',{},token);await attachController(data);}catch{}
  })();
});
