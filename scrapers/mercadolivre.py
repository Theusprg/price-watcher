# scrapers/mercadolivre.py (apenas a função mercadolivre, assumindo que get_driver_path e imports já estão lá)

import sys
import os
from bs4 import BeautifulSoup
from time import sleep
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import re

# Função get_driver_path (mantém a que você já tem)
def get_driver_path(driver_name):
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        bundle_dir = sys._MEIPASS
    else:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        bundle_dir = project_root
    return os.path.join(bundle_dir, 'drivers', driver_name)

def mercadolivre(produto, current_offset, time_str):
    options = ChromeOptions()
    #options.add_argument("--headless=new") # Removido para depuração, se quiser que ele NÃO apareça. Descomente esta linha.
    
    # Opções para evitar detecção (mantém as que você já tem)
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    driver_executable_path = get_driver_path("chromedriver.exe")
    if not os.path.exists(driver_executable_path):
        raise FileNotFoundError(f"Erro: Driver '{driver_executable_path}' não encontrado. Baixe-o e coloque na pasta 'drivers/' do seu projeto.")

    driver = None # Inicializa driver como None

    try:
        service = ChromeService(executable_path=driver_executable_path)
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))

        url = f"https://lista.mercadolivre.com.br/informatica/portateis-acessorios/{produto}/{produto}_Desde_{current_offset}_NoIndex_True"
        driver.get(url)

        # Usar WebDriverWait para esperar por elementos
        WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "h3.poly-component__title-wrapper"))
        )
        sleep(3)  # Pausa extra para garantir carregamento


        html = driver.page_source
        #print("DEBUG_ML: HTML da página salvo em debug_ml_page.html")
        soup = BeautifulSoup(html, "html.parser")
        
        produtos_raspados = []

        product_list_items = soup.find_all('li', class_='ui-search-layout__item')

        for item in product_list_items:
            # Nome do produto
            nome_elem = item.find('h3', class_='poly-component__title-wrapper')
            nome_text = nome_elem.get_text(strip=True) if nome_elem else "N/A"

            # Link do produto (dentro do <a> dentro do h3)
            link_elem = nome_elem.find('a') if nome_elem else None
            link_produto = link_elem.get('href') if link_elem else "N/A"

            # Preço
            preco_text_bruto = "N/A"
            preco_container = item.find('div', class_='poly-price__current')
            if preco_container:
                # A parte inteira do preço está em span com classe 'andes-money-amount__fraction'
                preco_frac = preco_container.find('span', class_='andes-money-amount__fraction')
                # Símbolo da moeda (ex: R$)
                preco_simbolo = preco_container.find('span', class_='andes-money-amount__currency-symbol')

                preco_text_bruto = ""
                if preco_simbolo:
                    preco_text_bruto += preco_simbolo.get_text(strip=True)
                if preco_frac:
                    preco_text_bruto += preco_frac.get_text(strip=True)

            produtos_raspados.append({
                "Site": "Mercado Livre",
                "Nome do Produto": nome_text,
                "Preço Bruto": preco_text_bruto,
                "Link do Produto": link_produto,
                "Data do Scraping": time_str
            })
        return produtos_raspados

    except Exception as e:
        print(f"DEBUG_ML: Erro inesperado na função mercadolivre: {e}")
        # Retorna uma lista vazia em caso de erro para não quebrar a ScraperThread
        return [] 
    finally:
        # Este bloco será executado SEMPRE, independentemente de haver um erro ou não.
        if driver: # Verifica se o driver foi inicializado antes de tentar fechá-lo
            driver.quit()
            print("DEBUG_ML: Navegador fechado (finally block).")
 # Teste rápido para verificar se a função está funcionando

