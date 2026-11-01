const editorURL=value=>/^https:\/\/www\.canva\.com\/design\/[^/]+\/[^/]+\/edit(?:[?#]|$)/.test(value||'');
const canonical=value=>(value||'').split('?')[0].split('#')[0];
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
  if (!['bridge','probe'].includes(message.type)) return;
  const own = sender.id === chrome.runtime.id;
  const popup=message.type==='probe'&&sender.url===chrome.runtime.getURL('popup.html');
  const canva = sender.tab && editorURL(sender.url);
  if (!own || (!canva&&!popup)) { respond({error:'Chỉ nhận yêu cầu từ Canva hoặc cửa sổ kết nối SKST.'}); return; }
  (async () => {
    try {
      const route=popup?'ping':message.route;
      if (!['next','checkpoint','result','voice','ping'].includes(route)) throw Error('Lệnh không hợp lệ');
      const {token,enabled} = await chrome.storage.local.get(['token','enabled']);
      if (!enabled) {respond({disabled:true});return;}
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
