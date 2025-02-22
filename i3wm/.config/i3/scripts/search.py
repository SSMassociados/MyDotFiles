#!/usr/bin/env python3

import csv
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, Scrollbar
import tkinter.font as tkf
import sys
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
import platform
from reportlab.lib.units import inch
import os
import subprocess
import threading
import webbrowser 

def open_about_window():
    about_window = tk.Toplevel(root)
    about_window.title("Sobre")
    about_window.attributes('-topmost', True)  # Define a janela como superior
    about_window.geometry('400x300')  # Define o tamanho da janela
    about_window.resizable(False, False)  # Impede o redimensionamento da janela
    about_window.configure(bg='#3B3B3B')  # Definindo o fundo da janela "About"
    
    def close_about_window(event=None):
        about_window.destroy()
        
    # Definindo um estilo personalizado para o Label na janela "About"
    about_style = ttk.Style()
    about_style.configure('About.TLabel', background='#3B3B3B', foreground='#ffffff', font=('JetBrains Mono', 12))
    
    about_label = ttk.Label(about_window, text="SIGE", style='About.TLabel')
    about_label.pack(padx=10, pady=10)
    
    # Vincular evento para fechar a janela "About" quando a tecla Esc for pressionada
    about_window.bind("<Escape>", close_about_window)
    
    # Estilo para as abas do Notebook
    notebook_style = ttk.Style()
    notebook_style.configure("TNotebook.Tab", font=('JetBrains Mono', 12))
    
    # Criar o Notebook (controlador de abas)
    notebook = ttk.Notebook(about_window, style="TNotebook")
    notebook.pack(fill='both', expand=True)
    
    # Aba Informações
    info_frame = ttk.Frame(notebook)
    notebook.add(info_frame, text='Informações')
    info_label = ttk.Label(info_frame, text='Informações sobre o programa...', font=('JetBrains Mono', 12))
    info_label.pack(padx=10, pady=10)
    
    # Aba Créditos
    credits_frame = ttk.Frame(notebook)
    notebook.add(credits_frame, text='Créditos')
    credits_label = ttk.Label(credits_frame, text='Créditos do desenvolvimento...', font=('JetBrains Mono', 12))
    credits_label.pack(padx=10, pady=10)
    
    # Aba Licença
    license_frame = ttk.Frame(notebook)
    notebook.add(license_frame, text='Licença')
    license_label = ttk.Label(license_frame, text='Informações sobre a licença...', font=('JetBrains Mono', 12))
    license_label.pack(padx=10, pady=10)

def search_student(student_name, csv_file):
    found_students = []  # Inicializa uma lista vazia para armazenar os alunos encontrados
    with open(csv_file, newline='', encoding='utf-8') as csvfile:  # Abre o arquivo CSV em modo de leitura
        reader = csv.reader(csvfile)  # Cria um objeto leitor CSV
        for row in reader:  # Itera sobre cada linha do arquivo CSV
            first_name = row[1].split()[0]  # Obtém o primeiro nome do aluno da segunda coluna (coluna de nomes)
            if student_name.lower() == first_name.lower():  # Verifica se o nome do aluno corresponde ao nome pesquisado (ignorando maiúsculas/minúsculas)
                found_students.append(row)  # Adiciona o aluno encontrado à lista de alunos encontrados
    # Ordena a lista de alunos encontrados em ordem alfabética pelo nome completo
    sorted_students = sorted(found_students, key=lambda x: x[1].lower())
    return sorted_students  # Retorna a lista de alunos encontrados em ordem alfabética pelo nome completo

