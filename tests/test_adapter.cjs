const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const context={globalThis:{},document:{},getComputedStyle:e=>({overflowX:e.overflowX}),setTimeout,Promise,console};vm.createContext(context);
vm.runInContext(fs.readFileSync('extension/adapter.js','utf8'),context);
const adapter=context.globalThis.SKSTAdapter;
const stock=[{id:'top',duration:8},{id:'short',duration:2},{id:'used',duration:8},{id:'fresh',duration:8}];
assert.equal(adapter.randomFallbackCard(stock,{duration:4},['used'],new Set(['top'])).id,'fresh');
assert.equal(adapter.randomFallbackCard(stock,{duration:4,_lastAsset:'used'},['used','fresh'],new Set(['top']),true).id,'fresh');
assert.equal(adapter.randomFallbackCard(stock.slice(0,2),{duration:4},[],new Set(['top']),true).id,'top');
assert.equal(adapter.norm('Nhón GÓT chân'),'nhon got chan');
const transition={getAttribute:k=>k==='aria-label'?'Thêm chuyển cảnh':null};
const persistentMenu={getAttribute:k=>k==='role'?'menu':null,querySelectorAll:()=>[transition]};
assert(adapter.timelineTransitionMenu(persistentMenu),'Persistent transition control between two clips is not a dismissible popup');
assert(!adapter.timelineTransitionMenu({...persistentMenu,querySelectorAll:()=>[transition,{getAttribute:()=>null}]}),'A real multi-item popup is still dismissible');
assert(!adapter.timelineTransitionMenu({...persistentMenu,getAttribute:()=> 'dialog'}),'Dialogs are not ignored');
const accessibleCopy={textContent:'Âm thanhÂm thanh',querySelectorAll:()=>[{remove:()=>accessibleCopy.textContent='Âm thanh'}]};
assert.equal(adapter.label({getAttribute:()=>null,cloneNode:()=>accessibleCopy}),'Âm thanh','Ignore Canva aria-hidden duplicate tab captions');
const scene={positive:['heel','senior'],negative:['ballet'],preferred:'Senior heel raise'};
assert(adapter.score({title:'Senior heel raise'},scene)>adapter.score({title:'ballet heel raise'},scene));
assert(adapter.score({title:'ballet heel raise'},scene)<-50);
const select=(...inputs)=>adapter.uploadInput({querySelectorAll:()=>inputs});
const canvaInput={accept:'*/*',disabled:false};
assert.equal(select(canvaInput),canvaInput,'Observed Canva wildcard input accepts MP3');
const imageOnly={accept:'image/*',disabled:false},audio={accept:'.MP3, .WAV',disabled:false};
assert.equal(select(imageOnly,canvaInput,audio),audio,'Prefer audio-compatible input');
assert.equal(select(imageOnly),null,'Do not send voice to image-only picker');
assert.equal(select({accept:'*/*',disabled:true}),null,'Disabled upload is not ready');
assert.equal(select(),null,'Missing lazy-loaded input must wait');
const duration={getAttribute:key=>key==='placeholder'?'--':null};
assert.equal(adapter.durationInput({querySelectorAll:()=>[duration]}),duration,'Observed Canva duration uses placeholder, not aria-label');
assert(adapter.audioOnTimeline('test.mp3',{querySelectorAll:selector=>{
 assert(selector.includes('[role="button"]'));
 return [{getAttribute:k=>k==='aria-label'?'test.mp3, đoạn âm thanh':null}];
}}),'Audio timeline DIV role=button must be recognized');
console.log('Adapter ranking and Canva upload-input regression checks passed. Live full timeline still requires browser validation.');

(async()=>{
 const name='SKST_voice_25ef76ab16becb2b.wav';
 let onTimeline=false,inserted=0;
 const node=(attrs,extra={})=>({
   offsetWidth:10,getAttribute:key=>attrs[key]||null,querySelector:()=>null,closest:()=>null,
   scrollIntoView(){},click(){assert.fail('Unexpected click');},...extra
 });
 const uploads=node({'aria-label':'Tải lên','aria-selected':'true'});
 const tab=node({'aria-label':'Âm thanh','aria-selected':'true','aria-controls':'audio-library'});
 const plus=node({'aria-label':'Thêm nội dung đa phương tiện/cảnh trống'});
 const preview=node({'aria-label':'Phát '+name});
 const other=node({'aria-label':'Thêm SKST_voice_aabbccddeeff1122.wav'});
 const card=node({'aria-label':'Thêm âm thanh',title:name},{
   textContent:'SKST_voice_25ef76ab16be…',click(){onTimeline=true;inserted++;}
 });
 const slider=(label,time)=>node({'aria-label':label,'aria-valuenow':String(time*1e6)});
 const audio=node({'aria-label':name+' đoạn âm thanh'},{
   querySelectorAll:()=>[slider('biên bắt đầu',0),slider('biên kết thúc',232)]
 });
 const panel={querySelectorAll:()=>[preview,other,card]};
 const document={
   getElementById:id=>id==='audio-library'?panel:null,
   querySelectorAll:selector=>{
     if(selector==='input[type="file"]')assert.fail('Do not upload an existing WAV again');
     if(selector==='[data-role="timeline-scene"]')return [];
     return [uploads,tab,plus,...(onTimeline?[audio]:[])];
   }
 };
 const env={globalThis:{},document,getComputedStyle:()=>({visibility:'visible'}),setTimeout:f=>f()};
 vm.runInNewContext(fs.readFileSync('extension/adapter.js','utf8'),env);
 const stages=[];
 const run=stage=>env.globalThis.SKSTAdapter.run({kind:'voice',duration:232,phase:{stage}},
   async stage=>{if(stage)stages.push(stage);},async()=>({name}));
 assert.equal((await run('upload_intent')).voice_name,name);
 assert.deepEqual(stages,['voice_insert_intent']);
 assert.equal((await run('voice_insert_intent')).voice_name,name);
 assert.equal(inserted,1,'A resumed voice already on the timeline must never be inserted twice');
})().catch(e=>{console.error(e);process.exitCode=1;});

