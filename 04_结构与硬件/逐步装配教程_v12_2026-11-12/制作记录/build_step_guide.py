from pathlib import Path
import json, math, html, shutil, textwrap, sys
import numpy as np, trimesh, vtk
from vtk.util.numpy_support import numpy_to_vtk,numpy_to_vtkIdTypeArray,vtk_to_numpy
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(r'E:\课程作业\大三上\张茫 用户研究与体验设计')
H=ROOT/'04_结构与硬件'; OUT=H/'逐步装配教程_v12_2026-11-12'; IMG=OUT/'图解'
SRC=H/'巴掌外观简化_v11'; PACK=H/'双机打印装配包_v11_2026-10-29'
items=json.loads((SRC/'装配清单.json').read_text(encoding='utf-8'))
lookup={o['name']:o for o in items}; mapping=json.loads((PACK/'制作记录/装配图对应.json').read_text(encoding='utf-8'))
ids={o['id']:o['source_name'] for o in mapping}; names={o['id']:o['name'] for o in mapping}
ids.update(board='R01_竖置原厂接收组合',battery='R02_前置立放电池',switch='R03_后置开关_v08模块',servo='R10_巴掌舵机PG002外形参考',horn='R11_原配舵盘_只传扭矩',rodL='F_guide_rod_-20',rodR='F_guide_rod_+20')
for o in items:
 if o['name'].startswith('F_ref'):ids[o['name']]=o['name']
REFS=[k for k in ids if k.startswith('F_ref')]
font=lambda n:ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',n)
cache={}; steps=[]
def load(k):
 if k not in cache:
  name=ids[k]; path=SRC/'装配网格'/lookup[name]['file']
  if k=='C02':path=PACK/'制作记录/主板托架_装配坐标.stl'
  cache[k]=trimesh.load_mesh(path,process=False)
 return cache[k]
def step(code,title,hardware,actions,check,parts=None,marks=None,view=(-1,-1,1),extra='',official=None,stack=None,shift=None,alpha=None):
 s=dict(code=code,title=title,hardware=hardware,actions=actions,check=check,parts=parts or [],marks=marks or [],view=view,extra=extra,official=official,stack=stack,shift=shift or {},alpha=alpha or {})
 steps.append(s);return s
