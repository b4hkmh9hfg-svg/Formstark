/* ===== Supabase: Anmeldung und Speicher ===== */
const SB_URL="https://uxiyjsbhtijrhptwlibs.supabase.co",SB_KEY="sb_publishable_sF0G1BqSIXTjOnWAjtYvjg_pZXxBYkZ";
const SBT=["workouts","eintraege","tageswerte"];
const SBORD={workouts:["id"],eintraege:["art","id"],tageswerte:["tag","bereich"]};
const SBCONF={workouts:"user_id,id",eintraege:"user_id,art,id",tageswerte:"user_id,tag,bereich"};
let SBon=false,SBc=null,SBp=null,SBmir=null,SBflT=null,SBtickT=null,SBchg=false,SBpend=false,SBpchg=false,SBwake=false;
const SBS={uid:"",email:"",partner:"",err:"",last:0,busy:false,tick:false,again:false};
/* --- kleiner Supabase-Client (Anmeldung + Tabellen), ohne Fremdbibliothek --- */
const SBSESS="formstark-sb-session";
let SBX=null;
function sbxLoad(){try{const o=JSON.parse(localStorage.getItem(SBSESS)||"null");if(o&&o.refresh_token&&o.user&&o.user.id)return o}catch(e){}return null}
function sbxSave(){try{if(SBX)localStorage.setItem(SBSESS,JSON.stringify(SBX));else localStorage.removeItem(SBSESS)}catch(e){}}
async function sbxFetch(url,opt){const r=await fetch(url,opt);let j=null;const t=await r.text();if(t){try{j=JSON.parse(t)}catch(e){j=t}}return{ok:r.ok,status:r.status,data:j}}
function sbxSet(d){SBX={access_token:d.access_token,refresh_token:d.refresh_token,exp:Date.now()+(+d.expires_in||3600)*1000,user:{id:d.user.id,email:d.user.email||""}};sbxSave()}
async function sbxLogin(email,password){
 const r=await sbxFetch(SB_URL+"/auth/v1/token?grant_type=password",{method:"POST",headers:{apikey:SB_KEY,"Content-Type":"application/json"},body:JSON.stringify({email,password})});
 if(!r.ok){const e=new Error((r.data&&(r.data.msg||r.data.error_description||r.data.message))||("Fehler "+r.status));e.status=r.status;e.invalid=r.status===400||r.status===401;throw e}
 sbxSet(r.data);return SBX.user}
async function sbxRefresh(){
 const r=await sbxFetch(SB_URL+"/auth/v1/token?grant_type=refresh_token",{method:"POST",headers:{apikey:SB_KEY,"Content-Type":"application/json"},body:JSON.stringify({refresh_token:SBX.refresh_token})});
 if(!r.ok){const e=new Error("Anmeldung abgelaufen");e.auth=(r.status===400||r.status===401||r.status===403);throw e}
 sbxSet(r.data)}
async function sbxToken(){if(!SBX)throw Object.assign(new Error("Nicht angemeldet"),{auth:true});if(Date.now()>SBX.exp-60000){try{await sbxRefresh()}catch(e){if(e.auth){SBX=null;sbxSave();if(SBon&&!SBS.leaving)sbToLogin("Bitte melde dich neu an.");throw e}if(Date.now()>SBX.exp)throw e}}return SBX.access_token}
async function sbxRest(method,path,body,prefer){
 const tok=await sbxToken();
 const h={apikey:SB_KEY,Authorization:"Bearer "+tok};
 if(body!==undefined)h["Content-Type"]="application/json";
 if(prefer)h.Prefer=prefer;
 const r=await sbxFetch(SB_URL+"/rest/v1/"+path,{method,headers:h,body:body===undefined?undefined:JSON.stringify(body)});
 if(r.status===401&&SBX){try{await sbxRefresh();return sbxRest(method,path,body,prefer)}catch(e){}}
 if(!r.ok){const m=(r.data&&(r.data.message||r.data.hint||r.data.error))||("Fehler "+r.status);throw Object.assign(new Error(m),{status:r.status})}
 return r.data}
