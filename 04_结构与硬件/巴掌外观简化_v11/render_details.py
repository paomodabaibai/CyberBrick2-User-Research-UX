from pathlib import Path
P=Path(__file__).resolve().parent
exec((P/'render_v11.py').read_text(encoding='utf-8').split('# Full robot views.')[0])
saved=items[:];savedm=meshes.copy()
items=[o for o in saved if o['name'].startswith(('12_','10_','13_','14'))]
im,ren,win=render('palm','whole',(-155,-180,130),(0,0,18),54)
d=ImageDraw.Draw(im);d.text((35,25),'v11 圆肩罩：固定螺丝留在罩外',font=font(30),fill='#243746')
label(im,ren,(-30,-30,3),(40,760),'四角整体内收，不再穿透盖子开大口')
label(im,ren,(-27,-15,37),(45,200),'盖子自身两颗固定螺丝保留')
d.text((35,995),'图中金色为承重座／压环，功能固定结构保留；需实物试装。',font=font(20),fill='#7b633d')
im.save(P/'预览/盖子避孔_细节.png');win.Finalize()
items=[o for o in saved if o['name'].startswith(('15_','P_04'))]
hn=next(o['name'] for o in items if o['name'].startswith('P_04'))
meshes[hn]=meshes[hn].copy();meshes[hn].apply_translation([25,0,0])
im,ren,win=render('palm','whole',(160,-230,180),(65,0,45),75)
d=ImageDraw.Draw(im);d.text((35,25),'腕部简化：一体接杆 + 独立手掌',font=font(30),fill='#243746')
label(im,ren,(38,0,46),(40,200),'双筋填实，顶面与边缘圆滑处理')
label(im,ren,(68,0,46),(40,800),'插芯与转盘、接杆一体打印')
label(im,ren,(92,0,46),(800,800),'手掌向内套入，再胶粘固定')
d.text((35,995),'拆开25mm仅作说明；取消腕部横销与小螺丝，中心舵盘螺丝仍须保留。',font=font(19),fill='#7b633d')
im.save(P/'预览/一体胶粘腕杆_装配示意.png');win.Finalize()
print('DETAILS_COMPLETE')
