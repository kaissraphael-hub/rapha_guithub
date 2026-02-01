import sys
import os
import csv
import unicodedata
from datetime import datetime

# Garante o PyQt5 no seu Linux Mint
sys.path.insert(0, "/home/rapha/Documentos/python testes")

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, 
                             QVBoxLayout, QGridLayout, QFrame, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QLineEdit, QHBoxLayout, 
                             QPushButton, QFileDialog, QDialog, QTextBrowser)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

class DetalhesDialog(QDialog):
    def __init__(self, dados, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"DETALHES: {dados['RES']}")
        self.setMinimumSize(750, 650)
        self.setStyleSheet("background-color: #1a1a1a; color: white; border: 1px solid #404040;")
        layout = QVBoxLayout(self)
        
        lbl_titulo = QLabel(f"📄 DETALHES - {dados['CATEGORIA']}")
        lbl_titulo.setStyleSheet("font-size: 20px; color: #2196F3; font-weight: bold; border:none;")
        layout.addWidget(lbl_titulo)

        self.info = QTextBrowser()
        self.info.setOpenExternalLinks(True) 
        self.info.setStyleSheet("background-color: #262626; border: 1px solid #333; font-size: 15px; padding: 15px; border-radius: 8px;")
        
        link_atende = "https://guarapuava.atende.net/autoatendimento/servicos/consulta-de-processo-digital/detalhar/1"
        
        secao_link = f"""
        <div style='background-color: #2d2d2d; padding: 15px; border-radius: 8px; border: 1px solid #4db8ff; margin-top: 15px;'>
            <b style='color: #FFD700; font-size: 16px;'>🔗 CONSULTA ATENDE.NET:</b><br><br>
            <a href='{link_atende}' style='color: #4db8ff; font-weight: bold; font-size: 15px;'>
                CLIQUE AQUI PARA CONSULTAR O PROCESSO NO NAVEGADOR
            </a>
        </div>
        """

        texto_detalhado = f"""
        <p><b style='color: #FF9800;'>TIPO/CATEGORIA:</b> {dados['CATEGORIA']}</p>
        <p><b style='color: #4CAF50;'>SITUAÇÃO:</b> {dados['STATUS']}</p>
        <p><b style='color: #2196F3;'>NOME/RESOLUÇÃO:</b> {dados['RES']}</p>
        <p><b style='color: #2196F3;'>VALOR:</b> {dados['VAL_STR']}</p>
        <p><b style='color: #2196F3;'>PROTOCOLOS:</b> {dados['PROT']}</p>
        <hr color='#404040'>
        <p><b style='color: #2196F3;'>PROCESSO:</b> {dados['PROC']}</p>
        <p><b style='color: #2196F3;'>CÓDIGO VERIFICADOR:</b> <span style='font-size: 18px; color: #FF9800;'>{dados['COD']}</span></p>
        {secao_link}
        <hr color='#404040'>
        <p><b style='color: #FF9800;'>DESCRIÇÃO DO OBJETO:</b></p>
        <p style='line-height: 1.5;'>{dados['OBJETO']}</p>
        """
        self.info.setHtml(texto_detalhado)
        layout.addWidget(self.info)

        btn_fechar = QPushButton("FECHAR")
        btn_fechar.setStyleSheet("background-color: #444; color: white; padding: 12px; border-radius: 5px; font-weight: bold;")
        btn_fechar.clicked.connect(self.accept)
        layout.addWidget(btn_fechar)

