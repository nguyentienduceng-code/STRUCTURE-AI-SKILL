"""Render current products to local scratch; compare without editing supplied PNGs."""
import json
import sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
AGENTS=HERE.parents[2]
sys.path.insert(0,str(AGENTS/'tools'))
from dce_virtual_drive_guard import configure_runtime,cleanup_preview
configure_runtime()
from dce_render_preview import render_dxf_to_png
from PIL import Image,ImageChops
PRODUCT=AGENTS.parent/'01_Projects/03_Sprint2_KetQua_NeChu_CAD'
records=[]
for sheet in ('KC-01','KC-02'):
    result=render_dxf_to_png(str(PRODUCT/(sheet+'_DA_NE_CHU_LeaderLine.dxf')),dpi=100,
                           view_box=(14500,33000,36500,47000))
    assert result['status']=='OK',result
    with Image.open(PRODUCT/(sheet+'_after.png')) as supplied,Image.open(result['output_png']) as rendered:
        a,b=supplied.convert('RGB'),rendered.convert('RGB')
        record={'sheet':sheet,'supplied_size':a.size,'fresh_size':b.size,'fresh_preview':result}
        if a.size==b.size:
            diff=ImageChops.difference(a,b)
            red,green,blue=diff.split()
            histogram=ImageChops.lighter(ImageChops.lighter(red,green),blue).histogram()
            record['different_pixels']=sum(histogram[1:])
            record['total_pixels']=a.width*a.height
            record['difference_bbox']=diff.getbbox()
            record['exact_pixel_match']=diff.getbbox() is None
        else:
            record['exact_pixel_match']=False
        fresh=HERE/(sheet+'_fresh_audit.png')
        b.save(fresh)
        small=b.copy();small.thumbnail((1800,1200));small.save(HERE/(sheet+'_fresh_overview.png'))
        overview=a.copy();overview.thumbnail((1800,1200));overview.save(HERE/(sheet+'_supplied_overview.png'))
        print(sheet,record.get('different_pixels'),'changed pixels',record['supplied_size'],record['fresh_size'])
        records.append(record)
    cleanup_preview(result['preview_id'])
(HERE/'preview_comparison.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
