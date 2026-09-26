import {chromium} from 'playwright';
import path from 'node:path';import os from 'node:os';import fs from 'node:fs/promises';import {fileURLToPath} from 'node:url';import {spawn} from 'node:child_process';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const dir=await fs.mkdtemp(path.join(os.tmpdir(),'portfolio-tests-'));
const python=process.env.WEALTH_PYTHON||path.join(root,'.venv',process.platform==='win32'?'Scripts/python.exe':'bin/python');
const server=spawn(python,['-m','uvicorn','backend.main:app','--port','8000'],{cwd:root,env:{...process.env,DATABASE_URL:'sqlite:///'+path.join(dir,'db.sqlite').replaceAll('\\\\','/')},stdio:'ignore'});
let browser;let checks=[];let errors=[];
try{
 for(let i=0;i<50;i++){try{if((await fetch('http://127.0.0.1:8000/api/health')).ok)break}catch{}await new Promise(r=>setTimeout(r,200))}
 browser=await chromium.launch({headless:true,...(process.env.WEALTH_CHROMIUM?{executablePath:process.env.WEALTH_CHROMIUM,args:JSON.parse(process.env.WEALTH_CHROMIUM_ARGS||'[]')}:{})});
 const page=await browser.newPage({viewport:{width:1512,height:1050}});page.on('pageerror',e=>errors.push(e.message));
 page.on('console',m=>{if(m.type()==='error'&&!m.text().includes('Failed to load resource'))errors.push('console: '+m.text())});
 await page.goto('http://127.0.0.1:8000');await page.getByRole('button',{name:'Explore interactive demo'}).click();
 await page.getByRole('heading',{name:'Make room for possibility.'}).waitFor();

 // --- FIRE planner Monte Carlo stress test -------------------------------
 await page.getByRole('button',{name:'FIRE planner',exact:true}).click();
 await page.getByRole('heading',{name:'Your freedom, your timeline.'}).waitFor();
 await page.getByLabel('Monthly retirement spending',{exact:false}).fill('40000');
 await page.getByRole('heading',{name:'How likely is your plan to survive real markets?'}).waitFor();
 await page.getByText('Running simulations…').waitFor({state:'detached',timeout:15000});
 await page.getByText('Chance your money lasts to',{exact:false}).waitFor();checks.push('Monte Carlo panel renders with a live draft');

 const firstProb=(await page.locator('.mc-panel .metric').first().locator('strong').innerText()).trim();
 await page.getByLabel('Annual market volatility (%)').fill('30');
 await page.getByText('Running simulations…').waitFor({state:'detached',timeout:15000});
 await page.waitForFunction((old)=>{
   const el=document.querySelector('.mc-panel .metric strong');return el&&el.textContent.trim()!==old;
 },firstProb,{timeout:15000});
 checks.push('raising volatility changes the simulated outcome');

 const before=await (await page.request.get('http://127.0.0.1:8000/api/state')).json();
 if(JSON.stringify(before.state.fire)!=='{}'&&before.state.fire.monthly_spending===40000)throw Error('Monte Carlo draft leaked into saved state');
 checks.push('Monte Carlo runs on the unsaved draft only');

 await page.getByLabel('Plan until age').fill('60');
 await page.getByRole('alert').waitFor();checks.push('plan-until-age validation surfaces the backend error');
 await page.getByLabel('Plan until age').fill('90');
 await page.getByRole('alert').waitFor({state:'detached',timeout:15000});checks.push('stale error clears once input is corrected');
 const mcDetails=page.getByText('See the numbers behind the chart',{exact:true}).nth(1);
 await mcDetails.scrollIntoViewIfNeeded();await mcDetails.click();
 await page.getByRole('columnheader',{name:'Median',exact:true}).waitFor();checks.push('accessible percentile table');
 await page.evaluate(()=>window.scrollTo({top:0,behavior:'instant'}));
 await page.screenshot({path:root+'/docs/monte-carlo-preview.png',fullPage:true});

 // --- Duplicate-aware CSV import ------------------------------------------
 page.once('dialog',d=>d.accept());  // unsaved-FIRE-draft navigation guard
 await page.getByRole('button',{name:'My finances',exact:true}).click();
 await page.getByRole('button',{name:/^Expenses/}).click();
 const existing=await page.locator('.table-scroll tbody tr').first().locator('td').first().locator('strong').innerText();
 const state=(await (await page.request.get('http://127.0.0.1:8000/api/state')).json()).state;
 const existingAmount=state.expenses[0].amount;
 const csv=`Name,Amount\n${existing},${existingAmount}\nBrand new subscription,499`;
 await page.getByLabel('Choose CSV').setInputFiles({name:'import.csv',mimeType:'text/csv',buffer:Buffer.from(csv)});
 await page.getByText('possible duplicate',{exact:true}).waitFor();checks.push('duplicate row flagged in preview');
 await page.getByRole('button',{name:'Confirm import'}).click();
 await page.getByText('Brand new subscription',{exact:true}).waitFor();
 const after=await (await page.request.get('http://127.0.0.1:8000/api/state')).json();
 const matches=after.state.expenses.filter(e=>e.name===existing).length;
 if(matches!==1)throw Error(`Expected duplicate to be skipped, found ${matches} copies of "${existing}"`);
 checks.push('duplicate skipped by default, new row still imported');

 // --- ML research page: interval and feature importance --------------------
 await page.getByRole('button',{name:'ML research',exact:true}).click();
 await page.getByText('likely range',{exact:false}).waitFor();checks.push('prediction interval rendered');
 await page.getByRole('heading',{name:'What moves the estimate'}).waitFor();checks.push('feature importance rendered');

 await page.setViewportSize({width:390,height:844});
 await page.getByRole('button',{name:'Open navigation'}).click();
 await page.getByRole('button',{name:'FIRE planner',exact:true}).click();
 await page.getByRole('heading',{name:'How likely is your plan to survive real markets?'}).waitFor();
 await page.getByText('Running simulations…').waitFor({state:'detached',timeout:15000});
 if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1))throw Error('Mobile overflow on Monte Carlo panel');
 checks.push('mobile Monte Carlo layout');

 if(errors.length)throw Error(errors.join('\n'));
 await fs.writeFile(root+'/docs/montecarlo-test-results.json',JSON.stringify({status:'passed',checks,errors},null,2));
 console.log(JSON.stringify({status:'passed',checks},null,2));
}finally{await browser?.close();server.kill('SIGTERM')}
