const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
function harness(tabs,diskVersion,updateVersion,options={}){
 const manifest=JSON.parse(fs.readFileSync('extension/manifest.json','utf8'));
 const local={token:'test-token',enabled:true};const calls={fetch:[],inject:[],reload:0,created:[]};let listener,updated,attached=false;
 const chrome={
  runtime:{id:'own',getURL:p=>'chrome-extension://own/'+p,getManifest:()=>manifest,onMessage:{addListener:fn=>listener=fn},onInstalled:{addListener:()=>{}},reload:()=>calls.reload++},
  storage:{local:{get:async()=>local,set:async value=>Object.assign(local,value)}},
  tabs:{onUpdated:{addListener:fn=>updated=fn},create:async spec=>{calls.created.push(spec);return {id:77,url:spec.url};},get:async()=>({id:77,url:options.finalURL||'https://www.canva.com/design/new/token/edit'}),query:async()=>tabs,sendMessage:async(id,msg)=>({ready:true})},
  scripting:{executeScript:async spec=>{calls.inject.push(spec);attached=true;}}
 };
 const context={chrome,URL,URLSearchParams,AbortSignal,setTimeout,Promise,console,fetch:async(url,opts)=>{
  if(url.startsWith('chrome-extension://'))return {ok:true,json:async()=>({...manifest,version:diskVersion||manifest.version})};
  calls.fetch.push({url,body:JSON.parse(opts.body)});
  if(url.endsWith('/checkpoint'))return {ok:true,json:async()=>({continue_:true})};
  if(url.endsWith('/companion/update')&&updateVersion)return {ok:true,json:async()=>({manifest:{...manifest,version:updateVersion},mode:'paused',active_task:false})};
  return {ok:true,json:async()=>({ok:true,version:manifest.version,target:'https://www.canva.com/design/target/token/edit',mode:'paused',active_task:false,connection:{ready:attached},...options.state})};
 }};
 vm.createContext(context);vm.runInContext(fs.readFileSync('extension/background.js','utf8'),context);
 return {calls,manifest,navigate:(tab,change={url:tab.url})=>updated(tab.id,change,tab),decision:context.reloadDecision,message:(msg,sender)=>new Promise(resolve=>listener(msg,sender,resolve))};
}
(async()=>{
 const h=harness([{id:1,active:true,url:'https://www.canva.com/design/other/token/edit'},{id:2,active:false,url:'https://www.canva.com/design/target/token/edit?ui=e30',title:'Right design'}]);
 const result=await h.message({type:'probe'},{id:'own',url:'chrome-extension://own/popup.html'});
 assert.equal(result.attached,true);assert.equal(h.calls.inject.length,1);assert.equal(h.calls.inject[0].target.tabId,2,'Use configured design, not another active tab');
 assert.equal(h.calls.inject[0].files.join(','),'adapter.js,content.js','Inject bundled controller only');
 const navigation=harness([{id:8,url:'https://www.canva.com/design/target/token/edit'}]);
 await navigation.navigate({id:8,url:'https://www.canva.com/design/target/token/edit'});
 assert.equal(navigation.calls.inject.length,1,'SPA URL transition attaches without opening popup');
 assert.equal(navigation.calls.created.length,0,'SPA attachment never opens another tab');
 const wrongNavigation=harness([{id:9,url:'https://www.canva.com/design/other/token/edit'}]);
 await wrongNavigation.navigate({id:9,url:'https://www.canva.com/design/other/token/edit'});
 await wrongNavigation.navigate({id:10,url:'https://example.com/'});
 assert.equal(wrongNavigation.calls.inject.length,0,'Never claim unrelated Canva designs or non-Canva pages');
 const nonceNav='abcdefghijklmnopqrstuvwx';
 const createdNavigation=harness([{id:11,url:'https://www.canva.com/design/new/token/edit#skst_start='+nonceNav}],null,null,{state:{target:'',bootstrap_nonce:nonceNav}});
 await createdNavigation.navigate({id:11,url:'https://www.canva.com/design/new/token/edit#skst_start='+nonceNav});
 assert.equal(createdNavigation.calls.inject.length,1,'New design is attached only with exact bootstrap marker');
 assert.equal(createdNavigation.calls.created.length,0);
 const bad=harness([{id:3,active:true,url:'https://example.com/'}]);
 const denied=await bad.message({type:'probe'},{id:'own',url:'chrome-extension://own/popup.html'});
 assert(denied.connected_only);assert.equal(bad.calls.inject.length,0,'Never inject outside Canva');
 const closed=harness([],null,null,{finalURL:'https://www.canva.com/design/target/token/edit'});
 const reopened=await closed.message({type:'probe',open_editor:true},{id:'own',url:'chrome-extension://own/popup.html'});
 assert(reopened.attached);assert.equal(closed.calls.created[0].url,'https://www.canva.com/design/target/token/edit','Connect opens saved design automatically');
 const nonce='abcdefghijklmnopqrstuvwx';
 const creating=harness([],null,null,{finalURL:'https://www.canva.com/design/new/token/edit#skst_start='+nonce,state:{target:'',bootstrap_nonce:nonce,create_url:'https://www.canva.com/design?create&type=TADUvCyAV_U#skst_start='+nonce}});
 const started=await creating.message({type:'probe',open_editor:true},{id:'own',url:'chrome-extension://own/popup.html'});
 assert(started.attached);assert.equal(creating.calls.created.length,1,'Create missing horizontal video from popup');
 await creating.message({type:'probe',open_editor:true},{id:'own',url:'chrome-extension://own/popup.html'});
 assert.equal(creating.calls.created.length,1,'Repeated Connect reuses created tab');
 const paired=harness([],null,null,{state:{target:'',create_url:''}});
 const pairedResult=await paired.message({type:'probe',open_editor:true},{id:'own',url:'chrome-extension://own/popup.html'});
 assert(pairedResult.connected_only);assert.equal(paired.calls.created.length,0,'Pairing before planning does not require a manual tab or create an unrelated design');
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

// A legacy boolean bootstrap flag must not block an updated controller.
(async()=>{
 let version='0.8.2',sent=0,ids=0;const loops=[];
 const env={window:{__skstContentStarted:true},crypto:{randomUUID:()=>String(++ids)},chrome:{runtime:{getManifest:()=>({version}),onMessage:{addListener:()=>{}},sendMessage:async()=>{sent++;return {mode:'paused'};}}},document:{title:'Canva',querySelector:()=>null,querySelectorAll:()=>[],getElementById:()=>null},setInterval:fn=>loops.push(fn),Promise,console};
 vm.createContext(env);const code=fs.readFileSync('extension/content.js','utf8');
 vm.runInContext(code,env);await new Promise(r=>setTimeout(r,0));
 assert.equal(loops.length,1,'Replace a stale pre-update boolean controller flag');
 vm.runInContext(code,env);assert.equal(loops.length,1,'Do not duplicate a same-version controller');
 const oldLoop=loops[0];version='0.8.3';vm.runInContext(code,env);await new Promise(r=>setTimeout(r,0));
 assert.equal(loops.length,2);const before=sent;await oldLoop();
 assert.equal(sent,before,'Superseded controller must stop polling/mutating');
})().catch(e=>{console.error(e);process.exitCode=1;});
