# Welcome to EasyFlowQ
EasyFlowQ is an open-source, user-friendly flow cytometry analyzer with graphic user interface (GUI).
For full documentation and tutorials, visit [EasyFlowQ's Documentation Site](https://ym3141.github.io/EasyFlowQ/).

## Overview
A user friendly GUI interface for analyzing flow cytometry data. The program is implemented by Qt/Python, and its UI logics are largely influenced by the original matlab version of [EasyFlow (by @ayaron)](https://github.com/AntebiLab/easyflow). The fcs file parser is based on the [FlowCal package](https://github.com/taborlab/FlowCal), with slight modification for implementing into the GUI. The standalone installers are packaged by [PyInstaller](https://pyinstaller.org/en/stable/) and [InstallForge](https://installforge.net/).

## Download and usage

You can either install EasyFlowQ via the provided installers, or run it directly with python ([Anaconda](https://www.anaconda.com/) installation required).

#### **Method #1:** Use the provided installer (Windows or MacOS)

Please refer to [release page](https://github.com/ym3141/EasyFlowQ/releases/) (see below) to download the latest standalone packages for your operating system (MacOS or Windows) and install EasyFlowQ. In most case, you should be able to run it without other dependency.

*Special note for MacOS users: you will need to ctrl/right-click the app and select open for the first time after you put the app into the "Application" folder. The system will remember it as an exception for later time (see [here](https://support.apple.com/guide/mac-help/open-a-mac-app-from-an-unidentified-developer-mh40616/mac)).*

![Download page](img/ReleasePage.jpg)

#### **Method #2:** Run from python (a python installation is needed)

For running the program from the source, download the whole code and run the command below. Standard Anaconda should be sufficient for running the program.
```
Path/To/Folder$ python ./main.py
```
## First time startup
For first time startup settings, please goto our [usage page](Basic Usage.md#first-time-setup).

## Contact and cite
For more info please contact <yitongma7@gmail.com>. If you use *EasyFlowQ* in your research, we would appreciate citation to the following preprint:
> Ma, Y., & Antebi, Y. (2023). EasyFlow: An open source, user friendly cytometry analyzer with graphic user interface (GUI). bioRxiv, 2023-08.