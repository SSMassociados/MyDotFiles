### HABILITANDO PLUGINS (ZSH-AUTOSUGGESTIONS ZSH-SYNTAX-HIGHLIGHTING & FZF)

### Download zsh-autosuggestions by
### git clone https://github.com/zsh-users/zsh-autosuggestions.git $ZSH_CUSTOM/plugins/zsh-autosuggestions

### Download zsh-syntax-highlighting by
### git clone https://github.com/zsh-users/zsh-syntax-highlighting.git $ZSH_CUSTOM/plugins/zsh-syntax-highlighting

### Download FZF —command line fuzzy finder
### git clone --depth 1 https://github.com/junegunn/fzf.git ~/.fzf && ~/.fzf/install

### Instalar o plugin fzf-tab (necessário para os zstyles de preview funcionarem)
### git clone https://github.com/Aloxaf/fzf-tab ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/fzf-tab

### Download K
### git clone https://github.com/supercrabtree/k $ZSH_CUSTOM/plugins/k

### Powerlevel10k no Oh My Zsh
### git clone --depth=1 https://github.com/romkatv/powerlevel10k.git ${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}/themes/powerlevel10k

# ==============================================================================
# 1. POWERLEVEL10K INSTANT PROMPT (DEVE FICAR NO TOPO ABSOLUTO)
# ==============================================================================
if [[ -r "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh" ]]; then
  source "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh"
fi

# ==============================================================================
# 2. VARIÁVEIS DE AMBIENTE E PATH
# ==============================================================================
export ZSH="$HOME/.oh-my-zsh"
export LANG=pt_BR.UTF-8

# Editor padrão (neovim se disponível, senão vim)
if [[ -n $SSH_CONNECTION ]]; then
  export EDITOR='vim'
else
  export EDITOR='nvim'
fi

# Suporte ao Tilix/VTE (Correção de diretório atual em terminais gráficos)
if [ $TILIX_ID ] || [ $VTE_VERSION ]; then
  source /etc/profile.d/vte.sh
fi

# ==============================================================================
# 3. OH-MY-ZSH & PLUGINS
# ==============================================================================
ZSH_THEME="powerlevel10k/powerlevel10k"

# Definição de Plugins
plugins=(
  git
  sudo
  web-search
  copypath
  copyfile
  copybuffer
  dirhistory
  history
  zsh-autosuggestions
  fzf-tab               # Deve ser carregado após plugins de completion
  zsh-syntax-highlighting # Deve ser o último plugin
)

source $ZSH/oh-my-zsh.sh

# ==============================================================================
# 4. CONFIGURAÇÕES DE HISTÓRICO E COMPORTAMENTO
# ==============================================================================
HISTSIZE=10000
SAVEHIST=10000
HISTFILE=~/.zsh_history

# Opções de Histórico
setopt appendhistory         # Adiciona ao final, não sobrescreve
setopt sharehistory          # Compartilha histórico entre terminais
setopt hist_ignore_space     # Espaço antes do comando ignora histórico
setopt hist_ignore_all_dups  # Remove duplicatas antigas
setopt hist_save_no_dups     # Não salva duplicatas
setopt hist_find_no_dups     # Busca limpa sem duplicatas
setopt hist_reduce_blanks    # Remove espaços extras

# ==============================================================================
# 5. AUTOCOMPLETAR E ESTILO (FZF-TAB)
# ==============================================================================
# Case-insensitive (ignora maiúsculas/minúsculas)
zstyle ':completion:*' matcher-list 'm:{a-z}={A-Za-z}'
# Usa cores do LS_COLORS
zstyle ':completion:*' list-colors "${(s.:.)LS_COLORS}"
# Desabilita menu cíclico
zstyle ':completion:*' menu no

# Previews com FZF-TAB
zstyle ':fzf-tab:complete:cd:*' fzf-preview 'ls --color $realpath'
zstyle ':fzf-tab:complete:__zoxide_z:*' fzf-preview 'ls --color $realpath'

