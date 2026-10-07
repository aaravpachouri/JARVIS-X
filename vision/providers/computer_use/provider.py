from abc import ABC, abstractmethod


class ComputerUseProvider(ABC):

    @abstractmethod
    def initialize(self):
        pass

    @abstractmethod
    def predict(

        self,

        image,

        instruction

    ):
        pass