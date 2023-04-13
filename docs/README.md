# Welcome to EasyFlowQ
EasyFlowQ is an open-source, user-friendly flow cytometry analyzer with graphic user interface (GUI).
For full documentation and tutorials, visit [EasyFlowQ's Documentation Site](https://ym3141.github.io/EasyFlowQ/).

## Overview
A user friendly GUI interface for analyzing flow cytometry data. The program is implemented by Qt/Python, and its UI logics are largely influenced by the original matlab version of [EasyFlow (by @ayaron)](https://github.com/AntebiLab/easyflow). The fcs file parser is based on the [FlowCal package](https://github.com/taborlab/FlowCal), with slight modification for implementing into the GUI. The standalone installers are packaged by [PyInstaller](https://pyinstaller.org/en/stable/) and [InstallForge](https://installforge.net/).

## Download and usage

You can either install EasyFlowQ via the provided installers, or run it directly with python ([Anaconda](https://www.anaconda.com/) installation required).

**Method #1: Use the provided installer (Windows or MacOS)**

Please refer to [release page](https://github.com/ym3141/EasyFlowQ/releases/) to download the latest standalone packages that can run on either MacOS or Windows. In most case, you should be able to run it without other dependency.

**Method #2: Run from python (a python installation is needed)**

For running the program from the source, download the whole code and run the command below. Standard Anaconda should be sufficient for running the program.
```
Path/To/Folder$ python ./main.py
```

## Contact
For more info please contact <yma2@caltech.edu>