(async()=>{
 let clicked=0;
 const parent={textContent:'Loại tệp Video MP4 Chất lượng'};
 const button={offsetWidth:10,parentElement:parent,getAttribute:key=>key==='aria-label'?'Tải xuống':null,
   scrollIntoView(){},click(){clicked++;}};
 const document={body:{},querySelectorAll:()=>[button]};
 const chrome={runtime:{sendMessage:async()=>clicked?{tracking:true,complete:true,id:7,filename:'part.mp4'}:{tracking:true}}};
 const env={globalThis:{},document,chrome,getComputedStyle:()=>({visibility:'visible'}),setTimeout:f=>f()};
 vm.runInNewContext(fs.readFileSync('extension/adapter.js','utf8'),env);
 const checkpoints=[];
 const result=await env.globalThis.SKSTAdapter.run({kind:'export',phase:{stage:'export_intent'}},async stage=>{if(stage)checkpoints.push(stage);});
 assert.equal(clicked,1,'Resume an armed export whose MP4 confirmation is still open');
 assert.deepEqual(checkpoints,['export_clicked']);
 assert.equal(result.download_id,7);
})().catch(e=>{console.error(e);process.exitCode=1;});

const candidates=[{id:'used',duration:10,title:'senior exercise'},{id:'short',duration:2,title:'senior exercise'},{id:'fresh',duration:8,title:'senior exercise'},{id:'bad',duration:8,title:'ballet'}];
assert.equal(adapter.eligibleCards(candidates,{duration:4,positive:['exercise'],negative:['ballet']},['used']).map(c=>c.id).join(','),'fresh','Expanded search still rejects used, short, and unsuitable clips');

for(const title of ['3D man walking','Animated elderly man exercise','Neon frame background','Question marks loop','Rainbow cartoon children','Human anatomy skeleton'])assert(!adapter.realPerson({title}),title);
for(const title of ['Senior man exercising at home','Woman massaging her calf','Bác sĩ khám cho người cao tuổi'])assert(adapter.realPerson({title}),title);
assert.equal(adapter.eligibleCards([{id:'unrelated',title:'Senior man cooking',duration:9}],{duration:4,positive:['heel'],negative:[]},[]).length,0,'A real person alone is insufficient without relevance');

const scrollContainer={scrollWidth:9000,clientWidth:1500,overflowX:'auto',parentElement:null};
const sceneNode={scrollWidth:100,clientWidth:100,overflowX:'hidden',parentElement:scrollContainer};
assert.equal(adapter.timelineScroller({querySelector:()=>sceneNode}),scrollContainer,'Locate true scroll container instead of last virtualized scene');

const queryField={value:'người cao tuổi nấu ăn',getAttribute:()=>null};
assert(adapter.searchReady(queryField,'người cao tuổi nấu ăn',[{id:'new'}],'old',500),'No literal heading caption is needed when the result grid changes');
assert(!adapter.searchReady(queryField,'đau đầu gối',[{id:'new'}],'old',5000),'Reject results when input is for another query');
assert(!adapter.searchReady(queryField,queryField.value,[{id:'old'}],'old',200),'Wait for unchanged stale cards');
assert(adapter.searchReady(queryField,queryField.value,[{id:'old'}],'old',3500),'Same query can legitimately return the same results');
const emptyNotice={offsetWidth:10,textContent:'Rất tiếc, chúng tôi không tìm thấy video nào cho “microvessels”. Hãy thử tìm kiếm nội dung liên quan.'};
const emptyPanel={querySelectorAll:()=>[emptyNotice]};
const microField={value:'microvessels',getAttribute:()=>null};
assert(adapter.emptyVideoResult(microField,'microvessels',emptyPanel));
assert(!adapter.emptyVideoResult({...microField,value:'mạch máu'},'mạch máu',emptyPanel),'An old empty result must not skip a new search');
assert(!adapter.emptyVideoResult({...microField,getAttribute:()=> 'true'},'microvessels',emptyPanel),'A loading result is not final');
assert.equal(adapter.uploadInput({querySelectorAll:()=>[{accept:'video/mp4'}]},'video').accept,'video/mp4');
assert.equal(adapter.eligibleCards([{id:'x',title:'Senior man smiling at home',duration:8}],{duration:3,positive:['senior'],subjects:['papaya']},[]).length,0,'Reject generic elderly footage for an explicit food subject');

assert(!adapter.subjectMatch('Senior woman enjoying her day','da'),'Short Vietnamese noun must not match part of another word');
assert(adapter.subjectMatch('Woman massaging legs','leg'),'Plural subject is accepted');

const photo={id:'photo:123',title:'Doctor explaining diagnosis to senior patient',duration:Infinity,media_kind:'image'};
assert.equal(adapter.eligibleCards([photo],{duration:4,positive:['doctor'],subjects:['doctor'],actions:['explain']},[]).length,1,'Still photos do not need a source-video duration');
assert.equal(adapter.eligibleCards([photo],{duration:4,positive:['doctor'],subjects:['doctor'],actions:['explain']},['photo:123']).length,0,'Do not reuse stock photos');

