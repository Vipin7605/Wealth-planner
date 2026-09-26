import {chromium} from 'playwright';
import path from 'node:path';import os from 'node:os';import fs from 'node:fs/promises';import {fileURLToPath} from 'node:url';import {spawn} from 'node:child_process';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const dir=await fs.mkdtemp(path.join(os.tmpdir(),'portfolio-tests-'));
const python=process.env.WEALTH_PYTHON||path.join(root,'.venv',process.platform==='win32'?'Scripts/python.exe':'bin/python');
const server=spawn(python,['-m','uvicorn','backend.main:app','--port','8000'],{cwd:root,env:{...process.env,DATABASE_URL:'sqlite:///'+path.join(dir,'db.sqlite').replaceAll('\\','/')},stdio:'ignore'});
let browser;let checks=[];let errors=[];
try{
 for(let i=0;i<50;i++){try{if((await fetch('http://127.0.0.1:8000/api/health')).ok)break}catch{}await new Promise(r=>setTimeout(r,200))}
 browser=await chromium.launch({headless:true,...(process.env.WEALTH_CHROMIUM?{executablePath:process.env.WEALTH_CHROMIUM,args:JSON.parse(process.env.WEALTH_CHROMIUM_ARGS||'[]')}:{})});
 const page=await browser.newPage({viewport:{width:1512,height:1050}});page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://127.0.0.1:8000');await page.getByRole('button',{name:'Explore interactive demo'}).click();
 await page.getByRole('heading',{name:'Make room for possibility.'}).waitFor();checks.push('restored Overview rendered');
 await page.screenshot({path:root+'/docs/dashboard-preview.png',fullPage:true});
 await page.getByRole('button',{name:'Financial health',exact:true}).click();
 await page.getByRole('button',{name:'Update my details'}).click();
 await page.getByLabel('Marital status',{exact:true}).selectOption('married');
 await page.getByLabel('Active health insurance',{exact:true}).selectOption('yes');await page.getByLabel('Health cover (₹)',{exact:true}).fill('500000');

 await page.getByRole('button',{name:'Save financial profile'}).click();await page.getByRole('heading',{name:'Make room for possibility.'}).waitFor();
 const data=await (await page.request.get('http://127.0.0.1:8000/api/export')).json();
 if(data.state.profile.marital_status!=='married')throw Error('saved health plan mismatch');checks.push('personal protection saved and exported');
 await page.reload();await page.getByRole('heading',{name:'Make room for possibility.'}).waitFor();checks.push('persisted dashboard reload');
 await page.getByRole('button',{name:'My finances',exact:true}).click();await page.getByRole('button',{name:/^Expenses /}).click();await page.getByRole('button',{name:'Maid · Need',exact:true}).click();await page.getByLabel('Monthly amount (₹)',{exact:true}).fill('2000');await page.getByRole('button',{name:'Save record'}).click();await page.getByRole('dialog').waitFor({state:'detached'});checks.push('needs template expense entry');
 await page.getByRole('button',{name:'Reports',exact:true}).click();await page.getByRole('heading',{name:'SWOT & recommended actions'}).waitFor();checks.push('report includes FIRE SWOT actions');
 await page.getByRole('button',{name:'Financial health',exact:true}).click();
 await page.setViewportSize({width:390,height:844});
 await page.waitForFunction(()=>document.querySelector('.sidebar').getBoundingClientRect().right<=1);
 if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1))throw Error('Mobile overflow '+JSON.stringify(await page.evaluate(()=>[...document.querySelectorAll('body *')].filter(e=>e.getBoundingClientRect().right>innerWidth+2).slice(0,15).map(e=>({tag:e.tagName,cls:e.className,right:e.getBoundingClientRect().right})))));
 await page.screenshot({path:root+'/docs/financial-health-mobile.png',fullPage:true});checks.push('mobile health layout');
 if(errors.length)throw Error(errors.join('\n'));
 await fs.writeFile(root+'/docs/health-test-results.json',JSON.stringify({status:'passed',checks,errors},null,2));console.log(JSON.stringify({status:'passed',checks},null,2));
}finally{await browser?.close();server.kill('SIGTERM')}
