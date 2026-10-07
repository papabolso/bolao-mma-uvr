-- Últimas 3 lutas de cada lutador (JSON), vindas do importador da ESPN.
-- Aparecem ao abrir a setinha "Últimas lutas" embaixo de cada confronto.
-- Formato: [{"r":"V","op":"Marvin Vettori","met":"Decisão unânime","dt":"07/25"}, ...]
-- Pode rodar mais de uma vez.
alter table lutas add column if not exists hist_1 text default '';
alter table lutas add column if not exists hist_2 text default '';
