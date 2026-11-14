import fs from 'node:fs';
import path from 'node:path';
import {LibreDwg,Dwg_File_Type} from './node_modules/@mlightcad/libredwg-web/dist/libredwg-web.js';
const output='G:/My Drive/Google AI Studio/.agents/memory/audits/dce_round2_20261114';
fs.mkdirSync(output,{recursive:true});
const reader=await LibreDwg.create('C:/Users/ADMIN/AppData/Local/Temp/dce_round2_dwg_tools/node_modules/@mlightcad/libredwg-web/wasm/');
for(const name of fs.readdirSync('C:/Dce Pro/Cad').filter(n=>/^Form .*\.dwg$/i.test(n))){
  const src=path.join('C:/Dce Pro/Cad',name);
  try{
    const ptr=reader.dwg_read_data(new Uint8Array(fs.readFileSync(src)),Dwg_File_Type.DWG);
    const db=reader.convert(ptr);
    fs.writeFileSync(path.join(output,name+'.json'),JSON.stringify(db,(_,v)=>typeof v==='bigint'?v.toString():v));
    console.log(name,Object.keys(db));
    reader.dwg_free(ptr);
  }catch(e){ console.log('FAILED',name,String(e)); }
}
