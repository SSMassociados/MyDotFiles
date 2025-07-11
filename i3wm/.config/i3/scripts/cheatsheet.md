# i3wm Cheat Sheet - Sidiclei Config

## 🌐 Workspaces e Navegação
| Atalho           | Ação                            |
| ---------------- | ------------------------------- |
| `Mod + 1-0`      | Ir para workspace 1-10          |
| `Mod+Shift+1-0`  | Mover janela para workspace     |
| `Ctrl+Alt+←/→`   | Navegar entre workspaces        |
| `Ctrl+Tab`       | Próximo workspace               |
| `Ctrl+Shift+Tab` | Workspace anterior              |
| `Mod+o`          | Ocultar Polybar                 |
| `Mod+k`          | Limpar janelas urgentes         |
| `Mod+Ctrl+←/→/↑` | Mover workspace entre monitores |

## 🪟 Gerenciamento de Janelas
| Atalho           | Ação                                   |
| ---------------- | -------------------------------------- |
| `Mod+←↑↓→`       | Navegar entre janelas                  |
| `Mod+Shift+←↑↓→` | Mover janelas                          |
| `Mod+Ctrl+←↑↓→`  | Redimensionar janelas                  |
| `Mod+s`          | Layout empilhado                       |
| `Mod+w`          | Layout em abas                         |
| `Mod+e`          | Alternar divisão H/V                   |
| `Mod+.`          | Alternar modo flutuante                |
| `Mod+,`          | Alternar foco tiling/flutuante         |
| `Mod+-`          | Esconder janela (scratchpad)           |
| `Mod+=`          | Mostrar janela oculta                  |
| `Mod+F11`        | Tela cheia                             |
| `Mod+q`          | Fechar janela                          |
| `Mod+Shift+q`    | Fechar TODAS janelas                   |
| `Mod+t`          | Alternar bordas                        |
| `Mod+Shift+h`    | Centralizar janela                     |
| `Mod+;`          | Alternar divisão H/V (janela atual)    |
| `Mod+/`          | Alternar orientação layout             |
| `Mod+Tab`        | Alternar entre layouts                 |
| `Mod+u`          | Focar janela urgente                   |
| `Mod+Ctrl+Del`   | Fechar seletivo (xkill) usando o mouse |
| `Mod+Esc`        | Matar processos travados               |

## 🚀 Aplicativos e Lançadores
| Atalho           | Ação                                                        |
| ---------------- | ----------------------------------------------------------- |
| `Mod+Enter`      | Terminal (Kitty)                                            |
| `F1`             | Desenhar Terminal flutuante                                 |
| `F2`             | Terminal rápido (i3-quickterm)                              |
| `Mod+f`          | Firefox                                                     |
| `Mod+b`          | Brave                                                       |
| `Mod+c`          | Google Chrome                                               |
| `Mod+x`          | Thunar                                                      |
| `Mod+r`          | Ranger                                                      |
| `Mod+d`          | Controles de Sessão "Desligar Reiniciar Suspender Bloquear" |
| `Alt+Space`      | Launcher/Seach Apps                                         |
| `Mod+m`          | Google Meet                                                 |
| `Mod+z`          | SIGE                                                        |
| `Mod+i`          | Cheatsheet (este arquivo)                                   |
| `F11`            | Agendador de alarmes                                        |
| `F6`/`XF86Calc`  | Calculadora                                                 |
| `F9`/`XF86Tools` | RMPC/Spotify                                                |

## 🔧 Utilitários do Sistema
| Atalho        | Ação                                |
| ------------- | ----------------------------------- |
| `Mod+Home`    | Editar config do i3                 |
| `Mod+End`     | Editar config da Polybar            |
| `Mod+'`       | Modo edição rápida de configs       |
| `Mod+Shift+r` | Reiniciar i3                        |
| `Mod+Shift+c` | Recarregar configuração             |
| `Mod+Shift+e` | Sair do i3                          |
| `Mod+Shift+d` | Desligar imediatamente              |
| `Mod+Shift+b` | Reiniciar sistema                   |
| `Mod+Shift+s` | Suspender                           |
| `Mod+Shift+w` | Reiniciar no Windows                |
| `Mod+l`       | Bloquear tela                       |
| `Mod+F4`      | Ativar/Desativar Picom (compositor) |
| `Mod+Shift+t` | Testar notificações do Dunst        |
| `Mod+Shift+x` | Ativar/Desativar Xidlehook          |
| `Mod+Ctrl+h`  | Ajuda do i3 (documentação)          |

