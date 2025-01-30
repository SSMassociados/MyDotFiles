#!/bin/bash
#set -ueo pipefail
#set -x

REPO_DIR=$(cd $(dirname $0) && pwd)
SRC_DIR=${REPO_DIR}/src

ROOT_UID=0
DEST_DIR=

# Destination directory
if [ "$UID" -eq "$ROOT_UID" ]; then
  DEST_DIR="/usr/share/themes"
else
  DEST_DIR="$HOME/.themes"
fi

THEME_NAME=Sierra
FLAT_VARIANTS=('' '-compact')
COLOR_VARIANTS=('-light' '-dark')
OPACITY_VARIANTS=('' '-solid')
THIN_VARIANTS=('' '-thin')

usage() {
  printf "%s\n" "Usage: $0 [OPTIONS...]"
  printf "\n%s\n" "OPTIONS:"
  printf "  %-25s%s\n" "-d, --dest DIR" "Specify theme destination directory (Default: ${DEST_DIR})"
  printf "  %-25s%s\n" "-n, --name NAME" "Specify theme name (Default: ${THEME_NAME})"
  printf "  %-25s%s\n" "-o, --opacity VARIANTS" "Specify theme opacity variant(s) [standard|solid] (Default: All variants)"
  printf "  %-25s%s\n" "-c, --color VARIANTS" "Specify theme color variant(s) [light|dark] (Default: All variants)"
  printf "  %-25s%s\n" "-t, --thin VARIANTS" "Specify theme titilebutton variant(s) [standard|thin] (Default: All variants)"
  printf "  %-25s%s\n" "-f, --flat VARIANT" "Specify theme flat compact variant [standard|compact] (Default: All variants)"
  printf "  %-25s%s\n" "-g, --gdm" "Install GDM theme"
  printf "  %-25s%s\n" "-h, --help" "Show this help"
  printf "\n%s\n" "INSTALLATION EXAMPLES:"
  printf "%s\n" "Install all theme variants into ~/.themes"
  printf "  %s\n" "$0 --dest ~/.themes"
  printf "%s\n" "Install all theme variants into ~/.themes including GDM theme"
  printf "  %s\n" "$0 --dest ~/.themes --gdm"
  printf "%s\n" "Install standard theme variant only"
  printf "  %s\n" "$0 --color standard --flat standard"
  printf "%s\n" "Install specific theme variants with different name into ~/.themes"
  printf "  %s\n" "$0 --dest ~/.themes --name MyTheme --color light dark --flat compact"
}

