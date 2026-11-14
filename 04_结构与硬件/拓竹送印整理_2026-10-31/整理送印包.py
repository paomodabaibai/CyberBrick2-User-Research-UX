from pathlib import Path
import zipfile, json, collections, xml.etree.ElementTree as ET, hashlib, csv, shutil, html, sys
import numpy as np

ROOT=Path(__file__).parent
SRC=Path('D:/WeChatFiles/xwechat_files/wxid_i6cwy1e36xrb22_f50d/msg/file/2026-10')
FILES=[('黑色','(黑色)通用机器人组件部分(1).3mf'),('白色','(白色)通用机器人身体部分(2).3mf'),('蓝色','(蓝色)蓝色机器人组件部分(2).3mf'),('红色','(红色)红色机器人组件部分(2).3mf')]
NS={'c':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
PROD='{http://schemas.microsoft.com/3dmanufacturing/production/2015/06}'
def md(e): return {a.get('key'):a.get('value') for a in e.findall('metadata') if a.get('key')}
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def transform(points,s):
    a=np.array([float(v) for v in (s or '1 0 0 0 1 0 0 0 1 0 0 0').split()]).reshape(4,3)
    return points@a[:3,:]+a[3,:]
def audit():
    records=[]
    for color,name in FILES:
        with zipfile.ZipFile(SRC/name) as z:
            assert z.testzip() is None
            cfg=ET.fromstring(z.read('Metadata/model_settings.config'))
            settings=json.loads(z.read('Metadata/project_settings.config'))
            obj={o.get('id'):md(o) for o in cfg.findall('object')}
            cache={}
            def verts(path,oid):
                key=(path,oid)
                if key in cache: return cache[key]
                r=ET.fromstring(z.read(path)); o=r.find("c:resources/c:object[@id='%s']"%oid,NS)
                v=o.findall('c:mesh/c:vertices/c:vertex',NS)
                if v: result=np.array([[float(n.get(k)) for k in ['x','y','z']] for n in v])
                else: result=np.vstack([transform(verts(c.get(PROD+'path',path).lstrip('/'),c.get('objectid')),c.get('transform')) for c in o.findall('c:components/c:component',NS)])
                cache[key]=result; return result
            model=ET.fromstring(z.read('3D/3dmodel.model'))
            assert model.get('unit')=='millimeter'
            instances=[]
            for b in model.findall('c:build/c:item',NS):
                oid=b.get('objectid'); info=obj[oid]
                points=transform(verts('3D/3dmodel.model',oid),b.get('transform'))
                ext=int(info.get('extruder','1'))-1
                instances.append({'object_id':oid,'name':info['name'],'printable':b.get('printable','1'),'bounds_mm':[points.min(0).round(3).tolist(),points.max(0).round(3).tolist()], 'size_mm':np.ptp(points,axis=0).round(2).tolist(),'material':settings['filament_type'][ext],'material_profile':settings['filament_settings_id'][ext],'color_hex':settings['filament_colour'][ext]})
            plates=cfg.findall('plate'); assert len(plates)==1
            plate_ids=[md(i)['object_id'] for i in plates[0].findall('model_instance')]
            assert collections.Counter(plate_ids)==collections.Counter(i['object_id'] for i in instances)
            assert all(i['printable']=='1' for i in instances)
            assert all(i['material']=='PLA' for i in instances)
            thumb=ROOT/'核查记录'/f'{color}_原装盘.png'; thumb.parent.mkdir(parents=True,exist_ok=True); thumb.write_bytes(z.read('Metadata/plate_1.png'))
            records.append({'color':color,'source':name,'sha256':digest(SRC/name),'count':len(instances),'parts':dict(collections.Counter(i['name'] for i in instances)),'instances':instances,'settings':{k:settings.get(k) for k in ['printer_model','printer_settings_id','print_settings_id','nozzle_diameter','layer_height','wall_loops','sparse_infill_density','enable_support','support_type','support_threshold_angle','curr_bed_type']},'gcode_present':any(n.endswith('.gcode') for n in z.namelist())})
    (ROOT/'核查记录'/'3mf解析记录.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps([{k:v for k,v in r.items() if k in ['color','count','parts']} for r in records],ensure_ascii=False,indent=2))
    return records

def package(pair_count):
    records=json.loads((ROOT/'核查记录'/'3mf解析记录.json').read_text(encoding='utf-8'))
    dest=ROOT/f'milk组_机器人送印包_蓝{pair_count}红{pair_count}_2026-10-31'
    dest.mkdir(exist_ok=True)
    (dest/'01_打印文件').mkdir(exist_ok=True); (dest/'02_装盘预览').mkdir(exist_ok=True)
    rows=[]; summaries=[]; hashes=[]
    for idx,r in enumerate(records,1):
        runs=1 if r['color']=='黑色' else pair_count
        filename=f'{idx:02d}_{r["color"]}_整盘打印{runs}次.3mf'
        target=dest/'01_打印文件'/filename; shutil.copy2(SRC/r['source'],target)
        assert digest(target)==r['sha256']
        hashes.append({'交付文件':filename,'原文件':r['source'],'SHA256':r['sha256']})
        shutil.copy2(ROOT/'核查记录'/f'{r["color"]}_原装盘.png',dest/'02_装盘预览'/f'{r["color"]}_原装盘.png')
        summaries.append([filename,r['color'],'PLA',r['count'],runs,r['count']*runs])
        for name,count in r['parts'].items():
            dims=next(i['size_mm'] for i in r['instances'] if i['name']==name)
            rows.append([r['color'],name,' × '.join(f'{v:g}' for v in dims),count,runs,count*runs])
    total=sum(r[-1] for r in summaries)
    text=f'''milk组桌面对战机器人｜打印委托单
日期：2026年10月31日
本次数量：蓝色巴掌机器人 {pair_count} 台＋红色拳头机器人 {pair_count} 台，共 {pair_count*2} 台。
用途：11月12日下午北京拓竹门店活动。

一、打印数量（请按“整盘次数”打印，不要再按文件名中旧的“打印1件”重复添加模型）
'''
    for f,c,mat,n,runs,qty in summaries: text+=f'{c}：{f}；每盘 {n} 件，整盘打印 {runs} 次，共 {qty} 件。\n'
    text+=f'''合计：{sum(r[-2] for r in summaries)} 个盘次，{total} 件打印件（不含支撑、裙边等辅助材料）。
黑色盘已有左眼10只＋右眼10只；只打印一盘，供 {pair_count*2} 台使用，其余 {20-pair_count*4} 只作备用。
白色盘已有两台的身体组件。蓝色盘是一台巴掌机的脚板和攻击组件。红色盘是一台拳头机的脚板、攻击组件及减速箱上下壳。
3MF原文件名末尾的(1)/(2)是收到的文件名称，不表示打印次数。

二、规格与切片
1. 材料：PLA。颜色按文件标注的白、黑、蓝、红装料。蓝、红请分别保持同一颜色；本次不要求精确色号。无需按项目中未使用的ABS/PETG耗材槽备料。
2. 单位：毫米；保持3MF内模型现有尺寸，禁止额外整体缩放或镜像。零件尺寸表为当前装盘姿态的外包尺寸，用于认件核对，不是要求修改到该尺寸。
3. 文件当前配置：Bambu Lab H2D，0.4mm喷嘴，0.20mm层高，4道墙，15%稀疏填充，纹理PEI板。以上是队友装盘文件的现有设置，未擅自修改。
4. 支撑：白、蓝、红盘已开启自动树状支撑；黑色眼睛盘未开启。请切片后检查悬空、支撑接触面及细孔/槽，必要时由打印老师调整支撑；不要封死导杆孔、螺丝孔和配合槽。
5. 如使用其他机型，请切换为实际打印机和耗材配置后重新切片。较小热床装不下时可分盘，但须保持零件尺寸与本单总数。
6. 这些是可编辑的已装盘3MF工程，不含G-code；打印时间、材料克重以老师最终切片结果为准。15%填充是现有设置，并非已验证的受力强度结论；若调整受力小件填充，请保持外形、孔位和配合尺寸。

三、交付与检查
1. 请去除支撑，清理孔口和滑动配合处；不要强行扩孔、粘合或组装。
2. 白色、黑色、蓝色、红色分别装袋；同色小件单独收好，尤其眼睛、压环、曲柄与连杆。
3. 对照“逐件数量与尺寸.csv”点数。红色减速箱上下壳已列入本次打印，不要漏掉。
4. 本包仅委托打印，不包含电子件、舵机、螺丝、铜螺母、齿轮和金属导杆采购或安装。
5. 已核对文件可解压、装盘实例数量和复制前后哈希；未在实际打印机切片，也未实物试装。请先检查切片预览，必要时先做一套试装后再完成剩余数量。

文件说明：01_打印文件是要打印的4个3MF；02_装盘预览是原工程内嵌预览，只用于认件，不代表切片验收结果；CSV可用Excel打开。
'''
    (dest/'00_给打印老师_规格与数量.txt').write_text(text,encoding='utf-8-sig')
    for fn,header,data in [('打印任务总表.csv',['文件','颜色','材料','每盘件数','整盘打印次数','合计件数'],summaries),('逐件数量与尺寸.csv',['颜色','零件名称','装盘姿态外包尺寸XYZ毫米','每盘数量','整盘次数','总数量'],rows)]:
        with (dest/fn).open('w',encoding='utf-8-sig',newline='') as f:
            w=csv.writer(f); w.writerow(header); w.writerows(data)
    def table(header,data): return '<table><thead><tr>'+''.join('<th>'+html.escape(str(c))+'</th>' for c in header)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+html.escape(str(c))+'</td>' for c in row)+'</tr>' for row in data)+'</tbody></table>'
    page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>milk组机器人打印委托单</title><style>body{font-family:"Microsoft YaHei",sans-serif;max-width:1040px;margin:36px auto;padding:0 22px;color:#183044;line-height:1.7}h1{font-size:28px}table{width:100%;border-collapse:collapse;margin:20px 0;font-size:14px}td,th{border:1px solid #cbd5df;padding:9px;text-align:left}th{background:#eef4f8}pre{white-space:pre-wrap;font-family:inherit}.photos{display:grid;grid-template-columns:1fr 1fr;gap:16px}img{width:100%;background:#eee}figure{margin:0}h2{margin-top:32px}@media print{body{margin:0}tr,figure{break-inside:avoid}}</style><h1>milk组机器人打印委托单</h1>'''
    page+=f'<p><strong>蓝色{pair_count}台＋红色{pair_count}台｜{sum(r[-2] for r in summaries)}个盘次｜{total}件</strong></p>'
    page+=table(['打印文件','颜色','材料','每盘件数','整盘次数','总件数'],summaries)
    page+='<pre>'+html.escape(text)+'</pre><h2>装盘认件预览</h2><div class="photos">'
    for r in records: page+=f'<figure><img src="02_装盘预览/{r["color"]}_原装盘.png"><figcaption>{r["color"]}盘：每盘{r["count"]}件</figcaption></figure>'
    page+='</div><h2>逐件数量与尺寸</h2>'+table(['颜色','零件','外包尺寸XYZ / mm','每盘','盘次','总数'],rows)+'</html>'
    (dest/'00_打开打印说明.html').write_text(page,encoding='utf-8')
    (dest/'文件来源与校验.json').write_text(json.dumps(hashes,ensure_ascii=False,indent=2),encoding='utf-8')
    archive=dest.with_suffix('.zip')
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(dest.rglob('*')):
            if p.is_file(): z.write(p,Path(dest.name)/p.relative_to(dest))
    with zipfile.ZipFile(archive) as z: assert z.testzip() is None
    print(json.dumps({'folder':str(dest),'archive':str(archive),'size_bytes':archive.stat().st_size,'plate_runs':sum(r[-2] for r in summaries),'parts':total},ensure_ascii=False))
if __name__=='__main__':
    if len(sys.argv)>1: package(int(sys.argv[1]))
    else: audit()
