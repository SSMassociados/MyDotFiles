# Setup fzf
# ---------
if [[ ! "$PATH" == */home/sidiclei/.fzf/bin* ]]; then
  PATH="${PATH:+${PATH}:}/home/sidiclei/.fzf/bin"
fi

source <(fzf --zsh)
