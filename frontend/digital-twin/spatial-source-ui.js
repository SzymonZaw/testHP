(() => {
  'use strict';
  if (window.__testhpSpatialSourceUIInstalled) return;
  window.__testhpSpatialSourceUIInstalled = true;

  const REFERENCE_SOURCES = [
    { id:'nih3d-hand-template-3DPX-017237', label:'NIH 3D · reference hand', page:'https://3d.nih.gov/entries/3DPX-017237', download:'https://3d.nih.gov/entries/download/17237/1', note:'Healthy adult hand registration template; reference geometry, not a user-specific twin.' },
    { id:'hubmap-data-portal', label:'HuBMAP · spatial / single-cell', page:'https://portal.hubmapconsortium.org/', download:'https://hubmapconsortium.org/hubmap-data/', note:'Human tissue, spatial and single-cell reference data; dataset/sample provenance remains attached.' },
    { id:'allen-cell-explorer', label:'Allen Cell Explorer · cell reference', page:'https://www.allencell.org/', download:'https://www.allencell.org/data-downloading.html', note:'Reference 3D cell imaging, segmentation and cell features; not cells from the current user.' }
  ];

  const css = `.dt-spatial-source{margin-top:12px;padding:12px;border:1px solid rgba(255,255,255,.10);border-radius:12px;background:rgba(13,17,23,.72);color:#dce5ee;font:12px/1.4 system-ui}.dt-spatial-source-head{display:flex;justify-content:space-between;gap:12px;align-items:center}.dt-spatial-source-title{font-weight:700;letter-spacing:.05em;text-transform:uppercase}.dt-spatial-source-sub{color:#9da7b5;margin-top:3px}.dt-spatial-source-actions{display:flex;flex-wrap:wrap;gap:8px;margin-top:10px}.dt-spatial-source button,.dt-spatial-source a{border:1px solid rgba(255,255,255,.14);background:#151c26;color:#e6edf3;border-radius:8px;padding:7px 9px;text-decoration:none;cursor:pointer;font:600 11px system-ui}.dt-spatial-source button[data-reference]{background:#102b3c;border-color:#315d76}.dt-spatial-source input{display:none}.dt-spatial-source-status{margin-top:9px;color:#9da7b5}.dt-spatial-source-status.error{color:#ff9a9a}.dt-spatial-source-status.ok{color:#9fe0b4}`;
  const style=document.createElement('style');style.textContent=css;document.head.appendChild(style);

  function findHost(){return document.getElementById('twin-viewport')||document.querySelector('[data-twin-viewport]')||document.querySelector('.twin-viewport');}
  function parseJson(file){return file.text().then(text=>{try{return JSON.parse(text);}catch(error){throw new Error(`Invalid metadata JSON: ${error.message}`);}});}
  async function loadReferenceHand(status){
    try{
      const catalogApi=window.testhpReferenceDatasetCatalog;
      const catalog=await catalogApi?.loadReferenceDatasetCatalog?.();
      const dataset=catalog?.datasets?.find(item=>item.id==='nih-hand-template-3dpx-017237');
      const url=dataset?.asset?.url;
      if(!url) throw new Error('NIH 3D reference hand asset is not available in the reference catalog.');
      const asset={id:dataset.id,url,sourceId:dataset.id,sourceType:'public_reference',status:'available',ownership:'reference',metadata:{...dataset,referenceOnly:true,assetUrl:url},mapping:{}};
      window.TestHPSpatialData?.setActiveAsset?.(asset);
      status.className='dt-spatial-source-status ok';
      status.textContent='NIH 3D reference hand active · reference-only geometry · Palm selected.';
      window.dispatchEvent(new CustomEvent('testhp:reference-hand-activated',{detail:{asset,regionId:'palm'}}));
    }catch(error){
      status.className='dt-spatial-source-status error';
      status.textContent=String(error.message||error);
    }
  }
  function createPanel(host){
    if(host.parentElement.querySelector('.dt-spatial-source')) return;
    const panel=document.createElement('section');panel.className='dt-spatial-source';panel.setAttribute('aria-label','Spatial data source');
    panel.innerHTML=`<div class="dt-spatial-source-head"><div><div class="dt-spatial-source-title">Spatial data</div><div class="dt-spatial-source-sub">Reference datasets or your own hand asset</div></div><div>USER / REFERENCE</div></div><div class="dt-spatial-source-actions"><button type="button" data-reference>Explore NIH 3D reference hand</button><button type="button" data-import>Import GLB/GLTF + metadata</button><input type="file" accept=".glb,.gltf,.json,model/gltf-binary,model/gltf+json,application/json" multiple data-files><button type="button" data-clear>Clear active asset</button></div><div class="dt-spatial-source-actions" data-references></div><div class="dt-spatial-source-status" data-status>Reference data is never treated as user health data.</div>`;
    host.parentElement.insertBefore(panel,host.nextSibling);
    const input=panel.querySelector('[data-files]'),status=panel.querySelector('[data-status]'),refs=panel.querySelector('[data-references]');
    panel.querySelector('[data-reference]').onclick=()=>loadReferenceHand(status);
    REFERENCE_SOURCES.forEach(source=>{const wrap=document.createElement('span');const page=document.createElement('a');page.href=source.page;page.target='_blank';page.rel='noopener noreferrer';page.textContent=source.label;page.title=source.note;wrap.appendChild(page);refs.appendChild(wrap);});
    panel.querySelector('[data-import]').onclick=()=>input.click();
    panel.querySelector('[data-clear]').onclick=()=>{window.TestHPSpatialData?.clearActiveAsset?.();status.className='dt-spatial-source-status';status.textContent='No imported asset is active.';};
    input.onchange=async()=>{
      const files=[...input.files];const assetFile=files.find(f=>/\.(glb|gltf)$/i.test(f.name));const metadataFile=files.find(f=>/\.json$/i.test(f.name));
      if(!assetFile||!metadataFile){status.className='dt-spatial-source-status error';status.textContent='Select one .glb/.gltf and one metadata .json file.';return;}
      try{
        const metadata=await parseJson(metadataFile);const assetUrl=URL.createObjectURL(assetFile);const normalized=window.TestHPSpatialData.normalizeImportMetadata(metadata,assetUrl);const mapping=window.TestHPSpatialData.mapGeometryToRegions(normalized);
        window.TestHPSpatialData.setActiveAsset({id:normalized.assetId,url:assetUrl,sourceId:normalized.sourceId,status:'available',ownership:'user',metadata:normalized,mapping});
        status.className='dt-spatial-source-status ok';status.textContent=`Imported ${assetFile.name} · ${normalized.regions.length} validated region(s).`;
      }catch(error){status.className='dt-spatial-source-status error';status.textContent=String(error.message||error);}
    };
  }
  function mount(){const host=findHost();if(host)createPanel(host);}
  const observer=new MutationObserver(mount);if(document.body)observer.observe(document.body,{childList:true,subtree:true});
  const timer=setInterval(()=>{mount();if(findHost())clearInterval(timer);},250);setTimeout(()=>clearInterval(timer),15000);
  window.addEventListener('testhp:reference-hand-requested',()=>{const panel=document.querySelector('.dt-spatial-source');const status=panel?.querySelector('[data-status]');if(status)loadReferenceHand(status);});
})();
