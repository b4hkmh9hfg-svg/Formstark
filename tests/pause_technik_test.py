"""Test: Technik nachlesen in der Trainings-Pause + neue Übungs-Animationen.
Prüft: Knopf in der Pause, Hinweise und typische Fehler sichtbar, Pause-Timer läuft weiter,
Hinweisbox schließt sich beim Start des nächsten Satzes, 375 px ohne Querscrollen,
neue Animationen werden gezeichnet, Konsole leer."""
import asyncio, sys
from playwright.async_api import async_playwright
sys.path.insert(0, "/home/claude/formstark/tests")
from sb_mock import MockSB
from beta_test_helpers import seed

URL = "file:///home/claude/formstark/beta/index.html"


def ok(c, msg):
    print(("OK   " if c else "FAIL ") + msg)
    if not c:
        ok.bad += 1


ok.bad = 0


async def main():
    m = MockSB()
    seed(m)
    errs = []
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await b.new_context(viewport={"width": 375, "height": 844})
        A = await ctx.new_page()
        A.on("pageerror", lambda e: errs.append("PAGEERROR " + str(e)))
        A.on("console", lambda c: errs.append("CONSOLE " + c.text) if c.type == "error" else None)
        await A.route("https://uxiyjsbhtijrhptwlibs.supabase.co/**", m.handle)
        await A.goto(URL)
        await A.wait_for_selector("#lgform")
        await A.fill("#lg-mail", "sara@test.de")
        await A.fill("#lg-pw", "pw1")
        await A.click("#lg-go")
        await A.wait_for_function("document.getElementById('lgform')===null", timeout=8000)
        await A.wait_for_timeout(800)

        # Training starten: erste Einheit, erste Aufwärmübung, Satz fertig -> Pause
        await A.evaluate("document.querySelector('[data-a=train]').click()")
        await A.wait_for_selector("[data-a=plbegin]", timeout=5000)
        ok(True, "Training-Player öffnet")
        await A.click("[data-a=plbegin]")
        await A.wait_for_selector("[data-a=plset]", timeout=8000)
        await A.click("[data-a=plset]")
        await A.wait_for_selector("[data-a=plrestskip]", timeout=5000)
        btn = await A.query_selector(".pl-cue [data-a=plcues]")
        ok(btn is not None, "in der Pause gibt es den Knopf zum Nachlesen")
        txt = await btn.inner_text() if btn else ""
        ok("Technik nachlesen" in txt, "Beschriftung: %s" % txt)

        t1 = await A.inner_text("#pl-t")
        await btn.click()
        await A.wait_for_selector(".cuesbox", timeout=3000)
        box = await A.inner_text(".cuesbox")
        n_cues = await A.locator(".cuesbox ol.cues li").count()
        ok(n_cues >= 1, "%d Hinweise zur Ausführung sichtbar" % n_cues)
        ok("typische fehler" in box.lower(), "Typische Fehler sichtbar")
        sw = await A.evaluate("document.documentElement.scrollWidth")
        ok(sw <= 376, "375 px: kein Querscrollen (%d)" % sw)
        await A.wait_for_timeout(1500)
        await A.screenshot(path="/tmp/claude-0/t/pause_technik.png")
        t2 = await A.inner_text("#pl-t")
        ok(t1 != t2, "Pause-Timer läuft weiter (%s -> %s)" % (t1, t2))
        # schließen mit ×
        await A.click(".cuesbox [data-a=plcues]")
        await A.wait_for_timeout(300)
        ok(await A.query_selector(".cuesbox") is None, "Hinweise lassen sich schließen")
        # wieder öffnen, Pause überspringen: Box muss weg sein, wenn der Satz beginnt
        await A.click(".pl-cue [data-a=plcues]")
        await A.wait_for_selector(".cuesbox")
        await A.click("[data-a=plrestskip]")
        await A.wait_for_timeout(600)
        ok(await A.query_selector(".cuesbox") is None, "Beim Start des nächsten Satzes ist die Box zu")

        # neue Animationen: Übung im Nachtragen hinzufügen, Figur wird gezeichnet
        await A.evaluate("document.querySelector('[data-a=plx]')&&document.querySelector('[data-a=plx]').click()")
        await A.reload()
        await A.wait_for_timeout(2000)
        await A.evaluate("document.querySelector('[data-a=log]').click()")
        await A.wait_for_selector("#lgw-add")
        ids = ["jacks", "mclimb", "gfront", "bandfront", "crunch", "bicycle", "kbswing", "cobra"]
        for i, eid in enumerate(ids):
            await A.select_option("#lgw-add", eid)
            await A.click("[data-a=lgwadd]")
            await A.wait_for_selector("#lgw-r-%d" % i)
        await A.wait_for_timeout(500)
        for eid in ids:
            n = await A.locator('#sheetHost [data-fig="%s"] svg line' % eid).count()
            ok(n > 5, "Figur %s wird gezeichnet (%d Linien)" % (eid, n))
        await A.wait_for_timeout(1200)
        await A.evaluate("document.querySelector('#sheetHost').scrollTo&&0")
        await A.screenshot(path="/tmp/claude-0/t/neue_figuren.png", full_page=False)

        real = [e for e in errs if "Failed to load resource" not in e]
        ok(not real, "keine Fehler in der Konsole: %s" % real[:3])
        await b.close()
    print("FEHLER:", ok.bad)
    sys.exit(1 if ok.bad else 0)


asyncio.run(main())
