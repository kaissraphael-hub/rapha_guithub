import sys
import os
import csv
import unicodedata
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, 
                             QVBoxLayout, QGridLayout, QFrame, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QLineEdit, QHBoxLayout, 
                             QPushButton, QFileDialog, QDialog, QTextBrowser)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor

# Ajuste o caminho do PyQt5 se necessário
sys.path.insert(0, "/home/rapha/Documentos/python testes")

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
        self.info.setStyleSheet("background-color: #262626; border: 1px solid #333; font-size: 15px; padding: 15px; border-radius: 8px;")
        
        texto_detalhado = f"""
        <p><b style='color: #FF9800;'>TIPO/CATEGORIA:</b> {dados['CATEGORIA']}</p>
        <p><b style='color: #4CAF50;'>SITUAÇÃO:</b> {dados['STATUS']}</p>
        <p><b style='color: #2196F3;'>NOME/RESOLUÇÃO:</b> {dados['RES']}</p>
        <p><b style='color: #2196F3;'>VALOR:</b> {dados['VAL_STR']}</p>
        <p><b style='color: #2196F3;'>PROTOCOLOS:</b> {dados['PROT']}</p>
        <hr color='#404040'>
        <p><b style='color: #2196F3;'>PROCESSO:</b> {dados['PROC']}</p>
        <p><b style='color: #2196F3;'>CÓDIGO VERIFICADOR:</b> <span style='font-size: 18px; color: #FF9800;'>{dados['COD']}</span></p>
        <hr color='#404040'>
        <p><b style='color: #FF9800;'>DESCRIÇÃO DO OBJETO:</b></p>
        <p style='line-height: 1.5;'>{dados['OBJETO']}</p>
        """
        self.info.setHtml(texto_detalhado)
        layout.addWidget(self.info)

        btn_fechar = QPushButton("FECHAR")
        btn_fechar.setStyleSheet("background-color: #444; color: white; padding: 12px; border-radius: 5px;")
        btn_fechar.clicked.connect(self.accept)
        layout.addWidget(btn_fechar)

