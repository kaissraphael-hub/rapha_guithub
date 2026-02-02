import os
import requests
import sys
import io
import warnings
import fitz  # PyMuPDF
from bs4 import BeautifulSoup
from tqdm import tqdm
from datetime import datetime
from inputimeout import inputimeout, TimeoutOccurred

# Configurações de sistema
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
warnings.filterwarnings("ignore")

# ================= CONFIGURAÇÃO AUTOMÁTICA =================
LISTA_VIP_PADRAO = ["RAPHAEL KAISS", "194789", "AMANDA WALTER PIRES", "195423"]
ANO_PADRAO = "2026"
# ===========================================================

def destacar_e_extrair(caminho_entrada, caminho_saida, termos):
    try:
        doc = fitz.open(caminho_entrada)
        achou = False
        detalhes = []
        for pagina in doc:
            texto_pag = pagina.get_text()
            for termo in termos:
                instancias = pagina.search_for(termo)
                if instancias:
                    achou = True
                    pos = texto_pag.lower().find(termo.lower())
                    trecho = texto_pag[max(0, pos-40):min(len(texto_pag), pos+80)].replace('\n', ' ')
                    detalhes.append(f"   - Termo: {termo.upper()} | Pág: {pagina.number + 1}")
                    detalhes.append(f"     Contexto: ...{trecho}...")
                    for inst in instancias:
                        annot = pagina.add_highlight_annot(inst)
                        annot.set_colors(stroke=(0, 1, 1)) # Ciano
                        annot.update()
        if achou:
            doc.save(caminho_saida)
            doc.close()
            return True, detalhes
        doc.close()
        return False, []
    except: return False, []

def iniciar_sistema():
    print("\n=== 🎯 MONITOR BOLETIM OFICIAL DE GUARAPUAVA: SISTEMA HÍBRIDO ===")
    print(f"Padrão Agendado: {LISTA_VIP_PADRAO}")
    
    try:
        # Tenta receber o input por 20 segundos
        entrada = inputimeout(prompt="⌨️ Digite novos termos (ou aguarde 10s para LISTA VIP): ", timeout=10)
        termos_finais = [t.strip().lower() for t in entrada.split(",")]
        print(f"🔎 Iniciando busca MANUAL por: {termos_finais}")
    except TimeoutOccurred:
        # Se o tempo acabar, usa a lista VIP
        termos_finais = [t.lower() for t in LISTA_VIP_PADRAO]
        print(f"\n⏰ Tempo esgotado! Iniciando busca AUTOMÁTICA (Lista VIP)...")

    rodar_processo(termos_finais)

def rodar_processo(termos_busca):
    data_hoje = datetime.now().strftime("%d-%m-%Y_%H-%M")
    url = f"https://guarapuava.pr.gov.br/boletins-oficiais/{ANO_PADRAO}-2/"
    pasta_base = os.path.expanduser(f"~/Documentos/python testes/BOLETINS_{ANO_PADRAO}")
    pasta_final = os.path.join(pasta_base, f"Resultados_{data_hoje}")
    
    for p in [pasta_base, pasta_final]:
        if not os.path.exists(p): os.makedirs(p)

    caminho_relatorio = os.path.join(pasta_final, "RESUMO_DIARIO.txt")
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        res_site = requests.get(url, headers=headers, timeout=20)
        soup = BeautifulSoup(res_site.text, 'html.parser')
        links_pdf = []
        for a in soup.find_all('a', href=True):
            if a['href'].lower().endswith('.pdf'):
                if a['href'] not in [l['url'] for l in links_pdf]:
                    links_pdf.append({'url': a['href'], 'nome': a.text.strip() or a['href'].split('/')[-1]})
        
        encontrados_total = 0
        with open(caminho_relatorio, "w", encoding="utf-8") as rel:
            rel.write(f"📋 RELATÓRIO - {data_hoje}\n")
            rel.write(f"🔎 BUSCA POR: {termos_busca}\n")
            rel.write("="*60 + "\n\n")

            for item in tqdm(links_pdf, desc="Analisando"):
                nome_limpo = "".join([c for c in item['nome'] if c.isalnum() or c in (' ', '-', '_')]).replace(" ", "_")
                if not nome_limpo.lower().endswith('.pdf'): nome_limpo += ".pdf"
                
                caminho_orig = os.path.join(pasta_base, nome_limpo)
                caminho_res = os.path.join(pasta_final, "ALERTA_" + nome_limpo)

                if not os.path.exists(caminho_orig):
                    try:
                        data = requests.get(item['url'], headers=headers, timeout=15).content
                        with open(caminho_orig, 'wb') as f: f.write(data)
                    except: continue

                achou, trechos = destacar_e_extrair(caminho_orig, caminho_res, termos_busca)
                if achou:
                    encontrados_total += 1
                    rel.write(f"📄 ARQUIVO: {item['nome']}\n")
                    for linha in trechos: rel.write(linha + "\n")
                    rel.write("-" * 50 + "\n")

        print(f"\n✅ CONCLUÍDO! {encontrados_total} ocorrências encontradas.")
        print(f"📁 Pasta: {pasta_final}")

    except Exception as e: print(f"❌ Erro: {e}")

if __name__ == "__main__":
    iniciar_sistema()