TOP=[(x,y,0) for x in (-30,30) for y in (-30,30)]
CAP=[(5.34+28.2*math.cos(math.radians(a)),28.2*math.sin(math.radians(a)),38.4) for a in (45,135,225,315)]
ST=[(x,y,29.8) for x in (-29,29) for y in (-6,6)]
def marks(points,label,vec=(0,0,15)):return [(list(p),label,list(vec)) for p in points]
step('A01','先在裸身体顶部装 4 颗铜螺母','M3 热熔铜螺母 ×4（长5.7mm，适配Ø4.0底孔）',[
'拿 C01 身体，眼睛一侧是正面，开关/USB 一侧是背面。图中圈出顶部四角孔。',
'身体里暂时不放主板、电池或舵机。先试装一颗匹配底孔的铜螺母，用热压工具垂直压入，顶面齐平。',
'其余三孔同样处理，冷却后再用 M3 螺钉轻试牙；本步不把螺钉留在孔内。'],'四颗平直、齐平；孔柱未开裂、未歪斜。',['C01'],marks(TOP,'铜螺母：由上向下热装'),extra='不是把 M3 螺丝硬拧进塑料。不同外径的 M3 铜螺母不能直接混用。')
step('A02','翻到背面，再装 2 颗铜螺母','同规格 M3 热熔铜螺母 ×2',[
'找到背面开关开口两侧的两个安装柱，位置在图中 1、2。','从身体后方水平热压入，等完全冷却。','这两颗以后接 A12 的开关面板螺丝；不要装进中间开关的细小孔。'],'身体共装了 6 颗铜螺母：上面4颗、后面2颗。',['C01'],marks([(-41.5,y,-28.5) for y in (-33.5,2.5)],'后面板铜螺母：后→前',(-18,0,0)),view=(-1,-.35,.6))
step('A03','四只腿部舵机先电气归中','180°位置舵机 ×4；本步不拧舵盘螺丝',[
'分别贴标签：S1 左髋、S2 左踝、S3 右髋、S4 右踝。左右按机器人自身看，面对机器人时会镜像。','使用项目现有“保持90°”程序，先在机械未连接时确认四只输出轴都归中。连续旋转舵机不能放在这四个位置。','归中后不要用手强扭输出轴。以下装舵盘/腿脚时保持中位；电子装入、插拔线时断开电源。'],'确认四只是180°定位型，且逐只实际到中位，再继续。',['C01','C04','C05','C06','C07'],view=(1,-1,.4),extra='本教程不会自动上传或运行程序。SG90/PG001若外壳或花键不同，必须先试配，不可硬压。')
step('A04','两只髋舵机装入身体','原配舵机安装自攻小螺丝 ×4（每只2颗）',[
'从身体敞开的顶部放入 S1、S3 两只髋舵机，输出轴穿出身体底部对应孔。','把两个安装耳贴平原有支座；从身体内部向下拧入每只两颗安装小螺丝。','线留在身体里并向侧壁整理，暂不装主板托架，给螺丝刀留空间。'],'两只舵机外壳固定、没有压线，输出轴仍处90°。',official=[4],extra='图为 Otto V9 官方原版安装位置。只沿用腿部安装关系，图中旧身体外壳与本版顶部布局不同。原配小螺丝不是 M3。')
step('A05','把髋舵盘放进两个短腿','髋舵盘 ×2；本步先不拧中心螺丝',[
'拿 C04/C05 短腿，找到下方圆弧窗口旁的舵盘卡位。','先用自己的舵盘干试；按官方图把舵盘从窗口送进卡槽，花键中心对准通孔。','只有原配长臂确实超出槽位时才修去多余端部；不要照图盲剪不同型号的舵盘。'],'舵盘坐进槽内，中心孔可从短腿内部接近。',official=[5])
step('A06','短腿对正，再锁住髋舵盘中心','原配舵盘中心螺丝 ×2（每边1颗）',[
'将身体倒放在软垫上，按图把两条短腿压到已归中的髋输出轴；短腿相互平行、左右镜像。','先轻压花键试位；若腿歪，抬起重新对齿，不能靠拧螺丝把歪腿拉正。','从短腿内腔沿输出轴方向拧入原配中心螺丝；两边各1颗。'],'两腿中立位置一致，中心螺丝已锁住舵盘但未滑牙。',official=[6,7],extra='官方图中 180° 箭头表示机械行程参考，不是要求本步通电扫到端点。')
step('A07','两只踝舵机配好舵盘，放进脚板','S2/S4 舵机 ×2；对应原配舵盘及中心小螺丝',[
'让踝舵机保持90°，按官方图给舵盘对中；舵盘方向以脚板槽位和两脚平放姿态为准。','将带舵盘的舵机放进 C06/C07 脚板的两侧立耳之间，舵盘一侧对准带孔的立耳。','先确认舵盘能完全入槽，中心螺丝可沿同轴大孔接近，再固定中心；不要把安装耳用的尖头螺丝拧入输出轴。'],'两只脚部组件成镜像；踝轴安装后可以通过侧孔维护。',official=[8,9])
step('A08','从脚板侧面固定踝舵盘','原配适配舵盘的自攻小螺丝 ×4（每脚2颗）',[
'脚板有舵盘的侧面能看到两只较小固定孔，按官方箭头各拧入1颗小螺丝。','两颗小螺丝穿脚板进入塑料舵盘小孔；中间大孔是轴心/工具通道，不要误当这两颗安装孔。','另一只脚重复。适度拧紧，以脚板与舵盘不松为准，不拧裂薄立耳。'],'每只脚两颗侧面固定螺丝就位，舵盘不会在槽里晃。',official=[10],extra='这里的螺钉以实际舵盘匹配的原配小自攻为准，不是 M3机牙螺丝。')
step('A09','脚部插入短腿，先把线穿进去','不新增 M3 螺丝',[
'按图先将踝舵机线穿过短腿，再穿过身体底部的走线口。','把脚部组件的舵机外壳插入短腿矩形套口，逐边压到位，不用导线拉拽。','将身体翻正；检查脚尖方向一致、双脚平放。走线留出腿转动的余量，再按 S1/S2/S3/S4 整理标签。'],'两腿垂直、脚底平齐、线不绕轴、不夹在短腿套口。',official=[11,12,13],extra='V9 这里主要靠原配套口配合。若新舵机外壳插不稳，先核对尺寸；不要任意钻孔穿过舵机。')
step('A10','在桌上先把主板固定到托架','外径2.5×8mm塑料自攻螺丝 ×4',[
'拿 C02 托架和接收主板组合，四个板孔与四根托柱对齐。USB 插口最终朝身体后面的开口。','从电路板一侧穿过板孔，向塑料托柱拧入4颗自攻；先四颗轻带上，再交替贴紧。','螺丝头不能压电路元件，板不能被拧弯。本包托架是Ø2.1底孔版本。'],'四角固定平整；USB插头可插拔。',['C02','board'],marks([(x,3.35,z) for x in (-29,-5) for z in (-29.5,-6.5)],'2.5×8 自攻：穿板→托柱',(0,-15,0)),view=(-.5,-1,.45),extra='不是 M2.5 机牙螺丝，也不是 M3。本图使用送印包内修正过的 C02。')
step('A11','主板托架落进身体定位柱','本步不加螺丝',[
'从身体顶部放入主板+托架，托架底部两孔套到身体内两根定位销。','确认两只脚都落到底，USB朝后，线束从侧面空隙经过。','上方攻击模块装好后会限制托架上抬；此刻不要强行给底脚另打螺丝。'],'托架坐到底，不挤髋舵机，不堵后方USB口。',['C01','C02','board'],marks([(-22,14,-31.5),(0,14,-31.5)],'托架脚套定位销；不拧螺丝',(0,0,16)),view=(-1,-1,1),alpha={'C01':.2},shift={'C02':(0,0,15),'board':(0,0,15)},extra='图中托架抬高15mm显示安装路径；装完必须落到底。')
step('A12','开关先拧在后面板上','外径2.5×6mm塑料自攻螺丝 ×1',[
'在桌上拿 C03 面板与 XA007 开关，把拨杆放进面板上端敞开的U形槽。','开关PCB下方安装耳贴住面板内侧圆支柱；从PCB一侧拧1颗2.5×6自攻进支柱。','按实际输入/输出标识先插好两端电源线，再把开关来回拨到底检查；不可夹住拨杆。'],'开关不晃、拨动顺畅，两端插头完全插入。',['C03','switch'],marks([(-34.22,-15,-27.25)],'2.5×6 自攻：PCB→面板柱',(15,0,0)),view=(1,-.45,.55),extra='这颗细孔固定开关PCB；下一步的两颗M3才是固定整块后面板。')
step('A13','整块后面板从背后锁到身体','M3×8 半圆头螺钉 ×2',[
'将开关线先送入身体内部，把C03贴到身体后方对应面。','从身体外后方，把两颗M3×8穿过面板左右孔，拧入A02已装的铜螺母。','两颗交替拧到贴合即可，不能靠螺丝挤压夹在缝里的导线。'],'后面板贴平，开关到底仍不卡，线没有夹在板缝。',['C01','C03','switch'],marks([(-43.9,y,-28.5) for y in (-33.5,2.5)],'M3×8：从背后向身体内',(-18,0,0)),view=(-1,-.2,.45))
step('A14','放电池、接线，然后再封顶','电池 ×1；理线带少量；不新增结构螺丝',[
'电池竖放在身体前部的限位空间，线路走两侧，不放进腿轴活动区。','按模块标识接：电池→XA007开关→接收板电源；S1左髋、S2左踝、S3右髋、S4右踝，左右均按机器人自身。','攻击线提前留到顶部：蓝机用已验证的D1舵机转接线，红机用M1电机线。先确认极性，不能只按线颜色猜。','插一次USB检查开口。盖上前逐根确认线在内部走线口中，没有压在身体/头部接缝。'],'电池、主板不松，开关可操作；拔插USB无需拆头。',['C01','C02','board','battery','C03'],view=(-1,-1,1),alpha={'C01':.18},extra='后方USB已确认用于数据；不要据此认为接上USB就能给电池充电。充电按原电池/充电器方式。')
step('A15','最后贴眼睛，认清正面','C08/C09 两只眼睛；少量502或适用胶',[
'找到身体正面（与USB/开关背面相反），先干放两只椭圆眼睛对齐。','平背面少量点胶贴在外壁；不要让胶流进孔或可拆接缝。','需要高光时用白色油漆笔点出，不必寻找额外高光小打印件。'],'两眼齐平、固定，正背面易辨。',['C01','C08','C09'],marks([(37.6,y,-18) for y in (-14,14)],'眼睛平背点胶；无螺丝',(15,0,0)),view=(1,-.3,.3))
# Palm branch
step('B01','承重座先装两颗盖子铜螺母','M3热熔铜螺母 ×2',[
'拿B03承重座，找到后侧两个较小的盖耳，不是外周四个压环螺母槽。','由上向下热装两颗铜螺母，冷却；位置见图1、2。','至此一台蓝机共用了8颗热熔铜螺母：身体6颗、承重座2颗。'],'两颗顶面齐平、轴线竖直。',['B03'],marks([(-27,y,33.5) for y in (-15,15)],'盖耳铜螺母：上→下'),view=(-1,-1,1))
step('B02','底座侧槽先塞入四颗普通螺母','M3普通六角螺母 ×4',[
'拿B01底座，找到舵机桥支座处的4个侧向六角螺母槽。','从侧边推入普通M3六角螺母，让其螺纹孔与上方竖孔同轴。','用待会使用的M3螺丝轻试能起牙后退出；本步不要装桥和上盖，以免堵槽。'],'4颗均到底、没有斜卡；这些不是热熔铜螺母。',['B01'],marks([(x,y,17.4) for x in (-29,29) for y in (-6,6)],'普通M3螺母：塞入侧槽',(0,16,0)),view=(-1,-1,.7))
step('B03','承重座底面预装四颗压环螺母','M3普通六角螺母 ×4',[
'把B03翻过来，找到外周四个六角槽；图为底面观察。','普通M3六角螺母分别塞到底，让孔与上方压环螺孔同轴。','先轻试螺丝起牙再退出，避免后面装完盖子才发现漏放。'],'普通螺母累计8颗：底座4颗，承重座底面4颗。',['B03'],marks([(p[0],p[1],29.5) for p in CAP],'普通M3螺母：从底面放入',(0,0,-15)),view=(-1,-1,-1))
step('B04','把连续旋转舵机装在舵机桥上','攻击用连续旋转舵机 ×1；匹配原配安装小螺丝 ×2',[
'将舵机从B02桥的矩形孔穿入，轴朝上，壳体垂在桥下面。','两个安装耳对齐桥上的两只小孔，使用与实际舵机匹配的原配安装小螺丝锁住。','把线引向下方，先不装B07转盘；舵盘花键需与实物一致。'],'舵机壳固定、输出轴向上，线不被桥夹住。',['B02','servo'],marks([(-13.9,0,25),(13.9,0,25)],'原配小螺丝：安装耳→桥'),view=(1,-1,.8),extra='此处模型孔Ø2.4只提供安装位置，不代表可以换M3；若新舵机耳孔/花键不同，要先试配。')
step('B05','承重座、舵机桥、底座锁成一组','M3×14 半圆头螺钉 ×4；用B02预放的4颗螺母',[
'将B02舵机桥放在B01支座上，再把B03承重座放到桥上方，四孔对齐。','从B03的四个下沉座面向下插M3×14，依次穿过承重座与桥，拧入B01的普通螺母。','先四颗都起牙，再交替拧紧；不要先上转盘挡住工具。'],'三个件贴合，四个螺丝头低于转盘运动空间。',['B01','B02','B03','servo'],marks(ST,'M3×14：座→桥→底座螺母'),view=(1,-1,1),extra='使用低头/半圆头；高圆柱头可能顶到转盘。')
step('B06','圆肩盖罩上，只锁后侧两个孔','M3×8 半圆头螺钉 ×2',[
'将B06圆肩盖从上方罩住机构，顶部圆孔对准承重座环口。','后侧两孔各用1颗M3×8，向下拧入B01步骤装好的两颗铜螺母。','身体四角安装孔此时仍露在盖子外；不要把这四孔当作本步盖子孔。'],'盖子贴合，无线卡在下边缘；顶盖两颗螺丝就位。',['B01','B02','B03','B06'],marks([(-27,y,37) for y in (-15,15)],'M3×8：圆肩盖→盖耳铜螺母'),view=(-1,-1,1))
step('B07','舵盘嵌进转盘槽，再锁中心','匹配舵机的原配舵盘及中心螺丝各1件',[
'先在桌上试B07底面的舵盘形状槽，舵盘必须贴入槽内；不能靠压环把不匹配的舵盘硬压下去。','将舵盘/B07转盘组合对到舵机轴，转盘下部台阶落入B03承重座环口。','从B07中央检修孔沿轴线，用原配中心螺丝把舵盘锁到输出轴；螺丝只锁舵盘，不能拉歪转盘。'],'转盘落座、轴心同心，原配中心螺丝未顶底；此时还没有手掌。',['B03','B06','horn','B07'],marks([(5.34,0,42.57)],'原配中心螺丝：中央孔→舵机轴'),view=(1,-1,1),extra='舵盘负责传扭矩，外圈承重座承受手掌重量。花键不合或舵盘凸起时不要继续。')
step('B08','两半压环扣住转盘边缘','M3×8 半圆头螺钉 ×4；使用B03步骤的4颗普通螺母',[
'把B04/B05两半压环从转盘两侧放好，使它们压住转盘的限位边缘。','图中4孔向下各装1颗M3×8，拧到下方预放普通螺母。先对角轻带，再逐渐贴合。','断电检查转盘无明显上下抬起；有阻力不能强扭舵机，先松开压环检查毛刺和装配间隙。'],'压环固定但不夹死转盘；螺丝头不与接杆干涉。',['B03','B06','B07','B04','B05'],marks(CAP,'M3×8：压环→预放普通螺母'),view=(-1,-1,1))
step('B09','蓝色头部整组装到身体','M3×8 半圆头螺钉 ×4',[
'先把攻击线从底座内部送进身体，接至已验证的D1转接线，断电核对G/V/S。','头部底座落在身体顶部，四角孔对上A01铜螺母；检查内部压臂没有压坏主板/线。','从盖子外侧四个露出的角孔向下拧M3×8。先全部起牙，再交替锁紧；接杆挡工具时转开接杆。'],'头部不晃，四角贴合，开关/USB保持可操作。',['C01','B01','B06','B07','B04','B05'],marks([(x,y,3) for x,y,z in TOP],'M3×8：头部底座→身体'),view=(-1,-1,1),extra='先不粘大手掌，四角螺丝更容易接近。')
step('B10','最后才把手掌粘到一体接杆上','B08手掌；少量502/适用胶；无插销、无腕部螺丝',[
'把B08手掌的腕部槽先套上B07一体插芯，干试到底，手掌朝向按外观图对齐。','确认没有支撑残渣或干涉，再取下，仅在插芯粘接面薄薄点胶，重新推到底并保持到初固。','不要把胶滴进转盘、压环或舵机轴；完全固化后再测试。'],'手掌与接杆不歪、不松；没有使用旧版黄色插块或横向销。',['B01','B06','B07','B04','B05','B08'],marks([(60,0,46)],'一体插芯：干试→点胶→插到底',(25,0,0)),view=(1,-1,.65))
# Fist branch
step('R01','电机减速器先固定在红色底座','完整LA024电机+LA016减速器；约2.5mm扎带 ×2',[
'先准备已经组装完整、可运转的减速电机。打印出来的两半壳不是完整减速器，内部还需原配齿轮和轴。','整组放进R01底座的电机托位，减速输出轴朝上、电机尾部朝后。','两根扎带从托位的绑扎通路绕住壳体收紧；尾部电线先穿底座隐藏走线口向下，不从身体接缝夹出。'],'减速器不抬起、不转动，扎带不碰输出轴和后续连杆。',['R01']+REFS,marks([(-44,0,12),(-23,0,12)],'两道固定区域：绕壳体扎带',(0,-18,8)),view=(-1,-1,.7),extra='本图对应完整原配减速总成；内部齿轮尚未装好的，先沿原配减速器说明装好，不凭这张外形图猜齿轮顺序。')
step('R02','桌上先连接曲柄与连杆','M3×16低头 ×1；2mm隔套 ×1；薄垫圈 ×2；M3防松螺母 ×1',[
'此步在桌上进行，曲柄暂时不要套到电机轴上，否则底部可能不好送螺丝。','从下向上按右图顺序穿：螺丝头→薄垫圈→R03曲柄偏心孔→2mm隔套→R04连杆端孔→薄垫圈→防松螺母。','曲柄有两个孔：中心大轴套是电机轴位置，离中心10mm的偏心孔才连接杆。','一手固定螺丝，一手慢慢拧防松螺母；消除明显上下晃动后停止，连杆必须仍能自由转动。'],'活动铰点能摆动；不能把连杆夹死在曲柄上。',['R03','R04'],marks([(-26,0,28.8)],'偏心孔：M3×16由下向上',(0,0,-20)),view=(1,-1,.75),stack=['上：M3防松螺母','薄垫圈','R04连杆（4mm）','隔套（2mm）','R03曲柄（4mm）','薄垫圈','下：M3×16螺丝头'])
step('R03','再连接连杆的另一端与滑架','M3×25低头 ×1；2mm隔套 ×1；薄垫圈 ×2；M3防松螺母 ×1',[
'保持上一步的曲柄—连杆组合，拿R05滑架，长舌头朝拳头前方。','从下向上穿：螺丝头→薄垫圈→R04另一端孔→2mm隔套→R05滑架中央孔→薄垫圈→防松螺母。','慢慢收紧到没有明显旷量但仍可转动。连杆在滑架下方，不要把它翻到滑架上面。'],'两处铰点都能转动，滑架舌头朝前。',['R03','R04','R05'],marks([(8,0,34.8)],'滑架中央孔：M3×25下→上',(0,0,-22)),view=(1,-1,.75),stack=['上：M3防松螺母','薄垫圈','R05滑架（10mm）','隔套（2mm）','R04连杆（4mm）','薄垫圈','下：M3×25螺丝头'])
step('R04','整组放下，曲柄对准减速输出轴','暂不加螺丝；先对形状干试',[
'把上一组曲柄—连杆—滑架抬到R01上方。','曲柄中心的双扁位孔对上减速器输出轴，轻轻套到底；滑架放在两导杆支座之间。','不要用锤子敲，也不要把曲柄偏心孔错套到输出轴。轴套太紧先清除毛刺并核对形状。'],'曲柄坐到位，滑架在两条导杆的中间，连杆仍在滑架下方。',['R01']+REFS+['R03','R04','R05'],marks([(-16,0,30.1)],'中心轴套对准输出轴',(0,0,20)),view=(1,-1,1))
step('R05','两根导杆从前穿入滑架','Ø3×64mm光滑金属杆 ×2',[
'从拳头方向的前支座穿入一根金属杆，再穿过滑架侧孔，最后进入后支座盲孔。','另一侧同样操作；滑架先位于两支座之间，不要先把两根杆装死再想放滑架。','用手轻推滑架，确认沿杆顺滑；需要时松开尚未固定的曲柄调整，不能暴力顶减速齿轮。'],'两杆平行、均进入后座，滑架不歪、不涩。',['R01','R03','R04','R05','rodL','rodR'],marks([(52,y,45.8) for y in (-20,20)],'Ø3×64：前→后穿入',(23,0,0)),view=(1,-1,.65))
step('R06','锁住导杆，再固定输出轴中心','M3×4紧定螺钉 ×2；输出轴原配中心锁紧螺丝 ×1',[
'前支座上方两只Ø2.6底孔需先攻M3牙、清干净屑，再装M3×4紧定螺钉；轻压住金属杆，别拧裂支座。','通过曲柄中心孔，用与减速输出轴实际螺纹匹配的原配中心螺丝锁住曲柄。','两处滑架/连杆活动螺母不再加紧。检查导杆不串出、曲柄不会从输出轴抬起。'],'导杆固定、曲柄轴向不脱落，两个铰点仍自由。',['R01','R03','R04','R05','rodL','rodR'],marks([(52,-20,50.8),(52,20,50.8)],'M3×4紧定：顶面向下')+marks([(-16,0,32.8)],'原配轴心螺丝：不是默认M3'),view=(1,-1,1),extra='中心通孔Ø2.7不能证明输出轴是M2.5或M3螺纹。沿用已运行旧机的原配螺丝，拿不准时先停在这一步。')
step('R07','拳头腕杆插上滑架舌头并穿螺丝','M3×18或×20 ×1；M3普通六角螺母 ×1',[
'R06拳头腕杆的槽对准R05前伸舌头，从前方向后插到位。','对齐腕部上下贯通孔，用M3×18或×20自上而下穿过腕杆与舌头，在底部配普通M3六角螺母。','该处是固定连接，可以锁紧；按实际垫片选长度，螺母后露1–2牙即可，不让长螺丝碰其他结构。'],'拳头固定、不扭摆；不要把本步与后方的活动铰点混淆。',['R03','R04','R05','R06','rodL','rodR'],marks([(25,0,52)],'腕部贯通孔：上螺丝、下螺母'),view=(1,-1,.8))
step('R08','封头前先检查一整圈行程','不增加螺丝',[
'断电下先检查两端极限和两处铰点，不强行反拖带阻力的减速器。','确认拳头往复时不碰底座/护罩，连杆上下有隔套，螺丝尾部没有擦到固定结构。','需要通电检验时固定底座、清空拳头前方，只做受控短时测试；卡住立刻断电处理。'],'约20mm往复行程通畅，再装身体；不能靠电机硬磨通卡点。',['R01']+REFS+['R03','R04','R05','R06','rodL','rodR'],view=(1,-1,.65))
step('R09','先把底座放到身体，护罩一起对孔','本步先穿线和对孔',[
'将电机线从底座尾部隐藏口向下送入身体，断电接到M1。','R01底座落到身体顶部，四角孔对齐；主板托架上方不压线。','放上R02护罩：后方两个罩脚与身体后方两孔共用螺丝，不另找旧版悬空耳孔。'],'四孔全部对正，后两个孔上有护罩脚，前两个孔没有。',['C01','R01','R02','R03','R04','R05','R06'],view=(-1,-1,.7),marks=marks([(-30,y,5) for y in (-30,30)],'后两孔：护罩脚+底座共用'))
step('R10','前面两颗8mm，后面两颗10mm','前：M3×8 ×2；后：M3×10 ×2',[
'先在前方两孔各轻拧1颗M3×8，穿R01底座进入身体铜螺母。','再从后方护罩敞口向下，各拧1颗M3×10，穿护罩脚+底座进入身体铜螺母。','四颗都起牙后再交替锁紧；检查底座四角贴合、M1线没有夹在接缝里。'],'红色头部和护罩固定，后USB与开关仍可操作。',['C01','R01','R02','R03','R04','R05'],marks([(30,y,3) for y in (-30,30)],'前2孔：M3×8向下')+marks([(-30,y,5) for y in (-30,30)],'后2孔：M3×10穿护罩脚'),view=(-1,-1,1))
step('Z01','最后检查，再做短时开机','无新增螺丝',[
'检查所有结构螺丝贴合；两个拳头活动铰点仍可转；巴掌转盘没有被压环夹死。','S1左髋、S2左踝、S3右髋、S4右踝；蓝机D1攻击舵机、红机M1电机。接线按板端标识和已验证转接线。','先托住机器人进入站姿，确认左右脚方向、无顶死，再落地试行走；随后单独试攻击，最后组合。','松杆应停，K4按住跳舞、松开恢复；本项目K4已不是急停，异常用实体电源开关断电。'],'机械、电气、动作分别确认，不把“拧得上”当作“动作已验证”。',['C01','C04','C05','C06','C07','C08','C09'],view=(1,-1,.4),extra='这是按现有v11送印模型核对的教程；新到舵机/五金的实物公差和实际安装效果仍需当场确认。')

