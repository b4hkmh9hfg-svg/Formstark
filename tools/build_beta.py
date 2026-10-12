#!/usr/bin/env python3
"""Baut die Supabase-Version der App (beta/) aus der Netlify-Version (index.html).

Aufruf:  python3 tools/build_beta.py <index.html der alten App> [ziel-ordner] [asset-praefix]
Beispiel: python3 tools/build_beta.py /home/claude/v21/web/index.html beta ../
Jeder Ersetzungsschritt prüft, dass die Stelle genau einmal vorkommt (sonst Abbruch).
"""
import os, re, shutil, sys

src = sys.argv[1]
out = sys.argv[2] if len(sys.argv) > 2 else "beta"
pre = sys.argv[3] if len(sys.argv) > 3 else "../"
here = os.path.dirname(os.path.abspath(__file__))
root = os.path.dirname(here)
beta = out != "."

t = open(src, encoding="utf-8").read()
layer = open(os.path.join(here, "sb_layer.js"), encoding="utf-8").read()


def rep(old, new, count=1):
    global t
    n = t.count(old)
    if n != count:
        sys.exit("FEHLER: Stelle %r kommt %d-mal vor (erwartet %d)" % (old[:90], n, count))
    t = t.replace(old, new)


# --- Speichern / Laden ---
rep("function persist(){S.upd=Date.now();saveLocal();publishDuo();if(!docRef)return;",
    "function persist(){S.upd=Date.now();saveLocal();publishDuo();if(SBon){sbDiffPush();return}if(!docRef)return;")
rep("async function flushDb(){if(!docRef||!dirty)return;",
    "async function flushDb(){if(SBon){await sbFlush();return}if(!docRef||!dirty)return;")
rep("function saveLocal(){try{localStorage.setItem(lsKey(acc.cur),JSON.stringify(S))}catch(e){}}",
    "function saveLocal(){if(SBon)return;try{localStorage.setItem(lsKey(acc.cur),JSON.stringify(S))}catch(e){}}")
rep("function accState(id){if(id===acc.cur)return S;if(OTH[id])return OTH[id];",
    "function accState(id){if(id===acc.cur)return S;if(OTH[id])return OTH[id];if(SBon)return null;")
rep("async function fetchOthers(){if(!dbH||!uidC)return;",
    "async function fetchOthers(){if(SBon){sbTick(true);return false}if(!dbH||!uidC)return;")
rep("/* ===== Online-Speicher (Firebase) für die Website ===== */", layer + "\n/* ===== Online-Speicher (Firebase, alt) ===== */")

# --- Start ---
rep(''' if(!IN_CLAUDE&&location.hash.includes("join=")){if(applyJoin(location.hash)){history.replaceState(null,"",location.pathname);flash("Einladung angenommen, verbinde …")}}
 if(!IN_CLAUDE&&SYNC){const ok=await initSync();if(!ok&&mode==="loading")mode="local";if(!PL)render();return}''',
    ''' if(!IN_CLAUDE){await sbBoot();return}''')
rep('''loadLocal();if(IN_CLAUDE||SYNC){mode="loading";setTimeout(()=>{if(mode==="loading"){mode="local";render()}},8000)}render();''',
    '''loadLocal();if(IN_CLAUDE){mode="loading";setTimeout(()=>{if(mode==="loading"){mode="local";render()}},8000)}else mode="loading";render();''')

# --- Ansichten: Anmeldung, Kontowahl ---
rep(''' renderAccBtn();
 if(!picked&&urlAcc&&''',
    ''' if(mode==="login"||mode==="slot"){if(nav)nav.hidden=true;$("#appname").textContent="Formstark";$("#ttl").textContent=mode==="login"?"Anmelden":"Hallo!";$("#wklbl").innerHTML="";const ab=$("#accbtn");if(ab)ab.hidden=true;v.classList.add("anim");v.innerHTML=mode==="login"?vLogin():vSlot();lastV="";return}
 renderAccBtn();
 if(!picked&&urlAcc&&''')

# --- Aktionen ---
rep(''' if(a==="backup"){exportData();return}
 if(a==="rescue"){openRescue();return}''',
    ''' if(a==="backup"){exportData();return}
 if(a==="sbsync"){sbTick(true);return}
 if(a==="sblogout"){sbLogout();return}
 if(a==="slotset"){sbFinish(v,!sbRaw(SBc));return}
 if(SBon&&(a==="rescue"||a==="slotreset"||a==="rescuep"||a==="rescuec"))return;
 if(a==="rescue"){openRescue();return}''')
