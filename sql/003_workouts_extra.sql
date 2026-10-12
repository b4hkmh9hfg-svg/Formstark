-- Formstark: zusätzliche Felder eines Workouts (z. B. Programm-Verweis der App), ohne die bestehenden Spalten zu ändern
alter table public.workouts add column if not exists extra jsonb not null default '{}'::jsonb;
