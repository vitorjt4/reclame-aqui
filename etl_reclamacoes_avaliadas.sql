\! echo "Deletando dados carregados antes..."

DELETE FROM reclame_aqui.reclamacoes_stg WHERE id in (SELECT reclamacao_id FROM reclame_aqui_dw.reclamacao);

-- reclame_aqui_dw.datetime

\! echo "Carregando dados na tabela datetime..."

INSERT INTO reclame_aqui_dw.datetime
SELECT distinct datetime, date(datetime), date_part('week', datetime),date_part('month', datetime),date_part('year', datetime)
	FROM reclame_aqui.reclamacoes_stg WHERE datetime not in (SELECT datetime FROM reclame_aqui_dw.datetime)
ORDER BY 1;

VACUUM ANALYZE reclame_aqui_dw.datetime;

----------------------------------------------------------------------------

-- reclame_aqui_dw.cidade

\! echo "Carregando dados na tabela categoria..."

INSERT INTO reclame_aqui_dw.cidade(cidade,uf)
SELECT distinct cidade,uf
FROM reclame_aqui.reclamacoes_stg WHERE not cidade is null
EXCEPT
SELECT cidade,uf FROM reclame_aqui_dw.cidade
ORDER BY 1;

VACUUM ANALYZE reclame_aqui_dw.cidade;

----------------------------------------------------------------------------

-- reclame_aqui_dw.reclamacao

\! echo "Carregando dados na tabela reclamacao..."

INSERT INTO reclame_aqui_dw.reclamacao
SELECT distinct id,titulo,reclamacao
FROM reclame_aqui.reclamacoes_stg
ORDER BY 1;

VACUUM ANALYZE reclame_aqui_dw.reclamacao;

----------------------------------------------------------------------------

-- reclame_aqui_dw_dw.reclamacoes_avaliadas

\! echo "Carregando dados na tabela fato reclamacoes_avaliadas..."

COPY(
SELECT distinct e.empresa_id, d.datetime, c.cidade_id, r.reclamacao_id, f.nota
	FROM reclame_aqui.reclamacoes_stg f
	JOIN reclame_aqui_dw.datetime d ON d.datetime=f.datetime
	JOIN reclame_aqui_dw.empresa e ON e.empresa_id=f.empresa_id
	LEFT JOIN reclame_aqui_dw.cidade c ON c.cidade=f.cidade AND c.uf=f.uf
	JOIN reclame_aqui_dw.reclamacao r ON r.reclamacao_id=f.id
) to '/home/ubuntu/dump/reclamacoes_avaliadas.txt';
COPY reclame_aqui_dw.reclamacoes_avaliadas FROM '/home/ubuntu/dump/reclamacoes_avaliadas.txt';

VACUUM ANALYZE reclame_aqui_dw.reclamacoes_avaliadas;
