from PIL import Image as im
from dataclasses import dataclass
from os import path as pt
import io
import os
import wand.image as wimage
import quicktex.dds as qtx

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
        self.filepath = file_path
        if pt.splitext(self.filepath)[1].lower() == ".dds":
            try:
                dds_image = qtx.read(self.filepath)
                dds_image.format

                wand_image = wimage.Image(filename=self.filepath)
                self._compression = wand_image.compression
                self._colorspace = wand_image.colorspace
                self._compression_quality = wand_image.compression_quality
                self._img_options = wand_image.options
                img_blob = wand_image.make_blob("bmp")
                assert img_blob is not None
                self.texture = Texture(im.open(io.BytesIO(img_blob)))
                print(
                    f"Special DDS handled (loading) compression {self._compression} quality {self._compression_quality} colorspace {self._colorspace}"
                )
            except Exception as e:
                print(f"Failed to load special DDS: {e}")
                print("Defaulting to PIL loading")
                self._compression = "dxt5"
                self._colorspace = "srgb"
                self._compression_quality = 1.0
                self._img_options = {
                    "dds:compression": self._compression,
                    "dds:mipmaps": "8",
                    "dds:cluster-fit": "false",
                }
                self.texture = Texture(im.open(file_path))
        else:
            self.texture = Texture(im.open(file_path))

    def getIdentityData(self) -> tuple[Texture, ConversionData]:
        width, height = self.texture.image.size
        return self.texture, ConversionData(width, height, 1.0)

    def saveReplacement(self, texture: Texture, path: str):
        self.texture = texture

        if pt.splitext(self.filepath)[1].lower() == ".dds":
            temp = io.BytesIO()
            self.texture.image.save(temp, format="bmp")
            wand_image = wimage.Image(blob=temp.getvalue())
            wand_image.compression = self._compression
            # wand_image.compression_quality = self._compression_quality
            wand_image.colorspace = self._colorspace
            assert self._img_options is not None and wand_image.options is not None
            for opt, val in self._img_options.items():
                if opt.startswith("dds:"):
                    wand_image.options[opt] = val
            wand_image.save(filename=path)
            print("Special DDS handled (saving)")

        else:
            self.texture.image.save(self.filepath)

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
