# Price Watcher

![Web Scraper Icon](resources/app_icon.ico) ## Descrição do Projeto

O **Price Watcher** é um aplicativo de desktop robusto e elegante, desenvolvido em Python, com o objetivo de realizar web scraping de preços de produtos em diversas plataformas de e-commerce. Ele consolida os dados coletados e oferece uma visualização gráfica para comparar preços entre os diferentes sites, auxiliando na busca pelas melhores ofertas.

Este projeto utiliza **PyQt6** para a interface gráfica moderna, **Selenium** para a automação de navegadores web, **BeautifulSoup4** para a análise de HTML, **Pandas** para manipulação e limpeza de dados, e **Matplotlib** para a geração de gráficos interativos. O gerenciamento de dependências é feito de forma eficiente com **Poetry**.

## Funcionalidades

* **Scraping Multi-Site:** Suporte para coleta de dados de preços em:
    * AliExpress
    * Mercado Livre
    * Pichau
    * Amazon
    * Kabum
    * TerabyteShop
* **Interface Gráfica (GUI):** Interface de usuário intuitiva e visualmente atraente.
* **Execução em Segundo Plano:** O processo de scraping roda em uma thread separada, mantendo a interface responsiva.
* **Limpeza e Processamento de Dados:** Conversão de preços para formato numérico para análise.
* **Armazenamento de Dados:** Salva os dados raspados em arquivos CSV organizados por site.
* **Visualização de Gráficos:** Gera gráficos comparativos de preços entre os sites para facilitar a análise.
* **Executável Standalone:** Possibilidade de compilar o aplicativo em um único arquivo executável para fácil distribuição (Windows).

## Como Funciona

O aplicativo permite que o usuário selecione um site de e-commerce, digite o nome de um produto e o número de páginas a serem raspadas. Em segundo plano, o Selenium automatiza o navegador para visitar as páginas de busca do site, e o BeautifulSoup extrai os nomes e preços dos produtos. Os dados são então limpos, processados e salvos em arquivos CSV. A aba de gráficos carrega esses dados e os exibe visualmente para comparação.

## Pré-requisitos

Antes de começar, certifique-se de ter os seguintes itens instalados:

* **Python 3.10 ou superior:** [python.org](https://www.python.org/downloads/)
* **Git:** Para clonar o repositório ([git-scm.com](https://git-scm.com/downloads))
* **Navegador Google Chrome e/ou Mozilla Firefox:** Para o Selenium.

## Instalação e Configuração

Siga os passos abaixo para configurar o projeto em seu ambiente local.

### 1. Clonar o Repositório

Abra seu terminal/prompt de comando e clone o repositório do GitHub:

```bash
git clone [https://github.com/Theusprg/price-watcher.git](https://github.com/Theusprg/price-watcher.git)
cd price-watcher
2. Instalar o Poetry
Se você ainda não tem o Poetry instalado, siga as instruções oficiais:

Windows (PowerShell):
PowerShell

(Invoke-WebRequest -Uri [https://install.python-poetry.org](https://install.python-poetry.org) -UseBasicParsing).Content | python -
Linux/macOS (Bash):
Bash

curl -sSL [https://install.python-poetry.org](https://install.python-poetry.org) | python3 -
Após a instalação, feche e reabra seu terminal. Verifique a instalação: poetry --version.

3. Configurar o Projeto com Poetry
Na raiz do seu projeto price-watcher (onde está o pyproject.toml), o Poetry gerenciará as dependências:

Bash

# Instala todas as dependências do projeto no ambiente virtual gerenciado pelo Poetry
# O "--no-root" é usado porque este projeto é um aplicativo, não uma biblioteca PyPI.
poetry install --no-root
4. Baixar os Web Drivers (MUITO IMPORTANTE!)
O Selenium precisa de drivers para controlar os navegadores. Para o executável, eles precisam ser empacotados.

Crie a pasta drivers/ na raiz do seu projeto:
Bash

mkdir drivers
Baixe os drivers necessários e coloque-os em drivers/:
ChromeDriver (para Google Chrome):
Verifique a versão do seu Chrome (ex: chrome://version/).
Baixe a versão correspondente: Google Chrome for Testing ou ChromeDriver Official.
Coloque chromedriver.exe em price-watcher/drivers/.
GeckoDriver (para Mozilla Firefox):
Verifique a versão do seu Firefox (ex: about:support).
Baixe a versão correspondente: GeckoDriver Releases.
Coloque geckodriver.exe em price-watcher/drivers/.
(Repita para outros navegadores como Edge se for usá-los).
5. Estrutura do Projeto
Certifique-se de que seu projeto tem a seguinte estrutura:

price-watcher/
├── .venv/
├── pyproject.toml
├── poetry.lock
├── app.py
├── drivers/
│   ├── chromedriver.exe
│   └── geckodriver.exe
├── scrapers/
│   ├── __init__.py
│   ├── aliexpress.py
│   ├── mercadolivre.py
│   ├── pichau.py
│   ├── amazon.py
│   ├── kabum.py
│   └── terabyteshop.py
├── data/
└── utils/
    ├── __init__.py
    └── data_processor.py
├── resources/  <-- Onde sua imagem de ícone estará
│   └── app_icon.ico
│   └── web_scraper_image.png
└── README.md
Como Executar o Aplicativo
Para rodar o aplicativo em modo de desenvolvimento (usando seu ambiente Python configurado pelo Poetry):

Bash

# Certifique-se de estar na raiz do projeto 'price-watcher'
poetry run python app.py
A interface gráfica será iniciada. Você pode selecionar um site, digitar o produto e o número de páginas, e iniciar o scraping. Os resultados serão salvos na pasta data/ e exibidos na aba "Gráficos".

Como Compilar para um Executável
Para criar um único arquivo executável (.exe no Windows) do seu aplicativo:

Verifique os pré-requisitos de Drivers (Passo 4 da Instalação).

Certifique-se de que sua imagem de ícone (app_icon.ico) está em resources/.

Execute o comando de compilação (no PowerShell no Windows):

PowerShell

poetry run pyinstaller --onefile --windowed `
--add-data "drivers;drivers" `
--add-data "resources;resources" `
--icon "resources/app_icon.ico" `
--name "PriceWatcherApp" `
app.py
--onefile: Cria um único arquivo executável.
--windowed: Impede a abertura do console.
--add-data "origem;destino_no_bundle": Copia pastas e arquivos para o executável.
--icon: Define o ícone do executável.
--name: Define o nome do executável.
O executável final (PriceWatcherApp.exe) será encontrado na pasta dist/ dentro da raiz do seu projeto.

Licença
Este projeto está licenciado sob a Licença MIT. Veja o arquivo LICENSE (ou o cabeçalho no pyproject.toml) para mais detalhes.

Autor
Cia (dragaoking123@gmail.com)