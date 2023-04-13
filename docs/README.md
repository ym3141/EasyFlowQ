# Welcome to EasyFlowQ
EasyFlowQ is an open-sourced, user-friendly flowcytometry analyzer with graphic user interface (GUI).
For full documentation and tutuorials, visit [EasyFlowQ's Documentation Site](https://ym3141.github.io/EasyFlowQ/).

## Overview
A user friendly GUI interface for analyzing flowcytometry data. The program is implemented by Qt/Python, and its UI logics are hugely influenced by the original matlab version of [EasyFlow (by @ayaron)](https://github.com/AntebiLab/easyflow). The basal fcs parsing are based on the [FlowCal package](https://github.com/taborlab/FlowCal), with slight modification for implementing into the GUI. The standalone packages are packaged by [PyInstaller](https://pyinstaller.org/en/stable/).

## Download and usage

You can either install EasyFlowQ via the provided installers, or run it directly with python ([Anaconda](https://www.anaconda.com/) installation required).

**Method #1: Using the provided installer (Windows or MacOS)**

Please refer to [release page](https://github.com/ym3141/EasyFlowQ/releases/) to download the latest standalone packages that can run on either MACOS or Windows. In most case, you should be able to run it without other dependency.

**Method #2: Run from python (a python installeration is needed)**

For running the progam from the source, download the whole code and run the commend below. Standard Anaconda should be suffecient for running the whole code.
```
Path/To/Folder$ python ./main.py
```

## Contact
For more info please contact <yma2@caltech.edu>