// Photo timing must also commit an already-open popover and retain tail seeking.
(async()=>{
 let committed=5,focused=false,blurred=false,plusScrolled=false;
 class Input{
  constructor(){this.current='5';this.offsetWidth=10;}
  set value(v){this.current=v;} get value(){return this.current;}
  getAttribute(k){return k==='placeholder'?'--':null;}
  focus(){focused=true;} blur(){blurred=true;committed=Number(this.value);}
  dispatchEvent(event){if(event.type==='keydown'&&event.key==='Enter'&&event.keyCode===13)committed=Number(this.value);} getClientRects(){return [1];}
 }
 const field=new Input();
 const button={offsetWidth:10,getAttribute:k=>k==='aria-label'?committed+' giây, sửa thời gian':null,getClientRects:()=>[1],focus:()=>field.blur(),scrollIntoView:()=>{},click:()=>{field.offsetWidth=0;field.getClientRects=()=>[];}};
 const plus={...button,getAttribute:k=>k==='aria-label'?'Thêm nội dung đa phương tiện/cảnh trống':null,scrollIntoView:()=>plusScrolled=true};
 const sliders=['biên bắt đầu','biên kết thúc'].map((l,i)=>({getAttribute:k=>k==='aria-label'?l:k==='aria-valuenow'?String(i?committed*1e6:0):null}));
 const row={parentElement:{querySelector:()=>sliders[0],querySelectorAll:()=>sliders},querySelector:()=>({src:'image.png'}),querySelectorAll:()=>[]};
 const doc={activeElement:field,body:field,querySelectorAll:s=>s==='input'?[field]:s==='[data-role="timeline-scene"]'?[row]:[button,plus]};
 const env={globalThis:{},document:doc,HTMLInputElement:Input,HTMLTextAreaElement:class{},Event:class{},KeyboardEvent:class{constructor(type,options){this.type=type;Object.assign(this,options);}},getComputedStyle:()=>({visibility:'visible'}),setTimeout:f=>{f();},Promise,console};
 vm.createContext(env);vm.runInContext(fs.readFileSync('extension/adapter.js','utf8'),env);
 await env.globalThis.SKSTAdapter.timePhoto(4.24);
 assert(focused&&blurred);assert.equal(committed,4.2,'Round and commit pending duration even when popover was already open');
 await env.globalThis.SKSTAdapter.tail();
 assert(plusScrolled,'Seek the picture-track endpoint, not the end of a longer voice');
})().catch(e=>{console.error(e);process.exitCode=1;});

assert.equal(adapter.uploadInput({querySelectorAll:()=>[{accept:'video/mp4'},{accept:'image/png'}]},'image').accept,'image/png','PNG error cards must use an image-compatible upload input');

(async()=>{
 let selected='true',clicks=0;
 const tab={offsetWidth:10,textContent:'Tải lên',getAttribute:k=>k==='aria-label'?'Tải lên':k==='aria-selected'?selected:null,scrollIntoView:()=>{},click:()=>{clicks++;selected=selected==='true'?'false':'true';}};
 const input={accept:'*/*',disabled:false};
 const doc={querySelectorAll:s=>s.startsWith('input')?(selected==='true'?[input]:[]):[tab]};
 const env={globalThis:{},document:doc,getComputedStyle:()=>({visibility:'visible'}),setTimeout:f=>f(),Promise,console};
 vm.createContext(env);vm.runInContext(fs.readFileSync('extension/adapter.js','utf8'),env);
 await env.globalThis.SKSTAdapter.ensureUploadPanel();
 assert.equal(clicks,0,'An open upload panel must never be collapsed by clicking its selected tab');
 selected='false';await env.globalThis.SKSTAdapter.ensureUploadPanel();
 assert.equal(clicks,1);assert.equal(selected,'true','A closed upload panel is opened once');
 await env.globalThis.SKSTAdapter.ensureUploadPanel();assert.equal(clicks,1);
})().catch(e=>{console.error(e);process.exitCode=1;});

