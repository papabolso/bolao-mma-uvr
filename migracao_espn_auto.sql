-- Resultados automáticos da ESPN.
-- espn_evento: ID do evento (o importador grava sozinho ao importar o card).
-- espn_auto: liga/desliga a sincronização automática no Admin.
-- Pode rodar mais de uma vez.
alter table config add column if not exists espn_evento text default '';
alter table config add column if not exists espn_auto boolean default true;
