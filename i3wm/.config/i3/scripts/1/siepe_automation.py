#!/usr/bin/env python3

from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# Configurações do Navegador
options = Options()
options.add_argument("--start-maximized")

# Inicialização do Driver
service = Service()
driver = webdriver.Firefox(service=service, options=options)
wait = WebDriverWait(driver, 25)

try:
    # Acesso ao Portal
    driver.get("https://www.siepe.educacao.pe.gov.br")
    print("🔑 Faça o login manualmente no navegador e pressione ENTER aqui no terminal...")
    input()

    print("⏳ Iniciando automação...")

    # 1. Acesso Restrito
    print("1️⃣ ACESSO RESTRITO...")
    acesso = wait.until(EC.element_to_be_clickable((
        By.XPATH, "//*[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'acesso restrito')]"
    )))
    driver.execute_script("arguments[0].click();", acesso)
    time.sleep(4)

    # 2. Gestão de Rede de Ensino
    print("2️⃣ GESTÃO DE REDE DE ENSINO...")
    gestao = wait.until(EC.element_to_be_clickable((
        By.XPATH, "//*[contains(text(), 'Gestão de Rede de Ensino')]"
    )))
    driver.execute_script("arguments[0].click();", gestao)
    time.sleep(5)

    # 3. Módulo Aluno
    print("3️⃣ MÓDULO ALUNO...")
    aluno = wait.until(EC.element_to_be_clickable((
        By.XPATH, "//div[contains(@class, 'icon-eol1331')] | //a[contains(@href, 'selecionarModulo(1331)')]"
    )))
    driver.execute_script("arguments[0].click();", aluno)
    time.sleep(6)

    # 4. Menu Lateral: Alunos
    print("4️⃣ Abrindo menu 'Alunos'...")
    # Seletor robusto para encontrar o item "Alunos" no menu lateral
    alunos_menu = wait.until(EC.element_to_be_clickable((
        By.XPATH, "//div[contains(@id, 'divMenuGestao')]//div[text()='Alunos']"
    )))
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", alunos_menu)
    time.sleep(1)
    driver.execute_script("arguments[0].click();", alunos_menu)
    print("✅ Menu 'Alunos' expandido!")

    # 5. Clique em Documentos (O passo que você solicitou)
    print("5️⃣ Clicando em 'Documentos'...")
    # Buscamos o div com texto "Documentos" que está dentro de um li do menu de gestão
    documentos = wait.until(EC.element_to_be_clickable((
        By.XPATH, "//li[contains(@id, 'divMenuGestao')]//div[text()='Documentos']"
    )))
    
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", documentos)
    time.sleep(1) # Pequena pausa para garantir a animação do menu
    driver.execute_script("arguments[0].click();", documentos)
    print("✅ Submenu 'Documentos' acessado com sucesso!")

    # --- PRÓXIMOS PASSOS ---
    # Se você precisar clicar em algo dentro de Documentos, como "Boletim escolar":
    # print("6️⃣ Clicando em Boletim Escolar...")
    # boletim = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[text()='Boletim escolar']")))
    # driver.execute_script("arguments[0].click();", boletim)

    print("\n🎉 Automação concluída até o nível de 'Documentos'!")
    input("\nPressione ENTER para fechar o navegador...")

except Exception as e:
    print(f"\n❌ Ocorreu um erro: {e}")
    input("\nPressione ENTER para encerrar...")

finally:
    driver.quit()
