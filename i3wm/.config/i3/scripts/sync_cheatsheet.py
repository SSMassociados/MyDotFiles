#!/usr/bin/env python3
"""
sync_cheatsheet.py — i3wm Cheatsheet Generator
Chamado pelo watch_config_i3.sh. Executa uma única vez.
"""

from __future__ import annotations

import os
import re
from datetime import datetime

# ── Personalização ────────────────────────────────────────────────────────────
MOD_REPLACEMENT = "🐧"   # troque por "Super" ou "Mod" se preferir texto puro

# ── Caminhos ──────────────────────────────────────────────────────────────────
I3_DIR    = os.path.expanduser("~/.config/i3/modules")
ENV_FILE  = os.path.join(I3_DIR, "env.conf")
OUTPUT_MD = os.path.expanduser("~/.config/i3/scripts/cheatsheet.md")

TARGET_FILES = ["binds.conf", "misc.conf", "monitors.conf", "input.conf"]

EXEC_VARS = (
    "$exe", "$always", "$term", "$nvim", "$center",
    "$float", "$full", "$scra", "$show", "$to", "$lock",
)

# ── Regexes globais pré-compilados ────────────────────────────────────────────
# MELHORIA: substituído \b por (?![a-zA-Z0-9_]) no lookahead negativo para
# evitar falsos positivos com variáveis que terminam em underscore.
_EXEC_VAR_NAMES = "|".join(re.escape(v.lstrip("$")) for v in EXEC_VARS)
_MOD_VARS = r"\$(?!(?:" + _EXEC_VAR_NAMES + r")(?![a-zA-Z0-9_]))\w+"

BIND_RE = re.compile(
    r"^(?:(" + _MOD_VARS + r")(?:\+(\S+)|\s+(\S+))|(bindsym)(?:\s+--\S+)*\s+(\S+))\s*(.*)",
    re.IGNORECASE,
)
SET_RE = re.compile(r'^set\s+(\$\w+)\s+(.+)$', re.IGNORECASE)

MODE_VAR_RE   = r'mode\s+["\']?(\$\w+)["\']?'
MODE_BLOCK_RE = re.compile(r'^' + MODE_VAR_RE + r'\s*\{', re.IGNORECASE)
MODE_CALL_RE  = re.compile(r'\bmode\s+["\']?(\$\w+)["\']?(?:\b|;|\s|$)', re.IGNORECASE)

INNER_BIND_RE = re.compile(r'^\s*bindsym\s+(\S+)\s+(.*)', re.IGNORECASE)

_RE_SEPARATORS = re.compile(r"^[=\-\^~\*\s#|═─━╌╍┄┅─\u2500-\u257f]+$")
_RE_NON_ALPHA  = re.compile(r"[^a-zA-ZÀ-ú]")
_RE_LABEL_TAG  = re.compile(r"^\[.+\][\s\-]*$")

_RE_MULTI_SEP  = re.compile(r"[ +]+")
_RE_MOD_WORD   = re.compile(r"\bMod\b")

_PATH_RE = re.compile(r"(?:~|\$HOME|/etc|/usr|/var|/home)[^\s\"'\\,;]*")

SKIP_PREFIXES = (
    "//", "set ", "include", "for_window", "assign",
    "workspace ", "gaps", "font", "default_", "hide_edge",
    "focus_on", "focus_wrapping", "mouse_warping", "popup_during",
    "client.", "floating_modifier", "title_align", "workspace_auto",
    "mode ", "}", "bar ", "set_from_resource",
)

# Palavras-chave de comandos i3 que nunca são teclas válidas num bindsym.
# Se o token capturado como "key" for uma dessas, o bind é um comando direto
# (ex: "$ct workspace next") e deve ser ignorado pelo parser de atalhos.
_I3_COMMAND_KEYWORDS = frozenset({
    "workspace", "focus", "move", "split", "layout", "floating",
    "sticky", "fullscreen", "scratchpad", "resize", "exec",
    "kill", "reload", "restart", "exit", "nop", "bar",
    "gaps", "border", "title_format", "mark", "unmark",
})

MAX_CMD_LEN = 250  # comprimento máximo para comandos sem caminho detectável