# ==============================================================================
# 6. KEYBINDINGS (ATALHOS)
# ==============================================================================
# Navegação no histórico inteligente (baseado no que já foi digitado)
autoload -U up-line-or-beginning-search
autoload -U down-line-or-beginning-search
zle -N up-line-or-beginning-search
zle -N down-line-or-beginning-search

bindkey '^p' up-line-or-beginning-search      # Ctrl+P (Cima)
bindkey '^n' down-line-or-beginning-search    # Ctrl+N (Baixo)
bindkey '^[w' kill-region                     # Alt+W (Apagar palavra)

# ==============================================================================
# 7. INTEGRAÇÕES (TOOLS)
# ==============================================================================
# FZF
eval "$(fzf --zsh)"

# Zoxide (Substituto inteligente do 'cd')
eval "$(zoxide init --cmd cd zsh)"

# ==============================================================================
# 8. ALIASES
# ==============================================================================
# Configuração
alias zshconfig="nano ~/.zshrc"
alias polyc="nano ~/.config/polybar/config"
alias i3c="nano ~/.config/i3/config"

# Navegação e Sistema Básicos
alias ..='cd ..'
alias c='clear'
alias e='exit'
alias mkdir='mkdir -pv'
alias cp='cp -iv'
alias mv='mv -iv'
alias rm='rm -iv'
alias rmdir='rmdir -v'

# Sistema (Arch Linux Utils)
alias grub-update="sudo grub-mkconfig -o /boot/grub/grub.cfg"
alias mirrors="sudo reflector -l 7 -a 24 -p https --sort rate --save /etc/pacman.d/mirrorlist"
#alias purga="yay -Yc; sudo fstrim -av"
alias purga="pacman -Qtdq | xargs -r sudo pacman -Rns; sudo fstrim -av"
alias info="inxi -SCMmBAGDNsPx -t cm"
alias erros="journalctl -p err -b"
alias g="devour geany"

# Atalhos Yay (Curto e grosso)
alias i="yay -S"     # Install
alias r="yay -Rns"   # Remove
alias u="yay -Syu"   # Update
alias s="yay -Ss"    # Search (Procurar para instalar)
alias q="yay -Q"     # Query (Listar pacotes instalados)

# --- MODERNIZAÇÃO DE COMANDOS (Inteligente) ---

# Find -> Fd
if command -v fd &>/dev/null; then
    alias find='fd'
fi

# Grep -> Ripgrep (Rg)
if command -v rg &>/dev/null; then
    alias grep='rg'
else
    alias grep='grep --color=auto'
    alias fgrep='fgrep --color=auto'
    alias egrep='egrep --color=auto'
fi

# Cat -> Bat
if command -v bat &>/dev/null; then
    alias cat='bat --theme base16'
fi

# Ls -> Lsd ou Eza
if command -v lsd &>/dev/null; then
    alias ls='lsd -F --group-dirs first'
    alias ll='lsd --all --header --long --group-dirs first'
    alias tree='lsd --tree'
elif command -v eza &>/dev/null; then
    alias ls='eza --icons'
    alias ll='eza -l --icons --git -a'
    alias tree='eza --tree --icons'
else
    alias ls='ls --color=auto'
    alias ll='ls -la --color=auto'
fi

# Alias for neovim
if [[ -x "$(command -v nvim)" ]]; then
    alias vi='nvim'
    alias vim='nvim'
    alias svi='sudo nvim'
    alias vis='nvim "+set si"'
elif [[ -x "$(command -v vim)" ]]; then
    alias vi='vim'
    alias svi='sudo vim'
    alias vis='vim "+set si"'
fi

# IP Addresses
if command -v ip &>/dev/null; then
    alias iplocal="ip -br -c a"
else
    alias iplocal="ifconfig | grep -Eo 'inet (addr:)?([0-9]*\.){3}[0-9]*' | grep -Eo '([0-9]*\.){3}[0-9]*' | grep -v '127.0.0.1'"
