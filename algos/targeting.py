"""
Основаная идея заключалается в отстреле кораблей противника по одному
"""

import json
from dataclasses import dataclass
from enum import Enum
from typing import List
from random import random, randint, choice


# region Primitives


@dataclass
class Vector:
    x: int
    y: int
    z: int

    def __add__(self, other):
        if not isinstance(other, Vector):
            raise TypeError()
        return Vector(self.x + other.x,
                      self.y + other.y,
                      self.z + other.z)

    def __sub__(self, other):
        if not isinstance(other, Vector):
            raise TypeError()
        return Vector(self.x - other.x,
                      self.y - other.y,
                      self.z - other.z)

    def __str__(self):
        return f'{self.x}/{self.y}/{self.z}'

    @property
    def coords(self):
        return self.x, self.y, self.z

    @classmethod
    def from_json(cls, data: str):
        x, y, z = map(int, data.split('/'))
        return cls(x, y, z)


# endregion


# region Utils


class JSONCapability:
    def to_json(self) -> dict:
        return {k: str(v) if isinstance(v, Vector) else v
                for k, v in self.__dict__.items() if v is not None}


class Physics:
    @staticmethod
    def clen(v: Vector) -> int:
        """Метрика Чебышёва"""
        return max(map(abs, v.coords))

    @staticmethod
    def mlen(v: Vector) -> int:
        """Манхэттенская метрика"""
        return sum(map(abs, v.coords))

    @staticmethod
    def get_len_vector(vector_difference: Vector) -> int:
        # метод, который находит длину раззности векторов
        return sum(value ** 2 for value in vector_difference.__dict__.values()) ** 0.5


# endregion


# region Equipment


class BlockType(Enum):
    Energy = 0
    Gun = 1
    Engine = 2
    Health = 3


class EffectType(Enum):
    Blaster = 0


@dataclass
class Block(JSONCapability):
    Name: str
    Type: BlockType

    @classmethod
    def from_json(cls, data):
        if BlockType(data['Type']) == BlockType.Energy:
            return EnergyBlock(**data)
        elif BlockType(data['Type']) == BlockType.Gun:
            return GunBlock(**data)
        elif BlockType(data['Type']) == BlockType.Engine:
            return EngineBlock(**data)
        elif BlockType(data['Type']) == BlockType.Health:
            return HealthBlock(**data)


@dataclass
class EnergyBlock(Block):
    Type = BlockType.Energy
    IncrementPerTurn: int
    MaxEnergy: int
    StartEnergy: int


@dataclass
class GunBlock(Block):
    Type = BlockType.Gun
    Damage: int
    EnergyPrice: int
    Radius: int
    EffectType: int


@dataclass
class EngineBlock(Block):
    Type = BlockType.Engine
    MaxAccelerate: int


@dataclass
class HealthBlock(Block):
    Type = BlockType.Health
    MaxHealth: int
    StartHealth: int


# endregion


# region Draft Input


@dataclass
class DraftCompleteShip(JSONCapability):
    Id: str
    Price: int
    Equipment: List[str]

    @classmethod
    def from_json(cls, data):
        return cls(**data)


@dataclass
class DraftEquipment(JSONCapability):
    Size: int
    Equipment: List[Block]

    @classmethod
    def from_json(cls, data):
        data['Equipment'] = list(map(Block.from_json, data['Equipment']))
        return cls(**data)


@dataclass
class MapRegion(JSONCapability):
    From: Vector
    To: Vector

    @classmethod
    def from_json(cls, data):
        data['From'] = Vector.from_json(data['From'])
        data['To'] = Vector.from_json(data['To'])
        return cls(**data)


@dataclass
class DraftOptions(JSONCapability):
    PlayerId: int
    MapSize: int
    Money: int
    MaxShipsCount: int
    DraftTimeout: int
    BattleRoundTimeout: int
    StartArea: MapRegion
    Equipment: List[DraftEquipment]
    Ships: List[DraftCompleteShip]

    @classmethod
    def from_json(cls, data):
        data['StartArea'] = MapRegion.from_json(['StartArea'])
        data['Equipment'] = list(map(DraftEquipment.from_json, data['Equipment']))
        data['Ships'] = list(map(DraftCompleteShip.from_json, data['Ships']))
        return cls(**data)


# endregion


# region Draft Output


@dataclass
class DraftShipChoice:
    CompleteShipId: str
    Position: Vector = None


@dataclass
class DraftChoice:
    Ships: List[DraftShipChoice] = None
    Message: str = None


# endregion


# region Battle Input


@dataclass
class Ship(JSONCapability):
    Id: int
    Position: Vector
    Velocity: Vector
    Health: int = None
    Energy: int = None
    Equipment: List[Block] = None

    @classmethod
    def from_json(cls, data):
        if data.get('Equipment'):  # не доступно для оппонента
            data['Equipment'] = list(map(Block.from_json, data.get('Equipment', [])))
        data['Position'] = Vector.from_json(data['Position'])
        data['Velocity'] = Vector.from_json(data['Velocity'])
        return cls(**data)


