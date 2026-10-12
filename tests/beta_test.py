import asyncio, json, random, datetime, subprocess, sys
from playwright.async_api import async_playwright
sys.path.insert(0, "/home/claude/formstark/tests")
from sb_mock import MockSB
random.seed(5)
T = datetime.date.today()
SARA, MARTIN = "11111111-aaaa", "22222222-bbbb"

def mk(name, pro, slot):
    log = {}
    for i in range(20):
        k = str(T - datetime.timedelta(days=i)); tr = random.random() < .6
        L = {"check": {"mood": random.randint(2, 5), "sleepH": round(random.uniform(5.5, 8.5), 1)},
             "food": [{"id": "f%d_%s" % (i, slot), "n": "Essen", "s": "Mittag", "k": random.randint(1200, 2300), "p": random.randint(60, 160)}], "water": random.randint(3, 10)}
        if tr:
            L["done"] = ["c_pull"] if pro else ["poA"]
            if random.random() < .4:
                L["wk"] = [{"id": "w%d_%s" % (i, slot), "n": "Park", "min": 40, "feel": 4, "items": [{"e": "pushup", "s": 3, "r": 12, "u": "r", "kg": None}]}]
        log[k] = L
    s = {"profile": {"name": name, "since": "2026-09-01"}, "start": str(T - datetime.timedelta(days=14)), "log": log, "obLater": True, "introSeen": True, "slot": slot, "body": {"sex": "w", "age": 30, "h": 170, "w": 65}}
    if pro: s["kind"] = "pro"
    return s

def rows_of(state, uid):
    out = subprocess.run(["node", "/home/claude/formstark/tests/rows.js"], input=json.dumps(state), capture_output=True, text=True, check=True).stdout
    return json.loads(out)

def seed(m):
    m.add_user("sara@test.de", "pw1", SARA); m.add_user("martin@test.de", "pw2", MARTIN)
    for st, uid in ((mk("Sara", 0, "me"), SARA), (mk("Martin", 1, "martin"), MARTIN)):
        r = rows_of(st, uid)
        m.put("profile", {"user_id": uid, **r["profile"]})
        for t in ("workouts", "eintraege", "tageswerte"):
            for row in r[t]: m.put(t, {"user_id": uid, **row})
    m.freig |= {(SARA, MARTIN), (MARTIN, SARA)}

URL = "file:///home/claude/formstark/beta/index.html"
async def new_page(b, m, w=390, errs=None):
    ctx = await b.new_context(viewport={"width": w, "height": 844})
    pg = await ctx.new_page()
    pg.on("pageerror", lambda e: errs.append("PAGEERROR " + str(e)))
    pg.on("console", lambda c: errs.append("CONSOLE " + c.text) if c.type == "error" else None)
    await pg.route("https://uxiyjsbhtijrhptwlibs.supabase.co/**", m.handle)
    return ctx, pg

async def login(pg, mail, pw):
    await pg.goto(URL); await pg.wait_for_selector("#lgform")
    await pg.fill("#lg-mail", mail); await pg.fill("#lg-pw", pw)
    await pg.click("#lg-go")
    await pg.wait_for_selector("#view .card", timeout=8000)
    await pg.wait_for_function("document.getElementById('lgform')===null", timeout=8000)

def ok(c, msg):
    print(("OK   " if c else "FAIL ") + msg)
    if not c: ok.bad += 1
ok.bad = 0

