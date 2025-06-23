from bs4 import BeautifulSoup
from time import sleep
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from webdriver_manager.firefox import GeckoDriverManager
import re
import csv
from datetime import datetime
import os
import sys
from PyQt5.QtWidgets import QApplication, QFileDialog

CACHE_PATH = "cache_perfil_firefox.txt"

def get_cached_profile_path():
    if os.path.exists(CACHE_PATH):
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            return f.read().strip()
    return None

def set_cached_profile_path(path):
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        f.write(path)

def get_firefox_profile_path():
    options = FirefoxOptions()
    service = FirefoxService(GeckoDriverManager().install())
    driver = webdriver.Firefox(service=service, options=options)

    profile_path = None
    try:
        driver.get("about:profiles")
        sleep(3)
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        tshs = soup.find_all("th", string="Pasta raiz")
        for th in tshs:
            td = th.find_next_sibling("td")
            if td:
                caminho = td.text.strip()
                if "Abrir pasta" in caminho:
                    caminho = caminho.replace("Abrir pasta", "").strip()
                profile_path = caminho
                break
    finally:
        driver.quit()

    return profile_path

def aliexpress(produto, number, time_str):
    # ====== Perfil Firefox ======
    profile_path = get_cached_profile_path()
    if not profile_path:
        profile_path = get_firefox_profile_path()
        if not profile_path:
            app = QApplication(sys.argv)
            profile_path = QFileDialog.getExistingDirectory(None, "Selecione a pasta do perfil do Firefox")
            if not profile_path:
                print("Nenhum perfil selecionado. Encerrando.")
                sys.exit()
        set_cached_profile_path(profile_path)

    options = FirefoxOptions()
    options.profile = profile_path
    # NÃO usar headless
    options.set_preference("dom.webdriver.enabled", False)
    options.set_preference("useAutomationExtension", False)

    service = FirefoxService(GeckoDriverManager().install())
    driver = webdriver.Firefox(service=service, options=options)

    # Remover o WebDriver do navigator (muito importante!)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    url = f"https://pt.aliexpress.com/w/wholesale-{produto}.html?page={number}&g=y&SearchText={produto}"
    driver.get(url)

    print(f"Abrindo a página {url}")
    print("👉 Se aparecer captcha, resolva manualmente. Depois pressione ENTER aqui para continuar...")

    input()  # Espera você resolver manualmente

    sleep(3)  # Pequena pausa extra

    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")

    # Correção: Usar 'kr_j0' para o nome do produto
    nomes = soup.find_all(class_=re.compile(r"\bkr_j0\b"))
    precos_divs = soup.find_all(class_=re.compile(r"\bkr_kj\b"))

    produtos = []
    # Usar min() para garantir que não haja erros se uma lista for menor
    for nome, preco_div in zip(nomes, precos_divs):
        nome_text = nome.get_text(strip=True)
        # Sua lógica para extrair o preço está correta para o HTML fornecido
        spans = preco_div.find_all('span')
        preco_text = ''.join(span.get_text() for span in spans).strip()
        produtos.append([nome_text, preco_text])

    driver.quit()

    # ==== Salvar CSV ====
    # Certifique-se de que a pasta 'data' existe
    output_dir = "data"
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, f"aliexpress_{produto}_{time_str}_page{number}.csv")

    with open(file_path, "w", newline="", encoding="utf-8") as arquivo:
        writer = csv.writer(arquivo)
        writer.writerow(["Nome", "Preço"])
        writer.writerows(produtos)

    print(f"✅ Página {number} salva com sucesso em '{file_path}'!")

# ==== Execução ====
if __name__ == "__main__":
    nome_produto = "notebook"
    # Defina o número inicial de páginas que deseja raspar
    # Você pode querer iterar sobre um número maior de páginas
    # ou deixar o usuário definir quantas páginas quer.
    # Por exemplo, para raspar as 3 primeiras páginas:
    start_page = 1
    num_pages_to_scrape = 1

    agora = datetime.now()
    time_str = agora.strftime("%Y%m%d_H%HM%MS%S") # Adicionado ano, mês, dia para evitar sobrescrever

    for i in range(start_page, start_page + num_pages_to_scrape):
        aliexpress(nome_produto, i, time_str)
        # Adicione uma pausa entre as páginas para evitar ser bloqueado
        sleep(5)