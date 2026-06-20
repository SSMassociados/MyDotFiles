# Dotfiles

Este repositório armazena minhas configurações pessoais (dotfiles) para diversos aplicativos e ambientes. Sou usuário de **Arch Linux** com **i3wm**, e as configurações são gerenciadas com `GNU Stow`, permitindo uma gestão organizada por meio de links simbólicos.

---

## 📂 Estrutura do Repositório

```
.dotfiles
├── autorandr          # Configuração automática de monitores (autorandr)
├── bashrc             # Configurações do Bash
├── betterlockscreen   # Tela de bloqueio (betterlockscreen)
├── btop               # Monitor de recursos (btop)
├── dunst              # Notificações (dunst)
├── feh                # Visualizador de imagens e wallpaper (feh)
├── flameshot          # Captura de tela (flameshot)
├── fonts              # Fontes personalizadas (~/.local/share/fonts)
├── geany              # Editor de texto (geany)
├── gestures           # Gestos para touchpad (libinput-gestures)
├── gitconfig          # Configuração global do Git (~/.gitconfig)
├── gtk-3.0            # Tema e configurações GTK 3
├── gtk-4.0            # Tema e configurações GTK 4
├── gtkrc-2.0          # Tema e configurações GTK 2
├── i3wm               # Configurações do i3wm (config, módulos, scripts, sons)
├── icons              # Ícones personalizados (~/.local/share/icons)
├── keepassxc          # Gerenciador de senhas (keepassxc)
├── kitty              # Terminal kitty (config + coleção de temas)
├── kvantum            # Estilo Qt via Kvantum
├── mime               # Associações de tipos MIME
├── mpd                # Player de música (mpd)
├── nvim               # Editor Neovim (init.lua / coc)
├── nwg-look           # Configurador de aparência GTK (nwg-look)
├── oh-my-zsh          # Framework Oh My Zsh (submódulo git)
├── picom              # Compositor (picom)
├── polybar            # Barra de status (polybar + scripts)
├── portal             # Configuração xdg-desktop-portal
├── qbittorrent        # Cliente BitTorrent (qBittorrent)
├── qt5ct              # Configurador de aparência Qt5
├── qt6ct              # Configurador de aparência Qt6
├── quickterm          # Terminal dropdown (i3-quickterm)
├── qutebrowser        # Navegador (qutebrowser)
├── ranger             # Gerenciador de arquivos (ranger)
├── redshift           # Ajuste de temperatura de cor (redshift)
├── rofi               # Launcher e menus (rofi + applets + temas)
├── systemd            # Serviços de usuário systemd
├── themes             # Temas GTK (~/.local/share/themes)
├── thunar             # Gerenciador de arquivos (thunar + scripts de contexto)
├── TUTORIAIS          # Tutoriais e anotações diversas
├── user               # Foto de perfil (~/.face)
├── user-dirs          # Diretórios padrão do usuário (xdg-user-dirs)
├── wallpaper          # Papéis de parede (~/.wallpaper)
├── xfce4              # Configurações herdadas do xfce4
├── xinitrc            # Inicialização do Xorg (~/.xinitrc)
├── xorg               # Configurações do Xorg (/etc/X11/xorg.conf.d)
├── xprofile           # Perfil do Xorg (~/.xprofile)
├── xresources         # Recursos do X (~/.Xresources)
├── xsettingsd         # Daemon de configurações do X (xsettingsd)
├── yazi               # Gerenciador de arquivos moderno (yazi)
├── zathura            # Visualizador de documentos (zathura)
└── zsh                # Configurações do Zsh (.zshrc, .p10k.zsh, fzf, plugins)
```

---

## 🖥️ Destaques do Setup

