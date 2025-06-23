from bs4 import BeautifulSoup

from time import sleep
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import re
import pandas as pd 
import csv
from datetime import datetime


#print("Coloque o nome do produto desejado:")
def amazon(produto,number):
    agora = datetime.now()
    time = agora.strftime("H%HM%MS%S")


    service = Service()
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")

    url = f"https://www.amazon.com.br/s?k={produto}&page={number}"
    driver  = webdriver.Chrome(service=service, options=options)
    sleep(4)
    driver.get(url)

    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")

    nomes = soup.find_all(class_=re.compile(r"\ba-text-normal\b"))
    
    preco = soup.find_all(class_=re.compile(r"\ba-offscreen\b"))
    produtos = []
    for nomes, preco in zip(nomes,preco):
        nome_text = nomes.get_text(strip=True)
        preco_text = preco.get_text(strip=True)
        produtos.append([nome_text, preco_text])
        #print(f"\nNome do produto:,{nome_text},\nPreço:,{preco_text}")
    driver.quit()
    
    with open(f"produtos_{time}page{pages}.csv", "w", newline="", encoding="utf-8") as arquivo:
        writer = csv.writer(arquivo)
        writer.writerow(["Nome", "Preço"])
        writer.writerows(produtos)
    print("Arquivo salvo com sucesso!")
pages = 1


nome_produto = "notebooks" #input("Nome do produto: ")
for i in range(1):
    resultado = amazon(nome_produto, pages)
    pages +=1
    i +=1