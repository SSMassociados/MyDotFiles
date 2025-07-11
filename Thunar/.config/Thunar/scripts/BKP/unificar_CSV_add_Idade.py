#!/usr/bin/env python3

import os
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta

# Lista todos os arquivos no diretório atual com extensão .csv
arquivos_csv = [arquivo for arquivo in os.listdir() if arquivo.endswith('.csv')]

# Inicializa um DataFrame vazio
dados_unificados = pd.DataFrame()

# Itera sobre cada arquivo CSV e os concatena no DataFrame unificado
for arquivo in arquivos_csv:
    dados = pd.read_csv(arquivo)
    dados_unificados = pd.concat([dados_unificados, dados])

# Obtém a data atual
data_atual = datetime.now()

# Calcula a idade para cada linha
dados_unificados['IDADE'] = pd.to_datetime(dados_unificados.iloc[:, 2]).apply(lambda x: relativedelta(data_atual, x))

# Formatando a idade no formato desejado
dados_unificados['IDADE'] = dados_unificados['IDADE'].apply(lambda x: f"{x.years} Anos, {x.months} Meses e {x.days} Dias")

# Renomeando a coluna 'Idade' para 'IDADE'
dados_unificados = dados_unificados.rename(columns={'Idade': 'IDADE'})

# Salvando os dados unificados em um único arquivo CSV
dados_unificados.to_csv('dados_unificados.csv', index=False)
