import asyncio, json, base64, sys
sys.path.insert(0,"/home/claude/formstark/tests")
from playwright.async_api import async_playwright
from sb_mock import MockSB
from beta_test_helpers import *

def ok(c,msg):
    print(("OK   " if c else "FAIL ")+msg)
    if not c: ok.bad+=1
ok.bad=0

cfg={"c":{"apiKey":"AIzaFAKE","projectId":"demo"},"t":"TEAMCODE1234567890ABCDE"}
link="https://formstark.netlify.app/#join="+base64.b64encode(json.dumps(cfg).encode()).decode()
def fsdoc(name,state):
    return {"name":"projects/demo/databases/(default)/documents/data/users/T/"+name,"fields":{"j":{"stringValue":json.dumps(state)},"upd":{"integerValue":"1"}}}
OLD_ME=mk("Sara",0,"me"); OLD_ME.pop("slot",None); OLD_ME["photos"]={"p1":"data:image/jpeg;base64,AAAA"}
OLD_ME["recipes"]=[{"id":"r1","n":"Bowl"}]; OLD_ME["prs"]=[{"id":"pr1","e":"pullpro","n":"Klimmzug","m":"r","man":[{"k":"2026-10-01","v":5}]}]
OLD_MT=mk("Martin",1,"martin"); OLD_MT.pop("slot",None)
async def fs(route):
    u=route.request.url
    if "/documents/data/users/" in u:
        return await route.fulfill(json={"documents":[fsdoc("state",OLD_ME),fsdoc("state_martin",OLD_MT)]})
    await route.fulfill(status=404,body="{}")
async def main():
    m=MockSB(); m.add_user("sara@test.de","pw1",SARA); errs=[]
    async with async_playwright() as p:
        b=await p.chromium.launch(); ctx=await b.new_context(viewport={"width":375,"height":900}); pg=await ctx.new_page()
        pg.on("pageerror",lambda e:errs.append(str(e)))
        await pg.route("https://uxiyjsbhtijrhptwlibs.supabase.co/**",m.handle); await pg.route("https://firestore.googleapis.com/**",fs)
        await pg.goto("file:///home/claude/formstark/umzug.html")
        await pg.fill("#mail","sara@test.de"); await pg.fill("#pw","pw1"); await pg.click("#lg")
        await pg.wait_for_selector("#c2:not([hidden])")
        await pg.fill("#link",link); await pg.click("#list")
        await pg.wait_for_selector("input[name=p]")
        txt=await pg.inner_text("#profiles"); ok("Sara" in txt and "Martin" in txt, "beide Profile gelistet")
        await pg.check("input[name=p][value='0']")
        await pg.wait_for_function("!document.getElementById('go').disabled")
        print(await pg.inner_text("#info"))
        await pg.click("#go")
        await pg.wait_for_function("document.getElementById('m3').innerText.startsWith('Fertig')",timeout=15000)
        res=await pg.inner_text("#m3"); ok("stimmen überein" in res, "Zahlen stimmen: "+res)
        print(await pg.inner_text("#res"))
        prof=m.t["profile"][(SARA,)]; ok(prof["einstellungen"]["slot"]=="me" and prof["name"]=="Sara","Profil mit slot=me")
        ok(all(r["quelle"]=="umzug" for r in m.rows("workouts",SARA)),"Workouts quelle=umzug")
        ok(len(m.rows("workouts",MARTIN))==0,"nichts für Martin geschrieben")
        # wiederholen -> keine Doppelten; Überschreiben nur mit Haken
        n1=(len(m.rows("workouts",SARA)),len(m.rows("eintraege",SARA)),len(m.rows("tageswerte",SARA)))
        await pg.check("input[name=p][value='0']"); await pg.click("input[name=p][value='1']"); await pg.click("input[name=p][value='0']")
        await pg.wait_for_selector("#ow:not([hidden])"); ok(await pg.is_disabled("#go"),"Wiederholung: erst mit Haken freigegeben")
        await pg.check("#conf"); await pg.click("#go")
        await pg.wait_for_function("document.getElementById('m3').innerText.startsWith('Fertig')",timeout=15000)
        n2=(len(m.rows("workouts",SARA)),len(m.rows("eintraege",SARA)),len(m.rows("tageswerte",SARA)))
        ok(n1==n2,"Wiederholung erzeugt keine Doppelten %s"%(n2,))
        # App lädt umgezogene Daten
        ctx2=await b.new_context(viewport={"width":390,"height":844}); A=await ctx2.new_page()
        A.on("pageerror",lambda e:errs.append(str(e)))
        await A.route("https://uxiyjsbhtijrhptwlibs.supabase.co/**",m.handle)
        await A.goto("file:///home/claude/formstark/beta/index.html"); await A.wait_for_selector("#lgform")
        await A.fill("#lg-mail","sara@test.de"); await A.fill("#lg-pw","pw1"); await A.click("#lg-go")
        await A.wait_for_function("document.getElementById('lgform')===null"); await A.wait_for_timeout(800)
        ok("Sara" in await A.inner_text("#ttl"),"Beta-App zeigt umgezogene Daten")
        await A.screenshot(path="/tmp/claude-0/t/umzug_app.png")
        real=[e for e in errs if "Failed to load" not in e]; ok(not real,"keine Fehler: %s"%real[:3])
        await pg.screenshot(path="/tmp/claude-0/t/umzug.png",full_page=True)
        await b.close()
    print("FEHLER:",ok.bad); sys.exit(1 if ok.bad else 0)
asyncio.run(main())
