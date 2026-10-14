"""Test: Training nachtragen mit Gesamtzahl (z. B. 200 Liegestütze) statt Sätze × Wiederholungen.
Prüft: Speicherformat bleibt {e,s,r,u,kg} (Martins Schnittstelle), Anzeige, Abgleich über die Datenbank,
375 px / iPad ohne Querscrollen, Konsole leer."""
import asyncio, sys, datetime
from playwright.async_api import async_playwright
sys.path.insert(0, "/home/claude/formstark/tests")
from sb_mock import MockSB
from beta_test_helpers import seed, SARA

URL = "file:///home/claude/formstark/beta/index.html"
T = datetime.date.today()


def ok(c, msg):
    print(("OK   " if c else "FAIL ") + msg)
    if not c:
        ok.bad += 1


ok.bad = 0


async def page(b, m, w, errs):
    ctx = await b.new_context(viewport={"width": w, "height": 844 if w < 600 else 1100})
    pg = await ctx.new_page()
    pg.on("pageerror", lambda e: errs.append("PAGEERROR " + str(e)))
    pg.on("console", lambda c: errs.append("CONSOLE " + c.text) if c.type == "error" else None)
    await pg.route("https://uxiyjsbhtijrhptwlibs.supabase.co/**", m.handle)
    await pg.goto(URL)
    await pg.wait_for_selector("#lgform")
    await pg.fill("#lg-mail", "sara@test.de")
    await pg.fill("#lg-pw", "pw1")
    await pg.click("#lg-go")
    await pg.wait_for_function("document.getElementById('lgform')===null", timeout=8000)
    await pg.wait_for_timeout(600)
    return ctx, pg


async def lauf(b, m, w, errs, tag):
    ctx, A = await page(b, m, w, errs)
    await A.click("[data-a=log]")
    await A.wait_for_selector("#lgw-add")
    # Übung hinzufügen: Liegestütze (pushup)
    await A.select_option("#lgw-add", "pushup")
    await A.click("[data-a=lgwadd]")
    await A.wait_for_selector("#lgw-r-0")
    ok(await A.query_selector("#lgw-s-0") is not None, "%s: zuerst Sätze × Wdh." % tag)
    s0, r0 = int(await A.input_value("#lgw-s-0")), int(await A.input_value("#lgw-r-0"))
    # auf Gesamtzahl umschalten
    await A.click("[data-a=lgwtot][data-v='0']")
    await A.wait_for_selector("#lgw-r-0")
    ok(await A.query_selector("#lgw-s-0") is None, "%s: Sätze-Feld verschwindet bei Gesamtzahl" % tag)
    btn = await A.inner_text("[data-a=lgwtot][data-v='0']")
    ok("Sätze" in btn, "%s: Knopf bietet Rückweg an (%s)" % (tag, btn))
    # Umschalten rechnet um: Sätze × Wdh. = Gesamtzahl
    v0 = await A.input_value("#lgw-r-0")
    ok(v0 == str(s0 * r0), "%s: %d×%d wird zu %d gesamt (%s)" % (tag, s0, r0, s0 * r0, v0))
    await A.fill("#lgw-r-0", "200")
    sw = await A.evaluate("document.documentElement.scrollWidth")
    ok(sw <= w + 1, "%s: kein Querscrollen (%d bei %d px)" % (tag, sw, w))
    await A.wait_for_timeout(1200)
    await A.screenshot(path="/tmp/claude-0/t/gesamt_%s.png" % tag)
    await A.click("[data-a=lgwsave]")
    await A.wait_for_timeout(1800)
    # Anzeige im Eintrag
    txt = await A.inner_text("#sheetHost")
    ok("200 Wdh." in txt and "1×200" not in txt, "%s: Anzeige „200 Wdh.“" % tag)
    # Speicherformat: s=1, r=200, keine Zusatzfelder
    # in der Datenbank (Martins Schnittstelle: uebungen=[{e,s,r,u,kg}])
    rows = [r for r in m.rows("workouts", SARA) if r.get("uebungen") and r["uebungen"][0].get("r") == 200]
    ok(len(rows) == 1 and rows[0]["uebungen"] == [{"e": "pushup", "s": 1, "r": 200, "u": "r", "kg": None}],
       "%s: Datenbank-Zeile mit Format {e,s,r,u,kg}: %s" % (tag, rows[0]["uebungen"] if rows else None))
    ctx2 = ctx
    return ctx2, A


async def main():
    m = MockSB()
    seed(m)
    errs = []
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx, A = await lauf(b, m, 375, errs, "375px")
        # zweites Gerät sieht den Eintrag
        ctxB, B = await page(b, m, 768, errs)
        await B.click("[data-a=log]")
        await B.wait_for_selector("#lgw-add")
        t = await B.inner_text("#sheetHost")
        ok("200 Wdh." in t, "zweites Gerät (iPad-Breite) sieht die 200 Liegestütze")
        # Rückweg: Sätze × Wdh. und normal speichern; Anzeige bleibt „4×12“
        await B.wait_for_selector("#lgw-add")
        await B.select_option("#lgw-add", "squat") if await B.query_selector("#lgw-add option[value=squat]") else None
        await B.click("[data-a=lgwadd]")
        await B.wait_for_selector("#lgw-s-0")
        await B.click("[data-a=lgwtot][data-v='0']")
        await B.click("[data-a=lgwtot][data-v='0']")
        ok(await B.query_selector("#lgw-s-0") is not None, "iPad: Rückweg zu Sätze × Wdh. klappt")
        await B.fill("#lgw-s-0", "4"); await B.fill("#lgw-r-0", "12")
        await B.click("[data-a=lgwsave]")
        await B.wait_for_timeout(1500)
        txt = await B.inner_text("#sheetHost")
        ok("4×12" in txt, "iPad: normale Eingabe zeigt weiter „4×12“")
        sw = await B.evaluate("document.documentElement.scrollWidth")
        ok(sw <= 769, "iPad: kein Querscrollen (%d)" % sw)
        await B.wait_for_timeout(1200)
        await B.screenshot(path="/tmp/claude-0/t/gesamt_ipad.png")
        real = [e for e in errs if "Failed to load resource" not in e]
        ok(not real, "keine Fehler in der Konsole: %s" % real[:3])
        await b.close()
    print("FEHLER:", ok.bad)
    sys.exit(1 if ok.bad else 0)


asyncio.run(main())
