// DOM-free contract test of the real browser component's file-drop and submit path.
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
const source=await readFile(new URL('../frontend/static/composer.js',import.meta.url),'utf8');
const {default:render}=await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));
class Element {
 constructor(){this.children=[];this.value='';this.files=[];this.dataset={};this.style={setProperty:(name,value)=>{this.style[name]=value;}};this.classList={add:()=>{},remove:()=>{}};}
 replaceChildren(){this.children=[];} appendChild(x){this.children.push(x);} setAttribute(k,v){this[k]=v;} contains(){return false;} focus(){} click(){}
}
globalThis.document={createElement:()=>new Element()};
globalThis.FileReader=class{readAsDataURL(file){this.result='data:text/csv;base64,'+Buffer.from(file.contents).toString('base64');queueMicrotask(()=>this.onload());}};
const elements=Object.fromEntries(['composer-wrap','composer','question','files','submit','attach','demo','composer-error','attachments','drop-hint','source-note'].map(x=>[x,new Element()]));
let draft,action;
const component={parentElement:{querySelector:q=>elements[q.slice(1)]},key:'test',data:{generation:'one',question:'Test question',files:[],extensions:['csv'],readOnly:false,disabled:false},setStateValue:(k,v)=>draft=v,setTriggerValue:(k,v)=>action=v};
render(component);
let prevented=false;
elements.composer.ondrop({preventDefault(){prevented=true;},dataTransfer:{files:[{name:'measurement.csv',size:4,contents:'a,b\n'}]}});
await new Promise(resolve=>setTimeout(resolve,0));
assert.ok(prevented);assert.equal(draft.files[0].name,'measurement.csv');assert.equal(Buffer.from(draft.files[0].data,'base64').toString(),'a,b\n');
assert.equal(elements.attachments.children.length,1);
component.data.theme='dark';component.data.colors={surface:'#192c36',text:'#e2edf1'};render(component);
assert.equal(elements['composer-wrap'].style['--ui-surface'],'#192c36');assert.equal(elements.question.value,'Test question');assert.equal(elements.attachments.children.length,1);
elements.composer.onsubmit({preventDefault(){}});
assert.equal(action.type,'start');assert.equal(action.question,'Test question');assert.equal(action.generation,'one');assert.equal(action.files.length,1);
elements.attachments.children[0].children[2].onclick();assert.equal(draft.files.length,0);
elements.composer.ondrop({preventDefault(){},dataTransfer:{files:[{name:'wrong.exe',size:2,contents:'xx'}]}});
assert.match(elements['composer-error'].textContent,/Supported formats/);
console.log('Composer drag/drop, exact attachment bytes, removal, invalid type and explicit submit passed.');
