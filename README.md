# SmartPotato

Make your potato GPU render nice graphics using smart resolution reduction.

## Inspiration

There are many mods for popular games that reduce their quality
to make them run well on old hardware.
The useful ones often reduce resolution of all textures so they use less VRAM.
Reducing the resolution however destroys the visuals, as that nice brick wall
doesn't even look like bricks when it gets blurry.

But the old PS1/PS2 games had even lower res textures, and they didn't look bad!
Why is that? Probably because they were artistically built for the low resolutions.
PS1 games had even lower res textures thatn what these mods give,
but a brick wall still looked like a brick wall.

Can we do this for newer games?

This tool tries to do exactly that!
It not only reduces resolution, but applies a serias of smartly chosen filters
that try to preserve the 'vibe' of the texture.
A grass texture might need the edges of grass blades sharpened,
a ground texture might need contrast increased.
SmartPotato tries all that and decides what the best filters are, for each texture.

## How it works?

It relies on neural networks, but **not** generative AI.
The produced textures are derived **only** from the original textures,
and simple algorithmic filters.

*No slop is allowed.*
In fact, the NN is used to remove edits that make textures look sloppy.

Let's get technical: 
The NN is used to transform each image into an embedding space,
and then compare them using embedding parameters to decide what transformed textures
have the most similar 'vibe' to the originals.
The more they deviate from the originals, the lower the quality is, which is a simple scalar number.
*You* decide what the bottom line of acceptable quality is.
SmartPotato reduces the resolution until the produced quality
would be lower than is desired.

## How to use

SmartPotato is a command line tool (so run the Python file in a terminal)
that provides several options for automating the conversion of massive texture sets.
- `--file <filename>` or `-f <filename>`: Process this single texture
- `--directory <path>` or `-d <path>`: Process all images in this folder, while keeping the folder structure
- `--output <path>` or `-o <path>`: The folder where the results will be saved
- `--reduceby <quality>` or `-r <quality>`: How much quality can be taken. Can be a number between 0.0 and 1.0, or a percentage (< 100%). This is a subjective value, but it's good to keep it around 10-15%.
- `--mindimension <size>` or `-m <size>`: The minimal width or height of produced textures. Images won't be reduced past this size, no matter the quality
- `--verbose`: Print more info to the terminal
- `--nvtt`: Directory containing the NVidia texture tools (needed for DDS textures)

Example output:
```
...
Handling image 5/10 ./experimenting/in/GHZ/rock.png (512x512)
    Reduced from 512x512 to 256x256 while keeping 89.66% quality
    Saving to `./experimenting/out/GHZ/rock.png`
...
Handling image 9/10 ./experimenting/in/carpet.PNG (128x128)
    Can't reduce, skipping.
Handling image 10/10 ./experimenting/in/GHZ/ground.png (1024x1024)
    Reduced from 1024x1024 to 256x256 while keeping 90.91% quality
    Saving to `./experimenting/out/GHZ/ground.png`
Total memory reduced by 84.06%
Modified 7 image files
On average keeping 93.22% quality
Minimum accepted quality was 88.54%
Our win ratio is 5.85/1.0!

Enjoy your crisp potato graphics!
```

## Supported texture formats

Formats accepted by `pillow` library:
`.sgi`, `.xpm`, `.apng`, `.ps`, `.grib`, `.j2k`, `.iim`, `.mpo`, `.vda`, `.ftu`, `.dib`, `.ico`, `.h5`, `.pfm`, `.pbm`, `.jfif`, `.jpf`, `.tiff`, `.dds`, `.im`, `.ras`, `.gbr`, `.fli`, `.avifs`, `.bufr`, `.jpx`, `.msp`, `.wmf`, `.jpe`, `.hdf`, `.pdf`, `.tga`, `.jp2`, `.gif`, `.jpc`, `.blp`, `.jpeg`, `.j2c`, `.bmp`, `.pcd`, `.rgba`, `.dcx`, `.psd`, `.fit`, `.ppm`, `.cur`, `.avif`, `.png`, `.pnm`, `.xbm`, `.eps`, `.webp`, `.tif`, `.mpeg`, `.palm`, `.emf`, `.fits`, `.rgb`, `.bw`, `.icb`, `.pcx`, `.ftc`, `.qoi`, `.pxr`, `.mpg`, `.flc`, `.jpg`, `.pgm`, `.vst`, `.icns`

`DDS` images (WIP/experimental):
- Need NVidia's texture tools. Get them from https://developer.nvidia.com/gpu-accelerated-texture-compression 
- Pass the option `--nvtt 'path of downloaded texture tools'`
- Hope it handles textures well

## Dependencies
There are 3 main dependencies for smartPotato:
- `pillow`
- `wand`
- `imgbeddings`

You can use `pip` to install python dependencies, or your system's package manager. Good luck!
```sh
pip install -r smartPotato/src/requirements.txt
```

Note that `imgbeddings` seems to have some incompatibilities with the huggingface modules. The `requirements.txt` file included with smartPotato specifies versions of packages that work as of time of writing this.

The best method is to make a virtual python environment:
```sh
python3 -m venv 'Your environment path'
```

And then install the deps there:
```sh
'Your environment path'/bin/pip3 install -r ./smartPotato/src/requirements.txt
```