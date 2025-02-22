import numpy as np
import random
import time
import os
import matplotlib.pyplot as plt
from matplotlib import colors
import tkinter as tk
from world import World
from visualization import Visualizer
from config import get_config


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

config = get_config()
GRID_SIZE = config["grid_size"]
prob_species1 = config["prob_species1"]
prob_species2 = config["prob_species2"]
DELAY = config["delay"]
p_move = config["p_move"]

if prob_species1 + prob_species2 > 1:
    raise ValueError("A soma das probabilidades das espécies não pode ser maior que 1.")


initial_energy   = 2      
energy_growth    = 1      
energy_threshold = 10     
energy_cost      = 1      
initial_strength = 1      


food_energy_factor = 2   
ore_strength_factor = 1  
misc_energy_factor = 1   


energia = np.zeros((GRID_SIZE, GRID_SIZE))
forca   = np.zeros((GRID_SIZE, GRID_SIZE))



food = np.zeros((GRID_SIZE, GRID_SIZE))
ore  = np.zeros((GRID_SIZE, GRID_SIZE))
misc = np.zeros((GRID_SIZE, GRID_SIZE))

for i in range(GRID_SIZE):
    for j in range(GRID_SIZE):
        if random.random() < 0.1:  
            food[i, j] = random.randint(1, 3)
        if random.random() < 0.05: 
            ore[i, j] = random.randint(1, 3)
        if random.random() < 0.05: 
            misc[i, j] = random.randint(1, 2)


def criar_mundo():
    
    p_empty = 1 - (prob_species1 + prob_species2)
    mundo = np.random.choice([0, 1, 2],
                             GRID_SIZE * GRID_SIZE,
                             p=[p_empty, prob_species1, prob_species2]).reshape(GRID_SIZE, GRID_SIZE)
    
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            if mundo[i, j] != 0:
                energia[i, j] = initial_energy
                forca[i, j] = initial_strength
    return mundo


def obter_vizinhos(i, j):
    vizinhos = [
        (i-1, j-1), (i-1, j), (i-1, j+1),
        (i, j-1),           (i, j+1),
        (i+1, j-1), (i+1, j), (i+1, j+1)
    ]
    return [(x, y) for (x, y) in vizinhos if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE]

def contar_vizinhos_por_especie(mundo, i, j, especie):
    count = 0
    for (x, y) in obter_vizinhos(i, j):
        if mundo[x, y] == especie:
            count += 1
    return count

def soma_energia_vizinhos(mundo, energia, i, j, especie):
    total = 0
    for (x, y) in obter_vizinhos(i, j):
        if mundo[x, y] == especie:
            total += energia[x, y]
    return total

def soma_forca_vizinhos(mundo, forca, i, j, especie):
    total = 0
    for (x, y) in obter_vizinhos(i, j):
        if mundo[x, y] == especie:
            total += forca[x, y]
    return total


