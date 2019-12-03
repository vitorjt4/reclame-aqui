# -*- coding: utf-8 -*-
"""
Created on Mon Nov 18 20:25:42 2019

@author: abonna
"""

from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import csv
from datetime import datetime,date
from time import sleep
import psycopg2
import credentials
from pyvirtualdisplay import Display
import os
from subprocess import call

### variaveis
DATABASE, HOST, USER, PASSWORD = credentials.setDatabaseLogin()
DELAY = 1
WAIT = 30
outdir = '/home/ubuntu/scripts/load-dados-reclame-aqui/csv/'
file = 'reclameaqui.csv'
tablename = 'reclame_aqui.reputacao_stg'
file2 = 'comentarios.csv'
tablename2 = 'reclame_aqui.reclamacoes_stg'
display = Display(visible=0, size=(800,600))
display.start()
driver = webdriver.Chrome(executable_path='/home/ubuntu/scripts/load-dados-reclame-aqui/chromedriver')

### conecta no banco de dados
db_conn = psycopg2.connect("dbname='{}' user='{}' host='{}' password='{}'".format(DATABASE, USER, HOST, PASSWORD))
cursor = db_conn.cursor()
print('Connected to the database')
query = "SELECT empresa_id FROM reclame_aqui_dw.empresa ORDER BY 1"
cursor.execute(query)
empresas = [item[0] for item in cursor.fetchall()]
cursor.close()
db_conn.close()

