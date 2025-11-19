-- ==============================================================================
-- PLUGINS - GERENCIADOR VIM-PLUG
-- ==============================================================================
vim.cmd [[
  call plug#begin()

  " 📝 Melhorias de Edição e Syntax
  Plug 'nvim-treesitter/nvim-treesitter', {'do': ':TSUpdate'}
  Plug 'cohama/lexima.vim'

  " 🎨 Interface e Temas
  Plug 'nvim-lualine/lualine.nvim'
  Plug 'rose-pine/neovim', { 'as': 'rose-pine' }
  Plug 'nvim-tree/nvim-web-devicons'
  Plug 'rcarriga/nvim-notify'
  Plug 'projekt0n/github-nvim-theme'

  " 🚀 Funcionalidades Avançadas
  Plug 'neoclide/coc.nvim', {'branch': 'release'}
  Plug 'voldikss/vim-floaterm'
  Plug 'NvChad/nvim-colorizer.lua'

  " 📁 Navegação e Estrutura
  Plug 'nvim-tree/nvim-tree.lua'
  Plug 'lukas-reineke/indent-blankline.nvim'

  " 🔧 Linguagens Específicas
  Plug 'linux-cultist/venv-selector.nvim'
  Plug 'mracos/mermaid.vim'

  call plug#end()
]]

-- ==============================================================================
-- CONFIGURAÇÕES ESPECÍFICAS DE PLUGINS
-- ==============================================================================

-- 🌳 Treesitter - Syntax moderna
require("nvim-treesitter.configs").setup {
  ensure_installed = { "lua", "bash", "python", "json", "javascript", "typescript" },
  sync_install = false,
  auto_install = true,
  highlight = { 
    enable = true,
    additional_vim_regex_highlighting = false,
  },
  indent = { enable = true }
}

-- 🎨 nvim-colorizer.lua - Realce de cores hexadecimais
require("colorizer").setup({
  filetypes = { "*" },
  user_default_options = {
    RGB = true,
    RRGGBB = true,
    names = true,
    RRGGBBAA = true,
    rgb_fn = true,
    hsl_fn = true,
    css = true,
    css_fn = true,
    mode = "background",
  },
})

-- 🌳 nvim-tree - Explorador de arquivos (configuração atualizada)
require("nvim-tree").setup({
  view = {
    width = 30,
  },
  renderer = {
    icons = {
      glyphs = {
        default = "",
        symlink = "",
      },
    },
  },
  actions = {
    open_file = {
      window_picker = {
        enable = true,
      },
    },
  },
})
vim.keymap.set("n", "<F5>", ":NvimTreeToggle<CR>", { noremap = true, silent = true })

-- 🚀 coc.nvim - Auto-completar inteligente
vim.g.coc_global_extensions = {
  'coc-json',
  'coc-tsserver', 
  'coc-pyright',
  'coc-sh',
  'coc-lua'
}

-- Configurações adicionais do coc (CORRIGIDO)
vim.api.nvim_create_autocmd("CursorHold", {
  pattern = "*",
  callback = function()
    vim.fn.CocActionAsync('highlight')
  end,
})

-- 🔔 nvim-notify - Sistema de notificações
require("notify").setup({
  timeout = 3000,
  background_colour = "#000000",
  stages = "fade_in_slide_out",
})

-- ✈️ lualine - Barra de status
require("lualine").setup {
  options = {
    theme = "auto",
    section_separators = { "", "" },
    component_separators = { "", "" },
  }
}

-- 📏 indent-blankline.nvim v3 (configuração correta)
require("ibl").setup({
  indent = {
    char = "│",
  },
  scope = {
    enabled = true,
    show_start = false,
    show_end = false,
  },
})

-- 🐚 floaterm - Terminal flutuante
vim.g.floaterm_width = 0.8
vim.g.floaterm_height = 0.8

-- ==============================================================================
-- CONFIGURAÇÕES GERAIS DO EDITOR
-- ==============================================================================

-- 🔧 Interface do Usuário
vim.opt.cursorline = true
vim.opt.number = true
vim.opt.relativenumber = true
vim.opt.mouse = "a"
vim.opt.title = true
vim.opt.ttimeoutlen = 10
vim.opt.background = "dark"
vim.opt.termguicolors = true

-- Tentar carregar rose-pine, fallback para padrão
local status, _ = pcall(vim.cmd.colorscheme, "rose-pine")
if not status then
  vim.cmd.colorscheme("desert")
end

-- 🔍 Pesquisa
vim.opt.hlsearch = true
vim.opt.ignorecase = true
vim.opt.incsearch = true
vim.opt.smartcase = true

