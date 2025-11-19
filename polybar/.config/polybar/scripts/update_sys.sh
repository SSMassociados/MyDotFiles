#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

# Cores carregadas do Pywal
source "${HOME}/.cache/wal/colors.sh"
primary="${color1}"  # Pode ajustar para outra cor do tema, se preferir

# Verifica se o modo silencioso foi ativado
quiet=false
if [[ "$1" == "--quiet" ]]; then
    quiet=true
fi

# Total de pacotes instalados
total_pkgs=$(pacman -Qq 2>/dev/null | wc -l)

# Updates do repositório (pacman-contrib)
command -v checkupdates >/dev/null && repo_updates=$(checkupdates 2>/dev/null | wc -l) || repo_updates=0

# Updates do AUR
command -v yay >/dev/null && aur_updates=$(yay -Qum 2>/dev/null | wc -l) || aur_updates=0

# Soma total de updates (repo + AUR)
all_updates=$((repo_updates + aur_updates))

# Modo silencioso: não mostrar nada se não houver updates
if $quiet && [[ "$all_updates" -eq 0 ]]; then
    exit 0
fi

# Ícone se houver atualizações
has_updates_icon=""
[ "$all_updates" -gt 0 ] && has_updates_icon="%{F$primary}%{F-}"

# Saída formatada para Polybar
echo "%{T4}%{F$primary}$has_updates_icon%{F-}%{T-} %{T4}%{F$primary}󰏔%{F-}%{T-} $total_pkgs %{T4}%{F$primary}%{F-}%{T-} $repo_updates %{T4}%{F$primary}%{F-}%{T-} $aur_updates"
