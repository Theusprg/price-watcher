from bs4 import BeautifulSoup
import requests 
import asyncio
from playwright.async_api import async_playwright

# Lista de sites para testar
url_usuario = {
    'Kabum': 'https://www.kabum.com.br/',#FEITO!
    'Terabyteshop': 'https://www.terabyteshop.com.br/',#FEITO!
    'aliexpress': 'https://pt.aliexpress.com/',#FEITO!
    'Pichau': 'https://www.pichau.com.br/', #FEITO!
    'Mercadolivre': 'https://www.mercadolivre.com.br/',#FEITO !  
    'Amazon': 'https://www.amazon.com.br/',
}

# Função que acessa o site e mostra o título da página
async def pegar_titulo(nome, url):
    async with async_playwright() as p:
        navegador = await p.chromium.launch(headless=True)  # navegador visível
        pagina = await navegador.new_page()

        # User-Agent "humano"
        await pagina.set_extra_http_headers({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        })

        print(f"\n🔗 Acessando {nome}: {url}")
        await pagina.goto(url, wait_until='load')
        await pagina.wait_for_timeout(5000)

        titulo_site = await pagina.title()
        print(f"✅ Título da página {nome}: {titulo_site}")
        await navegador.close()

# Função principal que percorre todos os sites
async def testar_todos_os_sites():
    for nome, url in url_usuario.items():
        try:
            await pegar_titulo(nome, url)
        except Exception as e:
            print(f"❌ Erro ao acessar {nome}: {e}")

# Executa
asyncio.run(testar_todos_os_sites())
