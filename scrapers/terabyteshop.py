from bs4 import BeautifulSoup
from time import sleep
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import re
import pandas as pd 
import csv
from datetime import datetime

#<a class="product-item__name" href="https://www.terabyteshop.com.br/produto/25749/notebook-gamer-superframe-force-intel-core-i5-12450h-rtx-4050-6gb-16gb-ddr4-ssd-1tb" 

#title="Notebook Gamer SuperFrame Force Intel Core i5 12450H / RTX 4050 6GB / 16GB DDR4 / 1TB SSD NVMe, Teclado ABNT2 Iluminado">
                       # <h2>Notebook Gamer SuperFrame Force Intel Core i5 12450H / RTX 4050 6GB / 16GB DDR4 / 1TB SSD NVMe, Teclado A</h2>
                 #   </a>

#<div class="product-item__new-price"><span>R$ 6.499,90</span> <small> àvista </small></div>

#<div class="tbt_esgotado">Todos vendidos</div>
def terabyteshop(produto, number):
    agora = datetime.now()
    time = agora.strftime("H%HM%MS%S")

    service = Service()
    options = webdriver.ChromeOptions()
   # options.add_argument("--headless=")
    url = f"https://www.terabyteshop.com.br/busca?str={produto}"
    driver = webdriver.Chrome(service=service, options=options)
    sleep(10)
    driver.get(url)
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    nome = soup.find_all(class_=re.compile(r"\bproduct-item__name\b"))
    preco = soup.find_all(class_=re.compile(r"\bproduct-item__new-price\b"))
    produtos = []
    for nome, preco in zip(nome, preco):
        nome_text = nome.get_text(strip=True)
        preco_text = preco.get_text(strip=True)
        produtos.append([nome_text, preco_text])
        #print(f"\nNome do produto:,{nome_text},\nPreço:,{preco_text}")
    driver.quit()
    
    with open(f"produtos_{time}page{number}.csv", "w", newline="", encoding="utf-8") as arquivo:
        writer = csv.writer(arquivo)
        writer.writerow(["Nome", "Preço"])
        writer.writerows(produtos)
    print("Arquivo salvo com sucesso!")
pages = 0 

nome_produto =  "notebooks"# input("Nome do produto: ")
resultado = terabyteshop(nome_produto, pages)
