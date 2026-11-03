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
let editorOpening=null;
function matchesProject(data,url){
  if(!editorURL(url))return false;
  if(data.target)return canonical(url)===canonical(data.target);
  return !!data.bootstrap_nonce&&new URLSearchParams(new URL(url).hash.slice(1)).get('skst_start')===data.bootstrap_nonce;
}
async function attachAfterNavigation(tab){
  if(!editorURL(tab?.url))return;
  const {token,enabled}=await chrome.storage.local.get(['token','enabled']);
  if(!enabled||!token)return;
  const data=await bridgeFetch('ping',{},token);
  if(!matchesProject(data,tab.url))return;
  await attachController(data,false);
}
// Canva can enter /edit through an SPA URL change: document_idle scripts for
// /edit were not present on the initial creation page. Observe that transition
// using the existing Canva-only host access, without opening another design.
chrome.tabs.onUpdated?.addListener(async(id,change,tab)=>{
  if(!change.url&&change.status!=='complete')return;
  try{await attachAfterNavigation(tab);}catch(error){
    await chrome.storage.local.set({lastConnectionError:'Chưa nối được bộ dựng sau khi mở Canva: '+error.message});
  }
});
chrome.runtime.onStartup?.addListener(async()=>{
  try{
    const {token,enabled}=await chrome.storage.local.get(['token','enabled']);
    if(enabled&&token)await attachController(await bridgeFetch('ping',{},token),false);
  }catch{}
});
async function ensureEditor(data,allowOpen){
  const tabs=await chrome.tabs.query({url:'https://www.canva.com/design/*'});
  let candidates=tabs.filter(t=>editorURL(t.url));
  if(data.target)candidates=candidates.filter(t=>canonical(t.url)===canonical(data.target));
  else if(data.bootstrap_nonce)candidates=candidates.filter(t=>new URLSearchParams(new URL(t.url).hash.slice(1)).get('skst_start')===data.bootstrap_nonce);
  else return null; // Pairing alone does not select an unrelated existing design.
  let tab=candidates.find(t=>t.active)||candidates.at(-1);
  if(tab)return tab;
  if(!allowOpen)return null;
  const address=data.target||data.create_url;
  if(!address)return null;
  const u=new URL(address);
  const create=u.origin==='https://www.canva.com'&&u.pathname==='/design'&&u.searchParams.has('create')&&u.searchParams.get('type')==='TADUvCyAV_U'&&/^#skst_start=[A-Za-z0-9_-]{24}$/.test(u.hash);
  if(!editorURL(address)&&!create)throw Error('Chỉ mở thiết kế Video trên Canva.');
  const key='editor:'+address;
  const saved=(await chrome.storage.local.get([key]))[key];
  if(saved){try{tab=await chrome.tabs.get(saved);}catch{tab=null;}}
  if(!tab){tab=await chrome.tabs.create({url:address,active:true});await chrome.storage.local.set({[key]:tab.id});}
  for(let i=0;i<60;i++){
    tab=await chrome.tabs.get(tab.id);
    if(editorURL(tab.url)&&(!data.target||canonical(tab.url)===canonical(data.target))&&(!data.bootstrap_nonce||new URLSearchParams(new URL(tab.url).hash.slice(1)).get('skst_start')===data.bootstrap_nonce))return tab;
    await new Promise(r=>setTimeout(r,1000));
  }
  throw Error('Canva chưa tải xong. Giữ tab vừa mở; tiện ích sẽ dùng lại tab đó khi kết nối lại.');
}
async function attachController(data,allowOpen=false){
  if(editorOpening)return editorOpening;
  editorOpening=(async()=>{
    const tab=await ensureEditor(data,allowOpen);
    if(!tab)return null;
    let lastError;
    for(let i=0;i<15;i++){
      try{
        await chrome.scripting.executeScript({target:{tabId:tab.id},files:['adapter.js','content.js']});
        const ready=await chrome.tabs.sendMessage(tab.id,{type:'skst_controller_ping'});
        if(ready?.ready)return tab;
      }catch(e){lastError=e;}
      await new Promise(r=>setTimeout(r,500));
    }
    throw Error('Chưa gắn được bộ dựng vào tab mới: '+(lastError?.message||'trang đang tải'));
  })();
  try{return await editorOpening;}finally{editorOpening=null;}
}
async function openNextDesign(body,sender,token){
  const href=new URL(body.create_url);
  if(href.origin!=='https://www.canva.com'||href.pathname!=='/design'||!href.searchParams.has('create')||href.searchParams.get('type')!=='TADUvCyAV_U')throw Error('Chỉ tạo Video khổ ngang trên Canva.');
  const check=async(stage,extra={})=>{
    const r=await bridgeFetch('checkpoint',{id:body.id,client:body.client,url:sender.url,...(stage?{stage,...extra}:{})},token);
    if(!r.continue_)throw Error('Đã tạm dừng trước khi mở phần tiếp theo.');
  };
  const key='next:'+canonical(sender.url);
  const cached=(await chrome.storage.local.get([key]))[key];
  let tab;
  if(cached){try{tab=await chrome.tabs.get(cached);}catch{throw Error('Tab phần tiếp theo đã đóng. Mở lại tab đó trước khi tiếp tục; không tự tạo trùng.');}}
  if(!tab){
    if(body.phase?.stage==='create_intent')throw Error('Lần trước dừng lúc mở thiết kế. Kiểm tra tab mới trước khi thử lại.');
    await check('create_intent');
    tab=await chrome.tabs.create({url:href.href,active:true});
    await chrome.storage.local.set({[key]:tab.id});
    await check('create_open',{tab_id:tab.id});
  }
  for(let i=0;i<60;i++){
    await check();tab=await chrome.tabs.get(tab.id);
    if(editorURL(tab.url)&&canonical(tab.url)!==canonical(sender.url))return {new_target:tab.url};
    await new Promise(r=>setTimeout(r,1000));
  }
  throw Error('Tab mới chưa tải xong. Giữ nguyên tab rồi bấm Tiếp tục.');
}
function canvaDownload(item,session){
  const source=value=>{try{const h=new URL(String(value).replace(/^blob:/,'')).hostname;return h==='canva.com'||h.endsWith('.canva.com')||h==='canvausercontent.com'||h.endsWith('.canvausercontent.com');}catch{return false;}};
  if(editorURL(item.referrer)&&canonical(item.referrer)!==session.target)return false;
  return !session.before.includes(item.id)&&Date.parse(item.startTime)>=session.started&&source(item.finalUrl||item.url)&&(/\.mp4$/i.test(item.filename||'')||item.mime==='video/mp4');
}
async function exportDownload(action,sender){
  const {token}=await chrome.storage.local.get(['token']);
  const state=await bridgeFetch('ping',{},token);
  if(canonical(state.target)!==canonical(sender.url))throw Error('Chỉ xác nhận tải MP4 của thiết kế đang dựng.');
  if(!await chrome.permissions.contains({permissions:['downloads']}))throw Error('Mở tiện ích SKST và bấm Cho phép kiểm tra tải MP4 trước khi xuất.');
  const key='export:'+canonical(sender.url);
  if(action==='arm'){
    const before=(await chrome.downloads.search({limit:100,orderBy:['-startTime']})).map(x=>x.id);
    await chrome.storage.local.set({[key]:{started:Date.now(),before,target:canonical(sender.url)}});return {tracking:true};
  }
  if(action!=='status')throw Error('Lệnh tải xuống không hợp lệ');
  const session=(await chrome.storage.local.get([key]))[key];if(!session)return {tracking:false};
  const items=await chrome.downloads.search(session.id?{id:session.id}:{startedAfter:new Date(session.started).toISOString(),limit:100,orderBy:['-startTime']});
  const matching=session.id?items.filter(i=>i.id===session.id):items.filter(i=>canvaDownload(i,session));
  if(matching.length>1)throw Error('Có nhiều MP4 Canva tải cùng lúc, chưa xác định được tệp của dự án. Chỉ xuất một dự án mỗi lần.');
  const item=matching[0];
  if(!item)return {tracking:true};
  if(!session.id){session.id=item.id;await chrome.storage.local.set({[key]:session});}
  if(item.state==='interrupted')throw Error('Tải MP4 bị gián đoạn: '+(item.error||'Chrome chưa tải xong')+'. Tiếp tục tải trong Chrome rồi bấm Tiếp tục.');
  if(item.state==='complete'&&item.exists===false)throw Error('MP4 đã tải nhưng tệp không còn trên máy.');
  return {tracking:true,id:item.id,filename:item.filename,complete:item.state==='complete'&&item.exists===true};
}
chrome.runtime.onMessage.addListener((message, sender, respond) => {
  if (!['bridge','probe','update_companion','open_next','export_download'].includes(message.type)) return;
  const own = sender.id === chrome.runtime.id;
  const popup=['probe','update_companion'].includes(message.type)&&sender.url===chrome.runtime.getURL('popup.html');
  const canva = sender.tab && editorURL(sender.url);
  if (!own || (!canva&&!popup) || (message.type==='update_companion'&&!popup)) { respond({error:'Chỉ nhận yêu cầu từ Canva hoặc cửa sổ kết nối SKST.'}); return; }
  (async () => {
    try {
      if(message.type==='export_download'){
        if(!canva)throw Error('Chỉ kiểm tra MP4 từ tab thiết kế Canva.');
        const {enabled}=await chrome.storage.local.get(['enabled']);if(!enabled)throw Error('Đã ngắt tiện ích');
        respond(await exportDownload(message.action,sender));return;
      }
      if(message.type==='open_next'){
        const {token,enabled}=await chrome.storage.local.get(['token','enabled']);
        if(!enabled)throw Error('Chưa bật kết nối.');
        respond(await openNextDesign(message.body,sender,token));return;
      }
      const route=popup?'ping':message.route;
      if (!['next','checkpoint','result','voice','title','fallback','ping'].includes(route)) throw Error('Lệnh không hợp lệ');
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
      if(route==='result'&&data.handoff&&data.ok){
        await attachController({target:data.target});
      }
      if(popup){
        if(message.open_editor){
          const prepared=await bridgeFetch('prepare_editor',{},token);data={...data,...prepared};
        }
        const tab=await attachController(data,!!message.open_editor);
        if(!tab){
          respond({...data,connected_only:true,message:'Đã ghép nối ứng dụng. Chọn voice rồi bấm Bắt đầu trong phần mềm; Chrome và Video khổ ngang sẽ tự mở.'});return;
        }
        for(let i=0;i<24;i++){
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