const bloodScene={duration:4,allow_all_media:true,subjects:['blood','artery'],actions:['flow'],positive:['blood','artery'],negative:[]};
const broadBlood={...bloodScene,topic_only:true};
const researchScene={...broadBlood,subjects:['research study','nghiên cứu'],positive:['research study','nghiên cứu'],actions:[]};
const researchCards=[
 {id:'lab',title:'Scientists working with a microscope in a laboratory',duration:19},
 {id:'exact',title:'Clinical research study',duration:8},
 {id:'school',title:'Student studying for exams',duration:20},
 {id:'short',title:'Scientist working',duration:2}
];
assert.equal(adapter.eligibleCards(researchCards,researchScene,[]).map(c=>c.id).join(','),'exact','Direct stock is searched first');
const researchFallback=adapter.illustrationScene(researchScene);
assert.equal(adapter.eligibleCards(researchCards,researchFallback,[]).map(c=>c.id).join(','),'lab','Illustration admits laboratory footage after exact search');
assert.equal(adapter.eligibleCards(researchCards,researchFallback,['lab']).length,0,'Research fallback preserves duration and repeat checks');
assert.equal(adapter.eligibleCards(researchCards,broadBlood,[]).length,0,'Research captions must not stand in for other subjects');
const journalScene={...researchScene,subjects:['Journal of Physiology'],queries:['Journal of Physiology']};
const journalFallback=adapter.illustrationScene(journalScene);
assert.ok(journalFallback.queries.includes('scientific journal'),'Older citations get stock fallback queries');
const journalCards=[{id:'paper',title:'Scientist reading a research paper',duration:9},{id:'school',title:'Student writing in her journal',duration:10}];
assert.equal(adapter.eligibleCards(journalCards,journalFallback,[]).map(c=>c.id).join(','),'paper','Personal diaries do not stand in for research papers');
const concreteScene={...researchScene,subjects:['green apple'],positive:['green apple'],queries:['green apple']};
const fruitCards=[{id:'right',title:'Apples with green peel',duration:9},{id:'wrong',title:'Green pears',duration:9}];
assert.equal(adapter.eligibleCards(fruitCards,concreteScene,[]).map(c=>c.id).join(','),'right','Reordered words must still include the concrete subject');
assert.equal(adapter.illustrationScene(concreteScene),null);
const vesselCards=[
 {id:'vessel',title:'3D atherosclerosis inside a human artery',duration:5},
 {id:'road',title:'Aerial view of a highway interchange',duration:23},
 {id:'short',title:'Artery with plaque',duration:2},
 {id:'teeth',title:'Dentist shows plaque on teeth',duration:8},
];
for(const subjects of [['blood vessel walls','thành mạch'],['blood vessel lumen','lòng mạch'],
                       ['arterial stiffness','độ cứng thành mạch']]){
 const scene={...researchScene,duration:4.7,subjects,positive:subjects};
 assert.equal(adapter.eligibleCards(vesselCards,scene,[]).length,0,'Source captions omit the precise description');
 const fallback=adapter.illustrationScene(scene);
 assert.ok(fallback.queries.includes('mạch máu'));
 assert.equal(adapter.eligibleCards(vesselCards,fallback,[]).map(c=>c.id).join(','),'vessel');
 assert.equal(adapter.eligibleCards(vesselCards,fallback,['vessel']).length,0);
}
const customIllustration={...journalScene,illustration_queries:['printed scientific article']};
for(const [subjects,near,wrong] of [
  [['orange juice','nước ép cam'],'Sliced orange on a table','Orange neon frame'],
  [['arterial plaque','thành mạch xơ vữa'],'Red blood cells in motion','Dental plaque removal'],
  [['blood vessel'],'Red blood cells in motion','Blood glucose meter'],
  [['elastin fibers','sợi elastin'],'Elastic connective tissue animation','Fabric threads'],
  [['microvessels','vi mạch'],'Red blood cells flowing in an artery','Highway interchange'],
  [['glomerulus','cầu thận'],'Human kidney anatomy','Human stomach anatomy'],
  [['brain microvessels','vi mạch trong não'],'Human brain animation','Office desk'],
  [['back muscles and tendons','gân cơ vùng lưng'],'Human lower back anatomy','Back to school supplies'],
  [['person with back pain','người đau lưng'],'Woman holding her lower back','Knee pain while running'],
  [['measuring blood glucose','đo đường huyết'],'Insulin vial and syringe','Traffic on a highway'],
]){
 const scene={...researchScene,subjects,positive:subjects};
 const illustration=adapter.illustrationScene(scene);
 const cards=[{id:'used',title:near,duration:8},{id:'near',title:near,duration:8},{id:'wrong',title:wrong,duration:8}];
 assert.equal(adapter.stockCandidates(cards,scene,['used','title:'+adapter.norm(near)],false,illustration).map(c=>c.id).join(','),'near',subjects[0]);
 assert.equal(adapter.stockCandidates(cards,scene,['used','near'],false,illustration).length,0,subjects[0]);
 assert.equal(adapter.stockCandidates(cards,scene,['used','near'],true,illustration)[0].id,'used',subjects[0]);
}
assert.equal(adapter.stockDuration('EDU 1:09'),69);
assert.equal(adapter.stockDuration('5,0 giây'),5);
assert.equal(adapter.stockDuration('EDU'),0);
assert.equal(adapter.illustrationScene(customIllustration).queries[0],'printed scientific article');
assert.equal(adapter.illustrationScene({...customIllustration,manual_queries:true}),null);
const foodTopic={queries:['cà rốt','carrots'],subjects:['carrot','cà rốt']};
const broadScene={duration:4,allow_all_media:true,manual_queries:true};
const titleCards=(...titles)=>titles.map((title,id)=>({id,title,duration:8}));
for(const query of ['xoa đầu','bóp đầu','đau đầu']){
 const fallback=adapter.illustrationScene({...broadScene,queries:[query]},null,true);
 assert(fallback.queries.includes('vùng đầu'));
 assert.equal(adapter.eligibleCards(titleCards('Cận cảnh đầu người','Đau bụng','Đầu gối bị đau'),fallback,[]).map(card=>card.title).join(','),'Cận cảnh đầu người');
}
for(const [query,subject,caption] of [
 ['người đang cắt củ sen cận cảnh','củ sen','Củ sen trên bàn'],
 ['animation of a hummingbird','hummingbird','Hummingbirds on a branch'],
]){
 const fallback=adapter.illustrationScene({...broadScene,queries:[query]},null,true);
 assert(fallback.queries.includes(subject),query);
 assert.equal(adapter.eligibleCards(titleCards(caption,'Generic illustration of a table'),fallback,[]).map(card=>card.title).join(','),caption);
}
const carrotScene={duration:4,allow_all_media:true,manual_queries:true,queries:['người cắt cà rốt thành lát']};
const carrotFallback=adapter.illustrationScene(carrotScene,foodTopic);
assert(carrotFallback.queries.includes('cà rốt'));
assert.equal(adapter.eligibleCards([
 {id:'carrot',title:'Fresh carrots on a table',duration:8},
 {id:'other',title:'Person chopping celery',duration:9},
],carrotFallback,[]).map(card=>card.id).join(','),'carrot');
assert.equal(adapter.illustrationScene({allow_all_media:true,manual_queries:true,queries:['swimming stroke','stroke']}),null);
for(const [query,broad,caption,unrelated] of [
 ['vi mạch trong não tổn thương mô phỏng','não bộ','Human brain animation','Highway interchange'],
 ['đột quỵ mô phỏng não','đau ngực','Woman clutching her chest','Swimming freestyle stroke'],
 ['đột quỵ','não bộ','Human brain anatomy','Paint brush stroke'],
 ['máy đo vận tốc sóng mạch chuyên dụng','máy đo huyết áp','Digital blood pressure monitor','Kitchen weighing scale'],
]){
 const scene={duration:4,allow_all_media:true,manual_queries:true,queries:[query],illustration_queries:['old unrelated AI query']};
 const fallback=adapter.illustrationScene(scene);
 assert(fallback.queries.includes(broad),query);
 assert(!fallback.queries.includes('old unrelated AI query'),query);
 const cards=[{id:'ok',title:caption,duration:8},{id:'wrong',title:unrelated,duration:8}];
 assert.equal(adapter.eligibleCards(cards,fallback,[]).map(c=>c.id).join(','),'ok',query);
}
for(const [subject,correct,wrong] of [['walnut','Walnut kernels on table','Cashew nuts on table'],['stomach','Human stomach anatomy','Human intestine anatomy'],['walking','Senior walking outdoors','Senior seated exercise'],['brain','Human brain illustration','Human heart illustration'],['juice','Fresh juice in glass','Fresh fruits on table']]){
 const scene={duration:4,allow_all_media:true,topic_only:true,subjects:[subject],positive:[subject]};
 assert.equal(adapter.eligibleCards([{id:'right',title:correct,duration:10},{id:'wrong',title:wrong,duration:10}],scene,[]).map(c=>c.id).join(','),'right','Match the named object, not a neighboring subject: '+subject);
}
assert.equal(adapter.eligibleCards([{id:'diagram',duration:10,title:'Blood cells anatomy'}],broadBlood,[]).length,1,'Broad topics accept related footage without exact action');
assert.equal(adapter.eligibleCards([{id:'rainbow',duration:10,title:'Rainbow neon frame'}],broadBlood,[]).length,0,'Broad topics still reject unrelated footage');
assert.equal(adapter.eligibleCards([{id:'diagram',duration:10,title:'Blood cells anatomy'}],broadBlood,['diagram']).length,0,'Prefer unused footage within a project');
assert.equal(adapter.eligibleCards([{id:'anatomy',duration:10,title:'3D blood cells flowing in an artery'}],bloodScene,[]).length,1,'Relevant medical 3D needs no people or face');
assert.equal(adapter.eligibleCards([{id:'device',duration:8,title:'Blood glucose meter on a table'}],{duration:4,allow_all_media:true,subjects:['glucose'],positive:['glucose']},[]).length,1,'Objects and devices are valid');
assert.equal(adapter.eligibleCards([{id:'wrong',duration:10,title:'Rainbow neon frame'}],bloodScene,[]).length,0,'Unrestricted media types still require script relevance');
assert.equal(adapter.relatedCards([{id:'used',duration:10,title:'Blood cells flowing'}],bloodScene,['used']).length,0,'No repeats in related selection');

