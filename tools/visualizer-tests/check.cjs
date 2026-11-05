const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),assert=require('node:assert/strict');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const site=path.resolve(__dirname,'../../docs'),prefix='/open-music-led-diffuser/';
const server=http.createServer((req,res)=>{
 const pathname=new URL(req.url,'http://localhost').pathname;
 if(!pathname.startsWith(prefix)){res.writeHead(404).end();return;}
 const relative=decodeURIComponent(pathname.slice(prefix.length))||'index.html',file=path.resolve(site,relative);
 if(!file.startsWith(site+path.sep)||!fs.existsSync(file)||!fs.statSync(file).isFile()){res.writeHead(404).end();return;}
 res.writeHead(200,{'Content-Length':fs.statSync(file).size,'Content-Type':{'.html':'text/html; charset=utf-8','.js':'text/javascript','.json':'application/json','.bin':'application/octet-stream'}[path.extname(file)]||'text/plain'});fs.createReadStream(file).pipe(res);
});
(async()=>{await new Promise(r=>server.listen(0,'127.0.0.1',r));const url=`http://127.0.0.1:${server.address().port}${prefix}`;
 const browser=await chromium.launch({...(process.env.CHROME_PATH?{executablePath:process.env.CHROME_PATH}:{}),headless:true,args:['--no-sandbox','--disable-dev-shm-usage','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 try{
  const page=await browser.newPage({viewport:{width:1500,height:1100}}),errors=[],failed=[];
  page.on('pageerror',e=>errors.push(String(e)));page.on('response',r=>{if(r.status()>=400)failed.push(`${r.status()} ${r.url()}`);});
  await page.goto(url,{timeout:60000});
  for(const n of [52,56,64]){
   await page.selectOption('#layout',String(n));
   await page.waitForFunction(n=>singleStencil.state().ready&&singleStencil.state().layout===String(n)&&singleStencil.state().layer===67&&document.querySelector('#flat').contentDocument.querySelector('h1')?.textContent.startsWith(String(n)),n,{timeout:180000});
   const f=page.frameLocator('#flat');
   await f.locator('body').evaluate(()=>layerInspector.setLayer(63));
   await page.selectOption('#x','9');await page.waitForFunction(()=>document.querySelector('#flat').contentWindow.layerInspector.state().variant==='x9');
   const a=await f.locator('#material').getAttribute('d');
   await page.selectOption('#x','6');await page.waitForFunction(()=>document.querySelector('#flat').contentWindow.layerInspector.state().variant==='x6');
   assert(a!==await f.locator('#material').getAttribute('d'),'X6 and X9 must differ at layer 63');
   await page.click('#three');
   await page.waitForFunction(n=>singleStencil.state().ready&&document.querySelector('#solid').contentWindow.geometryInspector?.state()?.layer===63&&document.querySelector('#solid').contentDocument.querySelector('h1')?.textContent.includes(`${n} LEDs`),n,{timeout:180000});
   const solid=page.frameLocator('#solid');assert.match(await solid.locator('#status').innerText(),/divided channels/);
   await page.selectOption('#x','9');await page.waitForFunction(()=>document.querySelector('#solid').contentDocument.querySelector('#status').textContent.includes('bulk only'));
   await solid.locator('body').evaluate(()=>{geometryInspector.setView('body','slab');geometryInspector.setLayer(3);});
   assert.equal((await solid.locator('body').evaluate(()=>geometryInspector.state())).part,'body');
   await solid.locator('body').evaluate(()=>{geometryInspector.setView('print','below');geometryInspector.setLayer(67);});
   await page.click('#two');await page.waitForFunction(()=>document.querySelector('#flat').contentWindow.layerInspector.state().layer===67);
   console.log(`${n}: relative assets, 2D/3D, X6/X9, body and mating face pass`);
  }
  await page.setViewportSize({width:390,height:900});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  assert(await page.frameLocator('#flat').locator('body').evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  assert.deepEqual(errors,[]);assert.deepEqual(failed,[]);
  const broken=await browser.newPage();await broken.route('**/assets/52-2d.bin',route=>route.fulfill({status:503,body:'Unavailable'}));
  await broken.goto(url);await broken.waitForFunction(()=>document.querySelector('#flat').contentDocument.querySelector('#error')?.textContent.includes('Geometry download failed'),undefined,{timeout:60000});
  await broken.close();console.log('PASS: mobile layout and visible asset-error handling');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;}).finally(()=>server.close());
