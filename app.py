# app.py

import sys
import os # Importado para manipulação de caminhos de arquivo/diretórios
from datetime import datetime # Importado para timestamps de arquivos
import time # Importado para sleep na thread

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFrame, QMessageBox, QTabWidget,
    QTextEdit # Usado para a área de log
)
from PyQt6.QtGui import QFont, QIntValidator # QIntValidator para validação de input
from PyQt6.QtCore import Qt, QPoint, QThread, pyqtSignal # QThread e pyqtSignal para multithreading

# --- Importar Matplotlib para Gráficos ---
import matplotlib
matplotlib.use('qtagg') # CORRIGIDO: Define o backend do Matplotlib para PyQt6
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas # CORRIGIDO: Importação do FigureCanvas
from matplotlib.figure import Figure
import numpy as np # Para dados de exemplo no gráfico
import pandas as pd # Para manipulação de dados (DataFrames)

# --- Importar módulos de scraping e processamento de dados ---
# Certifique-se que esses arquivos estão na pasta 'scrapers' e 'utils' respectivamente
from scrapers.aliexpress import aliexpress # CORRIGIDO: Nome do módulo
from scrapers.mercadolivre import mercadolivre # CORRIGIDO: Nome do módulo
# Adicione imports para outros scrapers aqui conforme você os cria (ex: from scrapers.amazon import amazon)

# CORRIGIDO: Removida a importação redundante 'import utils.data_processor as data_processor'
from utils.data_processor import limpar_e_converter_preco, carregar_dados_raspados

# --- Classe para a Thread de Scraping ---
class ScraperThread(QThread):
    # Sinais para comunicação com a GUI (pyqtSignal(tipo_do_argumento))
    progress_update = pyqtSignal(str) # Emite mensagens de progresso (ex: "Raspando página X")
    finished = pyqtSignal(object)     # Emite o DataFrame final (ou vazio se interrompido/erro) quando termina
    error = pyqtSignal(str)           # Emite uma mensagem de erro se algo der errado

    def __init__(self, selected_site, product_name, num_pages):
        super().__init__()
        self.selected_site = selected_site
        self.product_name = product_name
        self.num_pages = num_pages
        self.all_scraped_data = [] # Lista para coletar todos os dados brutos de todas as páginas
        self._is_running = True    # Flag para controlar a interrupção da thread

    def run(self):
        """
        Método principal da thread que executa a lógica de scraping.
        """
        self.progress_update.emit(f"Iniciando scraping para '{self.product_name}' no {self.selected_site}...")
        current_time_str = datetime.now().strftime("%Y%m%d_%H%M%S") # Timestamp para nome do arquivo CSV

        try:
            page_offset = 1 # Para AliExpress, começa em 1, incrementa por 1
            ml_offset = 1   # Para Mercado Livre, começa em 1, incrementa por 48

            for i in range(self.num_pages):
                if not self._is_running: # Verifica se a thread foi sinalizada para parar
                    self.progress_update.emit("Scraping interrompido pelo usuário.")
                    break # Sai do loop de páginas

                # --- Lógica de Paginação Específica para Cada Site ---
                if self.selected_site == "AliExpress":
                    self.progress_update.emit(f"Raspando AliExpress - Página {page_offset} de {self.num_pages}...")
                    page_data = aliexpress(self.product_name, page_offset, current_time_str)
                    page_offset += 1 # Prepara para a próxima página do AliExpress
                elif self.selected_site == "Mercado Livre":
                    self.progress_update.emit(f"Raspando Mercado Livre - Offset {ml_offset} (Pág. {i+1} de {self.num_pages})...")
                    page_data = mercadolivre(self.product_name, ml_offset, current_time_str)
                    ml_offset += 48 # Prepara para o próximo offset do Mercado Livre
                # --- Adicione a lógica para os outros sites aqui ---
                # elif self.selected_site == "Amazon":
                #     self.progress_update.emit(f"Raspando Amazon - Página {i+1} de {self.num_pages}...")
                #     page_data = amazon(self.product_name, i + 1, current_time_str)
                # elif self.selected_site == "Kabum":
                #     # Exemplo de chamada para Kabum (assumindo função kabum no seu arquivo kabum.py)
                #     # from scrapers.kabum import kabum
                #     self.progress_update.emit(f"Raspando Kabum - Página {i+1} de {self.num_pages}...")
                #     page_data = kabum(self.product_name, i + 1, current_time_str)
                # ...
                else:
                    self.error.emit(f"Site '{self.selected_site}' não configurado para scraping.")
                    return # Sai da thread se o site não for reconhecido

                if page_data: # Se dados foram coletados na página
                    self.all_scraped_data.extend(page_data) # Adiciona à lista geral de dados
                    self.progress_update.emit(f"Página {i+1} raspada. Total de itens: {len(self.all_scraped_data)}.")
                else:
                    self.progress_update.emit(f"Aviso: Nenhuns dados encontrados na página {i+1} para {self.selected_site}.")
                
                # Pausa entre as requisições para evitar bloqueio (simula comportamento humano)
                if self._is_running and i < self.num_pages - 1: # Pausa apenas se não é a última página e não foi interrompido
                    time.sleep(np.random.uniform(5, 10)) # Pausa aleatória entre 5 e 10 segundos

            # --- Após o Loop de Scraping ---
            if self._is_running: # Verifica se o scraping terminou normalmente (não foi interrompido)
                if not self.all_scraped_data: # Se não coletou nada
                    self.finished.emit(pd.DataFrame()) # Emite DataFrame vazio
                    self.progress_update.emit("Scraping concluído. Nenhuns produtos coletados.")
                    return

                df_raw = pd.DataFrame(self.all_scraped_data)
                df_processed = limpar_e_converter_preco(df_raw.copy()) # Passa uma cópia para evitar warnings

                # --- Salvamento Centralizado em CSV ---
                output_dir = "data"
                os.makedirs(output_dir, exist_ok=True) # Cria a pasta 'data' se não existir
                
                # Nome do arquivo CSV (ex: aliexpress_notebook_20231027_103000.csv)
                output_filename = f"{self.selected_site.lower().replace(' ', '_')}_{self.product_name.replace(' ', '_')}_{current_time_str}.csv"
                output_filepath = os.path.join(output_dir, output_filename)
                
                df_processed.to_csv(output_filepath, index=False, encoding='utf-8-sig') # utf-8-sig para melhor compatibilidade com Excel
                
                self.progress_update.emit(f"Dados salvos em: {output_filepath}")
                self.finished.emit(df_processed) # Emite o DataFrame processado para a GUI
            else: # Se a thread foi interrompida
                self.finished.emit(pd.DataFrame()) # Emite um DataFrame vazio para indicar interrupção

        except Exception as e:
            # Captura qualquer erro inesperado e o envia para a GUI
            self.error.emit(f"Erro inesperado durante o scraping: {str(e)}")

    def stop(self):
        """Método para sinalizar à thread que ela deve parar."""
        self._is_running = False

