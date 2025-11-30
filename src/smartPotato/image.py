from PIL import Image as im
from dataclasses import dataclass
from os import path as pt
import io
import os
import wand.image as wimage
import quicktex.dds as qtx
import subprocess
import tempfile

from .texture import *

# Create a temp directory
tempdir = tempfile.TemporaryDirectory(suffix=None, prefix=None, dir=None)
tempImageFilepath = pt.join(tempdir.name, "image.png")
with open(tempImageFilepath, "w") as fp:
    pass

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


@dataclass
class NVTT:
    nvttDir: str
    nvdecompressPath: str
    nvcompressPath: str
    nvddsinfoPath: str


class ImageHandler:

    def __init__(self, file_path, nvttDirInfo: NVTT):
        self.filepath = file_path
        self.nvttDirInfo = nvttDirInfo
        if pt.splitext(self.filepath)[1].lower() == ".dds":
            assert (
                nvttDirInfo is not None
            ), "Please provide an NVidia Texture Tools directory for DDS handling. Skipping!"

            p = subprocess.Popen(
                [nvttDirInfo.nvddsinfoPath, self.filepath],
                stdout=subprocess.PIPE,
            )
            pout, _ = p.communicate()
            infostr = pout.decode("utf-8")
            if "'DXT1'" in infostr:
                self.compressionOpt = "-bc1"
            elif "'DXT1nm'" in infostr:
                self.compressionOpt = "-bc1n"
            elif "'DXT1a'" in infostr:
                self.compressionOpt = "-bc1a"
            elif "'DXT3'" in infostr:
                self.compressionOpt = "-bc2"
            elif "'DXT5'" in infostr:
                self.compressionOpt = "-bc3"
            elif "'DXT5nm'" in infostr:
                self.compressionOpt = "-bc3n"
            elif "'ATI1'" in infostr:
                self.compressionOpt = "-bc4"
            elif "'ATI2'" in infostr:
                self.compressionOpt = "-ati2"
            elif "'DX10'" in infostr:
                self.compressionOpt = "-bc7"
            else:
                print(f"Unknown compression format from nvddsinfo dump: '{infostr}'")
                self.compressionOpt = "-bc3"

            # decompress to a temporary file in tmp folder

            subprocess.call(
                [
                    nvttDirInfo.nvdecompressPath,
                    "-format",
                    "png",
                    self.filepath,
                    tempImageFilepath,
                ]
            )
            self.texture = Texture(im.open(tempImageFilepath))
            os.remove(tempImageFilepath)
        else:
            self.texture = Texture(im.open(file_path))

    def getIdentityData(self) -> tuple[Texture, ConversionData]:
        width, height = self.texture.image.size
        return self.texture, ConversionData(width, height, 1.0)

    def saveReplacement(self, texture: Texture, path: str):
        self.texture = texture

        if pt.splitext(self.filepath)[1].lower() == ".dds":
            self.texture.image.save(tempImageFilepath)
            subprocess.call(
                [
                    self.nvttDirInfo.nvcompressPath,
                    self.compressionOpt,
                    "-production",
                    tempImageFilepath,
                    path,
                ]
            )
            os.remove(tempImageFilepath)

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
