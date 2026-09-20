import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
const source = await readFile(new URL('../frontend/static/theme.js', import.meta.url), 'utf8');
const {installHelpDismissal} = await import(`data:text/javascript;base64,${Buffer.from(source).toString('base64')}`);
const handlers = new Map();
const anchor = {dataset:{}, matches:()=>true, contains:target=>target===button || target===tip};
const button = {closest:()=>anchor};
const tip = {closest:()=>anchor};
const dormant = {dataset:{}, matches:()=>false};
const local = {dataset:{}, matches:()=>true};
const document = {querySelectorAll:()=>[anchor,dormant],
  addEventListener:(type,handler)=>handlers.set(type,handler),
  removeEventListener:(type,handler)=>{assert.equal(handlers.get(type),handler);handlers.delete(type);}};
const cleanup = installHelpDismissal(document,{querySelectorAll:()=>[local]});
handlers.get('keydown')({key:'Escape'});
assert.equal(anchor.dataset.helpDismissed,'true');
assert.equal(local.dataset.helpDismissed,'true');
assert.equal(dormant.dataset.helpDismissed,undefined);
// Moving within one tooltip must not undo Escape dismissal.
handlers.get('pointerover')({target:tip, relatedTarget:button});
assert.equal(anchor.dataset.helpDismissed,'true');
// A genuinely new visit restores help, without blurring or submitting anything.
handlers.get('pointerover')({composedPath:()=>[button], relatedTarget:null});
assert.equal(anchor.dataset.helpDismissed,undefined);
handlers.get('keydown')({key:'Escape'});
handlers.get('focusin')({target:button, relatedTarget:null});
assert.equal(anchor.dataset.helpDismissed,undefined);
cleanup();
assert.equal(handlers.size,0);
console.log(JSON.stringify({passed:true}));
