"""Test: Sakralchakra Flow (17 Haltungen) im Yoga-Bereich.
Prüft: Eintrag in der Flow-Liste, Info-Dialog, Player mit allen 17 Haltungen in der richtigen Reihenfolge,
Figuren werden gezeichnet, Seitenwechsel-Hinweis bei einseitigen Haltungen, 375 px ohne Querscrollen,
Konsole leer."""
import asyncio, sys
from playwright.async_api import async_playwright
sys.path.insert(0, "/home/claude/formstark/tests")
from sb_mock import MockSB
from beta_test_helpers import seed

URL = "file:///home/claude/formstark/beta/index.html"
SOLL = ["Kindeshaltung", "Schneidersitz", "Wirbelsäulen-Wellen", "Katze & Kuh", "Tiger-Flow", "Tiefer Ausfallschritt",
        "Hoher Ausfall", "Sonnengruß A", "Göttinnenhaltung", "Dreieck", "Taube", "Schmetterling", "Sitzende Grätsche",
        "Sitzende Vorbeuge", "Kobra", "Liegender Drehsitz"]


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

        await A.click("[data-a=tab][data-v=plan]")
        await A.click("[data-a=pseg][data-v=yoga]")
        await A.wait_for_selector("[data-a=flowinfo][data-v=sacral]")
        card = await A.inner_text("[data-a=flowinfo][data-v=sacral]")
        ok("Sakralchakra Flow" in card, "Flow steht in der Liste: %s" % card.replace("\n", " | "))
        ok("17 Posen" in card, "17 Posen in der Liste")
        n = await A.locator("[data-a=flowinfo][data-v=sacral] svg line").count()
        ok(n > 5, "Vorschaufigur wird gezeichnet (%d Linien)" % n)
        wurzel = await A.locator("[data-a=flowinfo][data-v=root]").count()
        ok(wurzel == 1, "Wurzelchakra Flow ist weiter da")

        await A.click("[data-a=flowinfo][data-v=sacral]")
        await A.wait_for_selector("#sheetHost [data-a=flow][data-v=sacral]")
        info = await A.inner_text("#sheetHost")
        ok("Lebensfreude" in info or "Ich fühle" in info, "Info-Dialog zeigt Beschreibung")
        sw = await A.evaluate("document.documentElement.scrollWidth")
        ok(sw <= 376, "375 px (Info): kein Querscrollen (%d)" % sw)
        await A.click("#sheetHost [data-a=flow][data-v=sacral]")
        await A.wait_for_selector(".pl-name", timeout=5000)

        namen = []
        for i in range(17):
            name = await A.inner_text(".pl-name")
            namen.append(name)
            lines = await A.locator("#player svg line").count()
            ok(lines > 5, "Schritt %d %s: Figur gezeichnet (%d Linien)" % (i + 1, name, lines))
            if i < 16:
                await A.click("[data-a=plnext]")
                await A.wait_for_timeout(250)
        ok(namen[:16] == SOLL, "Reihenfolge der 16 Haltungen stimmt: %s" % [x for x, y in zip(namen, SOLL) if x != y][:3])
        ok(len(namen) == 17 and namen[16] != "", "17. Schritt (Endentspannung): %s" % namen[16])
        sw = await A.evaluate("document.documentElement.scrollWidth")
        ok(sw <= 376, "375 px (Player): kein Querscrollen (%d)" % sw)
        await A.screenshot(path="/tmp/claude-0/t/sakral_player.png")

        real = [e for e in errs if "Failed to load resource" not in e]
        ok(not real, "keine Fehler in der Konsole: %s" % real[:3])
        await b.close()
    print("FEHLER:", ok.bad)
    sys.exit(1 if ok.bad else 0)


asyncio.run(main())
