# Development notes
This document contains notes that is intended for developers.

## Basic information about python versions
The development is mostly based on python 3.9. Backward capabilities are partially tested to python version 3.7.

## Information for packaging EasyFlowQ to standalone executables
Current EasyFlowQ standalone (python-installation-independent) packages is only available for Windows(x86) and MacOS(ARM) on the [release page](https://github.com/ym3141/EasyFlowQ/releases). This part of information is about how these packages are generated, and hopefully providing a helpful guide for people wanting to create similar packages on other platforms e.g. MacOS(intel based), native Windows on ARM, linux, etc.

In general, the the currently packaging workflow is largely based on this [tutorial](https://www.pythonguis.com/tutorials/packaging-pyqt5-pyside2-applications-windows-pyinstaller/). Thus, please read through and get familiar with some of the concepts, if you are interested.

### Prerequisite for packaging
Besides the obvious requirement of downloading/cloning/forking the [repository](https://github.com/ym3141/EasyFlowQ) properly into your local machine, there are two major categories of prerequisite.

1. **Setting up a proper python environment to run the source code.**  
This is commonly accomplished by pip or conda. Please note that PySide6 (critical in ver>=1.6) is yet available on conda, so it has to be installed from pip. Current python package dependencies can be found in the `pyproject.toml` file.  
Once all dependencies are ready, the source code can be simply run by `python ./main.py` (or `python3 ./main.py` depending on your system's default python commend). Make sure the program run as expected in the current environment.

2. **Setting up tools for standalone packaging.**  
The most critical step of the packaging is the use of [PyInstaller](https://pyinstaller.org/en/stable/). Note the PyInstaller from conda are slightly outdated comparing the one from pip, and might not be able to package PySide6, thus installing it from pip is preferred. On MacOS, [create-dmg](https://github.com/create-dmg/create-dmg) is used to create dmg packages, which provide a more "native" experience for MacOS users, and also compress the package.  

### Scripts for packaging
There are two scripts used for packaging on each system. The (power)shell script (`./release/pyi_mac.sh` for MacOS and `./release/pyi_win.ps1` for Windows) and the PyInstaller spec file (`release/pyi_universal.spec`). 

The shell scripts are system specific and responsible of cleaning up folders, getting the version number (as a string) and setting up environment for PyInstaller to run, subsequently calling PyInstaller. Eventually, these scripts also do the final packaging (making dmg files on MacOS, and simply zipping on Windows).

Note in the step, the version string is obtained by running the `__init__.py` file using python as `__main__`. 

PyInstaller's spec file ([more details on PyInstaller's documentation site](https://pyinstaller.org/en/stable/spec-files.html)) are now unified into a single file for both platforms. The script target the `./main.py` as the entry point of program. The script takes one parameter ([PyInstaller doc](https://pyinstaller.org/en/stable/spec-files.html#adding-parameters-to-spec-files)) as the version number and use it as for the naming of package. Additionally, inside the spec file, it determine what platform it is being run (using python's `system.platform`), and include the proper "hidden_imports" for each platform. 

### Potential caveats when setting up the packaging workflow
This sections talks about the potential bugs and caveats of the process. The list is by no mean complete.

One major factor here, is that the implementation of involved packages are different on different platform, even though python itself should be OS independent. A extreme example is the Intel MKL backend numpy uses, are not always used even on Windows with AMD CPU. This results in different things being packaged by PyInstaller on different machine running that "same" Windows OS.

**PyInstaller version**: It seems to me that different OS/python/env manager will install different built of PyInstaller by default, and some of them has caused problems before. The most reliable built in my experience is the one installed by the `pip` commend.

**PyInstaller's "hidden_imports"**: PyInstaller's "hidden_imports" should be able to handle most of the missing packages. If you find import errors running the packaged version, while not before the packaging, try adding the specific module into the "hidden_imports" list in the spec file. Note that lots of times, an error will only occurs when the missing module is called specifically. This means some of the import errors won't be triggered at start, but rather when the user do the specific functions. To identify all of this type of problems, one will need to test the packaged program extensively. Here is a not-so-complete list of things to look for this type of errors:
1. Function about saving different type of images, especially the vector types.
2. Function about exporting excel files.
3. Related to qt_resource_rc 

**Code-Signing on MacOS**: Code-sign is required for MacOS packages. To proper do it you need to have "Apple Certificate" and follow [these steps](https://stackoverflow.com/questions/69354021/how-do-i-go-about-code-signing-a-macos-application) (not verified). This is not done proper in the current pipeline. 
