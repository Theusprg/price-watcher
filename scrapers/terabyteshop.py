import sys
import os
from bs4 import BeautifulSoup
from time import sleep
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import re

# Nome do arquivo que guarda o caminho do perfil do Firefox
PERFIL_CACHE = "cache_perfil_firefox.txt"

def get_driver_path(driver_name):
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        bundle_dir = sys._MEIPASS
    else:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        bundle_dir = project_root
    return os.path.join(bundle_dir, 'drivers', driver_name)

def carregar_caminho_perfil():
    if os.path.exists(PERFIL_CACHE):
        with open(PERFIL_CACHE, "r", encoding="utf-8") as f:
            caminho = f.read().strip()
        if os.path.exists(caminho):
            return caminho
        else:
            print(f"Aviso: caminho salvo no cache '{caminho}' não existe.")
    # Se não existir cache ou caminho inválido, pede para o usuário digitar
    caminho = input("Digite o caminho completo do seu perfil Firefox: ").strip()
    with open(PERFIL_CACHE, "w", encoding="utf-8") as f:
        f.write(caminho)
    return caminho

def terabyte(produto, page_number, time_str):
    options = FirefoxOptions()
    # options.add_argument("--headless=new")  # Descomente se quiser headless
    
    options.set_preference("dom.webdriver.enabled", False)
    options.set_preference("useAutomationExtension", False)
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0")
    options.add_argument("--start-maximized")

    # Usa o perfil do Firefox do usuário
    caminho_perfil = carregar_caminho_perfil()
    options.profile = caminho_perfil

    driver_executable_path = get_driver_path("geckodriver.exe")
    if not os.path.exists(driver_executable_path):
        raise FileNotFoundError(f"Erro: Driver '{driver_executable_path}' não encontrado. Baixe-o e coloque na pasta 'drivers/' do seu projeto.")

    driver = None

    try:
        service = FirefoxService(executable_path=driver_executable_path)
        driver = webdriver.Firefox(service=service, options=options)

        url = f"https://www.terabyteshop.com.br/busca?str={produto}"
        driver.get(url)

        initial_page_source = driver.page_source
        print(f"DEBUG_TERABYTE: Page source inicial (primeiras 500 chars):\n{initial_page_source[:500]}")
        if "<html><head></head><body></body></html>" in initial_page_source.lower() or len(initial_page_source) < 100:
            print("DEBUG_TERABYTE: Page source inicial parece estar em branco ou muito vazio.")

        WebDriverWait(driver, 30).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "a.product-item__name"))
        )
        sleep(2)

        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")

        produtos_raspados = []

        nomes_elems = soup.find_all(class_=re.compile(r"\bproduct-item__name\b"))
        preco_elems = soup.find_all(class_=re.compile(r"\bproduct-item__new-price\b"))

        for nome_elem, preco_elem in zip(nomes_elems, preco_elems):
            nome_text = nome_elem.get_text(strip=True)
            preco_text_bruto = preco_elem.get_text(strip=True)
            link_produto = nome_elem.get('href') if nome_elem else "N/A"

            produtos_raspados.append({
                "Site": "TerabyteShop",
                "Nome do Produto": nome_text,
                "Preço Bruto": preco_text_bruto,
                "Link do Produto": link_produto,
                "Data do Scraping": time_str
            })

        return produtos_raspados

    except Exception as e:
        print(f"DEBUG_TERABYTE: Erro inesperado na função terabyte: {e}")
        if "timeout" in str(e).lower():
            print("DEBUG_TERABYTE: Tempo limite excedido ao carregar a página. Site pode estar bloqueando ou muito lento.")
        return []
    finally:
        if driver:
            driver.quit()
            print("DEBUG_TERABYTE: Navegador fechado (finally block).")
