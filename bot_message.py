import telepot
import emoji
from datetime import datetime, timedelta
from sys import argv

### Carrega emojis
OK = emoji.emojize(':heavy_check_mark:', use_aliases=True)
NOK = emoji.emojize(':cross_mark:', use_aliases=True)

### Ids do Telegram

botID = '784006906:AAF1qZj6fA9HdfdTijq04rmJ8nb5O43bmUg'
channelID = '@datasciencetork'

### variaveis

if argv[1] == 'START':
    message = 'Crawler do ReclameAqui iniciado ' + OK
else:
    message= 'Crawler do ReclameAqui finalizado ' + OK

bot = telepot.Bot(botID)
bot.sendMessage(channelID,message)