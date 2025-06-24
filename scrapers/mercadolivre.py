# scrapers/mercadolivre.py

import sys # Importado para verificar se está rodando como executável PyInstaller
import os  # Importado para manipulação de caminhos
from bs4 import BeautifulSoup
from time import sleep
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
# REMOVIDO: from webdriver_manager.chrome import ChromeDriverManager # Não usaremos mais o manager para o executável

import re

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
        # __file__ é o caminho para este script (ex: price-watcher/scrapers/mercadolivre.py)
        # Queremos o caminho para price-watcher/drivers/
        # Então, precisamos subir dois níveis de diretório
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        bundle_dir = project_root # O caminho base é a raiz do projeto

    # Combina o caminho base com o nome da pasta 'drivers' e o nome do driver
    return os.path.join(bundle_dir, 'drivers', driver_name)

def mercadolivre(produto, current_offset, time_str):
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless=new") # Você pode ativar isso depois se quiser rodar sem abrir a janela do navegador

    # --- Usar o caminho do driver empacotado/local ---
    # Assegure-se de que 'chromedriver.exe' está na pasta 'drivers/'
    driver_executable_path = get_driver_path("chromedriver.exe")
    
    # Verifica se o arquivo do driver realmente existe no caminho esperado
    if not os.path.exists(driver_executable_path):
        raise FileNotFoundError(f"Erro: Driver '{driver_executable_path}' não encontrado. Baixe-o e coloque na pasta 'drivers/' do seu projeto.")

    service = ChromeService(executable_path=driver_executable_path)
    driver = webdriver.Chrome(service=service, options=options)

    url = f"https://lista.mercadolivre.com.br/informatica/portateis-acessorios/{produto}/{produto}_Desde_{current_offset}_NoIndex_True"
    driver.get(url)

    sleep(4)

    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    
    nomes_elems = soup.find_all(class_=re.compile(r"\bpoly-component__title\b"))
    precos_elems = soup.find_all(class_=re.compile(r"\bpoly-price__current\b"))
    
    produtos_raspados = []
    for nome_elem, preco_elem in zip(nomes_elems, precos_elems):
        nome_text = nome_elem.get_text(strip=True)
        preco_text_bruto = preco_elem.get_text(strip=True)
        
        produtos_raspados.append({
            "Site": "Mercado Livre",
            "Nome do Produto": nome_text,
            "Preço Bruto": preco_text_bruto,
            "Data do Scraping": time_str
        })
    driver.quit()