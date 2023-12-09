from curses import nonl
from image import *
from texture import *

from collections import defaultdict

"""
Execute this to research on qualities of different methods 
"""


def researchAll():
    textures = [
        "./experimenting/lawn.png",
        "./experimenting/leaf.png",
        "./experimenting/rock.png",
        "./experimenting/plant.png",
        "./experimenting/carpet.png",
        "./experimenting/bricks.png",
        "./experimenting/oldwall.png",
        "./experimenting/technorock.png",
        "./experimenting/ground.png",
    ]

    limit = 0.7

    methodQualRatioSums: defaultdict[str, float] = defaultdict(lambda: 0.0)
    methodUsages: defaultdict[str, int] = defaultdict(lambda: 0)

    for texname in textures:
        pathdir = os.path.dirname(texname)
        pathfile = os.path.splitext(os.path.basename(texname))[0]
        pathext = os.path.splitext(os.path.basename(texname))[1]

        tex = Texture(im.open(texname))
        print(f"Loaded '{texname}'")
        width, height = tex.image.size

        og_tex = tex
        og_width, og_height = width, height

        outputs: list[tuple[Texture, float, str]] = []
        outputs.append((tex, 1.0, "Original"))

        while width > 2 and height > 2:
            prev_tex = tex

            naive = og_tex.transformResolution(width // 2, height // 2)

            og_sharp = og_tex.transformSharpen(
                math.floor(math.log2(og_width / width))
            ).transformResolution(width // 2, height // 2)
            og_detail = og_tex.transformIncreaseDetail(
                math.floor(math.log2(og_width / width))
            ).transformResolution(width // 2, height // 2)
            og_both = (
                og_tex.transformSharpen(math.floor(math.log2(og_width / width)))
                .transformIncreaseDetail(math.floor(math.log2(og_width / width)))
                .transformResolution(width // 2, height // 2)
            )
            og_comb = og_sharp.transformFadedTo(og_detail, 0.5)

            prev_sharp = prev_tex.transformSharpen(1).transformResolution(
                width // 2, height // 2
            )
            prev_detail = prev_tex.transformIncreaseDetail(1).transformResolution(
                width // 2, height // 2
            )
            prev_both = (
                prev_tex.transformSharpen(1)
                .transformIncreaseDetail(1)
                .transformResolution(width // 2, height // 2)
            )
            prev_comb = prev_sharp.transformFadedTo(prev_detail, 0.5)

            tex = tex.transformResolution(width // 2, height // 2)
            width, height = tex.image.size
            cur_sharp = tex.transformSharpen(1)
            cur_detail = tex.transformIncreaseDetail(1)
            cur_both = cur_sharp.transformIncreaseDetail(1)
            cur_comb = cur_sharp.transformFadedTo(cur_detail, 0.5)

            alphaSteps = [0.25, 0.5, 0.75]
            contenders: list[tuple[Texture, str]] = [
                (tex, "cur"),
                (naive, "naive"),
                (og_sharp, "ogsharp"),
                (og_detail, "ogdetail"),
                (og_both, "ogboth"),
                (og_comb, "ogcomb"),
                (prev_sharp, "prevsharp"),
                (prev_detail, "prevdetail"),
                (prev_both, "prevboth"),
                (prev_comb, "prevcomb"),
                (cur_sharp, "cursharp"),
                (cur_detail, "curdetail"),
                (cur_both, "curboth"),
                (cur_comb, "curcomb"),
            ]

            maxQual = 0.0
            maxQualMethodName = ""
            maxQualTex: Texture = tex
            methodQuals: dict[str, float] = {}

            savedSpecial1: Texture = tex
            savedBest: Texture = tex

            def tryQuality(t: Texture, name: str):
                nonlocal maxQual
                nonlocal maxQualMethodName
                nonlocal maxQualTex
                nonlocal methodQuals
                nonlocal savedSpecial1
                nonlocal savedBest

                print(f"used {name}, testing")
                qual = t.transformResolution(og_width, og_height).similarityTo(og_tex)
                methodQuals[name] = qual
                if qual > maxQual:
                    maxQual = qual
                    maxQualMethodName = name
                    maxQualTex = t
                print(f"  {qual*100.0:3.2f}%")

                if name == "special1-100":
                    savedSpecial1 = t
                if name == "cur-curboth-50":
                    savedBest = t

            # iterate over all contenders
            for i in range(len(contenders)):
                t, name = contenders[i]
                tryQuality(t, name)

            # iterate over all unique pairs in contenders
            for i in range(len(contenders) - 1):
                for j in range(i + 1, len(contenders)):
                    t1, name1 = contenders[i]
                    t2, name2 = contenders[j]
                    for a in alphaSteps:
                        t = t1.transformFadedTo(t2, a)
                        name = f"{name1}-{name2}-{int(a*100)}"
                        tryQuality(t, name)

            # special method
            prev_sharp_later_detail = prev_sharp.transformIncreaseDetail(1)
            for a in [0.0, 0.1, 0.25, 0.5, 0.75, 0.9, 1.0]:
                t = prev_sharp.transformFadedTo(prev_sharp_later_detail, a)
                name = f"special1-{int(a*100)}"
                tryQuality(t, name)
            # special method
            cur_later_detail = tex.transformIncreaseDetail(1)
            for a in [0.0, 0.1, 0.25, 0.5, 0.75, 0.9, 1.0]:
                t = tex.transformFadedTo(cur_later_detail, a)
                name = f"special2-{int(a*100)}"
                tryQuality(t, name)

            if maxQual >= limit:
                for name, qual in methodQuals.items():
                    methodQualRatioSums[name] += qual / maxQual
                    methodUsages[name] += 1

            tex = maxQualTex

            # save textures
            def saveTex(t: Texture, name: str):
                scal = t.transformResolution(og_width, og_height)
                scal.image.save(
                    f"{pathdir}/cvt/{pathfile}_{width}x{height}_{name}_{int(scal.similarityTo(og_tex)*100)}{pathext}"
                )

            saveTex(maxQualTex, maxQualMethodName)
            saveTex(naive, "naive")
            saveTex(savedSpecial1, "special1-100")
            saveTex(savedBest, "cur-curboth-50")

            outputs.append((maxQualTex, maxQual, maxQualMethodName))

        print(f"Results for {texname}:")
        for tex, q, name in outputs:
            w, h = tex.image.size
            print(
                f"  \u25cf {w:04}x{h:04} (-{(og_width*og_height-w*h)/(og_width*og_height)*100.0:5.2f}%) ~ {q*100.0:5.2f}% by {name}"
            )

    # shows relative qualities of all methods used, max first
    print(f"Quality of methods used:")
    methodQualRatios = {
        name: methodQualRatioSums[name] / methodUsages[name]
        for name in methodQualRatioSums.keys()
    }
    for name, ratio in sorted(methodQualRatios.items(), key=lambda item: item[1]):
        print(f"  \u25cf {name}: {ratio*100.0:6.3f}%")


if __name__ == "__main__":
    researchAll()