def _safe_sub(text: str, var: str, value: str) -> str:
    return re.sub(re.escape(var) + r'(?![a-zA-Z0-9_])', lambda _: value, text)


def _escape_markdown_syntax(text: str) -> str:
    if not text:
        return ""
    text = text.replace("|", "\\|")
    text = text.replace("[", "\\[").replace("]", "\\]")
    return text


# ── Filtro de comentários ─────────────────────────────────────────────────────
def is_noise_comment(text: str) -> bool:
    if not text:
        return True
    if _RE_SEPARATORS.match(text):
        return True
    letters = _RE_NON_ALPHA.sub("", text)
    if letters and letters == letters.upper() and len(letters) > 3:
        return True
    if _RE_LABEL_TAG.match(text):
        return True
    if len(text) > 90:
        return True
    return False


# ── Carrega e resolve env.conf ────────────────────────────────────────────────
def load_env(path: str) -> dict[str, str]:
    """
    Lê o env.conf e resolve variáveis recursivamente (até 5 passes).

    MELHORIA: encoding com errors='replace' para tolerância a arquivos com
    bytes não-UTF-8.
    """
    raw: dict[str, str] = {}
    if not os.path.exists(path):
        print(f"⚠️  env.conf não encontrado em {path}")
        return raw

    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            m = SET_RE.match(line)
            if m:
                val = m.group(2).strip()
                # Remove aspas externas (simples ou duplas)
                if len(val) >= 2 and val[0] == val[-1] and val[0] in ("'", '"'):
                    val = val[1:-1]
                raw[m.group(1)] = val

    # Ordenar por comprimento decrescente para substituição mais específica primeiro
    sorted_vars = sorted(raw.keys(), key=lambda x: -len(x))

    for _ in range(5):
        changed = False
        for var in sorted_vars:
            val = raw[var]
            nv = val
            for k in sorted_vars:
                if k != var and k in nv:
                    nv = _safe_sub(nv, k, raw[k])
            if nv != val:
                raw[var] = nv
                changed = True
        if not changed:
            break

    return raw


# ── Detecta variáveis auto-suficientes (sem tecla adicional) ──────────────────
def _detect_self_sufficient_mods(env: dict[str, str]) -> frozenset[str]:
    """
    MELHORIA: antes era um frozenset hardcoded {"$as", "$ct"}.
    Agora detecta automaticamente qualquer variável cujo valor seja um
    'bindsym <combo>' onde o combo contenha '+' — ou seja, o próprio
    bind já é a tecla completa (ex: Mod1+space, Ctrl+Tab).

    Isso elimina a necessidade de atualizar manualmente o código ao adicionar
    novas variáveis desse tipo no env.conf.
    """
    result: set[str] = set()
    for var, val in env.items():
        if val.startswith("bindsym ") or val.startswith("bindsym\t"):
            key_part = val[len("bindsym"):].strip()
            first = key_part.split()[0] if key_part else ""
            if "+" in first:
                result.add(var)
    return frozenset(result)


# ── Monta mapa de substituição de variáveis → atalhos legíveis ────────────────
def build_substitution_map(env: dict[str, str]) -> list[tuple[str, str]]:
    BIND_PREFIXES = ("bindsym ", "bindsym")
    SIMPLE_KEYS = {
        "Up", "Down", "Left", "Right", "Prior", "Next",
        "Home", "End", "Tab", "Return", "Escape", "space",
        "apostrophe", "semicolon", "comma", "period",
        "slash", "backslash", "minus", "equal",
        "bracketleft", "bracketright",
    }
    # Apenas mod2/mod3 são bloqueados: não têm mapeamento legível útil.
    # mod1 → Alt, mod4 → MOD_REPLACEMENT, mod5 → AltGr são tratados abaixo.
    FORBIDDEN_VALS = {"mod2", "mod3"}

    subs: dict[str, str] = {}
    for var, val in env.items():
        if val.lower() in FORBIDDEN_VALS:
            continue

        processed = False
        for prefix in BIND_PREFIXES:
            if val.startswith(prefix):
                k = val[len(prefix):].strip()
                k = (k.replace("Mod4", MOD_REPLACEMENT)
                      .replace("Mod1", "Alt")
                      .replace("Mod5", "AltGr"))
                if k.startswith("Alt+" + MOD_REPLACEMENT):
                    k = MOD_REPLACEMENT + "+Alt" + k[len("Alt+" + MOD_REPLACEMENT):]
                subs[var] = k
                processed = True
                break
        if processed:
            continue

        # Variáveis cujo valor é diretamente um nome de modificador Xorg.
        # Tratadas individualmente para gerar o label correto no cheatsheet.
        val_lower = val.lower()
        if val_lower == "mod4":
            subs[var] = MOD_REPLACEMENT
            continue
        if val_lower == "mod1":
            subs[var] = "Alt"
            continue
        if val_lower == "mod5":
            subs[var] = "AltGr"
            continue

        if val in SIMPLE_KEYS:
            subs[var] = val
        elif re.match(r"^[A-Za-z][a-z0-9_]*$", val):
            if len(val) == 1 or val[0].isupper():
                subs[var] = val

    return sorted(subs.items(), key=lambda x: -len(x[0]))


