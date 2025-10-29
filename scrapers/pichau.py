# scrapers/pichau.py

import sys
import os
from bs4 import BeautifulSoup
from time import sleep
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
import re

def get_driver_path(driver_name):
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        bundle_dir = sys._MEIPASS
    else:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        bundle_dir = project_root
    return os.path.join(bundle_dir, 'drivers', driver_name)

def pichau(produto, page_number, time_str):
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless=new")

    driver_executable_path = get_driver_path("chromedriver.exe")
    if not os.path.exists(driver_executable_path):
        raise FileNotFoundError(f"Erro: Driver '{driver_executable_path}' não encontrado. Baixe-o e coloque na pasta 'drivers/' do seu projeto.")

    service = ChromeService(executable_path=driver_executable_path)
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))

    url = f"https://www.pichau.com.br/{produto}/{produto}?page={page_number}"
    driver.get(url)

    sleep(4)

    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")

    nomes_elems = soup.find_all(class_=re.compile(r"\bMuiTypography-root\b"))
    preco_elems = soup.find_all(class_=re.compile(r"\bmui-1q2ojdg-price_vista\b"))
    
    produtos_raspados = []
    for nome_elem, preco_elem in zip(nomes_elems, preco_elems):
        nome_text = nome_elem.get_text(strip=True)
        preco_text_bruto = preco_elem.get_text(strip=True)
        produtos_raspados.append({
            "Site": "Pichau",
            "Nome do Produto": nome_text,
            "Preço Bruto": preco_text_bruto,
            "Data do Scraping": time_str
        })
    driver.quit()
    return produtos_raspados