# Rendering: exact assembly meshes, annotated hole centres; no new CAD modifications.
def actor(m,c,opacity=1):
 pts=vtk.vtkPoints();pts.SetData(numpy_to_vtk(np.asarray(m.vertices,dtype=np.float32),deep=True))
 cells=vtk.vtkCellArray();cells.SetCells(len(m.faces),numpy_to_vtkIdTypeArray(np.column_stack((np.full(len(m.faces),3),m.faces)).astype(np.int64).ravel(),deep=True))
 poly=vtk.vtkPolyData();poly.SetPoints(pts);poly.SetPolys(cells)
 norm=vtk.vtkPolyDataNormals();norm.SetInputData(poly);norm.SetFeatureAngle(45);norm.SplittingOff()
 mapper=vtk.vtkPolyDataMapper();mapper.SetInputConnection(norm.GetOutputPort())
 a=vtk.vtkActor();a.SetMapper(mapper);a.GetProperty().SetColor(*[int(c[i:i+2],16)/255 for i in (1,3,5)]);a.GetProperty().SetOpacity(opacity);a.GetProperty().SetAmbient(.35);a.GetProperty().SetDiffuse(.65);return a

def wrap(draw,text,x,y,w,size=25,fill='#203247',gap=7):
 f=font(size);line=''
 for ch in text:
  if ch=='\n' or draw.textlength(line+ch,font=f)>w:
   draw.text((x,y),line,font=f,fill=fill);y+=size+gap;line='' if ch=='\n' else ch
  else:line+=ch
 if line:draw.text((x,y),line,font=f,fill=fill);y+=size+gap
 return y