(async()=>{
 const slider=(name,now)=>({getAttribute:k=>k==='aria-label'?name:k==='aria-valuenow'?String(now):null});
 const node=sliders=>({parentElement:{querySelector:()=>sliders[0],querySelectorAll:()=>sliders},querySelector:()=>null,querySelectorAll:()=>[]});
 const rows=[node([slider('biên bắt đầu',0),slider('biên kết thúc',10000000)]),node([slider('biên kết thúc',10001000)])];
 const plus={getAttribute:k=>k==='aria-label'?'Thêm nội dung đa phương tiện/cảnh trống':null,scrollIntoView:()=>{}};
 const env={globalThis:{},document:{querySelectorAll:s=>s==='[data-role="timeline-scene"]'?rows:[plus]},getComputedStyle:()=>({visibility:'visible'}),setTimeout:f=>f(),Promise,console};
 plus.offsetWidth=10;
 vm.createContext(env);vm.runInContext(fs.readFileSync('extension/adapter.js','utf8'),env);
 const actual=env.globalThis.SKSTAdapter.timeline();
 assert.equal(actual[1].start,10,'A tiny clip without a start handle follows the previous clip, not time zero');
 assert.equal((await env.globalThis.SKSTAdapter.tail()).element,rows[1],'The final tiny clip must not be confused with its predecessor');
})().catch(e=>{console.error(e);process.exitCode=1;});

const reusableScene={...bloodScene,_usage:{often:5,rare:1,recent:1},_lastAsset:'recent'};
const reusedOptions=['often','rare','recent'].map(id=>({id,duration:8,title:'Blood circulation flowing in an artery'}));
assert.equal(adapter.reuseEligibleCards(reusedOptions,reusableScene,['often','rare','recent'])[0].id,'rare','Prefer least-used matching footage and avoid immediate repeats');
assert.equal(adapter.reuseEligibleCards([reusedOptions[2]],reusableScene,['recent'])[0].id,'recent','Reuse is allowed when it is the only fitting footage');
assert.equal(adapter.reuseEligibleCards([{id:'irrelevant',duration:10,title:'Neon frame'}],reusableScene,[]).length,0,'Reuse must never bypass relevance');

const unlinkItem={getAttribute:k=>k==='aria-label'?'Hủy liên kết thành phần đến clip':null};
assert(adapter.timelineTransitionMenu({...persistentMenu,querySelectorAll:()=>[unlinkItem]}),'The single persistent unlink control is not a blocking menu');
assert(!adapter.timelineTransitionMenu({...persistentMenu,querySelectorAll:()=>[unlinkItem,transition]}),'A real multi-action menu must still be closed');
(async()=>{
 let open=true,toggled=0,escaped=0;
 const item={getAttribute:k=>k==='aria-label'?'Sao chép':null};
 const menu={offsetWidth:10,getAttribute:k=>k==='role'?'menu':null,querySelectorAll:()=>[item,transition],textContent:'Menu clip'};
 const owner={offsetWidth:10,scrollIntoView:()=>{},click:()=>{open=false;toggled++;},getAttribute:k=>k==='aria-label'?'Tùy chọn về trang':k==='aria-expanded'?String(open):null};
 const env={globalThis:{},document:{activeElement:{dispatchEvent:()=>escaped++},querySelectorAll:s=>s.includes('aria-expanded')?(open?[owner]:[]):(open?[menu]:[])},getComputedStyle:()=>({visibility:'visible'}),setTimeout:f=>f(),Promise,console};
 vm.createContext(env);vm.runInContext(fs.readFileSync('extension/adapter.js','utf8'),env);
 await env.globalThis.SKSTAdapter.closeMenu();
 assert.equal(toggled,1,'Close the exact expanded page menu owner');assert.equal(escaped,0,'Do not send Escape to an unrelated focused element');
})().catch(e=>{console.error(e);process.exitCode=1;});

