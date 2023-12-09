from PIL import Image as im, ImageEnhance, ImageFilter
from imgbeddings import imgbeddings
import math
import numpy as np

from calc import *

# globals for embedding generation
ibed = imgbeddings()


class Texture:
    """
    Wrapper for texture-like Images that can be compared to other images
    by retrieving their embeddings.
    Takes into account the image as-is, and the image shifter by half and wrapped
    """

    def __init__(self, image: im.Image):
        self.image = image
        self._embedding: np.ndarray | None = None

    def getEmbedding(self) -> np.ndarray:
        """
        Retrieve the embedding for the image.

        Returns:
            np.ndarray: The embedding for the image.
        """
        if self._embedding is None:
            self._embedding = np.asarray(ibed.to_embeddings(self.image)).flatten()
        return self._embedding

    def similarityTo(self, other: "Texture") -> float:
        """
        Calculate the similarity between this texture and another texture.

        Parameters:
            other (Texture): The other texture to compare to.

        Returns:
            float: The similarity score between the two textures.
        """

        def rescale(a):
            return 1.0 - math.sin(math.acos(a))

        return rescale(
            vecDiff(
                self.getEmbedding(),
                other.getEmbedding(),
            )
        )

    def transformResolution(self, width: int, height: int) -> "Texture":
        """
        Returns a copy of this texture with the specified resolution.
        Scaled using bilinear interpolation.
        If transformation is identity, returns itself.
        """
        if width == self.image.width and height == self.image.height:
            return self
        else:
            return Texture(self.image.resize((width, height), resample=im.BILINEAR))

    def transformSharpen(self, repeat: int) -> "Texture":
        """
        Returns a copy of this texture but sharpened repeat times.
        If transformation is identity, returns itself.
        """
        if repeat == 0:
            return self
        else:
            img = self.image
            for i in range(0, repeat):
                img = img.filter(ImageFilter.SHARPEN)

            return Texture(img)

    def transformIncreaseDetail(self, repeat: int) -> "Texture":
        """
        Returns a copy of this texture but sharpened repeat times.
        If transformation is identity, returns itself.
        """
        if repeat == 0:
            return self
        else:
            img = self.image
            for i in range(0, repeat):
                img = img.filter(ImageFilter.DETAIL)

            return Texture(img)

    def transformFadedTo(self, other: "Texture", alpha: float) -> "Texture":
        """
        Returns a copy of this texture but blended with the other.
        If transformation is identity, returns itself or the other.
        """

        if alpha == 0:
            return self
        elif alpha == 1:
            return other
        else:
            return Texture(im.blend(self.image, other.image, alpha))
