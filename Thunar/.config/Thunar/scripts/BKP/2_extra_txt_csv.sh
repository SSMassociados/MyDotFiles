#!/bin/bash

# Verifica se foi fornecido pelo menos um argumento de linha de comando
if [ $# -eq 0 ]; then
    echo "Uso: $0 arquivo1.txt [arquivo2.txt ...]"
    exit 1
fi

# Verifica dependências
for cmd in notify-send paplay; do
    if ! command -v "$cmd" &>/dev/null; then
        echo "Erro: o programa '$cmd' não está instalado ou não está no PATH."
        exit 1
    fi
done

# Cria a subpasta CSV_Output se ainda não existir
mkdir -p CSV_Output

# Loop pelos arquivos fornecidos
for arquivo in "$@"; do
    if [ ! -f "$arquivo" ] || [[ "$arquivo" != *.txt ]]; then
        echo "O arquivo $arquivo não existe ou não é um .txt. Ignorando."
        continue
    fi

    saida="CSV_Output/$(basename "${arquivo%.txt}.csv")"

    # Inicializa variáveis de turma
    turma=""
    turno=""
    ano_fase_modulo=""

    while IFS= read -r linha; do
        if [[ "$linha" == *"TURMA:"* ]]; then
            turma=$(echo "$linha" | grep -oP 'TURMA:\s*\K[^ ]*')
            turno=$(echo "$linha" | grep -oP 'TURNO:\s*\K.*$')
            ano_fase_modulo=$(echo "$linha" | grep -oP 'ANO/FASE/MÓDULO:\s*\K.*?(?= TURMA:|$)')
            break
        fi
    done < "$arquivo"

    if [ -z "$turma" ]; then
        echo "Não foi possível determinar a turma em $arquivo. Ignorando."
        continue
    fi

    # Cabeçalho do CSV com novos campos
    echo "MATRÍCULA,NOME CIVIL,DATA DE NASCIMENTO,CIDADE,UF,FILIAÇÃO 1,FILIAÇÃO 2,E-MAIL,TELEFONE,ANO/FASE/MÓDULO,TURMA,TURNO" > "$saida"

    declare -A matriculas
    matricula=""
    nome_civil=""
    data_nascimento=""
    cidade=""
    uf=""
    filiacao_1=""
    filiacao_2=""
    email=""
    telefone=""

    while IFS= read -r linha || [ -n "$linha" ]; do
        if [[ "$linha" == *"MATRÍCULA:"* ]]; then
            matricula=$(echo "$linha" | grep -oP 'MATRÍCULA:\s*\K[0-9]+')
            if [[ -n "${matriculas[$matricula]}" ]]; then
                continue
            fi
            matriculas["$matricula"]=1

        elif [[ "$linha" == *"NOME CIVIL:"* ]]; then
            nome_civil=$(echo "$linha" | sed -E 's/.*NOME CIVIL:\s*([^[:digit:]]+).*/\1/' | sed 's/[[:space:]]*$//')

       elif [[ "$linha" == *"FILIAÇÃO"* ]]; then
    filiacao=$(echo "$linha" | cut -d ':' -f 2- | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')

    # Substitui " e " por vírgula se presente
    if [[ "$filiacao" == *" e "* ]]; then
        filiacao=$(echo "$filiacao" | sed 's/ e /, /')
    fi

    # Conta vírgulas para saber quantos nomes há
    num_virgulas=$(echo "$filiacao" | grep -o "," | wc -l)

    if [[ "$num_virgulas" -eq 0 ]]; then
        # Só um nome informado — presumimos que seja a mãe
        filiacao_1="Desconhecido"
        filiacao_2="$filiacao"
    else
        # Dois ou mais nomes — cortamos normalmente
        filiacao_1=$(echo "$filiacao" | cut -d ',' -f1 | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
        filiacao_2=$(echo "$filiacao" | cut -d ',' -f2- | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
    fi

    # Valores padrão se vazios
    filiacao_1="${filiacao_1:-Desconhecido}"
    filiacao_2="${filiacao_2:-Desconhecido}"

        elif [[ "$linha" == *"E-MAIL:"* ]]; then
            email=$(echo "$linha" | grep -oP 'E-MAIL:\s*\K([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})' | head -n 1)
            email="${email:-Sem e-mail}"

        elif [[ "$linha" == *"TELEFONE:"* ]]; then
            telefone=$(echo "$linha" | grep -oP 'TELEFONE:\s*\K.*' | sed 's/[()]//g; s/;/\n/g' | tr -s ' ' | paste -sd ';' -)
            telefone="${telefone:-Sem telefone}"

        elif [[ "$linha" == *"DATA DE NASCIMENTO:"* ]]; then
            data_nascimento=$(echo "$linha" | grep -oP 'DATA DE NASCIMENTO:\s*\K[^C]*' | sed 's/[[:space:]]*$//')
            cidade=$(echo "$linha" | grep -oP 'CIDADE:\s*\K[^U]*' | sed 's/[[:space:]]*$//')
            uf=$(echo "$linha" | grep -oP 'UF:\s*\K[^ ]*')

            # Validações e preenchimentos padrões
            nome_civil="${nome_civil:-Desconhecido}"
            data_nascimento="${data_nascimento:-00/00/0000}"
            cidade="${cidade:-Desconhecida}"
            uf="${uf:---}"
            filiacao_1="${filiacao_1:-}"
            filiacao_2="${filiacao_2:-}"
            email="${email:-Sem e-mail}"
            telefone="${telefone:-Sem telefone}"

            # Escreve linha no CSV
            echo "\"${matricula}\",\"${nome_civil}\",\"${data_nascimento}\",\"${cidade}\",\"${uf}\",\"${filiacao_1}\",\"${filiacao_2}\",\"${email}\",\"${telefone}\",\"${ano_fase_modulo}\",\"${turma}\",\"${turno}\"" >> "$saida"

            # Reseta campos do estudante
            nome_civil=""
            data_nascimento=""
            cidade=""
            uf=""
            filiacao_1=""
            filiacao_2=""
            email=""
            telefone=""
        fi
    done < "$arquivo"

    # Notificações
    notify-send -u normal -t 3000 "Extração Concluída" "Arquivo salvo: $saida"
    paplay /usr/share/sounds/freedesktop/stereo/complete.oga &>/dev/null
done
