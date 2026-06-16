#!/usr/bin/env sh

case "$1" in
    --clean)
        rm -rf ~/.local/share/Trash/files
        rm -rf ~/.local/share/Trash/info
        mkdir ~/.local/share/Trash/files
        mkdir ~/.local/share/Trash/info
        ;;
    *)
        if [ -r ~/.local/share/Trash/files ];then
            ls ~/.local/share/Trash/files/ | wc -l
        else
            echo "0"
        fi
        ;;
esac
