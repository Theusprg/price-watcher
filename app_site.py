from fastapi import FastAPI
from scrapers.aliexpress import aliexpress
from scrapers.amazon import amazon
from scrapers.kabum import kabum
from scrapers.mercadolivre import mercadolivre
from scrapers.pichau import pichau
from scrapers.terabyteshop import terabyte
from datetime import datetime

app = FastAPI()
#criar uma funçao no fastapi para linkar com o html um que seja o de buscar, select boxl, e um buscar
#ver o melhor modo de fazer isso, e de maneira geral pivotar o projeto para um site, na verdade ter os 2
#no final de tudo, com tudo feito criar um mini saas vendendo isso e fazer um dashboard de b.i com os
#melhores preços um dashboar geral, 
@app.get()
async def buscar():
    1
     
