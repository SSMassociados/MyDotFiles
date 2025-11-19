#!/bin/bash
echo "🚀 Instalando vim-plug..."
sh -c 'curl -fLo "${XDG_DATA_HOME:-$HOME/.local/share}"/nvim/site/autoload/plug.vim --create-dirs \
       https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim'

echo "📦 Instalando plugins..."
nvim --headless +PlugInstall +qall

echo "🔄 Atualizando plugins..."
nvim --headless +PlugUpdate +qall

echo "✅ Neovim configurado com sucesso!"
