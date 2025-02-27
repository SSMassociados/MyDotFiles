# Dotfiles

Este repositório armazena minhas configurações pessoais (dotfiles) para diversos aplicativos e ambientes. Sou usuário de **Arch Linux** com **i3wm**, e as configurações são gerenciadas com `GNU Stow`, permitindo uma gestão organizada por meio de links simbólicos.

## Estrutura do Repositório

Abaixo está a organização dos arquivos e diretórios:

```
.
├── bashrc                     # Configurações do Bash
├── betterlockscreen           # Configurações do Betterlockscreen
├── dunst                      # Notificações (Dunst)
├── feh                        # Visualizador de imagens (Feh)
├── fonts                      # Fontes personalizadas
├── fzf                        # Fuzzy Finder (FZF)
├── geany                      # Editor de texto (Geany)
├── gestures                   # Gestos para touchpad
├── git                        # Configurações do Git
├── gitconfig                  # Arquivo global do Git
├── gtk-2.0, gtk-3.0, gtk-4.0  # Temas e configurações GTK
├── i3wm                       # Configurações do i3wm
├── icons                      # Ícones personalizados
├── kitty                      # Terminal Kitty
├── LICENSE                    # Licença do repositório
├── mime                       # Configurações de tipos MIME
├── mpv                        # Player de mídia MPV
├── nvim                       # Editor de texto Neovim
├── oh-my-zsh                  # Configurações do Oh My Zsh
├── polybar                    # Barra de status Polybar
├── qBittorrent                # Configurações do qBittorrent
├── qt5ct, qt6ct               # Ferramentas de configuração Qt
├── qutebrowser                # Navegador Qutebrowser
├── ranger                     # Gerenciador de arquivos Ranger
├── rofi                       # Launcher Rofi
├── themes                     # Temas personalizados
├── Thunar                     # Gerenciador de arquivos Thunar
├── wal                        # Pywal (gerenciador de cores)
├── wallpaper                  # Papéis de parede
├── xbindkeys                  # Atalhos de teclado
├── xinitrc                    # Inicialização do Xorg
├── Xmodmap                    # Mapeamento de teclado
├── xsettingsd                 # Daemon de configurações do X
├── zathura                    # Visualizador de documentos Zathura
└── zshrc                      # Configurações do Zsh
```

## Como Usar

### Requisitos

- **Git**: Para clonar e sincronizar o repositório.
- **GNU Stow**: Para gerenciar links simbólicos.

Instale o `GNU Stow` conforme sua distribuição:

```bash
sudo pacman -S stow    # Arch Linux
sudo apt install stow  # Para sistemas baseados em Debian/Ubuntu
```

### Clonando o Repositório

Clone o repositório e navegue até a pasta:

```bash
git clone https://github.com/seu-usuario/dotfiles.git ~/.dotfiles
cd ~/.dotfiles
```

### Aplicando Configurações com Stow

Para aplicar configurações específicas (exemplo: `nvim`):

```bash
stow nvim
```

Para aplicar todas as configurações:

```bash
stow */
```

### Removendo Configurações

Para desfazer links simbólicos de um diretório específico:

```bash
stow -D nvim
```

Para remover todas as configurações:

```bash
stow -D */
```

### Sincronizando com Git

Para manter suas configurações sempre atualizadas:

```bash
git add .
git commit -m "Atualização das configurações"
git push origin main
```

Em outra máquina, basta puxar as mudanças:

```bash
git pull origin main
```

## Licença

Este repositório está licenciado sob os termos especificados no arquivo [LICENSE](https://github.com/SSMassociados/MyDotFiles/blob/main/LICENSE).

## Personalização

- Substitua `https://github.com/seu-usuario/dotfiles.git` pelo URL correto do seu repositório.
- Adicione/remova seções conforme sua necessidade.

---

Com essa estrutura, o `README.md` fica mais direto e fácil de entender, ajudando qualquer usuário (inclusive você no futuro) a configurar rapidamente o ambiente. 😊