import {test,expect} from '@playwright/test';
for(const width of [390,768,1440]) for(const theme of ['light','dark']) {
 test(`workload and evidence views ${width} ${theme}`,async({page})=>{
  await page.setViewportSize({width,height:1000});
  await page.addInitScript(theme=>localStorage.setItem('scaleproof-theme',theme),theme);
  await page.goto('');
  await expect(page.getByRole('heading',{name:'Capacity, accounted for.'})).toBeVisible();
  await page.getByRole('button',{name:'Preview policy'}).click();
  await expect(page.getByText('Within bounds',{exact:true})).toBeVisible();
  await expect(page.getByText('3,840',{exact:true})).toBeVisible();
  await page.getByRole('spinbutton',{name:'High arrival rate',exact:true}).fill('101');
  await page.getByRole('button',{name:'Preview policy'}).click();
  await expect(page.getByText('Needs a change',{exact:true})).toBeVisible();
  await page.reload();
  await expect(page.getByRole('spinbutton',{name:'High arrival rate',exact:true})).toHaveValue('101');
  for(const name of ['Capacity','Requests','Method']){await page.getByRole('button',{name:new RegExp(name+'$')}).click();await expect(page.locator('h2')).toBeVisible();expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy()}
  await page.emulateMedia({reducedMotion:'reduce'});
  await page.keyboard.press('Tab');
  expect(await page.evaluate(()=>document.activeElement?.tagName)).not.toBe('BODY');
 });
}
test('missing evidence has an explicit recovery state',async({page})=>{await page.route('**/evidence.json',r=>r.abort());await page.goto('');await expect(page.getByRole('alert')).toContainText('Evidence could not be loaded');await page.getByRole('button',{name:'Preview policy'}).click();await expect(page.getByText('Within bounds',{exact:true})).toBeVisible()});
test('200 percent layout remains bounded',async({page})=>{await page.setViewportSize({width:1440,height:1000});await page.goto('');await page.evaluate(()=>{document.body.style.zoom='2'});expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();await page.getByRole('button',{name:'Preview policy'}).click();await expect(page.getByText('Within bounds',{exact:true})).toBeVisible()});
