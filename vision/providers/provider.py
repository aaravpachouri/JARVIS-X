from abc import ABC, abstractmethod


class VisionProvider(ABC):

    ##################################################

    @abstractmethod
    def analyze(

        self,

        image_path

    ):

        """
        Returns a unified scene dictionary.

        Every AI vision backend must implement this.
        """

        pass