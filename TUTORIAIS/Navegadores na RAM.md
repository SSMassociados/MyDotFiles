------

## Guia: Navegadores na RAM com `profile-sync-daemon` (Arch Linux)

### 1. Instalação

Instale o pacote e o rsync (necessário para sincronização) via pacman:

```
sudo pacman -S profile-sync-daemon rsync
```

### 2. Configurar Permissões (Sudoers)

Para usar o modo eficiente (**OverlayFS**), o `psd` precisa de permissão root para montar o sistema de arquivos sem pedir senha.

Edite seu arquivo de sudoers personalizado:

```
sudo visudo -f /etc/sudoers.d/sidiclei
```

Certifique-se de que a linha de permissões `NOPASSWD` inclua o helper do overlay. Ela deve ficar assim (adicionando ao final da linha existente):

```
sidiclei ALL=(ALL) NOPASSWD: /usr/bin/grub-reboot, /usr/bin/systemctl reboot, /usr/bin/psd-overlay-helper
```

*Salve e saia (`:wq`).*

### 3. Configuração do PSD

Execute o `psd` uma vez para gerar os arquivos padrão e depois edite:

```
psd
nvim ~/.config/psd/psd.conf
```

Altere/Descomente as seguintes linhas para incluir **Chromium** e **Firefox** e ativar o **OverlayFS**:

```
# Define os navegadores a serem gerenciados
BROWSERS="chromium firefox"

# Ativa o modo OverlayFS (mais rápido e usa menos RAM inicial)
USE_OVERLAYFS="yes"

# (Opcional) Sincronizar antes de suspender (recomendado para notebooks)
# USE_SUSPSYNC="yes"
```

*Salve e saia (`:wq`).*

### 4. Ativação do Serviço

⚠️ **Importante:** Feche **todos** os navegadores (Chromium e Firefox) antes de prosseguir. Se necessário, use `killall chromium firefox`.

1. **Validar configuração:**

   ```
psd p
   ```
   
   *Verifique se a saída lista os dois navegadores e não apresenta erros de permissão.*

2. **Habilitar e Iniciar o Serviço:**

   ```
   systemctl --user enable --now psd
   ```

### 5. Verificação

Abra os navegadores, use um pouco e verifique se o daemon está gerenciando corretamente:

```
psd p
```

- **Status:** deve ser `active`.
- **Overlayfs size:** deve ser maior que 0 (ex: `15M`), indicando que as escritas estão indo para a RAM.

------

### Bônus: Otimizações para Firefox no i3wm

Para deixar o Firefox mais leve e integrado ao seu tiling window manager:

1. **Remover Barra de Título (Ganhar espaço):**
   - *Menu -> Mais ferramentas -> Personalizar barra de ferramentas -> Desmarcar "Barra de título".*
2. **Aceleração de Hardware (VA-API):**
   - Em `about:config`: `media.ffmpeg.vaapi.enabled` -> **true**.
3. **Privacidade e Limpeza:**
   - Em `about:config`:
     - `extensions.pocket.enabled` -> **false** (Remove Pocket)
     - `toolkit.telemetry.enabled` -> **false** (Remove Telemetria)
4. **Navegação via Teclado (Estilo Vim):**
   - Instalar extensão **Vimium** ou **Tridactyl**.

Agora seu sistema está configurado para máxima performance de disco e responsividade nos navegadores!