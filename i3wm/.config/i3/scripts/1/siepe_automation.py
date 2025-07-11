from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

service = Service("/sbin/geckodriver")
options = Options()

driver = webdriver.Firefox(service=service, options=options)
driver.maximize_window()

# Passo 1: abre página principal para login
driver.get("https://www.siepe.educacao.pe.gov.br")

input("🕒 Faça login manualmente no navegador e pressione ENTER aqui...")

# Passo 2: após login, abre a URL direta da ficha
url_ficha = "https://www.siepe.educacao.pe.gov.br/gestaoescolar.do"
driver.get(url_ficha)

# Aguarda o carregamento da página da ficha
try:
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    print("✅ Página da ficha carregada com sucesso.")
except:
    print("❌ Falha ao carregar página da ficha.")

# Passo 3: Clica no menu "Aluno"
try:
    aluno_element = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/form/div/div/div[2]/div[7]/div[1]/a[2]/div"))
    )
    aluno_element.click()
    print("✅ Clicou no menu ALUNO com sucesso!")
except Exception as e:
    print(f"❌ Erro ao clicar no menu ALUNO: {e}")

# Passo 4: Clica no próximo elemento (XPath fornecido)
try:
    prox_element = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/form/div/div/div[3]/div[1]/div/div[1]/div[1]"))
    )
    prox_element.click()
    print("✅ Clicou no próximo elemento com sucesso!")
except Exception as e:
    print(f"❌ Erro ao clicar no próximo elemento: {e}")

# Passo 5: Detecta e troca para iframe se existir
iframes = driver.find_elements(By.TAG_NAME, "iframe")
print(f"Há {len(iframes)} iframes na página.")
for i, iframe in enumerate(iframes):
    print(f"Iframe[{i}]: id='{iframe.get_attribute('id')}', name='{iframe.get_attribute('name')}'")

if iframes:
    driver.switch_to.frame(iframes[0])
    print("🟢 Entrou no iframe")

# Passo 6: Clica no menu Gestão pelo texto (mais confiável que id dinâmico)
try:
    menu_gestao = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), 'Gestão')]"))
    )
    menu_gestao.click()
    print("✅ Clicou no menu Gestão com sucesso!")
except Exception as e:
    print(f"❌ Erro ao clicar no menu Gestão: {e}")

# Volta para o DOM principal (caso tenha trocado o iframe)
driver.switch_to.default_content()

# Mantém aberto para você ver o resultado
input("Pressione ENTER para finalizar o script...")

driver.quit()
