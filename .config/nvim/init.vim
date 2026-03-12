set runtimepath^=~/.vim runtimepath+=~/.vim/after
let &packpath = &runtimepath
source ~/.vimrc

let s:plug_vim_data = stdpath('data') . '/site/autoload/plug.vim'
let s:plug_vim_vim = expand('~/.vim/autoload/plug.vim')

if !filereadable(s:plug_vim_data) && !filereadable(s:plug_vim_vim) && executable('curl')
  silent execute '!curl -fLo ' . shellescape(s:plug_vim_data) . ' --create-dirs https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim'
  autocmd VimEnter * ++once PlugInstall --sync | source $MYVIMRC
endif

if filereadable(s:plug_vim_data) || filereadable(s:plug_vim_vim)
  call plug#begin(stdpath('data') . '/plugged')

" Fuzzy Finder
  Plug 'nvim-lua/plenary.nvim'
  Plug 'nvim-telescope/telescope.nvim', { 'tag': '0.1.0' }

  Plug 'preservim/nerdtree'
  Plug 'dense-analysis/ale'
  Plug 'preservim/nerdcommenter'
  Plug 'tpope/vim-fugitive'
  Plug 'tpope/vim-surround'
  Plug 'airblade/vim-gitgutter'
  Plug 'vim-airline/vim-airline'
  Plug 'vim-airline/vim-airline-themes'
  call plug#end()
else
  echohl WarningMsg
  echom 'vim-plug is not installed; starting without plugins'
  echohl None
endif
