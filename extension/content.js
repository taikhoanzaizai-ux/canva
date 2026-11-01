(() => {
  if(window.__skstContentStarted)return;window.__skstContentStarted=true;
  const client=crypto.randomUUID();let busy=false;
  chrome.runtime.onMessage.addListener((message,sender,respond)=>{
    if(message.type==='skst_controller_ping'){respond({ready:true,version:chrome.runtime.getManifest().version});return;}
  });
  async function api(route,body={}){
    const result=await chrome.runtime.sendMessage({type:'bridge',route,body:{...body,client,title:document.title}});
    if(!result)throw Error('Tiện ích chưa phản hồi. Bấm Kết nối Canva để gắn lại bộ dựng.');
    if(result?.error)throw Error(result.error);
    if(result?.disabled)throw Error('Đã ngắt tiện ích');
    return result;
  }
  async function cycle(){
    if(busy)return;busy=true;let task;
    try{
      const result=await api('next');task=result.task;if(!task)return;
      const check=async(stage,extra={})=>{
        const state=await api('checkpoint',{id:task.id,...(stage?{stage,...extra}:{})});
        if(!state.continue_)throw Error('Đã tạm dừng theo yêu cầu.');
      };
      const output=await SKSTAdapter.run(task,check,()=>api('voice',{id:task.id}));
      await api('result',{id:task.id,...output});
    }catch(e){
      if(task){try{await api('result',{id:task.id,error:e.message});}catch{}}
      // Connection loss never causes an implicit duplicate click. Server retains phase.
    }finally{busy=false;}
  }
  setInterval(cycle,1700);
  cycle();
})();
