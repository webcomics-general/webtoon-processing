#!/usr/bin/env python3.10

"""Postprocessor for Webtoon Downloader.

Run this script with `-h` or `--help` to show usage:

```shell
# Run as a script
python3 webtoon_processing/webtoon_processing.py --help

# Run as a module
python3 -m webtoon_processing --help
```
"""

__author__ = "anon from /wcg/"
__date__ = "2023-10-15"
__version__ = "0.1"

import argparse
import logging
from pathlib import Path
from textwrap import dedent

import numpy as np
from PIL import Image


# Configure logging. Default log level is WARNING, use INFO or DEBUG
# for more information.
logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.INFO)


def parse_args():
    """Parse the command-line arguments of this program."""
    doc=dedent("""\
        Postprocess the image files downloaded by Webtoon Downloader.

        [Webtoon Downloader](https://github.com/Zehina/Webtoon-Downloader) is a
        command-line Python program for downloading the chapters of webcomics
        hosted on Webtoon.

        The chapters are stored on Webtoon as a series of images which are
        displayed together as a single, tall, scrollable image. Webtoon
        Downloader downloads those individual images. Panels and text bubbles
        are frequently split between two consecutive images.

        This Python program, Webtoon Processing, merges the individual images
        into a single, tall, scrollable image, and then splits that image into a
        series of smaller images with consideration for panels and text bubbles,
        by splitting in the whitespace (or darkspace) of the image.

        The images are merged in the order they are given on the command line.
        Since patterns such as 001_*.png expand to 001_0.png 001_10.png ...
        001_19.png 001_1.png 001_20.png ... 001_29.png 001_2.png..., consider
        sorting the input before passing it to the program. For instance, using
        the natural sort option of the "sort" command in GNU coreutils:

        %(prog)s [options] $(ls 001_*.png | sort --version-sort)"""
    )
    warning=dedent("""\
        Beware that this program is experimental. In particular, it is not well
        tested against wrong input arguments."""
    )
    parser = argparse.ArgumentParser(
        description=doc,
        epilog=warning,
        formatter_class=argparse.RawTextHelpFormatter,
        add_help=False
    )
    parser.add_argument(
        "-h", "--help", action="help", default=argparse.SUPPRESS,
        help="Show this help message and exit"
    )
    parser.add_argument(
        "-V", "--version", action="version",
        help="Show program's version number and exit",
        version="Postprocessor for Webtoon Downloader, "
                f"version {__version__}, {__date__}"
    )
    parser.add_argument(
        "--threshold", metavar="w", default=245, type=int,
        help="Whitespace (or darkspace) threshold\n"
             "Default: %(default)s\n"
             "* If w > 127, as in the default, cut in the whitespace, where\n"
             "  white is any pixel value above the threshold (inclusive).\n"
             "* If w <= 127, cut in the darkspace instead, where dark is\n"
             "  any pixel value below the threshold (inclusive)."
    )
    parser.add_argument(
        "--heights", nargs=3, metavar=("a", "b", "c"), default=[0, 1000, 800],
        type=int,
        help="Size hints\n"
             "Default: %(default)s\n"
             "How tall we want the resulting images to be:\n"
             "* The first value is the desired height of the first image.\n"
             "  It is honored exactly if it is positive (> 0), otherwise it\n"
             "  is ignored. This hint serves to make the first image a\n"
             "  cover page with a specific height.\n"
             "* The third value is the desired minimum height of the last\n"
             "  image.\n"
             "* The second value is the desired minimum height of the\n"
             "  images in-between the first one and the last one."
    )
    parser.add_argument(
        "--out", metavar="pattern", default="%i.png",
        help="Output filename pattern\n"
             "Default: %(default)s\n"
             "The name that the resulting images will be saved as. Must\n"
             "contain the placeholder %%i or %%d, which will be replaced by a\n"
             "number. For instance, the pattern out/001_%%i.png will yield\n"
             "the output files out/001_0.png, out/001_1.png, and so on. Any\n"
             "specified directory must exist. The default is the current\n"
             "directory."
    )
    parser.add_argument(
        "file", nargs="+", type=Path,
        help="Image file downloaded from Webtoon\n"
             "This is a chapter page as downloaded by Webtoon Downloader"
    )
    args = parser.parse_args()

    return args


def group_consecutive(data: np.array) -> list[np.array]:
    """Group consecutive elements in an array.

    Parameters
    ----------
    data : one-dimensional NumPy array
        The array's elements are strictly-increasing non-negative
        integers. For instance:
        ```
        >>> data = np.array([0, 1, 4, 5, 6, 8, 10, 11])
        ```

    Returns
    -------
    list of one-dimensional NumPy arrays
        The consecutive elements are grouped together. For instance:
        ```
        >>> print(consecutive(data))
        [array([0, 1]), array([4, 5, 6]), array([8]), array([10, 11])]
        ```
    """
    if data.ndim != 1:
        raise Exception("Input array must be one-dimensional.")

    return np.split(data, np.nonzero(np.diff(data) > 1)[0] + 1)


def merge(images: list[Image]) -> Image:
    """Merge images vertically.

    Parameters
    ----------
    images : list of PIL images
        Those are the pages of a Webtoon chapter, as downloaded by
        Webtoon Downloader.

    Returns
    -------
    PIL image
        The Webtoon chapter as a single image, made by stacking up the
        input images. It is an RGB image regardless of input.
    """
    width = max([image.width for image in images])
    height = sum([image.height for image in images])
    result = Image.new("RGB", (width, height))
    y = 0

    for image in images:
        logging.info(
            f"Merging image {image.filename} with height {image.height}"
        )
        result.paste(image, (0, y))
        y = y + image.height

    logging.info(f"Merged image has height {result.height}")

    return result