const sbUp=(table,rows,conf)=>sbxRest("POST",table+"?on_conflict="+conf,rows,"resolution=merge-duplicates,return=minimal");
function sbSel(table,filters,order,from){return sbxRest("GET",table+"?select=*"+filters+(order?"&order="+order:"")+"&limit=1000&offset="+(from||0))}
const sbPK=(t,r)=>t==="workouts"?r.id:t==="eintraege"?r.art+"|"+r.id:r.tag+"|"+r.bereich;
const sbEmpty=()=>({profile:null,workouts:{},eintraege:{},tageswerte:{}});
const sbLS=(pre,uid)=>pre+uid;
function sbLoad(pre,uid){try{const o=JSON.parse(localStorage.getItem(sbLS(pre,uid))||"null");if(o&&o.rows)return Object.assign({out:sbEmpty(),last:0},o)}catch(e){}return{rows:sbEmpty(),out:sbEmpty(),last:0}}
function sbSave(){try{localStorage.setItem(sbLS("formstark-sb-",SBS.uid),JSON.stringify(SBc))}catch(e){SBS.err="Der Speicher auf diesem Gerät ist voll."}}
function sbSaveP(){try{localStorage.setItem(sbLS("formstark-sbp-",SBS.uid),JSON.stringify(SBp))}catch(e){}}
function sbEff(c){const o={profile:(c.out&&c.out.profile)||c.rows.profile,workouts:[],eintraege:[],tageswerte:[]};SBT.forEach(t=>{o[t]=Object.values(Object.assign({},c.rows[t],(c.out&&c.out[t])||{}))});return o}
const sbHas=r=>!!(r.profile||r.workouts.length||r.eintraege.length||r.tageswerte.length);
function sbRaw(c){const e=sbEff(c);return sbHas(e)?FSD.zeilenZuS(e):null}
const sbStrip=r=>{const o=Object.assign({},r);delete o.user_id;delete o.aktualisiert;return o};
function sbErr(e){const m=String((e&&e.message)||e||"");if(!navigator.onLine||/fetch|network|load failed|timeout/i.test(m))return "Keine Verbindung. Änderungen werden später gesendet.";if(/JWT|token|auth/i.test(m))return "Bitte melde dich neu an.";return "Synchronisieren hat nicht geklappt: "+m.slice(0,140)}
function sbPending(){if(!SBc)return 0;return (SBc.out.profile?1:0)+SBT.reduce((n,t)=>n+Object.keys(SBc.out[t]).length,0)}

/* --- Schreiben: Unterschiede -> Outbox -> upsert --- */
function sbDiffPush(){
 if(!SBon)return;
 const neu=FSD.sZuZeilen(S),d=FSD.diffZeilen(SBmir,neu);
 if(FSD.leer(d))return;
 if(d.profile)SBc.out.profile=d.profile;
 SBT.forEach(t=>d[t].forEach(r=>{SBc.out[t][sbPK(t,r)]=r}));
 SBmir=neu;sbSave();sbFlushSoon();sbInd()}
function sbFlushSoon(){clearTimeout(SBflT);SBflT=setTimeout(()=>{sbFlush().then(()=>sbInd())},700)}
async function sbFlush(){
 if(!SBon||!SBc)return false;
 if(SBS.busy){SBS.again=true;return false}
 if(!sbPending())return true;
 SBS.busy=true;let ok=true;
 try{
  const o=SBc.out;
  if(o.profile){const row=o.profile;await sbUp("profile",[Object.assign({user_id:SBS.uid},row)],"user_id");SBc.rows.profile=sbStrip(row);if(SBc.out.profile===row)SBc.out.profile=null}
  for(const t of SBT){
   const keys=Object.keys(SBc.out[t]);
   for(let i=0;i<keys.length;i+=200){
    const part=keys.slice(i,i+200),sent=part.map(k=>SBc.out[t][k]);
    await sbUp(t,sent.map(r=>Object.assign({user_id:SBS.uid},r)),SBCONF[t]);
    part.forEach((k,j)=>{SBc.rows[t][k]=sbStrip(sent[j]);if(SBc.out[t][k]===sent[j])delete SBc.out[t][k]})}}
  SBS.err="";sbSave()
 }catch(e){ok=false;SBS.err=sbErr(e);sbSave()}
 SBS.busy=false;
 if(SBS.again){SBS.again=false;if(ok)return sbFlush()}
 return ok}

