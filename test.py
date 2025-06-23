import sys
from PyQt6.QtWidgets import ( # Mudou de PyQt5 para PyQt6
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFrame, QSizePolicy, QTabWidget
)
from PyQt6.QtGui import QFont, QIntValidator, QColor, QPalette # Mudou de PyQt5 para PyQt6
from PyQt6.QtCore import Qt, QPoint # Mudou de PyQt5 para PyQt6

# --- Importar Matplotlib para Gráficos ---
import matplotlib
matplotlib.use('Qt6Agg') # <--- MUITO IMPORTANTE! Backend do Matplotlib agora é para PyQt6
from matplotlib.backends.backend_qt6agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np # Para dados de exemplo

class ScraperApp(QMainWindow): # Mudamos para QMainWindow
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Web Scraper de Produtos - Versão Final (Demo)")
        self.setGeometry(100, 100, 950, 650) # Tamanho da janela aumentado para gráficos
        self.setStyleSheet("background-color: #2C2C2C;") # Fundo principal mais escuro e uniforme

        # --- Remover a barra de título nativa ---
        self.setWindowFlags(Qt.FramelessWindowHint)
        # Permite que o fundo seja transparente para bordas arredondadas da janela
        self.setAttribute(Qt.WA_TranslucentBackground) 

        # Variáveis para arrastar a janela
        self.old_pos = None

        # Lista de sites (agora como atributo da classe)
        self.sites = ["Amazon", "AliExpress", "Mercado Livre", "Kabum", "TerabyteShop", "Pichau"]

        self.init_ui()

    def init_ui(self):
        # --- Frame para o conteúdo principal da janela (para bordas arredondadas) ---
        self.main_window_frame = QFrame(self)
        self.main_window_frame.setStyleSheet("""
            QFrame {
                background-color: #2C2C2C; /* Cor de fundo do corpo do app */
                border-radius: 15px; /* Cantos arredondados para toda a janela */
            }
        """)
        self.setCentralWidget(self.main_window_frame) # Define como widget central da QMainWindow

        # Layout vertical principal dentro do frame
        full_layout = QVBoxLayout(self.main_window_frame)
        full_layout.setContentsMargins(0, 0, 0, 0)
        full_layout.setSpacing(0)

        # --- Barra de Título Customizada ---
        title_bar = QFrame(self)
        # Damos um objectName para identificar no mousePressEvent se o clique foi nele
        title_bar.setObjectName("custom_title_bar") 
        title_bar.setFixedHeight(40) # Altura da barra de título
        title_bar.setStyleSheet("""
            #custom_title_bar {
                background-color: #2C2C2C; /* Cor da barra de título (igual ao corpo) */
                border-top-left-radius: 15px; /* Arredonda só os de cima */
                border-top-right-radius: 15px;
                border-bottom-left-radius: 0px; /* Garante que os de baixo não arredondem */
                border-bottom-right-radius: 0px;
            }
        """)
        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(10, 0, 5, 0)
        title_bar_layout.setSpacing(5)

        # Título da Janela
        self.title_label = QLabel(self.windowTitle())
        self.title_label.setFont(QFont("Segoe UI", 12, QFont.Bold)) # Fonte mais moderna
        self.title_label.setStyleSheet("color: #E0E0E0;")
        title_bar_layout.addWidget(self.title_label)
        title_bar_layout.addStretch(1)

        # Botões da Barra de Título (Minimizar, Maximizar/Restaurar, Fechar)
        button_style = """
            QPushButton {
                background-color: #4A4A4A; /* Botões mais suaves */
                color: white;
                border: none;
                border-radius: 7px; /* Cantos um pouco mais suaves */
                font-size: 14px;
            }
            QPushButton:hover { background-color: #6A6A6A; }
            QPushButton:pressed { background-color: #8A8A8A; }
        """
        # Close Button (cor diferente)
        close_button_style = """
            QPushButton {
                background-color: #E74C3C; /* Vermelho para fechar */
                color: white;
                border: none;
                border-radius: 7px;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #C0392B; }
            QPushButton:pressed { background-color: #A0291C; }
        """

        self.min_button = QPushButton("-")
        self.min_button.setFixedSize(30, 30)
        self.min_button.setStyleSheet(button_style)
        self.min_button.clicked.connect(self.showMinimized)
        title_bar_layout.addWidget(self.min_button)

        self.max_button = QPushButton("[]")
        self.max_button.setFixedSize(30, 30)
        self.max_button.setStyleSheet(button_style)
        self.max_button.clicked.connect(self.toggle_maximize_restore)
        title_bar_layout.addWidget(self.max_button)

        self.close_button = QPushButton("X")
        self.close_button.setFixedSize(30, 30)
        self.close_button.setStyleSheet(close_button_style)
        self.close_button.clicked.connect(self.close)
        title_bar_layout.addWidget(self.close_button)

        full_layout.addWidget(title_bar) # Adiciona a barra de título customizada

        # --- QTabWidget para as abas (Scraping e Gráficos) ---
        self.tab_widget = QTabWidget(self.main_window_frame)
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane { /* A área onde o conteúdo das abas é exibido */
                border: 1px solid #4A4A4A;
                background-color: #2C2C2C;
                border-bottom-left-radius: 15px; /* Arredonda só os de baixo */
                border-bottom-right-radius: 15px;
                border-top-left-radius: 0px;
                border-top-right-radius: 0px;
            }
            QTabBar::tab {
                background: #3A3A3A; /* Cor das abas inativas */
                color: #B0B0B0;
                padding: 10px 20px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                margin-right: 2px;
                min-width: 100px; /* Largura mínima para as abas */
            }
            QTabBar::tab:selected {
                background: #4A4A4A; /* Cor da aba selecionada */
                color: #FFFFFF;
                font-weight: bold;
                border-top: 2px solid #007BFF; /* Linha azul na aba selecionada */
            }
            QTabBar::tab:hover {
                background: #4A4A4A;
            }
            QTabBar::tab:!selected { /* Aba não selecionada */
                border-top: 2px solid transparent; /* Para alinhar com a linha da selecionada */
            }
        """)
        full_layout.addWidget(self.tab_widget) # Adiciona o TabWidget ao layout principal

        # --- Aba de Scraping ---
        scraping_tab_content = QWidget()
        # O mesmo layout horizontal que você já tinha para o conteúdo e a sidebar
        scraping_h_layout = QHBoxLayout(scraping_tab_content)
        scraping_h_layout.setContentsMargins(0, 0, 0, 0)
        scraping_h_layout.setSpacing(0)

        # --- Content Area (Left/Middle) ---
        content_frame = QFrame()
        content_frame.setStyleSheet("background-color: #2C2C2C;") # Cor do fundo da aba
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(50, 50, 50, 50)
        content_layout.setSpacing(20)
        content_layout.addStretch(1)

        # Labels e QLineEdits estilizados
        self._add_input_field(content_layout, "BUSCA", "Digite o nome do produto...")
        self._add_input_field(content_layout, "PÁGINAS", "Número de páginas a raspar...", QIntValidator(1, 999))
        
        content_layout.addStretch(1)
        scraping_h_layout.addWidget(content_frame, 3)

        # --- Sidebar (Right) ---
        sidebar_frame = QFrame()
        sidebar_frame.setStyleSheet("background-color: #222222; border-radius: 0px;") # Sidebar mais escura
        sidebar_layout = QVBoxLayout(sidebar_frame)
        sidebar_layout.setContentsMargins(10, 20, 10, 20)
        sidebar_layout.setSpacing(10)
        sidebar_layout.addStretch(1)

        # Botões de seleção de site
        for site_name in self.sites:
            btn = QPushButton(site_name)
            btn.setFixedSize(160, 45) # Tamanho dos botões ligeiramente maior
            btn.setFont(QFont("Segoe UI", 12)) # Fonte para os botões
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #3A3A3A;
                    color: #E0E0E0;
                    border: none;
                    border-radius: 22px; /* Metade da altura para pílula */
                    padding: 5px;
                }
                QPushButton:hover {
                    background-color: #5A5A5A;
                    border: 1px solid #007BFF; /* Borda azul no hover */
                }
                QPushButton:pressed {
                    background-color: #007BFF; /* Azul quando pressionado */
                    color: white;
                }
            """)
            btn.clicked.connect(lambda checked, s=site_name: print(f"Site selecionado: {s}"))
            sidebar_layout.addWidget(btn, alignment=Qt.AlignCenter)

        sidebar_layout.addStretch(1)
        scraping_h_layout.addWidget(sidebar_frame, 1)

        self.tab_widget.addTab(scraping_tab_content, "Scraping")

        # --- Aba de Gráficos ---
        graphics_tab_content = QWidget()
        self.setup_graphics_tab(graphics_tab_content) # Chama a função para configurar a aba de gráficos
        self.tab_widget.addTab(graphics_tab_content, "Gráficos")

    # --- Método auxiliar para criar campos de entrada (reuso de código) ---
    def _add_input_field(self, layout, label_text, placeholder_text, validator=None):
        input_h_layout = QHBoxLayout()

        label_bg_frame = QFrame()
        label_bg_frame.setFixedSize(100, 40) # Tamanho do retângulo do label
        label_bg_frame.setStyleSheet("background-color: #3A3A3A; border-radius: 10px;")
        label_bg_layout = QVBoxLayout(label_bg_frame)
        label_bg_layout.setContentsMargins(0,0,0,0)
        label_text_label = QLabel(label_text)
        label_text_label.setAlignment(Qt.AlignCenter)
        label_text_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        label_text_label.setStyleSheet("color: #E0E0E0;")
        label_bg_layout.addWidget(label_text_label)
        input_h_layout.addWidget(label_bg_frame)

        input_field = QLineEdit()
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
                color: #A0A0A0;
            }
        """)
        if validator:
            input_field.setValidator(validator)
        input_h_layout.addWidget(input_field)

        layout.addLayout(input_h_layout)

        # Adiciona uma linha divisória sutil
        dashed_line = QLabel("..................................................................")
        dashed_line.setStyleSheet("color: #4A4A4A;")
        dashed_line.setAlignment(Qt.AlignCenter)
        layout.addWidget(dashed_line)


    # --- Configuração da Aba de Gráficos ---
    def setup_graphics_tab(self, tab_widget):
        graphics_layout = QVBoxLayout(tab_widget)
        graphics_layout.setContentsMargins(20, 20, 20, 20) # Padding interno da aba
        graphics_layout.setSpacing(15)

        # Título da aba de gráficos
        chart_title = QLabel("Comparativo de Preços por Site (Exemplo)")
        chart_title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        chart_title.setAlignment(Qt.AlignCenter)
        chart_title.setStyleSheet("color: #E0E0E0;")
        graphics_layout.addWidget(chart_title)

        # --- Configuração do Gráfico Matplotlib ---
        self.figure = Figure(figsize=(8, 6), facecolor='#2C2C2C') # Fundo da figura igual ao corpo do app
        self.canvas = FigureCanvas(self.figure)
        graphics_layout.addWidget(self.canvas)

        # Criar um subplot (o "eixo" do gráfico)
        ax = self.figure.add_subplot(111)
        ax.set_facecolor('#3A3A3A') # Cor de fundo da área do gráfico

        # Dados de exemplo para o gráfico
        sites_data = ["ML", "Ali", "Kabum", "Amazon", "Terabyte", "Pichau"]
        prices_data = np.random.randint(500, 3000, len(sites_data)) # Preços aleatórios de exemplo

        # Criar um gráfico de barras
        ax.bar(sites_data, prices_data, color='#007BFF') # Barras azuis

        # Estilizar o gráfico para o tema escuro
        ax.set_title("Preço Médio por Site (Fake Data)", color='#E0E0E0', fontsize=14)
        ax.set_xlabel("Site", color='#B0B0B0', fontsize=12)
        ax.set_ylabel("Preço (R$)", color='#B0B0B0', fontsize=12)

        ax.tick_params(axis='x', colors='#B0B0B0') # Cor dos rótulos do eixo X
        ax.tick_params(axis='y', colors='#B0B0B0') # Cor dos rótulos do eixo Y

        # Remover bordas e ticks desnecessários
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_color('#4A4A4A')
        ax.spines['left'].set_color('#4A4A4A')

        self.canvas.draw() # Desenha o gráfico no canvas

        # --- Botão para Atualizar Gráfico (com dados de exemplo por enquanto) ---
        self.update_chart_button = QPushButton("Atualizar Gráfico com Dados (Exemplo)")
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
        self.update_chart_button.clicked.connect(self.plot_example_data) # Conectar a uma função para plotar dados
        graphics_layout.addWidget(self.update_chart_button)


    def plot_example_data(self):
        # Limpa o gráfico anterior
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.set_facecolor('#3A3A3A')

        # --- Dados de Exemplo (você substituirá isso pelos seus dados raspados) ---
        sites_data = ["ML", "Ali", "Kabum", "Amazon", "Terabyte", "Pichau"]
        prices_data = {
            "ML": np.random.randint(1000, 2000),
            "Ali": np.random.randint(900, 1800),
            "Kabum": np.random.randint(1100, 2200),
            "Amazon": np.random.randint(950, 1900),
            "Terabyte": np.random.randint(1050, 2100),
            "Pichau": np.random.randint(1150, 2300)
        }
        chart_prices = [prices_data.get(site, 0) for site in sites_data]

        # Criar um gráfico de barras
        ax.bar(sites_data, chart_prices, color='#007BFF')

        # Estilizar o gráfico para o tema escuro
        ax.set_title("Preço Médio por Site", color='#E0E0E0', fontsize=14)
        ax.set_xlabel("Site", color='#B0B0B0', fontsize=12)
        ax.set_ylabel("Preço (R$)", color='#B0B0B0', fontsize=12)

        ax.tick_params(axis='x', colors='#B0B0B0')
        ax.tick_params(axis='y', colors='#B0B0B0')

        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_color('#4A4A4A')
        ax.spines['left'].set_color('#4A4A4A')

        self.canvas.draw() # Redesenha o gráfico

    # --- Métodos para Arrastar e Redimensionar a Janela Customizada ---
    def mousePressEvent(self, event):
        # Apenas permite arrastar se o clique for na barra de título customizada
        if event.button() == Qt.LeftButton:
            # Verifica se o clique foi dentro da área da barra de título customizada
            # findChild encontra o widget pelo objectName
            if self.findChild(QFrame, 'custom_title_bar').geometry().contains(event.pos()):
                self.old_pos = event.globalPos() # Posição global do mouse ao clicar
            else:
                self.old_pos = None # Reset para não arrastar se não clicou na barra

    def mouseMoveEvent(self, event):
        if self.old_pos is not None:
            delta = QPoint(event.globalPos() - self.old_pos)
            self.move(self.pos() + delta)
            self.old_pos = event.globalPos()

    def mouseReleaseEvent(self, event):
        self.old_pos = None

    def toggle_maximize_restore(self):
        if self.isMaximized():
            self.showNormal()
            self.max_button.setText("[]")
        else:
            self.showMaximized()
            self.max_button.setText("🗗") # Ícone de restaurar (ou use um símbolo diferente)


# --- Bloco de Execução Principal ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ScraperApp()
    window.show()
    sys.exit(app.exec_())