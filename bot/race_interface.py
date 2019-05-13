# interface for different macro bots
# (c) kaitai

import abc
from abc import abstractmethod


class RaceMacro(abc.ABC):

    def __init__(self, controller):
        super().__init__()
        self.controller = controller

    @abstractmethod
    def train_unit(self, building_typeID, unit_typeID):
        """Trains given units on given buildings."""
        raise NotImplementedError('Method train_unit not implemented')

    @abstractmethod
    def general_macro(self):
        """Takes care of general macro for the bot."""
        raise NotImplementedError('Method general_macro not implemented')

    @abstractmethod
    def early_tech(self):
        """Sets early game tech goals."""
        raise NotImplementedError('Method early_tech not implemented')

    @abstractmethod
    def mid_tech(self):
        """Sets middle game tech goals."""
        raise NotImplementedError('Method mid_tech not implemented')

    @abstractmethod
    def late_tech(self):
        """Sets late game tech goals."""
        raise NotImplementedError('Method late_tech not implemented')

    @abstractmethod
    def air_tech(self):
        """Sets air tech goals."""
        raise NotImplementedError('Method air_tech not implemented')

