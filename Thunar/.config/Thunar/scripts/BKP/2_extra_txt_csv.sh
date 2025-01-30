#!/bin/bash

# Verifica se foi fornecido pelo menos um argumento de linha de comando
if [ $# -eq 0 ]; then
    echo "Uso: $0 arquivo1.txt [arquivo2.txt ...]"
    exit 1
fi

# Verifica se o programa notify-send está disponível
if ! command -v notify-send &>/dev/null; then
    echo "Erro: o programa 'notify-send' não está instalado ou não está no PATH."
    exit 1
fi

# Verifica se o programa paplay está disponível
if ! command -v paplay &>/dev/null; then
    echo "Erro: o programa 'paplay' não está instalado ou não está no PATH."
    exit 1
fi

# Cria a subpasta CSV_Output se ainda não existir
if [ ! -d "CSV_Output" ]; then
    mkdir CSV_Output
fi

# Loop pelos argumentos de linha de comando (arquivos .txt)
for arquivo in "$@"; do
    # Verifica se o arquivo de entrada existe e é um arquivo de texto
    if [ -f "$arquivo" ] && [[ "$arquivo" == *.txt ]]; then
        # Nome do arquivo CSV de saída
        saida="CSV_Output/$(basename "${arquivo%.txt}.csv")"

        # Variáveis para armazenar informações
        turma=""
        turno=""
        ano_fase_modulo=""

        # Loop pelas linhas do arquivo
        while IFS= read -r linha; do
            # Verifica os campos adicionais
            if [[ "$linha" == *"TURMA:"* ]]; then
                turma=$(echo "$linha" | grep -oP 'TURMA:\s*\K[^ ]*')
                turno=$(echo "$linha" | grep -oP 'TURNO:\s*\K.*$')
                ano_fase_modulo=$(echo "$linha" | grep -oP 'ANO/FASE/MÓDULO:\s*\K.*?(?= TURMA:|$)')
                break
            fi
        done < "$arquivo"

        if [ -n "$turma" ]; then
            # Salva as informações em um arquivo CSV
            echo "MATRÍCULA,NOME CIVIL,DATA DE NASCIMENTO,CIDADE,UF,FILIAÇÃO 1,FILIAÇÃO 2,ANO/FASE/MÓDULO,TURMA,TURNO" > "$saida"

            # Variável para controlar as matrículas já processadas
            matricula_processada=""

            # Loop pelas linhas do arquivo
            while IFS= read -r linha; do
                # Verifica os campos adicionais
                if [[ "$linha" == *"MATRÍCULA:"* ]]; then
                    # Extrai a matrícula do aluno usando expressões regulares
                    matricula=$(echo "$linha" | grep -oP 'MATRÍCULA:\s*\K([0-9]+)')
                    # Verifica se a matrícula já foi processada para evitar duplicatas
                    if [[ "$matricula_processada" == *"$matricula"* ]]; then
                        continue
                    fi
                    matricula_processada+="$matricula "
                elif [[ "$linha" == *"NOME CIVIL:"* ]]; then
                    # Extrai o nome civil do aluno, removendo "NOME CIVIL:" da linha
                    nome_civil=$(echo "$linha" | cut -d ':' -f 2-)
                elif [[ "$linha" == *"FILIAÇÃO"* ]]; then
                    # Extrai informações de filiação do aluno, separando as filiações e substituindo " e " por ","
                    filiacao=$(echo "$linha" | cut -d ':' -f 2-)
                    filiacao=$(echo "$filiacao" | sed 's/ e /, /g')
                    filiacao_1=$(echo "$filiacao" | awk -F ', ' '{print $1}')
                    filiacao_2=$(echo "$filiacao" | awk -F ', ' '{print $2}')
                elif [[ "$linha" == *"DATA DE NASCIMENTO:"* ]]; then
                    # Extrai a data de nascimento do aluno e a cidade onde nasceu
                    data_nascimento=$(echo "$linha" | cut -d ':' -f 2- | sed 's/[[:space:]]\+CIDADE:.*//')
                    cidade=$(echo "$linha" | grep -oP 'CIDADE:\s*\K(.*)' | sed 's/^[[:space:]]*//; s/[[:space:]]*UF:.*//')
                    # Extrai a UF onde nasceu
                    uf=$(echo "$linha" | grep -oP 'UF:\s*\K(.*)' | sed 's/^[[:space:]]*//; s/[[:space:]]*$//')
                    # Salva os dados em formato CSV
                    echo "${matricula},${nome_civil},${data_nascimento},${cidade},${uf},${filiacao_1},${filiacao_2},${ano_fase_modulo},${turma},${turno}" >> "$saida"
                fi
            done < "$arquivo"

            # Notificação visual
            notify-send -u normal -t 3000 "Extração Concluída" "As informações do arquivo $arquivo foram salvas em $saida"

            # Notificação sonora
            paplay /usr/share/sounds/freedesktop/stereo/complete.oga &>/dev/null
        else
            echo "Não foi possível determinar o nome do arquivo de saída para $arquivo."
        fi
    else
        echo "O arquivo $arquivo não existe ou não é um arquivo de texto (.txt). Ignorando."
    fi
done