/* --- Lesen --- */
async function sbFetchAll(table,uid,since){
 const rows=[],f="&user_id=eq."+encodeURIComponent(uid)+(since?"&aktualisiert=gte."+encodeURIComponent(since):"");
 const ord=SBORD[table].map(c=>c+".asc").join(",");
 for(let from=0;;from+=1000){
  const data=await sbSel(table,f,ord,from);
  rows.push(...(data||[]));
  if(!data||data.length<1000)break}
 return rows}
async function sbPullInto(c,uid,withOut){
 const t0=Date.now(),since=c.last?new Date(c.last-300000).toISOString():null;let ch=false;
 {const data=await sbSel("profile","&user_id=eq."+encodeURIComponent(uid)+(since?"&aktualisiert=gte."+encodeURIComponent(since):""));
  if(data&&data[0]&&!(withOut&&c.out.profile)){const r=sbStrip(data[0]);if(JSON.stringify(r)!==JSON.stringify(c.rows.profile)){c.rows.profile=r;ch=true}}}
 for(const t of SBT){
  const data=await sbFetchAll(t,uid,since);
  data.forEach(raw=>{const k=sbPK(t,raw);if(withOut&&c.out[t][k])return;const r=sbStrip(raw);if(JSON.stringify(r)!==JSON.stringify(c.rows[t][k])){c.rows[t][k]=r;ch=true}})}
 c.last=t0;return ch}
async function sbPullOwn(){const ch=await sbPullInto(SBc,SBS.uid,true);sbSave();if(ch)SBchg=true;return ch}
async function sbPullPartner(){
 if(!SBS.partner){const data=await sbxRest("GET","profile?select=user_id&user_id=neq."+encodeURIComponent(SBS.uid));if(data&&data.length)SBS.partner=data[0].user_id}
 if(!SBS.partner)return false;
 if(!SBp||SBp.uid!==SBS.partner){SBp=Object.assign(sbLoad("formstark-sbp-",SBS.uid),{uid:SBS.partner});if(SBp.uid!==SBS.partner)SBp={uid:SBS.partner,rows:sbEmpty(),out:sbEmpty(),last:0}}
 const ch=await sbPullInto(SBp,SBS.partner,false);
 if(ch||!OTHset()){sbSaveP();sbPartnerS()}
 duoLive=Date.now();
 return ch}
const OTHset=()=>!!OTH[sbPslot()];
function sbPslot(){const o=SBp&&SBp.rows&&SBp.rows.profile&&SBp.rows.profile.einstellungen;return (o&&o.slot&&o.slot!==acc.cur)?o.slot:(acc.cur==="me"?"martin":"me")}
function sbPartnerS(){
 const raw=sbRaw(SBp);if(!raw)return;
 const slot=sbPslot();OTH[slot]=norm(raw,slot);
 others=OTH[slot].chPub?[OTH[slot].chPub]:[];SBpchg=true}

/* --- Zustand aufbauen / Remote-Änderungen übernehmen --- */
function sbRebuild(){const raw=sbRaw(SBc);if(!raw)return false;S=norm(raw,acc.cur);S.slot=acc.cur;SBmir=FSD.sZuZeilen(raw);applySkin();applyWeek();return true}
function sbIdle(){const a=document.activeElement;return !PL&&!$("#sheetHost").innerHTML&&!(a&&/^(INPUT|TEXTAREA|SELECT)$/.test(a.tagName))}
function sbApply(){
 if(!SBon)return;
 if(SBchg){if(!sbIdle()){SBpend=true;return}SBchg=false;SBpend=false;if(sbRebuild()){SBpchg=false;render();return}}
 if(SBpchg&&picked&&sbIdle()){SBpchg=false;if(!PL&&(tab==="zusammen"||tab==="heute"||tab==="essen"))render()}}

