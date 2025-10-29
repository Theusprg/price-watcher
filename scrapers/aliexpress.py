# scrapers/aliexpress.py

import sys
import os
from bs4 import BeautifulSoup
from time import sleep
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
import re

def get_driver_path(driver_name):
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        bundle_dir = sys._MEIPASS
    else:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        bundle_dir = project_root
    return os.path.join(bundle_dir, 'drivers', driver_name)

def aliexpress(produto, number, time_str):
    options = FirefoxOptions()
    options.set_preference("dom.webdriver.enabled", False)
    options.set_preference("useAutomationExtension", False)

    driver_executable_path = get_driver_path("geckodriver.exe")
    if not os.path.exists(driver_executable_path):
        raise FileNotFoundError(f"Erro: Driver '{driver_executable_path}' não encontrado. Baixe-o e coloque na pasta 'drivers/' do seu projeto.")

    service = FirefoxService(executable_path=driver_executable_path)
    driver = webdriver.Firefox(service=service, options=options)

    url = f"https://pt.aliexpress.com/w/wholesale-{produto}.html?page={number}&g=y&SearchText={produto}"
    driver.get(url)

    sleep(5)

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
