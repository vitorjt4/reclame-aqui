from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import csv
from datetime import datetime,date
from time import sleep
import credentials
from pyvirtualdisplay import Display
import os
import psycopg2

### variaveis
DATABASE, HOST, USER, PASSWORD = credentials.setDatabaseLogin()
DELAY = 1
WAIT = 30
outdir = '/home/ubuntu/scripts/load-dados-reclame-aqui/csv/'
file2 = 'comentarios_bancointer.csv'
display = Display(visible=0, size=(800,600))
display.start()
driver = webdriver.Chrome(executable_path='/home/ubuntu/scripts/load-dados-reclame-aqui/chromedriver')

### conecta no banco de dados
db_conn = psycopg2.connect("dbname='{}' user='{}' host='{}' password='{}'".format(DATABASE, USER, HOST, PASSWORD))
cursor = db_conn.cursor()
print('Connected to the database')
query = "SELECT empresa_id FROM reclame_aqui_dw.empresa WHERE empresa in ('GENIAL','BTG PACTUAL','RICO','XP INVESTIMENTOS','ORAMA','EASYNVEST','CLEAR','PI INVESTIMENTOS') ORDER BY 1"
cursor.execute(query)
empresas = [item[0] for item in cursor.fetchall()]
cursor.close()
db_conn.close()

for empresa in empresas:

    urls = []
    for i in range(1,100): ### Pega endereços de todas as reclamações das 3 primeiras paginas e armaza em um vetor
        try:
            driver.get("https://www.reclameaqui.com.br/empresa/"+empresa+"/lista-reclamacoes/?pagina="+str(i)+"&status=EVALUATED")
            element_present = EC.presence_of_element_located((By.ID, 'complains-anchor-top'))
            WebDriverWait(driver, WAIT).until(element_present)
            sleep(DELAY)
            for i in range(1,11):
                urls.append(driver.find_element_by_xpath('//*[@id="complains-anchor-top"]/ul[1]/li['+str(i)+']/a').get_attribute("href"))
        except:
            pass
    
    print('\tParsing claims from {}...'.format(empresa))
    print('Numero URLS: {}'.format(str(len(urls))))
    
    with open(outdir+file2,'a', newline="\n", encoding="utf-8") as ofile: ### arquivo com as reclamacoes avaliadas da empresa
        writer = csv.writer(ofile, delimiter=';')
        count_error = 0
        count_urls = 1
        for url in urls:
            print('Count URL: {}'.format(str(count_urls)))
            count_urls +=1
            try:
                driver.get(url)
                element_present = EC.visibility_of_element_located((By.XPATH, '//*[@id="complain-detail"]/div/div[1]/div[1]/div/div[1]/div[2]/div[1]/h1'))
                WebDriverWait(driver, WAIT).until(element_present)
                #driver.implicitly_wait(WAIT)
                #sleep(DELAY)
                titulo = driver.find_element_by_xpath('//*[@id="complain-detail"]/div/div[1]/div[1]/div/div[1]/div[2]/div[1]/h1').text
                cidade = driver.find_element_by_xpath('//*[@id="complain-detail"]/div/div[1]/div[1]/div/div[1]/div[2]/div[1]/ul[1]/li[1]').text.split('-')[0].strip()
                estado = driver.find_element_by_xpath('//*[@id="complain-detail"]/div/div[1]/div[1]/div/div[1]/div[2]/div[1]/ul[1]/li[1]').text.split('-')[-1].strip()
                if len(estado) > 2:
                    estado = ''
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