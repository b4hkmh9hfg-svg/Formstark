-- Formstark: beide Personen dürfen die Daten der jeweils anderen lesen (Ansicht "Zusammen").
-- Läuft nur, wenn es genau zwei Konten gibt; sonst passiert nichts.
insert into public.freigaben (besitzer, leser)
select a.id, b.id
from auth.users a
join auth.users b on a.id <> b.id
where (select count(*) from auth.users) = 2
on conflict do nothing;