install() {
  local dest=${1}
  local name=${2}
  local flat=${3}
  local color=${4}
  local opacity=${5}
  local thin=${6}

  [[ ${color} == '-light' ]] && local ELSE_LIGHT=${color}
  [[ ${color} == '-dark' ]] && local ELSE_DARK=${color}

  local THEME_DIR=${dest}/${name}${flat}${color}${opacity}${thin}

  [[ -d ${THEME_DIR} ]] && rm -rf ${THEME_DIR}

  echo "Installing '${THEME_DIR}'..."

  mkdir -p                                                                              ${THEME_DIR}
  cp -ur ${REPO_DIR}/COPYING                                                            ${THEME_DIR}

  # Install index.theme
  echo "[Desktop Entry]" >>                                                             ${THEME_DIR}/index.theme
  echo "Type=X-GNOME-Metatheme" >>                                                      ${THEME_DIR}/index.theme
  echo "Name=${name}${flat}${color}${opacity}${thin}" >>                                ${THEME_DIR}/index.theme
  echo "Comment=An Stylish Gtk+ theme based on Elegant Design" >>                       ${THEME_DIR}/index.theme
  echo "Encoding=UTF-8" >>                                                              ${THEME_DIR}/index.theme
  echo "" >>                                                                            ${THEME_DIR}/index.theme
  echo "[X-GNOME-Metatheme]" >>                                                         ${THEME_DIR}/index.theme
  echo "GtkTheme=${name}${flat}${color}${opacity}${thin}" >>                            ${THEME_DIR}/index.theme
  echo "MetacityTheme=${name}${flat}${color}${opacity}${thin}" >>                       ${THEME_DIR}/index.theme
  echo "IconTheme=Adwaita" >>                                                           ${THEME_DIR}/index.theme
  echo "CursorTheme=Adwaita" >>                                                         ${THEME_DIR}/index.theme
  echo "ButtonLayout=close,minimize,maximize:menu" >>                                   ${THEME_DIR}/index.theme
  # Install index.theme

  mkdir -p                                                                              ${THEME_DIR}/gnome-shell
  cp -ur ${SRC_DIR}/gnome-shell/{extensions,message-indicator-symbolic.svg,pad-osd.css} ${THEME_DIR}/gnome-shell
  cp -ur ${SRC_DIR}/gnome-shell/gnome-shell${color}${opacity}.css                       ${THEME_DIR}/gnome-shell/gnome-shell.css
  cp -ur ${SRC_DIR}/gnome-shell/common-assets                                           ${THEME_DIR}/gnome-shell/assets
  cp -ur ${SRC_DIR}/gnome-shell/assets${ELSE_DARK}/*.svg                                ${THEME_DIR}/gnome-shell/assets
  cd ${THEME_DIR}/gnome-shell
  ln -s assets/no-events.svg no-events.svg
  ln -s assets/process-working.svg process-working.svg
  ln -s assets/no-notifications.svg no-notifications.svg

  mkdir -p                                                                              ${THEME_DIR}/gtk-2.0
  cp -ur ${SRC_DIR}/gtk-2.0/gtkrc${color}                                               ${THEME_DIR}/gtk-2.0/gtkrc
  cp -ur ${SRC_DIR}/gtk-2.0/assets${color}                                              ${THEME_DIR}/gtk-2.0/assets
  cp -ur ${SRC_DIR}/gtk-2.0/common/*.rc                                                 ${THEME_DIR}/gtk-2.0
  cp -ur ${SRC_DIR}/gtk-2.0/menubar-toolbar${color}.rc                                  ${THEME_DIR}/gtk-2.0/menubar-toolbar.rc

  mkdir -p                                                                              ${THEME_DIR}/gtk-3.0
  cp -ur ${SRC_DIR}/gtk-3.0/assets                                                      ${THEME_DIR}/gtk-3.0
  cp -ur ${SRC_DIR}/gtk-3.0/thumbnail${flat}${color}.png                                ${THEME_DIR}/gtk-3.0/thumbnail.png
  cp -ur ${SRC_DIR}/gtk-3.0/gtk${flat}${color}${opacity}${thin}.css                     ${THEME_DIR}/gtk-3.0/gtk.css
  [[ ${color} != '-dark' ]] && \
  cp -ur ${SRC_DIR}/gtk-3.0/gtk${flat}-dark${opacity}${thin}.css                        ${THEME_DIR}/gtk-3.0/gtk-dark.css

  mkdir -p                                                                              ${THEME_DIR}/metacity-1
  cp -ur ${SRC_DIR}/metacity-1/metacity-theme${color}.xml                               ${THEME_DIR}/metacity-1/metacity-theme.xml
  cp -ur ${SRC_DIR}/metacity-1/{*.png,*.svg}                                            ${THEME_DIR}/metacity-1
  cd ${THEME_DIR}/metacity-1
	ln -s metacity-theme.xml metacity-theme-1.xml
	ln -s metacity-theme.xml metacity-theme-2.xml
	ln -s metacity-theme.xml metacity-theme-3.xml

  mkdir -p                                                                              ${THEME_DIR}/unity
  cp -ur ${SRC_DIR}/unity                                                               ${THEME_DIR}

  mkdir -p                                                                              ${THEME_DIR}/xfwm4
  cp -ur ${SRC_DIR}/xfwm4/assets${color}/*.png                                          ${THEME_DIR}/xfwm4
  cp -ur ${SRC_DIR}/xfwm4/themerc${color}                                               ${THEME_DIR}/xfwm4/themerc
}

install_gdm() {
    local THEME_DIR=${1}/${2}${3}${4}${5}${6}
      # bakup and install files related to gdm theme
      if [[ ! -f /usr/share/gnome-shell/gnome-shell-theme.gresource.bak ]]; then
          mv -f /usr/share/gnome-shell/gnome-shell-theme.gresource \
                /usr/share/gnome-shell/gnome-shell-theme.gresource.bak
      fi
      if [[ -f /usr/share/gnome-shell/theme/ubuntu.css ]]; then
          if [[ ! -f /usr/share/gnome-shell/theme/ubuntu.css.bak ]]; then
              mv -f /usr/share/gnome-shell/theme/ubuntu.css \
                     /usr/share/gnome-shell/theme/ubuntu.css.bak
          fi
          cp -af ${THEME_DIR}/gnome-shell/gnome-shell.css \
                 /usr/share/gnome-shell/theme/ubuntu.css
      fi
      glib-compile-resources \
       --sourcedir=${THEME_DIR}/gnome-shell \
       --target=/usr/share/gnome-shell/gnome-shell-theme.gresource \
       ${SRC_DIR}/gnome-shell/gnome-shell-theme.gresource.xml
  echo "Installing 'gnome-shell-theme.gresource'..."
}

while [[ $# -gt 0 ]]; do
  case "${1}" in
    -d|--dest)
      dest="${2}"
      if [[ ! -d "${dest}" ]]; then
        echo "ERROR: Destination directory does not exist."
        exit 1
      fi
      shift 2
      ;;
    -n|--name)
      name="${2}"
      shift 2
      ;;
    -g|--gdm)
      gdm='true'
      shift 1
      ;;
    -o|--opacity)
      shift
      for opacity in "${@}"; do
        case "${opacity}" in
          standard)
            opacitys+=("${OPACITY_VARIANTS[0]}")
            shift
            ;;
          solid)
            opacitys+=("${OPACITY_VARIANTS[1]}")
            shift
            ;;
          -*|--*)
            break
            ;;
          *)
            echo "ERROR: Unrecognized opacity variant '$1'."
            echo "Try '$0 --help' for more information."
            exit 1
            ;;
        esac
      done
      ;;
    -c|--color)
      shift
      for color in "${@}"; do
        case "${color}" in
          light)
            colors+=("${COLOR_VARIANTS[0]}")
            shift
            ;;
          dark)
            colors+=("${COLOR_VARIANTS[1]}")
            shift
            ;;
          -*|--*)
            break
            ;;
          *)
            echo "ERROR: Unrecognized color variant '$1'."
            echo "Try '$0 --help' for more information."
            exit 1
            ;;
        esac
      done
      ;;
    -f|--flat)
      shift
      for flat in "${@}"; do
        case "${flat}" in
          standard)
            flats+=("${FLAT_VARIANTS[0]}")
            shift
            ;;
          compact)
            flats+=("${FLAT_VARIANTS[1]}")
            shift
            ;;
          -*|--*)
            break
            ;;
          *)
            echo "ERROR: Unrecognized color variant '$1'."
            echo "Try '$0 --help' for more information."
            exit 1
            ;;
        esac
      done
      ;;
    -t|--thin)
      shift
      for thin in "${@}"; do
        case "${thin}" in
          standard)
            thins+=("${THIN_VARIANTS[0]}")
            shift
            ;;
          thin)
            thins+=("${THIN_VARIANTS[1]}")
            shift
            ;;
          -*|--*)
            break
            ;;
          *)
            echo "ERROR: Unrecognized thin variant '$1'."
            echo "Try '$0 --help' for more information."
            exit 1
            ;;
        esac
      done
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "ERROR: Unrecognized installation option '$1'."
      echo "Try '$0 --help' for more information."
      exit 1
      ;;
  esac
done

for flat in "${flats[@]:-${FLAT_VARIANTS[@]}}"; do
  for opacity in "${opacitys[@]:-${OPACITY_VARIANTS[@]}}"; do
    for color in "${colors[@]:-${COLOR_VARIANTS[@]}}"; do
      for thin in "${thins[@]:-${THIN_VARIANTS[@]}}"; do
        install "${dest:-${DEST_DIR}}" "${name:-${THEME_NAME}}" "${flat}" "${color}" "${opacity}" "${thin}"
      done
    done
  done
done

if [[ "${gdm:-}" == 'true' ]]; then
  install_gdm "${dest:-${DEST_DIR}}" "${name:-${THEME_NAME}}" "${flat}" "${color}" "${opacity}" "${thin}"
fi

echo
echo Done.