rep('''if(a==="accpick"){if(PL)return;closeSheet();picked=false;''',
    '''if(a==="accpick"){if(PL)return;if(SBon){openAccSheet();return}closeSheet();picked=false;''')
rep('function syncCard(){if(IN_CLAUDE)return "";', 'function syncCard(){if(IN_CLAUDE)return "";if(SBon)return sbCard();')

# --- Texte ---
rep("Online in deinem Firebase-Speicher gesichert und auf allen verbundenen Geräten gleich.",
    "Online in deinem Konto gesichert und auf allen Geräten gleich, auf denen du angemeldet bist.")
rep('''<button class="btn line sm" data-a="rescue">Datenrettung</button><label class="btn line sm"''',
    '''${SBon?"":`<button class="btn line sm" data-a="rescue">Datenrettung</button>`}<label class="btn line sm"''')
rep('''<div class="small ${dbH?"":"muted"}">${dbH?(duoLive?''', '''<div class="small ${(dbH||SBon)?"":"muted"}">${(dbH||SBon)?(duoLive?''')
rep("const saveTxt=()=>mode===\"db\"?",
    "const saveTxt=()=>SBon?(SBS.err?'<i class=\"local\"></i>'+esc(SBS.err):sbPending()?'<i class=\"local\"></i>Wird gesendet …':'<i></i>Gespeichert und abgeglichen'):mode===\"db\"?")

# --- Challenges: Fortschritt steht im eigenen Zustand (S.chPub), der Partner liest ihn ---
rep("function publishCh(){if(!chDb||!myId)return;",
    "function publishCh(){if(SBon){const o={};CH.forEach(c=>{if(S.ch[c.id])o[c.id]={n:chCount(c),d:c.d}});const pub=S.chShare&&S.profile?{name:S.profile.name,ch:o,t:Date.now()}:null;const cm=x=>JSON.stringify(x&&{name:x.name,ch:x.ch});if(cm(pub)!==cm(S.chPub)){if(pub)S.chPub=pub;else delete S.chPub;persist()}return}if(!chDb||!myId)return;")

# --- Dialog schließen: verzögerte Remote-Änderungen nachholen ---
rep('function closeSheet(){$("#sheetHost").innerHTML=""}',
    'function closeSheet(){$("#sheetHost").innerHTML="";if(SBon&&(SBpend||SBpchg))setTimeout(sbApply,60)}')

# --- Sicherung laden: Unterschiede in die Datenbank schreiben ---
rep('''S.lastBackup=S.lastBackup||key(today());saveLocal();
  if(docRef){''', '''S.lastBackup=S.lastBackup||key(today());saveLocal();
  if(SBon){S.slot=acc.cur;persist()}
  if(docRef){''')

# --- Musik-Pfad ---
n = t.count('"music/"')
t = t.replace('"music/"', '"%smusic/"' % pre)

# --- Kopfbereich ---
head_old = '<meta name="theme-color" content="#0A0A0B">'
head_new = (head_old + '\n<link rel="manifest" href="manifest.webmanifest">\n<link rel="apple-touch-icon" href="icon-180.png">\n'
            '<script src="%sdaten.js"></script>' % pre)
rep(head_old, head_new)
if beta:
    rep('<meta name="apple-mobile-web-app-title" content="Formstark">', '<meta name="apple-mobile-web-app-title" content="Formstark Beta">')
    rep("<title>Formstark</title>", "<title>Formstark Beta</title>")

os.makedirs(os.path.join(root, out), exist_ok=True)
open(os.path.join(root, out, "index.html"), "w", encoding="utf-8").write(t)

# --- Service Worker, Manifest, Symbole ---
srcdir = os.path.dirname(os.path.abspath(src))
sw = open(os.path.join(srcdir, "sw.js"), encoding="utf-8").read()
sw = re.sub(r'const C="[^"]*";', 'const C="formstark-%s-v1";' % ("beta" if beta else "app"), sw, count=1)
sw = sw.replace('const CORE=["./",', 'const CORE=["./","%sdaten.js",' % pre)
open(os.path.join(root, out, "sw.js"), "w", encoding="utf-8").write(sw)
man = open(os.path.join(srcdir, "manifest.webmanifest"), encoding="utf-8").read()
if beta:
    man = man.replace('"name": "Formstark"', '"name": "Formstark Beta"').replace('"short_name": "Formstark"', '"short_name": "Beta"')
open(os.path.join(root, out, "manifest.webmanifest"), "w", encoding="utf-8").write(man)
for ic in ("icon-180.png", "icon-192.png", "icon-512.png"):
    shutil.copy(os.path.join(srcdir, ic), os.path.join(root, out, ic))
print("ok:", out, "Musikstellen:", n, "Größe:", len(t))
