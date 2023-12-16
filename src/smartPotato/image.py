from PIL import Image as im
from dataclasses import dataclass
import os

from .texture import *

# Get a set of supported file extensions
supported_extensions = {
    extension.lower() for extension, _ in im.registered_extensions().items()
}


def isSupportedImage(file_path):
    # Check if the file has a supported extension
    _, file_extension = os.path.splitext(file_path)
    return file_extension.lower() in supported_extensions


@dataclass
class ConversionData:
    width: int
    height: int
    quality: float


class ImageHandler:
    def __init__(self, file_path):
        self.texture = Texture(im.open(file_path))

    def getIdentityData(self) -> tuple[Texture, ConversionData]:
        width, height = self.texture.image.size
        return self.texture, ConversionData(width, height, 1.0)

    def reduce(
        self, minwidth: int, minheight: int, minquality: float
    ) -> tuple[Texture, ConversionData]:
        # We will use a special method consisting of sharpening the image,
        # reducing its resolution and then increasing its detail by a variable amount.

        ogTex = self.texture
        curTex = ogTex
        curQual = 1.0
        newTex = curTex
        newQual = curQual

        while (
            newQual > minquality
            and newTex.image.width > minwidth
            and newTex.image.height > minheight
        ):
            # accept the new texture
            curTex = newTex
            curQual = newQual

            # reduce resolution without increasing detail
            nonDetTex = curTex.transformSharpen(1).transformResolution(
                curTex.image.width // 2, curTex.image.height // 2
            )

            # now increase detail, and find the best amount by blending with nonDetTex
            detTex = nonDetTex.transformIncreaseDetail(1)
            blendSteps = [0.1, 0.25, 0.5, 0.75, 0.9, 1.0]

            bestTex = nonDetTex
            bestQual = nonDetTex.transformResolution(
                ogTex.image.width, ogTex.image.height
            ).similarityTo(ogTex)

            for a in blendSteps:
                t = nonDetTex.transformFadedTo(detTex, a)
                qual = t.transformResolution(
                    ogTex.image.width, ogTex.image.height
                ).similarityTo(ogTex)
                if qual > bestQual:
                    bestTex = t
                    bestQual = qual

            # select the best quality of our options, but don't accept it yet
            newTex = bestTex
            newQual = bestQual

        return curTex, ConversionData(curTex.image.width, curTex.image.height, curQual)