# ── Helpers ───────────────────────────────────────────────────────────────────
def resolve_shortcut(mod: str, key: str, subs: list[tuple[str, str]]) -> str:
    combo = (mod + " " + key).strip() if mod.lower() != "bindsym" else key

    for v, h in subs:
        combo = _safe_sub(combo, v, h)

    # Fallback para Mod* residuais que não passaram pelo mapa de substituição
    combo = (combo.replace("Mod4", MOD_REPLACEMENT)
                  .replace("Mod1", "Alt")
                  .replace("Mod5", "AltGr"))

    # Normaliza separadores (espaços e + entre tokens) para + sem espaços,
    # mas só entre tokens — preserva + que faz parte de nomes de teclas
    # (ex: "XF86AudioRaiseVolume" não contém +, mas "Mod4+F1" sim).
    # Estratégia: dividir no espaço primeiro (tokens já separados pelo parser),
    # depois unir com " + " para espaçamento visual.
    tokens = _RE_MULTI_SEP.split(combo.strip())
    tokens = [t for t in tokens if t]  # remove vazios

    combo = _RE_MOD_WORD.sub(MOD_REPLACEMENT, " + ".join(tokens))

    return combo


def extract_inline_comment(rest: str) -> str:
    in_quote, qc, escaped = False, None, False
    for i, ch in enumerate(rest):
        if escaped:
            escaped = False
            continue
        if ch == '\\':
            escaped = True
            continue
        if ch in ('"', "'") and not in_quote:
            in_quote, qc = True, ch
        elif in_quote and ch == qc:
            in_quote = False
        elif ch == "#" and not in_quote:
            return rest[i + 1:].strip()
    return ""


def extract_filepath(rest: str) -> str:
    rest = re.sub(r',?\s*mode\s+"default".*$', "", rest).strip().rstrip(";,")
    m = _PATH_RE.search(rest)
    if m:
        return m.group(0).replace("$HOME", "~").replace("'", "").replace('"', "").rstrip(";,")

    clean_cmd = rest.strip()
    return clean_cmd if len(clean_cmd) <= MAX_CMD_LEN else clean_cmd[:MAX_CMD_LEN - 3] + "…"


def read_all_lines() -> list[str]:
    """
    MELHORIA: encoding com errors='replace' para tolerância a arquivos com
    bytes não-UTF-8, prevenindo UnicodeDecodeError silencioso.
    """
    lines: list[str] = []
    for filename in TARGET_FILES:
        path = os.path.join(I3_DIR, filename)
        if not os.path.exists(path):
            print(f"    ⚠️  {filename} não encontrado — ignorado")
            continue
        with open(path, encoding="utf-8", errors="replace") as f:
            lines.extend(f.readlines())
    return lines