- **WM:** i3wm com polybar, rofi e picom
- **Shell:** Zsh + Oh My Zsh + Powerlevel10k + fzf + autosuggestions + syntax-highlighting
- **Terminal:** Kitty (com +150 temas disponíveis)
- **Editor:** Neovim (init.lua) + Geany
- **Temas:** pywal para geração dinâmica de cores integrado ao dunst, polybar e wallpaper
- **Fontes:** Coleção ampla incluindo Nerd Fonts (JetBrains, Iosevka, FiraCode, Hack, etc.)
- **Scripts i3:** automação de wallpaper, scrcpy, barcode scan, QR code, notificações, monitor de bateria, entre outros

---

## 🧹 Limpeza de Configurações Antigas (Opcional)

Recomenda-se remover configurações antigas antes de aplicar os novos dotfiles para evitar conflitos. **Faça backup antes de executar estes comandos!**

### Arquivos na home:

```bash
rm -v ~/.{zshrc,bashrc,xinitrc,xprofile,Xresources,gitconfig,gtkrc-2.0,face,fzf.zsh,p10k.zsh} 2>/dev/null
```

### Diretórios no ~/.config:

```bash
rm -rfv ~/.config/{autorandr,betterlockscreen,btop,dunst,feh,flameshot,geany,i3,keepassxc,kitty,Kvantum,libinput-gestures.conf,mimeapps.list,mpd,nwg-look,nvim,picom,polybar,portal,qBittorrent,qt5ct,qt6ct,i3-quickterm,qutebrowser,ranger,redshift,rofi,systemd/user,Thunar,user-dirs.dirs,xdg-desktop-portal,xsettingsd,yazi,zathura,gtk-3.0,gtk-4.0} 2>/dev/null
```

### Recursos compartilhados:

```bash
rm -rfv ~/.local/share/{fonts,icons,themes} 2>/dev/null
```

### Configuração do Xorg (requer sudo):

```bash
sudo rm -v /etc/X11/xorg.conf.d/30-touchpad.conf 2>/dev/null
```

---

## 🛠 Como Usar

### Pré-requisitos

```bash
sudo pacman -S stow    # Arch Linux
sudo apt install stow  # Debian/Ubuntu
```

### Clonagem

```bash
git clone https://github.com/SSMassociados/MyDotFiles.git ~/.dotfiles
cd ~/.dotfiles
```

### Ignorar Pacotes com `.stow-local-ignore`

Para excluir pacotes permanentemente do Stow (sem precisar filtrá-los manualmente toda vez), crie o arquivo `.stow-local-ignore` na raiz do repositório:

```bash
nano ~/.dotfiles/.stow-local-ignore
```

Adicione os pacotes a ignorar, um por linha (formato regex):

```
^gtk-4\.0$
^xorg$
^TUTORIAIS$
```

A partir daí, o comando `stow -Rv -t ~ */` já os ignora automaticamente, sem necessidade de filtros extras.

Para ignorar pontualmente (sem salvar a regra), filtre na linha de comando:

```bash
stow -Rv -t ~ $(ls -1d ~/.dotfiles/*/ | xargs -n1 basename | grep -Ev '^(gtk-4\.0|xorg|TUTORIAIS)$' | tr '\n' ' ')
```

| Abordagem             | Quando usar                                              |
| --------------------- | -------------------------------------------------------- |
| `.stow-local-ignore`  | Exclusão permanente — pacotes que nunca devem ser linkados via stow |
| `grep -Ev` no comando | Exclusão pontual, sem necessidade de salvar a regra      |

---

## ⚠️ Importante: Sempre Simule Antes!

Use `-n` (dry-run) e `-v` (verbose) antes de qualquer operação.

### Aplicar Configurações

```bash
# Pacotes específicos:
stow -nv -d ~/.dotfiles -t ~ dunst picom    # Simula
stow -v  -d ~/.dotfiles -t ~ dunst picom    # Executa

# Todos os dotfiles:
stow -nv -d ~/.dotfiles -t ~ */             # Simula
stow -v  -d ~/.dotfiles -t ~ */             # Executa
```