/* --- Abgleich --- */
async function sbTick(manual){
 if(!SBon||SBS.tick)return;SBS.tick=true;
 try{await sbFlush();await sbPullOwn();try{await sbPullPartner()}catch(e){if(manual)throw e}if(!SBS.err||!sbPending())SBS.err="";SBS.last=Date.now()}
 catch(e){SBS.err=sbErr(e)}
 SBS.tick=false;sbApply();sbInd();
 if(manual)flash(SBS.err||"Abgeglichen ✓")}
function sbInd(){const el=$("#savest");if(el)el.innerHTML=saveTxt()}
function sbStartTimers(){
 if(SBwake)return;SBwake=true;
 document.addEventListener("visibilitychange",()=>{if(document.visibilityState==="visible")sbTick()});
 window.addEventListener("online",()=>sbTick());
 window.addEventListener("focus",()=>sbTick());
 SBtickT=setInterval(()=>{if(document.visibilityState==="visible")sbTick()},60000)}

/* --- Start / Anmeldung --- */
async function sbBoot(){
 try{
  SBX=sbxLoad();
  if(!SBX){mode="login";render();return}
  /* Sitzung prüfen; ohne Internet mit gespeicherten Daten trotzdem starten */
  try{await sbxToken()}catch(e){
   if(!SBX){mode="login";render();return}
   if(!sbLoad("formstark-sb-",SBX.user.id).last){SBS.err=sbErr(e);mode="login";render();return}}
  await sbStart(SBX.user)
 }catch(e){SBS.err="Start fehlgeschlagen: "+((e&&e.message)||e);mode="login";render()}}
async function sbStart(u){
 SBS.uid=u.id;SBS.email=u.email||"";SBS.partner="";SBS.err="";
 SBc=sbLoad("formstark-sb-",u.id);SBp=null;
 mode="loading";render();
 try{await sbPullOwn()}catch(e){SBS.err=sbErr(e)}
 const raw=sbRaw(SBc);
 let slot=raw&&raw.slot;
 if(raw&&!slot){mode="slot";render();return}
 if(!raw){if(SBS.err&&!navigator.onLine){mode="login";render();return}mode="slot";render();return}
 sbFinish(slot)}
function sbFinish(slot,fresh){
 acc.cur=slot;
 if(fresh){S=norm(null,slot);S.slot=slot;SBmir={profile:null,workouts:[],eintraege:[],tageswerte:[]}}
 else if(!sbRebuild()){S=norm(null,slot);S.slot=slot;SBmir={profile:null,workouts:[],eintraege:[],tageswerte:[]}}
 SBon=true;teamMode=true;mode="db";picked=true;obOpen=false;ob=null;
 sbStartTimers();render();
 sbTick(false)}
async function sbLogin(){
 const m=$("#lg-mail"),p=$("#lg-pw"),msg=$("#lg-msg"),btn=$("#lg-go");if(!m||!p)return;
 const email=m.value.trim(),pw=p.value;
 if(!email||!pw){if(msg)msg.textContent="Bitte E-Mail und Passwort eingeben.";return}
 if(btn)btn.disabled=true;if(msg)msg.innerHTML='<span class="spin"></span> Anmelden …';
 try{
  const u=await sbxLogin(email,pw);
  await sbStart(u)
 }catch(e){if(msg)msg.textContent=e.invalid?"E-Mail oder Passwort stimmt nicht.":(navigator.onLine?"Anmeldung nicht möglich: "+e.message:"Keine Verbindung.");if(btn)btn.disabled=false}}
async function sbToLogin(note){
 SBon=false;teamMode=false;clearInterval(SBtickT);SBtickT=null;SBwake=false;SBS.err=note||"";
 S=norm(null,"me");acc.cur="me";picked=false;mode="login";closeSheet();render()}
