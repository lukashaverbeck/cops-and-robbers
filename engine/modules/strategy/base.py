from abc import ABC, abstractmethod


class BaseCopsStrategy(ABC):
    @abstractmethod
    def init(self, finish_time: float) -> list[int]:
        raise NotImplementedError

    @abstractmethod
    def step(self, cop_positions: list[int], robber_position: int, finish_time: float) -> list[int]:
        raise NotImplementedError


class BaseRobberStrategy(ABC):
    @abstractmethod
    def init(self, cop_positions: list[int], finish_time: float) -> int:
        raise NotImplementedError

    @abstractmethod
    def step(self, cop_positions: list[int], robber_position: int, finish_time: float) -> int:
        raise NotImplementedError
