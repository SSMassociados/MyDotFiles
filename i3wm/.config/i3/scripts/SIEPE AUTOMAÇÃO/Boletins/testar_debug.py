#!/usr/bin/env python3
"""
Teste rápido do siepe_debug.py
Execute na pasta Boletins/ ou Fichas Individuais/ com:
    python3 testar_debug.py
"""
import sys, os

# ── 1. Testa importação ───────────────────────────────────────
print("1️⃣  Testando importação do siepe_debug...")
try:
    from siepe_debug import diagnosticar
    print("    ✅ siepe_debug importado com sucesso!\n")
except ImportError as e:
    print(f"    ❌ Falha na importação: {e}")
    print("    👉 Certifique-se de executar este script NA MESMA PASTA que o siepe_debug.py")
    print(f"    👉 Pasta atual: {os.getcwd()}")
    print(f"    👉 Arquivos aqui: {os.listdir('.')}")
    sys.exit(1)

# ── 2. Abre Firefox e testa o diagnóstico numa página real ────
print("2️⃣  Abrindo Firefox para teste de diagnóstico...")
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By

options = Options()
options.add_argument("--start-maximized")
driver = webdriver.Firefox(service=Service(), options=options)

try:
    # Usa uma página pública simples com formulário e paginação
    print("    🌐 Carregando página de teste (python.org)...")
    driver.get("https://www.python.org")
    import time; time.sleep(2)

    print("\n3️⃣  Executando diagnóstico na página...")
    diagnosticar(driver, "teste_pagina_inicial", salvar_html=True)

    # ── 3. Verifica arquivos gerados ──────────────────────────
    print("4️⃣  Verificando arquivos gerados...")
    arquivos = [f for f in os.listdir('.') if f.startswith('debug_')]
    if arquivos:
        print(f"    ✅ {len(arquivos)} arquivo(s) gerado(s):")
        for arq in sorted(arquivos):
            tamanho = os.path.getsize(arq)
            print(f"       📄 {arq}  ({tamanho:,} bytes)")
    else:
        print("    ⚠️  Nenhum arquivo debug_ encontrado.")

    print("\n5️⃣  Testando diagnóstico dentro de iframe...")
    driver.get("https://www.siepe.educacao.pe.gov.br")
    time.sleep(3)
    diagnosticar(driver, "teste_siepe_login", salvar_html=False)

    print("\n" + "═"*50)
    print("🏆 TESTE CONCLUÍDO COM SUCESSO!")
    print("   O siepe_debug.py está funcionando corretamente.")
    print("   Arquivos gerados nesta pasta:")
    for arq in sorted(f for f in os.listdir('.') if f.startswith('debug_')):
        print(f"   📄 {arq}")
    print("═"*50)

except Exception as e:
    print(f"\n❌ Erro durante teste: {e}")
    import traceback; traceback.print_exc()

finally:
    input("\nPressione ENTER para fechar o navegador...")
    driver.quit()
