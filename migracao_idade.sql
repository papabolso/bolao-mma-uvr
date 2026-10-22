-- Data de nascimento dos lutadores (AAAA-MM-DD), vinda do importador da ESPN.
-- A idade é calculada na hora de mostrar. Pode rodar mais de uma vez.
alter table lutas add column if not exists nasc_1 text default '';
alter table lutas add column if not exists nasc_2 text default '';
