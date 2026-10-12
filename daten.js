/* Formstark – Umwandlung zwischen dem App-Zustand S und Datenbank-Zeilen.
   Wird von der App (beta/) und vom Umzug (umzug.html) gemeinsam benutzt.
   Verlustfrei: zeilenZuS(sZuZeilen(S)) liefert wieder S (ohne gerätebezogene Felder). */
(function (root) {
  "use strict";

  /* Listen im Zustand S, deren Einträge einzelne Zeilen werden (Tabelle eintraege) */
  var LISTEN = ["prs", "recipes", "shop", "goals", "myw", "cex", "duels", "prog", "tests"];
  /* Tageslisten: log[Tag].acts / .food -> eintraege; log[Tag].wk -> workouts */
  var TAGLISTEN = ["acts", "food"];
  /* Landet nicht in der Datenbank (gerätebezogen oder abgeleitet) */
  var LOKAL = ["introSeen", "obLater", "hideInstall", "revSeen", "monSeen", "noPush", "lastBackup", "upd"];

  function istObj(x) { return x && typeof x === "object" && !Array.isArray(x); }
  function kopie(x) { return x === undefined ? undefined : JSON.parse(JSON.stringify(x)); }

  /* stabile Kurz-ID aus dem Inhalt (für Einträge ohne eigene id) */
  function hash(s) {
    var h1 = 0xdeadbeef, h2 = 0x41c6ce57;
    for (var i = 0; i < s.length; i++) {
      var c = s.charCodeAt(i);
      h1 = Math.imul(h1 ^ c, 2654435761);
      h2 = Math.imul(h2 ^ c, 1597334677);
    }
    h1 = Math.imul(h1 ^ (h1 >>> 16), 2246822507) ^ Math.imul(h2 ^ (h2 >>> 13), 3266489909);
    h2 = Math.imul(h2 ^ (h2 >>> 16), 2246822507) ^ Math.imul(h1 ^ (h1 >>> 13), 3266489909);
    return (4294967296 * (2097151 & h2) + (h1 >>> 0)).toString(36);
  }
  function eid(x, praefix, tag, i) {
    if (istObj(x) && x.id != null && x.id !== "") return String(x.id);
    return "g" + hash(praefix + "|" + (tag || "") + "|" + i + "|" + JSON.stringify(x));
  }

  /* Eintrag als daten-Objekt: der Eintrag selbst (Martins Schnittstelle: acts = {t,min,km,note}),
     plus _o = Reihenfolge. Keine Objekte werden als {_v: Wert} abgelegt. */
  function pack(x, i) {
    if (istObj(x)) {
      var d = kopie(x); d._o = i;
      if (!(x.id != null && x.id !== "")) d._ni = 1;     /* Eintrag hatte ursprünglich keine id */
      return d;
    }
    return { _v: kopie(x), _o: i };
  }
  function unpack(d, id) {
    if (d && Object.prototype.hasOwnProperty.call(d, "_v")) return kopie(d._v);
    var x = kopie(d), ohne = x._ni; delete x._o; delete x._ni;
    if (!ohne && (x.id == null || x.id === "")) x.id = id;   /* Zeilen von außen: id ergänzen */
    return x;
  }
  function ordnung(d) { return d && typeof d._o === "number" ? d._o : 1e9; }

  /* ---------- S -> Zeilen ---------- */
  function sZuZeilen(S) {
    var out = { profile: null, workouts: [], eintraege: [], tageswerte: [] };
    var einst = {};
    var k;
    for (k in S) {
      if (!Object.prototype.hasOwnProperty.call(S, k)) continue;
      if (k === "log" || k === "photos" || LOKAL.indexOf(k) >= 0) continue;
      if (LISTEN.indexOf(k) >= 0 && Array.isArray(S[k])) continue;
      einst[k] = kopie(S[k]);
    }
    var name = (S.profile && S.profile.name) || S.name || "Formstark";
    out.profile = { name: String(name), einstellungen: einst };

    LISTEN.forEach(function (art) {
      var L = Array.isArray(S[art]) ? S[art] : [];
      var ids = {};
      L.forEach(function (x, i) {
        var id = eid(x, art, "", i);
        while (ids[id]) id += "_";
        ids[id] = 1;
        out.eintraege.push({ art: art, id: id, tag: null, daten: pack(x, i), geloescht: false });
      });
    });

    var ph = S.photos || {};
    Object.keys(ph).forEach(function (id) {
      out.eintraege.push({ art: "photos", id: String(id), tag: null, daten: { _v: kopie(ph[id]), _o: 0 }, geloescht: false });
    });

    var log = S.log || {};
    Object.keys(log).forEach(function (tag) {
      var d = log[tag];
      if (!istObj(d)) return;
      Object.keys(d).forEach(function (key) {
        var v = d[key];
        if (key === "wk" && Array.isArray(v)) {
          var ids = {};
          v.forEach(function (w, i) {
            var id = eid(w, "wk", tag, i);
            while (ids[id]) id += "_";
            ids[id] = 1;
            var ex = {};
            Object.keys(w).forEach(function (f) {
              if (["id", "n", "min", "feel", "note", "items"].indexOf(f) < 0) ex[f] = kopie(w[f]);
            });
            ex.o = i;
            if (!(w.id != null && w.id !== "")) ex.noId = 1;
            out.workouts.push({
              id: id, tag: tag,
              name: w.n == null ? null : String(w.n),
              minuten: typeof w.min === "number" ? w.min : (w.min == null ? null : Number(w.min) || null),
              gefuehl: typeof w.feel === "number" ? w.feel : null,
              notiz: w.note == null ? null : String(w.note),
              quelle: "app",
              uebungen: kopie(w.items || []),
              extra: ex,
              geloescht: false
            });
            /* Rohwerte für verlustfreie Rückumwandlung, wenn sie nicht zur Spalte passen */
            var z = out.workouts[out.workouts.length - 1];
            if (z.minuten !== w.min) ex.rawMin = kopie(w.min);
            if (z.gefuehl !== w.feel) ex.rawFeel = kopie(w.feel);
            if (z.name !== w.n) ex.rawN = kopie(w.n);
            if (z.notiz !== w.note) ex.rawNote = kopie(w.note);
            ex.had = ["n", "min", "feel", "note", "items"].filter(function (f) { return Object.prototype.hasOwnProperty.call(w, f); });
          });
        } else if (TAGLISTEN.indexOf(key) >= 0 && Array.isArray(v)) {
          var ids2 = {};
          v.forEach(function (x, i) {
            var id = eid(x, key, tag, i);
            while (ids2[id]) id += "_";
            ids2[id] = 1;
            out.eintraege.push({ art: key, id: id, tag: tag, daten: pack(x, i), geloescht: false });
          });
        } else {
          out.tageswerte.push({ tag: tag, bereich: key, daten: { v: kopie(v) } });
        }
      });
      /* Tag ohne jeden Inhalt merken, damit leere Tage erhalten bleiben */
      if (!Object.keys(d).length) out.tageswerte.push({ tag: tag, bereich: "_leer", daten: { v: 1 } });
    });
    return out;
  }

  /* ---------- Zeilen -> S ---------- */
  function sortO(a, b) { return (a.o || 0) - (b.o || 0); }

  function zeilenZuS(rows) {
    var S = {};
    var p = rows.profile;
    if (p && istObj(p.einstellungen)) {
      Object.keys(p.einstellungen).forEach(function (k) { S[k] = kopie(p.einstellungen[k]); });
    }
    S.log = {};
    S.photos = {};
    LISTEN.forEach(function (art) { S[art] = []; });

    var tmp = {};
    (rows.eintraege || []).forEach(function (r) {
      if (r.geloescht || !r.daten) return;
      if (r.art === "photos") { S.photos[r.id] = kopie(r.daten._v); return; }
      var o = ordnung(r.daten), v = unpack(r.daten, r.id);
      if (LISTEN.indexOf(r.art) >= 0) {
        (tmp[r.art] = tmp[r.art] || []).push({ o: o, v: v });
      } else if (TAGLISTEN.indexOf(r.art) >= 0 && r.tag) {
        var key = r.tag + "|" + r.art;
        (tmp[key] = tmp[key] || []).push({ o: o, v: v });
      }
    });
    LISTEN.forEach(function (art) { S[art] = (tmp[art] || []).sort(sortO).map(function (x) { return x.v; }); });
    Object.keys(tmp).forEach(function (key) {
      if (key.indexOf("|") < 0) return;
      var i = key.indexOf("|"), tag = key.slice(0, i), art = key.slice(i + 1);
      S.log[tag] = S.log[tag] || {};
      S.log[tag][art] = tmp[key].sort(sortO).map(function (x) { return x.v; });
    });

    var wk = {};
    (rows.workouts || []).forEach(function (r) {
      if (r.geloescht) return;
      var ex = istObj(r.extra) ? r.extra : {};
      var had = Array.isArray(ex.had) ? ex.had : null;
      var w = {};
      if (!ex.noId) w.id = r.id;
      var f;
      for (f in ex) if (["o", "had", "noId", "rawMin", "rawFeel", "rawN", "rawNote"].indexOf(f) < 0) w[f] = kopie(ex[f]);
      function setze(feld, wert, raw, hatRaw) {
        if (had && had.indexOf(feld) < 0) return;
        w[feld] = hatRaw ? kopie(raw) : wert;
      }
      /* Zeilen von außen (z. B. Martins Assistent) haben kein extra: sinnvolle Vorgaben setzen */
      var fremd = !had;
      setze("n", fremd ? (r.name || "Workout") : r.name, ex.rawN, "rawN" in ex);
      setze("min", r.minuten, ex.rawMin, "rawMin" in ex);
      setze("feel", fremd ? (r.gefuehl || 0) : r.gefuehl, ex.rawFeel, "rawFeel" in ex);
      setze("note", fremd ? (r.notiz || "") : r.notiz, ex.rawNote, "rawNote" in ex);
      if (fremd && w.src === undefined) w.src = "";
      setze("items", kopie(r.uebungen || []), null, false);
      var t = r.tag;
      (wk[t] = wk[t] || []).push({ o: ex.o || 0, v: w });
    });
    Object.keys(wk).forEach(function (t) {
      S.log[t] = S.log[t] || {};
      S.log[t].wk = wk[t].sort(sortO).map(function (x) { return x.v; });
    });

    (rows.tageswerte || []).forEach(function (r) {
      if (!r.daten || r.daten._geloescht) return;
      S.log[r.tag] = S.log[r.tag] || {};
      if (r.bereich === "_leer") return;
      S.log[r.tag][r.bereich] = kopie(r.daten.v);
    });
    return S;
  }

  /* ---------- Unterschiede -> nur geänderte Zeilen ---------- */
  function schluessel(tabelle, r) {
    if (tabelle === "workouts") return r.id;
    if (tabelle === "eintraege") return r.art + "|" + r.id;
    return r.tag + "|" + r.bereich;
  }
  function inhalt(r) { return JSON.stringify(r); }

  /* alt, neu: Ergebnisse von sZuZeilen. Liefert Zeilen zum Schreiben (upsert). */
  function diffZeilen(alt, neu) {
    var out = { profile: null, workouts: [], eintraege: [], tageswerte: [] };
    if (!alt || !alt.profile || inhalt(alt.profile) !== inhalt(neu.profile)) out.profile = neu.profile;
    ["workouts", "eintraege", "tageswerte"].forEach(function (t) {
      var a = {}, n = {};
      ((alt && alt[t]) || []).forEach(function (r) { a[schluessel(t, r)] = r; });
      (neu[t] || []).forEach(function (r) { n[schluessel(t, r)] = r; });
      Object.keys(n).forEach(function (k) {
        if (!a[k] || inhalt(a[k]) !== inhalt(n[k])) out[t].push(n[k]);
      });
      Object.keys(a).forEach(function (k) {
        if (n[k]) return;
        var r = kopie(a[k]);
        if (t === "tageswerte") r.daten = { _geloescht: true };
        else r.geloescht = true;
        out[t].push(r);
      });
    });
    return out;
  }

  function leer(d) {
    return !d.profile && !d.workouts.length && !d.eintraege.length && !d.tageswerte.length;
  }

  var FSD = { sZuZeilen: sZuZeilen, zeilenZuS: zeilenZuS, diffZeilen: diffZeilen, leer: leer, LOKAL: LOKAL, LISTEN: LISTEN };
  if (typeof module !== "undefined" && module.exports) module.exports = FSD;
  else root.FSD = FSD;
})(typeof window !== "undefined" ? window : this);
