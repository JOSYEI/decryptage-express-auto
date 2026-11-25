window.DEUP = async function(tag, nparts, plName, plDesc){
  const R='https://raw.githubusercontent.com/JOSYEI/decryptage-express-auto/transfert/'+tag+'/';
  const sleep=ms=>new Promise(r=>setTimeout(r,ms));
  const log=[];
  const m=await (await fetch(R+'meta.json?x='+Date.now())).json();
  const parts=[];for(let i=0;i<nparts;i++){parts.push(await (await fetch(R+'video.part'+String(i).padStart(2,'0'))).blob())}
  const f=new File(parts,tag+'.mp4',{type:'video/mp4'});
  const inp=document.querySelector('input[type=file]');const dt=new DataTransfer();dt.items.add(f);inp.files=dt.files;inp.dispatchEvent(new Event('change',{bubbles:true}));
  let d;for(let i=0;i<40;i++){await sleep(500);d=document.querySelector('ytcp-uploads-dialog');if(d&&d.querySelectorAll('#textbox').length>=2)break}
  const tb=[...d.querySelectorAll('#textbox')];
  const setTxt=async(el,t)=>{el.focus();document.execCommand('selectAll');document.execCommand('insertText',false,t);el.dispatchEvent(new Event('input',{bubbles:true}))};
  await setTxt(tb[0],m.title);await setTxt(tb[1],m.description);
  const b=await (await fetch(R+'cover.jpg?x='+Date.now())).blob();
  const th=[...d.querySelectorAll('input[type=file]')].find(i=>/image/.test(i.accept));
  if(th){const t2=new DataTransfer();t2.items.add(new File([b],'cover.jpg',{type:'image/jpeg'}));th.files=t2.files;th.dispatchEvent(new Event('change',{bubbles:true}))}
  await sleep(1500);
  d.querySelector('[name=VIDEO_MADE_FOR_KIDS_NOT_MFK]').click();
  const al=d.querySelector('[name=VIDEO_HAS_ALTERED_CONTENT_YES]');if(al)al.click();
  const ti=d.querySelector('input[aria-label=Tags]');if(ti){ti.focus();document.execCommand('insertText',false,m.tags);ti.dispatchEvent(new Event('input',{bubbles:true}));ti.blur()}
  await sleep(800);
  // playlist
  const pb=[...d.querySelectorAll('ytcp-dropdown-trigger, button, ytcp-button')].find(e=>/Sélectionner les playlists|Sélectionner/.test(e.getAttribute('aria-label')||e.innerText||'')&&e.closest('ytcp-video-metadata-playlists'));
  const trig=d.querySelector('ytcp-video-metadata-playlists ytcp-dropdown-trigger')||pb;trig.click();await sleep(1200);
  const find=()=>[...document.querySelectorAll('ytcp-playlist-dialog label, ytcp-checkbox-lit, ytcp-playlist-dialog #items label')].find(e=>(e.innerText||'').trim().startsWith(plName));
  let item=find();
  if(!item){
    const nb=[...document.querySelectorAll('ytcp-playlist-dialog ytcp-button, ytcp-playlist-dialog tp-yt-paper-button')].find(e=>/playlist/i.test(e.innerText)&&/Nouvelle|Créer/.test(e.innerText));
    nb.click();await sleep(700);
    const np=[...document.querySelectorAll('tp-yt-paper-item, ytcp-text-menu tp-yt-paper-item')].find(e=>/Nouvelle playlist/.test(e.innerText));np.click();await sleep(1200);
    const pd=[...document.querySelectorAll('ytcp-playlist-metadata-editor, ytcp-dialog')].find(e=>/Créer une playlist/.test(e.innerText)&&e.querySelector('#textbox'));
    const t3=[...pd.querySelectorAll('#textbox')];await setTxt(t3[0],plName);await setTxt(t3[1],plDesc);
    const cb=[...pd.querySelectorAll('ytcp-button')].find(e=>/^Créer$/.test(e.innerText.trim()));cb.click();await sleep(2500);
    item=find();
  }
  const cbx=item.querySelector('ytcp-checkbox-lit')||item;const checked=(cbx.getAttribute&&cbx.getAttribute('aria-checked'))==='true'||(cbx.checked===true);
  if(!checked)(item.querySelector('#checkbox')||cbx).click();
  await sleep(500);
  const ok=[...document.querySelectorAll('ytcp-playlist-dialog ytcp-button')].find(e=>/^OK$/.test(e.innerText.trim()));ok&&ok.click();await sleep(800);
  return JSON.stringify({title:m.title.length,desc:m.description.length,tags:m.tags.length,pl:plName});
};
'ok'
