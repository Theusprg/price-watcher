# scrapers/aliexpress.py

import sys # Importado para verificar se está rodando como executável PyInstaller
import os  # Importado para manipulação de caminhos
from bs4 import BeautifulSoup
from time import sleep
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
# REMOVIDO: from webdriver_manager.firefox import GeckoDriverManager # Não usaremos mais o manager para o executável

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
        # __file__ é o caminho para este script (ex: price-watcher/scrapers/aliexpress.py)
        # Queremos o caminho para price-watcher/drivers/
        # Então, precisamos subir dois níveis de diretório
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        bundle_dir = project_root # O caminho base é a raiz do projeto

    # Combina o caminho base com o nome da pasta 'drivers' e o nome do driver
    return os.path.join(bundle_dir, 'drivers', driver_name)

def aliexpress(produto, number, time_str):
    options = FirefoxOptions()
    options.set_preference("dom.webdriver.enabled", False)
    options.set_preference("useAutomationExtension", False)

    # --- Usar o caminho do driver empacotado/local ---
    # Assegure-se de que 'geckodriver.exe' está na pasta 'drivers/'
    driver_executable_path = get_driver_path("geckodriver.exe")
    
    # Verifica se o arquivo do driver realmente existe no caminho esperado
    if not os.path.exists(driver_executable_path):
        raise FileNotFoundError(f"Erro: Driver '{driver_executable_path}' não encontrado. Baixe-o e coloque na pasta 'drivers/' do seu projeto.")

    service = FirefoxService(executable_path=driver_executable_path)
    driver = webdriver.Firefox(service=service, options=options)

    url = f"https://pt.aliexpress.com/w/wholesale-{produto}.html?page={number}&g=y&SearchText={produto}"
    driver.get(url)

    sleep(5) # Pausa para carregar a página

    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")

    nomes_elems = soup.find_all(class_=re.compile(r"\bkr_j0\b"))
    precos_divs = soup.find_all(class_=re.compile(r"\bkr_kj\b"))

    produtos_raspados = []
    for nome_elem, preco_div in zip(nomes_elems, precos_divs):
        nome_text = nome_elem.get_text(strip=True)
        spans = preco_div.find_all('span')
        preco_text_bruto = ''.join(span.get_text() for span in spans).strip()
        
        produtos_raspados.append({
            "Site": "AliExpress",
            "Nome do Produto": nome_text,
            "Preço Bruto": preco_text_bruto,
            "Data do Scraping": time_str
        })
    driver.quit()
    return produtos_raspados