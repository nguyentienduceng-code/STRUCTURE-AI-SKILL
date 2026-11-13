# -*- coding: utf-8 -*-
"""Universal Engineering Document Reader v3: real format fixtures + explicit dependency failures."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'.agents/tools'))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import unittest
import json
import tempfile
import shutil
import zipfile
import os
from unittest.mock import patch
import xml.etree.ElementTree as ET
import doc_reader as dr

class UniversalReaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='universal_reader_tests_')
        cls.directory = Path(cls.temp.name)
        from docx import Document
        from docx.oxml import OxmlElement
        doc = Document()
        doc.add_heading('1. LOADS', 1)
        doc.add_paragraph('q = 3.5 kN/m2; N = -250 kN; Concrete B30; 4Ø25')
        doc.add_heading('1.1 BEAM', 2)
        doc.add_heading('1.1.1 CHECK', 3)
        doc.add_paragraph('Beam D1 300x600')
        p = doc.add_paragraph('Stress = ')
        math = OxmlElement('m:oMath');fraction = OxmlElement('m:f')
        for name, value in [('num','M'),('den','W')]:
            node=OxmlElement('m:'+name);run=OxmlElement('m:r');text=OxmlElement('m:t');text.text=value
            run.append(text);node.append(run);fraction.append(node)
        math.append(fraction);p._p.append(math)
        table=doc.add_table(rows=3, cols=3)
        table.cell(0,0).text='Group';table.cell(0,1).merge(table.cell(0,2)).text='Values'
        table.cell(1,0).merge(table.cell(2,0)).text='C1'
        table.cell(1,1).text='B30';table.cell(1,2).text='300x600'
        table.cell(2,1).text='B25';table.cell(2,2).text='400x400'
        cls.docx=cls.directory/'fixture.docx';doc.save(cls.docx)
        import openpyxl
        wb=openpyxl.Workbook();ws=wb.active;ws.title='BOQ'
        ws.merge_cells('A1:F1');ws['A1']='PROJECT TITLE'
        ws.append([None]*6)
        ws.append(['STT','Description','Unit','Quantity','Unit Price','Amount'])
        ws.append([1,'Concrete B30','m3',2,4,'=D4*E4'])
        jr=wb.create_sheet('Joint Reactions');jr.append(['Joint','OutputCase','F1','F3','M2'])
        jr.append([None,None,'kN','kN','kNm']);jr.append([101,'ULS',-12.5,-250,15])
        cls.xlsx=cls.directory/'fixture.xlsx';wb.save(cls.xlsx);wb.close()
        cls.cached=cls.directory/'cached.xlsx'
        with zipfile.ZipFile(cls.xlsx) as z:
            files={n:z.read(n) for n in z.namelist()}
        namespace={'x':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
        root=ET.fromstring(files['xl/worksheets/sheet1.xml'])
        root.find(".//x:c[@r='F4']/x:v",namespace).text='8'
        files['xl/worksheets/sheet1.xml']=ET.tostring(root,encoding='utf-8',xml_declaration=True)
        with zipfile.ZipFile(cls.cached,'w',zipfile.ZIP_DEFLATED) as z:
            for name,value in files.items():z.writestr(name,value)
        cls.csv=cls.directory/'fixture.csv'
        cls.csv.write_text('PROJECT TITLE;;;;;\n\nSTT;Description;Unit;Quantity;Unit Price;Amount\n1;"Concrete; B30";m3;2;4;8\n',encoding='utf-8-sig')
        import pymupdf as fitz
        pdf=fitz.open();page=pdf.new_page(width=600,height=400)
        for y,line in [(30,'Engineering vector document with selectable text and structural details'),(60,'Concrete B30; Beam D1 300x600; q = 3.5 kN/m2')]:
            page.insert_text((20,y),line,fontsize=11)
        for x in [20,160,300]:page.draw_line((x,100),(x,190))
        for y in [100,130,160,190]:page.draw_line((20,y),(300,y))
        for y,a,b in [(120,'Joint','F3 (kN)'),(150,'101','-250'),(180,'102','-300')]:
            page.insert_text((30,y),a);page.insert_text((170,y),b)
        cls.pdf=cls.directory/'vector.pdf';pdf.save(cls.pdf);pdf.close()
        from PIL import Image,ImageDraw,ImageFont
        font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',36) if Path('C:/Windows/Fonts/arial.ttf').exists() else ImageFont.truetype('DejaVuSans.ttf',36)
        image=Image.new('RGB',(900,300),'white');draw=ImageDraw.Draw(image)
        draw.text((40,35),'ENGINEERING LOADS',font=font,fill='black');draw.text((40,110),'BEAM 300x600   B30',font=font,fill='black')
        cls.image=cls.directory/'scan.png';image.save(cls.image)
        cls.tiff=cls.directory/'scan.tiff';image.save(cls.tiff,save_all=True,append_images=[image])
        pdf=fitz.open();page=pdf.new_page();page.insert_text((30,40),'Vector page with enough engineering information to retain native text B30 300x600',fontsize=11)
        page=pdf.new_page(width=900,height=300);page.insert_image(page.rect,filename=str(cls.image))
        cls.mixed=cls.directory/'mixed.pdf';pdf.save(cls.mixed);pdf.close()
        import ezdxf
        cad=ezdxf.new('R2010');cad.layers.new('S-COLUMN');cad.layers.new('S-GRID')
        block=cad.blocks.new('COLUMN_400');block.add_lwpolyline([(0,0),(100,0),(100,200),(0,200)],close=True,dxfattribs={'layer':'0'})
        block.add_text('C1 B30 400x400',dxfattribs={'insert':(50,100),'height':20})
        outer=cad.blocks.new('ASSEMBLY');outer.add_blockref('COLUMN_400',(10,20))
        cad.modelspace().add_blockref('ASSEMBLY',(1000,2000),dxfattribs={'layer':'S-COLUMN','rotation':90})
        cad.modelspace().add_line((0,0),(1000,0),dxfattribs={'layer':'S-GRID'})
        cls.dxf=cls.directory/'fixture.dxf';cad.saveas(cls.dxf)

    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()

    def schema(self,result):
        for key in ['status','file_type','metadata','raw_text','tables','engineering_entities']:
            self.assertIn(key,result)
        self.assertEqual(set(result['engineering_entities']),{'loads','sections','rebars','materials','soils','grids','columns'})
        json.dumps(result,allow_nan=False)
        return result

    def test_word_headings_hierarchy_and_math(self):
        r=self.schema(dr.read_docx(self.docx));self.assertEqual(r['status'],'OK')
        self.assertEqual([h['level'] for h in r['headings']],[1,2,3])
        self.assertEqual(r['headings'][2]['parent_id'],r['headings'][1]['id'])
        self.assertIn('(M)/(W)',r['raw_text']);self.assertTrue(r['equations'][0]['omml'])

    def test_word_gridspan_and_vmerge(self):
        table=dr.read_docx(self.docx)['tables'][0]
        self.assertEqual(len(table['grid']),3)
        self.assertEqual(table['grid'][1][0],table['grid'][2][0])
        self.assertTrue(any(c['row_span']==2 for c in table['merged_cells']))
        self.assertTrue(any(c['col_span']==2 for c in table['merged_cells']))
        self.assertEqual(table['grid'][0],['Group','Values','Values'])

    def test_word_engineering_table_skips_title_and_extracts_signed_reactions(self):
        from docx import Document
        document = Document()
        table = document.add_table(rows=4, cols=3)
        table.cell(0, 0).merge(table.cell(0, 2)).text = 'ETABS SUPPORT RESULTS'
        for i, row in enumerate([['Joint', 'OutputCase', 'F3'],
                                 [None, None, 'kN'], ['101', 'ULS', '-250']], 1):
            for j, value in enumerate(row):
                table.cell(i, j).text = value or ''
        path = self.directory/'word_reactions.docx'
        document.save(path)
        result = self.schema(dr.read_document(path))
        extracted = result['tables'][0]
        self.assertEqual(extracted['table_type'], 'joint_reactions')
        self.assertEqual(extracted['header_index'], 1)
        self.assertEqual(extracted['rows'], [['101', 'ULS', '-250']])
        force = next(e for e in result['engineering_entities']['loads'] if e['label'] == 'F3')
        self.assertEqual((force['value'], force['unit']), (-250, 'kN'))

    def test_omml_preserves_delimiters_matrices_and_summation(self):
        namespace = dr.M_NS
        matrix = ET.fromstring(f'''<m:m xmlns:m="{namespace}"><m:mr>
            <m:e><m:r><m:t>a</m:t></m:r></m:e><m:e><m:r><m:t>b</m:t></m:r></m:e>
            </m:mr><m:mr><m:e><m:r><m:t>c</m:t></m:r></m:e>
            <m:e><m:r><m:t>d</m:t></m:r></m:e></m:mr></m:m>''')
        self.assertEqual(dr._omml_text(matrix), '[a, b; c, d]')
        expression = ET.fromstring(f'''<m:d xmlns:m="{namespace}">
            <m:dPr><m:begChr m:val="["/><m:endChr m:val="]"/></m:dPr>
            <m:e><m:nary><m:naryPr><m:chr m:val="∑"/></m:naryPr>
            <m:sub><m:r><m:t>i=1</m:t></m:r></m:sub>
            <m:sup><m:r><m:t>n</m:t></m:r></m:sup>
            <m:e><m:r><m:t>F</m:t></m:r></m:e></m:nary></m:e></m:d>''')
        self.assertEqual(dr._omml_text(expression), '[∑_(i=1)^(n)(F)]')

    def test_signed_load_and_engineering_entities(self):
        e=dr.read_document(self.docx)['engineering_entities']
        self.assertTrue(any(x['value']==-250 for x in e['loads']))
        self.assertTrue(any(x.get('grade')=='B30' for x in e['materials']))
        self.assertTrue(e['rebars'])

    def test_pdf_vector_and_structured_table(self):
        r=self.schema(dr.read_pdf(self.pdf));self.assertEqual(r['status'],'OK')
        self.assertFalse(r['metadata']['pages'][0]['scanned_candidate'])
        self.assertTrue(any(t['table_type']=='joint_reactions' for t in r['tables']))
        self.assertIn('B30',r['raw_text'])

    @unittest.skipUnless(dr._tesseract_binary(),'Tesseract native runtime not installed')
    def test_mixed_pdf_detects_and_ocrs_only_scanned_page(self):
        r=self.schema(dr.read_pdf(self.mixed,lang='eng'))
        self.assertEqual(r['status'],'OK',r['metadata']['warnings'])
        self.assertFalse(r['metadata']['pages'][0]['ocr_used'])
        self.assertTrue(r['metadata']['pages'][1]['ocr_used'])
        self.assertIn('ENGINEERING',r['raw_text'])

    def test_ocr_unavailable_preserves_other_pdf_pages(self):
        with patch.object(dr,'_run_ocr',side_effect=RuntimeError('missing native OCR')):
            r=self.schema(dr.read_pdf(self.mixed,lang='eng'))
        self.assertEqual(r['status'],'PARTIAL');self.assertIn('Vector page',r['raw_text'])
        self.assertTrue(any('OCR_UNAVAILABLE_PAGE:2' in w for w in r['metadata']['warnings']))

    def test_pymupdf_detects_scan_with_vector_header(self):
        import pymupdf as fitz
        path = self.directory/'scan_with_header.pdf'
        with fitz.open() as pdf:
            page = pdf.new_page(width=900, height=300)
            page.insert_image(page.rect, filename=str(self.image))
            page.insert_text((20, 20), 'Engineering document heading with enough selectable characters to pass the sparse threshold')
            pdf.save(path)
        recognized = {'text': 'OCR ENGINEERING BODY', 'tables': [], 'warnings': [],
                      'preprocessing': {}, 'languages': ['eng'], 'mean_word_confidence': 99}
        with patch.object(dr, '_PDF_BACKEND', 'pymupdf'), patch.object(dr, '_ocr_frame', return_value=recognized) as ocr:
            result = self.schema(dr.read_pdf(path))
        self.assertTrue(ocr.called)
        self.assertEqual(result['metadata']['backend'], 'pymupdf')
        self.assertGreater(result['metadata']['pages'][0]['image_coverage'], .9)
        self.assertTrue(result['metadata']['pages'][0]['scanned_candidate'])
        self.assertTrue(result['metadata']['pages'][0]['ocr_used'])
        self.assertIn('OCR ENGINEERING BODY', result['raw_text'])
        self.assertIn('selectable characters', result['metadata']['pages'][0]['vector_text'])

    def test_pdf_borderless_geotechnical_table(self):
        import pymupdf as fitz
        path = self.directory/'borderless_soils.pdf'
        with fitz.open() as pdf:
            page = pdf.new_page()
            for y, row in [(60, ['Layer', 'Depth(m)', 'SPT', 'Phi(deg)']),
                           (90, ['CLAY', '2.5', '8', '20']),
                           (120, ['SAND', '5.0', '25', '32'])]:
                for x, value in zip([30, 150, 270, 390], row):
                    page.insert_text((x, y), value)
            pdf.save(path)
        result = self.schema(dr.read_pdf(path, min_vector_chars=0))
        self.assertTrue(any(t['table_type'] == 'geotechnical' for t in result['tables']))
        self.assertTrue(any(s.get('layer') == 'CLAY' and s.get('SPT_N') == 8
                            for s in result['engineering_entities']['soils']))

    def test_excel_detects_header_below_merged_title(self):
        r=self.schema(dr.read_xlsx(self.cached));self.assertEqual(r['status'],'OK')
        table=next(t for t in r['tables'] if t['sheet']=='BOQ')
        self.assertEqual(table['header_row'],3);self.assertEqual(table['table_type'],'boq')
        self.assertEqual(table['rows'][0][5],8);self.assertEqual(table['formula_rows'][0][5],'=D4*E4')
        self.assertEqual(table['row_numbers'],[4])

    def test_excel_missing_cache_not_fabricated(self):
        r=dr.read_xlsx(self.xlsx);self.assertEqual(r['status'],'PARTIAL')
        self.assertIn('BOQ!F4',r['metadata']['missing_formula_cache'])
        self.assertIsNone(r['metadata']['formula_cells'][0]['cached_value'])

    def test_excel_joint_reactions_units_and_signs(self):
        r=dr.read_xlsx(self.cached)
        t=next(t for t in r['tables'] if t['table_type']=='joint_reactions')
        self.assertEqual(t['row_numbers'],[3]);self.assertTrue(t['unit_row'])
        force=next(x for x in r['engineering_entities']['loads'] if x['label']=='F3')
        self.assertEqual(force['value'],-250);self.assertEqual(force['unit'],'kN')
        self.assertEqual(force['joint'],101);self.assertEqual(force['case'],'ULS')

    def test_csv_delimiter_bom_and_quoted_cells(self):
        r=self.schema(dr.read_document(self.csv));self.assertEqual(r['file_type'],'CSV')
        self.assertEqual(r['tables'][0]['table_type'],'boq')
        self.assertEqual(r['tables'][0]['rows'][0][1],'Concrete; B30')

    def test_csv_quoted_multiline_is_preserved(self):
        p=self.directory/'multiline.csv';p.write_text('Joint,F3\n101,"first\nsecond"\n',encoding='utf-8')
        r=dr.read_xlsx(p);self.assertEqual(r['tables'][0]['rows'][0][1],'first\nsecond')

    def test_xls_binary_cached_fallback_is_explicit(self):
        import xlwt
        wb=xlwt.Workbook();ws=wb.add_sheet('BOQ')
        for i,row in enumerate([['Description','Quantity','Unit Price'],['Concrete',2,4]]):
            for j,value in enumerate(row):ws.write(i,j,value)
        p=self.directory/'legacy.xls';wb.save(str(p))
        with patch.object(dr,'_office_converter_available',return_value=False):r=self.schema(dr.read_xlsx(p))
        self.assertEqual(r['status'],'PARTIAL');self.assertEqual(r['tables'][0]['rows'][0][1],2)
        self.assertTrue(any('XLS_FORMULAS_UNAVAILABLE' in w for w in r['metadata']['warnings']))

    @unittest.skipUnless(dr._tesseract_binary(),'Tesseract native runtime not installed')
    def test_image_real_ocr(self):
        r=self.schema(dr.read_image_ocr(self.image,lang='eng'))
        self.assertEqual(r['status'],'OK');self.assertIn('ENGINEERING',r['raw_text'])
        self.assertEqual(r['metadata']['pages'][0]['preprocessing']['binarization'],'OTSU')

    @unittest.skipUnless(dr._tesseract_binary(),'Tesseract native runtime not installed')
    def test_multiframe_tiff_real_ocr(self):
        r=self.schema(dr.read_image_ocr(self.tiff,lang='eng'))
        self.assertEqual(r['metadata']['page_count'],2);self.assertEqual(r['status'],'OK')

    def test_multiframe_tiff_preserves_successful_pages_on_ocr_failure(self):
        recognized = {'text': 'ENGINEERING B30', 'tables': [], 'warnings': [], 'words': [],
                      'preprocessing': {}, 'languages': ['eng'], 'mean_word_confidence': 99}
        with patch.object(dr, '_ocr_frame', side_effect=[recognized, RuntimeError('page timeout')]):
            result = self.schema(dr.read_image_ocr(self.tiff))
        self.assertEqual(result['status'], 'PARTIAL')
        self.assertIn('ENGINEERING B30', result['raw_text'])
        self.assertEqual(result['metadata']['page_count'], 2)
        self.assertEqual(result['metadata']['pages'][1]['ocr_error'], 'page timeout')

    def test_excel_cached_formula_error_is_reported(self):
        path = self.directory/'cached_error.xlsx'
        with zipfile.ZipFile(self.cached) as archive:
            files = {name: archive.read(name) for name in archive.namelist()}
        ns = {'x': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
        root = ET.fromstring(files['xl/worksheets/sheet1.xml'])
        cell = root.find(".//x:c[@r='F4']", ns)
        cell.set('t', 'e')
        cell.find('x:v', ns).text = '#DIV/0!'
        files['xl/worksheets/sheet1.xml'] = ET.tostring(root, encoding='utf-8')
        with zipfile.ZipFile(path, 'w') as archive:
            for name, value in files.items():
                archive.writestr(name, value)
        result = self.schema(dr.read_xlsx(path))
        self.assertEqual(result['status'], 'PARTIAL')
        self.assertTrue(any('EXCEL_ERROR:BOQ:4:6:#DIV/0!' in w for w in result['metadata']['warnings']))
        self.assertEqual(result['metadata']['formula_cells'][0]['formula'], '=D4*E4')

    def test_preprocessing_deskews_table_lines(self):
        from PIL import Image,ImageDraw
        image=Image.new('RGB',(800,400),'white');draw=ImageDraw.Draw(image)
        for y in (70,150,230):draw.line((70,y,730,y),fill='black',width=3)
        processed,meta=dr._preprocess_image(image.rotate(6,expand=True,fillcolor='white'))
        self.assertTrue(3<abs(meta['deskew_degrees'])<9,meta)
        self.assertEqual(processed.mode,'L')

    def test_ocr_grid_table_geometry(self):
        from PIL import Image,ImageDraw
        image=Image.new('L',(800,300),255);draw=ImageDraw.Draw(image)
        for x in (40,350,700):draw.line((x,20,x,260),fill=0,width=3)
        for y in (20,100,180,260):draw.line((40,y,700,y),fill=0,width=3)
        words=[{'text':t,'left':x,'top':y,'width':80,'height':25,'confidence':99}
               for t,x,y in [('Joint',70,40),('F3',400,40),('101',70,120),('250',400,120),('102',70,200),('300',400,200)]]
        tables=dr._ocr_tables(image,words,1)
        self.assertEqual(tables[0]['structure'],'raster_grid')
        self.assertEqual(tables[0]['rows'][0],['101','250'])

    def test_missing_image_backend_reports_error(self):
        with patch.object(dr,'_tesseract_binary',return_value=None):r=self.schema(dr.read_image_ocr(self.image))
        self.assertEqual(r['status'],'ERROR');self.assertIn('Tesseract',r['error'])

    def test_cad_text_grids_and_nested_wcs_columns(self):
        r=self.schema(dr.read_dxf(self.dxf));self.assertEqual(r['status'],'OK',r.get('error'))
        self.assertIn('C1',r['raw_text']);self.assertTrue(r['engineering_entities']['grids'])
        columns=[c for c in r['engineering_entities']['columns'] if c['entity_type']=='LWPOLYLINE']
        self.assertTrue(columns,r['metadata'])
        self.assertEqual([round(v,3) for v in columns[0]['points_wcs'][0]],[980,2010,0])
        self.assertEqual(columns[0]['coordinate_system'],'WCS')

    def test_dwg_routes_through_native_bridge_without_mutating_input(self):
        original=self.directory/'stub.dwg';original.write_bytes(b'AC1032 test fixture bridge contract')
        before=original.read_bytes();parser=dr._load_cad_parser()
        def convert(source,output_dxf):
            self.assertNotEqual(Path(source),original);self.assertEqual(Path(source).read_bytes(),before)
            shutil.copy2(self.dxf,output_dxf);return output_dxf
        with patch.object(parser.DWGHeadlessBridge,'convert_dwg_to_dxf',side_effect=convert) as bridge:
            r=self.schema(dr.read_document(original))
        self.assertEqual(r['file_type'],'DWG');self.assertEqual(r['status'],'OK')
        self.assertEqual(original.read_bytes(),before);self.assertTrue(bridge.called)

    def test_native_dwg_missing_converter_is_explicit(self):
        p=self.directory/'missing-engine.dwg';p.write_bytes(b'AC1032')
        with patch.object(dr._load_cad_parser().DWGHeadlessBridge,'convert_dwg_to_dxf',side_effect=RuntimeError('No DWG converter')):
            r=self.schema(dr.read_document(p))
        self.assertEqual(r['status'],'ERROR');self.assertIn('No DWG converter',r['error'])

    def test_legacy_doc_routes_to_converter(self):
        p=self.directory/'stub.doc';p.write_bytes(b'legacy binary contract')
        def convert(source,directory,kind):
            self.assertEqual(kind,'docx');target=Path(directory)/'converted.docx';shutil.copy2(self.docx,target);return target
        with patch.object(dr,'_convert_office',side_effect=convert):r=self.schema(dr.read_document(p))
        self.assertEqual(r['file_type'],'DOC');self.assertIn('(M)/(W)',r['raw_text'])

    def test_corrupt_and_missing_inputs_return_common_schema(self):
        for name in ['missing.pdf','bad.docx','bad.xlsx','bad.dxf']:
            p=self.directory/name
            if not name.startswith('missing'):p.write_bytes(b'not a document')
            with self.subTest(name=name):
                self.assertEqual(self.schema(dr.read_document(p))['status'],'ERROR')

    def test_json_schema_for_every_family(self):
        for p in [self.docx,self.pdf,self.cached,self.csv,self.dxf]:
            with self.subTest(path=p.name):self.schema(dr.read_document(p))

    def test_scan_directory_includes_images(self):
        r=dr.scan_project_directory(str(self.directory),recursive=False)
        self.assertTrue(r['summary']['hinh_anh']>=2)

    def test_headerless_numeric_csv_keeps_first_row(self):
        p=self.directory/'numeric.csv';p.write_text('1,2\n3,4\n',encoding='utf-8')
        table=dr.read_xlsx(p)['tables'][0]
        self.assertTrue(table['header_inferred']);self.assertEqual(table['rows'],[['1','2'],['3','4']])

    def test_zero_formula_cache_is_not_missing(self):
        p=self.directory/'zero.xlsx'
        with zipfile.ZipFile(self.cached) as z:files={name:z.read(name) for name in z.namelist()}
        ns={'x':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
        root=ET.fromstring(files['xl/worksheets/sheet1.xml']);root.find(".//x:c[@r='F4']/x:v",ns).text='0'
        files['xl/worksheets/sheet1.xml']=ET.tostring(root,encoding='utf-8')
        with zipfile.ZipFile(p,'w') as z:
            for name,value in files.items():z.writestr(name,value)
        r=dr.read_xlsx(p);self.assertEqual(r['status'],'OK')
        self.assertEqual(r['metadata']['formula_cells'][0]['cached_value'],0)
        self.assertFalse(r['metadata']['missing_formula_cache'])

    def test_geotechnical_table_entities(self):
        p=self.directory/'soil.csv';p.write_text('Layer,Depth,SPT,Phi\nCLAY,2.5,8,20\n',encoding='utf-8')
        r=dr.read_document(p);self.assertEqual(r['tables'][0]['table_type'],'geotechnical')
        self.assertTrue(any(s.get('SPT_N')==8 and s.get('depth')==2.5 for s in r['engineering_entities']['soils']))

    def test_multiline_soil_header_preserves_angle_units(self):
        p=self.directory/'soil_multiline.csv'
        p.write_text('Layer,Depth(m),"N\nSPT",Phi(rad)\nCLAY,2.5,8,0.35\n',encoding='utf-8')
        r=dr.read_document(p);soil=next(v for v in r['engineering_entities']['soils'] if v.get('layer')=='CLAY')
        self.assertEqual(soil['SPT_N'],8);self.assertEqual(soil['phi'],0.35)
        self.assertEqual(soil['units']['phi'],'rad');self.assertNotIn('phi_deg',soil)

    def test_year_and_force_are_not_pile_or_spt(self):
        data,_=dr._extract_engineering_data('Report 2026; N = 250 kN; slab h=150mm; pile D600')
        self.assertFalse(any(s.get('diameter_mm')==2026 for s in data['sections']))
        self.assertFalse(any(s.get('SPT_N')==250 for s in data['soil_params']))
        self.assertTrue(any(s.get('thickness_mm')==150 for s in data['sections']))

    @unittest.skipUnless(dr._tesseract_binary(),'Tesseract native runtime not installed')
    def test_jpeg_uses_ocr_dispatch(self):
        from PIL import Image
        p=self.directory/'photo.jpeg'
        with Image.open(self.image) as image:image.save(p,quality=95)
        r=self.schema(dr.read_document(p,ocr_lang='eng'))
        self.assertEqual(r['file_type'],'JPEG');self.assertIn('ENGINEERING',r['raw_text'])

    @unittest.skipUnless(dr._tesseract_binary(),'Tesseract native runtime not installed')
    def test_raster_grid_real_ocr(self):
        from PIL import Image,ImageDraw,ImageFont
        image=Image.new('RGB',(800,300),'white');draw=ImageDraw.Draw(image)
        font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',32) if Path('C:/Windows/Fonts/arial.ttf').exists() else ImageFont.truetype('DejaVuSans.ttf',32)
        for x in (40,350,700):draw.line((x,20,x,260),fill='black',width=3)
        for y in (20,100,180,260):draw.line((40,y,700,y),fill='black',width=3)
        for text,x,y in [('Joint',70,40),('F3',400,40),('101',70,120),('250',400,120),('102',70,200),('300',400,200)]:draw.text((x,y),text,font=font,fill='black')
        p=self.directory/'table.png';image.save(p)
        r=dr.read_image_ocr(p,lang='eng');self.assertEqual(r['status'],'OK')
        self.assertEqual(r['tables'][0]['structure'],'raster_grid')
        self.assertIn('250',r['tables'][0]['rows'][0])

    def test_legacy_xls_conversion_failure_retains_cached_values(self):
        import xlwt
        p=self.directory/'fallback.xls';book=xlwt.Workbook();sheet=book.add_sheet('Table')
        for i,row in enumerate([['Name','Value'],['A',5]]):
            for j,value in enumerate(row):sheet.write(i,j,value)
        book.save(str(p))
        with patch.object(dr,'_office_converter_available',return_value=True), patch.object(dr,'_convert_office',side_effect=RuntimeError('converter unavailable')):
            r=dr.read_xlsx(p)
        self.assertEqual(r['status'],'PARTIAL');self.assertTrue(r['tables'])
        self.assertTrue(any('XLS_OFFICE_CONVERSION_FAILED' in w for w in r['metadata']['warnings']))


@unittest.skipUnless(os.environ.get('UNIVERSAL_READER_NATIVE_FIXTURE_DIR'),'Set native fixture directory to run licensed Office/AutoCAD integration')
class NativeConverterIntegration(unittest.TestCase):
    def test_native_binary_doc(self):
        p=Path(os.environ['UNIVERSAL_READER_NATIVE_FIXTURE_DIR'])/'native_fixture.doc'
        r=dr.read_document(p);self.assertIn(r['status'],['OK','PARTIAL'],r.get('error'))
        self.assertIn('LOADS',r['raw_text']);self.assertEqual(len(r['headings']),3)
        self.assertTrue(r['equations'] or any('LEGACY_DOC_GRAPHICS_NOT_OCR' in w for w in r['metadata']['warnings']))

    def test_native_binary_xls_with_formula(self):
        p=Path(os.environ['UNIVERSAL_READER_NATIVE_FIXTURE_DIR'])/'native_fixture.xls'
        r=dr.read_document(p);self.assertEqual(r['status'],'OK',r.get('error'))
        self.assertEqual(r['metadata']['formula_cells'][0]['formula'],'=B2*C2')
        self.assertEqual(r['metadata']['formula_cells'][0]['cached_value'],8)

    def test_native_binary_dwg_wcs(self):
        p=Path(os.environ['UNIVERSAL_READER_NATIVE_FIXTURE_DIR'])/'native_fixture.dwg'
        original=p.read_bytes();r=dr.read_document(p)
        self.assertEqual(r['status'],'OK',r.get('error'))
        self.assertTrue(r['engineering_entities']['columns']);self.assertTrue(r['engineering_entities']['grids'])
        self.assertEqual(p.read_bytes(),original)

if __name__=='__main__':unittest.main(verbosity=2)