# --- Classe Principal da Aplicação PyQt6 ---
class ScraperApp(QMainWindow): # Herda de QMainWindow
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Web Scraper de Produtos - Versão Final")
        self.setGeometry(100, 100, 950, 650) # Posição e tamanho inicial da janela
        self.setStyleSheet("background-color: #2C2C2C;") # Cor de fundo principal do aplicativo

        # --- Configurações para Barra de Título Customizada ---
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint) # CORRIGIDO: Remove a barra de título padrão do SO
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground) # CORRIGIDO: Permite fundo transparente para cantos arredondados

        # --- Variáveis para Arrastar a Janela ---
        self.old_pos = None # Armazena a posição do mouse ao iniciar o arrasto
        self.is_maximized = False # Flag para controlar estado de maximização/restauração

        # --- Variáveis de Estado do Aplicativo ---
        self.scraper_thread = None # Referência à instância da thread de scraping
        self.current_scraped_data = pd.DataFrame() # DataFrame para armazenar os dados raspados mais recentemente

        # Lista de sites suportados pelo aplicativo
        self.sites = ["AliExpress", "Mercado Livre", "Amazon", "Kabum", "TerabyteShop", "Pichau"] # AliExpress e ML primeiro para teste

        self.init_ui() # Chama o método para construir a interface

    def init_ui(self):
        """
        Constrói a interface gráfica do usuário.
        """
        # --- Frame Principal da Janela para Bordas Arredondadas ---
        # Um QFrame como widget central que terá os cantos arredondados.
        self.main_window_frame = QFrame(self)
        self.main_window_frame.setStyleSheet("""
            QFrame {
                background-color: #2C2C2C; /* Cor de fundo do corpo do app (mesma do fundo principal) */
                border-radius: 15px; /* Aplica borda arredondada a todo o frame */
            }
        """)
        self.setCentralWidget(self.main_window_frame) # Define este frame como o widget central da QMainWindow

        # --- Layout Vertical Principal dentro do main_window_frame ---
        # Este layout irá empilhar a barra de título customizada e o QTabWidget.
        full_layout = QVBoxLayout(self.main_window_frame)
        full_layout.setContentsMargins(0, 0, 0, 0) # Remove margens do layout
        full_layout.setSpacing(0) # Remove espaçamento entre widgets

        # --- Barra de Título Customizada (Topo da Janela) ---
        title_bar = QFrame(self)
        title_bar.setObjectName("custom_title_bar") # Usado para identificar o frame ao arrastar
        title_bar.setFixedHeight(40) # Altura fixa da barra de título
        title_bar.setStyleSheet("""
            #custom_title_bar {
                background-color: #2C2C2C; /* Cor da barra de título (igual ao corpo do app) */
                border-top-left-radius: 15px; /* Arredonda apenas os cantos superiores */
                border-top-right-radius: 15px;
                border-bottom-left-radius: 0px; /* Garante que os cantos inferiores não sejam arredondados */
                border-bottom-right-radius: 0px;
            }
        """)
        # Layout horizontal para os elementos da barra de título (título e botões)
        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(10, 0, 5, 0) # Margens internas
        title_bar_layout.setSpacing(5) # Espaçamento entre os elementos

        # Label do Título da Janela
        self.title_label = QLabel(self.windowTitle())
        self.title_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold)) # CORRIGIDO: QFont.Weight.Bold
        self.title_label.setStyleSheet("color: #E0E0E0;")
        title_bar_layout.addWidget(self.title_label)
        title_bar_layout.addStretch(1) # Empurra os botões para a direita

        # --- Estilos Comuns para Botões de Controle ---
        button_style = """
            QPushButton {
                background-color: #4A4A4A; /* Fundo cinza médio */
                color: white;
                border: none;
                border-radius: 7px; /* Cantos arredondados */
                font-size: 14px;
            }
            QPushButton:hover { background-color: #6A6A6A; } /* Fundo mais claro no hover */
            QPushButton:pressed { background-color: #8A8A8A; } /* Fundo ainda mais claro no clique */
        """
        # Estilo específico para o botão de fechar
        close_button_style = """
            QPushButton {
                background-color: #E74C3C; /* Vermelho */
                color: white;
                border: none;
                border-radius: 7px;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #C0392B; }
            QPushButton:pressed { background-color: #A0291C; }
        """

        # --- Botões de Controle da Janela (Minimizar, Maximizar/Restaurar, Fechar) ---
        self.min_button = QPushButton("-")
        self.min_button.setFixedSize(30, 30) # Tamanho fixo
        self.min_button.setStyleSheet(button_style)
        self.min_button.clicked.connect(self.showMinimized) # Conecta à função de minimizar
        title_bar_layout.addWidget(self.min_button)

        self.max_button = QPushButton("[]") # Texto para maximizar
        self.max_button.setFixedSize(30, 30)
        self.max_button.setStyleSheet(button_style)
        self.max_button.clicked.connect(self.toggle_maximize_restore) # Conecta à função de alternar maximizar
        title_bar_layout.addWidget(self.max_button)

        self.close_button = QPushButton("X") # Texto para fechar
        self.close_button.setFixedSize(30, 30)
        self.close_button.setStyleSheet(close_button_style)
        self.close_button.clicked.connect(self.close) # Conecta à função de fechar
        title_bar_layout.addWidget(self.close_button)

        full_layout.addWidget(title_bar) # Adiciona a barra de título customizada ao layout principal

        # --- QTabWidget para as Abas ("Scraping" e "Gráficos") ---
        self.tab_widget = QTabWidget(self.main_window_frame)
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane { /* Estilo do painel (área de conteúdo das abas) */
                border: 1px solid #4A4A4A;
                background-color: #2C2C2C;
                border-bottom-left-radius: 15px; /* Arredonda apenas os cantos inferiores */
                border-bottom-right-radius: 15px;
                border-top-left-radius: 0px;
                border-top-right-radius: 0px;
            }
            QTabBar::tab { /* Estilo das abas individuais */
                background: #3A3A3A; /* Cor de fundo da aba inativa */
                color: #B0B0B0; /* Cor do texto da aba inativa */
                padding: 10px 20px; /* Padding interno */
                border-top-left-radius: 8px; /* Cantos superiores arredondados */
                border-top-right-radius: 8px;
                margin-right: 2px; /* Espaço entre as abas */
                min-width: 100px; /* Largura mínima da aba */
            }
            QTabBar::tab:selected { /* Estilo da aba SELECIONADA */
                background: #4A4A4A; /* Fundo mais escuro */
                color: #FFFFFF; /* Texto branco */
                font-weight: bold; /* Negrito */
                border-top: 2px solid #007BFF; /* Linha azul no topo para indicar seleção */
            }
            QTabBar::tab:hover { /* Estilo da aba ao passar o mouse */
                background: #4A4A4A; /* Mesmo fundo da selecionada */
            }
            QTabBar::tab:!selected { /* Estilo para aba NÃO SELECIONADA */
                border-top: 2px solid transparent; /* Para alinhar com a linha da aba selecionada */
            }
        """)
        full_layout.addWidget(self.tab_widget) # Adiciona o TabWidget ao layout principal

        # --- Aba de Scraping ---
        scraping_tab_content = QWidget() # Widget que contém o conteúdo da aba "Scraping"
        scraping_h_layout = QHBoxLayout(scraping_tab_content) # Layout horizontal para conteúdo e sidebar
        scraping_h_layout.setContentsMargins(0, 0, 0, 0)
        scraping_h_layout.setSpacing(0)

        # --- Área de Conteúdo Central (Esquerda/Meio da Aba Scraping) ---
        content_frame = QFrame()
        content_frame.setStyleSheet("background-color: #2C2C2C;") # Cor de fundo da aba
        content_layout = QVBoxLayout(content_frame) # Layout vertical para os elementos de entrada
        content_layout.setContentsMargins(50, 50, 50, 50) # Padding interno
        content_layout.setSpacing(20) # Espaçamento entre widgets
        content_layout.addStretch(1) # Empurra elementos para o centro

        # Campos de Entrada (retornam a referência ao QLineEdit para acesso posterior)
        self.product_input = self._add_input_field(content_layout, "BUSCA", "Digite o nome do produto...", object_name="product_input")
        self.pages_input = self._add_input_field(content_layout, "PÁGINAS", "Número de páginas a raspar...", QIntValidator(1, 999), object_name="pages_input")
        
        # --- Botões de Ação (Iniciar/Parar Scraping) ---
        action_buttons_layout = QHBoxLayout() # Layout horizontal para os botões de ação
        action_buttons_layout.setSpacing(15)
        action_buttons_layout.addStretch(1) # Empurra botões para o centro/direita

        self.start_scraping_button = QPushButton("Iniciar Scraping")
        self.start_scraping_button.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold)) # CORRIGIDO: QFont.Weight.Bold
        self.start_scraping_button.setStyleSheet("""
            QPushButton {
                background-color: #007BFF; /* Azul */
                color: white;
                border-radius: 10px;
                padding: 10px 20px;
                border: none;
            }
            QPushButton:hover { background-color: #0056b3; } /* Azul mais escuro no hover */
            QPushButton:pressed { background-color: #004080; } /* Azul ainda mais escuro no clique */
        """)
        self.start_scraping_button.clicked.connect(self.start_scraping) # Conecta ao método de iniciar
        action_buttons_layout.addWidget(self.start_scraping_button)

        self.stop_scraping_button = QPushButton("Parar Scraping")
        self.stop_scraping_button.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold)) # CORRIGIDO: QFont.Weight.Bold
        self.stop_scraping_button.setStyleSheet("""
            QPushButton {
                background-color: #E74C3C; /* Vermelho */
                color: white;
                border-radius: 10px;
                padding: 10px 20px;
                border: none;
            }
            QPushButton:hover { background-color: #C0392B; }
            QPushButton:pressed { background-color: #A0291C; }
        """)
        self.stop_scraping_button.clicked.connect(self.stop_scraping) # Conecta ao método de parar
        self.stop_scraping_button.setEnabled(False) # Inicia desabilitado
        action_buttons_layout.addWidget(self.stop_scraping_button)
        action_buttons_layout.addStretch(1) # Empurra botões para o centro/esquerda

        content_layout.addLayout(action_buttons_layout) # Adiciona o layout dos botões ao layout de conteúdo

        # --- Label de Status/Log ---
        self.status_label = QLabel("Pronto para iniciar o scraping.")
        status_font = QFont("Segoe UI", 10)
        status_font.setItalic(True) # Texto em itálico
        self.status_label.setFont(status_font)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter) # CORRIGIDO: Centraliza o texto
        self.status_label.setStyleSheet("color: #B0B0B0; margin-top: 20px;") # Cor de texto e margem
        content_layout.addWidget(self.status_label)
        
        content_layout.addStretch(1) # Empurra elementos para o centro/topo
        scraping_h_layout.addWidget(content_frame, 3) # Adiciona o frame de conteúdo ao layout horizontal da aba

        # --- Sidebar (Direita da Aba Scraping) ---
        sidebar_frame = QFrame()
        sidebar_frame.setStyleSheet("background-color: #222222; border-radius: 0px;") # Sidebar mais escura
        sidebar_layout = QVBoxLayout(sidebar_frame) # Layout vertical para os botões da sidebar
        sidebar_layout.setContentsMargins(10, 20, 10, 20) # Padding interno
        sidebar_layout.setSpacing(10) # Espaçamento entre botões
        sidebar_layout.addStretch(1) # Empurra botões para o centro

        # Botões de seleção de site na Sidebar
        self.site_buttons = {} # Dicionário para armazenar referências aos botões (para marcar/desmarcar)
        for site_name in self.sites:
            btn = QPushButton(site_name)
            btn.setFixedSize(160, 45) # Tamanho fixo para os botões
            btn.setFont(QFont("Segoe UI", 12))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #3A3A3A; /* Fundo cinza escuro */
                    color: #E0E0E0; /* Texto quase branco */
                    border: none;
                    border-radius: 22px; /* Formato de pílula */
                    padding: 5px;
                }
                QPushButton:hover {
                    background-color: #5A5A5A; /* Mais claro no hover */
                    border: 1px solid #007BFF; /* Borda azul no hover */
                }
                QPushButton:pressed, QPushButton:checked { /* Quando pressionado ou "selecionado" */
                    background-color: #007BFF; /* Azul */
                    color: white;
                    border: none;
                }
            """)
            btn.setCheckable(True) # Torna o botão "toggleable" (pode ser marcado/desmarcado)
            btn.clicked.connect(lambda checked, s=site_name: self.on_site_selected(s)) # Conecta ao método de seleção de site
            sidebar_layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter) # CORRIGIDO: Alinhamento
            self.site_buttons[site_name] = btn # Guarda a referência

        sidebar_layout.addStretch(1) # Empurra botões para o centro/baixo
        scraping_h_layout.addWidget(sidebar_frame, 1) # Adiciona a sidebar ao layout horizontal da aba

        self.tab_widget.addTab(scraping_tab_content, "Scraping") # Adiciona a aba "Scraping" ao TabWidget

        # --- Aba de Gráficos ---
        graphics_tab_content = QWidget() # Widget que contém o conteúdo da aba "Gráficos"
        self.setup_graphics_tab(graphics_tab_content) # Chama o método para configurar a aba de gráficos
        self.tab_widget.addTab(graphics_tab_content, "Gráficos") # Adiciona a aba "Gráficos" ao TabWidget
        
        # Conecta a mudança de abas para que o gráfico seja atualizado quando o usuário clica na aba de gráficos
        self.tab_widget.currentChanged.connect(self.on_tab_changed)

        # Define um site selecionado inicial. O usuário ainda precisa clicar para confirmar na UI.
        self.selected_site_from_sidebar = self.sites[0] # Padrão para o primeiro site da lista


    # --- Método auxiliar para criar campos de entrada (QLineEdit) ---
    def _add_input_field(self, layout, label_text, placeholder_text, validator=None, object_name=None):
        input_h_layout = QHBoxLayout()

        # Frame para o fundo preto arredondado do "label"
        label_bg_frame = QFrame()
        label_bg_frame.setFixedSize(100, 40)
        label_bg_frame.setStyleSheet("background-color: #3A3A3A; border-radius: 10px;")
        label_bg_layout = QVBoxLayout(label_bg_frame)
        label_bg_layout.setContentsMargins(0,0,0,0)
        label_text_label = QLabel(label_text)
        label_text_label.setAlignment(Qt.AlignmentFlag.AlignCenter) # CORRIGIDO: Alinhamento
        label_text_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold)) # CORRIGIDO: QFont.Weight.Bold
        label_text_label.setStyleSheet("color: #E0E0E0;")
        label_bg_layout.addWidget(label_text_label)
        input_h_layout.addWidget(label_bg_frame)

        # Campo de entrada de texto (QLineEdit)
        input_field = QLineEdit()
        if object_name: # Atribui um objectName para poder acessá-lo depois via findChild ou diretamente
            input_field.setObjectName(object_name)
        input_field.setPlaceholderText(placeholder_text)
        input_field.setFixedHeight(40)
        input_field.setFont(QFont("Segoe UI", 12))
        input_field.setStyleSheet("""
            QLineEdit {
                background-color: #3A3A3A;
                color: #E0E0E0;
                border: none;
                border-radius: 10px;
                padding: 5px 15px;
            }
            QLineEdit::placeholder {
                color: #A0A0A0; /* Cor do texto de placeholder */
            }
        """)
        if validator: # Aplica o validador se fornecido
            input_field.setValidator(validator)
        input_h_layout.addWidget(input_field)

        layout.addLayout(input_h_layout) # Adiciona o layout horizontal ao layout principal da aba

        # Linha divisória sutil
        dashed_line = QLabel("..................................................................")
        dashed_line.setStyleSheet("color: #4A4A4A;")
        dashed_line.setAlignment(Qt.AlignmentFlag.AlignCenter) # CORRIGIDO: Alinhamento
        layout.addWidget(dashed_line)
        
        return input_field # Retorna a referência ao QLineEdit para que a classe principal possa obter seu texto

    # --- Métodos de Controle da Interface (Conectados aos Botões) ---
    def on_site_selected(self, site_name):
        """
        Atualiza o site selecionado e o status na GUI.
        Desmarca outros botões da sidebar.
        """
        self.selected_site_from_sidebar = site_name
        self.status_label.setText(f"Site selecionado: {site_name}. Digite o produto e páginas para iniciar.")
        self.status_label.setStyleSheet("color: #B0B0B0; margin-top: 20px;")
        
        # Garante que apenas o botão clicado permaneça marcado
        for s, btn in self.site_buttons.items():
            if s != site_name:
                btn.setChecked(False) # Desmarca os outros
            else:
                btn.setChecked(True) # Garante que este está marcado

    def start_scraping(self):
        """
        Inicia o processo de scraping em uma thread separada.
        """
        # --- Validações de Entrada ---
        if not hasattr(self, 'selected_site_from_sidebar') or not self.selected_site_from_sidebar:
            QMessageBox.warning(self, "Site Não Selecionado", "Por favor, selecione um site na barra lateral primeiro.")
            return

        product_name = self.product_input.text().strip()
        num_pages_str = self.pages_input.text().strip()

        if not product_name:
            QMessageBox.warning(self, "Entrada Inválida", "Por favor, insira o nome do produto para a busca.")
            self.status_label.setText("Erro: Nome do produto é obrigatório!")
            self.status_label.setStyleSheet("color: #E74C3C; margin-top: 20px;")
            return
        if not num_pages_str.isdigit() or int(num_pages_str) <= 0:
            QMessageBox.warning(self, "Entrada Inválida", "Número de páginas inválido. Use apenas números inteiros maiores que zero.")
            self.status_label.setText("Erro: Número de páginas inválido!")
            self.status_label.setStyleSheet("color: #E74C3C; margin-top: 20px;")
            return

        num_pages = int(num_pages_str)

        # --- Atualiza a UI para o início do scraping ---
        self.status_label.setText(f"Iniciando scraping para '{product_name}' em {self.selected_site_from_sidebar} ({num_pages} páginas)...")
        self.status_label.setStyleSheet("color: #007BFF; margin-top: 20px;") # Cor de status de processo
        
        self.start_scraping_button.setEnabled(False) # Desabilita o botão "Iniciar"
        self.stop_scraping_button.setEnabled(True)   # Habilita o botão "Parar"
        # Desabilita todos os botões da sidebar para evitar nova seleção durante o scraping
        for btn in self.site_buttons.values():
            btn.setEnabled(False)

        # --- Cria e Inicia a Thread de Scraping ---
        self.scraper_thread = ScraperThread(self.selected_site_from_sidebar, product_name, num_pages)
        # Conecta os sinais da thread aos slots da classe principal
        self.scraper_thread.progress_update.connect(self.on_scraping_progress)
        self.scraper_thread.finished.connect(self.on_scraping_finished)
        self.scraper_thread.error.connect(self.on_scraping_error)
        self.scraper_thread.start() # Inicia a execução da thread

    def stop_scraping(self):
        """
        Sinaliza para a thread de scraping que ela deve parar.
        """
        if self.scraper_thread and self.scraper_thread.isRunning():
            self.scraper_thread.stop() # Chama o método stop na thread
            self.status_label.setText("Solicitação para parar o scraping enviada...")
            self.status_label.setStyleSheet("color: orange; margin-top: 20px;")
        # Os botões serão reabilitados quando a thread realmente parar e emitir 'finished' ou 'error'

    # --- Slots para Receber Sinais da Thread de Scraping ---
    def on_scraping_progress(self, message):
        """Atualiza a label de status com o progresso do scraping."""
        self.status_label.setText(message)
        self.status_label.setStyleSheet("color: #B0B0B0; margin-top: 20px;")

    def on_scraping_finished(self, df_processed_data):
        """
        Chamado quando a thread de scraping termina (sucesso ou interrupção).
        """
        self.current_scraped_data = df_processed_data # Armazena o DataFrame final

        # Reabilita os botões da UI
        self.start_scraping_button.setEnabled(True)
        self.stop_scraping_button.setEnabled(False)
        for btn in self.site_buttons.values():
            btn.setEnabled(True) # Habilita os botões da sidebar novamente

        if not df_processed_data.empty: # Se há dados coletados
            self.status_label.setText("Scraping concluído! Dados salvos e prontos para análise.")
            self.status_label.setStyleSheet("color: #27AE60; margin-top: 20px;") # Cor verde para sucesso
            QMessageBox.information(self, "Scraping Concluído", "Dados coletados e salvos com sucesso!")
            self.plot_scraped_data() # Atualiza o gráfico com os novos dados
            self.tab_widget.setCurrentIndex(1) # Muda para a aba de Gráficos automaticamente
        else: # Se não coletou nada ou foi interrompido
            self.status_label.setText("Scraping finalizado, mas nenhum dado foi coletado ou o processo foi interrompido.")
            self.status_label.setStyleSheet("color: orange; margin-top: 20px;")
            QMessageBox.information(self, "Scraping Concluído", "Nenhum dado coletado ou processo interrompido.")

    def on_scraping_error(self, message):
        """
        Chamado quando a thread de scraping encontra um erro.
        """
        self.status_label.setText(f"Erro no scraping: {message}")
        self.status_label.setStyleSheet("color: #E74C3C; margin-top: 20px;") # Cor vermelha para erro
        
        # Reabilita os botões da UI
        self.start_scraping_button.setEnabled(True)
        self.stop_scraping_button.setEnabled(False)
        for btn in self.site_buttons.values():
            btn.setEnabled(True)
        QMessageBox.critical(self, "Erro no Scraping", message)
    
    # --- Métodos para Aba de Gráficos ---
    def on_tab_changed(self, index):
        """
        Chamado quando a aba do QTabWidget é alterada.
        Atualiza o gráfico se a aba de gráficos for selecionada.
        """
        if index == 1: # Assumindo que a aba de gráficos é a segunda (índex 1)
            self.plot_scraped_data()

    def setup_graphics_tab(self, tab_widget):
        """
        Configura o layout e os elementos da aba de gráficos.
        """
        graphics_layout = QVBoxLayout(tab_widget)
        graphics_layout.setContentsMargins(20, 20, 20, 20)
        graphics_layout.setSpacing(15)

        chart_title = QLabel("Comparativo de Preços por Site")
        chart_title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold)) # CORRIGIDO: QFont.Weight.Bold
        chart_title.setAlignment(Qt.AlignmentFlag.AlignCenter) # CORRIGIDO: Alinhamento
        chart_title.setStyleSheet("color: #E0E0E0;")
        graphics_layout.addWidget(chart_title)

        self.figure = Figure(figsize=(8, 6), facecolor='#2C2C2C') # Fundo da figura igual ao corpo do app
        self.canvas = FigureCanvas(self.figure)
        graphics_layout.addWidget(self.canvas)

        # Botão para Atualizar Gráfico (agora com dados reais carregados)
        self.update_chart_button = QPushButton("Atualizar Gráfico com Dados Atuais")
        self.update_chart_button.setFont(QFont("Segoe UI", 12))
        self.update_chart_button.setStyleSheet("""
            QPushButton {
                background-color: #007BFF;
                color: white;
                border-radius: 8px;
                padding: 8px 15px;
            }
            QPushButton:hover { background-color: #0056b3; }
        """)
        self.update_chart_button.clicked.connect(self.plot_scraped_data) # Conecta ao método de plotagem
        graphics_layout.addWidget(self.update_chart_button)

        self.plot_scraped_data() # Plota dados iniciais (vazios ou do último scraping/carregamento)

    def plot_scraped_data(self):
        """
        Carrega dados dos CSVs existentes (ou usa os dados raspados mais recentes),
        limpa-os e plota o gráfico.
        """
        self.figure.clear() # Limpa o gráfico anterior
        
        # CORRIGIDO: ax precisa ser definido ANTES de ser usado para ax.text ou outras operações
        ax = self.figure.add_subplot(111)
        ax.set_facecolor('#3A3A3A') # Cor de fundo da área do gráfico


        df_to_plot = self.current_scraped_data # Tenta usar os dados raspados mais recentes

        if df_to_plot.empty: # Se não há dados raspados recentemente, tenta carregar dos CSVs
            # self.status_label.setText("Nenhuns dados recentes na memória, tentando carregar de 'data/'...") # Não atualiza o status de dentro do plot
            df_to_plot = carregar_dados_raspados(diretorio_dados="data")
            # Se carregou algo, processa novamente para ter certeza
            if not df_to_plot.empty:
                df_to_plot = limpar_e_converter_preco(df_to_plot.copy())
                df_to_plot = df_to_plot.dropna(subset=['Preço Numérico']) # Remove linhas sem preço numérico
            
            if df_to_plot.empty: # Se mesmo depois de carregar e limpar, ainda está vazio
                ax.text(0.5, 0.5, "Nenhuns dados disponíveis para gráfico.\nExecute o scraping primeiro.",
                        horizontalalignment='center', verticalalignment='center',
                        transform=ax.transAxes, color='#B0B0B0', fontsize=12)
                ax.set_xticks([]) # Remove ticks se não há dados
                ax.set_yticks([])
                ax.spines['top'].set_visible(False) # Remove bordas
                ax.spines['right'].set_visible(False)
                ax.spines['bottom'].set_visible(False)
                ax.spines['left'].set_visible(False)
                self.canvas.draw()
                # self.status_label.setText("Gráfico: Nenhum dado válido encontrado para plotar.") # Não atualiza o status de dentro do plot
                return


        # --- Se houver dados válidos, plota o gráfico ---
        if 'Preço Numérico' in df_to_plot.columns and 'Site' in df_to_plot.columns:
            # Calcula a média do preço numérico por site
            average_prices = df_to_plot.groupby('Site')['Preço Numérico'].mean().reset_index()
            
            if not average_prices.empty:
                sites_data = average_prices['Site'].tolist()
                chart_prices = average_prices['Preço Numérico'].tolist()

                ax.bar(sites_data, chart_prices, color='#007BFF')
                ax.set_title("Preço Médio por Site (Dados Raspados)", color='#E0E0E0', fontsize=14)
            else: # Se o agrupamento resultou em DataFrame vazio (ex: todos os preços eram None)
                ax.text(0.5, 0.5, "Nenhum dado numérico válido após agrupamento.", horizontalalignment='center', verticalalignment='center', color='#B0B0B0', transform=ax.transAxes)
                ax.set_title("Nenhum Dado para Gráfico", color='#E0E0E0', fontsize=14)
        else: # Se as colunas essenciais não existem no DataFrame
            ax.text(0.5, 0.5, "Colunas 'Site' ou 'Preço Numérico' não encontradas nos dados.", horizontalalignment='center', verticalalignment='center', color='#B0B0B0', transform=ax.transAxes)
            ax.set_title("Erro nas Colunas de Dados", color='#E0E0E0', fontsize=14)


        ax.set_xlabel("Site", color='#B0B0B0', fontsize=12)
        ax.set_ylabel("Preço Médio (R$)", color='#B0B0B0', fontsize=12)

        ax.tick_params(axis='x', colors='#B0B0B0')
        ax.tick_params(axis='y', colors='#B0B0B0')

        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_color('#4A4A4A')
        ax.spines['left'].set_color('#4A4A4A')

        self.canvas.draw() # Desenha o gráfico


    # --- Métodos para Arrastar e Controlar a Janela Customizada ---
    def mousePressEvent(self, event):
        """Detecta clique do mouse para iniciar arrasto da janela."""
        if event.button() == Qt.MouseButton.LeftButton: # CORRIGIDO: MouseButton
            # Verifica se o clique foi na barra de título customizada
            # self.findChild(QFrame, 'custom_title_bar') busca o QFrame com o objectName dado
            if self.findChild(QFrame, 'custom_title_bar').geometry().contains(event.pos()):
                self.old_pos = event.globalPos() # Armazena a posição global do mouse
            else:
                self.old_pos = None # Não permite arrastar se não clicou na barra de título

    def mouseMoveEvent(self, event):
        """Move a janela enquanto o mouse é arrastado com o botão pressionado."""
        if self.old_pos is not None:
            # Calcula o deslocamento do mouse
            delta = QPoint(event.globalPos() - self.old_pos)
            self.move(self.pos() + delta) # Move a janela pela diferença
            self.old_pos = event.globalPos() # Atualiza a posição antiga do mouse

    def mouseReleaseEvent(self, event):
        """Reseta a posição antiga do mouse quando o botão é liberado."""
        self.old_pos = None

    def toggle_maximize_restore(self):
        """Alterna entre maximizar e restaurar a janela."""
        if self.isMaximized():
            self.showNormal() # Restaura a janela
            self.max_button.setText("[]") # Muda o texto/ícone do botão
        else:
            self.showMaximized() # Maximiza a janela
            self.max_button.setText("🗗") # Muda o texto/ícone do botão (símbolo Unicode para restaurar)

# --- Bloco de Execução Principal da Aplicação ---
if __name__ == "__main__":
    app = QApplication(sys.argv) # Cria a instância da aplicação PyQt
    window = ScraperApp()       # Cria a instância da sua janela principal
    window.show()               # Exibe a janela
    sys.exit(app.exec())        # Inicia o loop de eventos da aplicação (CORRIGIDO para PyQt6)      