def arrow(d,start,end,c='#e85b36'):
 p=np.array(start);q=np.array(end);v=q-p;n=np.linalg.norm(v)
 if n<3:return
 u=v/n;per=np.array([-u[1],u[0]])
 d.line([tuple(p),tuple(q)],fill=c,width=5);d.polygon([tuple(q),tuple(q-15*u+6*per),tuple(q-15*u-6*per)],fill=c)

def render(s):
 canvas=Image.new('RGB',(1600,1100),'#f6f7f9');d=ImageDraw.Draw(canvas)
 accent='#2279b7' if s['code'].startswith('B') else '#cc4a50' if s['code'].startswith('R') else '#273d55'
 d.rectangle((0,0,1600,112),fill=accent);d.text((35,22),s['code']+'  '+s['title'],font=font(36),fill='white')
 if s['official']:
  pages=[]
  for n in s['official']:
   path=OUT/f'制作记录/official_p{n}.png' if n>=10 else ROOT/f'01_研究参考/robot-battle-reference/manual_hi_p{n}.png'
   im=Image.open(path).convert('RGB');im.thumbnail((max(380,1450//len(s['official'])),800));pages.append(im)
  total=sum(im.width for im in pages)+20*(len(pages)-1);x=(1600-total)//2
  for im in pages:canvas.paste(im,(x,140));x+=im.width+20
  d=ImageDraw.Draw(canvas);wrap(d,'原版 Otto DIY V9 手册 · PDF页 '+','.join(map(str,s['official']))+'；这里只参考腿部安装。具体螺丝/动作要求见本步骤文字。',35,990,1500,24)
 else:
  ren=vtk.vtkRenderer();ren.SetBackground(.965,.97,.98);bounds=[]
  for k in s['parts']:
   m=load(k);vec=s['shift'].get(k)
   if vec:m=m.copy();m.apply_translation(vec)
   c='#dde2e6'
   if k.startswith('B'):c='#4c9ed0'
   elif k.startswith('R') and k in names:c='#db6669'
   elif k in ('C08','C09'):c='#29333e'
   elif k in ('C06','C07'):c='#70a6c7'
   elif k=='board':c='#528572'
   elif k in ('servo','switch'):c='#525969'
   elif k=='battery':c='#6a87be'
   elif k.startswith('F_ref') or k.startswith('rod'):c='#a8b3bd'
   if s['code'] in ('R02','R03','R04','R05','R06','R07','R08'):
    c={'R03':'#e3aa46','R04':'#4baf92','R05':'#4f98cc','R06':'#d85b60'}.get(k,c)
   ren.AddActor(actor(m,c,s['alpha'].get(k,1)));bounds.extend(m.bounds)
  b=np.asarray(bounds);center=(b.min(0)+b.max(0))/2;v=np.array(s['view'],dtype=float);v=v/np.linalg.norm(v)
  cam=ren.GetActiveCamera();cam.SetFocalPoint(*center);cam.SetPosition(*(center+v*350));cam.SetViewUp(0,0,1 if v[2]>=0 else -1);cam.ParallelProjectionOn()
  W,HH=1160,850;win=vtk.vtkRenderWindow();win.SetOffScreenRendering(True);win.SetSize(W,HH);win.SetMultiSamples(4);win.AddRenderer(ren);ren.ResetCamera();cam.Zoom(.86);win.Render()
  def proj(p):
   ren.SetWorldPoint(*p,1);ren.WorldToDisplay();x,y,_=ren.GetDisplayPoint();return (x,HH-y+130)
  grab=vtk.vtkWindowToImageFilter();grab.SetInput(win);grab.ReadFrontBufferOff();grab.Update();a=vtk_to_numpy(grab.GetOutput().GetPointData().GetScalars()).reshape(HH,W,3)
  canvas.paste(Image.fromarray(np.flipud(a).copy()),(0,130));d=ImageDraw.Draw(canvas)
  yy=150
  d.text((1180,yy),'图中编号 / 操作点',font=font(25),fill=accent);yy+=50
  for i,(p,t,vec) in enumerate(s['marks'],1):
   q=proj(p);start=proj(np.array(p)+vec);arrow(d,start,q)
   d.ellipse((q[0]-15,q[1]-15,q[0]+15,q[1]+15),outline='#d83f29',width=4)
   off=np.array(start)-np.array(q);ln=np.linalg.norm(off);pp=np.array(start)+(off/ln*15 if ln>0 else (0,-20))
   d.ellipse((pp[0]-17,pp[1]-17,pp[0]+17,pp[1]+17),fill='#d84d35');d.text(tuple(pp),str(i),anchor='mm',font=font(23),fill='white')
   yy=wrap(d,f'{i}. '+t,1180,yy,385,24)+17
  if s['stack']:
   yy+=12;yy=wrap(d,'铰点叠放：从上往下看',1180,yy,385,23,fill='#bb353f')+8
   for j,t in enumerate(s['stack']):
    d.rounded_rectangle((1180,yy,1565,yy+44),radius=5,fill=['#eee2bd','#dfe6eb','#cce5df','#f3d49c'][j%4]);d.text((1190,yy+6),t,font=font(22),fill='#203247');yy+=53
  else:
   yy+=20;yy=wrap(d,'本图出现的打印件',1180,yy,385,23,fill=accent)+7
   for k in s['parts']:
    if k in names:yy=wrap(d,k+' '+names[k],1180,yy,385,21)+5
    if yy>940:break
  d.text((35,1005),'箭头指向安装孔/操作点；未画出的螺纹、垫片按步骤文字装。',font=font(23),fill='#617183')
  win.Finalize()
 path=IMG/(s['code']+'.png');canvas.save(path,optimize=True);s['image']='图解/'+path.name
 print('Rendered',s['code'],flush=True)

for s in steps:render(s)
# Keep authoritative source PDFs and hardware schedule available offline.
shutil.copy2(ROOT/'01_研究参考/robot-battle-reference/OttoDIY_Manual_V9.pdf',OUT/'Otto_V9官方原版手册.pdf')
shutil.copy2(PACK/'00_先读说明/02_五金采购与用量.md',OUT/'五金总表_沿用v11.md')
(OUT/'制作记录/逐步数据.json').write_text(json.dumps(steps,ensure_ascii=False,indent=2),encoding='utf-8')
# Offline guide: one operation per page, keyboard/touch navigation, optional all-pages view.
style='''*{box-sizing:border-box}body{margin:0;background:#edf1f5;color:#23354b;font-family:"Microsoft YaHei",sans-serif}header{padding:24px 5vw;background:#23354b;color:white}h1{font-size:26px;margin:0 0 9px}header p{margin:8px 0;line-height:1.6}nav{position:sticky;top:0;background:#fff;z-index:5;padding:12px 5vw;box-shadow:0 2px 8px #0001;display:flex;gap:8px;flex-wrap:wrap}button,select{padding:10px 13px;border:1px solid #c8d0d8;border-radius:7px;background:white;font-size:15px;cursor:pointer}button.active{background:#23354b;color:white}main{max-width:1250px;margin:20px auto;padding:0 16px}.intro,.step{background:white;border-radius:12px;padding:22px;margin-bottom:24px}.step{display:none}.step.current,body.all .step{display:block}.step img{width:100%;height:auto;border:1px solid #e3e6e9;border-radius:6px}.hardware{background:#fff2d6;padding:12px 16px;border-left:4px solid #d6a541;line-height:1.65}.actions{font-size:18px;line-height:1.9;padding-left:28px}.actions li{padding-left:4px;margin:8px 0}.check{background:#e9f4ef;padding:14px;line-height:1.7}.note{font-size:15px;line-height:1.7;color:#755d33;background:#faf5eb;padding:12px}h2{margin:0 0 16px;font-size:24px}.caption{font-size:14px;color:#687b8b}footer{padding:20px 5vw;line-height:1.8}a{color:#1771a2} .bottom{display:flex;gap:12px;margin-top:20px}@media print{header,nav,footer,.intro,.bottom{display:none!important}.step{display:block!important;page-break-after:always;break-after:page;border-radius:0;margin:0;padding:0}main{margin:0;padding:0;max-width:none}.step img{max-height:46vh;object-fit:contain}.actions{font-size:12px;line-height:1.4}.hardware,.check,.note{font-size:11px;padding:6px}h2{font-size:18px}.actions li{margin:4px 0}@page{size:A4 portrait;margin:12mm}}'''
intro='''<div class="intro"><b>怎么用：</b>先按 A01–A15 完成共用身体，再选蓝机 B01–B10 或红机 R01–R10，最后做 Z01 检查。每页只做一件事，点“下一步”继续。<p>黄色框是本步五金；图中数字是孔位/操作点；下方列出实际动作和完成标准。可以点图片放大。示意渲染用不同颜色分辨零件，实际打印颜色不必相同。</p><p><b>先确认材料：</b>蓝机需8颗、红机需6颗匹配Ø4.0底孔的 M3热熔铜螺母（长5.7mm）。板和开关另用2.5mm塑料自攻，舵机用原配小螺丝；不是全部M3。没有对应件不要硬拧替代。</p><p>本版只细化装配说明，不改变已经打印的v11结构。孔位来自模型；新到五金、舵盘花键及实际动作仍需试装确认。脚部原版图保留 Otto DIY 来源。</p><a href="五金总表_沿用v11.md">查看逐项五金总表</a> · <a href="Otto_V9官方原版手册.pdf">Otto V9官方原版手册</a></div>'''
sections=[]
for i,s in enumerate(steps):
 e=html.escape
 sections.append(f'<section class="step" id="{s["code"]}"><h2>{s["code"]}　{e(s["title"])}</h2><p class="hardware"><b>本步准备：</b>{e(s["hardware"])}</p><a href="{s["image"]}" target="_blank"><img src="{s["image"]}" alt="{e(s["title"])}"></a><ol class="actions">'+''.join('<li>'+e(x)+'</li>' for x in s['actions'])+'</ol><p class="check"><b>完成后检查：</b>'+e(s['check'])+'</p>'+('<p class="note">'+e(s['extra'])+'</p>' if s['extra'] else '')+'<div class="bottom"><button onclick="move(-1)">← 上一步</button><button onclick="move(1)">下一步 →</button></div></section>')
opts=''.join(f'<option value="{i}">{s["code"]} {html.escape(s["title"])}</option>' for i,s in enumerate(steps))
js='''let nodes=[...document.querySelectorAll('.step')],idx=0;function show(i){idx=Math.max(0,Math.min(nodes.length-1,i));nodes.forEach((n,j)=>n.classList.toggle('current',j===idx));document.querySelector('#choose').value=idx;document.querySelector('#count').textContent=(idx+1)+' / '+nodes.length;history.replaceState(null,'','#'+nodes[idx].id)}function move(d){show(idx+d);window.scrollTo({top:document.querySelector('main').offsetTop-90,behavior:'smooth'})}function jump(code){show(nodes.findIndex(n=>n.id===code));window.scrollTo({top:document.querySelector('main').offsetTop-90,behavior:'smooth'})}document.querySelector('#choose').onchange=e=>show(+e.target.value);document.querySelector('#all').onclick=()=>document.body.classList.toggle('all');document.addEventListener('keydown',e=>{if(e.target.tagName==='SELECT')return;if(e.key==='ArrowRight')move(1);if(e.key==='ArrowLeft')move(-1)});show(Math.max(0,nodes.findIndex(n=>'#'+n.id===location.hash)));'''
page='<!doctype html><html lang="zh-CN"><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>milk机器人 · 逐步装配图解</title><style>'+style+'</style><header><h1>milk 机器人 · 一步一步装配</h1><p>适用：已送印的 v11 白色身体 / 蓝色巴掌 / 红色拳头　｜　2026-11-12</p></header><nav><button onclick="jump(\'A01\')">① 共用身体</button><button onclick="jump(\'B01\')">② 蓝色巴掌</button><button onclick="jump(\'R01\')">② 红色拳头</button><button onclick="jump(\'Z01\')">③ 完工检查</button><select id="choose">'+opts+'</select><button id="all">展开/收起全部</button><span id="count"></span></nav><main>'+intro+''.join(sections)+'</main><footer>本版依据：v11送印包五金表、修正后的C02托架、v11装配网格、v10/v11建模孔位、Otto V9官方手册。<br>蓝机路线26步，红机路线26步（含共同步骤与最后检查）；共36张操作图。没有自动运行硬件或更改模型。</footer><script>'+js+'</script></html>'
(OUT/'00_逐步装配图解.html').write_text(page,encoding='utf-8')
md=['# milk机器人逐步装配教程','适用v11送印件；2026-11-12。先A01–A15，再B或R，最后Z01。']
for s in steps:
 md+=['','## '+s['code']+' '+s['title'],'','本步准备：'+s['hardware'],'','![步骤图]('+s['image']+')','']+[f'{i+1}. {t}' for i,t in enumerate(s['actions'])]+['','完成检查：'+s['check'],s['extra']]
(OUT/'01_逐步装配文字版.md').write_text('\n'.join(md),encoding='utf-8')
(OUT/'制作记录/来源与核对说明.md').write_text('''# 来源与核对
- 未改变原模型；仅生成逐步文档和图片。
- 使用v11装配清单；C02替换为v11送印包中的Ø2.1自攻底孔修正版。
- 身体4顶孔/2背孔、主板4孔、开关1细孔、巴掌桥4孔/压环4孔/盖2孔、拳头导杆及活动铰点均取现有几何坐标。
- 红机展示相位为曲柄180度：输出轴X=-16，偏心孔X=-26，滑架中心X=8，腕部孔X=25；没有把0度相位坐标叠在180度网格上。
- 拳头两个活动铰点改为先在桌上串联，再套输出轴及穿导杆，避免下方送螺钉通路被固定结构遮挡。该顺序为装配安排，尚待实物操作确认。
- 官方V9原图用于腿部实际螺丝/穿线方式；不沿用旧笔记中髋踝轴方向的错误推断。
- 图中紧固件箭头和铰点叠放框为说明性标注；未建立实际每种螺钉实体并做扭矩或公差测试。
- 原配舵机小螺丝、舵盘花键、减速轴中心螺纹不臆测规格，需匹配实物。
- 减速箱内部齿轮顺序未重新验证；R01明确以已装完整LA024+LA016总成为前提。
''',encoding='utf-8')
print('DONE',len(steps),OUT,flush=True)

