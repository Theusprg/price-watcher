import sys
from PySide6 import QtCore, QtWidgets, QtGui
from datetime import datetime
import os
import re
import json

from scrapers.aliexpress import aliexpress
from scrapers.amazon import amazon
from scrapers.kabum import kabum
from scrapers.mercadolivre import mercadolivre
from scrapers.pichau import pichau
from scrapers.terabyteshop import terabyte

class Aplicativo(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Exemplo com input")

        self.input = QtWidgets.QLineEdit()
        self.input.setPlaceholderText("Digite algum item...")
        self.pages = QtWidgets.QLineEdit()
        self.pages.setPlaceholderText("Digite o número de páginas...")

        self.combo = QtWidgets.QComboBox()
        self.combo.addItems(["AliExpress", "Amazon", "Kabum", "Mercado Livre", "Pichau", "Terabyte Shop", "Todas as Lojas"])

        self.button = QtWidgets.QPushButton("Pesquisar")
        self.label = QtWidgets.QLabel("Esperando entrada...", alignment=QtCore.Qt.AlignCenter)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.input)
        layout.addWidget(self.pages)
        layout.addWidget(self.combo)
        layout.addWidget(self.button)
        layout.addWidget(self.label)
        self.button.clicked.connect(self.executar)

        self.funcoes = {
            "AliExpress": aliexpress,
            "Amazon": amazon,
            "Kabum": kabum,
            "Mercado Livre": mercadolivre,
            "Pichau": pichau,
            "Terabyte Shop": terabyte,
            "Todas as Lojas": lambda termo, paginas, tempo: self.todas_as_lojas()
        }

    def executar(self):
        termo = self.input.text()
        paginas = self.pages.text()
        tempo = datetime.now().strftime("%H:%M:%S")

        loja = self.combo.currentText()
        funcao = self.funcoes.get(loja)

        if funcao:
            resultados = funcao(termo, paginas, tempo)

            self.label.setText(f"Resultados encontrados: {len(resultados)}\nTempo: {tempo}")

            if not os.path.exists("resultados"):
                os.makedirs("resultados")

            nome_limpo = re.sub(r'[\\/*?:"<>|]', "_", f"{termo}_{loja}")

            caminho = f"resultados/{nome_limpo}.txt"

            with open(caminho, "w", encoding="utf-8") as f:
                for item in resultados:
                    if isinstance(item, dict):
                        for chave, valor in item.items():
                            if isinstance(valor, str):
                                valor = valor.replace('\xa0', ' ')
                            f.write(f"{chave}: {valor}\n")
                        f.write("-" * 30 + "\n")  
                    else:
                        f.write(f"{str(item)}\n")
        else:
            self.label.setText("Erro: Selecione uma loja válida.")

    def todas_as_lojas(self):
        termo = self.input.text()
        paginas = self.pages.text()
        tempo = datetime.now().strftime("%H:%M:%S")
        resultados = []
        for func in [aliexpress, amazon, kabum, mercadolivre, pichau, terabyte]:
            try:
                resultados.extend(func(termo, paginas, tempo))
            except Exception as e:
                print(f"Erro na loja {func.__name__}: {e}")
        return resultados


if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    janela = Aplicativo()
    janela.resize(600, 200)
    janela.show()
    sys.exit(app.exec())