def _parse_line_as_bind(line: str, self_sufficient_mods: frozenset[str]):
    """
    MELHORIA: recebe self_sufficient_mods como parâmetro em vez de usar
    um frozenset global hardcoded, permitindo detecção dinâmica.
    """
    m = BIND_RE.match(line)
    if not m:
        return None

    mod  = m.group(1) or m.group(4)
    key  = m.group(2) or m.group(3) or m.group(5)
    rest = m.group(6)

    # Se o token capturado como tecla é um comando i3 (ex: "$ct workspace next")
    # e o modificador é auto-suficiente (já contém o combo completo),
    # trata como bind auto-suficiente: key="" e rest = key + " " + rest
    if key and key.lower() in _I3_COMMAND_KEYWORDS:
        if mod in self_sufficient_mods:
            rest = (key + " " + rest).strip()
            key  = ""
        else:
            return None

    if key and key.startswith(EXEC_VARS):
        if mod in self_sufficient_mods:
            key = ""
        else:
            return None

    return mod, key, rest


# ── Parser principal ──────────────────────────────────────────────────────────
def parse_all(
    subs: list[tuple[str, str]],
    all_lines: list[str],
    self_sufficient_mods: frozenset[str],
) -> tuple[list[dict], dict[str, list[dict]]]:
    """
    MELHORIA: unifica as duas passagens sobre all_lines em uma única iteração,
    usando flags de estado (in_mode, collecting_normal) para coletar modos e
    binds normais ao mesmo tempo. Reduz o custo de O(2n) para O(n).
    """
    # ── Estruturas para modos ─────────────────────────────────────────────────
    mode_var_to_entry: dict[str, str] = {}
    mode_var_to_desc:  dict[str, str] = {}   # comentário acima do bindsym que ativa o modo
    mode_var_to_label: dict[str, str] = {}   # valor do set $var "legenda"
    mode_raw: dict[str, list[dict]]   = {}

    # ── Estruturas para binds normais ─────────────────────────────────────────
    entries: list[dict] = []

    in_mode      = False
    current_var  = ""
    prev_comment = ""

    for raw_line in all_lines:
        line = raw_line.strip()

        # ── Dentro de um bloco mode { ... } ──────────────────────────────────
        if in_mode:
            if line == "}":
                in_mode = False
                current_var = ""
                continue
            bm = INNER_BIND_RE.match(line)
            if not bm:
                continue
            subkey, rest = bm.group(1), bm.group(2)
            if subkey in ("Return", "Escape"):
                continue
            if re.match(r"^mode\s+", rest.strip()):
                continue
            mode_raw.setdefault(current_var, []).append(
                {"subkey": subkey, "desc": extract_filepath(rest)}
            )
            continue

        # ── Comentários e linhas vazias ───────────────────────────────────────
        if line.startswith("##"):
            prev_comment = ""
            continue
        if line.startswith("#"):
            t = line.lstrip("#").strip()
            prev_comment = "" if is_noise_comment(t) else t
            continue
        if not line:
            prev_comment = ""
            continue

        # ── Início de bloco mode ──────────────────────────────────────────────
        m_block = MODE_BLOCK_RE.match(line)
        if m_block:
            in_mode = True
            current_var = m_block.group(1)
            mode_raw.setdefault(current_var, [])
            prev_comment = ""
            continue

        # ── Declaração set ────────────────────────────────────────────────────
        sm = SET_RE.match(line)
        if sm:
            mode_var_to_label[sm.group(1)] = sm.group(2).strip()
            prev_comment = ""
            continue

        # ── Prefixos a ignorar ────────────────────────────────────────────────
        if any(line.startswith(p) for p in SKIP_PREFIXES):
            prev_comment = ""
            continue

        # ── Tenta parsear como bind ───────────────────────────────────────────
        parsed = _parse_line_as_bind(line, self_sufficient_mods)
        if not parsed:
            prev_comment = ""
            continue
        mod, key, rest = parsed

        # ── Bind que ativa um modo: registra entry point ──────────────────────
        mm = MODE_CALL_RE.search(rest)
        if mm:
            var = mm.group(1)
            mode_var_to_entry[var] = resolve_shortcut(mod, key, subs)
            if prev_comment:
                # Remove prefixo de atalho do comentário, ex:
                # "$sup+apostrophe - Dotfiles Mode Config" → "Dotfiles Mode Config"
                # "$sup+Home - i3 Config Modules"         → "i3 Config Modules"
                cleaned = re.sub(
                    r"^\$?\w[\w+]*\s*[-–—]\s*",
                    "",
                    prev_comment,
                ).strip()
                mode_var_to_desc[var] = cleaned or prev_comment
            prev_comment = ""
            continue  # não adiciona aos binds normais

        # ── Bind normal ───────────────────────────────────────────────────────
        inline = extract_inline_comment(rest)
        description = inline if inline else prev_comment
        if not description:
            prev_comment = ""
            continue

        entries.append({
            "key":  resolve_shortcut(mod, key, subs),
            "desc": description,
        })
        prev_comment = ""

    # ── Monta dicionário final de modos ───────────────────────────────────────
    final_modes: dict[str, dict] = {}
    for var, items in mode_raw.items():
        if not items:
            continue
        entry      = mode_var_to_entry.get(var, "?")
        entry_desc = mode_var_to_desc.get(var, "")    # (1) ex: "Dotfiles Mode Config"
        legend     = mode_var_to_label.get(var, "")   # (2) ex: "[K]itty | [B]etterloc | ..."

        # chave de desambiguação: prefere a descrição, cai no legend, cai na var
        dedup_key = entry_desc or legend or var
        base_key  = dedup_key
        counter   = 1
        while dedup_key in final_modes:
            dedup_key = f"{base_key} ({counter})"
            counter += 1

        final_modes[dedup_key] = {
            "entry":      entry,
            "entry_desc": entry_desc,
            "legend":     legend,
            "items":      [
                {"key": f"{entry} → {it['subkey']}", "desc": it["desc"]}
                for it in items
            ],
        }

    return entries, final_modes


