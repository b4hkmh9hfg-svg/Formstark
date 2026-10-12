-- Formstark: Grundgerüst (Tabellen)
create table if not exists public.profile (
  user_id uuid primary key default auth.uid() references auth.users(id) on delete cascade,
  name text not null,
  einstellungen jsonb not null default '{}'::jsonb,
  aktualisiert timestamptz not null default now()
);

create table if not exists public.workouts (
  user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  id text not null,
  tag date not null,
  name text, minuten int, gefuehl int, notiz text,
  quelle text not null default 'app',
  uebungen jsonb not null default '[]'::jsonb,
  geloescht boolean not null default false,
  aktualisiert timestamptz not null default now(),
  primary key (user_id, id)
);
create index if not exists workouts_sync on public.workouts (user_id, aktualisiert);

create table if not exists public.eintraege (
  user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  art text not null,
  id text not null,
  tag date,
  daten jsonb not null,
  geloescht boolean not null default false,
  aktualisiert timestamptz not null default now(),
  primary key (user_id, art, id)
);
create index if not exists eintraege_sync on public.eintraege (user_id, aktualisiert);

create table if not exists public.tageswerte (
  user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  tag date not null,
  bereich text not null,
  daten jsonb not null,
  aktualisiert timestamptz not null default now(),
  primary key (user_id, tag, bereich)
);
create index if not exists tageswerte_sync on public.tageswerte (user_id, aktualisiert);

create table if not exists public.freigaben (
  besitzer uuid not null references auth.users(id) on delete cascade,
  leser uuid not null references auth.users(id) on delete cascade,
  primary key (besitzer, leser)
);

create or replace function public.setze_aktualisiert() returns trigger
language plpgsql as $$ begin new.aktualisiert = now(); return new; end $$;

drop trigger if exists t_prof on public.profile;
drop trigger if exists t_wk on public.workouts;
drop trigger if exists t_ein on public.eintraege;
drop trigger if exists t_tag on public.tageswerte;
create trigger t_prof before update on public.profile for each row execute function public.setze_aktualisiert();
create trigger t_wk before update on public.workouts for each row execute function public.setze_aktualisiert();
create trigger t_ein before update on public.eintraege for each row execute function public.setze_aktualisiert();
create trigger t_tag before update on public.tageswerte for each row execute function public.setze_aktualisiert();
