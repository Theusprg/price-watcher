# scrapers/mercadolivre_scraper.py

from bs4 import BeautifulSoup
from time import sleep
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager # Importar para gerenciar o driver do Chrome
import re
# Importações de pandas, csv, datetime, os removidas

def mercadolivre(produto, current_offset, time_str): # Renomeado 'number' para 'current_offset'
    # Use ChromeDriverManager para gerenciar o driver do Chrome
    service = ChromeService(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless=new") # Você pode ativar isso depois se quiser rodar sem abrir a janela do navegador

    url = f"https://lista.mercadolivre.com.br/informatica/portateis-acessorios/{produto}/{produto}_Desde_{current_offset}_NoIndex_True"
    driver = webdriver.Chrome(service=service, options=options)
    sleep(4)
    driver.get(url)

    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    
    # Seletores do Mercado Livre (mantidos conforme você indicou)
    nomes_elems = soup.find_all(class_=re.compile(r"\bpoly-component__title\b"))
    precos_elems = soup.find_all(class_=re.compile(r"\bpoly-price__current\b"))
    
    produtos_raspados = []
    # Usar min() para garantir que não haja erros se uma lista for menor
    for nome_elem, preco_elem in zip(nomes_elems, precos_elems):
        nome_text = nome_elem.get_text(strip=True)
        preco_text_bruto = preco_elem.get_text(strip=True) # Preço bruto como string
        
        # Você pode adicionar o link do produto aqui se raspar
        # link_produto = algum_elemento_link.get('href') 
        
        produtos_raspados.append({
            "Site": "Mercado Livre",
            "Nome do Produto": nome_text,
            "Preço Bruto": preco_text_bruto,
            # "Link do Produto": link_produto,
            "Data do Scraping": time_str
        })
    driver.quit()
    return produtos_raspados # Retorna a lista de dicionários