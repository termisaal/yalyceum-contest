"""
Корабли выстраиваются по окружности и на протяжении всего боя стараются держать строй
В итоге вышла какая-то хрень
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

    def __mul__(self, k: int):
        if not isinstance(k, int):
            raise TypeError()
        return Vector(self.x * k,
                      self.y * k,
                      self.z * k)

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

    @staticmethod
    def circle_points(center: Vector, amount: int, angle: int, player_id: int):
        """Метод для нахождения координат построения"""
        circle_shifts = [Vector(-1, 2, 3), Vector(-1, 3, 2), Vector(-1, 4, 1), Vector(0, 4, 0), Vector(1, 4, -1),
                         Vector(2, 3, -1), Vector(3, 2, -1), Vector(4, 1, -1), Vector(4, 0, 0), Vector(4, -1, 1),
                         Vector(3, -1, 2), Vector(2, -1, 3), Vector(1, -1, 4), Vector(0, 0, 4), Vector(-1, 1, 4)]

        k = len(circle_shifts)

        for i in range(angle, k + angle, k // amount):
            yield center + circle_shifts[i % k] * player_id


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

    # FireInfos: List[FireInfo]

    @classmethod
    def from_json(cls, data):
        data['My'] = list(map(Ship.from_json, data['My']))
        data['Opponent'] = list(map(Ship.from_json, data['Opponent']))
        # data['FireInfos'] = list(map(FireInfo.from_json, data['FireInfos']))
        data.pop('FireInfos')
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
        self.setup = 7
        self.angle = 1

    def draft(self, data: dict) -> DraftChoice:
        self.draft_options = DraftOptions.from_json(data)

        self.draft_options.PlayerId = -(self.draft_options.PlayerId or -1)  # 1 низ, -1 вверх

        draft_choice = DraftChoice(
            [DraftShipChoice(CompleteShipId='forward')] * 4 + [DraftShipChoice(CompleteShipId='daedalus')])
        return draft_choice

    def attack(self, ship: Ship, closest_enemy: Ship, user_commands: List[Command]) -> Command or None:
        guns = [x for x in ship.Equipment if isinstance(x, GunBlock)]
        for gun in guns:
            if gun.Radius * 3 >= Physics.get_len_vector(ship.Position - closest_enemy.Position):
                user_commands.append(Command(Command=ATTACK,
                                             Parameters=AttackParameters(Id=ship.Id,
                                                                         Name=gun.Name,
                                                                         Target=closest_enemy.Position)))

    def heal(self, ship: Ship, closest_friend: Ship, user_commands: List[Command]) -> None:
        pass

    def battle(self, data: dict) -> UserOutput:
        state = State.from_json(data)
        user_output = UserOutput()
        user_output.UserCommands = []

        if self.setup == 7:
            for ship in state.My:
                user_output.UserCommands.append(Command(Command=MOVE,
                                                        Parameters=MoveParameters(Id=ship.Id,
                                                                                  Target=ship.Position +
                                                                                         Vector(3, 3, 3) *
                                                                                         self.draft_options.PlayerId)))

                closest_enemy = min(state.Opponent,
                                    key=lambda x: Physics.get_len_vector(ship.Position - x.Position))
                if not any([block.Name == 'big_heal' for block in ship.Equipment]):

                    self.attack(ship, closest_enemy, user_output.UserCommands)
                else:
                    closest_friend = list(filter(lambda x: x.Health < 80, state.My))
                    if closest_friend:
                        closest_friend = min(closest_friend, key=lambda x: x.Health)
                        self.heal(ship, closest_friend, user_output.UserCommands)
                    self.attack(ship, closest_enemy, user_output.UserCommands)

            self.setup -= 1
        elif self.setup > 0:
            center = Vector(3, 3, 3) if self.draft_options.PlayerId > 0 else Vector(26, 26, 26)

            for ship, ship_coord in zip(state.My, Physics.circle_points(center,
                                                                        len(state.My), 0,
                                                                        self.draft_options.PlayerId)):
                user_output.UserCommands.append(Command(Command=MOVE,
                                                        Parameters=MoveParameters(Id=ship.Id,
                                                                                  Target=ship_coord)))
                closest_enemy = min(state.Opponent,
                                    key=lambda x: Physics.get_len_vector(ship.Position - x.Position))
                if not any([block.Name == 'big_heal' for block in ship.Equipment]):

                    self.attack(ship, closest_enemy, user_output.UserCommands)
                else:
                    closest_friend = min(state.My, key=lambda x: x.Health and Physics.get_len_vector(
                        ship.Position - x.Position) <= [block for block in ship.Equipment if block.Name == 'big_heal'][
                                                                     0].Radius)
                    self.heal(ship, closest_friend, user_output.UserCommands)
                    self.attack(ship, closest_enemy, user_output.UserCommands)
            self.setup -= 1
        else:
            center = Vector(15, 15, 15)

            for ship, ship_coord in zip(state.My, Physics.circle_points(center,
                                                                        len(state.My), self.angle,
                                                                        self.draft_options.PlayerId)):
                user_output.UserCommands.append(Command(Command=MOVE,
                                                        Parameters=MoveParameters(Id=ship.Id,
                                                                                  Target=ship_coord)))
                closest_enemy = min(state.Opponent,
                                    key=lambda x: Physics.get_len_vector(ship.Position - x.Position))
                if not any([block.Name == 'big_heal' for block in ship.Equipment]):

                    self.attack(ship, closest_enemy, user_output.UserCommands)
                else:
                    closest_friend = min(state.My, key=lambda x: x.Health and Physics.get_len_vector(
                        ship.Position - x.Position) <= [block for block in ship.Equipment if block.Name == 'big_heal'][
                                                                     0].Radius)
                    self.heal(ship, closest_friend, user_output.UserCommands)
                    self.attack(ship, closest_enemy, user_output.UserCommands)
            self.angle += 1

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
