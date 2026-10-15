"""Test: Schritte aus dem iPhone-Kurzbefehl (?steps=, ?date=, ?days=) mit Supabase-Anmeldung.
Prüft: einzelner Tag, mehrere Tage nachtragen (nur leere Tage, nichts überschreiben),
deutsche Zahlen, Anmeldung nach dem Öffnen des Links, Konsole leer."""
import asyncio, sys, datetime
from playwright.async_api import async_playwright
sys.path.insert(0, "/home/claude/formstark/tests")
from sb_mock import MockSB
from beta_test_helpers import seed, SARA

URL = "file:///home/claude/formstark/beta/index.html"
T = datetime.date.today()
D = lambda n: str(T - datetime.timedelta(days=n))


def ok(c, msg):
    print(("OK   " if c else "FAIL ") + msg)
    if not c:
        ok.bad += 1


ok.bad = 0


def steps(m, tag):
    r = m.t["tageswerte"].get((SARA, tag, "steps"))
    return r["daten"].get("v") if r and not r["daten"].get("_geloescht") else None


async def ctx_page(b, m, errs, w=375):
    ctx = await b.new_context(viewport={"width": w, "height": 844})
    pg = await ctx.new_page()
    pg.on("pageerror", lambda e: errs.append("PAGEERROR " + str(e)))
    pg.on("console", lambda c: errs.append("CONSOLE " + c.text) if c.type == "error" else None)
    await pg.route("https://uxiyjsbhtijrhptwlibs.supabase.co/**", m.handle)
    return ctx, pg


async def fill_login(pg):
    await pg.wait_for_selector("#lgform")
    await pg.fill("#lg-mail", "sara@test.de")
    await pg.fill("#lg-pw", "pw1")
    await pg.click("#lg-go")
    await pg.wait_for_function("document.getElementById('lgform')===null", timeout=8000)


async def main():
    m = MockSB()
    seed(m)
    errs = []
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx, A = await ctx_page(b, m, errs)
        await A.goto(URL)
        await fill_login(A)
        await A.wait_for_timeout(800)

        # 1 einzelner Wert für heute
        await A.goto(URL + "?steps=8123")
        await A.wait_for_timeout(2500)
        ok(steps(m, D(0)) == 8123, "?steps=8123 trägt heute ein (%s)" % steps(m, D(0)))
        ok("steps" not in A.url, "Adresse wird danach bereinigt")

        # 2 deutsche Schreibweise mit Punkt, anderer Tag
        await A.goto(URL + "?steps=8.123&date=" + D(3))
        await A.wait_for_timeout(2500)
        ok(steps(m, D(3)) == 8123, "8.123 mit date= wird 8123 (%s)" % steps(m, D(3)))

        # 3 mehrere Tage: leere füllen, vorhandenen nicht überschreiben, Zukunft ignorieren, heute darf steigen
        m.put("tageswerte", {"user_id": SARA, "tag": D(2), "bereich": "steps", "daten": {"v": 4500}})
        tomorrow = str(T + datetime.timedelta(days=1))
        q = "?days=%s:5000,%s:6000,%s:7000,%s:999,%s:9000" % (D(1), D(2), D(4), tomorrow, D(0))
        await A.goto(URL + q)
        await A.wait_for_function("document.body.innerText.includes('nachgetragen')", timeout=6000)
        await A.wait_for_timeout(2000)
        ok(steps(m, D(1)) == 5000, "leerer Tag gestern gefüllt (%s)" % steps(m, D(1)))
        ok(steps(m, D(2)) == 4500, "vorhandener Wert bleibt 4500 (%s)" % steps(m, D(2)))
        ok(steps(m, D(4)) == 7000, "leerer Tag vor 4 Tagen gefüllt (%s)" % steps(m, D(4)))
        ok(steps(m, tomorrow) is None, "Zukunft wird ignoriert")
        ok(steps(m, D(0)) == 9000, "heute darf steigen: 8123 wird 9000 (%s)" % steps(m, D(0)))
        txt = await A.inner_text("body")
        ok("3 Tage" in txt and "1 schon vorhanden" in txt, "Hinweis nennt 3 Tage nachgetragen, 1 vorhanden")
        # Lower Wert für heute überschreibt nicht (Liste)
        await A.goto(URL + "?days=%s:100" % D(0))
        await A.wait_for_timeout(2000)
        ok(steps(m, D(0)) == 9000, "Liste senkt heute nie (%s)" % steps(m, D(0)))

        # 4 andere Trennzeichen und Zahlenformate
        q = "?days=%s=8123,5;%s:1.234" % (D(5), D(6))
        await A.goto(URL + q)
        await A.wait_for_timeout(2500)
        ok(steps(m, D(5)) == 8124, "Komma-Dezimal 8123,5 wird 8124 (%s)" % steps(m, D(5)))
        ok(steps(m, D(6)) == 1234, "1.234 wird 1234 (%s)" % steps(m, D(6)))

        # 5 acc= von früher stört nicht (Sara hat Slot "me")
        await A.goto(URL + "?acc=martin&steps=100")
        await A.wait_for_timeout(2500)
        ok("Sara" in await A.inner_text("#ttl"), "?acc=martin wird ignoriert, Titel bleibt Sara")
        ok(steps(m, D(0)) == 100, "?steps= überschreibt heute wie bisher (%s)" % steps(m, D(0)))
        sw = await A.evaluate("document.documentElement.scrollWidth")
        ok(sw <= 376, "375 px: kein Querscrollen (%d)" % sw)

        # 6 noch nicht angemeldet: Link öffnen, anmelden, danach ist es eingetragen
        m2 = MockSB()
        seed(m2)
        ctx2, N = await ctx_page(b, m2, errs)
        await N.goto(URL + "?days=%s:5000,%s:6000&steps=7777" % (D(1), D(2)))
        await fill_login(N)
        await N.wait_for_timeout(3000)
        ok(steps(m2, D(0)) == 7777, "erst anmelden, dann eingetragen: heute 7777 (%s)" % steps(m2, D(0)))
        ok(steps(m2, D(1)) == 5000 and steps(m2, D(2)) == 6000, "und die Tage davor (%s, %s)" % (steps(m2, D(1)), steps(m2, D(2))))

        real = [e for e in errs if "Failed to load resource" not in e]
        ok(not real, "keine Fehler in der Konsole: %s" % real[:3])
        await b.close()
    print("FEHLER:", ok.bad)
    sys.exit(1 if ok.bad else 0)


asyncio.run(main())
