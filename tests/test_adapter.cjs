const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const context={globalThis:{},document:{},getComputedStyle:e=>({overflowX:e.overflowX}),setTimeout,Promise,console};vm.createContext(context);
vm.runInContext(fs.readFileSync('extension/adapter.js','utf8'),context);
const adapter=context.globalThis.SKSTAdapter;
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
assert.equal(adapter.uploadInput({querySelectorAll:()=>[{accept:'video/mp4'}]},'video').accept,'video/mp4');
assert.equal(adapter.eligibleCards([{id:'x',title:'Senior man smiling at home',duration:8}],{duration:3,positive:['senior'],subjects:['papaya']},[]).length,0,'Reject generic elderly footage for an explicit food subject');

assert(!adapter.subjectMatch('Senior woman enjoying her day','da'),'Short Vietnamese noun must not match part of another word');
assert(adapter.subjectMatch('Woman massaging legs','leg'),'Plural subject is accepted');

const photo={id:'photo:123',title:'Doctor explaining diagnosis to senior patient',duration:Infinity,media_kind:'image'};
assert.equal(adapter.eligibleCards([photo],{duration:4,positive:['doctor'],subjects:['doctor'],actions:['explain']},[]).length,1,'Still photos do not need a source-video duration');
assert.equal(adapter.eligibleCards([photo],{duration:4,positive:['doctor'],subjects:['doctor'],actions:['explain']},['photo:123']).length,0,'Do not reuse stock photos');

// Canva keyboard handlers require legacy keyCode in addition to key/code.
(async()=>{
 let committed=5,focused=false,blurred=false,plusScrolled=false;
 class Input{
  constructor(){this.current='5';this.offsetWidth=10;}
  set value(v){this.current=v;} get value(){return this.current;}
  getAttribute(k){return k==='placeholder'?'--':null;}
  focus(){focused=true;} blur(){blurred=true;}
  dispatchEvent(event){if(event.type==='keydown'&&event.key==='Enter'&&event.keyCode===13)committed=Number(this.value);} getClientRects(){return [1];}
 }
 const field=new Input();
 const button={offsetWidth:10,getAttribute:k=>k==='aria-label'?committed+' giây, sửa thời gian':null,getClientRects:()=>[1]};
 const plus={...button,getAttribute:k=>k==='aria-label'?'Thêm nội dung đa phương tiện/cảnh trống':null,scrollIntoView:()=>plusScrolled=true};
 const doc={activeElement:field,body:field,querySelectorAll:s=>s==='input'?[field]:s==='[data-role="timeline-scene"]'?[]:[button,plus]};
 const env={globalThis:{},document:doc,HTMLInputElement:Input,HTMLTextAreaElement:class{},Event:class{},KeyboardEvent:class{constructor(type,options){this.type=type;Object.assign(this,options);}},getComputedStyle:()=>({visibility:'visible'}),setTimeout:f=>{f();},Promise,console};
 vm.createContext(env);vm.runInContext(fs.readFileSync('extension/adapter.js','utf8'),env);
 await env.globalThis.SKSTAdapter.timePhoto(4.24);
 assert(focused&&blurred);assert.equal(committed,4.24,'Commit pending duration even when popover was already open');
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
assert.equal(adapter.eligibleCards([{id:'anatomy',duration:10,title:'3D blood cells in an artery'}],bloodScene,[]).length,1,'Relevant medical 3D needs no people or face');
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
const reusedOptions=['often','rare','recent'].map(id=>({id,duration:8,title:'Blood circulation in an artery'}));
assert.equal(adapter.reuseEligibleCards(reusedOptions,reusableScene,['often','rare','recent'])[0].id,'rare','Prefer least-used matching footage and avoid immediate repeats');
assert.equal(adapter.reuseEligibleCards([reusedOptions[2]],reusableScene,['recent'])[0].id,'recent','Reuse is allowed when it is the only fitting footage');
assert.equal(adapter.reuseEligibleCards([{id:'irrelevant',duration:10,title:'Neon frame'}],reusableScene,[]).length,0,'Reuse must never bypass relevance');
