from dataclasses import dataclass
from enum import Enum
import random
from typing import List, Tuple, Optional, Dict

class EntityType(Enum):
    EMPTY = 0
    SPECIES1 = 1
    SPECIES2 = 2

class EntityRole(Enum):
    NORMAL = 0
    BUILDER = 1
    MINER = 2  # Novo papel

class ResourceType(Enum):
    FOOD = "food"
    ORE = "ore"
    MISC = "misc"

@dataclass
class Resource:
    type: ResourceType
    amount: int
    energy_factor: float
    strength_factor: float

    @staticmethod
    def create_random(resource_type: ResourceType) -> Optional['Resource']:
        if resource_type == ResourceType.ORE:  # Minério não gera aleatoriamente
            return None
        
        if random.random() < 0.1:
            amount = random.randint(1, 3)
            if resource_type == ResourceType.FOOD:
                return Resource(resource_type, amount, 1.0, 0.0)
            elif resource_type == ResourceType.MISC:
                return Resource(resource_type, amount, 0.5, 0.5)
        return None

    @staticmethod
    def create_ore(amount: int = 3) -> 'Resource':
        return Resource(ResourceType.ORE, amount, 3.0, 2.0)  # Minério dá mais energia e força

@dataclass
class Construction:
    owner_type: EntityType
    position: Tuple[int, int]
    energy: float = 100.0
    max_occupants: int = 10
    occupants: List['Entity'] = None
    last_reproduction: int = 0
    
    def __post_init__(self):
        if self.occupants is None:
            self.occupants = []
    
    def add_occupant(self, entity: 'Entity') -> bool:
        if len(self.occupants) < self.max_occupants:
            self.occupants.append(entity)
            entity.is_sheltered = True
            entity.current_construction = self
            return True
        return False
    
    def remove_occupant(self, entity: 'Entity'):
        if entity in self.occupants:
            # Não remover construtores/mineradores se estiver sob ataque
            if entity.role != EntityRole.NORMAL and len(self.occupants) <= 2:
                return
            self.occupants.remove(entity)
            entity.is_sheltered = False
            entity.current_construction = None
    
    def take_damage(self, amount: float) -> bool:
        """
        Aplica dano à construção e retorna True se ela foi destruída
        """
        self.energy -= amount
        if self.energy <= 0:
            # Expulsar todos os ocupantes
            for entity in self.occupants[:]:
                self.remove_occupant(entity)
        return self.energy <= 0
    
    def try_reproduce(self) -> Optional['Entity']:
        if len(self.occupants) >= 2:  # Precisa de pelo menos 2 seres
            if len(self.occupants) >= self.max_occupants:
                # Se estiver lotado, liberar apenas seres normais para formar exército
                normal_occupants = [o for o in self.occupants if o.role == EntityRole.NORMAL]
                special_occupants = [o for o in self.occupants if o.role != EntityRole.NORMAL]
                
                if len(normal_occupants) >= 8:
                    army = normal_occupants[:8]  # Pegar 8 seres normais
                    # Manter especiais e 2 normais para reprodução
                    self.occupants = special_occupants + normal_occupants[8:]
                    
                    for soldier in army:
                        self.remove_occupant(soldier)
                    print(f"Exército de 8 guerreiros formado da construção em {self.position}")
                    return army
            
            elif self.last_reproduction >= 2:
                parent1, parent2 = random.sample(self.occupants, 2)
                avg_energy = (parent1.energy + parent2.energy) * 0.5
                avg_strength = (parent1.strength + parent2.strength) * 0.5
                
                child = Entity(self.owner_type, avg_energy * 1.2, avg_strength * 1.2)
                
                if self.add_occupant(child):
                    parent1.energy *= 0.9
                    parent2.energy *= 0.9
                    self.last_reproduction = 0
                    print(f"Novo ser gerado na construção em {self.position}. Total: {len(self.occupants)}")
                
        return None
    
    def update(self):
        self.last_reproduction += 1

class Entity:
    def __init__(self, entity_type: EntityType, initial_energy: float = 2.0, initial_strength: float = 1.0):
        self.type = entity_type
        self.energy = initial_energy
        self.strength = initial_strength
        self.age = 0
        self.mutations = []
        self.last_reproduction = 0
        self.position: Optional[Tuple[int, int]] = None
        
        # Sistema de roles com probabilidades aumentadas
        role_chance = random.random()
        if role_chance < 0.16:  # 16% chance de ser construtor
            self.role = EntityRole.BUILDER
        elif role_chance < 0.32:  # 16% chance de ser minerador
            self.role = EntityRole.MINER
        else:
            self.role = EntityRole.NORMAL
            
        self.inventory: Dict[ResourceType, int] = {
            ResourceType.ORE: 0,
            ResourceType.MISC: 0
        }
        self.is_sheltered = False
        self.current_construction = None

    def get_power(self) -> float:
        base_power = self.energy + (self.strength * 2)
        if self.is_sheltered:
            base_power *= 1.5  # Bônus de poder quando protegido
        return base_power

    def can_build(self) -> bool:
        return (self.role == EntityRole.BUILDER and 
                self.inventory[ResourceType.ORE] >= 1 and 
                self.inventory[ResourceType.MISC] >= 2)

    def build_construction(self, position: Tuple[int, int]) -> Optional[Construction]:
        if not self.can_build():
            return None
        
        # Consumir recursos
        self.inventory[ResourceType.ORE] -= 1
        self.inventory[ResourceType.MISC] -= 2
        
        # Criar construção
        construction = Construction(self.type, position)
        construction.add_occupant(self)
        return construction

    def can_mine(self) -> bool:
        return self.role == EntityRole.MINER

    def transfer_to_builder(self, builder: 'Entity') -> bool:
        if (builder.role == EntityRole.BUILDER and 
            self.type == builder.type):  # Mesmo time
            # Transferir todos os recursos
            for resource_type in [ResourceType.ORE, ResourceType.MISC]:
                amount = self.inventory[resource_type]
                if amount > 0:
                    builder.inventory[resource_type] += amount
                    self.inventory[resource_type] = 0
            return True
        return False

    def consume_resource(self, resource: Resource) -> None:
        if resource.type == ResourceType.ORE and not self.can_mine():
            return  # Apenas mineradores podem coletar minério
            
        if resource.type in [ResourceType.ORE, ResourceType.MISC]:
            self.inventory[resource.type] += resource.amount
        self.energy += resource.amount * resource.energy_factor
        self.strength += resource.amount * resource.strength_factor

    def transfer_resources(self, other: 'Entity', resource_type: ResourceType, amount: int) -> bool:
        if (self.type == other.type and  # Mesmo time
            self.inventory[resource_type] >= amount):
            self.inventory[resource_type] -= amount
            other.inventory[resource_type] += amount
            return True
        return False

    def can_reproduce(self) -> bool:
        return (self.energy > 2.85 and  # Reduzido de 3 para 2.85 (5% menos energia necessária)
                self.age > 1 and  # Reduzido de 2 para 1 (reprodução mais cedo)
                self.age - self.last_reproduction > 1)

    def reproduce(self) -> 'Entity':
        child = Entity(self.type, self.energy * 0.4, self.strength)
        self.energy *= 0.6
        self.last_reproduction = self.age
        
        if random.random() < 0.15:
            mutation = random.choice(['energy+', 'strength+', 'efficiency+'])
            child.mutations = self.mutations + [mutation]
            if mutation == 'energy+':
                child.energy *= 1.2
            elif mutation == 'strength+':
                child.strength *= 1.2
        
        return child

    def update(self) -> None:
        self.age += 1
        self.energy = max(0, self.energy - 0.08) 