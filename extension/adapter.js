/* DOM adapter for Canva's Vietnamese Video editor. No private APIs or cookie access. */
(() => {
  'use strict';
  const norm=s=>String(s||'').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/đ/g,'d');
  const label=e=>{
    const explicit=e.getAttribute('aria-label');if(explicit)return explicit;
    // Canva renders duplicate tab captions; the decorative copy is aria-hidden.
    // Match the accessible caption instead of "Âm thanhÂm thanh" textContent.
    const copy=typeof e.cloneNode==='function'?e.cloneNode(true):e;
    if(copy!==e)copy.querySelectorAll('[aria-hidden="true"],[hidden],script,style').forEach(n=>n.remove());
    return (copy.textContent||'').replace(/\s+/g,' ').trim();
  };
  const visible=e=>e&&!!(e.offsetWidth||e.offsetHeight||e.getClientRects().length)&&getComputedStyle(e).visibility!=='hidden';
  const find=(name,selector='button,[role="button"],[role="menuitem"],[role="tab"]')=>[...document.querySelectorAll(selector)].find(e=>visible(e)&&(typeof name==='string'?label(e)===name:name.test(label(e))));
  const sleep=ms=>new Promise(r=>setTimeout(r,ms));
  let guard=async()=>{};
  const wait=async(fn,message='Canva chưa sẵn sàng',ms=16000)=>{
    const deadline=Date.now()+ms;
    while(Date.now()<deadline){await guard();const v=fn();if(v)return v;await sleep(250);}
    throw Error('Hết thời gian chờ: '+message+' ('+Math.round(ms/1000)+' giây).');
  };
  const click=async(e)=>{await guard();if(!e)throw Error('Không tìm thấy nút thao tác');e.scrollIntoView({block:'nearest',inline:'nearest'});e.click();await sleep(250);};
  const fill=(el,value)=>{
    const proto=el instanceof HTMLTextAreaElement?HTMLTextAreaElement.prototype:HTMLInputElement.prototype;
    Object.getOwnPropertyDescriptor(proto,'value').set.call(el,value);
    el.dispatchEvent(new Event('input',{bubbles:true}));el.dispatchEvent(new Event('change',{bubbles:true}));
  };
  const key=(el,k)=>{const number={Enter:13,Escape:27,Tab:9}[k]||0;const options={key:k,code:k,keyCode:number,which:number,bubbles:true,cancelable:true};el.dispatchEvent(new KeyboardEvent('keydown',options));el.dispatchEvent(new KeyboardEvent('keyup',options));};
  function uploadInput(root=document,kind='audio'){
    // Canva currently uses a hidden accept="*/*" input, not audio/video-only.
    const eligible=[...root.querySelectorAll('input[type="file"]')].filter(e=>!e.disabled);
    const score=e=>{
      const types=(e.accept||'').toLowerCase().split(',').map(t=>t.trim());
      if(kind==='image'&&types.some(t=>t==='image/*'||t==='image/png'||t==='.png'))return 3;
      if(kind==='video'&&types.some(t=>t==='video/*'||t==='video/mp4'||t==='.mp4'))return 3;
      if(kind==='audio'&&types.some(t=>t==='audio/*'||t==='audio/mpeg'||t==='.mp3'||t==='.wav'))return 3;
      if(types.some(t=>t===''||t==='*'||t==='*/*'))return 2;
      return 0;
    };
    return eligible.filter(e=>score(e)>0).sort((a,b)=>score(b)-score(a))[0]||null;
  }
  function uploadedVideoTab(root=document){
    return [...root.querySelectorAll('[role="tab"],button,[role="button"]')].find(e=>visible(e)&&label(e)==='Video'&&!e.closest('[role="tablist"][aria-label="Bảng bên"]'))||null;
  }
  async function ensureUploadPanel(){
    const tab=await wait(()=>find('Tải lên','[role="tab"]'),'Không thấy mục Tải lên');
    // Clicking the selected sidebar tab collapses Canva's upload panel.
    if(tab.getAttribute('aria-selected')!=='true')await click(tab);
    await wait(()=>uploadInput(),'Bảng Tải lên chưa hiển thị ô chọn tệp');
  }
  function durationInput(root=document){
    return [...root.querySelectorAll('input')].find(e=>e.getAttribute('placeholder')==='--'||e.getAttribute('aria-label')==='--')||null;
  }
  function audioOnTimeline(name,root=document){
    return [...root.querySelectorAll('button,[role="button"]')].some(e=>label(e).includes(name)&&label(e).includes('đoạn âm thanh'));
  }
  function timelineTransitionMenu(element){
    if(element.getAttribute('role')!=='menu')return false;
    const items=[...element.querySelectorAll('[role="menuitem"]')];
    return items.length===1&&label(items[0])==='Thêm chuyển cảnh';
  }
  const menus=()=>[...document.querySelectorAll('[role="menu"],[role="dialog"]')].filter(e=>visible(e)&&!timelineTransitionMenu(e));
  const sceneCount=()=>document.querySelectorAll('[data-role="timeline-scene"]').length;
  const endButton=()=>[...document.querySelectorAll('button,[role="button"]')].filter(e=>label(e)==='Thêm nội dung đa phương tiện/cảnh trống').at(-1);
  const timeline=()=>{let previousEnd=0;return [...document.querySelectorAll('[data-role="timeline-scene"]')].map(e=>{
    let parent=e.parentElement;
    for(let i=0;i<4&&parent&&!parent.querySelector('[role="slider"]');i++)parent=parent.parentElement;
    const sliders=parent?[...parent.querySelectorAll('[role="slider"]')]:[];
    const val=kind=>Number(sliders.find(s=>label(s).includes(kind))?.getAttribute('aria-valuenow')||0)/1e6;
    const image=e.querySelector('img');
    const background=[...e.querySelectorAll('[style]')].map(n=>n.style.backgroundImage||'').find(s=>s.startsWith('url('))||'';
    const hasStart=sliders.some(s=>label(s).includes('biên bắt đầu'));
    const start=hasStart?val('biên bắt đầu'):previousEnd,end=val('biên kết thúc');previousEnd=end;
    return {start,end,image:image?.src||background,element:e};
  });};
  function timelineScroller(root=document){
    let el=root.querySelector('[data-role="timeline-scene"]');
    for(let i=0;el&&i<30;i++,el=el.parentElement){
      if(el.scrollWidth>el.clientWidth+20&&/auto|scroll/.test(getComputedStyle(el).overflowX))return el;
    }
    return null;
  }
  const tail=async()=>{
    const end=await wait(endButton,'Không tìm thấy timeline video mới của Canva');
    // The voice extends past the unfinished picture track. Scrolling to the
    // container's full width hides every scene; target the picture-track plus.
    end.scrollIntoView({block:'nearest',inline:'end'});
    await sleep(900);
    const rows=timeline();return rows.at(-1)||{start:0,end:0,image:''};
  };
  const cards=()=>[...document.querySelectorAll('[role="button"][draggable="true"][aria-label]')].filter(visible).map(el=>{
    const group=el.closest('[role="group"]')||el.parentElement;
    const src=group.querySelector('img')?.src||'';
    const id=src.match(/video-public\.canva\.com\/([^/]+)/)?.[1]||src.split('?')[0]||'title:'+norm(label(el));
    const m=group.textContent.match(/(\d+(?:[.,]\d+)?)\s*(?:giây|seconds?|s\b)/i);
    return {el,id,stock:/video-public\.canva\.com\//.test(src),title:label(el),duration:m?Number(m[1].replace(',','.')):0};
  });
  function photoCards(){
    return [...document.querySelectorAll('[role="button"][draggable="true"][aria-label]')].filter(visible).map(el=>{
      const group=el.closest('[role="group"]')||el.parentElement;
      const src=group.querySelector('img')?.src||'';const match=src.match(/media-public\.canva\.com\/[^/]+\/([^/]+)/);
      return {el,id:match?'photo:'+match[1]:'',title:label(el).replace(/^Thêm /,'').replace(/ ảnh vào khung vẽ$/,''),duration:Infinity,media_kind:'image'};
    }).filter(c=>c.id);
  }
  function realPerson(card){
    const t=norm(card.title);
    if(/animation|animated|cartoon|illustrat|3d|render|cgi|graphic|neon|rainbow|question mark|skeleton|anatom|hoat hinh|minh hoa|mo phong|stick figure|background|loop/.test(t))return false;
    return /\b(man|woman|men|women|person|people|senior|elderly|patient|doctor|therapist|adult|couple|male|female|hands|feet|foot|legs)\b|nguoi|bac si|benh nhan|ban chan|bap chan|doi chan|ban tay/.test(t);
  }
  function subjectMatch(title,term){
    const value=norm(term).replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
    return new RegExp('(^|[^a-z0-9])'+value+'(?:s|es)?($|[^a-z0-9])').test(norm(title));
  }
  function eligibleCards(items,scene,used){
    return items.filter(c=>!used.includes(c.id)&&!used.includes('title:'+norm(c.title))&&c.duration>=scene.duration-.05&&(scene.allow_all_media||realPerson(c))&&(!scene.subjects?.length||scene.subjects.some(w=>subjectMatch(c.title,w)))&&(scene.allow_all_media||!scene.actions?.length||scene.actions.some(w=>norm(c.title).includes(norm(w))))&&score(c,scene)>=4).sort((a,b)=>score(b,scene)-score(a,scene));
  }
  function relatedCards(items,scene,used){
    return items.filter(c=>!used.includes(c.id)&&!used.includes('title:'+norm(c.title))&&c.duration>=scene.duration+.1&&(scene.allow_all_media||realPerson(c))&&(!scene.subjects?.length||scene.subjects.some(w=>subjectMatch(c.title,w)))&&score(c,scene)>=4).sort((a,b)=>score(b,scene)-score(a,scene));
  }
  function reuseEligibleCards(items,scene,used){
    const times=id=>scene._usage?.[id]||(used.includes(id)?1:0);
    return eligibleCards(items,scene,[]).sort((a,b)=>{
      const penalty=c=>times(c.id)*100+(c.id===scene._lastAsset?10000:0);
      return penalty(a)-penalty(b)||score(b,scene)-score(a,scene);
    });
  }
  function rememberReuse(scene,key,query,items,used){
    if(eligibleCards(items,scene,[]).some(c=>used.includes(c.id))){
      scene[key]||=[];if(!scene[key].includes(query))scene[key].push(query);
    }
  }
  function score(card,scene){
    const text=norm(card.title);let n=0;
    for(const word of scene.positive||[])if(text.includes(norm(word)))n+=4;
    for(const [index,word] of (scene.subjects||[]).entries())if(subjectMatch(text,word))n+=index<2?8:2;
    for(const word of scene.negative||[])if(text.includes(norm(word)))n-=100;
    if(/elderly|senior|aged|older|middle aged/.test(text))n+=2;
    if(scene.preferred&&text===norm(scene.preferred))n+=100;
    return n;
  }
  const closeMenu=async()=>{
    if(menus().length){key(document.activeElement||document.body,'Escape');await wait(()=>!menus().length,'Không đóng được bảng thao tác',3500);}
  };
  const selectClip=async(row)=>{
    if(!row?.element)throw Error('Không tìm thấy clip cần chọn');
    // The thumbnail can have zero width for legacy 1ms clips. Its own page
    // button still has a direct selection handler; do not hit a neighbour.
    const button=row.element.querySelector('button[aria-label="Tùy chọn về trang"],[role="button"][aria-label="Tùy chọn về trang"]');
    await click(button||row.element);await closeMenu();
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
  const prepareUpload=async(scene)=>{
    await closeMenu();const last=await tail();
    if(Math.abs(last.end-scene.start)>.12&&!(scene.start===0&&!last.image))throw Error('Timeline chưa ở đúng mốc chèn tiêu đề.');
    if(!(scene.start===0&&!last.image)){
      await click(endButton());
      await click(await wait(()=>find('Tải lên','[role="menuitem"]'),'Không mở được mục tải lên cho cảnh mới'));
    }
  };
  function searchReady(input,query,items,previous,elapsed){
    if(!input||norm(input.value).trim()!==norm(query).trim()||input.getAttribute('aria-busy')==='true')return false;
    const signature=items.map(c=>c.id).join('|');
    // Canva truncates captions and varies localized headings. Verify the actual
    // input plus a settled result grid instead of requiring a literal caption.
    return !!items.length&&(signature!==previous||elapsed>=3000);
  }
  const choose=async(scene,used,allowReuse=false)=>{
    if(scene.requires_review&&!scene.allow_all_media)throw Error('Cảnh cần từ khóa cụ thể: '+scene.text);
    for(const query of (allowReuse?scene._reuseVideoQueries||[]:scene.queries)){
      for(let attempt=0;attempt<2;attempt++){
        const input=await wait(()=>document.querySelector('input[aria-label="Tìm kiếm video"]'),'Không thấy ô tìm kiếm video khi đổi từ khóa');
        const previous=cards().map(c=>c.id).join('|');
        fill(input,query);await sleep(350);await guard();
        const liveInput=await wait(()=>document.querySelector('input[aria-label="Tìm kiếm video"]'),'Không thấy ô tìm kiếm video khi đổi từ khóa');
        key(liveInput,'Enter');const started=Date.now();let settled=false;
        for(let poll=0;poll<60;poll++){
          await guard();await sleep(250);
          const current=document.querySelector('input[aria-label="Tìm kiếm video"]');
          if(searchReady(current,query,cards().filter(c=>c.stock),previous,Date.now()-started)){settled=true;break;}
        }
        if(!settled)continue; // Only repeat read-only searches, never insertion.
        await sleep(700);
        for(let page=0;page<4;page++){
          await guard();const items=cards().filter(c=>c.stock);
          if(!allowReuse)rememberReuse(scene,'_reuseVideoQueries',query,items,used);
          const found=allowReuse?reuseEligibleCards(items,scene,used):eligibleCards(items,scene,used);
          if(found.length)return found[0];
          const last=cards().at(-1);if(last)last.el.scrollIntoView({block:'end',inline:'nearest'});
          await sleep(1500);
        }
        const related=relatedCards(cards().filter(c=>c.stock),scene,used);
        if(related.length)return related[0];
        break;
      }
    }
    throw Error('Không tìm được video đúng từ khóa, đủ dài cho: '+scene.text+'. Hãy sửa từ khóa cảnh rồi tiếp tục.');
  };
  const choosePhoto=async(scene,used,allowReuse=false)=>{
    if(scene.requires_review&&!scene.allow_all_media)return null;
    await closeMenu();const last=await tail();
    if(Math.abs(last.end-scene.start)>.12&&!(scene.start===0&&!last.image))throw Error('Timeline chưa đúng mốc tìm ảnh.');
    if(scene.start===0&&!last.image){await click(await wait(()=>find('Ảnh','[role="tab"]'),'Không thấy mục Ảnh'));}
    else{await click(endButton());await click(await wait(()=>find('Ảnh stock','[role="menuitem"]'),'Không thấy Ảnh stock'));}
    const inputFn=()=>[...document.querySelectorAll('input')].find(e=>visible(e)&&/^Tìm kiếm.*Ảnh/.test(e.getAttribute('aria-label')||''));
    for(const query of (allowReuse?scene._reusePhotoQueries||[]:scene.queries)){
      const input=await wait(inputFn,'Không thấy ô tìm kiếm ảnh');fill(input,query);await sleep(350);
      key(await wait(inputFn,'Không thấy ô tìm kiếm ảnh sau khi nhập'),'Enter');await sleep(2200);
      for(let page=0;page<4;page++){
        await guard();const items=photoCards();if(!allowReuse)rememberReuse(scene,'_reusePhotoQueries',query,items,used);
        const candidates=allowReuse?reuseEligibleCards(items,scene,used):eligibleCards(items,scene,used);
        if(candidates.length)return candidates[0];
        const lastPhoto=photoCards().at(-1);if(lastPhoto)lastPhoto.el.scrollIntoView({block:'end'});
        await sleep(1500);
      }
    }
    return null;
  };
  const timePhoto=async(duration)=>{
    // React commits this popover on blur. A synthetic Enter/Escape alone can
    // leave the edited number visible while the scene remains at five seconds.
    let field=durationInput();
    if(!visible(field))await click(await wait(()=>find(/giây, sửa thời gian$/),'Không thấy thời lượng ảnh'));
    field=await wait(()=>{const e=durationInput();return visible(e)?e:null;},'Không thấy ô đặt thời gian ảnh');
    field.focus();fill(field,String(Math.round(duration*1000)/1000));key(field,'Enter');
    field.blur();await sleep(500);
    key(document.activeElement||document.body,'Escape');
    await wait(()=>{
      const button=find(/giây, sửa thời gian$/);
      const value=label(button||{getAttribute:()=>null,textContent:''}).match(/([\d]+(?:[.,]\d+)?)\s*giây/);
      return value&&Math.abs(Number(value[1].replace(',','.'))-duration)<=.12;
    },'Canva chưa áp dụng thời lượng ảnh sau khi xác nhận',6000);
  };
  const trim=async(duration)=>{
    const button=await wait(()=>find(/^Xén video dài/),'Không tìm thấy công cụ cắt video');await click(button);
    const field=await wait(()=>{const e=durationInput();return visible(e)?e:null;},'Không tìm thấy ô độ dài video');
    fill(field,String(duration));key(field,'Enter');
    await click(await wait(()=>find('Xong'),'Không tìm thấy nút Xong'));
    await wait(()=>find(/^Xén video dài/),'Canva chưa áp dụng đoạn cắt');await sleep(700);
  };
  const mute=async()=>{
    let volume=find(/^Âm lượng/);
    if(!volume){
      const more=find('Mở thêm tùy chọn kiểm soát cho thành phần đã chọn');
      if(more){await click(more);volume=find(/^Âm lượng/);}
    }
    if(!volume){
      // Canva omits this control for silent stock, including the live-tested
      // "asian elderly male knee pain" clip. Do not stop an otherwise valid cut.
      key(document.activeElement||document.body,'Escape');return;
    }
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
  async function sceneTask(task,checkpoint,fallbackAsset){
    const s=task.scene;s._usage=task.usage||{};s._lastAsset=task.last_asset||'';let asset=task.phase?.asset,title=task.phase?.title||'';
    if(s.timing_original_duration<.1&&task.previous_scene&&['inserted','trimmed','muted'].includes(task.phase?.stage)){
      const last=await tail(),prev=task.previous_scene;
      if(sceneCount()===s.id-1&&last.end-last.start<.1&&Math.abs(last.start-prev.start)<=.12){
        await selectClip(last);await trim(s.start-last.start);
        const restored=await tail();if(Math.abs(restored.end-s.start)>.12)throw Error('Chưa phục hồi đủ thời lượng cảnh trước.');
      }
      const ready=await tail();
      if(sceneCount()===s.id-1&&Math.abs(ready.end-s.start)<=.12)await checkpoint('ready_after_repair');
    }
    if(task.phase?.stage==='insert_intent')throw Error('Lần trước dừng ngay lúc chèn cảnh. Kiểm tra Canva và dùng Xử lý cảnh bị dở trong ứng dụng.');
    if(!['inserted','trimmed','muted'].includes(task.phase?.stage)){
      await prepare(s);let selected;
      try{selected=await choose(s,task.used||[]);}catch(error){
        if(/đã tạm dừng|Phiên thao tác|Timeline|cảnh dở/i.test(error.message))throw error;
        const trySearch=async(fn)=>{try{return await fn();}catch(e){if(/đã tạm dừng|Phiên thao tác|Timeline|cảnh dở|mã kết nối|đã ngắt/i.test(e.message))throw e;return null;}};
        selected=await trySearch(()=>choosePhoto(s,task.used||[]));
        if(!selected&&s._reuseVideoQueries?.length){
          await prepare(s);selected=await trySearch(()=>choose(s,task.used||[],true));
        }
        if(!selected&&s._reusePhotoQueries?.length)selected=await trySearch(()=>choosePhoto(s,task.used||[],true));
        if(!selected){
          const generatedTask={...task,scene:{...s,title_text:s.text}};
          return await titleTask(generatedTask,checkpoint,fallbackAsset);
        }
      }
      asset=selected.id;title=selected.title+((task.used||[]).includes(asset)?' (dùng lại do thiếu tư liệu phù hợp khác)':'');task.media_kind=selected.media_kind||'video';
      await checkpoint('insert_intent',{asset,title,media_kind:task.media_kind});await click(selected.el);
      await wait(()=>task.media_kind==='image'?find(/giây, sửa thời gian$/):find(/^Xén video dài/),'Nội dung chưa được đưa vào timeline');
      await tail();
      if(sceneCount()!==s.id)throw Error(`Canva có ${sceneCount()} cảnh, đang chèn cảnh ${s.id}. Chưa xác nhận chèn thành công; kiểm tra cảnh dở để tránh chèn trùng.`);
      await checkpoint('inserted',{asset,title,media_kind:task.media_kind});
    } else {
      const last=await tail();
      if(last.element)await selectClip(last);
      task.media_kind=task.phase.media_kind||'video';
      await wait(()=>task.media_kind==='image'?find(/giây, sửa thời gian$/):find(/^Xén video dài/),'Hãy chọn cảnh cuối timeline để tiếp tục');
    }
    const selectedTail=await tail();
    if(sceneCount()!==s.id||Math.abs(selectedTail.start-s.start)>.12)throw Error('Cảnh cuối chưa đúng vị trí, chưa cắt để tránh sửa nhầm cảnh trước.');
    await selectClip(selectedTail);await ensureBackground();
    if(task.media_kind==='image'){
      const current=await tail();
      if(Math.abs(current.start-s.start)>.12)throw Error('Điểm bắt đầu ảnh chưa khớp voice; không thay đổi cảnh khác.');
      await timePhoto(s.start+s.duration-current.start);
    }else await trim(s.start+s.duration-selectedTail.start);
    await checkpoint('trimmed',{asset,title,media_kind:task.media_kind});
    if(task.media_kind!=='image')await mute();await checkpoint('muted',{asset,title,media_kind:task.media_kind});
    const last=await tail();
    if(Math.abs(last.start-s.start)>.12||Math.abs(last.end-(s.start+s.duration))>.12)throw Error('Độ dài/vị trí cảnh chưa khớp lời đọc. Kiểm tra cảnh cuối timeline, không thêm lại video.');
    return {asset,title};
  }
  async function rollbackScene(task,checkpoint){
    const s=task.scene;await closeMenu();
    let last=await tail();
    if(sceneCount()===s.id-1&&Math.abs(last.end-s.start)<=.12){await checkpoint('rollback_done');return;}
    if(sceneCount()!==s.id||Math.abs(last.start-s.start)>.12||!last.element)throw Error('Không xác định được riêng cảnh cuối để thay thẻ lỗi.');
    await selectClip(last);
    const pageMenu=()=>last.element.querySelector('button[aria-label="Tùy chọn về trang"],[role="button"][aria-label="Tùy chọn về trang"]');
    await click(await wait(pageMenu,'Không thấy menu của cảnh cuối cần thay'));
    const remove=await wait(()=>find(/^Xóa(?:\s|$)/,'[role="menuitem"]'),'Không thấy Xóa trong menu cảnh cuối');
    await checkpoint('rollback_intent',{reason:task.failure});await click(remove);
    await wait(()=>sceneCount()===s.id-1||(s.id===1&&sceneCount()===1&&!timeline().at(-1)?.image),'Canva chưa gỡ cảnh lỗi khỏi timeline');
    last=await tail();
    if(s.id>1&&Math.abs(last.end-s.start)>.12)throw Error('Sau khi gỡ cảnh lỗi, cuối hình chưa khớp mốc voice.');
    await checkpoint('rollback_done');
  }
  async function errorCardTask(task,checkpoint,assetData){
    const s=task.scene;
    if(['inserted','trimmed','muted'].includes(task.phase?.stage)){
      const last=await tail();if(!last.element)throw Error('Không thấy thẻ lỗi vừa chèn để đặt thời lượng');
      await selectClip(last);
    }else{
      if(task.phase?.stage==='insert_intent')throw Error('Thẻ lỗi đang chèn dở; chưa tự chèn lại.');
      const raw=await assetData();
      if(raw.mime!=='image/png')throw Error('Thẻ lỗi phải là ảnh PNG, không dùng lại clip Video tải lên đang lỗi.');
      task.fallback_id=raw.asset_id;
      const name=raw.name.replace(/\.png$/i,'');
      const uploaded=()=>{const e=find(new RegExp(name));return e&&!e.closest('[role="group"]')?.querySelector('[role="progressbar"]')?e:null;};
      const imageTab=()=>[...document.querySelectorAll('[role="tab"],button,[role="button"]')].find(e=>visible(e)&&['Hình ảnh','Images'].includes(label(e)));
      await closeMenu();await ensureUploadPanel();
      if(imageTab())await click(imageTab());
      if(!uploaded()){
        const input=await wait(()=>uploadInput(document,'image'),'Không thấy ô tải ảnh báo lỗi');
        const transfer=new DataTransfer();transfer.items.add(new File([Uint8Array.from(atob(raw.data),c=>c.charCodeAt(0))],raw.name,{type:'image/png'}));
        await checkpoint('error_image_uploading',{asset:raw.name});input.files=transfer.files;input.dispatchEvent(new Event('change',{bubbles:true}));
      }
      for(let i=0;i<120&&!uploaded();i++){
        await guard();const tab=imageTab();if(tab&&tab.getAttribute('aria-selected')!=='true')await click(tab);await sleep(500);
      }
      await wait(uploaded,'Ảnh báo lỗi chưa tải xong',5000);
      await prepareUpload(s);
      await ensureUploadPanel();
      if(imageTab())await click(imageTab());
      const imageCard=await wait(uploaded,'Không thấy ảnh báo lỗi vừa tải');
      await checkpoint('insert_intent',{asset:raw.name,media_kind:'image'});await click(imageCard);
      await wait(()=>sceneCount()===s.id,'Chưa xác nhận được ảnh báo lỗi trên timeline');
      await checkpoint('inserted',{asset:raw.name,media_kind:'image'});
    }
    await ensureBackground();const before=await tail();
    if(Math.abs(before.start-s.start)>.12)throw Error('Thẻ lỗi không nằm đúng mốc voice');
    await timePhoto(s.start+s.duration-before.start);
    const last=await tail();
    if(Math.abs(last.end-s.start-s.duration)>.12)throw Error('Thẻ lỗi chưa đủ thời lượng voice');
    await checkpoint('trimmed',{media_kind:'image'});
    return {asset:task.fallback_id,title:'LỖI CẢNH '+task.id};
  }
  async function titleTask(task,checkpoint,assetData){
    const s=task.scene;const phase=task.phase?.stage;
    if(phase==='insert_intent')throw Error('Tiêu đề có thể đã được chèn. Dùng Xử lý cảnh bị dở trước khi tiếp tục để tránh trùng.');
    if(!['inserted','trimmed','muted'].includes(phase)){
      const raw=await assetData();task.fallback_id=raw.asset_id;
      const titleName=raw.name.replace(/\.mp4$/i,'');
      const uploaded=()=>{
        const e=find(new RegExp(titleName));if(!e)return null;
        const group=e.closest('[role="group"]')||e.parentElement;
        return !group?.querySelector('[role="progressbar"]')?e:null;
      };
      await ensureUploadPanel();
      const existingTab=uploadedVideoTab();if(existingTab)await click(existingTab);
      if(!uploaded()&&phase!=='title_uploading'){
        const input=await wait(()=>uploadInput(document,'video'),'Chưa có ô tải video tiêu đề');
        const bytes=Uint8Array.from(atob(raw.data),c=>c.charCodeAt(0));
        const transfer=new DataTransfer();transfer.items.add(new File([bytes],raw.name,{type:'video/mp4'}));
        await checkpoint('title_uploading',{asset:raw.name,title:s.title_text});
        input.files=transfer.files;input.dispatchEvent(new Event('change',{bubbles:true}));
      }
      const videoTab=await wait(uploadedVideoTab,'Chưa thấy Video sau khi tải tệp lên',60000);await click(videoTab);
      await wait(uploaded,'Chưa tải xong video tiêu đề',90000);
      await prepareUpload(s);
      await ensureUploadPanel();
      await click(await wait(()=>uploadedVideoTab(),'Không thấy thẻ Video trong Tải lên'));
      const card=await wait(()=>find(new RegExp(titleName)),'Không thấy video tiêu đề vừa tải');
      await checkpoint('insert_intent',{asset:raw.name,title:s.title_text});await click(card);
      await wait(()=>find(/^Xén video dài/),'Chưa chèn được video tiêu đề');
      await tail();if(sceneCount()!==s.id)throw Error('Số cảnh sau khi chèn tiêu đề chưa khớp. Kiểm tra cảnh dở, không chèn lại.');
      await checkpoint('inserted',{asset:raw.name,title:s.title_text});
    }else{const last=await tail();if(last.element)await selectClip(last);}
    await ensureBackground();await trim(s.duration);await checkpoint('trimmed',{title:s.title_text});
    const last=await tail();if(Math.abs(last.start-s.start)>.12||Math.abs(last.end-s.start-s.duration)>.12)throw Error('Mốc cảnh tiêu đề chưa khớp voice. Kiểm tra cảnh cuối trước khi tiếp tục.');
    return {title:s.title_text,asset:task.fallback_id};
  }
  async function voiceTask(task,checkpoint,voice){
    if(task.phase?.stage==='upload_intent')throw Error('Voice có thể đã được tải. Kiểm tra Canva trước khi thử lại.');
    const last=await tail();
    if(last.image||last.end>5.1)throw Error('Cần thiết kế video ngang trống để bắt đầu. Ứng dụng không ghi đè bản dựng có sẵn.');
    await ensureUploadPanel();
    const raw=await voice();
    const input=await wait(()=>uploadInput(),'Canva chưa hiển thị ô tải voice. Mở Tải lên và thử lại',30000);
    const bytes=Uint8Array.from(atob(raw.data),c=>c.charCodeAt(0));
    const transfer=new DataTransfer();transfer.items.add(new File([bytes],raw.name,{type:raw.mime||'audio/mpeg'}));
    await checkpoint('upload_intent');input.files=transfer.files;input.dispatchEvent(new Event('change',{bubbles:true}));
    const audioTab=await wait(()=>find('Âm thanh','[role="tab"],button,[role="button"]'),'Đợi Canva hiển thị âm thanh tải lên',90000);await click(audioTab);
    const name=raw.name.replace(/\.mp3$/i,'');
    const card=await wait(()=>find(new RegExp(name.replace(/[.*+?^${}()|[\]\\]/g,'\\$&'))),'Đợi voice tải lên Canva',120000);
    await click(card);
    await wait(()=>audioOnTimeline(raw.name),'Voice chưa xuất hiện trên timeline');
    return {};
  }
  async function auditTask(task){
    await closeMenu();const last=await tail();
    if(sceneCount()!==task.count)throw Error(`Canva có ${sceneCount()} cảnh, cần ${task.count} cảnh. Không chuyển phần khi số cảnh chưa khớp.`);
    if(Math.abs(last.end-task.duration)>.12)throw Error(`Hình kết thúc ở ${last.end.toFixed(3)} giây nhưng voice phần này dài ${task.duration.toFixed(3)} giây. Cần sửa cảnh cuối trước khi chuyển phần.`);
    const audio=[...document.querySelectorAll('button,[role="button"]')].find(e=>label(e).includes('SKST_voice_')&&label(e).includes('đoạn âm thanh'));
    if(!audio)throw Error('Không xác nhận được voice trên timeline; không chuyển sang phần mới.');
    const ends=[...audio.querySelectorAll('[role="slider"]')].filter(e=>label(e).includes('biên kết thúc')).map(e=>Number(e.getAttribute('aria-valuenow'))/1e6);
    if(!ends.length||Math.abs(Math.max(...ends)-task.duration)>.12)throw Error('Voice trên Canva chưa đủ thời lượng phần này. Không xuất hoặc chuyển phần.');
    return {verified_duration:last.end,verified_count:sceneCount()};
  }
  async function nextDesignTask(task,checkpoint){
    await closeMenu();await click(await wait(()=>find('Tệp'),'Không thấy menu Tệp'));
    await click(await wait(()=>find('Tạo thiết kế mới'),'Không thấy Tạo thiết kế mới'));
    const link=await wait(()=>find('Video khổ ngang','a'),'Không thấy định dạng Video khổ ngang');
    const href=link.href;
    if(!/^https:\/\/www\.canva\.com\/design\?/.test(href)||!new URL(href).searchParams.has('create'))throw Error('Đường dẫn tạo video không hợp lệ.');
    return {create_url:href};
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
  globalThis.SKSTAdapter={norm,label,score,realPerson,subjectMatch,eligibleCards,reuseEligibleCards,relatedCards,searchReady,timelineScroller,timeline,tail,timePhoto,rollbackScene,cards,photoCards,uploadInput,uploadedVideoTab,ensureUploadPanel,durationInput,audioOnTimeline,timelineTransitionMenu,run:async(task,check,voice,titleAsset,fallbackAsset)=>{
    guard=()=>check();await guard();
    const checkpoint=async(stage,extra={})=>{await check(stage,extra);task.phase={stage,...extra};};
    try{
    if(task.kind==='scene'&&['rollback_intent','rollback_done'].includes(task.phase?.stage)){
      const reason=task.phase.reason||'Tiếp tục thay cảnh lỗi bằng thẻ chữ';
      await rollbackScene(task,checkpoint);throw Error(reason);
    }
    if(task.kind==='scene'&&task.scene.error_card)return await errorCardTask(task,checkpoint,fallbackAsset);
    if(task.kind==='scene')return task.scene.kind==='title'?await titleTask(task,checkpoint,titleAsset):await sceneTask(task,checkpoint,fallbackAsset);
    if(task.kind==='voice')return voiceTask(task,checkpoint,voice);
    if(task.kind==='audit')return auditTask(task);
    if(task.kind==='next_design')return nextDesignTask(task,checkpoint);
    if(task.kind==='export')return exportTask(task,checkpoint);
    throw Error('Loại thao tác không hợp lệ');
    }catch(error){
      if(task.kind==='scene'&&!task.scene.error_card&&['insert_intent','inserted','trimmed','muted'].includes(task.phase?.stage)&&!/đã tạm dừng|Phiên thao tác|đã ngắt/i.test(error.message)){
        task.failure=error.message;
        try{await rollbackScene(task,checkpoint);}catch(recovery){throw Error(error.message+' • Không thay được cảnh lỗi: '+recovery.message);}
      }
      throw error;
    }
  }};
})();
