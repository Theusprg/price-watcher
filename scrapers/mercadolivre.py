from bs4 import BeautifulSoup
from time import sleep
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import re
import pandas as pd
import csv
from datetime import datetime
import os # Importar para criar a pasta

# Função para o scraping do Mercado Livre
def mercadolivre(produto, current_offset, time_str): # Renomeado 'number' para 'current_offset' para clareza
    service = Service()
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless=new") # Removido comentário para ativar se quiser rodar sem interface

    # A URL agora usa o 'current_offset'
    url = f"https://lista.mercadolivre.com.br/informatica/portateis-acessorios/{produto}/{produto}_Desde_{current_offset}_NoIndex_True"
    print(f"Abrindo a página: {url}")

    driver = webdriver.Chrome(service=service, options=options)
    sleep(4)
    driver.get(url)

    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")

    # Seletor para nomes
    nomes = soup.find_all(class_=re.compile(r"\bpoly-component__title\b"))
    # Seletor para preços
    preco = soup.find_all(class_=re.compile(r"\bpoly-price__current\b"))

    produtos = []
    # Usar min() para garantir que não haja erros se uma lista for menor
    for nome_elem, preco_elem in zip(nomes, preco):
        nome_text = nome_elem.get_text(strip=True)
        preco_text = preco_elem.get_text(strip=True)
        produtos.append([nome_text, preco_text])
    driver.quit()

    # ==== Salvar CSV ====
    output_dir = "data_mercadolivre" # Pasta dedicada para Mercado Livre
    os.makedirs(output_dir, exist_ok=True) # Cria a pasta se não existir

    # Nome do arquivo agora inclui o offset para identificar a página
    file_name = f"mercadolivre_{produto}_{time_str}_offset_{current_offset}.csv"
    file_path = os.path.join(output_dir, file_name)

    with open(file_path, "w", newline="", encoding="utf-8") as arquivo:
        writer = csv.writer(arquivo)
        writer.writerow(["Nome", "Preço"])
        writer.writerows(produtos)
    print(f"✅ Arquivo '{file_name}' salvo com sucesso em '{output_dir}'!")

# --- Execução Principal ---
if __name__ == "__main__":
    nome_produto = "notebooks"
    num_paginas_para_raspar = 5 # Defina quantas páginas você quer raspar

    agora = datetime.now()
    # Formato de tempo para o nome do arquivo, mais robusto com data e hora
    time_str = agora.strftime("%Y%m%d_%H%M%S")

    current_offset = 1 # Começamos com 1, como você indicou

    for i in range(num_paginas_para_raspar):
        # Chama a função passando o produto, o offset atual e o timestamp
        mercadolivre(nome_produto, current_offset, time_str)

        # Atualiza o offset para a próxima página
        current_offset += 48

        # Pausa para evitar ser bloqueado (ajuste conforme necessário)
        sleep(5)