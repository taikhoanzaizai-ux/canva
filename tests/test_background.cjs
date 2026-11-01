const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
function harness(tabs,diskVersion,updateVersion){
 const manifest=JSON.parse(fs.readFileSync('extension/manifest.json','utf8'));
 const local={token:'test-token',enabled:true};const calls={fetch:[],inject:[],reload:0,created:[]};let listener,attached=false;
 const chrome={
  runtime:{id:'own',getURL:p=>'chrome-extension://own/'+p,getManifest:()=>manifest,onMessage:{addListener:fn=>listener=fn},onInstalled:{addListener:()=>{}},reload:()=>calls.reload++},
  storage:{local:{get:async()=>local,set:async value=>Object.assign(local,value)}},
  tabs:{create:async spec=>{calls.created.push(spec);return {id:77,url:spec.url};},get:async()=>({id:77,url:'https://www.canva.com/design/new/token/edit'}),query:async()=>tabs,sendMessage:async(id,msg)=>({ready:true})},
  scripting:{executeScript:async spec=>{calls.inject.push(spec);attached=true;}}
 };
 const context={chrome,URL,AbortSignal,setTimeout,Promise,console,fetch:async(url,opts)=>{
  if(url.startsWith('chrome-extension://'))return {ok:true,json:async()=>({...manifest,version:diskVersion||manifest.version})};
  calls.fetch.push({url,body:JSON.parse(opts.body)});
  if(url.endsWith('/checkpoint'))return {ok:true,json:async()=>({continue_:true})};
  if(url.endsWith('/companion/update')&&updateVersion)return {ok:true,json:async()=>({manifest:{...manifest,version:updateVersion},mode:'paused',active_task:false})};
  return {ok:true,json:async()=>({ok:true,version:manifest.version,target:'https://www.canva.com/design/target/token/edit',mode:'paused',active_task:false,connection:{ready:attached}})};
 }};
 vm.createContext(context);vm.runInContext(fs.readFileSync('extension/background.js','utf8'),context);
 return {calls,manifest,decision:context.reloadDecision,message:(msg,sender)=>new Promise(resolve=>listener(msg,sender,resolve))};
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
 const parts=h.manifest.version.split('.').map(Number);parts[2]++;const nextVersion=parts.join('.');
 const update=harness([],nextVersion);
 const pending=await update.message({type:'probe'},{id:'own',url:'chrome-extension://own/popup.html'});
 assert.equal(pending.reloading,true);assert.equal(update.calls.inject.length,0,'Reload before allocating work');
 await new Promise(r=>setTimeout(r,350));assert.equal(update.calls.reload,1);
 const newer={...h.manifest,version:nextVersion};
 assert.equal(h.decision(h.manifest,newer,{mode:'running',active_task:true}),'busy');
 assert.equal(h.decision(h.manifest,{...newer,permissions:[...newer.permissions,'history']},{mode:'paused'}),'permission_change','Never auto-accept additional permissions');
 assert.equal(h.decision(h.manifest,{...h.manifest,version:'0.2.3'},{mode:'paused'}),'none','Never downgrade');
 const success=harness([],null,nextVersion);
 const upgraded=await success.message({type:'update_companion'},{id:'own',url:'chrome-extension://own/popup.html'});
 assert.equal(upgraded.reloading,true);await new Promise(r=>setTimeout(r,450));assert.equal(success.calls.reload,1);
 const contentDenied=await success.message({type:'update_companion'},{id:'own',tab:{id:2},url:'https://www.canva.com/design/target/token/edit'});
 assert(contentDenied.error,'Only popup can request reload');
 const explicit=harness([]);
 const current=await explicit.message({type:'update_companion'},{id:'own',url:'chrome-extension://own/popup.html'});
 // Fixture supplies no local manifest: a failed update must never reload.
 assert(current.error);assert.equal(explicit.calls.reload,0);
 const external=await explicit.message({type:'update_companion'},{id:'wrong',url:'https://example.com'});
 assert(external.error);
 const next=harness([]);
 const sender={id:'own',tab:{id:1},url:'https://www.canva.com/design/target/token/edit'};
 const body={id:'next_design',client:'A',create_url:'https://www.canva.com/design?create&type=TADUvCyAV_U'};
 const newPart=await next.message({type:'open_next',body},sender);
 assert.equal(newPart.new_target,'https://www.canva.com/design/new/token/edit');assert.equal(next.calls.created.length,1);
 await next.message({type:'open_next',body},sender);assert.equal(next.calls.created.length,1,'Reuse existing next tab after retry');
 const unsafe=await next.message({type:'open_next',body:{...body,create_url:'https://example.com/design?create&type=TADUvCyAV_U'}},sender);
 assert(unsafe.error);assert.equal(next.calls.created.length,1);
 const manifest=JSON.parse(fs.readFileSync('extension/manifest.json','utf8'));
 assert(manifest.permissions.includes('scripting'));assert(manifest.host_permissions.every(v=>v.startsWith('https://www.canva.com/')||v.startsWith('http://127.0.0.1:8766/')));
 console.log('Controller attachment, exact design selection, and permission scope checks passed.');
})().catch(e=>{console.error(e);process.exitCode=1;});
