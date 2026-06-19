#!/usr/bin/env python3

# Dependências: Python, Pandas e XlsxWriter
import os
import sys
import pandas as pd

def converter_csv_para_xlsx(arquivos_csv):
    # Criar um subdiretório para salvar os arquivos .xlsx
    subdiretorio_saida = 'XLSX_Output'
    os.makedirs(subdiretorio_saida, exist_ok=True)

    for arquivo_csv in arquivos_csv:
        # Verifica se o arquivo fornecido é um arquivo .csv
        if not arquivo_csv.endswith('.csv'):
            print(f'O arquivo "{arquivo_csv}" não é um arquivo CSV. Ignorando...')
            continue
        
        # Lê o arquivo .csv
        try:
            df = pd.read_csv(arquivo_csv)
        except Exception as e:
            print(f'Erro ao ler o arquivo "{arquivo_csv}": {e}')
            continue

        # Nome do arquivo .xlsx
        nome_arquivo_xlsx = os.path.splitext(os.path.basename(arquivo_csv))[0] + '.xlsx'

        # Caminho completo para salvar o arquivo .xlsx
        caminho_arquivo_xlsx = os.path.join(subdiretorio_saida, nome_arquivo_xlsx)

        # Salva o DataFrame como um arquivo .xlsx
        try:
            with pd.ExcelWriter(caminho_arquivo_xlsx, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False)

                # Força o ajuste automático das larguras das colunas
                worksheet = writer.sheets['Sheet1']
                for i, col in enumerate(df.columns):
                    column_len = max(df[col].astype(str).map(len).max(), len(col) + 2)
                    worksheet.set_column(i, i, column_len)

            print(f'Arquivo "{nome_arquivo_xlsx}" convertido com sucesso.')

            # Notificação visual e sonora
            os.system(f'notify-send -u normal -t 3000 "Conversão do arquivo {arquivo_csv} concluída!"')
            os.system('paplay /usr/share/sounds/freedesktop/stereo/complete.oga')
        except Exception as e:
            print(f'Erro ao salvar o arquivo "{nome_arquivo_xlsx}": {e}')
            continue

if __name__ == "__main__":
    # Argumentos da linha de comando: arquivos .csv
    if len(sys.argv) < 2:
        print("Por favor, forneça pelo menos um arquivo CSV.")
        sys.exit(1)

    arquivos_csv = sys.argv[1:]

    converter_csv_para_xlsx(arquivos_csv)
