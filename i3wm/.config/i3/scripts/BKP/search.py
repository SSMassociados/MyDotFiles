#!/usr/bin/env python3

import csv
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sys
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

def search_student(student_name, csv_file):
    found_students = []
    with open(csv_file, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            first_name = row[1].split()[0]  # Obtém o primeiro nome do aluno
            if student_name.lower() == first_name.lower():
                found_students.append(row)
    return found_students

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

def show_search_result(event=None):
    # Limpa os resultados anteriores
    result_tree.delete(*result_tree.get_children())
    
    # Limpa a seleção da caixa de seleção de turma
    class_combobox.set("")
    
    student_name = entry.get().strip().split()[0]  # Obtém apenas o primeiro nome
    if student_name:
        if csv_file:
            found_students = search_student(student_name, csv_file)
            if found_students:
                for i, student in enumerate(found_students):
                    age = calculate_age(student[2])  # Calcula a idade com base na data de nascimento
                    result_tree.insert("", "end", values=(student[0], student[1], student[2], age, student[8]), tags=('even' if i % 2 == 0 else 'odd'))
                # Atualiza o rótulo com a quantidade de ocorrências encontradas
                occurrences_label.config(text=f"Ocorrências encontradas: {len(found_students)}")
            else:
                # Atualiza o rótulo para zero se nenhum aluno for encontrado
                occurrences_label.config(text="Ocorrências encontradas: 0")
                messagebox.showinfo("Resultado", "Aluno não encontrado.")
        else:
            messagebox.showinfo("Erro", "Por favor, selecione um arquivo CSV.")
    else:
        messagebox.showinfo("Erro", "Por favor, insira o nome do aluno.")
    entry.select_range(0, tk.END)  # Seleciona todo o texto na entrada de texto

def select_class(event=None):
    selected_class = class_combobox.get()
    if selected_class:
        # Limpa os resultados anteriores
        result_tree.delete(*result_tree.get_children())

        # Limpa o campo de pesquisa
        entry.delete(0, tk.END)
        
        if csv_file:
            found_students = search_class(selected_class, csv_file)
            if found_students:
                for i, student in enumerate(found_students):
                    age = calculate_age(student[2])  # Calcula a idade com base na data de nascimento
                    result_tree.insert("", "end", values=(student[0], student[1], student[2], age, student[8]), tags=('even' if i % 2 == 0 else 'odd'))
                # Atualiza o rótulo com a quantidade de ocorrências encontradas
                occurrences_label.config(text=f"Ocorrências encontradas: {len(found_students)}")
            else:
                # Atualiza o rótulo para zero se nenhum aluno for encontrado
                occurrences_label.config(text="Ocorrências encontradas: 0")
                messagebox.showinfo("Resultado", "Nenhum aluno encontrado para esta turma.")
        else:
            messagebox.showinfo("Erro", "Por favor, selecione um arquivo CSV.")
    else:
        messagebox.showinfo("Erro", "Por favor, selecione uma turma.")

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
    root.title("Pesquisar Aluno")
    root.configure(bg='#1f1f23')

    style = ttk.Style(root)
    style.configure('Treeview.Heading', font=('JetBrains Mono', 12))
    style.configure('TButton', font=('JetBrains Mono', 12))
    style.configure('TLabel', font=('JetBrains Mono', 12))
    style.configure('TEntry', font=('JetBrains Mono', 12))
    style.configure('Treeview', font=('JetBrains Mono', 11))
    style.configure('Treeview', rowheight=25)
    style.configure('Custom.Treeview', background='#1f1f23', foreground='#ffffff')

    main_frame = tk.Frame(root, bg='#1f1f23')
    main_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    entry = tk.Entry(main_frame, font=('JetBrains Mono', 12), bg='#2d2d32', fg='#ffffff')
    entry.grid(row=0, column=0, padx=5, pady=5, sticky="we")
    entry.focus_set()

    search_button = tk.Button(main_frame, text="Pesquisar", font=('JetBrains Mono', 12), command=show_search_result, bg='#007acc', fg='#ffffff')
    search_button.grid(row=0, column=1, padx=5, pady=5)

    result_frame = tk.Frame(main_frame, bg='#1f1f23')
    result_frame.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")

    result_label = tk.Label(result_frame, text="Resultados:", font=('JetBrains Mono', 12), bg='#1f1f23', fg='#ffffff')
    result_label.pack(pady=5)

    result_tree = ttk.Treeview(result_frame, columns=("Matr", "Nome", "Nasc", "Idade", "Turma"), show="headings", style="Custom.Treeview")
    result_tree.heading("Matr", text="Matr")
    result_tree.heading("Nome", text="Nome")
    result_tree.heading("Nasc", text="Nasc")
    result_tree.heading("Idade", text="Idade")
    result_tree.heading("Turma", text="Turma")
    result_tree.pack(expand=True, fill="both")

    # Configurar tags para linhas zebra
    result_tree.tag_configure('even', background='#2d2d32', foreground='#ffffff')
    result_tree.tag_configure('odd', background='#1f1f23', foreground='#ffffff')

    # Vincula a função de pesquisa ao pressionar Enter na entrada de texto
    entry.bind("<Return>", show_search_result)

    # Vincula a função de fechar janela ao pressionar Esc
    root.bind("<Escape>", lambda e: root.destroy())

    # Carrega as turmas no menu suspenso
    class_combobox = ttk.Combobox(main_frame, values=list(classes), font=('JetBrains Mono', 12), state="readonly")
    class_combobox.grid(row=2, column=0, padx=5, pady=5, sticky="we")
    class_combobox.bind("<<ComboboxSelected>>", select_class)

    # Rótulo para a seleção da turma
    class_label = tk.Label(main_frame, text="Turma     ", font=('JetBrains Mono', 12), bg='#1f1f23', fg='#ffffff')
    class_label.grid(row=2, column=0, padx=5, pady=5, sticky="w")

    # Rótulo para exibir a quantidade de ocorrências encontradas
    occurrences_label = tk.Label(main_frame, font=('JetBrains Mono', 12), bg='#1f1f23', fg='#ffffff')
    occurrences_label.grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky="w")

    # Configurações iniciais do rótulo de ocorrências
    occurrences_label.config(text="Ocorrências encontradas: 0")

    root.mainloop()

