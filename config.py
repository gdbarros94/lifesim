import tkinter as tk

def get_config():
    config = {}
    def submit():
        try:
            config["grid_size"] = int(entry_grid.get())
            config["prob_species1"] = float(entry_prob1.get())
            config["prob_species2"] = float(entry_prob2.get())
            config["delay"] = float(entry_delay.get())
            config["p_move"] = float(entry_pmove.get())
        except ValueError:
            config["grid_size"] = 20
            config["prob_species1"] = 0.15
            config["prob_species2"] = 0.15
            config["delay"] = 0.5
            config["p_move"] = 0.2
        root.destroy()
        
    root = tk.Tk()
    root.title("Configurações do Simulador")
    
    tk.Label(root, text="Tamanho da Grade:").grid(row=0, column=0, padx=5, pady=5)
    entry_grid = tk.Entry(root)
    entry_grid.insert(0, "20")
    entry_grid.grid(row=0, column=1, padx=5, pady=5)
    
    tk.Label(root, text="Probabilidade de Espécie 1 (0 a 1):").grid(row=1, column=0, padx=5, pady=5)
    entry_prob1 = tk.Entry(root)
    entry_prob1.insert(0, "0.15")
    entry_prob1.grid(row=1, column=1, padx=5, pady=5)
    
    tk.Label(root, text="Probabilidade de Espécie 2 (0 a 1):").grid(row=2, column=0, padx=5, pady=5)
    entry_prob2 = tk.Entry(root)
    entry_prob2.insert(0, "0.15")
    entry_prob2.grid(row=2, column=1, padx=5, pady=5)
    
    tk.Label(root, text="Intervalo de Atualização (s):").grid(row=3, column=0, padx=5, pady=5)
    entry_delay = tk.Entry(root)
    entry_delay.insert(0, "0.5")
    entry_delay.grid(row=3, column=1, padx=5, pady=5)
    
    tk.Label(root, text="Probabilidade de Movimento (0 a 1):").grid(row=4, column=0, padx=5, pady=5)
    entry_pmove = tk.Entry(root)
    entry_pmove.insert(0, "0.2")
    entry_pmove.grid(row=4, column=1, padx=5, pady=5)
    
    submit_button = tk.Button(root, text="Iniciar Simulação", command=submit)
    submit_button.grid(row=5, column=0, columnspan=2, padx=5, pady=10)
    
    root.mainloop()
    return config 