from typing import Iterable, Iterator
from dataclasses import dataclass
import os
import sys

from .image import *
from .texture import *


def absolutePath(file_path):
    # Check if the path is already absolute
    if os.path.isabs(file_path):
        return file_path

    # Get the absolute path of the current working directory
    current_directory = os.getcwd()

    # Join the current directory with the provided file path
    absolute_path = os.path.abspath(os.path.join(current_directory, file_path))

    # Return the absolute path
    return absolute_path


def listSupportedImages(directory):
    supported_images = []
    for root, _, files in os.walk(directory):
        for filename in files:
            file_path = os.path.join(root, filename)
            if isSupportedImage(file_path):
                supported_images.append(file_path)
    return supported_images


def main():
    @dataclass
    class FileSpec:
        """
        For listing files we process
        """

        absolutePrefix: str
        filepath: str

    # list of files we process
    filenameList: list[FileSpec] = []

    # launch params

    # --file
    def opt_file(args: Iterator[str]):
        nonlocal filenameList

        f = next(args)
        assert os.path.isfile(f), f"'{f}' is not recognized as a file"

        filenameList.append(
            FileSpec(os.path.join(absolutePath(f), os.path.pardir), os.path.basename(f))
        )

    # --directory
    def opt_directory(args: Iterator[str]):
        nonlocal filenameList

        d = next(args)
        assert os.path.isdir(d), f"'{d}' is not recognized as a directory"

        filenameList.extend(
            [
                FileSpec(
                    absolutePath(d), os.path.relpath(absolutePath(f), absolutePath(d))
                )
                for f in listSupportedImages(d)
            ]
        )

    # --output
    outputPrefix = os.path.curdir

    def opt_output(args: Iterator[str]):
        nonlocal outputPrefix

        d = next(args)
        assert os.path.isdir(d), f"'{d}' is not recognized as a(n existing) directory"

        outputPrefix = d

    # --reduceto
    shouldReduce = False
    reduceBy = 0.0

    def opt_reduceby(args: Iterator[str]):
        nonlocal shouldReduce
        nonlocal reduceBy

        arg = next(args)
        factor = 1.0

        if arg.endswith("%"):
            factor = 0.01
            arg = arg[:-1]

        reduceBy = float(arg) * factor
        shouldReduce = True

        assert (
            reduceBy >= 0.0 and reduceBy < 1.0
        ), "reduceby must be between 0.0 (inclusive) and 1.0 (exclusive)"

    # --mindimension
    minDimension = 32

    def opt_mindimension(args: Iterator[str]):
        nonlocal minDimension

        minDimension = int(next(args))

        assert minDimension > 2, "minDimension must be greater than 2"

    # --verbose
    verbose = False

    def opt_verbose(args: Iterator[str]):
        nonlocal verbose

        verbose = True

    # Option list
    supportedOptions = {
        "--file": opt_file,
        "-f": opt_file,
        "--directory": opt_directory,
        "-d": opt_directory,
        "--output": opt_output,
        "-o": opt_output,
        "--reduceby": opt_reduceby,
        "-r": opt_reduceby,
        "--mindimension": opt_mindimension,
        "-m": opt_mindimension,
        "--verbose": opt_verbose,
    }

    # parse argvs and execute the related functions
    iter_args = iter(sys.argv)
    next(iter_args)  # skip the program name
    try:
        while True:
            opt = next(iter_args)

            # check if option is supported and process it
            if opt in supportedOptions:
                try:
                    supportedOptions[opt](iter_args)
                except StopIteration as e:
                    print(f"Not enough arguments for option {opt}", file=sys.stderr)
                except AssertionError as e:
                    print(f"Error handling option {opt}: {e.args[0]}", file=sys.stderr)
            else:
                print(f"Unrecognized option {opt}", file=sys.stderr)
                break
    except StopIteration:
        pass

    # list of files we process
    if verbose:
        print("Files to process:")
        for f in filenameList:
            print(f"'{f.filepath}' from '{f.absolutePrefix}'")

    #
    # Execute the code
    #

    # reduce if requested
    ogTotalPixels = 0
    newTotalPixels = 0
    newQualSum = 0.0
    newMinQual = 1.0
    modifiedImageCount = 0
    processedImageCount = 0
    if shouldReduce:
        if len(filenameList):
            for f in filenameList:
                processedImageCount += 1

                try:
                    # load the file and prepare for output
                    inpath = os.path.join(f.absolutePrefix, f.filepath)
                    outpath = os.path.join(outputPrefix, f.filepath)

                    try:
                        handler = ImageHandler(inpath)
                    except Exception as e:
                        print(f"Error loading {inpath}: {e}", file=sys.stderr)
                        continue

                    # stats
                    ogW, ogH = handler.texture.image.size
                    ogTotalPixels += ogW * ogH

                    if verbose:
                        print(
                            f"Handling image {processedImageCount}/{len(filenameList)} {inpath} ({ogW}x{ogH})"
                        )

                    # reduction!
                    newtex, conversionData = handler.reduce(
                        minDimension, minDimension, 1.0 - reduceBy
                    )

                    # stats
                    newW, newH = newtex.image.size
                    newQual = conversionData.quality
                    newTotalPixels += newW * newH
                    newQualSum += newQual
                    if newQual < newMinQual:
                        newMinQual = newQual

                    # check if we managed to reduce
                    if newtex is handler.texture:
                        if verbose:
                            print(f"    Can't reduce, skipping.")
                    else:
                        if verbose:
                            print(
                                f"    Reduced from {ogW}x{ogH} to {newW}x{newH} while keeping {newQual*100.0:.2f}% quality"
                            )
                        modifiedImageCount += 1

                        # create the directory structure if it doesn't exist
                        os.makedirs(os.path.dirname(outpath), exist_ok=True)
                        newtex.image.save(outpath)
                except Exception as e:
                    print(
                        f"Error processing {f.filepath}: {e}",
                        file=sys.stderr,
                    )
                    continue

            # stats
            newAvgQual = newQualSum / len(filenameList)
            print(
                f"Total memory reduced by {(1.0 - newTotalPixels/ogTotalPixels)*100.0:.2f}%"
            )
            print(f"Modified {modifiedImageCount} image files")
            print(f"On average keeping {newAvgQual*100.0:.2f}% quality")
            print(f"Minimum accepted quality was {newMinQual*100.0:.2f}%")
            print(
                f"Our win ratio is {newAvgQual/(newTotalPixels/ogTotalPixels):.2f}/1.0!"
            )
            print("")
            print("Enjoy your crisp potato graphics!")
        else:
            print("No files supplied!")


if __name__ == "__main__":
    main()
