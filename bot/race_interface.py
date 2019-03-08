# interface for different macro bots
# (c) kaitai

import abc
from abc import abstractmethod

class Race_macro(abc.ABC):

    @abstractmethod
    def __init__(self, controller):
        raise NotImplementedError('Method __init__ not implemented')

    @abstractmethod
    def train_unit(self, goal, unit):
        raise NotImplementedError('Method train_unit not implemented')

    @abstractmethod
    def general_macro(self):
        raise NotImplementedError('Method general_macro not implemented')

    @abstractmethod
    def early_tech(self):
        raise NotImplementedError('Method early_tech not implemented')

    @abstractmethod
    def mid_tech(self):
        raise NotImplementedError('Method mid_tech not implemented')

    @abstractmethod
    def late_tech(self):
        raise NotImplementedError('Method late_tech not implemented')

    @abstractmethod
    def air_tech(self):
        raise NotImplementedError('Method air_tech not implemented')

