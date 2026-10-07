-- Cartel dos lutadores (V-D-E, ex: '4-1-0'), vindo do importador da ESPN.
-- Aparece embaixo do nome no card de palpite. Pode rodar mais de uma vez.
alter table lutas add column if not exists rec_1 text default '';
alter table lutas add column if not exists rec_2 text default '';