fi

if command -v curl &>/dev/null; then
    alias ipexternal="curl -s ifconfig.me && echo"
elif command -v wget &>/dev/null; then
    alias ipexternal="wget -qO- ifconfig.me && echo"
fi

# ==============================================================================
# 9. FUNÇÕES PERSONALIZADAS
# ==============================================================================

# Função que aceita cópia de múltiplos arquivos
function copy() {
    # Verifica dependência
    if ! command -v xclip &> /dev/null; then
        echo "❌ xclip não instalado. Execute: sudo pacman -S xclip"
        return 1
    fi
    
    # Caso 1: Dados via pipe
    if [ $# -eq 0 ]; then
        if xclip -selection clipboard; then
            echo "✓ Conteúdo copiado da entrada padrão (pipe)"
        else
            echo "❌ Falha ao copiar"
            return 1
        fi
    # Caso 2: Arquivo(s) como argumento
    else
        if cat "$@" | xclip -selection clipboard; then
            echo "✓ Conteúdo de $# arquivo(s) copiado"
        else
            echo "❌ Falha ao copiar arquivo(s)"
            return 1
        fi
    fi
}

# Yazi (File Manager) com troca de diretório ao sair
function y() {
    local tmp="$(mktemp -t "yazi-cwd.XXXXXX")"
    yazi "$@" --cwd-file="$tmp"
    # Usa 'command cat' para evitar alias do bat e garantir leitura pura
    if cwd="$(command cat -- "$tmp")" && [ -n "$cwd" ] && [ "$cwd" != "$PWD" ]; then
        builtin cd -- "$cwd"
    fi
    rm -f -- "$tmp"
}

# Gerenciamento de Pacotes com FZF
function install(){
  pacman -Sl | awk '{print $2" "$3}' | column -t | fzf --reverse --preview 'pacman -Si {1}' | xargs -ro sudo pacman -S
}

function remove(){
  pacman -Qq | fzf --reverse --preview 'pacman -Qi {}' | xargs -ro sudo pacman -Rns
}

function yinstall(){
  yay -Slq | fzf --reverse --preview 'yay -Si {1}' | xargs -ro yay -S
}

function yremove(){
  yay -Qq | fzf --reverse --preview 'yay -Qi {}' | xargs -ro yay -Rns
}

function ysearch(){
  yay -Ss | fzf --reverse --preview 'yay -Si {1}' | awk '{print $1}' | sed 's/\/.*//'
}

# ==============================================================================
# 10. HOOKS (SONS DE SUCESSO/ERRO)
# ==============================================================================
autoload -Uz add-zsh-hook

_first_prompt=true

oks() {
    local s=$?  # Captura o status imediatamente

    # Ignora execução no primeiro prompt ao abrir o terminal
    if [ "$_first_prompt" = true ]; then
        _first_prompt=false
        return
    fi

    if [[ $s -eq 0 ]]; then
        # echo SUCCESS  # Comentado para poluir menos, descomente se quiser ver
        paplay /usr/share/sounds/freedesktop/stereo/complete.oga 2>/dev/null
    else
        echo ERROR: $s
        paplay /usr/share/sounds/freedesktop/stereo/suspend-error.oga 2>/dev/null
    fi
}

add-zsh-hook precmd oks

# ==============================================================================
# 11. CARREGAMENTOS FINAIS
# ==============================================================================

# Fastfetch (Opcional - descomente se quiser ativar)
# if [[ $(tty) == *"pts"* ]]; then
#    fastfetch --config examples/13
# else
#    echo
# fi

# Configuração do Powerlevel10k (Deve ficar próximo ao final)
[[ ! -f ~/.p10k.zsh ]] || source ~/.p10k.zsh

# Dart / Flutter Completion
[[ -f /home/sidiclei/.dart-cli-completion/zsh-config.zsh ]] && . /home/sidiclei/.dart-cli-completion/zsh-config.zsh || true
