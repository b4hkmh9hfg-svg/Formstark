-- Formstark: Regeln (Row Level Security)
alter table public.profile enable row level security;
alter table public.workouts enable row level security;
alter table public.eintraege enable row level security;
alter table public.tageswerte enable row level security;
alter table public.freigaben enable row level security;

create or replace function public.darf_lesen(p_besitzer uuid) returns boolean
language sql stable security definer set search_path = public as $$
  select p_besitzer = auth.uid()
      or exists (select 1 from public.freigaben f where f.besitzer = p_besitzer and f.leser = auth.uid())
$$;

do $$
declare t text;
begin
  foreach t in array array['profile','workouts','eintraege','tageswerte'] loop
    execute format('drop policy if exists lesen on public.%I', t);
    execute format('drop policy if exists anlegen on public.%I', t);
    execute format('drop policy if exists aendern on public.%I', t);
    execute format('create policy lesen on public.%I for select using (public.darf_lesen(user_id))', t);
    execute format('create policy anlegen on public.%I for insert with check (user_id = auth.uid())', t);
    execute format('create policy aendern on public.%I for update using (user_id = auth.uid()) with check (user_id = auth.uid())', t);
  end loop;
end $$;

drop policy if exists f_lesen on public.freigaben;
drop policy if exists f_anlegen on public.freigaben;
drop policy if exists f_loeschen on public.freigaben;
create policy f_lesen on public.freigaben for select using (besitzer = auth.uid() or leser = auth.uid());
create policy f_anlegen on public.freigaben for insert with check (besitzer = auth.uid());
create policy f_loeschen on public.freigaben for delete using (besitzer = auth.uid());

-- Rechte: nur angemeldete Personen, nichts für anonym
revoke all on public.profile, public.workouts, public.eintraege, public.tageswerte, public.freigaben from anon;
grant select, insert, update on public.profile, public.workouts, public.eintraege, public.tageswerte to authenticated;
grant select, insert, delete on public.freigaben to authenticated;
