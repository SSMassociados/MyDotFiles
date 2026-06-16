#!/bin/bash
# ==============================================================
# sync_gtk3_to_gtk4.sh
# Sincroniza configurações GTK3 → GTK4.
# gtk-4.0 NÃO é versionado em dotfiles — este script cria e
# mantém toda a estrutura em ~/.config/gtk-4.0/ automaticamente.
# Seguro para rodar no ~/.xprofile a cada login.
# ==============================================================
set -euo pipefail

# ── Caminhos ──────────────────────────────────────────────────
GTK3_FILE="$HOME/.dotfiles/gtk-3.0/.config/gtk-3.0/settings.ini"
GTK4_DIR="$HOME/.config/gtk-4.0"
GTK4_CLEAN="$GTK4_DIR/settings.ini.clean"
GTK4_INI="$GTK4_DIR/settings.ini"

# ── Chaves compatíveis com GTK4 ───────────────────────────────
# Omitidas (GTK3-exclusivas que geram warnings no GTK4):
#   gtk-toolbar-style, gtk-toolbar-icon-size,
#   gtk-button-images, gtk-menu-images,
#   gtk-enable-event-sounds, gtk-enable-input-feedback-sounds

GTK4_KEYS_ARR=(
    "gtk-theme-name"
    "gtk-icon-theme-name"
    "gtk-cursor-theme-name"
    "gtk-cursor-theme-size"
    "gtk-font-name"
    "gtk-application-prefer-dark-theme"
    "gtk-enable-animations"
    "gtk-xft-antialias"
    "gtk-xft-dpi"
    "gtk-xft-hinting"
    "gtk-xft-hintstyle"
    "gtk-xft-rgba"
    "gtk-decoration-layout"
)

# Construir a expressão regular
GTK4_KEYS="^($(IFS='|'; echo "${GTK4_KEYS_ARR[*]}"))="

# ── Pré-requisito ─────────────────────────────────────────────
if [[ ! -f "$GTK3_FILE" ]]; then
    echo "⚠️  sync_gtk3_to_gtk4: $GTK3_FILE não encontrado, pulando." >&2
    exit 0
fi

# ── Garantir diretório real (nunca symlink) ───────────────────
if [[ -L "$GTK4_DIR" ]]; then
    echo "⚠️  $GTK4_DIR era symlink — removendo para criar diretório real..." >&2
    rm "$GTK4_DIR"
fi
mkdir -p "$GTK4_DIR"

# ── Regenerar settings.ini.clean atomicamente ─────────────────
TMP_FILE="$(mktemp "$GTK4_DIR/.settings.clean.XXXXXX")"
trap 'rm -f "$TMP_FILE"' EXIT

cat > "$TMP_FILE" << EOF
# Gerado automaticamente por sync_gtk3_to_gtk4.sh
# Origem: $GTK3_FILE
# Data:   $(date '+%Y-%m-%d %H:%M:%S')
# NÃO edite este arquivo manualmente.

[Settings]
EOF

grep -E "$GTK4_KEYS" "$GTK3_FILE" >> "$TMP_FILE" || {
    echo "⚠️  sync_gtk3_to_gtk4: nenhuma chave compatível encontrada." >&2
    exit 0
}

mv "$TMP_FILE" "$GTK4_CLEAN"
trap - EXIT

# ── Criar symlink interno apenas se necessário ────────────────
CURRENT_TARGET="$(readlink "$GTK4_INI" 2>/dev/null || true)"

if [[ "$CURRENT_TARGET" != "$GTK4_CLEAN" ]]; then
    ln -sf "$GTK4_CLEAN" "$GTK4_INI"
    echo "🔗 Link criado: $GTK4_INI"
    echo "            → $GTK4_CLEAN"
else
    echo "✔  Link já correto, mantido."
fi

echo ""
echo "✅ GTK4 sincronizado com GTK3."
echo "   GTK3: $GTK3_FILE"
echo "   GTK4: $GTK4_INI → $GTK4_CLEAN"
