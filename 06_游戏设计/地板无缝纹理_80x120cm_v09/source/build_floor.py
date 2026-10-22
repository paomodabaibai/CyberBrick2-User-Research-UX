"""Build dimensionally exact repeating print layouts; generated raster stays unchanged.

Only ReportLab PDF composition is performed here. PNG previews are rendered from PDFs
with Poppler separately, so the artwork and print proofs share the same source.
"""
from pathlib import Path
import json
from math import floor, ceil
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT = Path(__file__).resolve().parents[1]
TEMP = Path(r'E:\CodexData\Scratch\cyber-floor-20261019')
TEMP.mkdir(parents=True, exist_ok=True)
PRINT = ROOT / 'print'
IMG = ROOT / 'source' / '青蓝金属材质_imagegen原图.png'
pdfmetrics.registerFont(TTFont('CJK', r'C:\Windows\Fonts\msyh.ttc', subfontIndex=0))
pdfmetrics.registerFont(TTFont('CJKB', r'C:\Windows\Fonts\msyhbd.ttc', subfontIndex=0))
BASE = '#284955'
GRID = '#4a6d77'
CYAN = '#8bbdc5'
YELLOW = '#f0be50'
INK = '#284955'
MUTED = '#5d747b'

def rect(c,x,y,w,h,color):
    c.setFillColor(HexColor(color)); c.rect(x*mm,y*mm,w*mm,h*mm,stroke=0,fill=1)

def line(c,x1,y1,x2,y2,color,width=.15):
    c.setStrokeColor(HexColor(color)); c.setLineWidth(width*mm)
    c.line(x1*mm,y1*mm,x2*mm,y2*mm)

def text(c,x,y,s,size=9,color=INK,bold=False,align='left'):
    c.setFont('CJKB' if bold else 'CJK',size);c.setFillColor(HexColor(color))
    getattr(c,{'left':'drawString','center':'drawCentredString','right':'drawRightString'}[align])(x*mm,y*mm,s)

def init(c):
    """A 100 mm panel has a constant 1 mm boundary ring on every side.
    Every continuation edge contains the same paint color; nothing crosses that ring.
    The 200 mm master is four identical panels. No mirrored pixel manipulation.
    """
    c.setTitle('CYBER ARENA | Repeating floor | 80 x 120 cm')
    c.setAuthor('CyberBrick / milk')
    c.beginForm('panel',0,0,100*mm,100*mm)
    rect(c,0,0,100,100,BASE)
    c.saveState()
    p=c.beginPath();p.roundRect(1*mm,1*mm,98*mm,98*mm,.8*mm)
    c.clipPath(p,stroke=0,fill=0)
    c.drawImage(str(IMG),1*mm,1*mm,98*mm,98*mm,mask='auto')
    c.restoreState()
    # Fine engineering lines; quarter-period intersections align within each plate.
    for q in (25,50,75):
        line(c,q,1.6,q,98.4,GRID,.13)
        line(c,1.6,q,98.4,q,GRID,.13)
    c.setStrokeColor(HexColor('#416570'));c.setLineWidth(.17*mm)
    c.roundRect(1.35*mm,1.35*mm,97.3*mm,97.3*mm,.6*mm,stroke=1,fill=0)
    # Quiet etched corner brackets and printed fasteners, not physical obstacles.
    for x,y,sx,sy in ((5,5,1,1),(95,5,-1,1),(5,95,1,-1),(95,95,-1,-1)):
        line(c,x,y,x+sx*3,y,'#60848d',.2)
        line(c,x,y,x,y+sy*3,'#60848d',.2)
        c.setFillColor(HexColor(BASE));c.circle((x+sx*2)*mm,(y+sy*2)*mm,.55*mm,stroke=0,fill=1)
        line(c,x+sx*2-.22,y+sy*2,x+sx*2+.22,y+sy*2,'#6d8f97',.12)
    # Very small, symmetric warm accents connect to the existing wall graphics.
    for x in (46.4,50.4):
        rect(c,x,3.4,3.2,.65,YELLOW)
        rect(c,x,95.95,3.2,.65,YELLOW)
    for y in (46.4,50.4):
        rect(c,3.4,y,.65,3.2,YELLOW)
        rect(c,95.95,y,.65,3.2,YELLOW)
    c.endForm()

