// Native editable diagrams/tables, authored with the bundled Artifact Tool.
import fs from 'node:fs/promises';
import path from 'node:path';
import {createRequire} from 'node:module';
import {pathToFileURL} from 'node:url';
import {spawnSync} from 'node:child_process';
const root=process.cwd();
const buildDir=path.join(root,'.ppt_build/after_audit');
process.env.RUNTIME_NODE_MODULES ||= await fs.realpath(path.join(buildDir,'node_modules'));
process.env.RUNTIME_NODE ||= process.execPath;
const require=createRequire(path.join(buildDir,'runtime.cjs'));
const {Presentation,PresentationFile}=await import(pathToFileURL(require.resolve('@oai/artifact-tool')).href);
const skill=process.env.CYCLETWIN_PRESENTATION_SKILL || '/Users/kushagragupta/.codex/plugins/cache/openai-primary-runtime/presentations/26.1015.12040/skills/presentations';
const runtimePython=process.env.CYCLETWIN_BUILD_PYTHON || '/Users/kushagragupta/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3';
const {finalizePresentation}=await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')).href);
const claims=JSON.parse(await fs.readFile(path.join(root,'docs/claims.json'),'utf8'));
const revision=Date.now().toString();
const font='Arial';

function text(slide,value,x,y,w,h,size=30,color='#17242b',bold=false){
  const s=slide.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
  s.text=value;s.text.style={typeface:font,fontSize:size,bold,color};return s;
}
function diagram(slide){
  const a=claims.deliverables.architecture;
  const coords=[[65,230,330,105],[65,365,330,105],[470,285,330,120],[875,285,330,120],
                [875,470,330,100],[470,470,330,100],[65,535,330,70],[470,580,330,75]];
  const shapes=a.nodes.map((label,i)=>{
    const [x,y,w,h]=coords[i];
    const s=slide.shapes.add({geometry:'rect',position:{left:x,top:y,width:w,height:h},fill:i>=6?'#f1f2ef':'#e8f4f1',line:{fill:'#c8dcd5',width:1}});
    s.text=label;s.text.style={typeface:font,fontSize:i===7?14:i>=6?18:24,color:'#17242b'};return s;
  });
  for(const [from,to,fromSide,toSide] of [[0,2,'right','left'],[1,2,'right','left'],[2,3,'right','left'],[3,4,'bottom','top'],[4,5,'left','right']])
    slide.shapes.connect(shapes[from],shapes[to],{kind:'elbow',fromSide,toSide,line:{fill:'#0e766e',width:2},tail:{type:'arrow'}});
}
function makeSlide(p,content,index){
  const slide=p.slides.add();slide.background.fill='#fafaf8';
  text(slide,content.title,64,48,1152,80,index===0&&content.title==='CycleTwin'?70:44,'#17242b',false);
  text(slide,content.subtitle,64,132,1152,65,24,'#65757b');
  if(content.diagram) diagram(slide);
  else if(content.table){
    const values=content.table;
    const t=slide.tables.add({rows:values.length,columns:values[0].length,left:64,top:215,width:1152,height:410,values,
                              columnWidths:[140,140,275,275,322]});
    t.borders.assign({fill:'#e1e8e4',width:0.5});
    for(let r=0;r<values.length;r++)for(let col=0;col<values[0].length;col++){
      const cell=t.getCell(r,col);cell.fill=r===0?'#0e766e':r%2?'#ffffff':'#eef3f0';
      cell.text.style={typeface:font,fontSize:23,bold:r===0,color:r===0?'#ffffff':'#17242b'};
    }
  }else{
    const body=content.body || [];
    body.forEach((value,i)=>text(slide,value,74,230+i*(390/Math.max(body.length,1)),1120,88,30,i===0?'#0e766e':'#17242b'));
  }
  text(slide,content.footer,64,666,1152,30,18,'#65757b');
  slide.speakerNotes.text=content.notes || aNotes();
  return slide;
}
function aNotes(){return claims.deliverables.architecture.notes;}
await fs.mkdir(buildDir,{recursive:true});await fs.mkdir(path.join(root,'deliverables'),{recursive:true});
await fs.mkdir(path.join(buildDir,'final_outputs'),{recursive:true});
for(const [name,slides] of [['CycleTwin_pitch_deck',claims.deliverables.deck],['CycleTwin_architecture',[{...claims.deliverables.architecture,diagram:true}]]]){
  const p=Presentation.create({slideSize:{width:1280,height:720}});
  slides.forEach((s,i)=>makeSlide(p,s,i));
  const candidate=path.join(buildDir,name+'-'+revision+'-candidate.pptx');
  await (await PresentationFile.exportPptx(p)).save(candidate);
  const final=path.join(buildDir,'final_outputs',name+'-'+revision+'-final.pptx');
  const tableOwners=slides.flatMap((s,i)=>s.table?[i+1]:[]);
  await finalizePresentation({workspaceDir:root,candidatePath:candidate,finalPath:final,pythonExecutable:runtimePython,
    integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),
    layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),
    layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit',...tableOwners.flatMap(n=>['--require-native-table-slide',String(n)])],
    explicitTotalSlideCount:slides.length,requiredNativeTableOwnerSlides:tableOwners,
    fontPolicy:{basis:'design',families:[font]},verifyArtifactToolImport:true,
    receiptPath:path.join(buildDir,name+'-'+revision+'-validation.json')});
  await fs.copyFile(final,path.join(root,'deliverables',name+'.pptx'));
  const previews=path.join(buildDir,name+'-previews');await fs.mkdir(previews,{recursive:true});
  for(const [i,slide] of p.slides.items.entries()){
    const png=await p.export({slide,format:'png',scale:1});
    await fs.writeFile(path.join(previews,'slide-'+(i+1)+'.png'),new Uint8Array(await png.arrayBuffer()));
  }
  console.log('Finalized and rendered',name,slides.length);
}
const conversion=spawnSync('soffice',['--headless','--convert-to','pdf','--outdir',path.join(root,'deliverables'),
  path.join(root,'deliverables/CycleTwin_pitch_deck.pptx'),path.join(root,'deliverables/CycleTwin_architecture.pptx')],{encoding:'utf8'});
if(conversion.status!==0)throw new Error(conversion.stderr||'PDF conversion failed');
console.log(conversion.stdout);
