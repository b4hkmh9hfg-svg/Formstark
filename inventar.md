# Formstark – Inventar (Phase 4.1)

Stand: 12.10.2026, aus dem Code von app.html (Zustand S je Profil)

| Kategorie | Felder in Formstark | Ziel |
|---|---|---|
| Workouts | log[Tag].wk (id, n, min, feel, note, items[{e,s,r,u,kg}]) | workouts |
| Andere Listen mit id | log[Tag].acts (Ausdauer), log[Tag].food (Essen), prs (persönliche Rekorde), recipes, shop, goals, myw (eigene Workouts), cex, duels, prog, tests, fav, xwfav | eintraege (art = acts, food, prs, recipes, shop, goals, myw, cex, duels, prog, tests, fav, xwfav) |
| Einzelwerte pro Tag | log[Tag].steps, water, med, done[], flows[], sets{}, kg{}, rate{}, adapt{}, check{weight, sleepH, mood, pain, thoughts} | tageswerte (bereich = steps, water, med, done, flows, sets, kg, rate, adapt, check) |
| Einstellungen / Profil | profile, body, tg, water, rest, psize, kind, name, skin, voice, voiceName, voiceStyle, music, mv, cycle, start, week, mods, lvl, mp, mpDone, ch, chShare, custom, photos, v | profile.einstellungen (photos später prüfen: evtl. groß) |
| Gerätebezogen | introSeen, obLater, hideInstall, revSeen, monSeen, noPush, lastBackup | bleibt in localStorage |

Offene Punkte
- photos kann groß sein (Bilder im Zustand). Vorschlag: zuerst Größe prüfen, dann entscheiden.
- Listen ohne id bekommen beim Umzug eine stabile id.
- Die App speichert S direkt als Firestore-Felder (nicht als Feld j). Umzug liest beide Formen.
