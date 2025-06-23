# scrapers/aliexpress_scraper.py

from bs4 import BeautifulSoup
from time import sleep
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from webdriver_manager.firefox import GeckoDriverManager
import re
# Importações de csv, datetime, os, sys, PyQt5.QtWidgets removidas

def aliexpress(produto, number, time_str):
    # Por enquanto, vamos manter a lógica de inicialização do driver aqui.
    # No futuro, podemos pensar em passá-lo como argumento ou centralizar mais.
    options = FirefoxOptions()
    # Para evitar detecção, é comum usar um perfil de usuário real
    # No entanto, para o executável e simplicidade de demo, o ideal seria não depender
    # de um perfil externo ou gerenciar isso de forma mais robusta.
    # Por ora, vamos focar em fazer funcionar sem o perfil complexo do firefox para o executavel.
    # Se a proteção anti-bot continuar, teremos que revisitar isso.

    # Remover o WebDriver do navigator (muito importante!)
    options.set_preference("dom.webdriver.enabled", False)
    options.set_preference("useAutomationExtension", False)

    # Use GeckoDriverManager para gerenciar o driver do Firefox
    service = FirefoxService(GeckoDriverManager().install())
    driver = webdriver.Firefox(service=service, options=options)

    url = f"https://pt.aliexpress.com/w/wholesale-{produto}.html?page={number}&g=y&SearchText={produto}"
    driver.get(url)

    # Nota: A interface principal é que deve exibir as mensagens e esperar o input
    # print(f"Abrindo a página {url}")
    # print("👉 Se aparecer captcha, resolva manualmente. Depois pressione ENTER aqui para continuar...")
    # input()  # Esta linha travaria a GUI. Será removida e gerenciada pela GUI se necessário.

    sleep(5) # Pausa para carregar a página e possivelmente resolver captchas manualmente

    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")

    # Seletores atualizados (conforme o último ajuste para kr_j0 e kr_kj)
    nomes_elems = soup.find_all(class_=re.compile(r"\bkr_j0\b"))
    precos_divs = soup.find_all(class_=re.compile(r"\bkr_kj\b"))

    produtos_raspados = []
    # Usar min() para garantir que não haja erros se uma lista for menor
    for nome_elem, preco_div in zip(nomes_elems, precos_divs):
        nome_text = nome_elem.get_text(strip=True)
        spans = preco_div.find_all('span')
        preco_text_bruto = ''.join(span.get_text() for span in spans).strip()
        
        # Você pode adicionar o link do produto aqui se raspar
        # link_produto = algum_elemento_link.get('href') 
        
        produtos_raspados.append({
            "Site": "AliExpress",
            "Nome do Produto": nome_text,
            "Preço Bruto": preco_text_bruto,
            # "Link do Produto": link_produto,
            "Data do Scraping": time_str
        })
    driver.quit()
    return produtos_raspados # Retorna a lista de dicionários