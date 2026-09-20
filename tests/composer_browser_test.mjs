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
// A server acknowledgement can arrive after the user has typed more text.
elements.question.value='Newest unsent text';elements.question.oninput();
component.data.question='Older server acknowledgement';render(component);
assert.equal(elements.question.value,'Newest unsent text');
// A running investigation blocks another submit, but the next draft stays editable.
component.data.disabled=true;render(component);assert.equal(elements.question.disabled,false);assert.equal(elements.attach.disabled,false);assert.equal(elements.submit.disabled,true);
// A fresh draft generation really does clear old files and text.
component.data={...component.data,generation:'two',question:'',files:[],disabled:false};render(component);
assert.equal(elements.question.value,'');assert.equal(elements.attachments.children.length,0);
elements.composer.onsubmit({preventDefault(){}});assert.match(elements['composer-error'].textContent,/Enter a scientific question/);
elements.question.value='A valid question';elements.question.oninput();assert.equal(elements['composer-error'].textContent,'');
// A failed bridge dispatch leaves the draft usable, rather than stuck in Preparing.
elements.question.value='Retry my question';elements.question.oninput();
const failing={...component,setTriggerValue:()=>{throw new Error('Disconnected');}};render(failing);
elements.composer.onsubmit({preventDefault(){}});
assert.match(elements['composer-error'].textContent,/connection was interrupted/);assert.equal(elements.submit.disabled,false);
console.log('Late acknowledgements, active-run draft editing, fresh draft reset and connection failure recovery passed.');
