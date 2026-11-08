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
    return items.length===1&&['Thêm chuyển cảnh','Hủy liên kết thành phần đến clip'].includes(label(items[0]));
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
    return {start,end,hasStart,image:image?.src||background,element:e};
  });};
  function timelineScroller(root=document){
    let el=root.querySelector?.('[data-role="timeline-scene"]')||root.querySelectorAll?.('[data-role="timeline-scene"]')[0];
    for(let i=0;el&&i<30;i++,el=el.parentElement){
      if(el.scrollWidth>el.clientWidth+20&&/auto|scroll/.test(getComputedStyle(el).overflowX))return el;
    }
    return null;
  }
  async function readTimeline(){
    const scroller=timelineScroller();
    if(!scroller)return timeline();
    const origin=scroller.scrollLeft;
    const step=Math.max(1,Math.floor(scroller.clientWidth/2));
    const limit=Math.max(0,scroller.scrollWidth-scroller.clientWidth);
    const rows=new Map();
    try{
      for(let position=0;;position=Math.min(limit,position+step)){
        await guard();
        scroller.scrollLeft=position;
        await sleep(300);
        for(const row of timeline()){
          if(!Number.isFinite(row.end)||row.end<=0)continue;
          const previous=rows.get(row.end);
          if(previous?.hasStart&&row.hasStart&&previous.start!==row.start)throw Error('Timeline có mốc cảnh trùng nhau; chưa xác nhận được số cảnh.');
          if(!previous||(!previous.hasStart&&row.hasStart))rows.set(row.end,row);
          else if(!previous.image&&row.image)previous.image=row.image;
        }
        if(position===limit)break;
      }
    }finally{
      scroller.scrollLeft=origin;
      await sleep(300);
    }
    let previousEnd=0;
    return [...rows.values()].sort((a,b)=>a.end-b.end).map(row=>{
      const start=row.hasStart?row.start:previousEnd;
      if(!Number.isFinite(start)||Math.abs(start-previousEnd)>.12||row.end<=start)throw Error('Chưa đọc liền mạch các cảnh trên timeline Canva.');
      previousEnd=row.end;
      return {...row,start};
    });
  }
  async function countTimeline(expected){
    const visibleRows=timeline();
    return expected.includes(visibleRows.length)&&Math.abs(visibleRows[0]?.start||0)<=.12
      ?visibleRows.length:(await readTimeline()).length;
  }
  const tail=async()=>{
    const end=await wait(endButton,'Không tìm thấy timeline video mới của Canva');
    // The voice extends past the unfinished picture track. Scrolling to the
    // container's full width hides every scene; target the picture-track plus.
    end.scrollIntoView({block:'nearest',inline:'end'});
    await sleep(900);
    const rows=timeline();return rows.at(-1)||{start:0,end:0,image:''};
  };
  function stockDuration(text){
    const seconds=text.match(/(\d+(?:[.,]\d+)?)\s*(?:giây|seconds?|s\b)/i);
    if(seconds)return Number(seconds[1].replace(',','.'));
    const clock=text.match(/(?:^|[^\d:])(\d+:[0-5]\d(?::[0-5]\d)?)(?![\d:])/);
    return clock?clock[1].split(':').reduce((total,part)=>total*60+Number(part),0):0;
  }
  const cards=()=>[...document.querySelectorAll('[role="button"][draggable="true"][aria-label]')].filter(visible).map(el=>{
    const group=el.closest('[role="group"]')||el.parentElement;
    const src=group.querySelector('img')?.src||'';
    const id=src.match(/video-public\.canva\.com\/([^/]+)/)?.[1]||src.split('?')[0]||'title:'+norm(label(el));
    return {el,id,stock:/video-public\.canva\.com\//.test(src),title:label(el),duration:stockDuration(group.textContent)};
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
  function subjectWordsMatch(title,term){
    if(/[^\x00-\x7F]/.test(term)){
      const words=term.toLowerCase().normalize('NFC').match(/\p{L}+/gu)||[];
      return words.length>1&&words.every(word=>literalSubject(title,word));
    }
    const words=norm(term).match(/[a-z0-9]+/g)||[];
    return words.length>1&&words.every(word=>subjectMatch(title,word));
  }
  const VISUAL_FAMILIES=[
    {search:['đường huyết','blood glucose'],names:['blood glucose','blood sugar','glucose','diabetes','glucometer','insulin','đường huyết','tiểu đường','máy đo đường']},
    {search:['sợi elastin','elastin fibers','elastin collagen','sợi đàn hồi'],
     names:['elastin','collagen','elastic fibers','elastic fibres','elastic connective tissue','sợi đàn hồi','sợi collagen']},
    {search:['quả cam','orange fruit'],names:['orange juice','orange fruit','fresh oranges','orange slices','sliced orange','quả cam','trái cam','nước cam','ép cam','lát cam'],
     aliases:['orange','citrus','cam']},
    {search:['mạch máu','blood vessel anatomy','hồng cầu','blood cells'], names:[
      'blood vessel','blood vessels','vascular','artery','arteries','arterial','vein','veins',
      'capillary','capillaries','microvessel','microvasculature','microvascular','vi mạch','atherosclerosis','mạch máu','thành mạch','lòng mạch',
      'động mạch','tĩnh mạch','mao mạch','xơ vữa','hồng cầu','tế bào máu','máu lưu thông',
      'blood cells','blood flow','blood circulation','bloodstream',
    ],aliases:['blood','máu','mạch','circulation']},
    {search:['người già thể dục','senior exercise'],names:['exercise','exercising','fitness','workout','thể dục','tập luyện']},
    {search:['đột quỵ','não bộ','đau ngực','chest pain'],
     triggers:['đột quỵ','brain stroke','stroke brain','ischemic stroke','cerebral stroke','stroke symptoms'],
     names:['đột quỵ','brain stroke','stroke symptoms','ischemic stroke','cerebral stroke','não bộ','bộ não','brain','cerebral','đau ngực','ôm ngực','chest pain','clutching chest','clutching his chest','clutching her chest']},
    {search:['máy đo huyết áp','blood pressure monitor','đo huyết áp'],
     triggers:['pulse wave velocity monitor','pulse wave velocity device','pulse wave velocity equipment','máy đo vận tốc sóng mạch'],
     names:['máy đo huyết áp','đo huyết áp','blood pressure monitor','blood pressure measurement','blood pressure cuff','sphygmomanometer','pulse wave velocity monitor','máy đo vận tốc sóng mạch']},
    {search:['não bộ','human brain'],triggers:['brain','cerebral','não bộ','bộ não','vi mạch trong não','vi mạch não'],
     names:['brain','cerebral','não bộ','bộ não']},
    {search:['vùng đầu','đau đầu','xoa đầu','head massage'],
     triggers:['đau đầu','nhức đầu','xoa đầu','bóp đầu','vùng đầu','headache','head massage','scalp'],
     names:['đầu','vùng đầu','thái dương','da đầu','head','headache','temple massage','scalp'],
     exclude:['đầu gối','đầu tiên','knee']},
    {search:['tim','human heart anatomy'],names:['heart','cardiac','heartbeat','tim','trái tim']},
    {search:['dạ dày','human stomach'],names:['stomach','dạ dày']},
    {search:['lá gan','human liver'],names:['liver','lá gan']},
    {search:['quả thận','human kidney'],names:['kidney','renal','quả thận','cầu thận','glomerulus','glomeruli','glomerular','nephron']},
    {search:['đau lưng','vùng lưng','cột sống','lower back','back pain'],
     triggers:['lưng','cột sống','thoát vị đĩa đệm','back pain','back muscles','human back','lower back','spine','lumbar','herniated disc'],
     names:['lưng','cột sống','đĩa đệm','human back','lower back','upper back','back pain','back muscle','back anatomy','back stretching','holding his back','holding her back','spine','spinal','lumbar','herniated disc']},
    {search:['đường ruột','human intestine'],names:['intestine','intestinal','đường ruột','ruột non','ruột già']},
    {search:['đi bộ','walking'],names:['walking','walk','đi bộ']},
    {search:['kéo giãn chân','leg stretch'],names:['leg stretch','leg stretching','kéo giãn chân','kéo giãn cơ chân']},
  ];
  function visualFamilies(scene){
    // Manual edits remove the AI subjects. Their explicit queries then anchor
    // the fallback, rather than the previous AI labels or surrounding narration.
    const subjects=scene.manual_queries?scene.queries||[]:scene.subjects||[];
    const matches=VISUAL_FAMILIES.filter(family=>subjects.some(term=>(family.triggers||family.names).some(name=>subjectMatch(term,name))));
    return matches.length?matches:VISUAL_FAMILIES.filter(family=>subjects.some(term=>family.aliases?.some(name=>norm(term)===norm(name))));
  }
  const descriptiveWords=new Set((
    'a an the of and or in on at by with for from to is are as into through around '+
    'person people man woman senior elderly human someone animated animation simulation illustration graphic diagram anatomy '+
    'show showing closeup close up footage video image photo realistic motion moving professional specialized '+
    'holding touching using doing getting making cutting chopping massaging massage applying standing sitting walking '+
    'pain painful sore soreness tired fresh old new slow fast '+
    'của và hoặc trong trên dưới với cho từ đến tại ở đang bị có một các những người cụ ông bà '+
    'hình ảnh minh họa mô phỏng hoạt giải phẫu chân thực cận cảnh video chuyên dụng '+
    'xoa bóp mỏi đau nhức cầm chạm cắt dùng làm giữ đứng ngồi chạy tập'
  ).split(/\s+/));
  function genericTopic(scene){
    const phrases=scene.manual_queries?scene.queries:scene.subjects?.length?scene.subjects:scene.queries;
    const subjects=[];
    for(const phrase of (phrases||[]).slice(0,4)){
      const words=(phrase.toLowerCase().normalize('NFC').match(/\p{L}+/gu)||[]).filter(word=>!descriptiveWords.has(word));
      if(!words.length||words.length>5)continue;
      const subject=words.join(' ');
      if(words.length===1&&subject.length<3)continue;
      subjects.push(subject);
    }
    const unique=[...new Set(subjects)];
    return unique.length?{queries:unique,subjects:unique}:null;
  }
  function literalSubject(title,term){
    const clean=value=>value.toLowerCase().normalize('NFC').match(/\p{L}+/gu)?.join(' ')||'';
    const text=' '+clean(title)+' ',word=clean(term);
    return !!word&&[word,word+'s',word+'es'].some(value=>text.includes(' '+value+' '));
  }
  function illustrationScene(scene,topic,allowGeneric=false){
    if(!(scene.topic_only||scene.allow_all_media))return null;
    const families=visualFamilies(scene);
    const generic=allowGeneric&&!families.length&&!topic&&!scene.illustration_queries?.length?genericTopic(scene):null;
    if(scene.manual_queries&&!families.length&&!topic&&!generic)return null;
    let queries=scene.manual_queries?[]:scene.illustration_queries;
    if(!queries?.length){
      // Older plans did not include a separate stock illustration for citations.
      const subjects=scene.subjects||[];
      if(subjects.length&&subjects.every(term=>/^(?:research(?: study)?|scientific research|nghien cuu(?: khoa hoc)?)$/.test(norm(term)))){
        queries=['scientist in laboratory','bài báo khoa học'];
      }else if(subjects.length&&subjects.every(term=>/^(?:(?:the )?journal of |tap chi )/.test(norm(term)))){
        queries=['scientific journal','bài báo khoa học'];
      }
    }
    // Dedicated families use more specific captions. Use the shared topics
    // for other scenes without replacing their original search.
    const broad=families.length?null:topic||generic;
    if(!queries?.length&&!families.length&&!broad)return null;
    queries=[...new Set([...(queries||[]),...families.flatMap(family=>family.search),...(broad?.queries||[])])];
    const subjects=[...queries,...families.flatMap(family=>family.names),...(broad?.subjects||[])];
    if(subjects.includes('scientist in laboratory'))subjects.push('scientist','laboratory','researcher','microscope','nhà khoa học','phòng thí nghiệm');
    if(subjects.includes('scientific journal')||subjects.includes('bài báo khoa học'))subjects.push('scientific paper','research paper','tạp chí khoa học');
    return {...scene,queries,subjects,positive:subjects,topic_only:true,actions:[],preferred:'',
            literal_subjects:!!generic||families.some(family=>family.exclude),exclude:families.flatMap(family=>family.exclude||[])};
  }
  function matchesSceneSubject(title,scene){
    if(scene.exclude?.some(term=>literalSubject(title,term)))return false;
    if(scene.literal_subjects)return scene.subjects.some(term=>literalSubject(title,term));
    return !scene.subjects?.length||scene.subjects.some(term=>subjectMatch(title,term)||
      (scene.topic_only&&subjectWordsMatch(title,term)));
  }
  function eligibleCards(items,scene,used){
    return items.filter(c=>!used.includes(c.id)&&c.duration>=scene.duration-.05&&(scene.allow_all_media||realPerson(c))&&matchesSceneSubject(c.title,scene)&&(scene.topic_only||!scene.actions?.length||scene.actions.some(w=>norm(c.title).includes(norm(w))))&&score(c,scene)>=4).sort((a,b)=>score(b,scene)-score(a,scene));
  }
  function relatedCards(items,scene,used){
    return eligibleCards(items,scene,used).filter(c=>c.duration>=scene.duration+.1);
  }
  function reuseEligibleCards(items,scene,used){
    const times=id=>scene._usage?.[id]||(used.includes(id)?1:0);
    return eligibleCards(items,scene,[]).sort((a,b)=>{
      const penalty=c=>times(c.id)*100+(c.id===scene._lastAsset?10000:0);
      return penalty(a)-penalty(b)||score(b,scene)-score(a,scene);
    });
  }
  function stockCandidates(items,scene,used,allowReuse,illustration){
    const select=allowReuse?reuseEligibleCards:eligibleCards;
    const exact=select(items,scene,used);
    return exact.length||!illustration?exact:select(items,illustration,used);
  }
  function rememberReuse(scene,key,query,items,used,illustration){
    if(items.some(c=>used.includes(c.id)&&stockCandidates([c],scene,[],false,illustration).length)){
      scene[key]||=[];if(!scene[key].includes(query))scene[key].push(query);
    }
  }
  function score(card,scene){
    const text=norm(card.title);let n=0;
    for(const word of scene.positive||[])if(text.includes(norm(word)))n+=4;
    for(const [index,word] of (scene.subjects||[]).entries()){
      if(subjectMatch(text,word))n+=index<2?8:2;
      else if(scene.topic_only&&subjectWordsMatch(text,word))n+=5;
    }
    if(scene.topic_only&&scene.actions?.some(w=>text.includes(norm(w))))n+=3;
    for(const word of scene.negative||[])if(text.includes(norm(word)))n-=100;
    if(/elderly|senior|aged|older|middle aged/.test(text))n+=2;
    if(scene.preferred&&text===norm(scene.preferred))n+=100;
    return n;
  }
  const closeMenu=async()=>{
    if(!menus().length)return;
    const owner=[...document.querySelectorAll('button[aria-label="Tùy chọn về trang"][aria-expanded="true"],[role="button"][aria-label="Tùy chọn về trang"][aria-expanded="true"]')].find(visible);
    if(owner){await click(owner);}
    else{
      const menu=menus()[0],target=menu.querySelector('[role="menuitem"],button,[tabindex]')||menu;
      if(typeof target.focus==='function')target.focus();key(target,'Escape');
    }
    await wait(()=>!menus().length,'Không đóng được menu đang mở: '+menus().map(e=>label(e).slice(0,100)).join(' / '),3500);
  };
  const selectClip=async(row)=>{
    if(!row?.element)throw Error('Không tìm thấy clip cần chọn');
    // The thumbnail can have zero width for legacy 1ms clips. Its own page
    // button still has a direct selection handler; do not hit a neighbour.
    const button=row.element.querySelector('button[aria-label="Tùy chọn về trang"],[role="button"][aria-label="Tùy chọn về trang"]');
    await click(button||row.element);
    if(button?.getAttribute('aria-expanded')==='true')await click(button);
    await closeMenu();
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
  function emptyVideoResult(input,query,root=document){
    if(!input||norm(input.value).trim()!==norm(query).trim()||input.getAttribute('aria-busy')==='true')return false;
    const quoted=norm(query).trim();
    if(!quoted)return false;
    return [...root.querySelectorAll('[role="status"],[role="alert"],p,span,div')].some(el=>{
      const content=el.textContent||'';
      if(content.length>=350)return false;
      const message=norm(content).trim();
      return /^(?:rat tiec,? (?:chung toi )?khong tim thay video|sorry,? (?:we )?(?:could not|couldn't|did not|didn't) find (?:any )?videos?)/.test(message)&&
        [`"${quoted}"`,`“${quoted}”`,`'${quoted}'`].some(value=>message.includes(value))&&visible(el);
    });
  }
  function randomFallbackCard(items,scene,used,top,allowReuse=false){
    const valid=items.filter(card=>card.duration>=scene.duration-.05);
    const lower=valid.filter(card=>!top.has(card.id));
    let pool=lower.filter(card=>!used.includes(card.id));
    if(!pool.length&&allowReuse){
      pool=lower.filter(card=>card.id!==scene._lastAsset);
      if(!pool.length)pool=lower;
      if(!pool.length)pool=valid.filter(card=>!used.includes(card.id));
      if(!pool.length)pool=valid;
    }
    return pool[Math.floor(Math.random()*pool.length)];
  }
  const choose=async(scene,used,allowReuse=false,illustration=null,randomFallback=false)=>{
    if(scene.requires_review&&!scene.allow_all_media)return null;
    for(const query of (allowReuse?scene._reuseVideoQueries||[]:scene.queries)){
      for(let attempt=0;attempt<2;attempt++){
        const input=await wait(()=>document.querySelector('input[aria-label="Tìm kiếm video"]'),'Không thấy ô tìm kiếm video khi đổi từ khóa');
        const previous=cards().filter(c=>c.stock).map(c=>c.id).join('|');
        fill(input,query);await sleep(350);await guard();
        const liveInput=await wait(()=>document.querySelector('input[aria-label="Tìm kiếm video"]'),'Không thấy ô tìm kiếm video khi đổi từ khóa');
        key(liveInput,'Enter');const started=Date.now();let settled=false,empty=false;
        for(let poll=0;poll<60;poll++){
          await guard();await sleep(250);
          const current=document.querySelector('input[aria-label="Tìm kiếm video"]');
          if(emptyVideoResult(current,query)){empty=true;break;}
          if(searchReady(current,query,cards().filter(c=>c.stock),previous,Date.now()-started)){settled=true;break;}
        }
        if(empty)break;
        if(!settled)continue; // Only repeat read-only searches, never insertion.
        await sleep(700);
        const top=new Set(cards().filter(c=>c.stock).slice(0,2).map(card=>card.id));
        for(let page=0;page<4;page++){
          await guard();const items=cards().filter(c=>c.stock);
          if(randomFallback){
            const card=randomFallbackCard(items,scene,used,top,page===3);
            if(card)return card;
            items.at(-1)?.el.scrollIntoView({block:'end',inline:'nearest'});
            await sleep(1500);
            continue;
          }
          if(!allowReuse)rememberReuse(scene,'_reuseVideoQueries',query,items,used,illustration);
          const found=stockCandidates(items,scene,used,allowReuse,illustration);
          if(found.length)return found[0];
          const last=cards().at(-1);if(last)last.el.scrollIntoView({block:'end',inline:'nearest'});
          await sleep(1500);
        }
        if(randomFallback)break;
        const related=relatedCards(cards().filter(c=>c.stock),scene,used);
        if(related.length)return related[0];
        break;
      }
    }
    return null;
  };
  const choosePhoto=async(scene,used,allowReuse=false,illustration=null)=>{
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
        await guard();const items=photoCards();if(!allowReuse)rememberReuse(scene,'_reusePhotoQueries',query,items,used,illustration);
        const candidates=stockCandidates(items,scene,used,allowReuse,illustration);
        if(candidates.length)return candidates[0];
        const lastPhoto=photoCards().at(-1);if(lastPhoto)lastPhoto.el.scrollIntoView({block:'end'});
        await sleep(1500);
      }
    }
    return null;
  };
  const photoDuration=duration=>Math.max(.1,Math.round((duration+Number.EPSILON)*10)/10);
  const timePhoto=async(duration,allowExisting=false)=>{
    const before=timeline().at(-1);
    if(!before||!Number.isFinite(duration)||duration<=0)throw Error('Không xác định được cảnh ảnh/thời lượng cần đặt.');
    const expected=before.start+duration;
    const applied=()=>{
      const last=timeline().at(-1);
      return last&&Math.abs(last.start-before.start)<=.02&&Math.abs(last.end-expected)<=.12;
    };
    // Use the same endpoint tolerance as the caller and the next scene.
    // Resizing can change which rows Canva mounts, so match the final start.
    if(applied()&&!visible(durationInput()))return;
    const owner=()=>find(/giây, sửa thời gian$/);
    for(const confirmWithEnter of [false,true]){
      await guard();
      const last=timeline().at(-1);
      if(!last||Math.abs(last.start-before.start)>.02)throw Error('Cảnh cuối đã thay đổi trong lúc đặt thời lượng ảnh.');
      if(!visible(durationInput()))await click(await wait(owner,'Không thấy thời lượng ảnh'));
      const field=await wait(()=>{const e=durationInput();return visible(e)?e:null;},'Không thấy ô đặt thời gian ảnh');
      // Canva truncates extra decimal digits. Round before sending the value.
      field.focus();fill(field,String(photoDuration(duration)));await sleep(350);
      await guard();
      // Try committing by blur first. Some editors need Enter after the input
      // state has settled. Never use the global apply-to-all button.
      if(confirmWithEnter&&visible(field))key(field,'Enter');
      if(visible(durationInput())){
        const button=await wait(owner,'Không thấy nút đóng thời lượng ảnh');button.focus();
        await sleep(350);
        if(visible(durationInput()))await click(await wait(owner,'Không đóng được thời lượng ảnh'));
      }
      for(let poll=0;poll<6;poll++){
        await guard();
        if(applied())return;
        await sleep(250);
      }
    }
    if(allowExisting&&!visible(durationInput()))return;
    await wait(applied,'Mốc bắt đầu/kết thúc ảnh chưa khớp sau khi lưu thời lượng',8000);
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
  const warningBounds=(row,overlay)=>overlay&&Number.isFinite(overlay.start)&&Number.isFinite(overlay.end)&&
    overlay.start>=row.start-.001&&overlay.end<=row.end+.001&&overlay.end>overlay.start;
  function warningNodes(message){
    const marker=message.split(' • ')[0]+' •';
    return [...document.querySelectorAll('[role="button"],button,[aria-label],[title]')].filter(element=>{
      if(element.closest('[data-role="timeline-scene"]'))return false;
      const caption=element.getAttribute('aria-label')||element.getAttribute('title')||element.textContent?.trim()||'';
      return caption===message||caption.startsWith(marker);
    });
  }
  function warningTrack(message){
    const tracks=new Map();
    for(const element of warningNodes(message)){
      for(let node=element,i=0;node&&i<4;node=node.parentElement,i++){
        const handles=[...node.querySelectorAll('[role="slider"]')];
        const start=handles.find(h=>label(h).includes('biên bắt đầu'));
        const end=handles.find(h=>label(h).includes('biên kết thúc'));
        if(handles.length!==2||!start||!end||node.querySelector('[data-role="timeline-scene"]'))continue;
        const value=handle=>Number(handle.getAttribute('aria-valuenow')??NaN)/1e6;
        tracks.set(start,{element,start:value(start),end:value(end),startHandle:start,endHandle:end});
        break;
      }
    }
    return tracks.size===1?tracks.values().next().value:null;
  }
  function timelineRuler(row){
    const clip=row.element.getBoundingClientRect();
    const x=clip.left+clip.width/2;
    for(let y=clip.top-8;y>=clip.top-90;y-=4){
      const hit=document.elementFromPoint(x,y);
      for(let node=hit,i=0;node&&i<5;node=node.parentElement,i++){
        const name=norm((node.getAttribute('data-role')||'')+' '+(node.getAttribute('aria-label')||''));
        if(/ruler|time.?scale|thuoc (?:do|thoi gian)/.test(name))return {node:hit,x,y};
      }
    }
    return null;
  }
  async function seekWarningScene(row){
    const ruler=timelineRuler(row);
    if(!ruler)throw Error('Chưa tìm thấy thước timeline để đặt chữ đúng cảnh.');
    await guard();
    ruler.node.dispatchEvent(new MouseEvent('click',{bubbles:true,clientX:ruler.x,clientY:ruler.y}));
    await sleep(350);
  }
  async function dragWarningEdge(handle,delta){
    await guard();
    const rect=handle.getBoundingClientRect(),x=rect.left+rect.width/2,y=rect.top+rect.height/2;
    if(!rect.width||!Number.isFinite(delta))throw Error('Không đọc được tay nắm thời lượng chữ.');
    const send=(target,type,clientX,buttons)=>target.dispatchEvent(new PointerEvent(type,{
      bubbles:true,cancelable:true,pointerId:1,pointerType:'mouse',isPrimary:true,clientX,clientY:y,button:0,buttons,
    }));
    send(handle,'pointerdown',x,1);
    send(handle,'pointermove',x+delta,1);
    send(handle,'pointerup',x+delta,0);
    await sleep(350);
  }
  async function fitWarningTrack(row,message){
    let track=await wait(()=>warningTrack(message),'Chưa đọc được mốc bắt đầu/kết thúc của chữ',4500);
    if(warningBounds(row,track))return;
    const live=timeline().find(clip=>Math.abs(clip.start-row.start)<.01&&Math.abs(clip.end-row.end)<.01);
    const pixels=(live?.element.getBoundingClientRect().width||0)/(row.end-row.start);
    if(!Number.isFinite(pixels)||pixels<=0||row.end-row.start<.16)throw Error('Clip quá ngắn để căn chữ an toàn.');
    const start=row.start+.04,end=row.end-.04;
    // Open room on the right first when moving a text clip forward.
    const edges=track.end<=start?['end','start','end']:['start','end'];
    for(const edge of edges){
      track=warningTrack(message);
      if(!track)throw Error('Canva chưa hiển thị riêng dòng chữ cần căn.');
      const target=edge==='start'?start:end;
      if(Math.abs(track[edge]-target)>.02)await dragWarningEdge(track[edge+'Handle'],(target-track[edge])*pixels);
    }
    if(!warningBounds(row,warningTrack(message)))throw Error('Chữ vượt khỏi thời lượng clip thay thế.');
  }
  async function settleWarning(row,message){
    try{await fitWarningTrack(row,message);}
    catch(error){
      if(/đã tạm dừng|Phiên thao tác|đã ngắt|mã kết nối/i.test(error.message))throw error;
      const track=warningTrack(message);
      if(track&&!warningBounds(row,track)){
        await click(track.element);
        if(document.activeElement===track.element&&track.element.getAttribute('aria-selected')==='true'){
          await guard();
          track.element.dispatchEvent(new KeyboardEvent('keydown',{key:'Delete',code:'Delete',keyCode:46,bubbles:true}));
          await sleep(350);
          if(!warningNodes(message).length)throw Error('Đã gỡ dòng chữ vượt khỏi clip. Video thay thế được giữ lại.');
        }
      }
      error.overlayUnverified=true;
      throw error;
    }
  }
  async function addFallbackWarning(row,message){
    if(warningNodes(message).length){
      await settleWarning(row,message);
      return;
    }
    await selectClip(row);
    await seekWarningScene(row);
    await click(await wait(()=>find('Văn bản','[role="tab"]'),'Không thấy mục Văn bản',4500));
    const heading=await wait(()=>find(/^(Thêm tiêu đề|Thêm văn bản|Thêm hộp văn bản)$/i),'Không thấy nút thêm văn bản',4500);
    await click(heading);
    try{
    const editor=await wait(()=>{
      const element=document.activeElement;
      return element?.isContentEditable&&!element.closest('[role="tablist"],[role="menu"],[role="dialog"]')?element:null;
    },'Canva chưa mở ô nhập chữ trên khung vẽ',4500);
    await guard();
    const range=document.createRange(),selection=window.getSelection();
    range.selectNodeContents(editor);
    if(selection){selection.removeAllRanges();selection.addRange(range);}
    const transfer=new DataTransfer();transfer.setData('text/plain',message);
    editor.dispatchEvent(new ClipboardEvent('paste',{clipboardData:transfer,bubbles:true,cancelable:true}));
    await sleep(350);await guard();
    if(document.activeElement===editor&&!editor.textContent.includes(message)&&document.execCommand)
      document.execCommand('insertText',false,message);
    await wait(()=>editor.textContent.includes(message),'Canva chưa xác nhận chữ báo tư liệu thay thế',4500);
    key(editor,'Escape');
    }catch(error){
      error.overlayUnverified=true;
      throw error;
    }
    await settleWarning(row,message);
  }
  async function sceneTask(task,checkpoint){
    const s=task.scene;s._usage=task.usage||{};s._lastAsset=task.last_asset||'';let asset=task.phase?.asset,title=task.phase?.title||'';
    let warning=task.phase?.fallback_warning||'';
    let warningAlreadyAttempted=task.phase?.stage==='overlay_intent';
    const contextOnly=s.context_only||(!s.manual_queries&&norm(s.text).trim()==='khoang nghi');
    if(warningAlreadyAttempted){
      const last=await tail();
      if(Math.abs(last.end-s.start)<=.12&&await countTimeline([s.id-1])===s.id-1){
        if(warningNodes(warning).length)return {overlay_unverified:'Video thay thế đã bị gỡ nhưng dòng chữ cũ còn trên timeline.'};
        await checkpoint('ready_after_repair');warningAlreadyAttempted=false;warning='';asset='';title='';
      }
    }
    if(s.timing_original_duration<.1&&task.previous_scene&&['inserted','trimmed','muted'].includes(task.phase?.stage)){
      const last=await tail(),prev=task.previous_scene;
      if(last.end-last.start<.1&&Math.abs(last.start-prev.start)<=.12&&await countTimeline([s.id-1])===s.id-1){
        await selectClip(last);await trim(s.start-last.start);
        const restored=await tail();if(Math.abs(restored.end-s.start)>.12)throw Error('Chưa phục hồi đủ thời lượng cảnh trước.');
      }
      const ready=await tail();
      if(Math.abs(ready.end-s.start)<=.12&&await countTimeline([s.id-1])===s.id-1)await checkpoint('ready_after_repair');
    }
    if(task.phase?.stage==='insert_intent')throw Error('Lần trước dừng ngay lúc chèn cảnh. Kiểm tra Canva và dùng Xử lý cảnh bị dở trong ứng dụng.');
    if(!['inserted','trimmed','muted','overlay_intent'].includes(task.phase?.stage)){
      await prepare(s);
      const illustration=illustrationScene(s,task.related_topic,true),used=task.used||[];
      const search={...s,queries:[...new Set([...s.queries,...(illustration?.queries||[])])],_reuseVideoQueries:[],_reusePhotoQueries:[]};
      if(contextOnly){
        search.queries=[...new Set([...search.queries.filter(q=>norm(q).trim()!=='khoang nghi'),'cảnh đường phố','street scenery'])];
        search.requires_review=false;
      }
      if(s.manual_queries&&illustration){
        // Rank on the current input. Bare "stroke" can also mean swimming.
        search.subjects=s.queries.filter(query=>norm(query).trim()!=='stroke');
        if(!search.subjects.length)search.subjects=illustration.subjects;
        search.positive=search.subjects;
        search.literal_subjects=illustration.literal_subjects;
        search.exclude=illustration.exclude;
      }
      let selected=await choose(search,used,false,illustration);
      if(!selected&&search._reuseVideoQueries.length)selected=await choose(search,used,true,illustration);
      if(!selected&&search.queries[0]){
        const fallback=contextOnly?[...new Set([...search.queries,'cảnh đường phố','street scenery','phong cảnh thiên nhiên'])]:
          norm(s.queries[0]).trim()==='kho'?[s.queries[0],'nhà kho','storage warehouse']:[s.queries[0]];
        selected=await choose({...search,queries:fallback},used,false,null,true);
        if(selected&&!contextOnly)warning=`LỖI CẢNH ${s.id} • Video thay thế: ${s.queries[0]}`.slice(0,160);
      }
      if(!selected)selected=await choosePhoto(search,used,false,illustration);
      if(!selected&&search._reusePhotoQueries.length)selected=await choosePhoto(search,used,true,illustration);
      if(!selected){
        return {missing_stock:'Canva không có video thay thế đủ dài hoặc ảnh phù hợp cho: '+(s.queries[0]||s.text)};
      }
      asset=selected.id;title=selected.title+((task.used||[]).includes(asset)?' (dùng lại do thiếu tư liệu phù hợp khác)':'');task.media_kind=selected.media_kind||'video';
      await checkpoint('insert_intent',{asset,title,media_kind:task.media_kind,fallback_warning:warning});await click(selected.el);
      await wait(()=>task.media_kind==='image'?find(/giây, sửa thời gian$/):find(/^Xén video dài/),'Nội dung chưa được đưa vào timeline');
      await tail();
      const count=await countTimeline([s.id]);
      if(count!==s.id)throw Error(`Canva có ${count} cảnh, đang chèn cảnh ${s.id}. Chưa xác nhận chèn thành công; kiểm tra cảnh dở để tránh chèn trùng.`);
      await checkpoint('inserted',{asset,title,media_kind:task.media_kind,fallback_warning:warning});
    } else if(!warningAlreadyAttempted){
      const last=await tail();
      if(last.element)await selectClip(last);
      task.media_kind=task.phase.media_kind||'video';
      await wait(()=>task.media_kind==='image'?find(/giây, sửa thời gian$/):find(/^Xén video dài/),'Hãy chọn cảnh cuối timeline để tiếp tục');
    }
    const mediaPhase={asset,title,media_kind:task.media_kind,fallback_warning:warning};
    await tail();
    const count=await countTimeline([s.id]);
    const selectedTail=timeline().at(-1);
    if(count!==s.id||!selectedTail||Math.abs(selectedTail.start-s.start)>.12)throw Error('Cảnh cuối chưa đúng vị trí, chưa cắt để tránh sửa nhầm cảnh trước.');
    if(!warningAlreadyAttempted){
      await selectClip(selectedTail);await ensureBackground();
      if(task.media_kind==='image'){
        const current=await tail();
        if(Math.abs(current.start-s.start)>.12)throw Error('Điểm bắt đầu ảnh chưa khớp voice; không thay đổi cảnh khác.');
        await timePhoto(s.start+s.duration-current.start);
      }else await trim(s.start+s.duration-selectedTail.start);
      await checkpoint('trimmed',mediaPhase);
      if(task.media_kind!=='image')await mute();await checkpoint('muted',mediaPhase);
    }
    const last=await tail();
    if(Math.abs(last.start-s.start)>.12||Math.abs(last.end-(s.start+s.duration))>.12)throw Error('Độ dài/vị trí cảnh chưa khớp lời đọc. Kiểm tra cảnh cuối timeline, không thêm lại video.');
    if(!warning)return {asset,title};
    let overlayError='';
    if(!warningAlreadyAttempted){
      await checkpoint('overlay_intent',mediaPhase);
    }
    try{
      if(!warningAlreadyAttempted)await addFallbackWarning(last,warning);
      else if(warningNodes(warning).length)await settleWarning(last,warning);
      else overlayError='Cần kiểm tra chữ của clip thay thế sau lần gián đoạn.';
    }catch(error){
      if(/đã tạm dừng|Phiên thao tác|đã ngắt|mã kết nối/i.test(error.message))throw error;
      if(error.overlayUnverified)return {overlay_unverified:error.message};
      overlayError=error.message;
    }
    const verified=await tail();
    if(Math.abs(verified.start-s.start)>.12||Math.abs(verified.end-s.start-s.duration)>.12||await countTimeline([s.id])!==s.id)
      throw Error('Timeline đã thay đổi khi thêm chữ lên video thay thế.');
    return {asset,title,fallback_warning:warning,overlay_error:overlayError};
  }
  async function rollbackScene(task,checkpoint){
    const s=task.scene;await closeMenu();
    const before=await tail();
    const count=await countTimeline([s.id-1,s.id]);
    if(count===s.id-1&&Math.abs(before.end-s.start)<=.12){await checkpoint('rollback_done');return;}
    const last=await tail();
    if(count!==s.id||Math.abs(last.start-s.start)>.12||!last.element)throw Error('Không xác định được riêng cảnh cuối để thay thẻ lỗi.');
    await selectClip(last);
    const pageMenu=()=>last.element.querySelector('button[aria-label="Tùy chọn về trang"],[role="button"][aria-label="Tùy chọn về trang"]');
    await click(await wait(pageMenu,'Không thấy menu của cảnh cuối cần thay'));
    const remove=await wait(()=>find(/^Xóa(?:\s|$)/,'[role="menuitem"]'),'Không thấy Xóa trong menu cảnh cuối');
    await checkpoint('rollback_intent',{reason:task.failure});await click(remove);
    const after=await tail();
    if(!(s.id===1&&sceneCount()===1&&!after.image)&&
       (Math.abs(after.end-s.start)>.12||await countTimeline([s.id-1])!==s.id-1))throw Error('Sau khi gỡ cảnh lỗi, timeline chưa khớp mốc voice.');
    await checkpoint('rollback_done');
  }
  async function errorCardTask(task,checkpoint,assetData){
    const s=task.scene;
    const isError=!!s.error_card;
    const cardPhase={media_kind:'image',card_kind:isError?'error':'text'};
    // Reconcile the failed insert once; never repeat the original media search.
    // A confirmed final scene is removed before the single error image is added.
    if(isError&&!['inserted','trimmed','muted'].includes(task.phase?.stage)){
      const last=await tail(),count=await countTimeline([s.id-1,s.id]);
      const placement=errorPlacement(count,last,s);
      if(placement==='replace'){
        await rollbackScene(task,checkpoint);
      }else if(placement!=='append')throw Error('Timeline chưa khớp mốc cần đặt ảnh lỗi; không sửa cảnh khác.');
      await checkpoint('error_ready');
    }
    if(['inserted','trimmed','muted'].includes(task.phase?.stage)){
      const last=await tail();if(!last.element)throw Error('Không thấy thẻ lỗi vừa chèn để đặt thời lượng');
      if(await countTimeline([s.id])!==s.id||Math.abs(last.start-s.start)>.12)throw Error('Thẻ lỗi chưa đúng cảnh cần xử lý.');
    }else{
      if(task.phase?.stage==='insert_intent')throw Error('Thẻ lỗi đang chèn dở; chưa tự chèn lại.');
      let raw=await assetData();
      if(raw.error_text||raw.card_text)raw={...raw,mime:'image/png',data:errorImage(raw.error_text||raw.card_text)};
      if(raw.mime!=='image/png')throw Error('Thẻ chữ cần ảnh PNG.');
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
      await checkpoint('insert_intent',{asset:raw.name,...cardPhase});await click(imageCard);
      await tail();
      if(await countTimeline([s.id])!==s.id)throw Error('Chưa xác nhận được ảnh báo lỗi trên timeline');
      await checkpoint('inserted',{asset:raw.name,...cardPhase});
    }
    const before=await tail();
    if(!before.element||Math.abs(before.start-s.start)>.12)throw Error('Thẻ chữ không nằm đúng mốc voice');
    await selectClip(before);await ensureBackground();
    await timePhoto(s.start+s.duration-before.start,true);
    const last=await tail();
    let cardFrames;
    if(Math.abs(last.end-s.start-s.duration)>.12){
      const rows=await readTimeline(),card=rows.at(-1);
      if(rows.length!==s.id||!card?.image||Math.abs(card.start-s.start)>.12||
         !Number.isFinite(card.end)||card.end<=card.start)throw Error('Chưa xác nhận được vị trí thẻ chữ đã chèn.');
      cardFrames=rows.map(({start,end})=>({start,end}));
    }
    await checkpoint('trimmed',cardPhase);
    return {asset:task.fallback_id||(isError?'error:'+s.id:undefined),title:isError?'LỖI CẢNH '+task.id:s.title_text||s.text,
            card_frames:cardFrames};
  }
  function errorPlacement(count,last,scene){
    if(scene.id===1&&count===1&&!last.image)return 'append';
    if(count===scene.id&&Math.abs(last.start-scene.start)<=.12)return 'replace';
    if(count===scene.id-1&&Math.abs(last.end-scene.start)<=.12)return 'append';
    return 'unknown';
  }
  function errorImage(text){
    const canvas=document.createElement('canvas');canvas.width=1920;canvas.height=1080;
    const ctx=canvas.getContext('2d');ctx.fillStyle='#101010';ctx.fillRect(0,0,1920,1080);
    let lines=[],size=48;
    for(;size>=10;size-=2){
      ctx.font=`bold ${size}px Arial`;lines=[];
      for(const paragraph of String(text).split('\n')){
        let line='';for(const word of paragraph.split(/\s+/)){
          // Split even an unbroken diagnostic token to keep it inside the frame.
          for(const char of (line?' ':'')+word){if(ctx.measureText(line+char).width>1700){lines.push(line);line='';}line+=char;}
        }lines.push(line);
      }
      if(lines.length*(size+14)<=880)break;
    }
    ctx.fillStyle='#ffffff';ctx.textAlign='center';ctx.textBaseline='top';
    const top=Math.max(70,(1080-lines.length*(size+14))/2);
    lines.forEach((line,i)=>ctx.fillText(line,960,top+i*(size+14)));
    return canvas.toDataURL('image/png').split(',')[1];
  }
  async function titleTask(task,checkpoint,assetData){
    const s=task.scene;const phase=task.phase?.stage;
    if(phase==='insert_intent')throw Error('Tiêu đề có thể đã được chèn. Dùng Xử lý cảnh bị dở trước khi tiếp tục để tránh trùng.');
    if(task.phase?.card_kind==='text')return await errorCardTask(task,checkpoint,assetData);
    if(!['inserted','trimmed','muted'].includes(phase)){
      const raw=await assetData();task.fallback_id=raw.asset_id;
      if(raw.card_text||raw.mime==='image/png')return await errorCardTask(task,checkpoint,async()=>raw);
      const titleName=raw.name.replace(/\.mp4$/i,'');
      const uploaded=()=>{
        const e=find(new RegExp(titleName));if(!e)return null;
        const group=e.closest('[role="group"]')||e.parentElement;
        return !group?.querySelector('[role="progressbar"]')?e:null;
      };
      await ensureUploadPanel();
      const existingTab=uploadedVideoTab();if(existingTab)await click(existingTab);
      if(!uploaded()){
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
      await tail();if(await countTimeline([s.id])!==s.id)throw Error('Số cảnh sau khi chèn tiêu đề chưa khớp. Kiểm tra cảnh dở, không chèn lại.');
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
    return {voice_name:raw.name};
  }
  function verifyVoice(name,duration){
    if(!name)throw Error('Thiếu tên voice cần đối chiếu; chưa xác nhận phần dựng.');
    const audio=[...document.querySelectorAll('button,[role="button"]')].find(e=>label(e).includes(name)&&label(e).includes('đoạn âm thanh'));
    if(!audio)throw Error('Không xác nhận được voice trên timeline; không chuyển sang phần mới.');
    const starts=[...audio.querySelectorAll('[role="slider"]')].filter(e=>label(e).includes('biên bắt đầu')).map(e=>Number(e.getAttribute('aria-valuenow'))/1e6);
    if(!starts.length||starts.some(v=>!Number.isFinite(v)||Math.abs(v)>.12))throw Error('Voice chưa bắt đầu từ giây 0; cần đưa đúng voice về đầu timeline.');
    const ends=[...audio.querySelectorAll('[role="slider"]')].filter(e=>label(e).includes('biên kết thúc')).map(e=>Number(e.getAttribute('aria-valuenow'))/1e6);
    if(!ends.length||!ends.every(Number.isFinite)||Math.abs(Math.max(...ends)-duration)>.12)throw Error('Voice trên Canva chưa đủ thời lượng phần này. Không xuất hoặc chuyển phần.');
    return {verified_voice_start:Math.min(...starts),verified_voice_end:Math.max(...ends),voice_name:name};
  }
  async function fitFinalScene(rows,voiceEnd){
    const expected=rows.at(-1);
    if(Math.abs(expected.end-voiceEnd)<=.12)return rows;
    const last=await tail();
    if(!last.element||!last.image||Math.abs(last.start-expected.start)>.02||Math.abs(last.end-expected.end)>.02||voiceEnd-last.start<.1)
      throw Error('Chưa xác nhận được cảnh cuối để tự căn điểm hết voice.');
    await selectClip(last);
    const kind=await wait(()=>find(/^Xén video dài/)?'video':find(/giây, sửa thời gian$/)?'image':null,'Không thấy công cụ căn thời lượng cảnh cuối');
    if(kind==='video')await trim(voiceEnd-last.start);
    else await timePhoto(voiceEnd-last.start,true);
    const checked=await readTimeline(),tailRow=checked.at(-1);
    if(checked.length!==rows.length||!tailRow?.image||Math.abs(tailRow.start-expected.start)>.02||Math.abs(tailRow.end-voiceEnd)>.12)
      throw Error(`Canva chưa căn được cảnh cuối về ${voiceEnd.toFixed(2)} giây. Hãy chỉnh cảnh cuối gần mốc này rồi xác nhận lại.`);
    return checked;
  }
  async function manualReviewTask(task){
    await closeMenu();await tail();
    let rows=await readTimeline();
    const count=rows.length,scene=task.scene;
    if(!task.allowed_counts.includes(count))throw Error(`Canva có ${count} cảnh, cần ${task.allowed_counts.join(' hoặc ')} cảnh. Hãy thay cảnh tại chỗ, không thêm thừa hay xóa cảnh khác.`);
    if(!rows[scene.id-1]?.image)throw Error(`Cảnh ${scene.id} chưa có ảnh/video trên timeline.`);
    if(task.overlay_scene&&!rows[task.overlay_scene-1]?.image)throw Error(`Chưa thấy video đã chèn ở cảnh ${task.overlay_scene}.`);
    const voice=verifyVoice(task.voice_name,task.voice_duration);
    if(task.fit_final&&scene.id===count)rows=await fitFinalScene(rows,voice.verified_voice_end);
    const row=rows[scene.id-1];
    if(!Number.isFinite(row.start)||!Number.isFinite(row.end))throw Error('Chưa đọc được mốc thời gian cảnh tự sửa.');
    const frames=rows.map(r=>({start:r.start,end:r.end}));
    return {manual_verified:true,review_token:task.review_token,verified_count:count,verified_start:row.start,verified_end:row.end,frames,asset:row.image,verified_overlay_scene:task.overlay_scene,...voice};
  }
  async function auditTask(task){
    await closeMenu();await tail();
    let rows=await readTimeline();
    if(rows.length!==task.count)throw Error(`Canva có ${rows.length} cảnh, cần ${task.count} cảnh. Không chuyển phần khi số cảnh chưa khớp.`);
    if(task.require_last_media&&!rows.at(-1)?.image)throw Error('Cảnh cuối của phần này chưa có hình. Bổ sung ảnh hoặc video vào đúng cảnh rồi bấm Tiếp tục.');
    const voice=verifyVoice(task.voice_name,task.duration);
    rows=await fitFinalScene(rows,voice.verified_voice_end);
    const last=rows.at(-1);
    return {verified_duration:last.end,verified_count:rows.length};
  }
  function designTitleInput(root=document){
    return [...root.querySelectorAll('input,textarea,[contenteditable="true"][role="textbox"]')].find(e=>visible(e)&&/tên(?: cho)? thiết kế|tiêu đề thiết kế|design title|design name|thiết kế không tên|untitled design/i.test((e.getAttribute('aria-label')||'')+' '+(e.getAttribute('placeholder')||'')));
  }
  async function renameTask(task){
    const name=task.design_name;
    if(typeof name!=='string'||!name.trim()||name.length>200)throw Error('Tên thiết kế không hợp lệ.');
    const value=e=>e?.getAttribute('contenteditable')==='true'?e.textContent:e?.value;
    const confirmed=()=>{
      const field=designTitleInput();
      const owner=field?.closest?.('[role="menuitem"],[role="button"],button');
      const mirror=(owner?.textContent||'').replace(/\s+/g,' ').trim();
      return field&&value(field)===name&&(mirror===name||String(document.title)===name||String(document.title).startsWith(name+' - '));
    };
    let failure;
    for(let attempt=0;attempt<2;attempt++){
      try{
        await guard();await closeMenu();if(confirmed())return {design_name:name};
        let input=designTitleInput();
        const owner=input?.closest?.('[role="menuitem"],[role="button"],button');
        if(owner&&document.activeElement!==input)await click(owner);
        if(!input){
          const current=document.title.replace(/\s*[-–|]\s*Canva\s*$/i,'').trim();
          await click(find(/^(Đổi tên thiết kế|Sửa tên thiết kế|Rename design|Edit design title)$/i)||
            [...document.querySelectorAll('button,[role="button"],[role="menuitem"]')].find(e=>visible(e)&&label(e)===current));
        }
        input=await wait(()=>designTitleInput(),'Không thấy ô tên thiết kế Canva',5000);
        input.focus();
        if(input.getAttribute('contenteditable')==='true'){
          input.textContent=name;input.dispatchEvent(new Event('input',{bubbles:true}));
        }else fill(input,name);
        await sleep(350);
        const outside=find('Điểm bắt đầu khung vẽ')||find('Tệp','[role="menuitem"]');
        if(outside?.focus)outside.focus();else input.blur();
        await wait(confirmed,'Canva chưa xác nhận tên mới: '+name,5000);
        return {design_name:name};
      }catch(error){
        if(/đã tạm dừng|phiên thao tác|đã ngắt/i.test(error.message))throw error;
        failure=error.message;
      }
    }
    return {design_name:name,rename_warning:failure||'Canva chưa nhận tên thiết kế; tiếp tục dựng và thử tên lại sau.'};
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
    const request=async(action)=>{
      const r=await chrome.runtime.sendMessage({type:'export_download',action});
      if(!r||r.error)throw Error(r?.error||'Chưa xác nhận được trạng thái tải MP4');return r;
    };
    const confirm=()=>{
      const buttons=[...document.querySelectorAll('button,[role="button"]')];
      return buttons.find(button=>{
        if(!visible(button)||label(button)!=='Tải xuống'||button.disabled||button.getAttribute('aria-disabled')==='true')return false;
        for(let panel=button.parentElement,i=0;panel&&i<7&&panel!==document.body;i++,panel=panel.parentElement){
          if(panel.textContent.includes('Video MP4')&&/Loại tệp|Chất lượng/.test(panel.textContent))return true;
        }
        return false;
      });
    };
    if(['export_intent','export_clicked'].includes(task.phase?.stage)){
      const prior=await request('status');
      if(prior.complete)return {download_complete:true,download_id:prior.id,download_path:prior.filename};
      if(prior.id===undefined&&task.phase.stage==='export_intent'&&confirm()){
        if(!prior.tracking)await request('arm');
        await click(confirm());
        await checkpoint('export_clicked');
      }else if(!prior.tracking)throw Error('Không có phiên tải đã lưu; chưa xuất lại để tránh tệp trùng.');
    }else{
      if(!confirm()){
        await closeMenu();await click(await wait(()=>find('Chia sẻ','button,[role="button"],[role="menuitem"]'),'Không thấy Chia sẻ'));
        await click(await wait(()=>find('Tải xuống'),'Không thấy Tải xuống'));
      }
      const button=await wait(confirm,'Chưa thấy nút xác nhận tải Video MP4 trong Canva');
      await request('arm');await checkpoint('export_intent');
      await click(button);await checkpoint('export_clicked');
    }
    for(let i=0;i<600;i++){
      await guard();const r=await request('status');
      if(r.complete)return {download_complete:true,download_id:r.id,download_path:r.filename};
      await sleep(1000);
    }
    throw Error('MP4 chưa tải xong sau 10 phút. Giữ tab để Tiếp tục kiểm tra; không tự xuất trùng.');
  }
  globalThis.SKSTAdapter={norm,label,score,realPerson,subjectMatch,illustrationScene,eligibleCards,reuseEligibleCards,relatedCards,stockCandidates,randomFallbackCard,stockDuration,searchReady,emptyVideoResult,timelineScroller,timeline,tail,photoDuration,timePhoto,rollbackScene,cards,photoCards,uploadInput,uploadedVideoTab,ensureUploadPanel,durationInput,audioOnTimeline,timelineTransitionMenu,closeMenu,errorImage,errorPlacement,auditTask,errorCardTask,titleTask,warningBounds,fitWarningTrack,run:async(task,check,voice,titleAsset,fallbackAsset)=>{
    guard=()=>check();await guard();
    const checkpoint=async(stage,extra={})=>{await check(stage,extra);task.phase={stage,...extra};};
    try{
    if(task.kind==='manual_review')return await manualReviewTask(task);
    if(task.kind==='rename')return await renameTask(task);
    if(task.kind==='scene'&&!task.scene.error_card&&['rollback_intent','rollback_done'].includes(task.phase?.stage)){
      const reason=task.phase.reason||'Tiếp tục thay cảnh lỗi bằng thẻ chữ';
      await rollbackScene(task,checkpoint);throw Error(reason);
    }
    if(task.kind==='scene'&&task.scene.error_card)return await errorCardTask(task,checkpoint,fallbackAsset);
    if(task.kind==='scene'&&task.phase?.card_kind==='text')return await errorCardTask(task,checkpoint,fallbackAsset);
    if(task.kind==='scene')return task.scene.kind==='title'?await titleTask(task,checkpoint,titleAsset):await sceneTask(task,checkpoint);
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