async function sbLogout(){
 if(sbPending()){await sbFlush();if(sbPending()&&!confirm("Es gibt Änderungen, die noch nicht gesendet wurden (kein Internet?). Sie gehen beim Abmelden verloren. Trotzdem abmelden?"))return}
 SBS.leaving=true;const uid=SBS.uid;
 try{if(SBX)await sbxFetch(SB_URL+"/auth/v1/logout",{method:"POST",headers:{apikey:SB_KEY,Authorization:"Bearer "+SBX.access_token}})}catch(e){}
 SBX=null;sbxSave();
 try{localStorage.removeItem("formstark-sb-"+uid);localStorage.removeItem("formstark-sbp-"+uid)}catch(e){}
 Object.keys(OTH).forEach(k=>delete OTH[k]);others=[];SBc=null;SBp=null;
 SBS.leaving=false;sbToLogin("")}

/* --- Ansichten --- */
function vLogin(){return `<section class="card" style="gap:12px"><p class="serif" style="font-size:30px;line-height:1.15;margin:0">Willkommen bei Formstark</p><div class="small muted">Melde dich mit deiner E-Mail-Adresse an. Deine Daten sind nur für dich sichtbar.</div>
 <form id="lgform" autocomplete="on" style="display:flex;flex-direction:column;gap:12px"><div class="field"><label for="lg-mail">E-Mail</label><input id="lg-mail" name="email" type="email" inputmode="email" autocomplete="username" autocapitalize="off" autocorrect="off" spellcheck="false" required></div>
 <div class="field"><label for="lg-pw">Passwort</label><input id="lg-pw" name="password" type="password" autocomplete="current-password" required></div>
 <button class="btn accent big wide" id="lg-go" type="submit">Anmelden</button></form>
 <div class="small" id="lg-msg" style="color:var(--warn)">${esc(SBS.err||"")}</div></section>`}
function vSlot(){return `<section class="card" style="gap:6px"><p class="serif" style="font-size:28px;line-height:1.15;margin:0">Wer bist du?</p><div class="small muted">Das legt deinen Plan und deine Vorgaben fest. Du wählst das nur einmal.</div></section>
 ${ACCS.map(x=>`<section class="card row between" style="align-items:center"><div><b>${esc(x.def)}</b><div class="small muted">${esc(x.sub)}</div></div><button class="btn accent sm" data-a="slotset" data-v="${x.id}">Das bin ich</button></section>`).join("")}
 <div class="small muted" style="padding:0 6px">Angemeldet als ${esc(SBS.email)} · <button class="textbtn" data-a="sblogout">Abmelden</button></div>`}
function sbAgo(){if(!SBS.last)return "noch nicht";const m=Math.round((Date.now()-SBS.last)/60000);return m<1?"gerade eben":"vor "+m+" Min."}
function sbPanel(){const n=sbPending();return `<div class="small">${SBS.err?`<span style="color:var(--warn)">${esc(SBS.err)}</span>`:`<span class="live"></span>Verbunden und synchronisiert`}</div>
 <div class="small muted">Angemeldet als ${esc(SBS.email)} · zuletzt abgeglichen ${sbAgo()}${n?` · ${n} Änderung${n===1?"":"en"} warten auf Senden`:""}</div>
 <div class="row wrapf"><button class="btn accent sm" data-a="sbsync">Jetzt abgleichen</button><button class="btn line sm" data-a="sblogout">Abmelden</button></div>`}
function sbCard(){return `<section class="card"><h3>Online-Speicher & Sync</h3>${sbPanel()}<div class="small muted">Die App auf dem Home-Bildschirm hat einen eigenen Speicher: melde dich dort einmal separat an.</div></section>`}
function openAccSheet(){openSheet(`<div class="grab"></div><div class="row between"><h2>Konto</h2><button class="iconbtn" data-a="close" aria-label="Schließen">×</button></div>${sbPanel()}`)}
document.addEventListener("submit",e=>{if(e.target&&e.target.id==="lgform"){e.preventDefault();sbLogin()}});
