import os
import re
import psycopg2
from collections import Counter
import credentials
import nltk
import csv
from gensim.models import Phrases
from gensim.models import Word2Vec
from nltk.corpus import stopwords
import psycopg2
import credentials
from subprocess import call
import enchant

DATABASE, HOST, USER, PASSWORD = credentials.setDatabaseLogin()

stopwords = stopwords.words('portuguese')
p = enchant.Dict("pt_BR")
e = enchant.Dict()
nonstopwords = ['intermedium','isafe','sms','xiaomi','nfc','sicoob','wifi','cdb','redmi','ios','mei','crashar','nuconta','samsung','iphone','aff','ok','credicard','criptomoedas','cdbs','bugado','itoken','broker','fintech','fintechs','uber','fgc','superapp','instagram','facebook','whatsapp','blackfriday','friday']

def words(text):
    pattern = re.compile(r"[^\s]+")
    non_alpha = re.compile(r"[^\w]", re.IGNORECASE)
    for match in pattern.finditer(text):
        nxt = non_alpha.sub("", match.group()).lower()
        return nxt

### variaveis
outdir = '/home/ubuntu/scripts/load-dados-reclame-aqui/csv/'
file = 'bigram.csv'
query_app = "SELECT empresa_id FROM reclame_aqui_dw.empresa"
query_company = "SELECT empresa FROM reclame_aqui_dw.empresa"
query_comentario = "SELECT titulo FROM reclame_aqui_dw.vw_reclamacoes_avaliadas WHERE empresa_id = '{}'"
tablename = 'reclame_aqui_dw.bigrams_titulos'

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
        cursor.execute(query_comentario.format(app))
        comments = [item[0] for item in cursor.fetchall()]

        bigram = Phrases(min_count=1, threshold=5)
        sentences = []
        for row in comments:
            try:
                sentence = [words(word) for word in nltk.word_tokenize(row,language='portuguese')]
                sentence = [x.replace('oq','que').replace('vcs','vocês').replace('vc','você').replace('funcao','função').replace('notificacoes','notificações').replace('hj','hoje').replace('pq','porque').replace('msm','mesmo').replace('td','tudo').replace('vzs','vezes').replace('vlw','valeu').replace('msg','mensagem').replace('mt','muito') for x in sentence if x]
                sentence = [x for x in sentence if x not in stopwords]
                #sentence = [p.suggest(word)[0].lower() if word not in nonstopwords and (not p.check(word) and not e.check(word)) and p.suggest(word) and word not in app.lower() else word for word in sentence]
                sentences.append(sentence)
                bigram.add_vocab([sentence])
            except:
                pass

        try:
            #print(sentences)
            bigram_model = Word2Vec(bigram[sentences])
            bigram_model_counter = Counter()

            for key in bigram_model.wv.vocab.keys():
                if len(key.split("_")) > 1:
                    bigram_model_counter[key] += bigram_model.wv.vocab[key].count

            most_commons =  bigram_model_counter.most_common()
            for phrase,counts in most_commons:
                if phrase.rstrip('_'):
                    writer.writerow([app,phrase.rstrip('_'),counts])
        except:
            print('Error')
            pass
### TRUNCATE
call('psql -d torkcapital -c "TRUNCATE '+tablename+'";',shell=True)

### copy
with open(outdir+file, 'r') as ifile:
    SQL_STATEMENT = "COPY %s FROM STDIN WITH CSV DELIMITER AS ';' NULL AS ''"
    print("Executing Copy in "+tablename)
    cursor.copy_expert(sql=SQL_STATEMENT % tablename, file=ifile)
    db_conn.commit()
cursor.close()
db_conn.close()
os.remove(outdir+file)

### VACUUM ANALYZE
call('psql -d torkcapital -c "VACUUM VERBOSE ANALYZE '+tablename+'";',shell=True)