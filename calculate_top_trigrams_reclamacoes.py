import os
import re
import psycopg2
import csv
from collections import Counter
import credentials
from nltk.tokenize import word_tokenize,sent_tokenize
from nltk.corpus import stopwords
from nltk.util import ngrams
import psycopg2
import credentials
from subprocess import call
import enchant

DATABASE, HOST, USER, PASSWORD = credentials.setDatabaseLogin()

stopwords = stopwords.words('portuguese')
p = enchant.Dict("pt_BR")
e = enchant.Dict()
nonstopwords = ['intermedium','isafe','sms','xiaomi','nfc','sicoob','wifi','cdb','redmi','ios','mei','crashar','nuconta','samsung','iphone','aff','ok','credicard','criptomoedas','cdbs','bugado','itoken','broker','fintech','fintechs','superapp','instagram','facebook','whatsapp','blackfriday','friday']

def words(text):
    pattern = re.compile(r"[^\s]+")
    non_alpha = re.compile(r"[^\w]", re.IGNORECASE)
    for match in pattern.finditer(text):
        nxt = non_alpha.sub("", match.group()).lower()
        return nxt

### variaveis
outdir = '/home/ubuntu/scripts/load-dados-reclame-aqui/csv/'
file = 'trigram.csv'
query_app = "SELECT empresa_id FROM reclame_aqui_dw.empresa"
query_company = "SELECT empresa FROM reclame_aqui_dw.empresa"
query_data = "SELECT DISTINCT ano,mes FROM reclame_aqui_dw.vw_reclamacoes_avaliadas WHERE empresa_id = '{}' AND mes != date_part('month',current_date) ORDER BY 2,1"
query_comentario = "SELECT reclamacao FROM reclame_aqui_dw.vw_reclamacoes_avaliadas WHERE empresa_id = '{}' AND ano = {} AND mes = {}"
tablename = 'reclame_aqui_dw.trigrams_reclamacoes_avaliadas'

### conecta no banco de dados
db_conn = psycopg2.connect("dbname='{}' user='{}' host='{}' password='{}'".format(DATABASE, USER, HOST, PASSWORD))
cursor = db_conn.cursor()
print('Connected to the database')

cursor.execute(query_company)
companies = [item[0].lower() for item in cursor.fetchall()]
nonstopwords = nonstopwords + companies

with open(outdir+file,'w', newline="\n", encoding="utf-8") as ofile:
    writer = csv.writer(ofile, delimiter=';')

    cursor.execute(query_app)
    apps = [item[0] for item in cursor.fetchall()]
    for app in apps:
        print('Parsing '+app+'...')
        cursor.execute(query_data.format(app))
        datas = [item for item in cursor.fetchall()]
        for ano,mes in datas:
            try:
                print('Ano: {} - Mês: {}'.format(ano,mes))
                cursor.execute(query_comentario.format(app,ano,mes))
                comments = [str(item[0]) for item in cursor.fetchall()]
                ltrigrams = []
                for comment in comments:
                    sentence = [words(word) for word in word_tokenize(comment,language='portuguese')]
                    sentence = [x.replace('oq','que').replace('vcs','vocês').replace('vc','você').replace('funcao','função').replace('notificacoes','notificações').replace('hj','hoje').replace('pq','porque').replace('msm','mesmo').replace('td','tudo').replace('vzs','vezes').replace('vlw','valeu').replace('msg','mensagem').replace('mt','muito') for x in sentence if x]
                    sentence = [x for x in sentence if x not in stopwords]
                    trigrams=ngrams(sentence,3)
                    ltrigrams += list(trigrams)
                counter = Counter(ltrigrams)

                for trigram,count in counter.most_common():
                    if trigram and count > 1:
                        trigram = '_'.join(trigram)
                        writer.writerow([app,ano,mes,trigram.rstrip('_'),count])
            except:
                pass

## copy
with open(outdir+file, 'r') as ifile:
    SQL_STATEMENT = "COPY %s FROM STDIN WITH CSV DELIMITER AS ';' NULL AS ''"
    print("Executing Copy in "+tablename)
    cursor.copy_expert(sql=SQL_STATEMENT % tablename, file=ifile)
    db_conn.commit()
cursor.close()
db_conn.close()
os.remove(outdir+file)

# ### VACUUM ANALYZE
call('psql -d torkcapital -c "VACUUM VERBOSE ANALYZE '+tablename+'";',shell=True)