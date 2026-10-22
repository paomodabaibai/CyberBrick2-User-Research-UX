"""Rebuild the existing vector wall-sticker design for textured 3D surfaces.
Internal PDF intermediates are kept on E:, then rasterized by Poppler.
"""
from pathlib import Path
import subprocess
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT=Path(__file__).resolve().parents[1]
TEMP=Path(r'E:\CodexData\Scratch\arena-model-20261021')
pdfmetrics.registerFont(TTFont('CJK',r'C:\Windows\Fonts\msyh.ttc',subfontIndex=0))
pdfmetrics.registerFont(TTFont('CJKB',r'C:\Windows\Fonts\msyhbd.ttc',subfontIndex=0))
for w,h in [(115,55),(115,75),(115,95),(120,75)]:
    name=f'wall_{w}_h{h}'
    c=canvas.Canvas(str(TEMP/f'{name}.pdf'),pagesize=(w*mm,h*mm))
    def rect(x,y,a,b,col):
        c.setFillColor(HexColor(col));c.rect(x*mm,y*mm,a*mm,b*mm,stroke=0,fill=1)
    def line(x,y,a,b,col,width=.2):
        c.setStrokeColor(HexColor(col));c.setLineWidth(width*mm)
        c.line(x*mm,y*mm,a*mm,b*mm)
    def txt(x,y,s,size,col,bold=False,right=False):
        c.setFont('CJKB' if bold else 'CJK',size);c.setFillColor(HexColor(col))
        (c.drawRightString if right else c.drawString)(x*mm,y*mm,s)
    rect(0,0,w,h,'#e8efed')
    rect(1.5,1.5,w-3,h-3,'#284955')
    c.saveState();p=c.beginPath();p.rect(1.5*mm,1.5*mm,(w-3)*mm,(h-3)*mm);c.clipPath(p,stroke=0,fill=0)
    for x in range(0,w,15):line(x,1.5,x,h-1.5,'#3b5e68',.22)
    for y in range(15,h,15):line(1.5,y,w-1.5,y,'#3b5e68',.22)
    rect(1.5,1.5,w-3,7,'#f0be50')
    for x in range(-10,w+10,16):
        p=c.beginPath();p.moveTo(x*mm,1.5*mm);p.lineTo((x+6)*mm,1.5*mm)
        p.lineTo((x+13)*mm,8.5*mm);p.lineTo((x+7)*mm,8.5*mm);p.close()
        c.setFillColor(HexColor('#263d44'));c.drawPath(p,stroke=0,fill=1)
    c.restoreState()
    txt(6,h-12,'CYBER / ARENA',11,'#ffffff',True)
    txt(6,h-19,'机器人对战场',6.5,'#b7dce2')
    line(6,15,w-6,15,'#8bbdc5',.4)
    txt(w-6,19,'BATTLE FIELD',6,'#cfe7e8',right=True)
    c.showPage();c.save()
    subprocess.run(['pdftoppm','-f','1','-singlefile','-scale-to','1024','-png',str(TEMP/f'{name}.pdf'),str(ROOT/'textures'/name)],check=True,capture_output=True)
    print(name)
