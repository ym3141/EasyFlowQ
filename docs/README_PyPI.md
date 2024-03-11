# Welcome to EasyFlowQ
EasyFlowQ is an open-source, user-friendly flow cytometry analyzer with graphic user interface (GUI).
For full documentation and tutorials, visit [EasyFlowQ's Documentation Site](https://ym3141.github.io/EasyFlowQ/).

## Overview
A user friendly GUI interface for analyzing flow cytometry data. The program is implemented by Qt/Python, and its UI logics are largely influenced by the original matlab version of [EasyFlow (by @ayaron)](https://github.com/AntebiLab/easyflow). The fcs file parser is based on the [FlowCal package](https://github.com/taborlab/FlowCal), with slight modification for implementing into the GUI. The standalone installers are packaged by [PyInstaller](https://pyinstaller.org/en/stable/) and [InstallForge](https://installforge.net/).

## Download and usage

To download EasyFlowQ from PyPI:
```
pip install EasyFlowQ
```

After installation, run:
```
EasyFlowQ
```

Or run it from a script using:
```
import EasyFlowQ.main_entry
EasyFlowQ.main_entry.newWindowFunc()
```

## Documentation site:
Please refers to [the documentation site](https://ym3141.github.io/EasyFlowQ/) for more information.

## Contact
For more info please contact <yitongma7@gmail.com>. If you use *EasyFlowQ* in your research, we would appreciate citation to the following preprint:
> Ma, Y., & Antebi, Y. (2023). EasyFlow: An open source, user friendly cytometry analyzer with graphic user interface (GUI). bioRxiv, 2023-08.
