# scrapers/terabyteshop.py

import sys # Importado para verificar se está rodando como executável PyInstaller
import os  # Importado para manipulação de caminhos
from bs4 import BeautifulSoup
from time import sleep
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
# REMOVIDO: from webdriver_manager.chrome import ChromeDriverManager # Não usaremos mais o manager para o executável

import re
# REMOVIDO: Importações de pandas, csv, datetime (data e hora serão passadas)
# A função não salva mais CSV nem tem bloco de execução global

# --- Função auxiliar para obter o caminho CORRETO do driver ---
# Esta função é crucial para que o executável PyInstaller encontre o driver
def get_driver_path(driver_name):
    # Verifica se o script está rodando dentro de um executável PyInstaller
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # No executável PyInstaller, o _MEIPASS é o diretório temporário onde tudo é extraído.
        # Assumimos que a pasta 'drivers' foi copiada para a raiz desse diretório temporário.
        bundle_dir = sys._MEIPASS
    else:
        # Se estiver rodando em ambiente de desenvolvimento (ex: com 'poetry run python app.py')
        # __file__ é o caminho para este script (ex: price-watcher/scrapers/terabyteshop.py)
        # Queremos o caminho para price-watcher/drivers/
        # Então, precisamos subir dois níveis de diretório
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        bundle_dir = project_root # O caminho base é a raiz do projeto

    # Combina o caminho base com o nome da pasta 'drivers' e o nome do driver
    return os.path.join(bundle_dir, 'drivers', driver_name)

# --- Função de scraping para TerabyteShop ---
# Recebe 'time_str' para adicionar ao dicionário de produto
def terabyte(produto, page_number, time_str): # Renomeado 'number' para 'page_number' para clareza
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless=new") # Você pode manter headless ou remover se quiser ver o navegador

    # --- Usar o caminho do driver empacotado/local ---
    # Assegure-se de que 'chromedriver.exe' está na pasta 'drivers/' do seu projeto
    driver_executable_path = get_driver_path("chromedriver.exe")
    
    # Verifica se o arquivo do driver realmente existe no caminho esperado
    if not os.path.exists(driver_executable_path):
        raise FileNotFoundError(f"Erro: Driver '{driver_executable_path}' não encontrado. Baixe-o e coloque na pasta 'drivers/' do seu projeto.")

    service = ChromeService(executable_path=driver_executable_path)
    driver = webdriver.Chrome(service=service, options=options)

    # ATENÇÃO: URL ajustada para incluir paginação
    url = f"https://www.terabyteshop.com.br/busca?str={produto}&p={page_number}"
    driver.get(url)

    sleep(4) # Pausa para carregar a página (originalmente 10s, ajustei para 4s para consistência)

    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    
    # Seus seletores 'product-item__name' e 'product-item__new-price'
    # ATENÇÃO: Produtos "esgotados" podem não ter o elemento de preço.
    # Isso pode causar um desemparelhamento ou perda de dados se o número de nomes
    # for diferente do número de preços.
    nomes_elems = soup.find_all(class_=re.compile(r"\bproduct-item__name\b"))
    preco_elems = soup.find_all(class_=re.compile(r"\bproduct-item__new-price\b"))
    
    produtos_raspados = []
    # Usar min() para garantir que não haja erros se uma lista for menor
    # (por exemplo, se um produto não tiver preço visível e o seletor de preço não o encontrar)
    for nome_elem, preco_elem in zip(nomes_elems, preco_elems):
        nome_text = nome_elem.get_text(strip=True)
        preco_text_bruto = preco_elem.get_text(strip=True) # Preço bruto como string
        
        # Você pode adicionar o link do produto aqui se raspar (ex: o elemento 'a' com class product-item__name é o próprio link)
        # link_produto = nome_elem.get('href') # Se o nome estiver dentro de um <a> que é o link
        
        produtos_raspados.append({
            "Site": "TerabyteShop", # Nome do site
            "Nome do Produto": nome_text,
            "Preço Bruto": preco_text_bruto,
            # "Link do Produto": link_produto, # Adicionar se você raspar
            "Data do Scraping": time_str
        })
    driver.quit()
    return produtos_raspados # Retorna a lista de dicionários em vez de salvar o CSV

# REMOVIDO: Bloco de execução global (pages, nome_produto, resultado),
# pois este arquivo será importado e executado pelo app.py.