-- ⚡ Desempenho
vim.opt.autowrite = true

-- 📝 Renderização de Texto
vim.opt.display:append("lastline")
vim.opt.spell = true
vim.opt.spelllang = { "pt", "en" }
vim.opt.linebreak = true
vim.opt.scrolloff = 3
vim.opt.sidescrolloff = 5
vim.opt.wrap = true

-- 📐 Recuo e Indentação
vim.opt.autoindent = true
vim.opt.expandtab = true
vim.opt.shiftround = true
vim.opt.shiftwidth = 2
vim.opt.smarttab = true
vim.opt.tabstop = 2

-- 💾 Comportamento
vim.opt.hidden = true
vim.opt.showmatch = true

-- 📋 Área de Transferência (CORRIGIDO)
if vim.fn.has('wsl') == 1 then
  -- Configuração para WSL usando a nova API de clipboard
  vim.opt.clipboard = "unnamedplus"
else
  vim.opt.clipboard = "unnamedplus"
end

vim.opt.completeopt = { "menuone", "noselect" }

-- 🖥️ Layout e Janelas
vim.opt.inccommand = "split"
vim.opt.splitbelow = true
vim.opt.splitright = true

-- ==============================================================================
-- MAPEAMENTOS DE TECLAS (KEYBINDS)
-- ==============================================================================

-- 💾 Operações Básicas
vim.keymap.set("n", "<C-s>", ":w!<CR>", { noremap = true, silent = true })
vim.keymap.set("n", "<C-q>", ":qa<CR>", { noremap = true, silent = true })
vim.keymap.set("n", "<F4>", ":bd<CR>", { noremap = true, silent = true })

-- 📁 Navegação entre Buffers
vim.keymap.set("n", "<F1>", ":bprevious<CR>", { noremap = true, silent = true })
vim.keymap.set("n", "<F2>", ":bnext<CR>", { noremap = true, silent = true })

-- 🐚 Terminal Flutuante
vim.keymap.set("n", "<F8>", ":FloatermToggle<CR>", { noremap = true, silent = true })

-- 🐚 Cabeçalho Automático para Shell Script
vim.keymap.set("n", "<F9>", function()
  local filename = vim.fn.expand("%:t")
  local lines = {
    "#!/bin/bash",
    "#",
    "# " .. filename,
    "#",
    "# Versão: 1.0",
    "# Script para: ",
    "# Autor: " .. (os.getenv("USER") or "Seu Nome"),
    "#"
  }
  vim.api.nvim_buf_set_lines(0, 0, 0, false, lines)
  vim.api.nvim_win_set_cursor(0, {7, 11})  
end, { noremap = true, silent = true })

-- 📋 Manipulação de Texto
vim.keymap.set("n", "<S-Down>", ":m .+1<CR>==", { noremap = true, silent = true })
vim.keymap.set("n", "<S-Up>", ":m .-2<CR>==", { noremap = true, silent = true })
vim.keymap.set("v", "<C-c>", '"+y', { noremap = true, silent = true })
vim.keymap.set("v", "<C-v>", '"+p', { noremap = true, silent = true })

-- 🚀 coc.nvim - Navegação de Código
vim.keymap.set("n", "gd", "<Plug>(coc-definition)", { silent = true })
vim.keymap.set("n", "gy", "<Plug>(coc-type-definition)", { silent = true })
vim.keymap.set("n", "gi", "<Plug>(coc-implementation)", { silent = true })
vim.keymap.set("n", "gr", "<Plug>(coc-references)", { silent = true })

-- Atalhos úteis para coc
vim.keymap.set("n", "<leader>rn", "<Plug>(coc-rename)", {})
vim.keymap.set("x", "<leader>f", "<Plug>(coc-format-selected)", {})
vim.keymap.set("n", "<leader>f", "<Plug>(coc-format)", {})

-- ==============================================================================
-- AUTOCOMANDOS E FINALIZAÇÃO
-- ==============================================================================

-- 📦 Instalação Automática de Plugins
vim.cmd [[
  augroup PlugInstallOnStart
    autocmd!
    autocmd VimEnter *
      \  if len(filter(values(g:plugs), '!isdirectory(v:val.dir)'))
      \|   PlugInstall --sync | q
      \| endif
  augroup END
]]

-- Autocomandos úteis
vim.cmd [[
  " Limpar espaços em branco no final ao salvar
  autocmd BufWritePre * %s/\s\+$//e

  " Manter cursor position ao recarregar
  autocmd BufReadPost *
    \ if line("'\"") >= 1 && line("'\"") <= line("$") |
    \   execute "normal! g`\"" |
    \ endif
]]
