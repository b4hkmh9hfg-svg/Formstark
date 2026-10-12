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

