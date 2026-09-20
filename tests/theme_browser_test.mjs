import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
const source = await readFile(new URL('../frontend/static/theme.js', import.meta.url),'utf8');
const {default:render} = await import(`data:text/javascript;base64,${Buffer.from(source).toString('base64')}`);
const root = {dataset:{}};
const stored = new Map([['trace-theme','astral']]);
const events=[];
const handlers=new Map();
globalThis.document={documentElement:root,querySelectorAll:()=>[],addEventListener:()=>{},removeEventListener:()=>{}};
globalThis.CustomEvent=class{constructor(type,options){this.type=type;this.detail=options.detail;}};
globalThis.window={localStorage:{getItem:key=>stored.get(key),setItem:(key,value)=>stored.set(key,value)},
  dispatchEvent:event=>events.push(event),addEventListener:(type,handler)=>handlers.set(type,handler),
  removeEventListener:type=>handlers.delete(type)};
const control={dataset:{}};
const toggle={attributes:{},setAttribute(name,value){this.attributes[name]=value;}};
const cleanup=render({parentElement:{querySelectorAll:()=>[],querySelector:selector=>selector==='.theme-control'?control:toggle},
  data:{defaultTheme:'dark'},setStateValue:()=>assert.fail('Theme must stay client-side'),
  setTriggerValue:()=>assert.fail('Theme must not send server actions')});
assert.equal(root.dataset.traceTheme,'astral');
assert.equal(toggle.attributes['aria-checked'],'true');
toggle.onclick();
assert.equal(root.dataset.traceTheme,'dark');
assert.equal(stored.get('trace-theme'),'dark');
assert.equal(events.at(-1).detail,'dark');
cleanup();
assert.equal(handlers.size,0);
// An ordinary server rerender must preserve the browser selection.
render({parentElement:{querySelectorAll:()=>[],querySelector:selector=>selector==='.theme-control'?control:toggle},data:{defaultTheme:'astral'}});
assert.equal(root.dataset.traceTheme,'dark');
handlers.get('storage')({key:'trace-theme',newValue:'astral'});
assert.equal(root.dataset.traceTheme,'astral');
console.log(JSON.stringify({passed:true}));