assert.equal(adapter.eligibleCards([{id:'wrongAction',duration:10,title:'Blood cells anatomy'}],bloodScene,[]).length,0,'All media styles must still match the spoken action');
assert.equal(adapter.relatedCards([{id:'wrongAction',duration:10,title:'Blood cells anatomy'}],bloodScene,[]).length,0,'Related results cannot bypass action matching');
assert.equal(adapter.errorPlacement(1,{start:0,end:5,image:''},{id:1,start:0}),'append');
assert.equal(adapter.errorPlacement(17,{start:60,end:90,image:'clip'},{id:17,start:60}),'replace','A failed trim replaces only the exact failed scene');
assert.equal(adapter.errorPlacement(16,{start:56,end:60,image:'clip'},{id:17,start:60}),'append','A failed search appends one error image');
assert.equal(adapter.errorPlacement(17,{start:56,end:60,image:'clip'},{id:17,start:60}),'unknown','Never delete a different scene');
(async()=>{
 const drawn=[];let ctx={font:'',fillRect:()=>{},measureText:t=>({width:t.length*parseInt(ctx.font.replace('bold ',''))*.65}),fillText:(text,x,y)=>drawn.push({text,x,y,font:ctx.font})};
 const env={globalThis:{},document:{createElement:()=>({getContext:()=>ctx,toDataURL:()=> 'data:image/png;base64,UE5H'})},console};
 vm.createContext(env);vm.runInContext(fs.readFileSync('extension/adapter.js','utf8'),env);
 assert.equal(env.globalThis.SKSTAdapter.errorImage(('LỖI 80% %{n} '+ 'x'.repeat(500)+'\n').repeat(3)),'UE5H');
 assert(drawn.length>3);assert(drawn.every(d=>d.y>=70&&d.y<1000),'All error text must stay inside the card');
 assert(drawn.some(d=>d.text.includes('80%')),'Percent signs are literal');
})().catch(e=>{console.error(e);process.exitCode=1;});
(async()=>{
 let offset=0,name='SKST_voice_correct.wav';
 const slider=(kind,value)=>({getAttribute:k=>k==='aria-label'?kind:k==='aria-valuenow'?String(value):null});
 const sliders=[slider('biên bắt đầu',0),slider('biên kết thúc',4000000)];
 const row={parentElement:{querySelector:()=>sliders[0],querySelectorAll:()=>sliders},querySelector:()=>({src:'clip'}),querySelectorAll:()=>[]};
 const plus={offsetWidth:10,getAttribute:k=>k==='aria-label'?'Thêm nội dung đa phương tiện/cảnh trống':null,scrollIntoView:()=>{}};
 const audio={getAttribute:k=>k==='aria-label'?name+' đoạn âm thanh':null,querySelectorAll:()=>[slider('biên bắt đầu',offset),slider('biên kết thúc',4000000)]};
 const doc={querySelectorAll:s=>s==='[data-role="timeline-scene"]'?[row]:s.includes('[role="menu"]')?[]:[plus,audio]};
 const env={globalThis:{},document:doc,getComputedStyle:()=>({visibility:'visible'}),setTimeout:f=>f(),Promise,console};
 vm.createContext(env);vm.runInContext(fs.readFileSync('extension/adapter.js','utf8'),env);
 const task={count:1,duration:4,voice_name:'SKST_voice_correct.wav'};
 await env.globalThis.SKSTAdapter.auditTask(task);
 offset=1000000;await assert.rejects(()=>env.globalThis.SKSTAdapter.auditTask(task),/giây 0/);
 offset=0;name='SKST_voice_wrong.wav';await assert.rejects(()=>env.globalThis.SKSTAdapter.auditTask(task),/voice trên timeline/);
})().catch(e=>{console.error(e);process.exitCode=1;});

(async()=>{
 let title='Thiết kế không tên - Video',value='Thiết kế không tên - Video',commits=0;
 class Input{get value(){return value;}set value(v){value=v;}getAttribute(k){return k==='aria-label'?'Tên thiết kế':null;}focus(){}blur(){title=value+' - Canva';commits++;}dispatchEvent(){}get offsetWidth(){return 100;}}
 class Textarea{}
 const input=new Input();
 const document={get title(){return title;},querySelectorAll:s=>s.startsWith('input,textarea')?[input]:[]};
 const env={globalThis:{},document,HTMLInputElement:Input,HTMLTextAreaElement:Textarea,KeyboardEvent:class{},Event:class{},getComputedStyle:()=>({visibility:'visible'}),setTimeout:f=>f(),Promise,console};
 vm.createContext(env);vm.runInContext(fs.readFileSync('extension/adapter.js','utf8'),env);
 let checks=0;
 const result=await env.globalThis.SKSTAdapter.run({kind:'rename',design_name:'Bài 1.2'},async()=>{checks++;});
 assert.equal(result.design_name,'Bài 1.2');assert.equal(value,'Bài 1.2');assert.equal(commits,1);assert(checks>0,'Rename obeys the pause/session guard');
 const again=await env.globalThis.SKSTAdapter.run({kind:'rename',design_name:'Bài 1.2'},async()=>{});
 assert.equal(again.design_name,'Bài 1.2');assert.equal(value,'Bài 1.2','Resuming never appends a second part suffix');
})().catch(e=>{console.error(e);process.exitCode=1;});

(async()=>{
 let value='5.0 giây',end=114.98,open=true,enters=0,commits=0,applyAll=0,requiresEnter=false;
 const start=109.98;
 class Input{get value(){return value;}set value(v){value=v;}getAttribute(k){return k==='placeholder'?'--':null;}focus(){}blur(){if(!requiresEnter){end=start+Math.floor(Number(value)*10+1e-8)/10;commits++;}}dispatchEvent(e){if(e.key==='Enter'){enters++;if(requiresEnter){end=start+Number(value);open=false;}}}get offsetWidth(){return open?50:0;}get offsetHeight(){return 0;}getClientRects(){return open?[{}]:[];}}
 class Textarea{}
 const field=new Input();
 const owner={offsetWidth:50,scrollIntoView:()=>{},getAttribute:k=>k==='aria-label'?'5.0 giây, sửa thời gian':null,focus:()=>field.blur(),click:()=>{open=!open;}};
 const all={offsetWidth:50,scrollIntoView:()=>{},getAttribute:k=>k==='aria-label'?'Áp dụng cho mọi trang':null,click:()=>applyAll++};
 const slider=(label,read)=>({getAttribute:k=>k==='aria-label'?label:k==='aria-valuenow'?String(read()*1e6):null});
 const sliders=[slider('biên bắt đầu',()=>start),slider('biên kết thúc',()=>end)];
 const row={parentElement:{querySelector:()=>sliders[0],querySelectorAll:()=>sliders},querySelector:()=>({src:'error.png'}),querySelectorAll:()=>[]};
 const document={querySelectorAll:s=>s==='[data-role="timeline-scene"]'?[row]:s==='input'?[field]:[owner,all]};
 const env={globalThis:{},document,HTMLInputElement:Input,HTMLTextAreaElement:Textarea,KeyboardEvent:class{constructor(_,o){this.key=o.key;}},Event:class{},getComputedStyle:()=>({visibility:'visible'}),setTimeout:f=>f(),Promise,console};
 vm.createContext(env);vm.runInContext(fs.readFileSync('extension/adapter.js','utf8'),env);
 await env.globalThis.SKSTAdapter.timePhoto(4.02);
 assert.equal(enters,0,'Never commit stale React state by sending immediate Enter');
 assert.equal(commits,1);assert.equal(applyAll,0);assert.equal(open,false);
 assert(Math.abs(end-113.98)<.001,'Persist the rounded image duration on the timeline');
 // The stale toolbar caption is still 5.0 above: actual timeline is authoritative.
 await env.globalThis.SKSTAdapter.timePhoto(4.02);assert.equal(commits,1,'A resumed correct error image must not be edited or uploaded again');
 end=start+5;
 await env.globalThis.SKSTAdapter.timePhoto(4.92);
 assert.equal(commits,1,'Accept an existing 5 s error card for a 4.92 s scene without reopening Canva timing');
 assert.equal(end,start+5);
 open=true;value='5.0 giây';end=start+5;
 await env.globalThis.SKSTAdapter.timePhoto(1.195);
 assert.equal(value,'1.2','Round before sending to a control that truncates extra decimals');
 assert(Math.abs(end-start-1.2)<.000001);assert.equal(commits,2);
 requiresEnter=true;open=false;end=start+5;
 await env.globalThis.SKSTAdapter.timePhoto(4.82);
 assert(Math.abs(end-start-4.8)<.000001,'Confirm the existing 5 s card when blur alone does not commit');
 assert(enters>0);assert.equal(applyAll,0);
})().catch(e=>{console.error(e);process.exitCode=1;});

