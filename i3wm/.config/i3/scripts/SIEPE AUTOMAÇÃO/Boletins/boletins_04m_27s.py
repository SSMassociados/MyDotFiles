#!/usr/bin/env python3
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
import math, time, re
from siepe_debug import diagnosticar

# ═════════════════════════════════════════════════════════════
# CONFIGURAÇÃO
# ═════════════════════════════════════════════════════════════
CURSO      = "EM35"
SERIES     = ["1ANO", "2ANO", "3ANO"]
ALUNOS_PAG = 20

# ═════════════════════════════════════════════════════════════
# XPaths — confirmados via Automa
# ═════════════════════════════════════════════════════════════
XPATH_MENU_ALUNOS     = "//*[self::a or self::td or self::li or self::div or self::span][normalize-space(.)='Alunos']"
XPATH_MENU_DOCUMENTOS = "//*[self::a or self::td or self::li or self::div or self::span][normalize-space(.)='Documentos']"
XPATH_MENU_BOLETIM    = "//*[@id='divMenuGestao_1781088678121_i2002'] | //*[self::a or self::td or self::li or self::div or self::span][normalize-space(.)='Boletim escolar']"

XPATH_CURSO        = "//div[@id='divCorpoGestaoEscolar']/FORM[1]/TABLE[1]/TBODY[1]/TR[1]/TD[1]/DIV[2]/DIV[4]/DIV[1]/TABLE[1]/TBODY[1]/TR[5]/TD[2]/SELECT[1]"
XPATH_SERIE        = "//div[@id='divCorpoGestaoEscolar']/FORM[1]/TABLE[1]/TBODY[1]/TR[1]/TD[1]/DIV[2]/DIV[4]/DIV[1]/TABLE[1]/TBODY[1]/TR[6]/TD[2]/SELECT[1]"
XPATH_TURMA        = "//div[@id='divCorpoGestaoEscolar']/FORM[1]/TABLE[1]/TBODY[1]/TR[1]/TD[1]/DIV[2]/DIV[4]/DIV[1]/TABLE[1]/TBODY[1]/TR[7]/TD[2]/SELECT[1]"
XPATH_PESQUISAR    = "//*[@id='lnk_pesquisar']"
XPATH_MARCAR_TODOS = "//*[@id='chkMarcarTodos']"
XPATH_SELECIONAR   = "//*[@id='lnk_emitirBoletim']"

UL_PAGINACAO = (
    "//div[@id='divCorpoGestaoEscolar']"
    "/FORM[1]/TABLE[1]/TBODY[1]/TR[1]/TD[1]"
    "/DIV[3]/DIV[4]/DIV[1]/TABLE[1]/TBODY[1]/TR[22]/TD[1]/UL[1]"
)
def xpath_pagina(n):
    return UL_PAGINACAO + f"/LI[{n + 2}]/A[1]"

# ═════════════════════════════════════════════════════════════
# Helpers — mesmos do script funcional, com StaleElement tratado
# ═════════════════════════════════════════════════════════════
def entrar_iframe_com_elemento(driver, xpath, descricao):
    driver.switch_to.default_content()
    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    for i, frame in enumerate(iframes):
        try:
            driver.switch_to.frame(frame)
            els = driver.find_elements(By.XPATH, xpath)
            if els:
                print(f"    ✅ '{descricao}' encontrado no iframe #{i}.")
                return els[0]
        except Exception:
            pass
        driver.switch_to.default_content()
    driver.switch_to.default_content()
    els = driver.find_elements(By.XPATH, xpath)
    if els:
        print(f"    ✅ '{descricao}' encontrado no conteúdo principal.")
        return els[0]
    raise RuntimeError(f"'{descricao}' não encontrado.\nXPath: {xpath}")

def clicar(driver, wait, xpath, descricao, scroll=True):
    try:
        el = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
        if scroll:
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
            time.sleep(0.4)
        driver.execute_script("arguments[0].click();", el)
        print(f"    ✅ '{descricao}' clicado.")
        return el
    except TimeoutException:
        diagnosticar(driver, descricao.replace(' ','_'))
        raise RuntimeError(f"Timeout: '{descricao}'\nXPath: {xpath}")

def clicar_em_iframe(driver, xpath, descricao, pausa=1.5):
    el = entrar_iframe_com_elemento(driver, xpath, descricao)
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
    time.sleep(0.4)
    driver.execute_script("arguments[0].click();", el)
    print(f"    ✅ '{descricao}' clicado (iframe).")
    time.sleep(pausa)