## 🖥️ Controles de Tela
| Atalho        | Ação                               |
| ------------- | ---------------------------------- |
| `Print`       | Captura de tela inteira (Scrot)    |
| `Shift+Print` | Captura de janela (Scrot)          |
| `Mod+Print`   | Captura de área (Flameshot)        |
| `Mod+g`       | Gravar tela                        |
| `Mod+F8`      | Espelhamento em um segundo monitor |
| `Alt+o`       | OCR (texto de imagem)              |
| `Alt+q`       | QR code                            |

## 🎵 Controles de Mídia
| Atalho               | Ação                   |
| -------------------- | ---------------------- |
| `XF86AudioPlay`      | Play/Pause             |
| `XF86AudioNext`      | Próxima faixa          |
| `XF86AudioPrev`      | Faixa anterior         |
| `XF86AudioRaiseVol`  | Aumentar volume (+10%) |
| `XF86AudioLowerVol`  | Diminuir volume (-10%) |
| `XF86AudioMute`      | Mudo                   |
| `XF86MicMute`        | Mudo no microfone      |
| `XF86MonBrightness↑` | Aumentar brilh+do      |
| `XF86MonBrightness↓` | Diminuir brilho        |

## 📱 Dispositivos e Conexões
| Atalho       | Ação                          |
| ------------ | ----------------------------- |
| `Mod+PIPE`   | KDE Connect                   |
| `Mod+Ctrl+b` | Bluetooth (Blueman)           |
| `F5`         | UPnP (djmount)                |
| `F7`         | Gnirehtet (Reverse Tethering) |
| `F8`         | Scrcpy (Espelhamento Android) |

## 🛠️ Modos Especiais
### Modo Edição de Arquivos (`Mod+'`)
| Tecla | Arquivo Editado              |
| ----- | ---------------------------- |
| `i`   | ~/.config/i3/config          |
| `p`   | ~/.config/polybar/config.ini |
| `k`   | ~/.config/kitty/kitty.conf   |
| `b`   | ~/.config/betterlockscreenrc |
| `d`   | ~/.config/dunst/dunstrc      |
| `o`   | ~/.config/picom/picom.conf   |
| `f`   | ~/.config/feh/themes         |
| `z`   | ~/.zshrc                     |
| `n`   | ~/.config/nvim/init.vim      |
| `t`   | ~/.config/zathura/zathurarc  |
| `s`   | /etc/samba/smb.conf          |

### Notificações (Dunst)
| Atalho             | Ação                       |
| ------------------ | -------------------------- |
| `Ctrl+Space`       | Fechar notificação         |
| `Ctrl+Shift+Space` | Fechar todas notificações  |
| `Ctrl+,`           | Mostrar última notificação |
| `Ctrl+.`           | Abrir contexto/link        |

## 🖱️ Controles do Mouse
| Ação do Mouse       | Comportamento           |
| ------------------- | ----------------------- |
| `Botão Meio`        | Fechar janela           |
| `Mod+Botão Meio`    | Forçar fechar janela    |
| `Mod+Botão Direito` | Alternar modo flutuante |
| `Scroll Esquerdo`   | Mover janela ←          |
| `Scroll Direito`    | Mover janela →          |

## 🔄 Layouts Salvos
| Atalho       | Ação                                |
| ------------ | ----------------------------------- |
| `Mod+Ctrl+1` | Carregar Layout 1 (Workspace 7)     |
| `Mod+Ctrl+2` | Carregar Layout 2 (Workspace atual) |
| `F12`        | Gerenciar layouts salvos            |

## 🎨 Aparência
| Atalho        | Ação                         |
| ------------- | ---------------------------- |
| `Mod+Shift+g` | Modo de configuração de gaps |
| `Mod+Shift+o` | Alternar bordas inteligentes |
| `Mod+Shift+i` | Alternar gaps inteligentes   |

## ✨ Recursos Especiais
| Atalho        | Ação                         |
| ------------- | ---------------------------- |
| `Mod+a`       | Alternar alarme              |
| `Mod+Shift+a` | Agendador de alarmes Escolar |
| `Mod+Shift+z` | Pesquisa avançada            |