def search_class(class_name, csv_file):
    found_students = []
    with open(csv_file, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # Pula o cabeçalho
        for row in reader:
            if class_name.lower() == row[8].lower():
                found_students.append(row)
    return found_students

def calculate_age(birth_date):
    today = datetime.now()
    birth_date = pd.to_datetime(birth_date)
    age = relativedelta(today, birth_date)
    age_formatted = f"{age.years} Anos, {age.months} Meses e {age.days} Dias"
    return age_formatted

def adjust_column_widths(tree):
    # Atualiza o widget para garantir que as medidas sejam precisas
    tree.update_idletasks()

    # Cria um dicionário para armazenar a largura máxima de cada coluna
    column_widths = {}

    # Itera sobre todas as colunas
    for col in tree["columns"]:
        # Configura a largura da coluna com base no título
        column_widths[col] = tkf.Font().measure(col)

    # Itera sobre todas as linhas de dados para encontrar a largura máxima do conteúdo em cada coluna
    for child in tree.get_children():
        for idx, value in enumerate(tree.item(child)["values"]):
            # Obtém o nome da coluna
            col = tree["columns"][idx]
            # Calcula a largura do conteúdo da célula
            cell_width = tkf.Font().measure(value)
            # Atualiza a largura máxima se necessário
            if cell_width > column_widths[col]:
                column_widths[col] = cell_width

    # Ajusta a largura de cada coluna
    for col, width in column_widths.items():
        tree.column(col, width=width)

def export_to_pdf(filename, data):
    # Configuração dos parâmetros de margem e tamanho da página
    doc = SimpleDocTemplate(filename, pagesize=A4, leftMargin=50, rightMargin=50, topMargin=50, bottomMargin=50)
    elements = []

    # Cabeçalho
    header = ["Matrícula", "Nome", "Nascimento", "Idade", "Turma"]
    data.insert(0, header)

    # Estilo para o cabeçalho
    header_style = TableStyle([('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                               ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                               ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                               ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                               ('BOTTOMPADDING', (0, 0), (-1, 0), 12)])

    # Estilo para os dados
    data_style = [('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                  ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                  ('GRID', (0, 0), (-1, -1), 1, colors.black)]

    # Adicionando listras zebradas
    for i in range(0, len(data), 2):
        data_style.append(('BACKGROUND', (0, i+1), (-1, i+1), colors.beige))

    # Tabela
    table = Table(data)
    table.setStyle(header_style)
    table.setStyle(TableStyle(data_style))
    elements.append(table)

    # Salvar o PDF
    doc.build(elements)

    # Criando uma janela personalizada para exibir a mensagem de exportação concluída
    export_success_window = tk.Toplevel(root)
    export_success_window.title("Exportação Concluída")
    export_success_window.configure(bg='#3B3B3B')

    # Defina a janela flutuante para ser acima da janela principal
    export_success_window.transient(root)

 # Mensagem de sucesso
    success_label = tk.Label(export_success_window, text=f"Ata exportada com sucesso para:\n{filename}", font=('JetBrains Mono', 12), bg='#3B3B3B', fg='#ffffff')
    success_label.pack(pady=10)

    # Função para visualizar o arquivo exportado com o visualizador padrão do sistema
    def visualize_pdf():
        try:
            subprocess.Popen(["atril", filename])
        except FileNotFoundError:
            messagebox.showerror("Erro", "Visualizador de PDF padrão não encontrado. Verifique se está configurado corretamente no seu sistema.")

    # Função para abrir o diretório onde o arquivo foi exportado
    def open_directory():
        directory = os.path.dirname(filename)
        subprocess.Popen(["xdg-open", directory])

    # Função para fechar a janela de exportação
    def close_window():
        export_success_window.destroy()

    # Botão para visualizar o arquivo exportado
    visualize_button = tk.Button(export_success_window, text="Visualizar", font=('JetBrains Mono', 12), command=visualize_pdf, bg='#007acc', fg='#ffffff')
    visualize_button.pack(side=tk.LEFT, padx=10, pady=10)

    # Botão para abrir o diretório onde o arquivo foi exportado
    open_button = tk.Button(export_success_window, text="Abrir Local", font=('JetBrains Mono', 12), command=open_directory, bg='#007acc', fg='#ffffff')
    open_button.pack(side=tk.LEFT, padx=10, pady=10)

    # Botão para fechar a janela de exportação
    close_button = tk.Button(export_success_window, text="Sair", font=('JetBrains Mono', 12), command=close_window, bg='#007acc', fg='#ffffff')
    close_button.pack(side=tk.LEFT, padx=10, pady=10)

    # Vinculações de eventos para navegação pelo teclado
    export_success_window.bind("<Return>", lambda event: visualize_pdf() if export_success_window.focus_get() == visualize_button else (open_directory() if export_success_window.focus_get() == open_button else close_window()))
    export_success_window.bind("<Escape>", lambda event: close_window())
    export_success_window.bind("<Tab>", lambda event: visualize_button.focus_set() if export_success_window.focus_get() == close_button else (open_button.focus_set() if export_success_window.focus_get() == visualize_button else None))
    export_success_window.bind("<Shift-Tab>", lambda event: close_button.focus_set() if export_success_window.focus_get() == visualize_button else (visualize_button.focus_set() if export_success_window.focus_get() == open_button else None))

# Variável global para armazenar o último local de salvamento
last_save_location = ""

# Função para exportar a ata para PDF
def export_ata_to_pdf():
    global last_save_location
    
    # Pede ao usuário para selecionar o local do arquivo e sugere o nome da turma
    turma = class_combobox.get()
    initialfile = f"ATA_{turma.replace(' ', '_')}" if turma else "ATA"
    filename = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("Arquivo PDF", "*.pdf")], initialfile=initialfile, initialdir=last_save_location)

    # Se o usuário selecionou um arquivo, exporta a ata
    if filename:
        # Memoriza o último local de salvamento
        last_save_location = os.path.dirname(filename)
        
        # Substitui espaços por sublinhados no nome do arquivo
        filename = filename.replace(" ", "_").replace("-", "_")
        
        # Obtém o título da ata
        ata_title = "ATA DE ASSINATURAS"
        if turma:
            ata_title += f" - \"{turma}\""

        # Obtém a data atual formatada
        current_date = datetime.now().strftime("%d/%m/%Y - %A - %H:%M:%S")

        # Obtém os resultados da Treeview
        data = []
        for i, row_id in enumerate(result_tree.get_children(), start=1):
            row = result_tree.item(row_id)['values']
            # Adiciona uma linha para a assinatura
            data.append([i, row[0], row[1], "                                                                                          ."])  # Alteração na linha para assinatura
        
        # Configuração dos parâmetros de margem e tamanho da página    
        doc = SimpleDocTemplate(filename, pagesize=letter, leftMargin=3, rightMargin=3,topMargin=-0.10*inch, bottomMargin=-0.10*inch)
        elements = []

        # Adiciona o título à ata
        title_style = ParagraphStyle(name='TitleStyle', fontSize=14, alignment=TA_CENTER)
        title = Paragraph(f"<b>{ata_title}</b>", title_style)
        elements.append(title)

        # Adiciona um pequeno espaço entre o título e a data
        elements.append(Spacer(1, 5))

        # Adiciona a data
        date_style = ParagraphStyle(name='DateStyle', fontSize=12, alignment=TA_CENTER)
        date = Paragraph(current_date, date_style)
        elements.append(date)

        # Adiciona uma quebra de linha após a data
        elements.append(Spacer(1, 10))

        # Cabeçalho
        header = ["#", "Matrícula", "Nome", "Assinatura"]
        data.insert(0, header)

        # Estilo para o cabeçalho
        header_style = TableStyle([
         ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
         ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
         ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
         ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
         ('BOTTOMPADDING', (0, 0), (-1, 0), 3),  # Reduzindo o espaçamento após o cabeçalho
         ('TOPPADDING', (0, 0), (-1, 0), 3),     # Adicionando espaçamento antes do cabeçalho
        ])

        # Estilo para os dados
        data_style = [('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                      ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                      ('GRID', (0, 0), (-1, -1), 1, colors.black)]

        # Adicionando listras zebradas
        for i in range(0, len(data), 2):
            data_style.append(('BACKGROUND', (0, i+1), (-1, i+1), colors.beige))

        # Tabela
        table = Table(data)
        table.setStyle(header_style)
        table.setStyle(TableStyle(data_style))
        elements.append(table)

        # Salvar o PDF
        doc.build(elements)

        # Criando uma janela personalizada para exibir a mensagem de exportação concluída
        export_success_window = tk.Toplevel(root)
        export_success_window.title("Exportação Concluída")
        export_success_window.configure(bg='#3B3B3B')
        
        # Defina a janela flutuante para ser acima da janela principal
        export_success_window.transient(root)
        
        # Mensagem de sucesso
        success_label = tk.Label(export_success_window, text=f"Ata exportada com sucesso para:\n{filename}", font=('JetBrains Mono', 12), bg='#3B3B3B', fg='#ffffff')
        success_label.pack(pady=10)
    
        # Função para visualizar o arquivo exportado com o visualizador padrão do sistema
        def visualize_pdf():
            try:
                subprocess.Popen(["atril", filename])
            except FileNotFoundError:
                show_custom_message("Erro", "Visualizador de PDF padrão não encontrado.")

        # Função para abrir o diretório onde o arquivo foi exportado
        def open_directory():
            directory = os.path.dirname(filename)
            subprocess.Popen(["xdg-open", directory])

        # Função para fechar a janela de exportação
        def close_window():
            export_success_window.destroy()

        # Botão para visualizar o arquivo exportado
        visualize_button = tk.Button(export_success_window, text="Visualizar", font=('JetBrains Mono', 12), command=visualize_pdf, bg='#007acc', fg='#ffffff')
        visualize_button.pack(side=tk.LEFT, padx=10, pady=10)

        # Botão para abrir o diretório onde o arquivo foi exportado
        open_button = tk.Button(export_success_window, text="Abrir Local", font=('JetBrains Mono', 12), command=open_directory, bg='#007acc', fg='#ffffff')
        open_button.pack(side=tk.LEFT, padx=10, pady=10)

        # Botão para fechar a janela de exportação
        close_button = tk.Button(export_success_window, text="Sair", font=('JetBrains Mono', 12), command=close_window, bg='#007acc', fg='#ffffff')
        close_button.pack(side=tk.LEFT, padx=10, pady=10)
        
        # Vinculações de eventos para navegação pelo teclado
        export_success_window.bind("<Return>", lambda event: visualize_pdf() if export_success_window.focus_get() == visualize_button else (open_directory() if export_success_window.focus_get() == open_button else close_window()))
        export_success_window.bind("<Escape>", lambda event: close_window())
        export_success_window.bind("<Tab>", lambda event: visualize_button.focus_set() if export_success_window.focus_get() == close_button else (open_button.focus_set() if export_success_window.focus_get() == visualize_button else None))
        export_success_window.bind("<Shift-Tab>", lambda event: close_button.focus_set() if export_success_window.focus_get() == visualize_button else (visualize_button.focus_set() if export_success_window.focus_get() == open_button else None))

def export_results_to_pdf():
    # Obtém os resultados da Treeview
    data = []
    for row_id in result_tree.get_children():
        row = result_tree.item(row_id)['values']
        data.append(row)

    # Pede ao usuário para selecionar o local do arquivo
    filename = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("Arquivo PDF", "*.pdf")])

    # Se o usuário selecionou um arquivo, exporta os resultados
    if filename:
        export_to_pdf(filename, data)
    else:
        show_custom_message("Exportação Cancelada")

# Função para abrir declaração do Bolsa Familia em threads separadas
def open_declaration_thread():
    declaration_path = "/home/sidiclei/Área de trabalho/AUSTRO/DECLARAÇÕES/DECLARAÇÃO BOLSA FAMÍLIA.docx"
    if os.path.exists(declaration_path):
        subprocess.run(["xdg-open", declaration_path])
    else:
        show_custom_message("Erro", "Bolsa Familia \nnão foi encontrada.")

# Função para abrir o documento de presença em threads separadas
def open_presence_thread():
    presence_path = "/home/sidiclei/Área de trabalho/AUSTRO/DECLARAÇÕES/DECLARAÇÃO DE COMPARECIMENTO.docx"
    if os.path.exists(presence_path):
        subprocess.run(["xdg-open", presence_path])
    else:
        show_custom_message("Erro", "Presença \nnão foi encontrada.")
        
# Função para abrir o declaração de provisoria em threads separadas
def open_provisoria_thread():
    provisoria_path = "/home/sidiclei/Área de trabalho/AUSTRO/DECLARAÇÕES/Provisória.docx"
    if os.path.exists(provisoria_path):
        subprocess.run(["xdg-open", provisoria_path])
    else:
        show_custom_message("Erro", "Provisória \nnão foi encontrada.")

def open_declaration():
    threading.Thread(target=open_declaration_thread).start()

def open_presence():
    threading.Thread(target=open_presence_thread).start()
    
def open_provisoria():
    threading.Thread(target=open_provisoria_thread).start()
    
def open_siepe():
    webbrowser.open("https://www.siepe.educacao.pe.gov.br/")  # Abrindo o link no navegador padrão
    
def open_censo():
    webbrowser.open("https://censobasico.inep.gov.br/censobasico/#/")  # Abrindo o link no navegador padrão

def show_search_result(event=None):
    # Limpa os resultados anteriores
    result_tree.delete(*result_tree.get_children())
    
    # Limpa a seleção da caixa de seleção de turma
    class_combobox.set("")
    
    student_name = entry_student.get().strip().split()[0]  # Obtém apenas o primeiro nome
    if student_name:
        if csv_file:
            found_students = search_student(student_name, csv_file)
            if found_students:
                for i, student in enumerate(found_students):
                    age = calculate_age(student[2])  # Calcula a idade com base na data de nascimento
                    result_tree.insert("", "end", values=(student[0], student[1], student[2], age, student[8]), tags=('even' if i % 2 == 0 else 'odd'))
                # Atualiza o rótulo com a quantidade de ocorrências encontradas
                occurrences_label.config(text=f"Ocorrências encontradas: {len(found_students)}")
                # Ajusta as larguras das colunas
                adjust_column_widths(result_tree)  # Ajusta as larguras das colunas após a inserção dos resultados
            else:
                # Atualiza o rótulo para zero se nenhum aluno for encontrado
                occurrences_label.config(text="Ocorrências encontradas: 0")
                show_custom_message("Resultado", "Aluno não encontrado.")
        else:
            show_custom_message("Erro", "Por favor, selecione um arquivo CSV.")
    else:
        show_custom_message("Erro", "Por favor, insira o nome do aluno.")
    entry_student.select_range(0, tk.END)

def select_class(event=None):
    selected_class = class_combobox.get()
    if selected_class:
        # Limpa os resultados anteriores
        result_tree.delete(*result_tree.get_children())

        # Limpa o campo de pesquisa
        entry_student.delete(0, tk.END)
        
        if csv_file:
            found_students = search_class(selected_class, csv_file)
            if found_students:
                for i, student in enumerate(found_students):
                    age = calculate_age(student[2])  # Calcula a idade com base na data de nascimento
                    result_tree.insert("", "end", values=(student[0], student[1], student[2], age, selected_class), tags=('even' if i % 2 == 0 else 'odd'))
                # Atualiza o rótulo com a quantidade de ocorrências encontradas
                occurrences_label.config(text=f"Ocorrências encontradas: {len(found_students)}")
                # Ajusta as larguras das colunas
                adjust_column_widths(result_tree)  # Ajusta as larguras das colunas após a inserção dos resultados
            else:
                # Atualiza o rótulo para zero se nenhum aluno for encontrado
                occurrences_label.config(text="Ocorrências encontradas: 0")
                show_custom_message("Resultado", "Nenhum aluno encontrado para esta turma.")
        else:
            show_custom_message("Erro", "Por favor, selecione um arquivo CSV.")

def center_window(window):
    window.update_idletasks()
    width = window.winfo_width()
    height = window.winfo_height()
    x = (window.winfo_screenwidth() // 2) - (width // 2)
    y = (window.winfo_screenheight() // 2) - (height // 2)
    window.geometry('{}x{}+{}+{}'.format(width, height, x, y))

def show_custom_message(title, message):
    custom_message_window = tk.Toplevel(root)
    custom_message_window.title(title)
    custom_message_window.configure(bg='#3B3B3B')
    custom_message_window.attributes('-topmost', 'true')
    custom_message_window.update_idletasks()
        
    custom_message_window.transient(root)
    
    message_label = tk.Label(custom_message_window, text=message, font=('JetBrains Mono', 12), bg='#3B3B3B', fg='#ffffff')
    message_label.pack(pady=10)

    close_button = tk.Button(custom_message_window, text="Fechar", font=('JetBrains Mono', 12), command=custom_message_window.destroy, bg='#007acc', fg='#ffffff')
    close_button.pack(pady=10)
            
    center_window(custom_message_window)
         
if __name__ == "__main__":
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    else:
        csv_file = ""
    
    if csv_file:
        # Obtendo as turmas do arquivo CSV
        classes = set()
        with open(csv_file, newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)  # Pular o cabeçalho
            for row in reader:
                classes.add(row[8])
    else:
        classes = []

    root = tk.Tk()
    root.title("Sistema de Informações e Gerenciamento Escolar")
    root.configure(bg='#3B3B3B')
    
    # Adiciona uma Label na janela principal
    sige_label = ttk.Label(root, text="SISTEMA DE INFORMAÇÕES E GERENCIAMENTO ESCOLAR", font=('JetBrains Mono', 12), background='#333333', foreground='#ffffff')
    sige_label.pack(side=tk.TOP, pady=10)

    style = ttk.Style(root)
    style.configure('Treeview.Heading', font=('JetBrains Mono', 12))
    style.configure('TButton', font=('JetBrains Mono', 12))
    style.configure('TLabel', font=('JetBrains Mono', 12))
    style.configure('TEntry', font=('JetBrains Mono', 12))
    style.configure('Treeview', font=('JetBrains Mono', 11))
    style.configure('Treeview', rowheight=25)
    style.configure('Custom.Treeview', background='#3B3B3B', foreground='#ffffff')

    main_frame = tk.Frame(root, bg='#3B3B3B')
    main_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    # Frame para os elementos de pesquisa
    search_frame = tk.Frame(main_frame, bg='#3B3B3B')
    search_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

    student_label = tk.Label(search_frame, text="Aluno:", font=('JetBrains Mono', 12), bg='#3B3B3B', fg='#ffffff')
    student_label.pack(side=tk.LEFT, padx=(5, 0), pady=5)

    entry_student = tk.Entry(search_frame, font=('JetBrains Mono', 12), bg='#2d2d32', fg='#ffffff')
    entry_student.pack(side=tk.LEFT, padx=(0, 5), pady=5, fill=tk.X, expand=True)

    search_button = tk.Button(search_frame, text="Pesquisar", font=('JetBrains Mono', 12), command=show_search_result, bg='#007acc', fg='#ffffff')
    search_button.pack(side=tk.LEFT, padx=(10, 5), pady=5)

    class_label = tk.Label(search_frame, text="Turma:", font=('JetBrains Mono', 12), bg='#3B3B3B', fg='#ffffff')
    class_label.pack(side=tk.LEFT, padx=(5, 0), pady=5)

    class_combobox = ttk.Combobox(search_frame, values=list(classes), font=('JetBrains Mono', 12), state="readonly")
    class_combobox.pack(side=tk.LEFT, padx=(0, 5), pady=5)
    class_combobox.bind("<<ComboboxSelected>>", select_class)

    result_frame = tk.Frame(main_frame, bg='#3B3B3B')
    result_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)

    result_label = tk.Label(result_frame, text="Resultados:", font=('JetBrains Mono', 12), bg='#3B3B3B', fg='#ffffff')
    result_label.pack(pady=5)

    result_tree = ttk.Treeview(result_frame, columns=("Matrícula", "Nome", "Nascimento", "Idade", "Turma"), show="headings", style="Custom.Treeview")
    result_tree.heading("Matrícula", text="Matrícula")
    result_tree.heading("Nome", text="Nome")
    result_tree.heading("Nascimento", text="Nascimento")
    result_tree.heading("Idade", text="Idade")
    result_tree.heading("Turma", text="Turma")
    result_tree.pack(expand=True, fill="both")

    # Ajuste automático das colunas
    for column in ("Matrícula", "Nome", "Nascimento", "Idade", "Turma"):
        result_tree.column(column, stretch=True)

    # Configurar tags para linhas zebra
    result_tree.tag_configure('even', background='#2d2d32', foreground='#ffffff')
    result_tree.tag_configure('odd', background='#3B3B3B', foreground='#ffffff')

    # Rótulo para exibir a quantidade de ocorrências encontradas
    occurrences_label = tk.Label(main_frame, font=('JetBrains Mono', 12), bg='#3B3B3B', fg='#ffffff')
    occurrences_label.pack(side=tk.TOP, fill=tk.X, padx=5, pady=(5, 0))
      
    # Criando um Frame para os botões de exportação
    export_buttons_frame = tk.Frame(root, bg='#3B3B3B')
    export_buttons_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=(10, 0))

    # Botão para exportar para PDF
    export_pdf_button = tk.Button(export_buttons_frame, text="Resultados", font=('JetBrains Mono', 12), command=export_results_to_pdf, bg='#007acc', fg='#ffffff', width=11)
    export_pdf_button.pack(side=tk.LEFT, padx=5, pady=5)

    # Botão para exportar ata para PDF
    export_ata_button = tk.Button(export_buttons_frame, text="Ata", font=('JetBrains Mono', 12), command=export_ata_to_pdf, bg='#007acc', fg='#ffffff', width=11)
    export_ata_button.pack(side=tk.LEFT, padx=5, pady=5)

    # Botão para abrir declaração do Bolsa familia
    declaration_button = tk.Button(export_buttons_frame, text="Bolsa", font=('JetBrains Mono', 12), command=open_declaration, bg='#007acc', fg='#ffffff', width=11)
    declaration_button.pack(side=tk.LEFT, padx=5, pady=5)

    # Botão para abrir o documento de presença
    presence_button = tk.Button(export_buttons_frame, text="Presença", font=('JetBrains Mono', 12), command=open_presence, bg='#007acc', fg='#ffffff', width=11)
    presence_button.pack(side=tk.LEFT, padx=5, pady=5)
    
    # Botão para abrir o documento de provisoria
    presence_button = tk.Button(export_buttons_frame, text="Provisória", font=('JetBrains Mono', 12), command=open_provisoria, bg='#007acc', fg='#ffffff', width=11)
    presence_button.pack(side=tk.LEFT, padx=5, pady=5)

    # Botão para abrir o site do SIEPE
    siepe_button = tk.Button(export_buttons_frame, text="SIEPE", font=('JetBrains Mono', 12), command=open_siepe, bg='#007acc', fg='#ffffff', width=11)
    siepe_button.pack(side=tk.LEFT, padx=5, pady=5)

    # Botão para abrir o site do Censo Escolar
    censo_button = tk.Button(export_buttons_frame, text="Censo Escolar", font=('JetBrains Mono', 12), command=open_censo, bg='#007acc', fg='#ffffff', width=11)
    censo_button.pack(side=tk.LEFT, padx=5, pady=5)

    # Criação do botão "About" no lado direito
    about_button = tk.Button(root, text="About", font=('JetBrains Mono', 10), command=open_about_window, bg='#333333', fg='#ffffff')
    about_button.pack(side=tk.RIGHT, anchor=tk.SE, padx=10, pady=10)
    
    # Vincula a função de pesquisa ao pressionar Enter na entrada de texto
    #entry_student.bind("<Return>", show_search_result)
            
    # Foca o campo de entrada para pesquisa individual
    entry_student.focus_set()
    
    # Adiciona vinculações de teclas para navegação e acionamento de botões
    root.bind("<Return>", show_search_result)
    root.bind("<Escape>", lambda e: root.destroy())
    root.bind("<Return>", lambda event: search_button.invoke() if root.focus_get() == entry_student else None)
    root.bind("<Shift-Tab>", lambda event: class_combobox.focus() if entry_student.focus_get() else entry_student.focus())
    root.bind("<Tab>", lambda event: class_combobox.focus() if entry_student.focus_get() else entry_student.focus())

    root.mainloop()