def atualizar_mundo(mundo):
    global energia, forca, food, ore, misc
    novo_mundo = np.copy(mundo)
    nova_energia = np.copy(energia)
    nova_forca = np.copy(forca)
    
    
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            if novo_mundo[i, j] != 0:
                
                if food[i, j] > 0:
                    nova_energia[i, j] += food[i, j] * food_energy_factor
                    food[i, j] = 0
                
                if ore[i, j] > 0:
                    nova_forca[i, j] += ore[i, j] * ore_strength_factor
                    ore[i, j] = 0
                
                if misc[i, j] > 0:
                    nova_energia[i, j] += misc[i, j] * misc_energy_factor
                    misc[i, j] = 0
                
                nova_energia[i, j] += energy_growth

    
    
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            if novo_mundo[i, j] != 0:
                especie = novo_mundo[i, j]
                poder = nova_energia[i, j] + nova_forca[i, j] * 2
                for (x, y) in obter_vizinhos(i, j):
                    if novo_mundo[x, y] != 0 and novo_mundo[x, y] != especie:
                        poder_inimigo = nova_energia[x, y] + nova_forca[x, y] * 2
                        if poder > poder_inimigo:
                            novo_mundo[x, y] = especie
                            nova_energia[x, y] = max(poder - energy_cost, 0)
                            nova_forca[x, y] = nova_forca[i, j]
                        elif poder_inimigo > poder:
                            novo_mundo[i, j] = novo_mundo[x, y]
                            nova_energia[i, j] = max(poder_inimigo - energy_cost, 0)
                            nova_forca[i, j] = nova_forca[x, y]
                        else:
                            if random.random() < 0.5:
                                novo_mundo[x, y] = especie
                                nova_energia[x, y] = max(poder - energy_cost, 0)
                                nova_forca[x, y] = nova_forca[i, j]
                            else:
                                novo_mundo[i, j] = novo_mundo[x, y]
                                nova_energia[i, j] = max(poder_inimigo - energy_cost, 0)
                                nova_forca[i, j] = nova_forca[x, y]

    
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            celula = novo_mundo[i, j]
            if celula != 0:
                same = contar_vizinhos_por_especie(novo_mundo, i, j, celula)
                
                if same < 2 or same > 3 or nova_energia[i, j] > energy_threshold:
                    pass
                    novo_mundo[i, j] = 0
                    nova_energia[i, j] = 0
                    nova_forca[i, j] = 0
            else:
                count1 = contar_vizinhos_por_especie(novo_mundo, i, j, 1)
                count2 = contar_vizinhos_por_especie(novo_mundo, i, j, 2)
                if count1 == 3 and count2 != 3:
                    novo_mundo[i, j] = 1
                    nova_energia[i, j] = initial_energy
                    nova_forca[i, j] = initial_strength
                elif count2 == 3 and count1 != 3:
                    novo_mundo[i, j] = 2
                    nova_energia[i, j] = initial_energy
                    nova_forca[i, j] = initial_strength
                elif count1 == 3 and count2 == 3:
                    total_energy_1 = soma_energia_vizinhos(novo_mundo, energia, i, j, 1)
                    total_energy_2 = soma_energia_vizinhos(novo_mundo, energia, i, j, 2)
                    if total_energy_1 >= total_energy_2:
                        novo_mundo[i, j] = 1
                        nova_energia[i, j] = initial_energy
                        nova_forca[i, j] = initial_strength
                    else:
                        novo_mundo[i, j] = 2
                        nova_energia[i, j] = initial_energy
                        nova_forca[i, j] = initial_strength

    
    indices = [(i, j) for i in range(GRID_SIZE) for j in range(GRID_SIZE)]
    random.shuffle(indices)
    for (i, j) in indices:
        if novo_mundo[i, j] != 0:
            vizinhos = obter_vizinhos(i, j)
            empty_neighbors = [(x, y) for (x, y) in vizinhos if novo_mundo[x, y] == 0]
            if empty_neighbors and random.random() < p_move:
                new_i, new_j = random.choice(empty_neighbors)
                novo_mundo[new_i, new_j] = novo_mundo[i, j]
                nova_energia[new_i, new_j] = max(nova_energia[i, j] - energy_cost, 0)
                nova_forca[new_i, new_j] = nova_forca[i, j]
                #novo_mundo[i, j] = 0
                #nova_energia[i, j] = 0
                #nova_forca[i, j] = 0

    
    
    processed = set()
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            if novo_mundo[i, j] != 0:
                especie = novo_mundo[i, j]
                
                same_neighbors = [(x, y) for (x, y) in obter_vizinhos(i, j) if novo_mundo[x, y] == especie]
                local_density = len(same_neighbors)
                
                
                if local_density >= 4:
                    if random.random() < 0.15:  
                        pass
                        #novo_mundo[i, j] = 0
                        #nova_energia[i, j] = 0
                        #nova_forca[i, j] = 0
                
                elif local_density in [2, 3]:
                    r = random.random()
                    if r < 0.55:
                        
                        for (a, b) in obter_vizinhos(i, j):
                            if novo_mundo[a, b] == 0:
                                novo_mundo[a, b] = especie
                                nova_energia[a, b] = initial_energy
                                nova_forca[a, b] = initial_strength
                                break
                    elif r < 0.60:
                        
                        filhos_criados = 0
                        for (a, b) in obter_vizinhos(i, j):
                            if novo_mundo[a, b] == 0:
                                novo_mundo[a, b] = especie
                                nova_energia[a, b] = initial_energy
                                nova_forca[a, b] = initial_strength
                                filhos_criados += 1
                                if filhos_criados == 2:
                                    break
                    elif r < 0.80:
                        
                        if random.random() < 0.5:
                            pass
                            #novo_mundo[i, j] = 0
                            #nova_energia[i, j] = 0
                            #nova_forca[i, j] = 0
                        else:
                            if same_neighbors:
                                x, y = random.choice(same_neighbors)
                                novo_mundo[x, y] = 0
                                nova_energia[x, y] = 0
                                nova_forca[x, y] = 0
                    else:
                        
                        pass
                        processed.add((i, j, x, y))
    
    
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            if novo_mundo[i, j] == 0:
                if random.random() < 0.05:
                    food[i, j] = random.randint(1, 3)
                if random.random() < 0.03:
                    ore[i, j] = random.randint(1, 3)
                if random.random() < 0.03:
                    misc[i, j] = random.randint(1, 2)
    
    energia = nova_energia
    forca = nova_forca
    return novo_mundo


def exibir_mundo_visualmente(mundo):
    plt.cla()
    cmap = colors.ListedColormap(["white", "blue", "red"])
    plt.imshow(mundo, cmap=cmap, interpolation="nearest")
    plt.title("Simulador de Vida - Ambiente com Recursos")
    plt.pause(DELAY)


def main():
    # Obter configurações
    config = get_config()
    
    # Criar mundo
    world = World(
        size=config["grid_size"],
        prob_species1=config["prob_species1"],
        prob_species2=config["prob_species2"]
    )
    
    # Criar visualizador
    visualizer = Visualizer(world, config["delay"])
    
    # Loop principal
    while plt.get_fignums():
        world.update()
        visualizer.update()

if __name__ == "__main__":
    main()
