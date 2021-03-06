"""
Файл-шаблон для всех последующих скриптов
Прошу, не добавляйте сюда никакой логики поведения, иначе я обижусь
"""

import json
from dataclasses import dataclass
from enum import Enum
from typing import List


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

    def __mul__(self, other):
        if not isinstance(other, int):
            raise TypeError()
        return Vector(self.x * other,
                      self.y * other,
                      self.z * other)

    def __str__(self):
        return f'{self.x}/{self.y}/{self.z}'

    def __eq__(self, other):
        return self.coords == other.coords

    def __ne__(self, other):
        return self.coords != other.coords

    def __gt__(self, other):
        return self.coords > other.coords

    def __lt__(self, other):
        return self.coords < other.coords

    def __ge__(self, other):
        return self.coords >= other.coords

    def __le__(self, other):
        return self.coords <= other.coords

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
    def get_len_vector(vector_diff: Vector) -> int:
        """Метод для нахождения длины разности векторов"""

        return sum(value ** 2 for value in vector_diff.coords) ** 0.5

    @staticmethod
    def bresenham_ray(point1: Vector, point2: Vector, length: int = None) -> List[Vector]:
        """Метод для построение вектора по алгоритмы Брезенхама (https://clck.ru/Vbigh)"""

        x1, y1, z1 = point1.coords
        x2, y2, z2 = point2.coords

        points = [(x1, y1, z1)]
        x_shift = abs(x2 - x1)
        y_shift = abs(y2 - y1)
        z_shift = abs(z2 - z1)

        x_step = int(x2 > x1)
        y_step = int(y2 > y1)
        z_step = int(z2 > z1)

        # изменения поведения в зависимости от ведущей оси
        if x_shift >= y_shift and x_shift >= z_shift:
            # p1, p2 - смещение относительно ведущей оси, не стал изменять названия переменных
            p1 = 2 * y_shift - x_shift
            p2 = 2 * z_shift - x_shift
            while x1 != x2:
                x1 += x_step
                if p1 >= 0:
                    y1 += y_step
                    p1 -= 2 * x_shift
                if p2 >= 0:
                    z1 += z_step
                    p2 -= 2 * x_shift
                p1 += 2 * y_shift
                p2 += 2 * z_shift
                points.append(Vector(x1, y1, z1))
        elif y_shift >= x_shift and y_shift >= z_shift:
            p1 = 2 * x_shift - y_shift
            p2 = 2 * z_shift - y_shift
            while y1 != y2:
                y1 += y_step
                if p1 >= 0:
                    x1 += x_step
                    p1 -= 2 * y_shift
                if p2 >= 0:
                    z1 += z_step
                    p2 -= 2 * y_shift
                p1 += 2 * x_shift
                p2 += 2 * z_shift
                points.append(Vector(x1, y1, z1))
        else:
            p1 = 2 * y_shift - z_shift
            p2 = 2 * x_shift - z_shift
            while z1 != z2:
                z1 += z_step
                if p1 >= 0:
                    y1 += y_step
                    p1 -= 2 * z_shift
                if p2 >= 0:
                    x1 += x_step
                    p2 -= 2 * z_shift
                p1 += 2 * y_shift
                p2 += 2 * x_shift
                points.append(Vector(x1, y1, z1))

        return points[:length or 999]  # не самый лучший вариант, зато в коде места не занимает


# endregion


# region Equipment


class BlockType(Enum):
    Energy = 0
    Gun = 1
    Engine = 2
    Health = 3
    Shield = 4
    Radar = 6
    Heal = 7


class EffectType(Enum):
    Blaster = 0
    Railgun = 1


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
        elif BlockType(data['Type']) == BlockType.Shield:
            return ShieldBlock(**data)
        elif BlockType(data['Type']) == BlockType.Radar:
            return RadarBlock(**data)
        elif BlockType(data['Type']) == BlockType.Heal:
            return HealBlock(**data)


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


@dataclass
class ShieldBlock(Block):
    Type = BlockType.Shield
    EnergyPrice: int
    Armor: int


@dataclass
class RadarBlock(Block):
    EnergyPrice: int
    Radius: int


@dataclass
class HealBlock(Block):
    Type = BlockType.Heal
    EnergyPrice: int
    Radius: int
    HealthGain: int
    EnergyGain: int


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
        data['Equipment'] = Block.from_json(data['Equipment'])
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
    StartArea: MapRegion
    Equipment: List[DraftEquipment]
    CompleteShips: List[DraftCompleteShip]
    DraftTimeout: int = None
    BattleRoundTimeout: int = None

    @classmethod
    def from_json(cls, data):
        data['StartArea'] = MapRegion.from_json(data['StartArea'])
        data['Equipment'] = list(map(DraftEquipment.from_json, data['Equipment']))
        data['CompleteShips'] = list(map(DraftCompleteShip.from_json, data['CompleteShips']))
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
DEFEND = 'DEFEND'
SCAN = 'SCAN'


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
class DefendParameters(CommandParameters):
    Id: int
    Name: str


@dataclass
class ScanParameters(CommandParameters):
    Id: int
    Name: str


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
        self.draft_options = None

    def draft(self, data: dict) -> DraftChoice:
        self.draft_options = DraftOptions.from_json(data)
        draft_choice = DraftChoice()

        # тут должно быть поведение во время драфта

        return draft_choice

    def battle(self, data: dict) -> UserOutput:
        state = State.from_json(data)
        user_output = UserOutput()

        # тут должно быть поведение во время боя

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