def find_whitespace(image: Image, threshold: int = 245) -> list[np.array]:
    """Find vertical whitespace (or darkspace) in an image.

    If threshold > 127, as in the default threshold = 245, find which
    rows in the image are white, where white is any pixel value above
    the threshold (inclusive).

    If threshold <= 127, find which rows in the image are dark, where
    dark is any pixel value below the threshold (inclusive).

    Parameters
    ----------
    image : PIL image
        A Webtoon chapter.
    threshold : integer between 0 (black) and 255 (white)
        All pixel values between this threshold and 0 (or 255) are
        considered white (or black).

    Returns
    -------
    list of one-dimensional Numpy arrays
        Each item in this list is an array of strictly-increasing
        consecutive elements corresponding to the indices of the image
        rows which are white (or dark). In other words, each array is a
        span of vertical whitespace (or darkspace) in the image.
    """
    grayscale = np.asarray(image.convert("L"))

    if threshold > 127:
        white = np.all(grayscale >= threshold, axis=1)  # booleans
        white = np.nonzero(white)[0]                    # indices
        logging.info(f"Found {len(white)} rows of whitespace")
        return group_consecutive(white)
    else:
        dark = np.all(grayscale <= threshold, axis=1)  # booleans
        dark = np.nonzero(dark)[0]                     # indices
        logging.info(f"Found {len(dark)} rows of darkspace")
        return group_consecutive(dark)


def find_optimal_cuts(
        image: Image,
        whitespace: list[np.array],
        hints: list[int] = [0, 1000, 800],
    ) -> list[int]:
    """Find where to cut in the vertical whitespace of an image.

    We cut in the middle of the whitespace, taking into account size
    hints to avoid splitting the image into chunks that are too small.

    In other words, we don't cut in the middle of every detected span of
    whitespace, but only where it leads to chunks that are large enough.

    Parameters
    ----------
    image : PIL image
        A Webtoon chapter.
    whitespace : list of one-dimensional NumPy arrays
        Each item in this list is an array of strictly-increasing
        consecutive elements corresponding to the indices of the image
        rows which are white. In other words, each array is a span of
        vertical whitespace in the image.
    hints : list of three positive integers, default [0, 1000, 800]
        How tall we want the resulting chunks to be:
        * The first value is the desired height of the first chunk. It
          is honored exactly if it is positive (> 0), otherwise it is
          ignored. This hint serves to make the first chunk a cover page
          with a specific height.
        * The third value is the desired minimum height of the last
          chunk.
        * The second value is the desired minimum height of the chunks
          in-between the first one and the last one.

    Returns
    -------
    list of non-negative integers
        The rows at which we should split the image. Includes the first
        row (0) and the last row (image height).
    """
    if len(hints) != 3:
        raise Exception(
            "Size hints must be a list of three positive integers."
        )

    # Cut image in the middle of the whitespace that is large enough...
    if len(whitespace[0]) == 0:
        # No whitespace whatsoever is present
        middles = []
    else:
        # At least one row of whitespace is present
        min_space_height = 40
        middles = [(space[0] + space[-1]) // 2
            for space in whitespace if space[-1] - space[0] > min_space_height]

    logging.debug(f"Candidate rows to split the image at: {middles}")

    # ...but only if the resulting chunks are large enough...
    cut_here = [0, hints[0]] if hints[0] > 0 else [0]
    for y in middles:
        if y - cut_here[-1] >= hints[1]:
            cut_here.append(y)

    # ...and don't forget to include the tail if it is not in already
    h = image.height
    if cut_here[-1] < h:
        if cut_here[-1] == 0 or h - cut_here[-1] >= hints[2]:
            cut_here.append(h)
        else:
            cut_here[-1] = h

    logging.info(f"Splitting image at rows: {cut_here}")

    return cut_here


def split(image: Image, cut_here: list[int]) -> list[Image]:
    """Split image at the indicated vertical positions.

    Parameters
    ----------
    image : PIL image
        A Webtoon chapter.
    cut_here : list of non-negative integers
        The rows at which we should split the image. Must include the
        first row (0) and the last row (image height).

    Returns
    -------
    list of PIL images
        The same Webtoon chapter, divided into pages at the indicated
        positions.
    """
    chunks = []
    x1, x2 = 0, image.width
    for i in range(len(cut_here) - 1):
        y1, y2 = cut_here[i], cut_here[i + 1]
        logging.debug(
            f"Extracting chunk ({x1}, {y1}) to ({x2}, {y2}) "
            f"with height {y2 - y1}"
        )
        chunk = image.crop((x1, y1, x2, y2))
        chunks.append(chunk)

    return chunks


def main():
    """Postprocessor for Webtoon Downloader."""
    # Parse command-line arguments
    args = parse_args()

    # Merge input images into one tall image
    images = [Image.open(f) for f in args.file]
    image = merge(images)

    # Find vertical whitespace in the image
    whitespace = find_whitespace(image, threshold=args.threshold)

    # Decide where to cut in the whitespace
    cut_here = find_optimal_cuts(image, whitespace, hints=args.heights)

    # Split the tall image
    images = split(image, cut_here)

    # Output the split images
    count = 0
    pattern = args.out
    for i, chunk in enumerate(images):
        outfile = Path(pattern % i)
        logging.info(f"Saving chunk of height {chunk.height} to file {outfile}")
        chunk.save(outfile)

        count = count + chunk.height
        logging.debug(f"Saved a total of {count} rows so far")

    logging.info(f"Saved a total of {count} rows in chunks")

    # Output the tall image
    pattern = pattern.replace("%i", "%s").replace("%d", "%s")
    outfile = Path(pattern % "all")
    image.save(outfile)


if __name__ == "__main__":
    main()
