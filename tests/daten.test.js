const FSD=require("../daten.js"); const assert=require("assert");
function norm(S){const o=JSON.parse(JSON.stringify(S));FSD.LOKAL.forEach(k=>delete o[k]);
  if(o.photos&&!Object.keys(o.photos).length)delete o.photos;
  FSD.LISTEN.forEach(k=>{if(Array.isArray(o[k])&&!o[k].length)delete o[k]});
  Object.keys(o.log||{}).forEach(t=>{});return o}
function rt(S){const rows=FSD.sZuZeilen(S);const j=JSON.parse(JSON.stringify(rows));return FSD.zeilenZuS(j)}
function eq(S,label){const a=norm(S),b=norm(rt(S));try{assert.deepStrictEqual(b,a)}catch(e){console.log("FAIL",label);console.log(JSON.stringify(a).slice(0,600));console.log(JSON.stringify(b).slice(0,600));process.exit(1)}console.log("ok",label)}

const S1={v:5,kind:"base",name:"Sara",skin:"edel",profile:{name:"Sara",since:"2026-09-01"},pid:"p1",
 start:"2026-09-21",tg:{kMin:1650,kMax:1750,pMin:110,pMax:130},water:8,rest:90,fav:["a","b"],xwfav:["x"],
 mp:{"2026-10-01":{a:1}},mpDone:{k:true},cycle:{on:false,len:28,starts:[]},ch:{c1:{x:1}},custom:{s1:{a:[1,2]}},
 prs:[{id:"pr1",e:"pullpro",n:"Klimmzug",m:"r",man:[{k:"2026-10-01",v:5}]},{id:"pr2",e:"squat",n:"Kniebeuge",m:"kg",man:[]}],
 recipes:[{id:"r1",n:"Bowl",own:1,ing:[{n:"Reis"}]},{n:"ohne id"},{n:"ohne id"}],
 shop:[{id:"s1",t:"Milch",d:false}],goals:[{id:"g1",t:"Ziel"}],tests:[{date:"2026-10-02",pull:3}],myw:[],cex:[],duels:[],prog:[{id:"u1",url:"x",date:"2026-10-01"}],
 photos:{ph1:"data:image/jpeg;base64,AAAA"},obLater:true,introSeen:true,upd:123,
 log:{
  "2026-10-01":{steps:9000,water:5,done:["stange1","morning"],flows:["slow"],med:10,kg:{"s|e":2.5},sets:{"s|e":[true,false,true]},rate:{k:{e:3,n:"ok"}},adapt:{a:"",weak:0},check:{weight:61.5,sleepH:7,mood:4,thoughts:"gut"},
   wk:[{id:"w1",src:"stange1",n:"Stange",min:40,feel:4,note:"gut",items:[{e:"pullpro",s:3,r:5,u:"r",kg:null}]},{id:"w2",src:"",n:"Park",min:null,feel:0,note:"",items:[]}],
   acts:[{id:"a1",t:"run",min:30,km:4.2,n:"x"}],food:[{id:"f1",s:"fruh",n:"Brot",k:200,p:8,rid:""},{id:"f2",s:"mit",n:"Reis",k:300,p:6,rid:"r1",nu:{a:1}}]},
  "2026-10-02":{},
  "2026-10-03":{wk:[{n:"alt ohne id",min:"45",items:[{e:"x",s:1,r:1}]},{n:"alt2"}],food:[{n:"ohne id",k:1,p:1,s:"a"}]}
 }};
eq(S1,"voller Zustand");
eq({v:5,profile:null,log:{}},"leer");
eq({v:5,name:"Formstark",profile:{name:"Jo"},log:{"2026-01-01":{extra:{a:1},zz:[1,2,3],nul:null,zero:0,txt:""}}},"unbekannte Tagesfelder");

// Diff
const a=FSD.sZuZeilen(S1);
const S2=JSON.parse(JSON.stringify(S1)); S2.log["2026-10-01"].steps=9500; S2.log["2026-10-01"].wk.pop(); S2.log["2026-10-01"].food.push({id:"f3",s:"abd",n:"Pasta",k:500,p:15,rid:""}); delete S2.log["2026-10-01"].med;
const d=FSD.diffZeilen(a,FSD.sZuZeilen(S2));
assert.strictEqual(d.profile,null);
assert.strictEqual(d.workouts.length,1); assert.strictEqual(d.workouts[0].id,"w2"); assert.strictEqual(d.workouts[0].geloescht,true);
assert.strictEqual(d.eintraege.length,1); assert.strictEqual(d.eintraege[0].id,"f3");
const tw=d.tageswerte.map(x=>x.bereich+":"+JSON.stringify(x.daten)).sort(); assert.deepStrictEqual(tw,['med:{"_geloescht":true}','steps:{"v":9500}']);
assert(FSD.leer(FSD.diffZeilen(a,FSD.sZuZeilen(S1))));
console.log("ok diff");
// Löschmarken wirken beim Zurückbauen
const rowsAfter=JSON.parse(JSON.stringify(FSD.sZuZeilen(S1)));
d.workouts.forEach(r=>{const i=rowsAfter.workouts.findIndex(x=>x.id===r.id);rowsAfter.workouts[i]=r});
d.tageswerte.forEach(r=>{const i=rowsAfter.tageswerte.findIndex(x=>x.tag===r.tag&&x.bereich===r.bereich);if(i>=0)rowsAfter.tageswerte[i]=r;else rowsAfter.tageswerte.push(r)});
d.eintraege.forEach(r=>{const i=rowsAfter.eintraege.findIndex(x=>x.art===r.art&&x.id===r.id);if(i>=0)rowsAfter.eintraege[i]=r;else rowsAfter.eintraege.push(r)});
rowsAfter.profile=d.profile||rowsAfter.profile;
assert.deepStrictEqual(norm(FSD.zeilenZuS(rowsAfter)),norm(S2)); console.log("ok löschen/ändern");
// Zeilenformat für Martins Schnittstelle
const w=a.workouts[0]; console.log("Beispiel-Workout-Zeile:",JSON.stringify(w));
// Zeile von außen (ohne extra)
const fremd=FSD.zeilenZuS({profile:{name:"M",einstellungen:{}},workouts:[{id:"x1",tag:"2026-10-05",name:"Pull",minuten:30,gefuehl:4,notiz:null,quelle:"assistent",uebungen:[{e:"pullpro",s:3,r:8,u:"r",kg:null}],geloescht:false}],eintraege:[{art:"acts",id:"a9",tag:"2026-10-05",daten:{t:"run",min:20,km:3,note:""},geloescht:false}],tageswerte:[]});
console.log("fremd:",JSON.stringify(fremd.log));