class DashboardSESA(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SESA - Executive Management System")
        self.resize(1550, 900)
        self.setStyleSheet("QMainWindow { background-color: #1a1a1a; }")

        self.todos_dados = []
        self.dados_filtrados_atualmente = []
        self.carregar_dados()
        self.init_ui()

        # Configuração do Timer de Inatividade (3 minutos)
        self.timer_inatividade = QTimer()
        self.timer_inatividade.setInterval(30000) 
        self.timer_inatividade.timeout.connect(self.iniciar_modo_automatico)
        self.timer_inatividade.start()

        self.timer_carrossel = QTimer()
        self.timer_carrossel.setInterval(10000) 
        self.timer_carrossel.timeout.connect(self.proxima_categoria_automatico)
        
        self.modo_auto_ativo = False
        self.installEventFilter(self)
        self.filtrar()

    def eventFilter(self, obj, event):
        if event.type() in [event.MouseMove, event.KeyPress, event.MouseButtonPress]:
            self.timer_inatividade.start()
            if self.modo_auto_ativo:
                self.parar_modo_automatico()
        return super().eventFilter(obj, event)

    def iniciar_modo_automatico(self):
        self.lista_categorias_giro = list(set(d['CATEGORIA'] for d in self.todos_dados if d['CATEGORIA']))
        if self.lista_categorias_giro:
            self.modo_auto_ativo = True
            self.indice_atual_giro = 0
            self.timer_carrossel.start()
            self.f_res.setStyleSheet("background-color: #0d47a1; color: white; border: 2px solid #2196F3;")
            self.proxima_categoria_automatico()

    def parar_modo_automatico(self):
        self.modo_auto_ativo = False
        self.timer_carrossel.stop()
        self.f_res.setStyleSheet("")
        self.f_res.clear()
        self.f_res.setPlaceholderText("📂 BUSCAR NOME OU CATEGORIA...")
        self.filtrar()

    def proxima_categoria_automatico(self):
        if not self.lista_categorias_giro: return
        cat = self.lista_categorias_giro[self.indice_atual_giro]
        self.f_res.setText(cat)
        self.indice_atual_giro = (self.indice_atual_giro + 1) % len(self.lista_categorias_giro)

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
                idx_cab = next(i for i, l in enumerate(reader) if any("PROTOCOLOS" in str(c).upper() for c in l))
                cab = [str(c).strip().upper() for c in reader[idx_cab]]
                def get_idx(termos):
                    for i, col in enumerate(cab):
                        if any(t in col for t in termos): return i
                    return -1
                indices = {"prot": get_idx(["PROTOCOLOS"]), "res": get_idx(["RESOLUÇÃO"]), "status": get_idx(["STATUS RESUMIDOS"]), 
                           "valor": get_idx(["VALOR"]), "objeto": get_idx(["OBJETO"]), "proc": get_idx(["PROCESSO"]), 
                           "cod": get_idx(["CÓD VERIFICADOR"]), "cat": get_idx(["CATEGORIA"])}
                
                self.todos_dados = []
                for linha in reader[idx_cab + 1:]:
                    if len(linha) > indices["prot"] and linha[indices["prot"]].strip():
                        v_txt = linha[indices["valor"]].strip()
                        v_limpo = v_txt.replace('R$', '').replace('.', '').replace(',', '.').replace('"', '').strip()
                        try: v_num = float(v_limpo) if v_limpo else 0.0
                        except: v_num = 0.0
                        self.todos_dados.append({
                            "RES": linha[indices["res"]], "RES_L": self.remover_acentos(linha[indices["res"]]),
                            "PROT": linha[indices["prot"]], "STATUS": linha[indices["status"]],
                            "OBJETO": linha[indices["objeto"]], "OBJ_L": self.remover_acentos(linha[indices["objeto"]]),
                            "PROC": linha[indices["proc"]], "COD": linha[indices["cod"]],
                            "CATEGORIA": linha[indices["cat"]] if indices["cat"] != -1 else "OUTROS",
                            "CAT_L": self.remover_acentos(linha[indices["cat"]] if indices["cat"] != -1 else ""),
                            "VAL_STR": v_txt, "VAL_NUM": v_num
                        })
        except: pass

    def init_ui(self):
        central = QWidget(); self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        top_bar = QHBoxLayout()
        self.f_res = QLineEdit(); self.f_res.setPlaceholderText("📂 BUSCAR NOME OU CATEGORIA...")
        self.f_obj = QLineEdit(); self.f_obj.setPlaceholderText("🔍 BUSCAR NO OBJETO...")
        self.btn_limpar = QPushButton("🧹 LIMPAR"); self.btn_limpar.clicked.connect(self.limpar_filtros)
        self.btn_limpar.setStyleSheet("background-color: #f44336; color: white; font-weight: bold; padding: 12px; border-radius: 5px;")
        self.btn_exportar = QPushButton("📥 EXPORTAR"); self.btn_exportar.clicked.connect(self.exportar_csv)
        self.btn_exportar.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 12px; border-radius: 5px;")
        
        top_bar.addWidget(self.f_res, 3); top_bar.addWidget(self.f_obj, 3); top_bar.addWidget(self.btn_limpar, 1); top_bar.addWidget(self.btn_exportar, 1)
        layout.addLayout(top_bar)
        
        self.grid_cards = QGridLayout(); layout.addLayout(self.grid_cards)

        self.tabela = QTableWidget(); self.tabela.setColumnCount(8)
        self.tabela.setHorizontalHeaderLabels(['SITUAÇÃO', 'CATEGORIA', 'NOME / RESOLUÇÃO', 'OBJETO', 'VALOR', 'PROTOCOLOS', 'PROCESSO', 'CÓD. VERIF.'])
        self.tabela.setEditTriggers(QTableWidget.NoEditTriggers); self.tabela.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabela.verticalHeader().setVisible(False); self.tabela.cellDoubleClicked.connect(self.abrir_detalhes)
        self.tabela.setStyleSheet("QTableWidget { background-color: #262626; color: white; font-weight: bold; } QHeaderView::section { background-color: #333; color: white; padding: 10px; }")

        # Ajuste de largura das colunas
        header = self.tabela.horizontalHeader()
        self.tabela.setColumnWidth(0, 190)
        self.tabela.setColumnWidth(1, 190)
        self.tabela.setColumnWidth(2, 210)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        layout.addWidget(self.tabela)

        self.f_res.textChanged.connect(self.filtrar)
        self.f_obj.textChanged.connect(self.filtrar)

    def limpar_filtros(self):
        self.f_res.clear(); self.f_obj.clear(); self.filtrar()

    def exportar_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Salvar como CSV", "", "CSV (*.csv)")
        if path:
            try:
                with open(path, 'w', encoding='utf-8-sig', newline='') as f:
                    writer = csv.writer(f, delimiter=';')
                    writer.writerow(['SITUAÇÃO', 'CATEGORIA', 'NOME', 'OBJETO', 'VALOR', 'PROTOCOLOS', 'PROCESSO', 'CÓDIGO'])
                    for d in self.dados_filtrados_atualmente: 
                        writer.writerow([d['STATUS'], d['CATEGORIA'], d['RES'], d['OBJETO'], d['VAL_STR'], d['PROT'], d['PROC'], d['COD']])
            except: pass

    def abrir_detalhes(self, row, col):
        if row < len(self.dados_filtrados_atualmente):
            dialog = DetalhesDialog(self.dados_filtrados_atualmente[row], self); dialog.exec_()

    def filtrar(self):
        r_t = self.remover_acentos(self.f_res.text())
        o_t = self.remover_acentos(self.f_obj.text())
        self.dados_filtrados_atualmente = [d for d in self.todos_dados if (r_t in d['RES_L'] or r_t in d['CAT_L']) and o_t in d['OBJ_L']]
        
        self.tabela.setRowCount(len(self.dados_filtrados_atualmente))
        for i, d in enumerate(self.dados_filtrados_atualmente):
            st = d['STATUS'].upper()
            if "CRÍ" in st:
                icon, cor = "[ ! ] CRÍTICO", "#ff5252"
            elif any(x in st for x in ["OK", "CONCLU", "PAGA"]):
                icon, cor = "[ v ] CONCLUÍDO", "#69f0ae"
            else:
                icon, cor = "[ > ] EM ANDAMENTO", "#ffd740"
            
            celulas = [icon, d['CATEGORIA'], d['RES'], d['OBJETO'], d['VAL_STR'], d['PROT'], d['PROC'], d['COD']]
            for j, texto in enumerate(celulas):
                item = QTableWidgetItem(str(texto))
                item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
                if j == 0: item.setForeground(QColor(cor)) 
                self.tabela.setItem(i, j, item)
        self.atualizar_cards()

    def atualizar_cards(self):
        for i in reversed(range(self.grid_cards.count())): 
            self.grid_cards.itemAt(i).widget().setParent(None)
        
        v_total = sum(d['VAL_NUM'] for d in self.dados_filtrados_atualmente)
        vf = f"R$ {v_total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        
        total_protocolos = 0
        nomes_unicos = set()
        for d in self.dados_filtrados_atualmente:
            nomes_unicos.add(d['RES'])
            prot_texto = str(d.get('PROT', '')).strip()
            if prot_texto and prot_texto.upper() != "N/A":
                # Conta protocolos separados por vírgula ou ponto e vírgula
                lista_p = [p for p in prot_texto.replace(';', ',').split(',') if p.strip()]
                total_protocolos += len(lista_p)
        
        txt_itens = f"{len(nomes_unicos)} ({total_protocolos} Prot.)"
        
        self.grid_cards.addWidget(self.criar_card("INVESTIMENTO TOTAL", vf, "#4CAF50"), 0, 0)
        self.grid_cards.addWidget(self.criar_card("RES. ÚNICAS (TOTAL PROTOCOLOS)", txt_itens, "#2196F3"), 0, 1)

    def criar_card(self, t, v, c):
        card = QFrame()
        card.setStyleSheet(f"background: #262626; border-radius: 10px; border-bottom: 4px solid {c}; padding: 10px;")
        l = QVBoxLayout(card)
        lbl_t = QLabel(t)
        lbl_t.setStyleSheet("color: #ffffff; font-size: 11px; font-weight: bold; border: none;") 
        l.addWidget(lbl_t)
        val = QLabel(v)
        val.setStyleSheet(f"color: {c}; font-size: 24px; font-weight: bold; border: none;")
        l.addWidget(val)
        return card

if __name__ == "__main__":
    app = QApplication(sys.argv); window = DashboardSESA(); window.show(); sys.exit(app.exec_())