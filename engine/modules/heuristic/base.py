from abc import ABC, abstractmethod
from typing import Generic

from networkx import Graph

from .util import CopPositions, RobberPosition, VertexT


class _BaseHeuristic(ABC, Generic[VertexT]):
    graph: Graph

    def __init__(self, graph: Graph, n_cops: int):
        # assert n_cops >= 1, f"Game can't be played with less than one cops, but number of cops was {n_cops}."
        self.graph = graph.copy()
        self.n_cops = n_cops

    @abstractmethod
    def compute_move(self, *args, **kwargs):
        raise NotImplementedError


class CopsInitializationHeuristic(_BaseHeuristic, ABC):
    @abstractmethod
    def compute_move(self) -> CopPositions:
        raise NotImplementedError


class CopsHeuristic(_BaseHeuristic, ABC):
    @abstractmethod
    def compute_move(self, cop_positions: CopPositions, robber_position: RobberPosition) -> CopPositions:
        raise NotImplementedError


class RobberInitializationHeuristic(_BaseHeuristic, ABC):
    @abstractmethod
    def compute_move(self, cop_positions: CopPositions) -> RobberPosition:
        pass


class RobberHeuristic(_BaseHeuristic, ABC):
    @abstractmethod
    def compute_move(self, cop_positions: CopPositions, robber_position: RobberPosition) -> RobberPosition:
        raise NotImplementedError
