from pathlib import Path
import json,html,shutil
P=Path(__file__).resolve().parent.parent
src=(P/'制作记录/build_step_guide.py').read_text(encoding='utf-8-sig')
ns={'__file__':str(P/'制作记录/build_step_guide.py')};exec(src.split('for s in steps:render(s)')[0],ns)
allsteps=ns['steps']; selected=[]
for s in allsteps:
 if s['code'] in ['A10','A11','A12','A13','A14']:
  old=s['code'];s['code']='M0'+str(int(old[1:])-9)
  s['actions']=[a.replace('A02已装','准备时已装').replace('A02已','准备时已') for a in s['actions']]
  if old=='A12':s['extra']='这颗细孔固定开关PCB；下一步两颗M3才固定整块后面板。'
  ns['render'](s);selected.append(s)
 elif s['code'].startswith(('B','R','Z')):selected.append(s)
for s in selected:s.setdefault('image','图解/'+s['code']+'.png')
# Better isolate moving joints: show the gap rather than hide the lower member.
for s in selected:
 if s['code']=='B02':
  s['marks']=[([x,y,17.4],'普通M3螺母：沿侧槽送入',[0,16 if y>0 else -16,0]) for x in (-29,29) for y in (-6,6)]; s['actions'][0]='拿B01底座，找到两根支柱侧面的水平螺母槽；每根柱的槽里放两颗普通M3螺母。'; s['alpha']={'B01':.55}; ns['render'](s)
 if s['code']=='R02':s['shift']={'R04':(0,0,12)};s['extra']='本图将连杆抬高12mm便于看孔；实际叠层之间只放2mm隔套。';ns['render'](s)
 if s['code']=='R03':s['shift']={'R05':(0,0,12)};s['extra']='本图将滑架抬高12mm便于看孔；实际连杆与滑架之间只放2mm隔套。';ns['render'](s)
 # Make step references unambiguous.
 if s['code']=='B05':s['hardware']='M3×14 半圆头螺钉 ×4；使用步骤B02已预放的4颗螺母'
 if s['code']=='B09':s['actions']=[a.replace('A01铜螺母','身体顶部预装铜螺母') for a in s['actions']]
(P/'制作记录/重点版数据.json').write_text(json.dumps(selected,ensure_ascii=False,indent=2),encoding='utf-8')
style='''*{box-sizing:border-box}body{margin:0;background:#edf1f5;color:#23354b;font-family:"Microsoft YaHei",sans-serif}header{padding:24px 4vw;background:#23354b;color:white}h1{font-size:26px;margin:0 0 8px}nav{position:sticky;top:0;background:white;z-index:4;padding:12px 4vw;display:flex;flex-wrap:wrap;gap:8px;box-shadow:0 2px 8px #0001}button,select{border:1px solid #c8d0da;border-radius:7px;background:white;padding:10px;font-size:15px;cursor:pointer}main{max-width:1230px;margin:20px auto;padding:0 16px}.intro,.step{padding:24px;background:white;border-radius:12px;margin:18px 0}.step{display:none}.step.current,body.all .step{display:block}img{width:100%;border:1px solid #e3e6ea;border-radius:7px}h2{font-size:24px;margin:0 0 14px}.hardware{background:#fff2d7;border-left:4px solid #d0a24c;padding:12px;line-height:1.7}ol{font-size:18px;line-height:1.9;padding-left:30px}li{margin:8px 0}.check{padding:14px;background:#e8f4ed;line-height:1.8}.note{padding:12px;background:#faf4e8;color:#755d33;font-size:15px;line-height:1.7}.bottom{display:flex;gap:12px;margin:20px 0 0}details{margin:12px 0}a{color:#1b729f}footer{padding:24px 4vw;line-height:1.8}@media print{nav,header,.intro,footer,.bottom{display:none}main{margin:0;padding:0}.step{display:block!important;break-after:page;padding:0;margin:0}img{max-height:43vh;object-fit:contain}ol{font-size:12px;line-height:1.5}.hardware,.check,.note{font-size:11px}h2{font-size:18px}@page{size:A4;margin:12mm}}'''
intro='''<div class="intro"><b>这版只讲新版主板与攻击模块。Otto腿脚沿用你已经熟悉的装法，不重复。</b><p>先做 M01–M05（主板/开关/电池），再选 B01–B10（蓝色巴掌）或 R01–R10（红色拳头），最后 Z01。每台共16个操作页。图片数字指孔位，黄色框列本步螺丝。</p><p><b>封装前必须准备：</b>身体顶部4颗、背面2颗M3热熔铜螺母；蓝机承重座另2颗，见B01。规格：长5.7mm、适配Ø4.0安装底孔。不是任意M3螺母都能代替。热装要在裸件上完成，先取出电子件并冷却后再安装。</p><details><summary>查看身体6颗铜螺母的位置（已装好可跳过）</summary><img src="图解/A01.png"><img src="图解/A02.png"></details><p>主板用外径2.5×8塑料自攻×4；开关用外径2.5×6塑料自攻×1；舵盘、输出轴使用各自原配螺丝，不能一律换M3。</p><p><a href="02_主板与攻击模块_逐页图解.pdf">下载逐页PDF</a> · <a href="五金总表_沿用v11.md">完整五金总表</a>。每张图都可以点开单独放大。</p><p>零件位置和孔位取自v11送印模型；图上配色用于辨认部件。新到舵机花键、实际螺丝长度和打印公差仍要试装；图示不代表实物已装配验证。</p></div>'''
e=html.escape
sections=[]
for s in selected:
 sections.append(f'<section class="step" id="{s["code"]}"><h2>{s["code"]}　{e(s["title"])}</h2><p class="hardware"><b>准备：</b>{e(s["hardware"])}</p><a href="{s["image"]}" target="_blank"><img src="{s["image"]}" alt="{e(s["title"])}"></a><ol>'+''.join('<li>'+e(a)+'</li>' for a in s['actions'])+'</ol><p class="check"><b>装完检查：</b>'+e(s['check'])+'</p>'+('<p class="note">'+e(s['extra'])+'</p>' if s['extra'] else '')+'<div class="bottom"><button onclick="move(-1)">← 上一步</button><button onclick="move(1)">下一步 →</button></div></section>')