# ── Categorias ────────────────────────────────────────────────────────────────
CATEGORIES: list[tuple[str, str, list[str]]] = [
    # 01 ── Workspaces e Navegação
    ("🌐", "Workspaces e Navegação", [
        r"workspace", r"área de trabalho",
        r"focar janela urgente", r"janela urgente",
        r"sticky.*workspaces", r"workspaces.*sticky",
        r"multi-monitor workspace",
    ]),
    # 02 ── Controles do Mouse
    ("🖱️", "Controles do Mouse", [
        r"botão (meio|direito)",
        r"scroll (esquerdo|direito).*janela",
        r"força fechar",
        r"alterna flutuante",
        r"button\d",
    ]),
    # 03 ── Gerenciamento de Janelas
    ("🪟", "Gerenciamento de Janelas", [
        r"mover foco", r"mover janela",
        r"foco (←|→|↑|↓)",
        r"focar (container|elemento|filho|pai)",
        r"alternar.*janelas", r"alternar foco.*tiling",
        r"janelas em abas", r"janelas empilhadas",
        r"split (horizontal|vertical|toggle|alternando)",
        r"layout (toggle|restore|alternando)",
        r"orientação.*invertendo",
        r"modo flutuante", r"flutuante.*toggle",
        r"alternar bordas",
        r"scratchpad", r"janela oculta",
        r"tela cheia", r"fullscreen",
        r"fecha (janela|todas)", r"fechar.*seletivo",
        r"mata.*processo", r"cursor em x",
        r"centralizar janela",
        r"(aumenta|diminui) (largura|altura)",
        r"(←|→|↑|↓).*(aumenta|diminui)",
        r"sticky toggle",
        r"alternando h", r"alternando.*v",
        r"\burgência\b",
    ]),
    # 04 ── Aplicativos e Lançadores
    ("🚀", "Aplicativos e Lançadores", [
        r"\bkitty\b", r"firefox", r"brave", r"chrome", r"thunar",
        r"ranger", r"yazi", r"google meet", r"launcher",
        r"calculadora", r"spotify", r"\brmpc\b", r"alarme",
        r"terminal flutuante", r"dropdown",
        r"qutebrowser",
        r"wallpaper", r"pywal",
        r"launch search", r"\bsearch\b",
        r"start/close",
    ]),
    # 05 ── Utilitários do Sistema
    ("🔧", "Utilitários do Sistema", [
        r"reinici.*i3", r"reinici.*sistema",
        r"recarreg", r"sai do i3", r"login manager",
        r"desligamento", r"power menu",
        r"suspende", r"bloque.*tela",
        r"dual boot", r"compositor", r"picom",
        r"inatividade", r"xidlehook",
        r"ajuda do i3", r"cheatsheet",
        r"polybar", r"todas.*barras|barras.*instâncias",
        r"monitor (secund|principal|secu)",
        r"alternar monitores",
        r"testar notifica",
        r"dunst(?!ctl)",
    ]),
    # 06 ── Controles de Tela
    ("🖥️", "Controles de Tela", [
        r"print\b", r"screenshot", r"screen recording", r"gravar",
        r"captura", r"área selecionada", r"tela inteira", r"janela clicada",
        r"ocr\b", r"barcode", r"qrcode", r"qr.*(code|scan|share)",
        r"espelhamento",
    ]),
    # 07 ── Controles de Mídia
    ("🎵", "Controles de Mídia", [
        r"volume", r"\bmute\b", r"mudo", r"microfone",
        r"\bplay\b", r"\bpause\b", r"\bparar\b",
        r"faixa (anterior|próxima)", r"próxima faixa",
        r"brilho", r"brightness",
    ]),
    # 08 ── Dispositivos e Conexões
    ("📱", "Dispositivos e Conexões", [
        r"android", r"bluetooth", r"\bupnp\b", r"tethering",
        r"scrcpy", r"kde connect", r"gnirehtet", r"autoadb",
        r"\bwifi\b", r"\bquick\b",
    ]),
    # 09 ── Layouts Salvos
    ("💾", "Layouts Salvos", [
        r"restore bindings", r"layout.*restore", r"salvar.*layout",
        r"save.*layout", r"cenário", r"layout_\d",
    ]),
    # 10 ── Aparência
    ("🎨", "Aparência", [
        r"\btema\b", r"\bcores?\b", r"border toggle",
    ]),
    # 11 ── Notificações
    ("🔔", "Notificações", [
        r"fecha notifica", r"limpa.*notifica", r"mostra.*notifica",
        r"última notifica", r"contexto/link", r"dunstctl",
        r"retoma notificações",
    ]),
    # 12 ── Recursos Especiais
    ("✨", "Recursos Especiais", [
        r"\bsige\b", r"launch sige", r"austro",
    ]),
]

