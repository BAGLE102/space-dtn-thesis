const {chromium}=require(process.argv[2]);
const {pathToFileURL}=require('url');
const fs=require('fs');
(async()=>{
 const browser=await chromium.launch({headless:true,...(process.argv[5]?{executablePath:process.argv[5]}:{})});
 const page=await browser.newPage({viewport:{width:800,height:1050}});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto(pathToFileURL(process.argv[3]).href);
 const frame=page.frameLocator('iframe');
 await frame.locator('[data-role="queue"] tr').first().waitFor();
 const checks=await frame.locator('#dtn-process-view').evaluate(root=>{
   const $=n=>root.querySelector(`[data-role="${n}"]`);
   const data=JSON.parse(document.getElementById('dtn-process-data').textContent);
   let checked=0;
   for(let ci=0;ci<data.length;ci++){
     $('case').value=String(ci);$('case').dispatchEvent(new Event('change'));
     for(let bi=0;bi<data[ci].records.length;bi++){
       $('bundle').value=String(bi);$('bundle').dispatchEvent(new Event('change'));
       const count=Number($('slider').max)+1;
       for(let s=0;s<count;s++){
         $('slider').value=String(s);$('slider').dispatchEvent(new Event('input'));
         if(/NaN|undefined/.test($('graph').innerHTML+$('status').textContent+$('queue').textContent))throw Error('Invalid visual values');
         if(!$('status').textContent)throw Error('Missing explanation');
         const trace=data[ci].records[bi].trace;
         const init=data[ci].records[bi].labels.L0?1:0;
         const event=s<init?{queue_after:['L0']}:trace[s-init];
         const ids=(event.queue_after||[]);
         const rows=$('queue').querySelectorAll('tr');
         if(rows.length!==Math.max(1,ids.length))throw Error('Queue row mismatch');
         checked++;
       }
     }
   }
   $('case').value='0';$('case').dispatchEvent(new Event('change'));
   $('bundle').value='1';$('bundle').dispatchEvent(new Event('change'));
   $('mode').value='schedule';$('mode').dispatchEvent(new Event('change'));
   $('slider').value='8';$('slider').dispatchEvent(new Event('input'));
   const buffers=$('buffers').textContent;
   if(!buffers.includes('B：4 / 4 MB')||!buffers.includes('D：4 / 4 MB'))throw Error('Schedule event peaks mismatch');
   $('slider').value='8.25';$('slider').dispatchEvent(new Event('input'));
   if(!$('buffers').textContent.includes('D：0 / 4 MB'))throw Error('Delivery release mismatch');
   $('mode').value='search';$('mode').dispatchEvent(new Event('change'));
   const trace=data[0].records[1].trace;
   const failure=trace.findIndex(e=>e.reason==='BUFFER')+1;
   $('slider').value=String(failure);$('slider').dispatchEvent(new Event('input'));
   if(!$('status').textContent.includes('Buffer 超限'))throw Error('Buffer failure not displayed');
   return {cases:data.length,queries:data.reduce((s,c)=>s+c.records.length,0),steps_checked:checked,buffer_event_peak_checked:true};
 });
 await page.waitForTimeout(500);
 await page.screenshot({path:process.argv[4]+'/process_search.png',fullPage:true});
 await frame.locator('[data-role="next"]').click();
 await frame.locator('[data-role="prev"]').click();
 await frame.locator('[data-role="play"]').click();
 await page.waitForTimeout(1400);
 await frame.locator('[data-role="play"]').click();
 await frame.locator('[data-role="mode"]').selectOption('schedule');
 await frame.locator('[data-role="slider"]').fill('7.5');
 await frame.locator('[data-role="slider"]').dispatchEvent('input');
 await page.waitForTimeout(500);
 await page.screenshot({path:process.argv[4]+'/process_schedule.png',fullPage:true});
 await page.setViewportSize({width:320,height:1100});
 await page.waitForTimeout(150);
 const narrow=await frame.locator('#dtn-process-view').evaluate(root=>({width:root.clientWidth,scroll:root.scrollWidth}));
 if(narrow.scroll>narrow.width+2)throw Error('Mobile horizontal overflow');
 await page.screenshot({path:process.argv[4]+'/process_mobile.png',fullPage:true});
 if(errors.length)throw Error(errors.join('\n'));
 fs.writeFileSync(process.argv[4]+'/browser_checks.json',JSON.stringify({...checks,javascript_errors:errors,mobile_width:narrow,playback_controls_checked:true},null,2)+'\n');
 console.log(JSON.stringify(checks));await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
