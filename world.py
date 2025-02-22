import numpy as np
import random
from typing import List, Tuple, Optional
from entities import Entity, EntityType, EntityRole, Resource, ResourceType

class World:
    def __init__(self, size: int, prob_species1: float, prob_species2: float):
        self.size = size
        self.grid = [[None for _ in range(size)] for _ in range(size)]
        self.resources = [[None for _ in range(size)] for _ in range(size)]
        self.constructions = [[None for _ in range(size)] for _ in range(size)]
        
        # Contadores
        self.species1_count = 0
        self.species2_count = 0
        self.construction1_count = 0
        self.construction2_count = 0
        self.resources1 = {ResourceType.ORE: 0, ResourceType.MISC: 0}
        self.resources2 = {ResourceType.ORE: 0, ResourceType.MISC: 0}
        
        self.armies = {
            EntityType.SPECIES1: [],  # Lista de grupos de seres
            EntityType.SPECIES2: []
        }
        
        self.initialize_world(prob_species1, prob_species2)

    def initialize_world(self, prob_species1: float, prob_species2: float) -> None:
        # Inicializar entidades
        for i in range(self.size):
            for j in range(self.size):
                rand = random.random()
                if rand < prob_species1:
                    self.grid[i][j] = Entity(EntityType.SPECIES1)
                elif rand < prob_species1 + prob_species2:
                    self.grid[i][j] = Entity(EntityType.SPECIES2)
        
        # Inicializar minério (apenas uma vez)
        num_ore_deposits = int(self.size * self.size * 0.05)  # 5% do mapa terá minério
        ore_positions = []
        while len(ore_positions) < num_ore_deposits:
            i = random.randint(0, self.size-1)
            j = random.randint(0, self.size-1)
            if (i,j) not in ore_positions:
                ore_positions.append((i,j))
                self.resources[i][j] = Resource.create_ore()

    def get_neighbors(self, x: int, y: int) -> List[Tuple[int, int]]:
        neighbors = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                new_x, new_y = x + dx, y + dy
                if 0 <= new_x < self.size and 0 <= new_y < self.size:
                    neighbors.append((new_x, new_y))
        return neighbors

    def count_entities(self):
        self.species1_count = 0
        self.species2_count = 0
        self.construction1_count = 0
        self.construction2_count = 0
        self.resources1 = {ResourceType.ORE: 0, ResourceType.MISC: 0}
        self.resources2 = {ResourceType.ORE: 0, ResourceType.MISC: 0}
        
        # Contar entidades na grade e seus recursos
        for i in range(self.size):
            for j in range(self.size):
                entity = self.grid[i][j]
                if entity:
                    if entity.type == EntityType.SPECIES1:
                        self.species1_count += 1
                        for resource_type in [ResourceType.ORE, ResourceType.MISC]:
                            self.resources1[resource_type] += entity.inventory[resource_type]
                    elif entity.type == EntityType.SPECIES2:
                        self.species2_count += 1
                        for resource_type in [ResourceType.ORE, ResourceType.MISC]:
                            self.resources2[resource_type] += entity.inventory[resource_type]
        
        # Contar construções e entidades dentro delas
        for i in range(self.size):
            for j in range(self.size):
                construction = self.constructions[i][j]
                if construction:
                    if construction.owner_type == EntityType.SPECIES1:
                        self.construction1_count += 1
                        self.species1_count += len(construction.occupants)
                        for occupant in construction.occupants:
                            for resource_type in [ResourceType.ORE, ResourceType.MISC]:
                                self.resources1[resource_type] += occupant.inventory[resource_type]
                    else:
                        self.construction2_count += 1
                        self.species2_count += len(construction.occupants)
                        for occupant in construction.occupants:
                            for resource_type in [ResourceType.ORE, ResourceType.MISC]:
                                self.resources2[resource_type] += occupant.inventory[resource_type]

    def update(self) -> None:
        new_grid = [[None for _ in range(self.size)] for _ in range(self.size)]
        defenders_to_return = []  # Lista de defensores que devem voltar para construção
        
        # Primeira fase: Movimento inteligente e Consumo de Recursos
        for i in range(self.size):
            for j in range(self.size):
                entity = self.grid[i][j]
                if entity is None or entity.is_sheltered:
                    continue

                # Verificar se há construção inimiga próxima
                for nx, ny in self.get_neighbors(i, j):
                    construction = self.constructions[nx][ny]
                    if construction and construction.owner_type != entity.type:
                        # Atacar construção
                        construction.take_damage(entity.get_power() * 0.2)
                        print(f"Construção atacada na posição ({nx}, {ny})")
                        
                        # Fazer defensores saírem
                        if construction.occupants:
                            print(f"{len(construction.occupants)} defensores saindo para proteger a construção!")
                            # Encontrar posições livres ao redor
                            empty_positions = []
                            for dx, dy in self.get_neighbors(nx, ny):
                                if self.grid[dx][dy] is None and new_grid[dx][dy] is None:
                                    empty_positions.append((dx, dy))
                            
                            # Colocar defensores em posições livres
                            random.shuffle(empty_positions)
                            for defender in construction.occupants[:]:
                                if empty_positions:
                                    dx, dy = empty_positions.pop()
                                    construction.remove_occupant(defender)
                                    new_grid[dx][dy] = defender
                                    defenders_to_return.append((defender, construction))
                                    print(f"Defensor posicionado em ({dx}, {dy})")
                                else:
                                    break
                        
                        if construction.energy <= 0:
                            self.constructions[nx][ny] = None
                            print(f"Construção destruída na posição ({nx}, {ny})")

                # Consumir recursos
                if self.resources[i][j]:
                    entity.consume_resource(self.resources[i][j])
                    self.resources[i][j] = None

                # Buscar alvos
                target = self.find_nearest_target(i, j, entity)
                
                if target:
                    tx, ty, action = target
                    
                    if action == "attack" and self.manhattan_distance(i, j, tx, ty) <= 1:
                        # Atacar construção
                        construction = self.constructions[tx][ty]
                        if construction:
                            construction.take_damage(entity.get_power() * 0.2)
                            if construction.energy <= 0:
                                self.constructions[tx][ty] = None
                                print(f"Construção destruída na posição ({tx}, {ty})")
                    
                    elif action == "mate" and self.manhattan_distance(i, j, tx, ty) <= 1:
                        # Reproduzir com parceiro
                        partner = self.grid[tx][ty]
                        if partner and partner.can_reproduce() and entity.can_reproduce():
                            empty_neighbors = [(x, y) for x, y in self.get_neighbors(i, j)
                                            if self.grid[x][y] is None]
                            if empty_neighbors:
                                child_x, child_y = random.choice(empty_neighbors)
                                new_grid[child_x][child_y] = entity.reproduce()
                                print(f"Reprodução ocorreu na posição ({child_x}, {child_y})")
                    
                    elif action == "shelter" and self.manhattan_distance(i, j, tx, ty) <= 1:
                        # Entrar na construção
                        construction = self.constructions[tx][ty]
                        if construction and construction.add_occupant(entity):
                            continue
                    
                    # Mover em direção ao alvo
                    new_x, new_y = self.move_towards(entity, (i, j), (tx, ty))
                    if (new_x, new_y) != (i, j):
                        new_grid[new_x][new_y] = entity
                        continue

                # Se não conseguiu mover para o alvo, mover aleatoriamente
                if random.random() < 0.2:
                    empty_neighbors = [(x, y) for x, y in self.get_neighbors(i, j)
                                    if self.grid[x][y] is None]
                    if empty_neighbors:
                        new_x, new_y = random.choice(empty_neighbors)
                        new_grid[new_x][new_y] = entity
                        continue

                new_grid[i][j] = entity

        # Segunda fase: Combate e Reprodução
        for i in range(self.size):
            for j in range(self.size):
                entity = new_grid[i][j]
                if entity is None:
                    continue

                # Combate
                for nx, ny in self.get_neighbors(i, j):
                    neighbor = new_grid[nx][ny]
                    if (neighbor and 
                        neighbor.type != entity.type and 
                        entity.get_power() > neighbor.get_power()):
                        new_grid[nx][ny] = None

                # Reprodução
                if entity.can_reproduce():
                    empty_neighbors = [(x, y) for x, y in self.get_neighbors(i, j)
                                    if new_grid[x][y] is None]
                    if empty_neighbors:
                        child_x, child_y = random.choice(empty_neighbors)
                        new_grid[child_x][child_y] = entity.reproduce()

        self.grid = new_grid
        self.update_resources()

        # Atualizar construções e reprodução dentro delas
        for i in range(self.size):
            for j in range(self.size):
                entity = self.grid[i][j]
                
                # Verificar mineração de ore
                if (entity and entity.role == EntityRole.MINER and 
                    self.resources[i][j] and self.resources[i][j].type == ResourceType.ORE):
                    print(f"Minério minerado por {'Time Azul' if entity.type == EntityType.SPECIES1 else 'Time Vermelho'} na posição ({i}, {j})")
                
                # Verificar construção
                if entity and entity.can_build():
                    empty_neighbors = sum(1 for x, y in self.get_neighbors(i, j)
                                       if self.grid[x][y] is None and 
                                          self.constructions[x][y] is None)
                    if empty_neighbors >= 3:
                        construction = entity.build_construction((i, j))
                        if construction:
                            self.constructions[i][j] = construction
                            team = "Time Azul" if entity.type == EntityType.SPECIES1 else "Time Vermelho"
                            print(f"Nova construção do {team} na posição ({i}, {j})")
                    
                    # Verificar ameaças e resto do código das construções...
                    threats = []
                    for nx, ny in self.get_neighbors(i, j):
                        enemy = self.grid[nx][ny]
                        if enemy and enemy.type != construction.owner_type:
                            threats.append((enemy, (nx, ny)))
                    
                    if threats:
                        # Defender a construção
                        for occupant in construction.occupants[:]:
                            construction.remove_occupant(occupant)
                            # Encontrar posição livre próxima
                            for nx, ny in self.get_neighbors(i, j):
                                if self.grid[nx][ny] is None:
                                    self.grid[nx][ny] = occupant
                                    break

        # Permitir construção de novas estruturas
        for i in range(self.size):
            for j in range(self.size):
                entity = self.grid[i][j]
                if entity and entity.can_build():
                    # Verificar se há espaço adequado para construção
                    empty_neighbors = sum(1 for x, y in self.get_neighbors(i, j)
                                       if self.grid[x][y] is None and 
                                          self.constructions[x][y] is None)
                    if empty_neighbors >= 3:  # Precisa de espaço
                        construction = entity.build_construction((i, j))
                        if construction:
                            self.constructions[i][j] = construction

        # Permitir que entidades entrem em construções aliadas
        for i in range(self.size):
            for j in range(self.size):
                entity = self.grid[i][j]
                if entity and not entity.is_sheltered:
                    for nx, ny in self.get_neighbors(i, j):
                        construction = self.constructions[nx][ny]
                        if (construction and 
                            construction.owner_type == entity.type and
                            construction.add_occupant(entity)):
                            self.grid[i][j] = None
                            break

        # Mineradores procuram construtores para entregar recursos
        for i in range(self.size):
            for j in range(self.size):
                entity = self.grid[i][j]
                if (entity and 
                    entity.role == EntityRole.MINER and 
                    (entity.inventory[ResourceType.ORE] > 0 or 
                     entity.inventory[ResourceType.MISC] > 0)):
                    
                    # Procurar construtor nas vizinhanças
                    for nx, ny in self.get_neighbors(i, j):
                        neighbor = self.grid[nx][ny]
                        if (neighbor and 
                            neighbor.role == EntityRole.BUILDER and 
                            neighbor.type == entity.type):
                            entity.transfer_to_builder(neighbor)
                            break

        # Tentar retornar defensores para suas construções
        for defender, construction in defenders_to_return:
            if (not defender.is_sheltered and  # Defensor ainda vivo e fora da construção
                construction and  # Construção ainda existe
                construction.energy > 0):  # Construção não foi destruída
                
                cx, cy = construction.position
                # Verificar se está adjacente à construção
                for nx, ny in self.get_neighbors(cx, cy):
                    if self.grid[nx][ny] == defender:
                        # Tentar retornar para a construção
                        if construction.add_occupant(defender):
                            self.grid[nx][ny] = None
                            print(f"Defensor retornou para a construção em ({cx}, {cy})")
                        break

        # Atualizar contagem de entidades
        self.count_entities()

        # Verificar formação de novos exércitos (apenas com seres normais)
        for team in [EntityType.SPECIES1, EntityType.SPECIES2]:
            team_entities = []
            for i in range(self.size):
                for j in range(self.size):
                    entity = self.grid[i][j]
                    if (entity and 
                        entity.type == team and 
                        not entity.is_sheltered and
                        entity.role == EntityRole.NORMAL):  # Apenas seres normais
                        team_entities.append(entity)
                        entity.position = (i, j)
            
            if len(team_entities) >= 10:
                potential_army = team_entities[:10]
                self.form_army(potential_army)

        # Atualizar exércitos existentes
        self.update_armies()

    def update_resources(self) -> None:
        for i in range(self.size):
            for j in range(self.size):
                if self.resources[i][j] is None:
                    # Gerar apenas comida e misc, não minério
                    for resource_type in [ResourceType.FOOD, ResourceType.MISC]:
                        resource = Resource.create_random(resource_type)
                        if resource:
                            self.resources[i][j] = resource
                            break 

    def manhattan_distance(self, x1: int, y1: int, x2: int, y2: int) -> int:
        return abs(x1 - x2) + abs(y1 - y2)

    def find_nearest_target(self, x: int, y: int, entity: Entity, max_distance: int = 10) -> Optional[Tuple[int, int]]:
        """Encontra o alvo mais próximo (construção inimiga, parceiro ou construção aliada)"""
        best_distance = max_distance + 1
        best_target = None
        
        for i in range(self.size):
            for j in range(self.size):
                distance = self.manhattan_distance(x, y, i, j)
                if distance > max_distance:
                    continue
                    
                # Procurar construção inimiga para atacar
                construction = self.constructions[i][j]
                if (construction and 
                    construction.owner_type != entity.type and 
                    distance < best_distance):
                    best_distance = distance
                    best_target = (i, j, "attack")
                
                # Se não estiver procurando ataque, procurar parceiro/abrigo
                elif distance < best_distance:
                    # Procurar construção aliada com espaço
                    if (construction and 
                        construction.owner_type == entity.type and
                        len(construction.occupants) < construction.max_occupants):
                        best_distance = distance
                        best_target = (i, j, "shelter")
                    
                    # Procurar parceiro para reprodução
                    partner = self.grid[i][j]
                    if (partner and 
                        partner.type == entity.type and 
                        partner != entity and
                        partner.can_reproduce() and 
                        entity.can_reproduce()):
                        best_distance = distance
                        best_target = (i, j, "mate")
        
        return best_target

    def move_towards(self, entity: Entity, current_pos: Tuple[int, int], target_pos: Tuple[int, int]) -> Tuple[int, int]:
        """Move a entidade em direção ao alvo"""
        cx, cy = current_pos
        tx, ty = target_pos
        
        # Calcular direção do movimento
        dx = 1 if tx > cx else -1 if tx < cx else 0
        dy = 1 if ty > cy else -1 if ty < cy else 0
        
        # Tentar mover na direção calculada
        new_x = cx + dx
        new_y = cy + dy
        
        if (0 <= new_x < self.size and 
            0 <= new_y < self.size and 
            self.grid[new_x][new_y] is None):
            return (new_x, new_y)
        
        return current_pos 

    def form_army(self, entities: List[Entity]) -> None:
        """Agrupa entidades em um exército, apenas com guerreiros (papel NORMAL)"""
        # Filtrar apenas seres normais (não construtores/mineradores)
        warriors = [e for e in entities if e.role == EntityRole.NORMAL]
        
        if len(warriors) >= 8:
            team = warriors[0].type
            self.armies[team].append(warriors)
            print(f"Novo exército formado para o {'Time Azul' if team == EntityType.SPECIES1 else 'Time Vermelho'} com {len(warriors)} guerreiros")

    def update_armies(self) -> None:
        """Atualiza o comportamento dos exércitos"""
        for team in [EntityType.SPECIES1, EntityType.SPECIES2]:
            for army in self.armies[team][:]:  # Copiar lista para poder modificar
                # Remover soldados mortos
                army[:] = [soldier for soldier in army if soldier.energy > 0]
                
                if len(army) < 4:  # Exército muito pequeno, dissolver
                    self.armies[team].remove(army)
                    continue
                
                # Encontrar inimigos próximos ou construções inimigas
                enemies = []
                for i in range(self.size):
                    for j in range(self.size):
                        entity = self.grid[i][j]
                        if entity and entity.type != team:
                            enemies.append((entity, (i, j)))
                
                if enemies:
                    # Atacar inimigo mais próximo
                    target, pos = min(enemies, key=lambda e: self.manhattan_distance(
                        army[0].position[0], army[0].position[1], e[1][0], e[1][1]))
                    
                    # Mover exército em direção ao alvo
                    for soldier in army:
                        if not soldier.position:
                            continue
                        new_pos = self.move_towards(soldier, soldier.position, pos)
                        if new_pos != soldier.position:
                            self.grid[soldier.position[0]][soldier.position[1]] = None
                            self.grid[new_pos[0]][new_pos[1]] = soldier
                            soldier.position = new_pos 