#!/usr/bin/env python3
"""
Módulo de debug para automações SIEPE.
Importe e chame diagnosticar(driver, "contexto") em qualquer ponto do script.
"""
from selenium.webdriver.common.by import By
import time, os, re

def diagnosticar(driver, contexto="", salvar_html=True):
    """
    Coleta e exibe diagnóstico completo da página no momento do erro.
    Salva screenshot e (opcionalmente) o HTML do iframe ativo.

    Parâmetros:
        driver      — instância do WebDriver
        contexto    — texto descritivo do passo onde ocorreu o erro
        salvar_html — se True, salva o HTML do frame atual em arquivo
    """
    ts = time.strftime("%H%M%S")
    nome_base = f"debug_{ts}_{contexto.replace(' ','_')[:30]}" if contexto else f"debug_{ts}"

    print(f"\n{'━'*52}")
    print(f"  🔬 DIAGNÓSTICO — {contexto or 'sem contexto'}")
    print(f"{'━'*52}")

    # ── 1. Screenshot ─────────────────────────────────────────
    arq_png = f"{nome_base}.png"
    try:
        driver.save_screenshot(arq_png)
        print(f"  📸 Screenshot salvo: {arq_png}")
    except Exception as e:
        print(f"  ⚠️  Screenshot falhou: {e}")

    # ── 2. URL e título ───────────────────────────────────────
    try:
        print(f"  🌐 URL   : {driver.current_url}")
        print(f"  📄 Título: {driver.title}")
    except Exception:
        pass

    # ── 3. Iframes presentes ──────────────────────────────────
    try:
        driver.switch_to.default_content()
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        print(f"\n  🖼️  Iframes encontrados: {len(iframes)}")
        for i, fr in enumerate(iframes):
            src = fr.get_attribute("src") or ""
            fid = fr.get_attribute("id") or ""
            print(f"      [{i}] id='{fid}'  src='{src[:60]}'")
    except Exception as e:
        print(f"  ⚠️  Erro ao listar iframes: {e}")

    # ── 4. Contexto do frame atual ────────────────────────────
    print(f"\n  📦 Inspecionando frame atual...")
    _inspecionar_frame(driver, contexto, nome_base, salvar_html)

    # ── 5. Inspeciona iframe #0 se diferente do atual ─────────
    try:
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        if iframes:
            driver.switch_to.default_content()
            driver.switch_to.frame(iframes[0])
            print(f"\n  📦 Inspecionando iframe #0...")
            _inspecionar_frame(driver, contexto + "_iframe0", nome_base + "_iframe0", salvar_html)
    except Exception:
        pass
    finally:
        try:
            driver.switch_to.default_content()
        except Exception:
            pass

    print(f"{'━'*52}\n")


def _inspecionar_frame(driver, contexto, nome_base, salvar_html):
    """Inspeciona seletores relevantes dentro do frame atual."""

    # ── Selects presentes ─────────────────────────────────────
    try:
        from selenium.webdriver.support.ui import Select as SeleniumSelect
        selects = driver.find_elements(By.TAG_NAME, "select")
        print(f"    📋 Selects encontrados: {len(selects)}")
        for s in selects:
            sid   = s.get_attribute("id") or s.get_attribute("name") or "?"
            sel   = SeleniumSelect(s)
            opcoes = [o.text.strip() for o in sel.options if o.text.strip()]
            selecionado = sel.first_selected_option.text.strip()
            print(f"        id/name='{sid}'  selecionado='{selecionado}'  opções={opcoes[:6]}{'...' if len(opcoes)>6 else ''}")
    except Exception as e:
        print(f"    ⚠️  Erro ao listar selects: {e}")

    # ── Links de paginação ────────────────────────────────────
    try:
        print(f"\n    🔢 Links de paginação (SIEPE — TR[22]/UL):")

        # XPath exato confirmado pelo Automa para o SIEPE
        XPATH_UL_SIEPE = (
            "//div[@id='divCorpoGestaoEscolar']"
            "/FORM[1]/TABLE[1]/TBODY[1]/TR[1]/TD[1]"
            "/DIV[3]/DIV[4]/DIV[1]/TABLE[1]/TBODY[1]/TR[22]/TD[1]/UL[1]"
        )
        ul_els = driver.find_elements(By.XPATH, XPATH_UL_SIEPE)

        if ul_els:
            lis = driver.execute_script(
                "return Array.from(arguments[0].children).filter(e => e.tagName==='LI');",
                ul_els[0]
            )
            for i, li in enumerate(lis):
                links = li.find_elements(By.XPATH, "./a")
                texto  = links[0].text.strip() if links else li.text.strip()
                classe = li.get_attribute("class") or ""
                print(f"        LI[{i+1}] texto='{texto}'  classe_li='{classe}'")
        else:
            print(f"        UL do SIEPE não encontrada (divCorpoGestaoEscolar/TR[22]).")
            print(f"        → Página atual pode não ser o formulário de pesquisa.")

    except Exception as e:
        print(f"    ⚠️  Erro ao listar paginação: {e}")

    # ── Checkbox chkMarcarTodos ───────────────────────────────
    try:
        chk = driver.find_elements(By.ID, "chkMarcarTodos")
        print(f"\n    ☑️  chkMarcarTodos: {'encontrado' if chk else 'NÃO encontrado'}")
        if chk:
            print(f"        checked={chk[0].is_selected()}  displayed={chk[0].is_displayed()}")
    except Exception:
        pass

    # ── Botão PESQUISAR ───────────────────────────────────────
    try:
        btn = driver.find_elements(By.ID, "lnk_pesquisar")
        print(f"    🔍 lnk_pesquisar: {'encontrado' if btn else 'NÃO encontrado'}")
    except Exception:
        pass

    # ── Botão SELECIONAR ──────────────────────────────────────
    try:
        sel = driver.find_elements(By.ID, "lnk_emitirBoletim")
        print(f"    ✔️  lnk_emitirBoletim: {'encontrado' if sel else 'NÃO encontrado'}")
    except Exception:
        pass

    # ── Texto de resultados ───────────────────────────────────
    try:
        resultados = driver.find_elements(By.XPATH,
            "//*[contains(normalize-space(text()),'Resultados') "
            "and contains(normalize-space(text()),' de ')]"
        )
        if resultados:
            print(f"\n    📊 Texto de resultados: '{resultados[0].text.strip()}'")
        else:
            print(f"\n    📊 Texto de resultados: não encontrado")
    except Exception:
        pass

    # ── Mensagens de erro na página ───────────────────────────
    try:
        erros = driver.find_elements(By.XPATH,
            "//*[contains(@class,'erro') or contains(@class,'error') or "
            "contains(@class,'alert') or contains(@id,'erro') or contains(@id,'error')]"
        )
        erros_txt = [e.text.strip() for e in erros if e.text.strip()]
        if erros_txt:
            print(f"\n    🚨 Mensagens de erro na página:")
            for txt in erros_txt:
                print(f"        → {txt[:120]}")
    except Exception:
        pass

    # ── HTML do frame (opcional) ──────────────────────────────
    if salvar_html:
        try:
            arq_html = f"{nome_base}.html"
            html = driver.execute_script("return document.documentElement.outerHTML;")
            with open(arq_html, "w", encoding="utf-8") as f:
                f.write(html)
            print(f"\n    💾 HTML salvo: {arq_html} ({len(html):,} chars)")
        except Exception as e:
            print(f"\n    ⚠️  HTML não salvo: {e}")