async def main():
    m = MockSB(); seed(m); errs = []
    async with async_playwright() as p:
        b = await p.chromium.launch()
        # 1 falsches Passwort, dann richtig
        ctxA, A = await new_page(b, m, errs=errs)
        await A.goto(URL); await A.wait_for_selector("#lgform")
        await A.fill("#lg-mail", "sara@test.de"); await A.fill("#lg-pw", "falsch"); await A.click("#lg-go")
        await A.wait_for_function("document.getElementById('lg-msg').innerText.includes('stimmt nicht')")
        ok(True, "falsches Passwort wird abgelehnt")
        await A.fill("#lg-pw", "pw1"); await A.click("#lg-go")
        await A.wait_for_function("document.getElementById('lgform')===null", timeout=8000)
        await A.wait_for_timeout(600)
        ttl = await A.inner_text("#ttl"); ok("Sara" in ttl, "Anmeldung: Titel = " + ttl)
        txt0 = await A.inner_text("#view"); ok("gegessen" in txt0.lower() and "schritte" in txt0.lower(), "Heute zeigt Daten (Gegessen, Schritte)")
        await A.screenshot(path="/tmp/claude-0/t/beta_heute.png")
        # 2 Schritte eintragen
        await A.fill("#stp-in", "8123"); await A.press("#stp-in", "Tab")
        await A.wait_for_timeout(1800)
        k = str(T)
        row = m.t["tageswerte"].get((SARA, k, "steps"))
        ok(row and row["daten"] == {"v": 8123}, "Schritte in der Datenbank: %s" % (row and row["daten"]))
        ok(row and row["user_id"] == SARA, "gehört Sara")
        posts = [x for x in m.log if x[0] == "POST"]
        ok(len(posts) >= 1 and sum(x[2] for x in posts if x[1] != "profile") <= 3, "nur geänderte Zeilen gesendet: %s" % posts)
        # 3 Gerät B
        ctxB, B = await new_page(b, m, errs=errs)
        await login(B, "sara@test.de", "pw1"); await B.wait_for_timeout(600)
        v = await B.input_value("#stp-in"); ok(v.replace(".", "") == "8123", "Gerät B sieht 8123 (%s)" % v)
        # 4 A ändert, B holt nach
        await A.fill("#stp-in", "9000"); await A.press("#stp-in", "Tab"); await A.wait_for_timeout(1500)
        await B.evaluate("window.dispatchEvent(new Event('online'))"); await B.wait_for_timeout(1500)
        v = await B.input_value("#stp-in"); ok(v.replace(".", "") == "9000", "B holt Änderung von A (%s)" % v)
        # 5 gleichzeitig verschiedene Dinge
        await A.evaluate("document.querySelector('[data-a=water]')&&document.querySelector('[data-a=water]').click()")
        await B.fill("#stp-in", "9500"); await B.press("#stp-in", "Tab"); await A.wait_for_timeout(1500)
        await A.evaluate("window.dispatchEvent(new Event('online'))"); await A.wait_for_timeout(1500)
        v = await A.input_value("#stp-in"); ok(v.replace(".", "") == "9500", "A holt Änderung von B (%s)" % v)
        # 6 offline
        await ctxA.set_offline(True); m.offline = True
        await A.fill("#stp-in", "9900"); await A.press("#stp-in", "Tab"); await A.wait_for_timeout(1500)
        pend = await A.evaluate("(()=>{const o=JSON.parse(localStorage.getItem('formstark-sb-%s'));return Object.keys(o.out.tageswerte).length})()" % SARA)
        ok(pend >= 1, "offline: Änderung wartet in der Outbox (%d)" % pend)
        ok(m.t["tageswerte"][(SARA, k, "steps")]["daten"]["v"] == 9500, "Server hat noch den alten Wert")
        await A.reload(); await A.wait_for_timeout(2500)
        v = await A.input_value("#stp-in"); ok(v.replace(".", "") == "9900", "offline neu geöffnet: lokaler Stand 9900 (%s)" % v)
        await ctxA.set_offline(False); m.offline = False
        await A.evaluate("window.dispatchEvent(new Event('online'))"); await A.wait_for_timeout(2000)
        ok(m.t["tageswerte"][(SARA, k, "steps")]["daten"]["v"] == 9900, "online: Änderung kommt an")
        # 7 Zusammen
        await A.click("[data-a=tab][data-v=zusammen]"); await A.wait_for_timeout(500)
        txt = await A.inner_text("#view"); ok("Martin" in txt, "Zusammen zeigt Martin")
        await A.screenshot(path="/tmp/claude-0/t/beta_zusammen.png", full_page=True)
        # 8 Sicherheit: A schreibt nicht für Martin
        r = await A.evaluate("""fetch('https://uxiyjsbhtijrhptwlibs.supabase.co/rest/v1/workouts?on_conflict=user_id,id',{method:'POST',headers:{apikey:'x',Authorization:'Bearer tok-%s','Content-Type':'application/json'},body:JSON.stringify([{user_id:'%s',id:'x',tag:'2026-01-01'}])}).then(r=>r.status)""" % (SARA, MARTIN))
        ok(r == 403, "fremde Zeilen schreiben wird abgelehnt (%s)" % r)
        # 9 Abmelden
        await A.click("#accbtn"); await A.wait_for_timeout(300)
        txt = await A.inner_text("#sheetHost"); ok("sara@test.de" in txt, "Konto-Dialog zeigt E-Mail")
        await A.click("[data-a=sblogout]"); await A.wait_for_selector("#lgform")
        left = await A.evaluate("Object.keys(localStorage).filter(k=>k.startsWith('formstark-sb')).length")
        ok(left == 0, "nach Abmelden keine Daten im Gerätespeicher (%d)" % left)
        # 10 Martin, kleines Display
        ctxM, M = await new_page(b, m, w=375, errs=errs)
        await login(M, "martin@test.de", "pw2"); await M.wait_for_timeout(600)
        ok("Martin" in await M.inner_text("#ttl"), "Martin angemeldet")
        await M.screenshot(path="/tmp/claude-0/t/beta_martin375.png")
        sw = await M.evaluate("document.documentElement.scrollWidth"); ok(sw <= 376, "375 px: keine Querscrollbalken (%d)" % sw)
        # 11 neue Person ohne Daten: Kontowahl
        m.add_user("neu@test.de", "pw3", "33333333-cccc")
        ctxN, N = await new_page(b, m, errs=errs)
        await login(N, "neu@test.de", "pw3"); await N.wait_for_timeout(500)
        t = await N.inner_text("#view"); ok("Wer bist du" in t, "neue Person: Kontowahl")
        real = [e for e in errs if "Failed to load resource" not in e]
        ok(not real, "keine Fehler in der Konsole: %s" % real[:3])
        await b.close()
    print("FEHLER:", ok.bad); sys.exit(1 if ok.bad else 0)
asyncio.run(main())
