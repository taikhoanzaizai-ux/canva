(() => {
  const version=chrome.runtime.getManifest().version;
  if(window.__skstContentStarted===version)return;
  window.__skstContentStarted=version;
  const epoch=crypto.randomUUID();window.__skstControllerEpoch=epoch;
  const active=()=>window.__skstControllerEpoch===epoch;
  const client=crypto.randomUUID();let busy=false,dismissedWarning=null;
  chrome.runtime.onMessage.addListener((message,sender,respond)=>{
    if(message.type==='skst_controller_ping'){respond({ready:true,version:chrome.runtime.getManifest().version});return;}
  });
  async function api(route,body={}){
    if(!active())throw Error('Bộ dựng cũ đã được thay bằng bản cập nhật.');
    const result=await chrome.runtime.sendMessage({type:'bridge',route,body:{title:document.title,...body,client}});
    if(!result)throw Error('Tiện ích chưa phản hồi. Bấm Kết nối Canva để gắn lại bộ dựng.');
    if(result?.error)throw Error(result.error);
    if(result?.disabled)throw Error('Đã ngắt tiện ích');
    return result;
  }
  function showStatus(result){
    if(!active())return;
    const existing=document.getElementById('skst-progress-status');
    if(result.mode!=='attention'){existing?.remove();dismissedWarning=null;return;}
    const message='SKST đã tạm dừng: '+(result.message||'Kiểm tra thông báo trong ứng dụng.');
    if(message===dismissedWarning||existing?.dataset.warning===message)return;
    dismissedWarning=null;
    existing?.remove();
    const panel=document.createElement('div');panel.id='skst-progress-status';panel.dataset.warning=message;
    panel.style.cssText='position:fixed;bottom:12px;right:12px;max-width:420px;padding:12px 44px 12px 16px;background:#fff4df;color:#523700;border:1px solid #dba650;border-radius:8px;font:14px/1.5 Arial,sans-serif;z-index:2147483647;box-shadow:0 2px 10px #0002;pointer-events:none';
    const text=document.createElement('span');text.textContent=message;text.setAttribute('role','status');
    const close=document.createElement('button');
    close.type='button';close.textContent='×';close.title='Đóng cảnh báo SKST';close.setAttribute('aria-label',close.title);
    close.style.cssText='position:absolute;top:6px;right:6px;width:28px;height:28px;padding:0;border:0;border-radius:4px;background:transparent;color:inherit;font:22px/1 Arial,sans-serif;cursor:pointer;pointer-events:auto';
    close.addEventListener('click',event=>{event.stopPropagation();dismissedWarning=message;panel.remove();});
    panel.append(text,close);document.body.appendChild(panel);
  }
  function openExportTarget(target){
    const url=new URL(target);
    if(url.origin!=='https://www.canva.com'||!/^\/design\/[^/]+\/[^/]+\/edit\/?$/.test(url.pathname))throw Error('Link phần cần xuất không hợp lệ.');
    window.location.assign(url.href);
  }
  async function cycle(){
    if(busy||!active())return;busy=true;let task,advance=false;
    try{
      const blank_video=!!document.querySelector('button[aria-label="Thêm nội dung đa phương tiện/cảnh trống"]')&&!document.querySelector('[data-role="timeline-scene"] img')&&![...document.querySelectorAll('button,[role="button"]')].some(e=>(e.getAttribute('aria-label')||'').includes('đoạn âm thanh'));
      const result=await api('next',{blank_video});showStatus(result);
      if(result.export_target){openExportTarget(result.export_target);return;}
      task=result.task;if(!task)return;
      const check=async(stage,extra={})=>{
        const state=await api('checkpoint',{id:task.id,review_token:task.review_token,...(stage?{stage,...extra}:{})});
        if(!state.continue_)throw Error('Đã tạm dừng theo yêu cầu.');
      };
      const fallback=async()=>{
        for(let i=0;i<240;i++){
          const result=await api('fallback',{id:task.id,retry:i===0});if(!result.pending)return result;
          await check();await new Promise(r=>setTimeout(r,1000));
        }
        throw Error('Tư liệu dự phòng chưa chuẩn bị xong. Tiến độ được giữ để tiếp tục.');
      };
      let output=await SKSTAdapter.run(task,check,()=>api('voice',{id:task.id}),()=>api('title',{id:task.id}),fallback);
      if(task.kind==='next_design'){
        output=await chrome.runtime.sendMessage({type:'open_next',body:{id:task.id,client,phase:task.phase,create_url:output.create_url}});
        if(!output||output.error)throw Error(output?.error||'Chưa mở được thiết kế tiếp theo.');
      }
      const outcome=await api('result',{id:task.id,...output});
      if(outcome.export_target){
        openExportTarget(outcome.export_target);return;
      }
      advance=true;
    }catch(e){
      if(task){
        try{const result=await api('result',{id:task.id,review_token:task.review_token,error:e.message});
          advance=result.continuing===true;
          showStatus({mode:'attention',message:result.continuing?'Cảnh '+task.id+': '+e.message+' Đang chèn thẻ lỗi rồi tiếp tục.':e.message});
        }catch(connectionError){showStatus({mode:'attention',message:'Mất kết nối khi báo lỗi cảnh '+task.id+': '+connectionError.message+'. Đang thử nối lại; tiến độ được giữ.'});}
      }else showStatus({mode:'attention',message:'Chưa nhận được lệnh dựng: '+e.message+'. Đang thử kết nối lại.'});
      // Connection loss never causes an implicit duplicate click. Server retains phase.
    }finally{busy=false;if(advance&&active())void cycle();}
  }
  setInterval(cycle,1700);
  cycle();
})();