class DashboardSESA(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SESA - Executive Management System (Obras e Emendas)")
        self.resize(1550, 900)
        self.setStyleSheet("QMainWindow { background-color: #1a1a1a; }")

        self.todos_dados = []
        self.dados_filtrados_atualmente = []
        self.carregar_dados()
        self.init_ui()
        self.filtrar()

    def remover_acentos(self, texto):
        if not texto: return ""
        return "".join(c for c in unicodedata.normalize('NFD', str(texto)) if unicodedata.category(c) != 'Mn').lower().strip()

    def carregar_dados(self):
        base_path = os.path.dirname(os.path.abspath(sys.argv[0]))
        caminho = os.path.join(base_path, "dados.csv")
        
        try:
            if not os.path.exists(caminho): return

            with open(caminho, mode='r', encoding='utf-8') as f:
                reader = list(csv.reader(f))
                
                idx_cab = -1
                for i, linha in enumerate(reader):
                    if any("PROTOCOLOS" in str(c).upper() for c in linha):
                        idx_cab = i
                        break
                
                if idx_cab == -1: return
                cab = [str(c).strip().upper() for c in reader[idx_cab]]
                
                def get_idx(termos):
                    for i, col in enumerate(cab):
                        if any(t in col for t in termos): return i
                    return -1

                indices = {
                    "prot": get_idx(["PROTOCOLOS"]),
                    "res": get_idx(["RESOLUÇÃO"]),
                    "status": get_idx(["STATUS RESUMIDOS"]),
                    "valor": get_idx(["VALOR"]),
                    "objeto": get_idx(["OBJETO"]),
                    "proc": get_idx(["PROCESSO"]),
                    "cod": get_idx(["CÓD VERIFICADOR"]),
                    "cat": get_idx(["CATEGORIA"]) # Nova coluna vinda do tratamento
                }

                self.todos_dados = []
                for linha in reader[idx_cab + 1:]:
                    if len(linha) > indices["prot"] and linha[indices["prot"]].strip():
                        v_txt = linha[indices["valor"]].strip()
                        v_limpo = v_txt.replace('R$', '').replace('.', '').replace(',', '.').replace('"', '').strip()
                        try: v_num = float(v_limpo) if v_limpo else 0.0
                        except: v_num = 0.0

                        self.todos_dados.append({
                            "RES": linha[indices["res"]], 
                            "RES_L": self.remover_acentos(linha[indices["res"]]),
                            "PROT": linha[indices["prot"]], 
                            "STATUS": linha[indices["status"]],
                            "OBJETO": linha[indices["objeto"]], 
                            "OBJ_L": self.remover_acentos(linha[indices["objeto"]]),
                            "PROC": linha[indices["proc"]], 
                            "COD": linha[indices["cod"]],
                            "CATEGORIA": linha[indices["cat"]] if indices["cat"] != -1 else "OUTROS",
                            "CAT_L": self.remover_acentos(linha[indices["cat"]] if indices["cat"] != -1 else ""),
                            "VAL_STR": v_txt,
                            "VAL_NUM": v_num
                        })
        except Exception as e: print(f"Erro: {e}")

    def init_ui(self):
        central = QWidget(); self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        top_bar = QHBoxLayout()
        self.f_res = QLineEdit(); self.f_res.setPlaceholderText("📂 BUSCAR NOME OU CATEGORIA...")
        self.f_obj = QLineEdit(); self.f_obj.setPlaceholderText("🔍 BUSCAR NO OBJETO...")
        
        self.btn_limpar = QPushButton("🧹 LIMPAR")
        self.btn_limpar.setStyleSheet("background-color: #f44336; color: white; font-weight: bold; padding: 12px; border-radius: 5px;")
        self.btn_limpar.clicked.connect(self.limpar_filtros)

        self.btn_exp = QPushButton("📥 EXPORTAR")
        self.btn_exp.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 12px; border-radius: 5px;")
        self.btn_exp.clicked.connect(self.exportar_csv)

        top_bar.addWidget(self.f_res, 3); top_bar.addWidget(self.f_obj, 3)
        top_bar.addWidget(self.btn_limpar, 1); top_bar.addWidget(self.btn_exp, 1)
        layout.addLayout(top_bar)
        
        self.grid_cards = QGridLayout(); layout.addLayout(self.grid_cards)

        self.tabela = QTableWidget()
        self.tabela.setColumnCount(8) # Aumentado para 8
        self.tabela.setHorizontalHeaderLabels(['SITUAÇÃO', 'CATEGORIA', 'NOME / RESOLUÇÃO', 'OBJETO', 'VALOR', 'PROTOCOLOS', 'PROCESSO', 'CÓD. VERIF.'])
        self.tabela.setEditTriggers(QTableWidget.NoEditTriggers) 
        self.tabela.setSelectionBehavior(QTableWidget.SelectRows) 
        self.tabela.verticalHeader().setVisible(False)
        self.tabela.cellDoubleClicked.connect(self.abrir_detalhes)

        self.tabela.setStyleSheet("QTableWidget { background-color: #262626; color: white; font-weight: bold; } QHeaderView::section { background-color: #333; color: white; padding: 10px; }")

        header = self.tabela.horizontalHeader()
        self.tabela.setColumnWidth(1, 150) # Categoria
        self.tabela.setColumnWidth(2, 250) # Nome
        header.setSectionResizeMode(3, QHeaderView.Stretch) # Objeto
        layout.addWidget(self.tabela)

        self.f_res.textChanged.connect(self.filtrar)
        self.f_obj.textChanged.connect(self.filtrar)

    def limpar_filtros(self):
        self.f_res.clear(); self.f_obj.clear(); self.filtrar()

    def abrir_detalhes(self, row, col):
        if row < len(self.dados_filtrados_atualmente):
            dialog = DetalhesDialog(self.dados_filtrados_atualmente[row], self)
            dialog.exec_()

    def filtrar(self):
        r_t = self.remover_acentos(self.f_res.text())
        o_t = self.remover_acentos(self.f_obj.text())
        
        # Filtra por Nome OU Categoria na primeira barra de busca
        self.dados_filtrados_atualmente = [
            d for d in self.todos_dados 
            if (r_t in d['RES_L'] or r_t in d['CAT_L']) and o_t in d['OBJ_L']
        ]
        
        self.tabela.setRowCount(len(self.dados_filtrados_atualmente))
        for i, d in enumerate(self.dados_filtrados_atualmente):
            st = d['STATUS'].upper()
            icon = "🔴 CRÍTICO" if "CRÍ" in st else "🟢 OK" if "OK" in st else "🟡 EM ANDAMENTO"
            
            celulas = [icon, d['CATEGORIA'], d['RES'], d['OBJETO'], d['VAL_STR'], d['PROT'], d['PROC'], d['COD']]
            for j, texto in enumerate(celulas):
                item = QTableWidgetItem(str(texto))
                item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
                self.tabela.setItem(i, j, item)
        self.atualizar_cards()

    def atualizar_cards(self):
        for i in reversed(range(self.grid_cards.count())): self.grid_cards.itemAt(i).widget().setParent(None)
        v_total = sum(d['VAL_NUM'] for d in self.dados_filtrados_atualmente)
        vf = f"R$ {v_total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        self.grid_cards.addWidget(self.criar_card("INVESTIMENTO TOTAL", vf, "#4CAF50"), 0, 0)
        self.grid_cards.addWidget(self.criar_card("ITENS VISÍVEIS", str(len(self.dados_filtrados_atualmente)), "#2196F3"), 0, 1)

    def criar_card(self, t, v, c):
        card = QFrame(); card.setStyleSheet(f"background: #262626; border-radius: 10px; border-bottom: 4px solid {c}; padding: 10px;")
        l = QVBoxLayout(card); l.addWidget(QLabel(t)); val = QLabel(v); val.setStyleSheet(f"color: {c}; font-size: 22px; font-weight: bold;"); l.addWidget(val)
        return card

    def exportar_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Salvar Excel", "", "CSV (*.csv)")
        if path:
            with open(path, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f, delimiter=';')
                writer.writerow(['STATUS', 'CATEGORIA', 'NOME', 'OBJETO', 'VALOR', 'PROTOCOLOS', 'PROCESSO', 'CÓDIGO'])
                for d in self.dados_filtrados_atualmente: 
                    writer.writerow([d['STATUS'], d['CATEGORIA'], d['RES'], d['OBJETO'], d['VAL_STR'], d['PROT'], d['PROC'], d['COD']])

if __name__ == "__main__":
    app = QApplication(sys.argv); window = DashboardSESA(); window.show(); sys.exit(app.exec_())