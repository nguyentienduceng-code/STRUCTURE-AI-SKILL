import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
import json, pathlib, collections, hashlib
import ezdxf
from ezdxf import bbox

BASE = pathlib.Path(r'G:\My Drive\Google AI Studio\01_Projects\03_Sprint2_KetQua_NeChu_CAD')
def box(e):
    try:
        b=bbox.extents([e]); return [float(b.extmin.x),float(b.extmin.y),float(b.extmax.x),float(b.extmax.y)] if b.has_data else None
    except Exception: return None
def overlap(a,b): return a and a[0]<b[2] and a[2]>b[0] and a[1]<b[3] and a[3]>b[1]
def rect(e):
    if e.dxftype()!='LWPOLYLINE': return None
    p=list(e.get_points('xy')); return [min(x for x,y in p),min(y for x,y in p),max(x for x,y in p),max(y for x,y in p)]
out={}
for p in sorted(BASE.glob('KC-0*v50_DA_SUA_KHUNG.dxf')):
    d=ezdxf.readfile(p); m=d.modelspace(); E=list(m)
    frames=[rect(e) for e in E if e.dxf.layer=='DCE_Frame' and rect(e)]
    frames.sort(key=lambda b:(b[2]-b[0])*(b[3]-b[1]),reverse=True)
    outer,inner,title=frames[:3]
    schedules=[rect(e) for e in E if e.dxf.layer in ('DCE_Schedule','DCE_Note') and rect(e)]
    title_hits=[(e.dxftype(),e.dxf.layer,e.dxf.handle) for e in E if e.dxf.layer!='DCE_Frame' and e.dxftype() in ('LINE','TEXT','DIMENSION') and overlap(box(e),title)]
    axes=[e for e in E if e.dxf.layer=='DCE_Truc' and e.dxftype()=='LINE']
    axis_title=[(e.dxf.handle,box(e)) for e in axes if overlap(box(e),title)]
    schedule_hits=[(e.dxf.handle,box(e)) for e in axes if any(overlap(box(e),s) for s in schedules)]
    plan=[(e,box(e)) for e in E if e.dxf.layer in ('DCE_Dim','DCE_Truc','DCE_BaoBeTong','DCE_Block','DCE_Name')]
    rightmost=max((b[2],e.dxf.handle,e.dxf.layer) for e,b in plan if b)
    dims=list(m.query('DIMENSION')); hatches=list(m.query('HATCH'))
    texts=[e for e in E if e.dxftype() in ('TEXT','MTEXT','ATTRIB','ATTDEF')]
    texts += [a for i in m.query('INSERT') for a in i.attribs]
    bad=[]; titles=[]; white=[]
    for e in texts:
        color=e.dxf.get('color',256); rgb=e.dxf.get('true_color',None); val=e.dxf.get('text','')
        if color==2 or rgb in (0xFFFFFF,0xFFFF00,0x7FFF00,0xADFF2F): bad.append((e.dxf.handle,color,rgb,val[:35]))
        if rgb==0xFFFFFF: white.append(e.dxf.handle)
        if 'TYPICAL FLOOR' in val.upper(): titles.append((e.dxf.handle,color,rgb,val[:60]))
    inserts=list(m.query('INSERT'))
    attribs=sum(len(i.attribs) for i in inserts)
    r=dict(sha256=hashlib.sha256(p.read_bytes()).hexdigest(),entities=len(E),outer=outer,inner=inner,title=title,
      margins=[inner[0]-outer[0],inner[1]-outer[1],outer[2]-inner[2],outer[3]-inner[3]],
      schedules=schedules,title_hits=title_hits,axis_title_hits=axis_title,schedule_axis_hits=schedule_hits,
      axes=[(e.dxf.handle,tuple(e.dxf.start)[:2],tuple(e.dxf.end)[:2]) for e in axes],
      dimensions=len(dims),dimstyles=dict(collections.Counter(e.dxf.dimstyle for e in dims)),
      hatches=len(hatches),hatch_specs={str(k):v for k,v in collections.Counter((e.dxf.layer,e.dxf.color,e.dxf.pattern_name) for e in hatches).items()},
      inserts=len(inserts),attribs=attribs,attdefs=sum(1 for b in d.blocks for e in b if e.dxftype()=='ATTDEF'),
      text_count=len(texts),bad_text=bad,white_text=white,titles=titles,
      axis11_title_vertical_gap=min(min(float(e.dxf.start.y),float(e.dxf.end.y))-title[3] for e in axes if abs(float(e.dxf.start.x)-78200)<1),
      axis11_schedule_horizontal_gap=min(s[0]-78200 for s in schedules),
      plan_rightmost=rightmost,plan_sidebar_gap=min(s[0] for s in schedules)-rightmost[0],
      entity_types=dict(collections.Counter(e.dxftype() for e in E)))
    out[p.name]=r
print(json.dumps(out,ensure_ascii=False,indent=2,default=str))
