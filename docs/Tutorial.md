# Step-by-step example
**This page is still in the works**

Here we provide a step-by-step example of using EasyFlow to analyze a dataset of 
The dataset used in this tutorial can be downloaded from: ..... This tutorial is also part of demos published in 

## Step 0: Considerations before start
Before start, we highly recommend your download or move all the data (fcs files) into a local drive on your system, and make sure you have the permission to write to the drive (or folder). Depending on your operation system, it might be helpful to run EasyFlowQ as administrator if possible.

## Step 1: Start EasyFlowQ and load fcs file
Start EasyFlowQ using your [method of choice](README.md#download-install-and-run) (either through a GUI, CLI, or directly from python script). Click the "Load data (.fcs)" button in the interface's upper left corner (Ctrl + L also works). Navigate to the place of your fcs files, and select the following files.

    Unstained.fcs
    Stained.fcs

Select open, and the fcs files should be loaded.

## Step 2: Save a session file (optional)
We highly recommend to save the session at this point. To do so, simple select "File -> Save" in the menu bar (Ctrl + S also works). We recommend save the session file in the same directory with the fcs file.

## Step 3: Create polygon gates for live and single cells
