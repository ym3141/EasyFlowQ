# Basic usage

This page will describe the basics of using EasyFlowQ, including basic settings, loading sessions and FCS files, as well as basic analysis method. For more examples, please visit our [Tutorial](Tutorial.md) page.

## First time setup

Upon the first time start, EasyFlowQ will greet you with the setting window (see below). If this is your first time using EasyFlowQ, we recommend you only change the first setting (**Default fcs directory**). Click browse and select the top-most folder that you normally keep your flow cytometry data. The EasyFlowQ will always open this directory when you load sessions or fcs files, and it will speed up your analysis workflow. 

![Startup Setting](img/StartUpSettings.png)

The other settings you can change in this page include:
- **Limit total number of dots**: Decrease the number if refreshing of dot plot is slow. 
- **Plot DPI scaling**: Tweak this if your plots' font and marks are unreasonably small or large. Generally tweak this number up will make font larger. *This is only applied to the plotting region!*

Click the "Default" button if you want to reset all settings to default.

If you encounter a "Permission Error" pop up after clicking "OK". That suggest you likely do not have the permission to write in the installed directory. The settings are not saved but you can continue to use the program and do analysis. To correct this, run the program as administrator.

Don't worry if you missed this. This setting window is always available in the **settings** menu.


