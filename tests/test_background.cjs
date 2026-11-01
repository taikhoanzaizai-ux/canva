const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
function harness(tabs){
 const calls={fetch:[],inject:[]};let listener,attached=false;
 const chrome={
  runtime:{id:'own',getURL:p=>'chrome-extension://own/'+p,getManifest:()=>({version:'0.2.3'}),onMessage:{addListener:fn=>listener=fn}},
  storage:{local:{get:async()=>({token:'test-token',enabled:true})}},
  tabs:{query:async()=>tabs,sendMessage:async(id,msg)=>({ready:true})},
  scripting:{executeScript:async spec=>{calls.inject.push(spec);attached=true;}}
 };
 const context={chrome,AbortSignal,setTimeout,Promise,console,fetch:async(url,opts)=>{
  calls.fetch.push({url,body:JSON.parse(opts.body)});
  return {ok:true,json:async()=>({ok:true,version:'0.2.3',target:'https://www.canva.com/design/target/token/edit',mode:'paused',connection:{ready:attached}})};
 }};
 vm.createContext(context);vm.runInContext(fs.readFileSync('extension/background.js','utf8'),context);
 return {calls,message:(msg,sender)=>new Promise(resolve=>listener(msg,sender,resolve))};
}
(async()=>{
 const h=harness([{id:1,active:true,url:'https://www.canva.com/design/other/token/edit'},{id:2,active:false,url:'https://www.canva.com/design/target/token/edit?ui=e30',title:'Right design'}]);
 const result=await h.message({type:'probe'},{id:'own',url:'chrome-extension://own/popup.html'});
 assert.equal(result.attached,true);assert.equal(h.calls.inject.length,1);assert.equal(h.calls.inject[0].target.tabId,2,'Use configured design, not another active tab');
 assert.equal(h.calls.inject[0].files.join(','),'adapter.js,content.js','Inject bundled controller only');
 const bad=harness([{id:3,active:true,url:'https://example.com/'}]);
 const denied=await bad.message({type:'probe'},{id:'own',url:'chrome-extension://own/popup.html'});
 assert(denied.error);assert.equal(bad.calls.inject.length,0,'Never inject outside Canva');
 const outsider=harness([]);
 const refused=await outsider.message({type:'probe'},{id:'wrong',url:'https://example.com/'});
 assert(refused.error);assert.equal(outsider.calls.fetch.length,0,'Untrusted sender cannot reach local bridge');
 const manifest=JSON.parse(fs.readFileSync('extension/manifest.json','utf8'));
 assert(manifest.permissions.includes('scripting'));assert(manifest.host_permissions.every(v=>v.startsWith('https://www.canva.com/')||v.startsWith('http://127.0.0.1:8766/')));
 console.log('Controller attachment, exact design selection, and permission scope checks passed.');
})().catch(e=>{console.error(e);process.exitCode=1;});
