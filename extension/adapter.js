/* DOM adapter for Canva's Vietnamese Video editor. No private APIs or cookie access. */
(() => {
  'use strict';
  const norm=s=>String(s||'').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/đ/g,'d');
  const label=e=>e.getAttribute('aria-label')||e.textContent?.trim()||'';
  const visible=e=>e&&!!(e.offsetWidth||e.offsetHeight||e.getClientRects().length)&&getComputedStyle(e).visibility!=='hidden';
  const find=(name,selector='button,[role="button"],[role="menuitem"],[role="tab"]')=>[...document.querySelectorAll(selector)].find(e=>visible(e)&&(typeof name==='string'?label(e)===name:name.test(label(e))));
  const sleep=ms=>new Promise(r=>setTimeout(r,ms));
  let guard=async()=>{};
  const wait=async(fn,message='Canva chưa sẵn sàng',ms=16000)=>{
    const deadline=Date.now()+ms;
    while(Date.now()<deadline){await guard();const v=fn();if(v)return v;await sleep(250);}
    throw Error(message+'. Ứng dụng đã dừng để giữ nguyên tiến độ.');
  };
  const click=async(e)=>{await guard();if(!e)throw Error('Không tìm thấy nút thao tác');e.scrollIntoView({block:'nearest',inline:'nearest'});e.click();await sleep(250);};
  const fill=(el,value)=>{
    const proto=el instanceof HTMLTextAreaElement?HTMLTextAreaElement.prototype:HTMLInputElement.prototype;
    Object.getOwnPropertyDescriptor(proto,'value').set.call(el,value);
    el.dispatchEvent(new Event('input',{bubbles:true}));el.dispatchEvent(new Event('change',{bubbles:true}));
  };
  const key=(el,k)=>{el.dispatchEvent(new KeyboardEvent('keydown',{key:k,code:k,bubbles:true}));el.dispatchEvent(new KeyboardEvent('keyup',{key:k,code:k,bubbles:true}));};
  const menus=()=>[...document.querySelectorAll('[role="menu"],[role="dialog"]')].filter(visible);
  const endButton=()=>[...document.querySelectorAll('button,[role="button"]')].filter(e=>label(e)==='Thêm nội dung đa phương tiện/cảnh trống').at(-1);
  const timeline=()=>[...document.querySelectorAll('[data-role="timeline-scene"]')].map(e=>{
    let parent=e.parentElement;
    for(let i=0;i<4&&parent&&!parent.querySelector('[role="slider"]');i++)parent=parent.parentElement;
    const sliders=parent?[...parent.querySelectorAll('[role="slider"]')]:[];
    const val=kind=>Number(sliders.find(s=>label(s).includes(kind))?.getAttribute('aria-valuenow')||0)/1e6;
    const image=e.querySelector('img');return {start:val('biên bắt đầu'),end:val('biên kết thúc'),image:image?.src||'',element:e};
  });
  const tail=async()=>{
    const end=await wait(endButton,'Không tìm thấy timeline video mới của Canva');end.scrollIntoView({block:'nearest',inline:'end'});await sleep(700);
    const rows=timeline();return rows.reduce((best,row)=>row.end>best.end?row:best,{start:0,end:0,image:''});
  };
  const cards=()=>[...document.querySelectorAll('[role="button"][draggable="true"][aria-label]')].filter(visible).map(el=>{
    const group=el.closest('[role="group"]')||el.parentElement;
    const src=group.querySelector('img')?.src||'';
    const id=src.match(/video-public\.canva\.com\/([^/]+)/)?.[1]||src.split('?')[0]||'title:'+norm(label(el));
    const m=group.textContent.match(/(\d+(?:[.,]\d+)?)\s*(?:giây|seconds?|s\b)/i);
    return {el,id,title:label(el),duration:m?Number(m[1].replace(',','.')):0};
  });
  function score(card,scene){
    const text=norm(card.title);let n=0;
    for(const word of scene.positive||[])if(text.includes(norm(word)))n+=4;
    for(const word of scene.negative||[])if(text.includes(norm(word)))n-=100;
    if(/elderly|senior|aged|older|middle aged/.test(text))n+=2;
    if(scene.preferred&&text===norm(scene.preferred))n+=100;
    return n;
  }
  const closeMenu=async()=>{
    if(menus().length){key(document.activeElement||document.body,'Escape');await wait(()=>!menus().length,'Không đóng được bảng thao tác',3500);}
  };
  const prepare=async(scene)=>{
    await closeMenu();
    const last=await tail();
    if(Math.abs(last.end-scene.start)>.12&&!(scene.start===0&&!last.image))throw Error(`Timeline đang kết thúc ở ${last.end.toFixed(2)} giây, cần ${scene.start.toFixed(2)} giây. Kiểm tra cảnh dở trước khi tiếp tục.`);
    if(scene.start===0&&!last.image){
      await click(await wait(()=>find('Video','[role="tab"]'),'Không thấy mục Video'));
      await wait(()=>document.querySelector('input[aria-label="Tìm kiếm video"]'),'Không thấy ô tìm kiếm video');return;
    }
    const plus=endButton();await click(plus);
    let stock=find('Video stock','[role="menuitem"],button,[role="button"],span');
    if(!stock){await sleep(400);stock=find('Video stock','[role="menuitem"],button,[role="button"],span');}
    if(!stock){await click(endButton());stock=await wait(()=>find('Video stock','[role="menuitem"],button,[role="button"],span'),'Không mở được Video stock');}
    await click(stock);
    await wait(()=>document.querySelector('input[aria-label="Tìm kiếm video"]'),'Không tìm thấy ô tìm kiếm video');
  };
  const choose=async(scene,used)=>{
    for(const query of scene.queries){
      const input=await wait(()=>document.querySelector('input[aria-label="Tìm kiếm video"]'));
      fill(input,query);key(input,'Enter');
      await wait(()=>!(input.getAttribute('aria-busy')==='true'),'Tìm video chưa xong');
      await sleep(2200);await guard();
      const candidates=cards().filter(c=>!used.includes(c.id)&&!used.includes('title:'+norm(c.title))&&c.duration>=scene.duration-.05&&score(c,scene)>-50).sort((a,b)=>score(b,scene)-score(a,scene));
      if(candidates.length)return candidates[0];
    }
    throw Error('Không tìm được video đủ dài và chưa dùng cho: '+scene.text+'. Hãy sửa từ khóa cảnh rồi tiếp tục.');
  };
  const trim=async(duration)=>{
    const button=await wait(()=>find(/^Xén video dài/),'Không tìm thấy công cụ cắt video');await click(button);
    const field=await wait(()=>[...document.querySelectorAll('input')].find(e=>visible(e)&&e.getAttribute('aria-label')==='--'),'Không tìm thấy ô độ dài video');
    fill(field,String(duration));key(field,'Enter');
    await click(await wait(()=>find('Xong'),'Không tìm thấy nút Xong'));
    await wait(()=>find(/^Xén video dài/),'Canva chưa áp dụng đoạn cắt');
  };
  const mute=async()=>{
    const volume=find('Âm lượng');
    if(!volume)throw Error('Không tìm thấy Âm lượng. Kiểm tra video đã được chọn.');
    await click(volume);
    const checkbox=await wait(()=>find(/^(Tắt tiếng|Bật tiếng)$/,'[role="checkbox"],input[type="checkbox"],button,[role="button"]'),'Không tìm thấy nút tắt âm thanh');
    const state=checkbox.getAttribute('aria-checked');
    if(label(checkbox)==='Tắt tiếng'&&state!=='true')await click(checkbox);
    await closeMenu();
    // Volume can be a non-modal popover; Escape closes it without touching timeline.
    key(document.activeElement||document.body,'Escape');await sleep(250);
  };
  const ensureBackground=async()=>{
    await tail();const last=timeline().at(-1)||{};
    if(last.image&&last.end>last.start)return;
    const toolbar=document.querySelector('[role="toolbar"][aria-label*="Kiểm soát"]');
    const videos=[...document.querySelectorAll('video')].filter(visible);
    const canvasVideo=videos.find(e=>e.getBoundingClientRect().left>400);
    if(!canvasVideo)throw Error('Video chưa phủ nền. Hãy chọn video rồi đặt làm nền trong Canva, sau đó tiếp tục.');
    const r=canvasVideo.getBoundingClientRect();canvasVideo.dispatchEvent(new MouseEvent('contextmenu',{bubbles:true,clientX:r.x+r.width/2,clientY:r.y+r.height/2,button:2}));
    await click(await wait(()=>find('Đặt video làm nền','[role="menuitem"],button,[role="button"]'),'Không đặt được video làm nền'));
  };
  async function sceneTask(task,checkpoint){
    const s=task.scene;let asset=task.phase?.asset,title=task.phase?.title||'';
    if(task.phase?.stage==='insert_intent')throw Error('Lần trước dừng ngay lúc chèn cảnh. Kiểm tra Canva và dùng Xử lý cảnh bị dở trong ứng dụng.');
    if(!['inserted','trimmed','muted'].includes(task.phase?.stage)){
      await prepare(s);const selected=await choose(s,task.used||[]);asset=selected.id;title=selected.title;
      await checkpoint('insert_intent',{asset,title});await click(selected.el);
      await wait(()=>find(/^Xén video dài/),'Video chưa được đưa vào timeline');
      await checkpoint('inserted',{asset,title});
    } else {
      const last=await tail();
      if(last.element)await click(last.element);
      await wait(()=>find(/^Xén video dài/),'Hãy chọn video cuối timeline để tiếp tục');
    }
    await ensureBackground();await trim(s.duration);await checkpoint('trimmed',{asset,title});
    await mute();await checkpoint('muted',{asset,title});
    const last=await tail();
    if(Math.abs(last.start-s.start)>.12||Math.abs(last.end-(s.start+s.duration))>.12)throw Error('Độ dài/vị trí cảnh chưa khớp lời đọc. Kiểm tra cảnh cuối timeline, không thêm lại video.');
    return {asset,title};
  }
  async function voiceTask(task,checkpoint,voice){
    if(task.phase?.stage==='upload_intent')throw Error('Voice có thể đã được tải. Kiểm tra Canva trước khi thử lại.');
    const last=await tail();
    if(last.image||last.end>5.1)throw Error('Cần thiết kế video ngang trống để bắt đầu. Ứng dụng không ghi đè bản dựng có sẵn.');
    await click(await wait(()=>find('Tải lên','[role="tab"]'),'Không thấy mục Tải lên'));
    const raw=await voice();
    const inputs=[...document.querySelectorAll('input[type="file"]')];
    const input=inputs.find(e=>/audio|mp3/.test(e.accept))||inputs.find(e=>!e.accept||/video/.test(e.accept));
    if(!input)throw Error('Không tìm thấy ô tải voice của Canva. Tải voice thủ công rồi kiểm tra kết nối.');
    const bytes=Uint8Array.from(atob(raw.data),c=>c.charCodeAt(0));
    const transfer=new DataTransfer();transfer.items.add(new File([bytes],raw.name,{type:'audio/mpeg'}));
    await checkpoint('upload_intent');input.files=transfer.files;input.dispatchEvent(new Event('change',{bubbles:true}));
    const audioTab=await wait(()=>find('Âm thanh','[role="tab"],button,[role="button"]'),'Đợi Canva hiển thị âm thanh tải lên',90000);await click(audioTab);
    const name=raw.name.replace(/\.mp3$/i,'');
    const card=await wait(()=>find(new RegExp(name.replace(/[.*+?^${}()|[\]\\]/g,'\\$&'))),'Đợi voice tải lên Canva',120000);
    await click(card);
    await wait(()=>[...document.querySelectorAll('button')].some(e=>label(e).includes(raw.name)&&label(e).includes('đoạn âm thanh')),'Voice chưa xuất hiện trên timeline');
    return {};
  }
  async function exportTask(task,checkpoint){
    if(task.phase?.stage==='export_intent')throw Error('Có lần xuất chưa xác nhận. Kiểm tra mục tải xuống Canva.');
    await closeMenu();await click(await wait(()=>find('Chia sẻ','button,[role="button"],[role="menuitem"]'),'Không thấy Chia sẻ'));
    await click(await wait(()=>find('Tải xuống'),'Không thấy Tải xuống'));
    const mp4=()=>[...document.querySelectorAll('body')][0].textContent.includes('Video MP4');
    if(!mp4())throw Error('Chọn định dạng Video MP4 trong bảng tải xuống, rồi tiếp tục.');
    await checkpoint('export_intent');
    await click(await wait(()=>[...document.querySelectorAll('button')].filter(e=>visible(e)&&label(e)==='Tải xuống'&&!e.disabled).at(-1),'Nút tải xuống chưa sẵn sàng'));
    await wait(()=>/Đang tải xuống|Nếu quá trình tải xuống/.test(document.body.innerText),'Canva chưa bắt đầu xuất video',30000);
    return {};
  }
  globalThis.SKSTAdapter={norm,score,timeline,cards,run:async(task,check,voice)=>{
    guard=()=>check();await guard();
    const checkpoint=(stage,extra={})=>check(stage,extra);
    if(task.kind==='scene')return sceneTask(task,checkpoint);
    if(task.kind==='voice')return voiceTask(task,checkpoint,voice);
    if(task.kind==='export')return exportTask(task,checkpoint);
    throw Error('Loại thao tác không hợp lệ');
  }};
})();