@dataclass
class FireInfo(JSONCapability):
    Source: Vector
    Target: Vector
    EffectType: EffectType

    @classmethod
    def from_json(cls, data):
        data['Source'] = Vector.from_json(data['Source'])
        data['Target'] = Vector.from_json(data['Target'])
        return cls(**data)


@dataclass
class State(JSONCapability):
    My: List[Ship]
    Opponent: List[Ship]
    FireInfos: List[FireInfo]

    @classmethod
    def from_json(cls, data):
        data['My'] = list(map(Ship.from_json, data['My']))
        data['Opponent'] = list(map(Ship.from_json, data['Opponent']))
        data['FireInfos'] = list(map(FireInfo.from_json, data['FireInfos']))
        return cls(**data)


# endregion


# region Battle Output


MOVE = 'MOVE'
ACCELERATE = 'ACCELERATE'
ATTACK = 'ATTACK'


@dataclass
class CommandParameters(JSONCapability):
    pass


@dataclass
class MoveParameters(CommandParameters):
    Id: int
    Target: Vector


@dataclass
class AccelerateParameters(CommandParameters):
    Id: int
    Vector: Vector


@dataclass
class AttackParameters(CommandParameters):
    Id: int
    Name: str
    Target: Vector


@dataclass
class Command(JSONCapability):
    Command: str
    Parameters: CommandParameters


@dataclass
class UserOutput(JSONCapability):
    UserCommands: List[Command] = None
    Message: str = None


# endregion


class Game:
    def __init__(self):
        self.targeted = None
        # вес ближайшего врага ко всем
        self.main_particle_weight = 0.9
        # вес ближайшего врага к конкретной частице
        self.best_particle_weight = 0.1

    @staticmethod
    def draft(_: dict) -> DraftChoice:
        return DraftChoice()  # корабли набираются автоматически]

    def velocity_change(self, closest_enemy: Ship, ship: Ship) -> dict:
        # собственно метод алгоритма роя
        # вынес словари в переменные, чтобы не создавать их десятки раз, пока мы в списочном выражении
        targeted_position_dict = self.targeted.Position.__dict__
        closest_enemy_position_dict = closest_enemy.Position.__dict__
        ship_position_dict = ship.Position.__dict__
        best_particle_weight_koef = random()
        main_particle_weight_koef = random()

        # перевел это на конкретную задачу (https://jenyay.net/Programming/ParticleSwarm#:~:text=vi%2Ct%2B1%20%3D%20vi%2Ct%20%2B%20%CF%86p%20rp%20(pi%20-%20xi%2C%20t)%20%2B%20%CF%86g%20rg%20(gi%20-%20xi%2C%20t))
        return {
            key: (
                    value + self.best_particle_weight * best_particle_weight_koef *
                    (closest_enemy_position_dict[key] - ship_position_dict[key]) +
                    main_particle_weight_koef * random() *
                    (targeted_position_dict[key] - ship_position_dict[key]))
            for key, value in ship.Velocity.__dict__.items()}

    def battle(self, data: dict) -> UserOutput:
        state = State.from_json(data)
        user_output = UserOutput()

        '''# если "жертва" ещё не выбрана или была убита, флот выбирает новую
        if self.targeted_id is None or self.targeted_id not in [x.Id for x in state.Opponent]:'''
        # так как корабли движутся, цель выбираем каждый ход
        # сумма расстояний от всех кораблей до новой жертвы должна быть наименьшей
        self.targeted = min(state.Opponent,
                            key=lambda x: sum([Physics.get_len_vector(y.Position - x.Position) for y in state.My]))

        user_output.UserCommands = []
        for ship in state.My:
            guns = [x for x in ship.Equipment if isinstance(x, GunBlock)]

            if guns:
                # корабль выбирает оружие с наибольшей дальностью
                ranged_gun = max(guns, key=lambda x: x.Radius)

                # ближайший оппонент к текущему кораблю
                closest_enemy = min(state.Opponent, key=lambda x: Physics.get_len_vector(ship.Position - x.Position))

                # Проверка, что оружие достанет до "жертвы" (взял с запасом)
                if ranged_gun.Radius * 3 >= Physics.get_len_vector(ship.Position - closest_enemy.Position):
                    user_output.UserCommands.append(Command(Command=ATTACK,
                                                            Parameters=AttackParameters(
                                                                Id=ship.Id,
                                                                Name=ranged_gun.Name,
                                                                Target=closest_enemy.Position)))

                ship.Velocity.__dict__ = self.velocity_change(closest_enemy, ship)

                user_output.UserCommands.append(Command(Command=MOVE,
                                                        Parameters=MoveParameters(Id=ship.Id,
                                                                                  Target=self.targeted.Position)))
        return user_output

    def main(self):
        while True:
            line_in = input()
            data = json.loads(line_in)

            if 'PlayerId' in data:
                result = self.draft(data)
            else:
                result = self.battle(data)

            line_out = json.dumps(result,
                                  default=JSONCapability.to_json,
                                  ensure_ascii=False)
            print(line_out)


if __name__ == '__main__':
    Game().main()
