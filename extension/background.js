chrome.runtime.onMessage.addListener((message, sender, respond) => {
  if (!['bridge','probe'].includes(message.type)) return;
  const own = sender.id === chrome.runtime.id;
  const popup=message.type==='probe'&&sender.url===chrome.runtime.getURL('popup.html');
  const canva = sender.tab && /^https:\/\/www\.canva\.com\/design\/[^/]+\/[^/]+\/edit(?:[?#]|$)/.test(sender.url || '');
  if (!own || (!canva&&!popup)) { respond({error:'Chỉ nhận yêu cầu từ Canva hoặc cửa sổ kết nối SKST.'}); return; }
  (async () => {
    try {
      const route=popup?'ping':message.route;
      if (!['next','checkpoint','result','voice','ping'].includes(route)) throw Error('Lệnh không hợp lệ');
      const {token,enabled} = await chrome.storage.local.get(['token','enabled']);
      if (!enabled) {respond({disabled:true});return;}
      const response = await fetch('http://127.0.0.1:8766/'+route, {
        method:'POST', headers:{'Content-Type':'application/json','X-SKST-Token':token||''},
        body:JSON.stringify(popup?{}:{...message.body,url:sender.url,extension_version:chrome.runtime.getManifest().version}), signal:AbortSignal.timeout(20000)
      });
      const data=await response.json();
      if (!response.ok) throw Error(data.error||'Không kết nối được ứng dụng');
      respond(data);
    } catch(e) {respond({error:e.message});}
  })();return true;
});