def selecionar_select(driver, xpath, valor, descricao, pausa=2.0, por_texto=False):
    deadline = time.time() + 20
    while time.time() < deadline:
        els = driver.find_elements(By.XPATH, xpath)
        if els:
            try:
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", els[0])
                time.sleep(0.3)
                sel = Select(els[0])
                if por_texto:
                    sel.select_by_visible_text(valor)
                else:
                    try:
                        sel.select_by_value(valor)
                    except Exception:
                        sel.select_by_visible_text(valor)
                print(f"    ✅ '{descricao}' = {valor}")
                time.sleep(pausa)
                return
            except StaleElementReferenceException:
                time.sleep(0.3)
                continue
            except Exception:
                pass
        time.sleep(0.5)
    diagnosticar(driver, descricao.replace(' ','_'))
    raise RuntimeError(f"Não foi possível selecionar '{descricao}' = {valor}")

def clicar_direto(driver, xpath, descricao, pausa=2.0, scroll=True):
    deadline = time.time() + 20
    while time.time() < deadline:
        els = driver.find_elements(By.XPATH, xpath)
        if els:
            try:
                if scroll:
                    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", els[0])
                    time.sleep(0.4)
                driver.execute_script("arguments[0].click();", els[0])
                print(f"    ✅ '{descricao}' clicado.")
                time.sleep(pausa)
                return
            except StaleElementReferenceException:
                time.sleep(0.3)
                continue
        time.sleep(0.5)
    diagnosticar(driver, descricao.replace(' ','_'))
    raise RuntimeError(f"'{descricao}' não encontrado.\nXPath: {xpath}")

def elemento_existe(driver, xpath):
    return len(driver.find_elements(By.XPATH, xpath)) > 0

def ler_turmas_disponiveis(driver, xpath_select):
    deadline = time.time() + 20
    while time.time() < deadline:
        els = driver.find_elements(By.XPATH, xpath_select)
        if els:
            sel = Select(els[0])
            turmas = [
                o.text.strip() for o in sel.options
                if o.text.strip() not in ("", "-", " ", "--")
                and o.get_attribute("value") not in ("", "-", " ", "--")
            ]
            if turmas:
                return turmas
        time.sleep(0.5)
    diagnosticar(driver, "turmas_nao_carregaram")
    raise RuntimeError("Turmas não carregaram.\nScreenshot: erro_turmas_nao_carregaram.png")

# Regex robusto — melhoria mantida
def ler_total_e_paginas(driver):
    padrao = re.compile(r'Resultados\s+\d+\s+a\s+\d+\s+de\s+(\d+)', re.IGNORECASE)
    candidatos = driver.find_elements(By.XPATH,
        "//*[contains(normalize-space(text()),'Resultados') "
        "and contains(normalize-space(text()),' de ')]"
    )
    for el in candidatos:
        m = padrao.search(el.text.strip())
        if m:
            total = int(m.group(1))
            return total, math.ceil(total / ALUNOS_PAG)
    return None, 1

# ═════════════════════════════════════════════════════════════
# Processar turma
# ═════════════════════════════════════════════════════════════
def processar_turma(driver, turma):
    print(f"\n    {'·'*44}")
    print(f"    🎓 Turma: {turma}")

    selecionar_select(driver, XPATH_TURMA, turma, "Turma", pausa=1, por_texto=True)

    print(f"    🔍 Pesquisando alunos...")
    clicar_direto(driver, XPATH_PESQUISAR, "PESQUISAR", pausa=3)

    if not elemento_existe(driver, XPATH_MARCAR_TODOS):
        print(f"    ⚠️  Nenhum aluno encontrado. Pulando.")
        return

    total, num_paginas = ler_total_e_paginas(driver)
    if total is not None:
        print(f"    📊 {total} aluno(s) → {num_paginas} página(s)")
    else:
        print(f"    📊 Total não detectado → assumindo 1 página")
        num_paginas = 1

    for pag in range(1, num_paginas + 1):
        if pag > 1:
            print(f"    ➡️  Página {pag}/{num_paginas}...")
            clicar_direto(driver, xpath_pagina(pag), f"Pág {pag}", pausa=3)

        print(f"    📄 Pág {pag}/{num_paginas} — marcando todos...")
        clicar_direto(driver, XPATH_MARCAR_TODOS, f"Marcar Todos {pag}", pausa=1)
        time.sleep(1)

    print(f"    🏁 {num_paginas} pág(s). Clicando SELECIONAR...")
    clicar_direto(driver, XPATH_SELECIONAR, "SELECIONAR", pausa=4)
    print(f"    🎉 Turma {turma} concluída!")

# ═════════════════════════════════════════════════════════════
# Navegador
# ═════════════════════════════════════════════════════════════
options = Options()
options.add_argument("--start-maximized")
driver = webdriver.Firefox(service=Service(), options=options)
wait   = WebDriverWait(driver, 25)

