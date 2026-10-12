"""Nachgebautes Supabase (Anmeldung + Tabellen mit Zugriffsregeln) für Playwright-Tests.
Nur für Tests: läuft im Speicher, keine echten Daten."""
import json, time, datetime
from urllib.parse import urlparse, parse_qs

CORS = {
    "access-control-allow-origin": "*",
    "access-control-allow-headers": "apikey, authorization, content-type, prefer, x-client-info",
    "access-control-allow-methods": "GET, POST, PATCH, DELETE, OPTIONS",
}
PK = {"profile": ("user_id",), "workouts": ("user_id", "id"),
      "eintraege": ("user_id", "art", "id"), "tageswerte": ("user_id", "tag", "bereich")}


def now_iso():
    return datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")


class MockSB:
    def __init__(self):
        self.t = {k: {} for k in PK}
        self.users = {}       # email -> (passwort, uid)
        self.freig = set()    # (besitzer, leser)
        self.log = []         # (methode, tabelle, anzahl)
        self.fail_writes = False
        self.offline = False

    def add_user(self, email, pw, uid):
        self.users[email] = (pw, uid)

    def put(self, table, row):
        r = dict(row)
        r.setdefault("aktualisiert", now_iso())
        self.t[table][tuple(r[c] for c in PK[table])] = r

    def rows(self, table, uid=None):
        return [r for r in self.t[table].values() if uid is None or r["user_id"] == uid]

    def uid_of(self, req):
        a = req.headers.get("authorization", "")
        return a[len("Bearer tok-"):] if a.startswith("Bearer tok-") else None

    async def handle(self, route, req):
        if self.offline:
            return await route.abort('internetdisconnected')
        u = urlparse(req.url)
        if req.method == "OPTIONS":
            return await route.fulfill(status=204, headers=CORS)
        h = dict(CORS, **{"content-type": "application/json"})
        if u.path == "/auth/v1/token":
            q = parse_qs(u.query)
            body = json.loads(req.post_data or "{}")
            if q.get("grant_type") == ["password"]:
                ok = self.users.get(body.get("email"))
                if not ok or ok[0] != body.get("password"):
                    return await route.fulfill(status=400, headers=h, body=json.dumps({"error_description": "Invalid login credentials"}))
                uid = ok[1]
            else:
                uid = body.get("refresh_token", "").replace("r-", "")
            email = next(e for e, (p, i) in self.users.items() if i == uid)
            return await route.fulfill(status=200, headers=h, body=json.dumps({
                "access_token": "tok-" + uid, "refresh_token": "r-" + uid, "expires_in": 3600,
                "user": {"id": uid, "email": email}}))
        if u.path == "/auth/v1/logout":
            return await route.fulfill(status=204, headers=CORS)
        if u.path.startswith("/rest/v1/"):
            table = u.path.split("/")[-1]
            uid = self.uid_of(req)
            if not uid:
                return await route.fulfill(status=401, headers=h, body=json.dumps({"message": "JWT"}))
            readable = {uid} | {b for (b, l) in self.freig if l == uid}
            if req.method == "GET":
                q = parse_qs(u.query)
                rows = [r for r in self.t[table].values() if r["user_id"] in readable]
                for k, vals in q.items():
                    if k in ("select", "order", "limit", "offset"):
                        continue
                    op, _, val = vals[0].partition(".")
                    if op == "eq":
                        rows = [r for r in rows if str(r.get(k)) == val]
                    elif op == "neq":
                        rows = [r for r in rows if str(r.get(k)) != val]
                    elif op == "gte":
                        rows = [r for r in rows if str(r.get(k)) >= val]
                order = (q.get("order") or [""])[0]
                for col in reversed([c.split(".")[0] for c in order.split(",") if c]):
                    rows.sort(key=lambda r: str(r.get(col)))
                off = int((q.get("offset") or ["0"])[0]); lim = int((q.get("limit") or ["1000"])[0])
                rows = rows[off:off + lim]
                self.log.append(("GET", table, len(rows)))
                return await route.fulfill(status=200, headers=h, body=json.dumps(rows))
            if req.method == "POST":
                if self.fail_writes:
                    return await route.fulfill(status=500, headers=h, body=json.dumps({"message": "Serverfehler (Test)"}))
                rows = json.loads(req.post_data or "[]")
                for r in rows:
                    if r.get("user_id") != uid:
                        return await route.fulfill(status=403, headers=h, body=json.dumps({"message": "new row violates row-level security policy"}))
                for r in rows:
                    k = tuple(r[c] for c in PK[table])
                    cur = dict(self.t[table].get(k, {}))
                    cur.update(r)
                    cur["aktualisiert"] = now_iso()
                    self.t[table][k] = cur
                self.log.append(("POST", table, len(rows)))
                return await route.fulfill(status=201, headers=CORS)
        return await route.fulfill(status=404, headers=h, body="{}")