opts=''.join(f'<option value="{i}">{s["code"]} {e(s["title"])}</option>' for i,s in enumerate(selected))
js='''const nodes=[...document.querySelectorAll('.step')];let idx=0;function show(i){idx=Math.max(0,Math.min(nodes.length-1,i));nodes.forEach((n,j)=>n.classList.toggle('current',j===idx));document.querySelector('#choose').value=idx;document.querySelector('#count').textContent=(idx+1)+' / '+nodes.length;history.replaceState(null,'','#'+nodes[idx].id)}function move(d){show(idx+d);document.querySelector('.step.current').scrollIntoView({behavior:'smooth',block:'start'})}function jump(id){show(nodes.findIndex(n=>n.id===id));document.querySelector('.step.current').scrollIntoView({behavior:'smooth',block:'start'})}document.querySelector('#choose').onchange=e=>show(+e.target.value);document.querySelector('#all').onclick=()=>document.body.classList.toggle('all');document.addEventListener('keydown',e=>{if(e.target.tagName==='SELECT')return;if(e.key==='ArrowRight')move(1);if(e.key==='ArrowLeft')move(-1)});show(Math.max(0,nodes.findIndex(n=>'#'+n.id===location.hash)));'''
page='<!doctype html><html lang="zh-CN"><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>主板与攻击模块 · 逐步装配</title><style>'+style+'.step{scroll-margin-top:110px}</style><header><h1>主板与攻击模块 · 逐步装配</h1><p>milk ARENA / v11送印件 / 2026-11-12　每一步都标孔、标螺丝、标顺序</p></header><nav><button onclick="jump(\'M01\')">主板与开关</button><button onclick="jump(\'B01\')">蓝色巴掌</button><button onclick="jump(\'R01\')">红色拳头</button><button onclick="jump(\'Z01\')">装完检查</button><select id="choose">'+opts+'</select><button id="all">展开/收起全部</button><span id="count"></span></nav><main>'+intro+''.join(sections)+'</main><footer>制作依据：v11送印装配清单、修正C02托架、v10/v11孔位定义及已有五金表。<br>保持原模型和旧教程不变；本版不上传代码、不操作机器人。</footer><script>'+js+'</script></html>'
# Preserve previously generated expanded guide only as an optional reference.
old=P/'00_逐步装配图解.html'
if old.exists():shutil.copy2(old,P/'制作记录/含Otto腿部步骤_历史展开版.html')
old.write_text(page,encoding='utf-8')
md=['# 主板与攻击模块逐步装配','按M01–M05→蓝B/红R→Z01进行。身体铜螺母预装位置见图解A01、A02。']
for s in selected:
 md+=['','## '+s['code']+' '+s['title'],'','准备：'+s['hardware'],'','![步骤图]('+s['image']+')','']+[f'{i+1}. {a}' for i,a in enumerate(s['actions'])]+['','装完检查：'+s['check'],s['extra']]
(P/'01_逐步装配文字版.md').write_text('\n'.join(md),encoding='utf-8')
print('FOCUS READY',len(selected))