(async()=>{
 let end=5,open=false,value='5.0';
 class Input{get value(){return value;}set value(v){value=v;}get offsetWidth(){return open?10:0;}
  getClientRects(){return open?[{}]:[];}getAttribute(k){return k==='placeholder'?'--':null;}focus(){}dispatchEvent(){}}
 const field=new Input();
 const element=(name,handlers={})=>({offsetWidth:10,getAttribute:k=>k==='aria-label'?name:null,scrollIntoView(){},...handlers});
 const timing=element('5.0 giây, sửa thời gian',{click:()=>{open=!open},focus:()=>{end=Number(value)}});
 const plus=element('Thêm nội dung đa phương tiện/cảnh trống');
 const slider=(name,read)=>({getAttribute:k=>k==='aria-label'?name:k==='aria-valuenow'?String(read()*1e6):null});
 const sliders=[slider('biên bắt đầu',()=>0),slider('biên kết thúc',()=>end)];
 const row=element('scene',{click(){},parentElement:{querySelector:()=>sliders[0],querySelectorAll:()=>sliders},
  querySelector:s=>s==='img'?{src:'card.png'}:null,querySelectorAll:()=>[]});
 const audio=element('voice.wav đoạn âm thanh',{querySelectorAll:()=>[slider('biên bắt đầu',()=>0),slider('biên kết thúc',()=>3.36)]});
 const document={querySelectorAll:s=>s==='[data-role="timeline-scene"]'?[row]:s==='input'?[field]:s.includes('[role="menu"]')?[]:[timing,plus,audio]};
 const env={globalThis:{},document,HTMLInputElement:Input,HTMLTextAreaElement:class{},Event:class{},getComputedStyle:()=>({visibility:'visible'}),setTimeout:f=>f()};
 vm.runInNewContext(fs.readFileSync('extension/adapter.js','utf8'),env);
 const result=await env.globalThis.SKSTAdapter.run({kind:'manual_review',fit_final:true,scene:{id:1},allowed_counts:[1],voice_name:'voice.wav',voice_duration:3.36},async()=>{});
 assert.equal(result.verified_end,3.4,'Fit the final 5-second card to the verified 3.36-second voice');
})().catch(e=>{console.error(e);process.exitCode=1;});

// Canva only mounts a window of a long timeline. A manual confirmation at
// scene 50 and the final audit must read the same complete picture track.
(async()=>{
 const scroller={scrollLeft:0,scrollWidth:1000,clientWidth:320,overflowX:'auto'};
 const slider=(label,time)=>({getAttribute:k=>k==='aria-label'?label:k==='aria-valuenow'?String(time*1e6):null});
 const rows=Array.from({length:50},(_,i)=>{
   const sliders=[...(i===30?[]:[slider('biên bắt đầu',i*4)]),slider('biên kết thúc',(i+1)*4)];
   return {parentElement:{parentElement:scroller,querySelector:()=>sliders[0],querySelectorAll:()=>sliders},querySelector:()=>({src:'clip-'+i}),querySelectorAll:()=>[]};
 });
 const plus={offsetWidth:10,getAttribute:k=>k==='aria-label'?'Thêm nội dung đa phương tiện/cảnh trống':null,scrollIntoView:()=>{scroller.scrollLeft=680;}};
 const name='SKST_voice_part1.mp3';
 const audio={getAttribute:k=>k==='aria-label'?name+' đoạn âm thanh':null,querySelectorAll:()=>[slider('biên bắt đầu',0),slider('biên kết thúc',200)]};
 const document={querySelectorAll:s=>{
   if(s==='[data-role="timeline-scene"]'){
     const first=Math.floor(scroller.scrollLeft/20);
     return rows.slice(first,first+16);
   }
   return s.includes('[role="menu"]')?[]:[plus,audio];
 }};
 const env={globalThis:{},document,getComputedStyle:e=>({visibility:'visible',overflowX:e.overflowX}),setTimeout:f=>f(),Promise,console};
 vm.createContext(env);vm.runInContext(fs.readFileSync('extension/adapter.js','utf8'),env);
 const adapter=env.globalThis.SKSTAdapter;
 const review=await adapter.run({kind:'manual_review',scene:{id:50},allowed_counts:[50],voice_name:name,voice_duration:200},async()=>{});
 assert.equal(review.verified_count,50);assert.equal(review.verified_start,196);
 assert.equal(review.frames[30].start,120,'Recover a missing start handle from the previous scene');
 assert.equal(scroller.scrollLeft,680,'Restore the visible timeline after verification');
 assert.equal((await adapter.auditTask({count:50,duration:200,voice_name:name})).verified_count,50);
 rows.pop();
 await assert.rejects(()=>adapter.auditTask({count:50,duration:200,voice_name:name}),/Canva có 49 cảnh/);
})().catch(e=>{console.error(e);process.exitCode=1;});