try:
    driver.get("https://www.siepe.educacao.pe.gov.br")
    print("🔑 Faça o login manualmente e pressione ENTER...")
    input()
    _t_inicio = time.time()
    print("⏳ Iniciando automação — BOLETIM ESCOLAR...\n")

    print("1️⃣  ACESSO RESTRITO...")
    clicar(driver, wait,
        "//*[contains(text(),'Acesso Restrito') or contains(text(),'ACESSO RESTRITO')]",
        "Acesso Restrito")
    time.sleep(3)

    print("2️⃣  GESTÃO DE REDE DE ENSINO...")
    clicar(driver, wait,
        "//*[contains(text(),'Gestão de Rede de Ensino')]",
        "Gestão de Rede de Ensino")
    time.sleep(4)

    print("3️⃣  MÓDULO ALUNO...")
    try:
        clicar(driver, wait, "//div[contains(@class,'icon-eol1331')]", "Módulo Aluno (ícone)")
    except RuntimeError:
        clicar(driver, wait,
            "//a[contains(@href,'selecionarModulo(1331)') or contains(@onclick,'1331')]",
            "Módulo Aluno (href)")
    time.sleep(5)

    print("4️⃣  Abrindo menu 'Alunos'...")
    clicar_em_iframe(driver, XPATH_MENU_ALUNOS, "Menu Alunos", pausa=2)

    print("5️⃣  Clicando em 'Documentos'...")
    clicar_em_iframe(driver, XPATH_MENU_DOCUMENTOS, "Submenu Documentos", pausa=2)

    print("6️⃣  Clicando em 'Boletim escolar'...")
    clicar_em_iframe(driver, XPATH_MENU_BOLETIM, "Boletim escolar", pausa=3)

    print("    🔄 Entrando no iframe do formulário...")
    entrar_iframe_com_elemento(driver, XPATH_CURSO, "Select Curso")

    print(f"7️⃣  Selecionando Curso '{CURSO}'...")
    selecionar_select(driver, XPATH_CURSO, CURSO, "Curso", pausa=2)

    resumo = {}
    for idx_serie, serie in enumerate(SERIES, start=1):
        print(f"\n{'═'*50}")
        print(f"  📚 SÉRIE {idx_serie}/{len(SERIES)}: {serie}")
        print(f"{'═'*50}")

        selecionar_select(driver, XPATH_SERIE, serie, "Série", pausa=2)
        turmas = ler_turmas_disponiveis(driver, XPATH_TURMA)
        print(f"  📋 {len(turmas)} turma(s): {', '.join(turmas)}")
        resumo[serie] = turmas

        for idx_turma, turma in enumerate(turmas, start=1):
            print(f"\n  [{idx_turma}/{len(turmas)}]", end="")
            processar_turma(driver, turma)
            time.sleep(1)

        print(f"\n  ✅ Série {serie} — {len(turmas)} turma(s) concluída(s).")

    total_turmas = sum(len(t) for t in resumo.values())
    _elapsed = time.time() - _t_inicio
    _min, _seg = divmod(int(_elapsed), 60)
    print("\n" + "═"*50)
    print("🏆 BOLETIM ESCOLAR — AUTOMAÇÃO CONCLUÍDA!")
    print(f"   Curso : {CURSO}")
    for serie, turmas in resumo.items():
        print(f"   {serie}  : {', '.join(turmas)}")
    print(f"   Total : {total_turmas} turma(s) processada(s)")
    print(f"   ⏱️  Tempo : {_min}m {_seg:02d}s  ({_elapsed:.1f}s total)")
    print("═"*50)
    input("\nPressione ENTER para fechar o navegador...")

except RuntimeError as e:
    _elapsed = time.time() - _t_inicio if "_t_inicio" in dir() else 0
    _min, _seg = divmod(int(_elapsed), 60)
    print(f"\n❌ {e}")
    print(f"   ⏱️  Tempo até o erro: {_min}m {_seg:02d}s")
    diagnosticar(driver, "boletim")
    input("\nPressione ENTER para encerrar...")

except Exception as e:
    _elapsed = time.time() - _t_inicio if "_t_inicio" in dir() else 0
    _min, _seg = divmod(int(_elapsed), 60)
    diagnosticar(driver, "boletim")
    print(f"\n❌ Erro inesperado: {e}")
    print(f"   ⏱️  Tempo até o erro: {_min}m {_seg:02d}s")
    print("   → Screenshot: erro_boletim.png")
    input("\nPressione ENTER para encerrar...")

finally:
    driver.switch_to.default_content()
    driver.quit()
