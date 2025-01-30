call plug#begin()
Plug 'mateusbraga/vim-spell-pt-br'
Plug 'vim-scripts/bash-support.vim'
Plug 'rcarriga/nvim-notify'
Plug 'voldikss/vim-floaterm'
Plug 'sheerun/vim-polyglot'
Plug 'nvim-tree/nvim-web-devicons' " optional, for file icons
Plug 'nvim-tree/nvim-tree.lua'
Plug 'vim-airline/vim-airline'
Plug 'vim-airline/vim-airline-themes'
Plug 'flazz/vim-colorschemes'
Plug 'w0rp/ale'
Plug 'neoclide/coc.nvim', {'branch': 'release'}
Plug 'gorodinskiy/vim-'
Plug 'ryanoasis/vim-devicons'
Plug 'tiagofumo/vim-nerdtree-syntax-highlight'
Plug 'thaerkh/vim-indentguides'
Plug 'cohama/lexima.vim'
call plug#end()

autocmd VimEnter *
  \  if len(filter(values(g:plugs), '!isdirectory(v:val.dir)'))
  \|   PlugInstall --sync | q
  \| endif

" ====== OPÇÕES DE INTERFACE DO USUÁRIO ======
set ruler "Sempre mostra a posição do cursor.
set wildmenu "Mostra um menu mais avançado para sugestões de auto-completar.
set cursorline "Realça a linha atualmente sob o cursor
"set cursorcolumn "
set number "Mostra os números das linhas na barra lateral.
set relativenumber "Mostra as linhas a partir da atual. Útil para auxiliar em comandos que usam mais linhas.
set noerrorbells "Desativa o bipe em caso de erros.
set visualbell "Pisca a tela em vez de apitar em caso de erro.
set mouse=a "Ativa o mouse para rolagem e redimensionamento
set title "Defina o título da janela, refletindo o arquivo atualmente sendo editado.
set ttimeoutlen=0 "Tempo em milissegundos para aceitar comandos.
set background=dark "Use cores que combinem com um fundo escuro.
"set termguicolors
set t_Co=256
colorscheme Monokai

" ====== OPÇÕES DE PESQUISA ======
set hlsearch "Realçar os termos de pesquisa
set ignorecase "Ignora maiúsculas e minúsculas ao pesquisar.
set incsearch "Mostrar correspondências de pesquisa enquanto você digita.
set smartcase "Mude automaticamente a pesquisa para diferenciar maiúsculas de minúsculas quando consulta de pesquisa contém uma letra maiúscula.

" ====== OPÇÕES DE DESEMPENHO ======
set ttyfast "Acelerar a rolagem no Vim
set complete-=i "Limite os arquivos pesquisados ​​para preenchimento automático.
set lazyredraw  "não atualiza a tela durante macro e execução do roteiro.
set autowrite "Salvar arquivos automaticamente antes de abrir outro arquivo

" ====== OPÇÕES DE RENDERIZAÇÃO DE TEXTO ======
set display+=lastline "Sempre tente mostrar a última linha de um parágrafo.
"set spell =pt_br,en "Ativar a verificação ortográfica (talvez seja necessário baixar o pacote de idiomas)
set encoding=UTF-8 "Use uma codificação que suporte Unicode.
set linebreak "Evite quebrar uma linha no meio de uma palavra.
set scrolloff=1 "O número de linhas da tela a serem mantidas acima e abaixo do cursor.
set sidescrolloff=5 "O número de colunas da tela para manter o esquerda e direita do cursor.
"syntax enable "Habilita o realce da sintaxe.
syntax on "Realce de sintaxe exibe o código-fonte em cores diferentes para melhorar sua legibilidade.
set wrap "Habilita quebra de linha.

" ====== OPÇÕES DE RECUO ======
filetype plugin indent on "Ativar regras de recuo que são específico do tipo de arquivo.
set autoindent "Novas linhas herdam o recuo de linhas anteriores
set expandtab "Converte tabulações em espaços.
set shiftround "Ao deslocar linhas, arredonde o recuo para o múltiplo mais próximo de “shiftwidth”
set shiftwidth=2 "Ao deslocar, recue usando dois espaços.
set smarttab " Insere o número “tabstop” de espaços quando a tecla “tab” é pressionado.
set tabstop=2 "Recuar usando dois espaços.

" ====== OPÇÕES DIVERSAS ======
set hidden "Com esta opção definida, suas alterações persistirão no buffer, mas não serão salvas no disco.
set showmatch "Mostre o fechamento de { ( [
set showcmd "Mostra (parcialmente) o status dos comandos

" ====== ÁREA DE TRANSFERÊNCIA ======
set clipboard=unnamedplus "Habilita a área de transferência entre o Vim/Neovim e os demais programas do sistema.
set completeopt=noinsert,menuone,noselect "Modifica o comportamento do menu de auto-completar para se comportar mais como uma IDE.

" ====== TELA/JANELA ======
set inccommand=split "Mostra substituições em uma divisão da janela, antes de aplicar no arquivo.
set splitbelow splitright "Configura o comportamento da divisão da tela com o comando :split (dividir a tela horizontalmente) e :vsplit (verticalmente). Neste caso, as telas sempre se dividirão abaixo da tela atual e à direita.

" Airline config
let g:airline#extensions#tabline#enabled = 1
let g:airline#extensions#tabline#show_buffers = 1
let g:airline#extensions#tabline#switch_buffers_and_tabs = 1
let g:airline#extensions#tabline#tab_nr_type = 1
let g:airline_theme='powerlineish'

" IndentGuides config
let g:indentguides_spacechar = '▏'
let g:indentguides_tabchar = '▏'

" Lexima config
let g:indentguides_spacechar = '▏'
let g:indentguides_tabchar = '▏'

" ====== KEYBINDS ======
" nnoremap– Permite mapear teclas no modo normal.
" inoremap– Permite mapear teclas no modo de inserção.
" vnoremap– Permite mapear chaves no modo visual.

" Salvar o arquivo
nnoremap <C-s> :w!<CR>
" Serve para sair somente
nnoremap <C-q> :qa<CR>
nnoremap <F1> :bprevious<CR>
nnoremap <F2> :bnext<CR>
" Fecha o arquivo aberto.
nnoremap <F4> :bd<CR>
" Mostra ou esconde NERDTree
nnoremap <F5> :NERDTreeToggle<CR>

" F6 para 'ocultar' e F7 volta os comentários do arquivo atual
noremap <F6> :hi Comment ctermfg=black guifg=black<cr>
noremap <F7> :hi Comment term=bold ctermfg=cyan guifg=cyan<cr>

" Abre um terminal em uma janela dividida inferior.
nnoremap <F8> :FloatermToggle<CR>

" Cria o cabecalho padrao para shell script
map <F9> ggO#!/bin/bash
\<c-o>:r!echo %<cr># <c-o>o
\# Versao: <c-o>o
\# Script para:<c-o>o
\# Autor: Sidiclei Sebastião<cr>

nnoremap <silent> <s-Down> :m +1<CR>
nnoremap <silent> <s-Up> :m -2<CR>
vnoremap <C-c> "+y<CR>

