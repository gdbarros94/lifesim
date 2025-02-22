import matplotlib.pyplot as plt
from matplotlib import colors
import numpy as np
from world import World
from entities import EntityType, ResourceType

class Visualizer:
    def __init__(self, world: World, delay: float):
        self.world = world
        self.delay = delay
        self.fig, self.ax = plt.subplots(figsize=(8, 8))
        self.setup_plot()

    def setup_plot(self):
        plt.ion()
        # Cores para entidades (opacas)
        self.entity_colors = ["white", "blue", "red"]
        # Cores para recursos (semi-transparentes)
        self.resource_colors = ["none", "green", "gold", "purple"]
        # Cores para construções
        self.construction_colors = ["black", "pink"]  # Preto para time azul, rosa para vermelho
        self.resource_alpha = {
            ResourceType.FOOD: 0.3,
            ResourceType.ORE: 0.5,
            ResourceType.MISC: 0.3
        }

    def update(self):
        self.ax.clear()

        # Criar grade base branca
        base_grid = np.zeros((self.world.size, self.world.size))
        self.ax.imshow(base_grid, cmap=colors.ListedColormap(["white"]))

        # Plotar recursos com transparência
        for i in range(self.world.size):
            for j in range(self.world.size):
                resource = self.world.resources[i][j]
                if resource is not None:
                    if resource.type == ResourceType.FOOD:
                        color = "green"
                        alpha = self.resource_alpha[ResourceType.FOOD]
                    elif resource.type == ResourceType.ORE:
                        color = "gold"
                        alpha = self.resource_alpha[ResourceType.ORE]
                    else:  # MISC
                        color = "purple"
                        alpha = self.resource_alpha[ResourceType.MISC]
                    
                    self.ax.add_patch(plt.Rectangle((j-0.5, i-0.5), 1, 1, 
                                                  facecolor=color, 
                                                  alpha=alpha))

        # Plotar construções
        for i in range(self.world.size):
            for j in range(self.world.size):
                construction = self.world.constructions[i][j]
                if construction:
                    team_idx = construction.owner_type.value - 1
                    color = self.construction_colors[team_idx]
                    
                    # Opacidade baseada na ocupação
                    occupation_ratio = len(construction.occupants) / construction.max_occupants
                    alpha = 0.3 + (occupation_ratio * 0.7)  # Varia de 0.3 a 1.0
                    
                    self.ax.add_patch(plt.Rectangle((j-0.5, i-0.5), 1, 1,
                                                  facecolor=color,
                                                  alpha=alpha))
                    
                    # Adicionar número de ocupantes
                    num_occupants = len(construction.occupants)
                    self.ax.text(j, i, str(num_occupants),
                               ha='center', va='center',
                               color='white' if team_idx == 0 else 'black',  # Texto branco para construções pretas
                               fontweight='bold',
                               fontsize=10)

        # Visualizar entidades
        entity_grid = np.array([[0 if cell is None else cell.type.value 
                               for cell in row] 
                              for row in self.world.grid])

        # Plotar entidades
        for i in range(self.world.size):
            for j in range(self.world.size):
                if entity_grid[i,j] > 0:
                    color = self.entity_colors[entity_grid[i,j]]
                    self.ax.add_patch(plt.Rectangle((j-0.5, i-0.5), 1, 1, 
                                                  facecolor=color))

        # Configurar limites e grade
        self.ax.set_xlim(-0.5, self.world.size-0.5)
        self.ax.set_ylim(-0.5, self.world.size-0.5)
        self.ax.grid(True)

        # Adicionar contagem de entidades e recursos ao título
        title = f"Simulador de Vida - Ambiente com Recursos\n"
        title += f"Time Azul: {self.world.species1_count} seres, {self.world.construction1_count} construções\n"
        title += f"Recursos Time Azul - Ore: {self.world.resources1[ResourceType.ORE]}, Misc: {self.world.resources1[ResourceType.MISC]}\n"
        title += f"Time Vermelho: {self.world.species2_count} seres, {self.world.construction2_count} construções\n"
        title += f"Recursos Time Vermelho - Ore: {self.world.resources2[ResourceType.ORE]}, Misc: {self.world.resources2[ResourceType.MISC]}"
        self.ax.set_title(title)

        plt.pause(self.delay) 