// Canva truncates a long decimal input: send an explicitly rounded tenth.
for(const d of [.1,.149,.15,.195,.999,1.195,2.999,4.782,4.25,5.057]){
 const q=adapter.photoDuration(d),canva=Math.floor(Number(String(q))*10+1e-8)/10;
 assert(Math.abs(canva-d)<=.050001,`Canva must keep rounded duration ${d}, got ${canva}`);
}
let plannedEnd=0,actualEnd=0;
for(let i=0;i<500;i++){
 plannedEnd+=[1.195,4.782,2.999,3.337,.195][i%5];
 actualEnd+=adapter.photoDuration(plannedEnd-actualEnd);
 assert(Math.abs(actualEnd-plannedEnd)<=.050001,'Absolute endpoint compensation must prevent cumulative drift');
}

(async()=>{
 let image=true,end=4,voiceEnd=8,changed=0,checks=0;
 const slider=(label,get)=>({getAttribute:k=>k==='aria-label'?label:k==='aria-valuenow'?String(get()*1e6):null});
 const sliders=[slider('biên bắt đầu',()=>0),slider('biên kết thúc',()=>end)];
 const row={parentElement:{querySelector:()=>sliders[0],querySelectorAll:()=>sliders},querySelector:()=>image?{src:'manual-photo'}:null,querySelectorAll:()=>[]};
 const rows=[row];
 const plus={offsetWidth:20,getAttribute:k=>k==='aria-label'?'Thêm nội dung đa phương tiện/cảnh trống':null,scrollIntoView:()=>{},click:()=>changed++};
 const audio={getAttribute:k=>k==='aria-label'?'SKST_voice_manual.wav đoạn âm thanh':null,querySelectorAll:()=>[slider('biên bắt đầu',()=>0),slider('biên kết thúc',()=>voiceEnd)]};
 const doc={querySelectorAll:s=>s==='[data-role="timeline-scene"]'?rows:s.includes('[role="menu"]')?[]:[plus,audio]};
 const env={globalThis:{},document:doc,getComputedStyle:()=>({visibility:'visible'}),setTimeout:f=>f(),Promise,console};
 vm.createContext(env);vm.runInContext(fs.readFileSync('extension/adapter.js','utf8'),env);
 const task={id:'manual:1',kind:'manual_review',scene:{id:1,start:0,duration:4},allowed_counts:[1],voice_name:'SKST_voice_manual.wav',voice_duration:8};
 const run=()=>env.globalThis.SKSTAdapter.run(task,async()=>{checks++;});
 const ok=await run();assert.equal(ok.manual_verified,true);assert.equal(ok.verified_end,4);assert.equal(ok.verified_voice_end,8);assert(checks>0);assert.equal(changed,0,'Manual review must never insert, trim or delete the user repair');
 end=5;assert.equal((await run()).verified_end,5,'Keep a relative user edit and send its real endpoint for compensation');end=4;
 image=false;await assert.rejects(run,/chưa có ảnh/);image=true;
 rows.push(row);await assert.rejects(run,/Canva có 2 cảnh/);rows.pop();
 voiceEnd=7;await assert.rejects(run,/Voice trên Canva/);assert.equal(changed,0);
})().catch(e=>{console.error(e);process.exitCode=1;});

(async()=>{
 let display='Untitled design - Video',pending=display,editing=false,activated=0,enters=0;
 let document;
 class Input{
  get value(){return pending;}set value(v){pending=v;}
  getAttribute(k){return k==='aria-label'?'Tiêu đề thiết kế':k==='tabindex'?'-1':null;}
  closest(){return owner;}get offsetWidth(){return 100;}
  focus(){document.activeElement=this;}blur(){if(editing){display=pending;editing=false;}}
  dispatchEvent(e){if(e.key==='Enter')enters++;}
 }
 const field=new Input();
 const owner={offsetWidth:100,get textContent(){return display;},getAttribute:()=>null,scrollIntoView(){},click(){activated++;editing=true;pending='';document.activeElement=field;}};
 const outside={offsetWidth:20,getAttribute:k=>k==='aria-label'?'Điểm bắt đầu khung vẽ':null,focus(){field.blur();document.activeElement=this;}};
 document={title:'Untitled design - Video',activeElement:null,querySelectorAll:s=>s.startsWith('input,textarea')?[field]:s.includes('[role="menu"]')?[]:[outside,owner]};
 const env={globalThis:{},document,HTMLInputElement:Input,HTMLTextAreaElement:class{},Event:class{},KeyboardEvent:class{constructor(_,o){Object.assign(this,o);}},getComputedStyle:()=>({visibility:'visible'}),setTimeout:f=>f(),Promise,console};
 vm.createContext(env);vm.runInContext(fs.readFileSync('extension/adapter.js','utf8'),env);
 const run=()=>env.globalThis.SKSTAdapter.run({kind:'rename',design_name:'Bài 9.5'},async()=>{});
 const output=await run();assert.equal(output.design_name,'Bài 9.5');assert.equal(output.rename_warning,undefined);
 assert.equal(activated,1,'Activate Canva menuitem before editing the initially inactive title field');
 assert.equal(display,'Bài 9.5');assert.equal(enters,0,'Do not send immediate Enter');
 assert.equal(document.title,'Untitled design - Video','A stale browser title must not block a committed header name');
 await run();assert.equal(activated,1,'An already named part is idempotent');
 let n=0;await assert.rejects(()=>env.globalThis.SKSTAdapter.run({kind:'rename',design_name:'Bài 9.6'},async()=>{if(++n===2)throw Error('Đã tạm dừng theo yêu cầu.');}),/tạm dừng/);
})().catch(e=>{console.error(e);process.exitCode=1;});
