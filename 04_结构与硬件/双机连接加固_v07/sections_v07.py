"""Annotated sections of each v07 fix (review evidence only)."""
from pathlib import Path
import json,numpy as np,trimesh
import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
plt.rcParams['font.sans-serif']=['Microsoft YaHei','SimHei'];plt.rcParams['axes.unicode_minus']=False
P=Path(__file__).resolve().parent;O=P/'预览/修改剖面';O.mkdir(parents=True,exist_ok=True)
MAN=json.loads((P/'装配清单.json').read_text(encoding='utf-8'))
L={o['name']:trimesh.load_mesh(P/'装配网格'/o['file']) for o in MAN};C={o['name']:o['color'] for o in MAN}
def pick(*pre):return [n for n in L if n.startswith(pre)]
def draw(names,axis,val,fn,xl,yl,title,notes):
 n=np.eye(3)[axis];ij=[i for i in range(3) if i!=axis];fig,ax=plt.subplots(figsize=(10,7))
 for nm in names:
  seg=trimesh.intersections.mesh_plane(L[nm],n,n*val)
  if len(seg):ax.add_collection(LineCollection(seg[:,:,ij],colors=C[nm],linewidths=1.3));ax.plot([],[],color=C[nm],label=nm[:22])
 for (x,y,tx,ty,s) in notes:ax.annotate(s,(x,y),(tx,ty),fontsize=9,color='#1d6b3a',arrowprops=dict(arrowstyle='->',color='#1d6b3a'),bbox=dict(fc='white',ec='#1d6b3a',alpha=.92))
 ax.set_xlim(*xl);ax.set_ylim(*yl);ax.set_aspect('equal');ax.grid(alpha=.3);ax.set_title(title)
 ax.set_xlabel('XYZ'[ij[0]]+' mm');ax.set_ylabel('XYZ'[ij[1]]+' mm');ax.legend(fontsize=7,loc='upper left',bbox_to_anchor=(1,1))
 fig.tight_layout();fig.savefig(O/fn,dpi=110);plt.close(fig)
common=pick('01_','R01','R02','02_','R03','03_','04_','05_')
draw(common+pick('20_','21_'),1,-30,'F01_左后孔改热熔螺母.png',(-52,-15),(-35,12),'F01（D01）Y=-30：四个顶部孔统一 M3×5.7 热熔螺母',
 [(-30,-3,-50,6,'Ø4.0×6 热熔螺母孔\n凸台到 Z-8，开关仓在其下方'),(-34,-20,-50,-28,'开关已后移，不再切到凸台')])
draw(common+pick('F_','20_','21_'),1,0,'F02_拳头尾部入线.png',(-90,-30),(-15,30),'F02（D02）Y=0：入线口移到电机尾面后方',
 [(-61.5,0,-88,-10,'新入线口 X-64.2..-58.5，宽9mm\n线从电机尾部直接下落'),(-67,10,-88,20,'护罩后壁在入线口之后，不再压线')])
draw(common,2,-16.2,'F03_开关插头空间.png',(-55,-5),(-40,12),'F03（D03/D04）Z=-16.2：开关后移6.5、右移4.5',
 [(-37,3.5,-30,9,'+Y 插口前方 6.0mm'),(-37,-33,-28,-38,'-Y 插口前方 5.5mm'),(-45,-37,-53,-30,'侧壁 2mm')])
draw(pick('03_','R03','01_'),0,-42.7,'F04_开关面板螺丝.png',(-42,10),(-40,0),'F04（D05）X=-42.7：面板孔距边≥1.8mm，后接热熔螺母凸台',
 [(-33.5,-28.5,-25,-37,'M3×8 → 热熔螺母'),(2.5,-28.5,-8,-37,'M3×8 → 热熔螺母')])
palm=pick('10_','11_','12_','13_','14','15_','R10','R11')
draw(common+palm,1,6,'F05_承重座螺钉沉低.png',(-40,45),(15,48),'F05（D06）Y=6：沉孔加深到 Z29.8，用 ISO7380 半圆头',
 [(29,31,10,44,'半圆头顶 Z31.45，距转盘 2.05mm\n径向环在此处整齐开口，不留薄片')])
draw(common+palm,0,-29,'F06_罩螺丝热熔螺母.png',(-35,35),(0,42),'F06（D07）X=-29：罩螺丝进热熔螺母',
 [(-18,29,-5,12,'耳片下加 7mm 凸台\nØ4.0 热熔螺母孔')])
draw(common+pick('10_'),1,0,'F07_电池限位.png',(-45,42),(-42,8),'F07（D10）Y=0：顶模块挂下电池后挡与压条',
 [(16.9,-15,-5,-25,'后挡，距电池 0.3mm'),(25,-6.8,10,4,'压条，距电池顶 0.3mm')])
draw(common+pick('10_'),1,12,'F08_托架压紧.png',(-45,20),(-42,8),'F08（D09）Y=12：托架下有定位销、上有压臂',
 [(-22,-1.8,-40,4,'压臂距托架 0.2mm'),(-22,-30,-40,-20,'底柱定位销 Ø2.9')])
print('SECTIONS_COMPLETE',sorted(p.name for p in O.iterdir()))