for empresa in empresas:

    driver.get("https://www.reclameaqui.com.br/empresa/"+empresa+"/")
    print('Parsing {}...'.format(empresa))
    element_present = EC.presence_of_element_located((By.XPATH, '//*[@id="reputacao-da-empresa"]/div/div/div/div[3]/div[1]/div[1]/div[1]/div/div[1]/div[2]/p[2]'))
    WebDriverWait(driver, WAIT).until(element_present)
    sleep(DELAY)
    ### avaliacoes resumidas da empresa
    nota = driver.find_element_by_xpath('//*[@id="reputacao-da-empresa"]/div/div/div/div[3]/div[1]/div[1]/div[1]/div/div[1]/div[2]/p[2]/span[1]').text.replace('--','')
    reclamacoes = driver.find_element_by_xpath('//*[@id="link-list-complain-all-middle"]').text
    respondidas = driver.find_element_by_xpath('//*[@id="link-list-complain-answered-middle"]').text
    nao_respondidas = driver.find_element_by_xpath('//*[@id="link-list-complain-not-answered-middle"]').text
    avaliadas = driver.find_element_by_xpath('//*[@id="link-list-complain-evaluated-middle"]').text
    nota_consumidor = driver.find_element_by_xpath('//*[@id="reputacao-da-empresa"]/div/div/div/div[3]/div[1]/div[1]/div[2]/div[4]/span').text.replace(',','.').replace('--','')

    categoria = []
    servico = []
    problema = []

    element_present = EC.presence_of_element_located((By.ID, 'principais-problemas'))
    WebDriverWait(driver, WAIT).until(element_present)

    for i in range(1,7):
        try:
            categoria.append(driver.find_element_by_xpath('//*[@id="principais-problemas"]/div/div/div[2]/section[1]/div/div[2]/ul/li['+str(i)+']/a/span').text)
            categoria.append(driver.find_element_by_xpath('//*[@id="principais-problemas"]/div/div/div[2]/section[1]/div/div[2]/ul/li['+str(i)+']/span').text.replace('(','').replace(')',''))
        except:
            break
    if len(categoria) != 12:
        for i in range(12-len(categoria)):
            categoria += ['']

    for i in range(1,7):
        try:
            servico.append(driver.find_element_by_xpath('//*[@id="principais-problemas"]/div/div/div[2]/section[2]/div/div[2]/ul/li['+str(i)+']/a/span').text)
            servico.append(driver.find_element_by_xpath('//*[@id="principais-problemas"]/div/div/div[2]/section[2]/div/div[2]/ul/li['+str(i)+']/span').text.replace('(','').replace(')',''))
        except:
            break
    if len(servico) != 12:
        for i in range(12-len(servico)):
            servico += ['']

    for i in range(1,7):
        try:
            problema.append(driver.find_element_by_xpath('//*[@id="principais-problemas"]/div/div/div[2]/section[3]/div/div[2]/ul/li['+str(i)+']/a/span').text)
            problema.append(driver.find_element_by_xpath('//*[@id="principais-problemas"]/div/div/div[2]/section[3]/div/div[2]/ul/li['+str(i)+']/span').text.replace('(','').replace(')',''))
        except:
            break
    if len(problema) != 12:
        for i in range(12-len(problema)):
            problema += ['']

    with open(outdir+file,'a', newline="\n", encoding="utf-8") as ofile: ### arquivo com a reputaca das empresas
        writer = csv.writer(ofile, delimiter=';')
        writer.writerow([empresa,str(date.today()),nota,reclamacoes,respondidas,nao_respondidas,avaliadas,nota_consumidor]+categoria+servico+problema)

    urls = []
    for i in range(1,4): ### Pega endereços de todas as reclamções das 3 primeiras paginas e armaza em um vetor
        try:
            driver.get("https://www.reclameaqui.com.br/empresa/"+empresa+"/lista-reclamacoes/?pagina="+str(i)+"&status=EVALUATED")
            element_present = EC.presence_of_element_located((By.ID, 'complains-anchor-top'))
            WebDriverWait(driver, WAIT).until(element_present)
            sleep(DELAY)
            for i in range(1,11):
                urls.append(driver.find_element_by_xpath('//*[@id="complains-anchor-top"]/ul[1]/li['+str(i)+']/a').get_attribute("href"))
        except:
            break
    print('\tParsing claims from {}...'.format(empresa))
    with open(outdir+file2,'a', newline="\n", encoding="utf-8") as ofile: ### arquivo com as reclamacoes avaliadas da empresa
        writer = csv.writer(ofile, delimiter=';')
        count_error = 0
        for url in urls:
            try:
                driver.get(url)
                element_present = EC.visibility_of_element_located((By.XPATH, '//*[@id="complain-detail"]/div/div[1]/div[1]/div/div[1]/div[2]/div[1]/h1'))
                WebDriverWait(driver, WAIT).until(element_present)
                #driver.implicitly_wait(WAIT)
                #sleep(DELAY)
                titulo = driver.find_element_by_xpath('//*[@id="complain-detail"]/div/div[1]/div[1]/div/div[1]/div[2]/div[1]/h1').text
                cidade = driver.find_element_by_xpath('//*[@id="complain-detail"]/div/div[1]/div[1]/div/div[1]/div[2]/div[1]/ul[1]/li[1]').text.split('-')[0].strip()
                estado = driver.find_element_by_xpath('//*[@id="complain-detail"]/div/div[1]/div[1]/div/div[1]/div[2]/div[1]/ul[1]/li[1]').text.split('-')[-1].strip()
                id = driver.find_element_by_xpath('//*[@id="complain-detail"]/div/div[1]/div[1]/div/div[1]/div[2]/div[1]/ul[1]/li[2]/b').text.split(' ')[-1]
                current_date = driver.find_element_by_xpath('//*[@id="complain-detail"]/div/div[1]/div[1]/div/div[1]/div[2]/div[1]/ul[1]/li[3]').text
                current_date = str(datetime.strptime(current_date, '%d/%m/%y às %Hh%M')) ### parser da data no formato do DB
                comentario = driver.find_element_by_xpath('//*[@id="complain-detail"]/div/div[1]/div[1]/div/div[2]/p').text
                try: ### procura a nota de avaliacao do usuario. localizacao pode mudar se houver replicas
                    nota = driver.find_element_by_xpath('//*[@id="complain-detail"]/div/div[1]/div[1]/div/div[4]/div[4]/div[3]/div/div/div[2]/div/p').text
                except:
                    try:
                        nota = driver.find_element_by_xpath('//*[@id="complain-detail"]/div/div[1]/div[1]/div/div[3]/div[4]/div[3]/div/div/div[2]/div/p').text
                    except:
                        for i in range(5,10):
                            try:
                                nota = driver.find_element_by_xpath('//*[@id="complain-detail"]/div/div[1]/div[1]/div/div['+str(i)+']/div[4]/div[3]/div/div/div[2]/div/p').text
                            except:
                                pass
                            else: 
                                break
                writer.writerow([empresa,titulo,cidade,estado,id,current_date,comentario,nota])
            except:
               count_error += 1
               pass
    print('\tErrors: '+str(count_error))

 ##close the browser window
driver.quit()
display.stop()
### conecta no banco de dados
db_conn = psycopg2.connect("dbname='{}' user='{}' host='{}' password='{}'".format(DATABASE, USER, HOST, PASSWORD))
cursor = db_conn.cursor()

## copy reclame_aqui.reputacao_stg
with open(outdir+file, 'r') as ifile:
    SQL_STATEMENT = "COPY %s FROM STDIN WITH CSV DELIMITER AS ';' NULL AS ''"
    print("Executing Copy in "+tablename)
    cursor.copy_expert(sql=SQL_STATEMENT % tablename, file=ifile)
    db_conn.commit()
os.remove(outdir+file)

### VACUUM ANALYZE
call('psql -d torkcapital -c "VACUUM VERBOSE ANALYZE '+tablename+'";',shell=True)

### copy reclame_aqui.reclamacoes_stg
with open(outdir+file2, 'r') as ifile:
    SQL_STATEMENT = "COPY %s FROM STDIN WITH CSV DELIMITER AS ';' NULL AS ''"
    print("Executing Copy in "+tablename2)
    cursor.copy_expert(sql=SQL_STATEMENT % tablename2, file=ifile)
    db_conn.commit()
cursor.close()
db_conn.close()
os.remove(outdir+file2)

### VACUUM ANALYZE
call('psql -d torkcapital -c "VACUUM VERBOSE ANALYZE '+tablename2+'";',shell=True)