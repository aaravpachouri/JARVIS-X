from pathlib import Path

from PIL import Image

import cv2
import numpy as np


class VisionService:

    def __init__(self):

        pass

    ##################################################

    def loadImage(

        self,

        image_path

    ):

        image = Image.open(

            image_path

        )

        return np.array(

            image

        )

    ##################################################

    def loadOpenCV(

        self,

        image_path

    ):

        return cv2.imread(

            str(

                Path(image_path)

            )

        )

    ##################################################

    def width(

        self,

        image

    ):

        return image.shape[1]

    ##################################################

    def height(

        self,

        image

    ):

        return image.shape[0]

    ##################################################

    def center(

        self,

        image

    ):

        return (

            self.width(image) // 2,

            self.height(image) // 2

        )

    ##################################################

    def size(

        self,

        image

    ):

        return (

            self.width(image),

            self.height(image)

        )