_COMPILED_CATEGORIES = [
    (emoji, name, [re.compile(p, re.IGNORECASE) for p in patterns])
    for emoji, name, patterns in CATEGORIES
]


# ── Ordenação por prefixo modificador ────────────────────────────────────────
# Prioridade dos prefixos: define a ordem visual dentro de cada seção.
# Prefixos não listados ficam no fim, ordenados alfabeticamente entre si.
_PREFIX_PRIORITY: list[str] = [
    MOD_REPLACEMENT,                    # 🐧
    f"{MOD_REPLACEMENT} + Shift",       # 🐧 + Shift
    f"{MOD_REPLACEMENT} + Ctrl",        # 🐧 + Ctrl
    f"{MOD_REPLACEMENT} + Alt",         # 🐧 + Alt
    "Ctrl + Alt",
    "Ctrl + Shift",
    "Ctrl",
    "Alt + Shift",
    "Alt",
    "AltGr",                            # Mod5
    "Shift",
]


def _shortcut_sort_key(shortcut: str) -> tuple[int, str]:
    """
    Retorna (prioridade, shortcut) para ordenação estável.
    Extrai o prefixo modificador (tudo antes da última tecla) e
    busca sua posição em _PREFIX_PRIORITY.
    Atalhos com mesmo prefixo são sub-ordenados alfabeticamente pela tecla final.
    """
    parts = [p.strip() for p in shortcut.split("+")]
    # Prefixo = todas as partes exceto a última tecla de ação
    prefix = " + ".join(parts[:-1]) if len(parts) > 1 else parts[0]

    # Normaliza emojis/unicode para comparação
    for i, p in enumerate(_PREFIX_PRIORITY):
        if prefix.lower() == p.lower():
            return (i, shortcut)

    # Prefixo desconhecido: ordena após os conhecidos, por ordem alfabética
    return (len(_PREFIX_PRIORITY), shortcut)


def sort_bindings(items: list[dict]) -> list[dict]:
    """
    Ordena uma lista de binds pelo prefixo modificador do atalho.
    Mantém a ordem original como critério de desempate (sort estável).
    """
    return sorted(items, key=lambda b: _shortcut_sort_key(b["key"]))


