# Notizen zum Umbau (ohne Daten und Geheimnisse)

## Stand 12.10.2026
- Sicherung (sicherung.html) und GitHub Pages laufen: https://b4hkmh9hfg-svg.github.io/Formstark/
- Supabase-Projekt angelegt (Frankfurt), E-Mail-Anmeldung an, Nutzerin angelegt. Martin: wird angelegt.
- SQL 001 (Tabellen) und 002 (Regeln) ausgeführt, Test ohne Login: "permission denied" (richtig).
- SQL 003 (Spalte workouts.extra für App-Zusatzfelder) steht noch aus.
- daten.js: Umwandlung App-Zustand <-> Zeilen, getestet (tests/daten.test.js).

## Entscheidungen
- Die App speichert den Zustand S je Profil als Firestore-Feld j (JSON-Text) + upd.
- Eintraege: daten = der Eintrag selbst (acts = {t,min,km,note}), Reihenfolge in _o.
- Fotos: Tabelle eintraege, art = photos (Größe vor dem Umzug prüfen).
- Gerätebezogene Felder (introSeen, hideInstall, …) bleiben im localStorage.

## Offen
- App unter /beta/ an Supabase anschließen, umzug.html, Tests, Martin informieren, Umschalten.