### Remover Configurações

```bash
# Pacote específico:
stow -nv -d ~/.dotfiles -t ~ -D dunst picom  # Simula
stow -v  -d ~/.dotfiles -t ~ -D dunst picom  # Executa

# Todos os dotfiles:
cd ~/.dotfiles && stow -nvD -t ~ */          # Simula
cd ~/.dotfiles && stow -vD  -t ~ */          # Executa
```

### Reconstruir Links (-R)

```bash
# Pacote específico:
cd ~/.dotfiles && stow -R -t ~ dunst picom

# Todos os dotfiles:
cd ~/.dotfiles && stow -Rv  -t ~ */    # Com verbose
cd ~/.dotfiles && stow -Rnv -t ~ */    # Dry-run
```

> **Nota:** O pacote `xorg` usa `/etc/X11/xorg.conf.d` como destino e requer `sudo`:
> ```bash
> sudo stow -v -d ~/.dotfiles -t / xorg
> ```

---

## 📋 Referência de Opções do Stow

| Opção         | Significado                                                                 |
| ------------- | --------------------------------------------------------------------------- |
| `-t <target>` | Define o **diretório de destino** dos links simbólicos. Ex.: `-t ~`         |
| `-R`          | **Recria links existentes** — atualiza links que já existem                 |
| `-v`          | **Verbose** — mostra o que o Stow está fazendo                              |
| `-n`          | **Dry-run** — simula as ações sem alterar nada                              |
| `-D`          | **Delete** — remove links simbólicos criados anteriormente pelo Stow        |

💡 **Combinações úteis:**
- `-nv` → simula e mostra detalhes, sem mexer em nada
- `-Rv -t ~` → aplica/recria os links no home com verbose
- `-nvD` → simula a remoção de links sem deletar nada

---

## 🔧 Comandos Úteis

### Listar todos os pacotes do repositório em uma linha

Exibe todos os pacotes em uma linha **e** copia para a área de transferência ao mesmo tempo. Útil para colar direto no comando `stow`:

```bash
ls -1d ~/.dotfiles/*/ | xargs -n1 basename | tr '\n' ' ' | tee >(xclip -selection clipboard); echo
```

### Exportar a árvore completa de arquivos para a área de transferência

Exibe a estrutura do repositório (incluindo arquivos ocultos) **e** copia para a área de transferência ao mesmo tempo:

```bash
/usr/bin/tree ~/.dotfiles -L 5 -a | tee >(xclip -selection clipboard)
```

> **Nota:** use `/usr/bin/tree` para garantir o binário nativo, já que `tree` pode estar mapeado para `lsd` via alias.

---

## 🔄 Sincronização com Git

O alias `dotsync` (definido no `.zshrc`) automatiza o fluxo completo de `add → commit → push`:

```zsh
# Dotfiles Sync
dotsync() {
    cd ~/.dotfiles || { echo "❌ Pasta ~/.dotfiles não encontrada"; return 1; }

    echo "🔄 Entrando em ~/.dotfiles..."
    git status

    if git status --porcelain | grep -q .; then
        git add .
        echo "✅ Arquivos adicionados"

        if [ -z "$1" ]; then
            git commit -m "Atualização automática dos dotfiles"
        else
            git commit -m "$1"
        fi

        git push && echo "🚀 Push realizado com sucesso!"
    else
        echo "✅ Nenhum arquivo modificado."
    fi
}
```

**Uso:**

```bash
dotsync                        # Commit com mensagem automática
dotsync "minha mensagem aqui"  # Commit com mensagem personalizada
```

Em outra máquina, para sincronizar:

```bash
cd ~/.dotfiles && git pull origin main
```

---

## 📜 Licença

Este repositório está licenciado sob os termos especificados no arquivo [LICENSE](https://github.com/SSMassociados/MyDotFiles/blob/main/LICENSE).
