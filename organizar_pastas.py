import os
import shutil
import sys
import io
import select
import time

# Força o terminal a aceitar UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def organizar_pasta():
    caminho_padrao = "/home/rapha/Downloads"
    tempo_espera = 10 

    # O flush=True garante que o texto apareça ANTES do cronômetro começar
    print(f"\n📂 --- ORGANIZADOR AUTOMÁTICO ---", flush=True)
    print(f"Padrão: {caminho_padrao}", flush=True)
    print(f"Digite um caminho ou aguarde {tempo_espera}s para o padrão: ", end="", flush=True)

    # Verifica se há entrada no teclado (stdin)
    # No Linux, o select precisa que o sys.stdin esteja pronto
    pronto, _, _ = select.select([sys.stdin], [], [], tempo_espera)

    if pronto:
        caminho = sys.stdin.readline().strip()
        if not caminho:
            caminho = caminho_padrao
    else:
        print(f"\n\n⏰ Tempo esgotado! Organizando pasta padrão...")
        caminio = caminho_padrao # Corrigindo erro de digitação
        caminho = caminho_padrao

    # --- Seus formatos originais ---
    formatos = {
        "Vídeos": [".mp4", ".mkv", ".avi", ".mov"],
        "Imagens": [".jpg", ".jpeg", ".png", ".gif", ".svg"],
        "Documentos textos": [ ".docx", ".txt", ".xlsx", ".pptx"],
        "Musicas": [".mp3", ".wav", ".flac"],
        "Compactados": [".zip", ".rar", ".7z", ".tar"],
        "Python": [".py", ".pyc"],
        "PDFs": [".pdf"],
    }

    try:
        os.chdir(caminho)
    except Exception as e:
        print(f"❌ Erro ao acessar: {caminho}")
        return

    ficheiros = [f for f in os.listdir() if os.path.isfile(f) and f != "organizar_pastas.py"]

    if not ficheiros:
        print("✅ Pasta já está organizada.")
        return

    for ficheiro in ficheiros:
        _, extensao = os.path.splitext(ficheiro)
        extensao = extensao.lower()

        movido = False
        for pasta, extensoes in formatos.items():
            if extensao in extensoes:
                if not os.path.exists(pasta): os.makedirs(pasta)
                try:
                    print(f"🚚 Movendo: {ficheiro} -> {pasta}/")
                    shutil.move(ficheiro, os.path.join(pasta, ficheiro))
                except: pass
                movido = True
                break
        
        if not movido:
            if not os.path.exists("Outros"): os.makedirs("Outros")
            try: shutil.move(ficheiro, os.path.join("Outros", ficheiro))
            except: pass

    print("\n✨ Concluído!")

if __name__ == "__main__":
    organizar_pasta()