def field(c,x,y,w,h,phase_x=0,phase_y=0):
    """Infinite periodic field, clipped to a viewport; used for true bleed too."""
    c.saveState()
    p=c.beginPath();p.rect(x*mm,y*mm,w*mm,h*mm);c.clipPath(p,stroke=0,fill=0)
    for i in range(floor(phase_x/100),ceil((phase_x+w)/100)):
        for j in range(floor(phase_y/100),ceil((phase_y+h)/100)):
            c.saveState();c.translate((x+i*100-phase_x)*mm,(y+j*100-phase_y)*mm)
            c.doForm('panel');c.restoreState()
    c.restoreState()

def scale_bar(c,x,y):
    line(c,x,y,x+100,y,INK,.24)
    for t in (0,50,100):line(c,x+t,y-1.1,x+t,y+1.1,INK,.22)
    text(c,x+50,y-5,'此线必须量得 100 mm',7.5,MUTED,align='center')

def base_pdf(path,w,h):
    c=canvas.Canvas(str(path),pagesize=(w*mm,h*mm),pageCompression=1)
    init(c);return c

def marks_a3(c,x,y,w,h):
    # Side marks fit within the typical 5 mm unprintable margin on A3.
    for yy in (y,y+h):
        line(c,5,yy,6.5,yy,INK,.17)
        line(c,413.5,yy,415,yy,INK,.17)
    for xx in (x,x+w):
        line(c,xx,y-7,xx,y-3.5,INK,.17)
        line(c,xx,y+h+3.5,xx,y+h+7,INK,.17)
    for yy,sign in ((y,-1),(y+h,1)):
        line(c,x+200,yy+sign*3.5,x+200,yy+sign*7,INK,.17)

def a3():
    c=base_pdf(PRINT/'01_A3双拼_打印12张_每张40x20cm.pdf',420,297)
    text(c,10,282,'CYBER / ARENA',17,bold=True)
    text(c,410,283,'A3 · 横向 · 实际大小 100%',10,align='right')
    text(c,10,273,'四边连续地板 / 80 × 120 cm',9,MUTED)
    text(c,410,273,'本页打印 12 张；净尺寸 400 × 200 mm；四边出血 3 mm',9,MUTED,align='right')
    x,y=10,48.5
    field(c,x-3,y-3,406,206,-3,-3);marks_a3(c,x,y,400,200)
    text(c,210,258,'中间两处短线：需要 20 × 20 cm 方块时，连接上下定位点裁开',8,MUTED,align='center')
    text(c,10,33,'沿外侧裁切标记取净幅；出血切掉；两张并排、六排铺满。',9,bold=True)
    text(c,10,26,'先测校准线，再裁切。关闭“适合页面”及“多页合一”；薄哑面纸，平接不搭接。',8.5,MUTED)
    scale_bar(c,10,15)
    text(c,410,14,'图案没有固定墙位，可按已完成隔断裁开适配。',8,MUTED,align='right')
    c.showPage();c.save()

def a4():
    c=base_pdf(PRINT/'02_A4单块_打印24张_每张20x20cm.pdf',210,297)
    text(c,10,282,'CYBER / ARENA',15,bold=True)
    text(c,200,283,'A4 · 实际大小 100%',8.5,align='right')
    text(c,10,272,'本页打印 24 张 / 裁后 200 × 200 mm / 4 列 × 6 行',8.5,MUTED)
    x,y=5,53
    field(c,x,y,200,200)
    # Width is already 200 mm. Do not put horizontal crop marks into printer margins.
    for xx in (x,x+200):
        line(c,xx,y-4,xx,y-.7,INK,.17)
        line(c,xx,y+200+.7,xx,y+204,INK,.17)
    text(c,105,262,'按图案外缘裁切；上、下短线辅助确定左右裁线',7.5,MUTED,align='center')
    text(c,10,41,'此版无出血，打印机可打印宽度须至少 200 mm。',8.5,bold=True)
    text(c,10,33,'边缘若被截断，请用 A3 版；不要缩小页面。',8.5,MUTED)
    text(c,10,25,'每张保持相同朝向，薄纸平接；关闭“适合页面”。',8.5,MUTED)
    scale_bar(c,10,14)
    c.showPage();c.save()

