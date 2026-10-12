# Formstark – Regeln für Claude
- Antworte auf Deutsch, einfach und kurz. Die Nutzerin arbeitet nur mit dem iPad/iPhone, ohne Kommandozeile: beschreibe jeden Klick (GitHub, Supabase) konkret.
- Kleine Schritte: jede Änderung in eigenem Zweig + Pull Request; neue Versionen zuerst unter /beta/ testen lassen.
- Vor jedem Vorschlag testen: 375 px + iPad-Breite, Fehlerkonsole leer, Abgleich mit zwei Tabs/Geräten.
- Nutzerdaten nie löschen/überschreiben ohne Zustimmung. Gelöscht wird per geloescht = true.
- Geheimnisse nie in Code/Repo/Chat: kein service_role-Key, kein Team-Code, keine Sicherungsdateien. Im Code nur SUPABASE_URL + anon/publishable key.
- Datenbank-Änderungen als nummerierte Dateien in sql/ (001, 002, …), danach RLS-Probe ohne Login.

## Architektur
- GitHub Pages (main, Root). Supabase: profile, workouts, eintraege, tageswerte, freigaben – ein Eintrag = eine Zeile.
- App arbeitet mit S; Laden = Zeilen → Cache → zeilenZuS(); Speichern = diffZeilen() → Outbox → upsert (daten.js).
- Nachladen bei Start, visibilitychange, online, alle 60 s. Neue Daten nie verwerfen, nur verzögert rendern.

## Schnittstelle für Martins Assistent (nicht kaputt machen)
- Tabelle workouts (id, tag, name, minuten, gefuehl, notiz, quelle, uebungen=[{e,s,r,u,kg}]), eintraege art='acts' (daten={t,min,km,note}). Übungs-IDs nie umbenennen/entfernen.
- Änderungen daran vorher mit Martin absprechen.
