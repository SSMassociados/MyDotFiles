# Dotfiles

Este repositório contém minhas configurações  pessoais (dotfiles) para vários aplicativos e ambientes. As  configurações são gerenciadas usando o `GNU Stow` para criar links simbólicos de forma organizada.

## Estrutura do Repositório

Aqui está uma visão geral da estrutura do repositório:

```
.
├── bashrc                  # Configurações do Bash
├── betterlockscreen        # Configurações do Betterlockscreen
├── dunst                   # Configurações do Dunst (notificações)
├── feh                     # Configurações do Feh (visualizador de imagens)
├── fonts                   # Fontes personalizadas
├── fzf                     # Configurações do FZF (fuzzy finder)
├── geany                   # Configurações do Geany (editor de texto)
├── gestures                # Configurações de gestos de touchpad
├── git                     # Configurações específicas do Git
├── gitconfig               # Arquivo de configuração global do Git
├── gtk-2.0                 # Configurações do GTK 2.0
├── gtk-3.0                 # Configurações do GTK 3.0
├── gtk-4.0                 # Configurações do GTK 4.0
├── gtkrc-2.0               # Configurações específicas do GTK 2.0
├── i3wm                    # Configurações do i3 Window Manager
├── icons                   # Ícones personalizados
├── kitty                   # Configurações do terminal Kitty
├── LICENSE                 # Licença do repositório
├── mime                    # Configurações de tipos MIME
├── mpv                     # Configurações do player de mídia MPV
├── nvim                    # Configurações do Neovim (editor de texto)
├── nwg-look                # Configurações do utilitário de aparência
├── oh-my-zsh               # Configurações do Oh My Zsh
├── picon                   # Ícones personalizados
├── polybar                 # Configurações da barra de status Polybar
├── qBittorrent             # Configurações do qBittorrent
├── qt5ct                   # Configurações do Qt5 Configuration Tool
├── qt6ct                   # Configurações do Qt6 Configuration Tool
├── qutebrowser             # Configurações do navegador Qutebrowser
├── ranger                  # Configurações do gerenciador de arquivos Ranger
├── rofi                    # Configurações do launcher Rofi
├── themes                  # Temas personalizados
├── Thunar                  # Configurações do gerenciador de arquivos Thunar
├── user-dirs               # Configurações de diretórios de usuário
├── wal                     # Configurações do Pywal (gerenciador de cores)
├── wallpaper               # Papéis de parede personalizados
├── xbindkeys               # Configurações de atalhos de teclado
├── Xdefault                # Configurações padrão do servidor X
├── xinitrc                 # Script de inicialização do Xorg
├── Xmodmap                 # Configurações de mapeamento de teclado
├── xsettingsd              # Configurações do daemon de configurações do X
├── zathura                 # Configurações do visualizador de documentos Zathura
└── zshrc                   # Configurações do Zsh
```

## Como Usar

### Pré-requisitos

- **Git**: Para clonar e sincronizar o repositório.
- **GNU Stow**: Para gerenciar links simbólicos das configurações.

Instale o `GNU Stow` se ainda não o tiver:

```
sudo apt install stow  # Para sistemas baseados em Debian/Ubuntu
sudo pacman -S stow    # Para sistemas baseados em Arch
```

### Clonando o Repositório

Clone este repositório em seu diretório home:

```
git clone https://github.com/seu-usuario/dotfiles.git ~/.dotfiles
cd ~/.dotfiles
```

### Aplicando Configurações com GNU Stow

Para aplicar as configurações de um diretório específico (por exemplo, `nvim`), use o comando:

```
stow nvim
```

Isso criará links simbólicos dos arquivos no diretório `nvim` para o local apropriado no seu `$HOME`.

Para aplicar todas as configurações de uma vez:

```
stow */
```

### Removendo Configurações

Para remover os links simbólicos de um diretório específico (por exemplo, `nvim`), use:

```
stow -D nvim
```

Para remover todas as configurações:

```
stow -D */
```

### Sincronizando com Git

Para manter suas configurações atualizadas em várias máquinas, use o Git para sincronizar:

1. Faça commit das mudanças:

   ```
   git add .
   git commit -m "Atualizando configurações"
   git push origin main
   ```
   
2. Em outra máquina, puxe as mudanças:

   ```
   git pull origin main
   ```

## Licença

Este repositório está licenciado sob a licença especificada no arquivo [LICENSE](https://LICENSE).

------

### Personalização

- Substitua `https://github.com/seu-usuario/dotfiles.git` pelo URL do seu repositório real.
- Adicione ou remova seções conforme necessário para refletir suas configurações e fluxo de trabalho.

Esse `README.md` deve fornecer uma boa documentação para você e para qualquer pessoa que queira usar ou contribuir com seu repositório de dotfiles. 😊