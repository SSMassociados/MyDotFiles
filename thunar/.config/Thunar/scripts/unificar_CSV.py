#!/usr/bin/env python3

import os
import sys
import pandas as pd

# Verifica se foram passados os nomes dos arquivos CSV como argumentos
if len(sys.argv) < 3:
    print("Por favor, forneça os nomes dos arquivos CSV como argumentos.")
    print("Exemplo: nome_do_script.py arquivoX.csv arquivoY.csv")
    sys.exit(1)

# Extrai os nomes dos arquivos CSV dos argumentos de linha de comando
arquivos_csv = sys.argv[1:]

# Inicializa um DataFrame vazio
dados_unificados = pd.DataFrame()

# Itera sobre cada arquivo CSV e os concatena no DataFrame unificado
for arquivo in arquivos_csv:
    # Verifica se o arquivo existe
    if not os.path.isfile(arquivo):
        print(f"O arquivo '{arquivo}' não foi encontrado.")
        continue
    # Lê os dados do arquivo CSV e os concatena no DataFrame unificado
    dados = pd.read_csv(arquivo)
    dados_unificados = pd.concat([dados_unificados, dados])

# Salva os dados unificados em um único arquivo CSV
dados_unificados.to_csv('dados_unificados.csv', index=False)

# Notificação sonora
os.system('paplay /usr/share/sounds/freedesktop/stereo/complete.oga')

# Notificação visual
os.system('notify-send "Unificação concluída" "Os dados foram unificados no arquivo \'dados_unificados.csv\'."')

print("Processo concluído. Os dados foram unificados no arquivo 'dados_unificados.csv'.")
