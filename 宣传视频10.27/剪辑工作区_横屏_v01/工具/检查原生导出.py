from pathlib import Path
import json,subprocess,io
from PIL import Image,ImageDraw,ImageFont
W=Path(__file__).resolve().parents[1]; movie=W/'06_预览/棋甲对决_横屏粗剪_v02_达芬奇原生导出.mp4'
shots=json.loads((W/'03_剪辑方案/横屏60秒_剪辑清单.json').read_text('utf8'))
c=Image.new('RGB',(1600,4*275),'#eeeeee');d=ImageDraw.Draw(c);font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',17)
for i,s in enumerate(shots):
 sec=s['record_in']+s['duration']/2
 b=subprocess.check_output(['ffmpeg','-v','error','-ss',str(sec),'-i',str(movie),'-frames:v','1','-vf','scale=400:225','-f','image2pipe','-vcodec','mjpeg','-'])
 im=Image.open(io.BytesIO(b));c.paste(im,((i%4)*400,(i//4)*275+42));d.text(((i%4)*400+5,(i//4)*275+5),f'{i+1:02} {sec:.1f}s '+s['title'],font=font,fill='black')
c.save(W/'06_预览/Resolve_v02_全片16段检查.jpg')
