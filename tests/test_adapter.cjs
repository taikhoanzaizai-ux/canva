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
