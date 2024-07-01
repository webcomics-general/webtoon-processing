<!-- -*- coding: utf-8-unix -*- -->

# Postprocessor for Webtoon Downloader

[Webtoon Downloader](https://github.com/Zehina/Webtoon-Downloader) is a command-line Python program for downloading the chapters of webcomics hosted on Webtoon.

The chapters are stored on Webtoon as a series of images which are displayed together as a single, tall, scrollable image. Webtoon Downloader downloads those individual images. Panels and text bubbles are frequently split between two consecutive images.

This Python program, Webtoon Processing, merges the individual images into a single, tall, scrollable image, and then splits that image into a series of smaller images with consideration for panels and text bubbles, by splitting in the whitespace (or darkspace) of the image.

## Dependencies

This program was developed and tested using Python 3.10, NumPy 1.26, and Pillow 10.0. It is likely to work with other versions, but is known to require at least Python 3.9 (though it could easily be adapted to work with older releases).

To install the dependencies, run something like:

```shell
python3 -m pip install --upgrade pip wheel
python3 -m pip install numpy Pillow
```

The name of your Python interpreter is `py`, `python`, and/or `python3` depending on your operating system, how you installed Python, and whether or not you are running Python in a virtual environment.

## Usage

If you installed the dependencies in a virtual environment, activate that environment. Then navigate to the directory containing the package `webtoon_processing` and run that package on image files downloaded from Webtoon, for instance:

```shell
# Run as a script
python3 webtoon_processing/webtoon_processing.py [options] $(ls /path/to/images/001_*.png | sort --version-sort)

# Run as a module
python3 -m webtoon_processing [options] $(ls /path/to/images/001_*.png | sort --version-sort)
```

Run with `-h` or `--help` to show usage:

```shell
# As a script
python3 webtoon_processing/webtoon_processing.py --help

# As a module
python3 -m webtoon_processing --help
```

To uninstall, delete the directory containing the package `webtoon_processing`, and optionally delete the directory containing your Python virtual environment, if you are using one.
