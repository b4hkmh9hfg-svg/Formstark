# Notizen zum Umbau (ohne Daten und Geheimnisse)

## Stand 13.10.2026 (Phase 5 und 6 gebaut, noch nicht getestet mit echtem Supabase)
- Sicherung (sicherung.html) und GitHub Pages laufen: https://b4hkmh9hfg-svg.github.io/Formstark/
- Supabase-Projekt angelegt (Frankfurt), E-Mail-Anmeldung an, Nutzerin angelegt. Martin: wird angelegt.
- SQL 001 (Tabellen) und 002 (Regeln) ausgeführt, Test ohne Login: "permission denied" (richtig).
- SQL 003 (Spalte workouts.extra) von der Nutzerin ausführen lassen; SQL 004 (Freigaben beider Personen) erst, wenn beide Konten existieren.
- daten.js: Umwandlung App-Zustand <-> Zeilen, getestet (tests/daten.test.js).

## Entscheidungen
- Die App speichert den Zustand S je Profil als Firestore-Feld j (JSON-Text) + upd.
- Eintraege: daten = der Eintrag selbst (acts = {t,min,km,note}), Reihenfolge in _o.
- Fotos: Tabelle eintraege, art = photos (Größe vor dem Umzug prüfen).
- Nur hideInstall und noPush bleiben im localStorage; introSeen & Co. werden mitsynchronisiert.

## Gebaut
- beta/index.html: App mit Anmeldung (E-Mail + Passwort), Speichern über Outbox + upsert, Nachladen (Start, Zurückkehren, online, alle 60 s), Zusammen über freigaben. Erzeugt mit tools/build_beta.py aus der Netlify-Version.
- Kleiner eigener Supabase-Client in der App (keine Fremdbibliothek, da das npm-Register für Claude gesperrt ist).
- umzug.html: liest das alte Firestore-Profil (nur lesen), schreibt Zeilen, vergleicht alt/neu.
- Tests: tests/daten.test.js (node), tests/beta_test.py und tests/umzug_test.py (Playwright, nachgebautes Supabase in tests/sb_mock.py).

## Offen
- SQL 003 und 004 ausführen, Martin-Konto anlegen, Registrierung sperren.
- /beta/ testen, Umzug je Person, Martin informieren (Schnittstelle), Umschalten.
