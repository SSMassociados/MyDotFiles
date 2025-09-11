# Dotfiles

Este repositório armazena minhas configurações pessoais (dotfiles) para diversos aplicativos e ambientes. Sou usuário de **Arch Linux** com **i3wm**, e as configurações são gerenciadas com `GNU Stow`, permitindo uma gestão organizada por meio de links simbólicos.

------

## 📂 Estrutura do Repositório

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

------

## 🧹 Limpeza de Configurações Antigas (Opcional)

Recomenda-se remover configurações antigas antes de aplicar os novos dotfiles para evitar conflitos. **Faça backup antes de executar estes comandos!**

### Limpeza de arquivos na home directory:

```
rm -v ~/.{zshrc,bashrc,wallpaper,xinitrc,gitconfig} 2>/dev/null
```

### Limpeza de diretórios no .config:
```
rm -rfv ~/.config/{betterlockscreen,dunst,feh,gtk-{3.0,4.0},.gtkrc-2.0,i3,kitty,mimeapps.list,nvim,picom,polybar,qBittorrent,qt{5,6}ct,qutebrowser,ranger,rofi,xsettingsd,zathura,geany} 2>/dev/null
```

### Limpeza de recursos compartilhados:
```
rm -rfv ~/.local/share/{fonts,icons,themes} 2>/dev/null
```

------

## 🛠 Como Usar

### Pré-requisitos

```
sudo pacman -S stow    # Arch Linux
sudo apt install stow  # Debian/Ubuntu
```

### Clonagem

```
git clone https://github.com/seu-usuario/dotfiles.git ~/.dotfiles
cd ~/.dotfiles
```

------

## ⚠️ Importante: Sempre Simule Antes!

Use `-n` (dry-run) e `-v` (verbose) antes de qualquer operação:

### Aplicar Configurações

```
# Para pacotes específicos (ex: dunst picom):
stow -nv -d ~/.dotfiles -t ~ dunst picom  # Simula
stow -v -d ~/.dotfiles -t ~ dunst picom   # Executa

# Para todos os dotfiles:
stow -nv -d ~/.dotfiles -t ~ */           # Simula
stow -v -d ~/.dotfiles -t ~ */            # Executa
```

### Remover Configurações

```
# Pacote específico:
stow -nv -d ~/.dotfiles -t ~ -D dunst picom  # Simula
stow -v -d ~/.dotfiles -t ~ -D dunst picom   # Executa

# Todos os dotfiles:
cd ~/.dotfiles && stow -nvD -t ~ */       # Simula
cd ~/.dotfiles && stow -vD -t ~ */        # Executa
```

### Reconstruir Links (-R)

```
# Pacote específico::
cd ~/.dotfiles && stow -R -t ~ dunst picom

# # Todos os dotfiles,com flags:
cd ~/.dotfiles && stow -Rv -t ~ */   # Com verbose
cd ~/.dotfiles && stow -Rn -t ~ */   # Dry-run
```

------



| Opção         | Significado                                                  |
| ------------- | ------------------------------------------------------------ |
| `-t <target>` | Define o **diretório de destino** dos links simbólicos. Ex.: `-t ~` cria links no seu home. |
| `-R`          | **Recria links existentes**. Se algum link já existe, ele é atualizado/reescrito. |
| `-v`          | **Verbose** — mostra detalhadamente o que o Stow está fazendo (útil para debug). |
| `-n`          | **No-action / dry run** — simula as ações, mostra o que seria feito **sem alterar nada**. |
| `-D`          | **Delete** — desfaz links simbólicos criados anteriormente pelo Stow, removendo os links do destino. |

💡 **Dicas de uso combinado:**

- `-nv` → apenas simula e mostra detalhes, sem mexer em nada.
- `-R -v -t ~` → aplica/recria os links no seu home, mostrando detalhes.
- `-nvD` → simula a remoção de links, sem deletar nada de fato.



💡 **Dicas de uso combinado:**

- `-nv` → apenas simula e mostra detalhes, sem mexer em nada.
- `-R -v -t ~` → aplica/recria os links no seu home, mostrando detalhes.
- `-nvD` → simula a remoção de links, sem deletar nada de fato.

## 🔄 Sincronização com Git

```
# Atualizar:
git add .
git commit -m "Atualização das configurações"
git push origin main

# Em outra máquina:
git pull origin main
```

------

## 📜 Licença

Este repositório está licenciado sob os termos especificados no arquivo [LICENSE](https://github.com/SSMassociados/MyDotFiles/blob/main/LICENSE).

## Personalização

- Substitua `https://github.com/seu-usuario/dotfiles.git` pelo URL correto do seu repositório.

---

