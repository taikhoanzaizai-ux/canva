const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const context={globalThis:{},document:{},setTimeout,Promise,console};vm.createContext(context);
vm.runInContext(fs.readFileSync('extension/adapter.js','utf8'),context);
const adapter=context.globalThis.SKSTAdapter;
assert.equal(adapter.norm('Nhón GÓT chân'),'nhon got chan');
const scene={positive:['heel','senior'],negative:['ballet'],preferred:'Senior heel raise'};
assert(adapter.score({title:'Senior heel raise'},scene)>adapter.score({title:'ballet heel raise'},scene));
assert(adapter.score({title:'ballet heel raise'},scene)<-50);
console.log('Adapter ranking: passed; live Canva mutations require installed extension validation.');
