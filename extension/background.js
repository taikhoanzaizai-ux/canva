chrome.runtime.onMessage.addListener((message, sender, respond) => {
  if (message.type !== 'bridge') return;
  const own = sender.id === chrome.runtime.id;
  const canva = sender.tab && /^https:\/\/www\.canva\.com\/design\/[^/]+\/[^/]+\/edit(?:[?#]|$)/.test(sender.url || '');
  if (!own || !canva) { respond({error:'Chỉ nhận yêu cầu từ thiết kế Canva.'}); return; }
  (async () => {
    try {
      if (!['next','checkpoint','result','voice','ping'].includes(message.route)) throw Error('Lệnh không hợp lệ');
      const {token,enabled} = await chrome.storage.local.get(['token','enabled']);
      if (!enabled) {respond({disabled:true});return;}
      const response = await fetch('http://127.0.0.1:8766/'+message.route, {
        method:'POST', headers:{'Content-Type':'application/json','X-SKST-Token':token||''},
        body:JSON.stringify({...message.body,url:sender.url}), signal:AbortSignal.timeout(20000)
      });
      const data=await response.json();
      if (!response.ok) throw Error(data.error||'Không kết nối được ứng dụng');
      respond(data);
    } catch(e) {respond({error:e.message});}
  })();return true;
});
