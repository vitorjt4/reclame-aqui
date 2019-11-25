
-- reclame_aqui_dw.date

\! echo "Carregando dados na tabela date..."

INSERT INTO reclame_aqui_dw.date
SELECT distinct date, date_part('week', date),date_part('month', date),date_part('year', date)
	FROM reclame_aqui.reputacao_stg WHERE date not in (SELECT date FROM reclame_aqui_dw.date)
ORDER BY 1;

VACUUM ANALYZE reclame_aqui_dw.date;

----------------------------------------------------------------------------

-- reclame_aqui_dw.categoria

\! echo "Carregando dados na tabela categoria..."

INSERT INTO reclame_aqui_dw.categoria(categoria)
SELECT distinct categoria
FROM reclame_aqui.vw_reputacao WHERE not categoria is null
EXCEPT
SELECT categoria FROM reclame_aqui_dw.categoria
ORDER BY 1;

VACUUM ANALYZE reclame_aqui_dw.categoria;

----------------------------------------------------------------------------

-- reclame_aqui_dw.servico

\! echo "Carregando dados na tabela servico..."

INSERT INTO reclame_aqui_dw.servico(servico)
SELECT distinct servico
FROM reclame_aqui.vw_reputacao WHERE not servico is null
EXCEPT
SELECT servico FROM reclame_aqui_dw.servico
ORDER BY 1;

VACUUM ANALYZE reclame_aqui_dw.servico;

----------------------------------------------------------------------------

-- reclame_aqui_dw.problema

\! echo "Carregando dados na tabela problema..."

INSERT INTO reclame_aqui_dw.problema(problema)
SELECT distinct problema
FROM reclame_aqui.vw_reputacao WHERE not problema is null
EXCEPT
SELECT problema FROM reclame_aqui_dw.problema
ORDER BY 1;

VACUUM ANALYZE reclame_aqui_dw.problema;

----------------------------------------------------------------------------

-- reclame_aqui_dw_dw.reputacao

\! echo "Carregando dados na tabela fato reputacao..."

COPY(
SELECT e.empresa_id, d.dia, f.nota, f.reclamacoes, f.nao_respondidas, f.avaliadas, f.nota_consumidor,
	c.categoria_id, f.categoria_value, s.servico_id, f.servico_value, p.problema_id, f.problema_value
	FROM reclame_aqui.vw_reputacao f
	JOIN reclame_aqui_dw.date d ON d.dia=f.date
	JOIN reclame_aqui_dw.empresa e ON e.empresa_id=f.empresa_id
	JOIN reclame_aqui_dw.categoria c ON c.categoria=f.categoria
	JOIN reclame_aqui_dw.servico s ON s.servico=f.servico
	JOIN reclame_aqui_dw.problema p ON p.problema=f.problema
) to '/home/ubuntu/dump/reputacao.txt';
COPY reclame_aqui_dw.reputacao FROM '/home/ubuntu/dump/reputacao.txt';

VACUUM ANALYZE reclame_aqui_dw.reputacao;