def masters():
    p=PRINT/'03_整幅80x120cm_实尺打印.pdf'
    c=base_pdf(p,800,1200);field(c,0,0,800,1200);c.showPage();c.save()
    c=base_pdf(TEMP/'tile_200mm.pdf',200,200);field(c,0,0,200,200);c.showPage();c.save()
    c=base_pdf(TEMP/'proof_400mm.pdf',400,400);field(c,0,0,400,400);c.showPage();c.save()

def preview():
    c=base_pdf(TEMP/'preview.pdf',360,270)
    rect(c,0,0,360,270,'#edf2f1')
    text(c,16,248,'CYBER / ARENA',23,bold=True)
    text(c,16,237,'与现有墙贴同色系的四边连续地板',11,MUTED)
    c.saveState();c.translate(16*mm,56*mm);c.scale(.205,.205)
    field(c,0,0,1200,800)
    c.restoreState()
    text(c,16,46,'120 × 80 cm 全场效果 · 无固定墙位 · 可按现有隔断裁切',8.5,MUTED)
    text(c,278,211,'20 × 20 cm',15,bold=True)
    text(c,278,201,'循环基础块',9,MUTED)
    c.saveState();c.translate(278*mm,131*mm);c.scale(.33,.33)
    field(c,0,0,200,200);c.restoreState()
    text(c,278,116,'A3  /  12 张',11,bold=True)
    text(c,278,106,'每张裁为 40 × 20 cm',8.5,MUTED)
    text(c,278,89,'A4  /  24 张',11,bold=True)
    text(c,278,79,'每张裁为 20 × 20 cm',8.5,MUTED)
    text(c,278,62,'四边周期一致',10,bold=True)
    text(c,278,52,'印前先核对 100 mm 标尺',8.5,MUTED)
    line(c,16,34,344,34,'#c5d3d4',.2)
    text(c,16,22,'深青蓝金属微纹理 / 25 mm 工程格线 / 克制的警示黄',9,MUTED)
    text(c,344,22,'预览图，打印请使用实尺 PDF',8,MUTED,align='right')
    c.showPage();c.save()

if __name__=='__main__':
    a3();a4();masters();preview()
    manifest={
      'map_mm':[800,1200], 'master_tile_mm':[200,200], 'panel_period_mm':100,
      'grid_pitch_mm':25, 'image_native_px':[1254,1254], 'image_placed_mm':[98,98],
      'image_effective_ppi':round(1254/98*25.4,2),
      'A3':{'page_mm':[420,297],'trim_rect_mm':[10,48.5,400,200],'bleed_mm':3,'copies':12,'layout':[2,6]},
      'A4':{'page_mm':[210,297],'trim_rect_mm':[5,53,200,200],'bleed_mm':0,'copies':24,'layout':[4,6],'minimum_printable_width_mm':200},
      'print_scale_percent':100,
      'seam_method':'Generated texture contained within periodic vector panels; 1 mm constant boundary per panel edge; geometry repeats every 100 mm on both axes.',
      'scope':'New 800 x 1200 mm floor only. Existing partitions already built; no placement or dimension changes.',
      'color_reference':'v07 wall artwork: #284955, #3b5e68, #f0be50, #8bbdc5',
      'generation':'Built-in imagegen for material texture, ReportLab for exact periodic layout, Poppler for PDF rendering.'
    }
    (ROOT/'source'/'打印尺寸清单.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(manifest,ensure_ascii=False,indent=2))