# ── Geração do Markdown ───────────────────────────────────────────────────────
def generate_markdown(bindings: list[dict], modes: dict[str, list[dict]]) -> None:
    """
    MELHORIA: os.makedirs agora recebe um diretório validado — evita
    FileNotFoundError quando OUTPUT_MD não contém separador de diretório.
    """
    now = datetime.now().strftime("%d/%m/%Y - %H:%M:%S")
    out: list[str] = [
        "# i3wm Cheat Sheet - Sidiclei Config\n",
        f"> 🕒 **Última atualização:** {now}\n\n",
        "> 🐧 = Super (Mod4)\n\n",
    ]

    buckets: dict[str, list] = {f"{e} {n}": [] for e, n, _ in CATEGORIES}
    leftovers: list[dict] = []

    for b in bindings:
        dl_lower = b["desc"].lower()
        placed = False
        for emoji, name, compiled_pats in _COMPILED_CATEGORIES:
            if any(p.search(dl_lower) for p in compiled_pats):
                buckets[f"{emoji} {name}"].append(b)
                placed = True
                break
        if not placed:
            leftovers.append(b)

    for cat, items in buckets.items():
        if not items:
            continue
        out += [f"## {cat}\n", "| Atalho | Ação |\n| --- | --- |\n"]
        out += [
            f"| {_escape_markdown_syntax(b['key'])} | {_escape_markdown_syntax(b['desc'])} |\n"
            for b in sort_bindings(items)
        ]
        out.append("\n")

    if leftovers:
        out += ["## 🧩 Outros Atalhos\n", "| Atalho | Ação |\n| --- | --- |\n"]
        out += [
            f"| {_escape_markdown_syntax(b['key'])} | {_escape_markdown_syntax(b['desc'])} |\n"
            for b in sort_bindings(leftovers)
        ]
        out.append("\n")

    if modes:
        out.append("## 🔑 Modos Especiais\n\n")
        for _, mode in modes.items():
            items = mode["items"]
            if not items:
                continue

            entry      = _escape_markdown_syntax(mode["entry"])
            entry_desc = _escape_markdown_syntax(mode["entry_desc"])
            legend     = _escape_markdown_syntax(mode["legend"])

            # Linha (1): ### atalho — Descrição
            if entry_desc:
                out.append(f"### {entry} → {entry_desc}\n")
            else:
                out.append(f"### {entry}\n")

            # Linha (2): legenda em itálico (o set $var "...")
            if legend:
                out.append(f"*{legend}*\n\n")

            out.append("| Atalho | Arquivo / Comando |\n| --- | --- |\n")

            for b in sort_bindings(items):
                out.append(
                    f"| {_escape_markdown_syntax(b['key'])} | {_escape_markdown_syntax(b['desc'])} |\n"
                )
            out.append("\n")

    # MELHORIA: guard para OUTPUT_MD sem diretório pai (ex: nome de arquivo puro)
    output_dir = os.path.dirname(OUTPUT_MD)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.writelines(out)

    total = len(bindings) + sum(len(m["items"]) for m in modes.values())
    print(f"✅ cheatsheet.md atualizado — {total} atalhos ({now})")


if __name__ == "__main__":
    print("📖 Lendo env.conf...")
    env  = load_env(ENV_FILE)
    subs = build_substitution_map(env)
    print(f"   {len(subs)} variáveis mapeadas com sucesso.")

    # MELHORIA: detecção automática de mods auto-suficientes
    self_sufficient_mods = _detect_self_sufficient_mods(env)
    print(f"   {len(self_sufficient_mods)} mods auto-suficientes detectados: {self_sufficient_mods}")

    print("📂 Lendo arquivos de configuração...")
    all_lines = read_all_lines()
    print(f"   {len(all_lines)} linhas carregadas")

    print("🔍 Parseando binds e modos...")
    bindings, modes = parse_all(subs, all_lines, self_sufficient_mods)
    print(f"   {len(bindings)} atalhos normais | {len(modes)} modos especiais")

    generate_markdown(bindings, modes)
