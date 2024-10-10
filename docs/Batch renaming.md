# Batch-renaming with xlsx

**Note**: This page if for batch renaming samples. If you want to rename individual sample, simply click the name in the "sample section" on the left of the window, and rename it.

Renaming samples from a high throughput experiment setup can be time consuming. EasyflowQ provides two methods to batch renaming samples names. Both methods provides a easy way for batch renaming your samples using a excel files (.xlsx). To access these tools, go to "Data" -> "Rename with file" (see below).

![BasicOperations](img/BatchRename.jpg)

## Regular rename (Single mapping)
---
For basic renaming, create a excel file (.xlsx), with the sample names (file name without ".fcs" by default) in the first column (A), and new names in the second column (B). Save this excel file at desired location. We recommend the same folder as the .fcs files. Here is an example:

![SimpleRenameExcel](img/SimpleRename.jpg){: style="width:300px"}

Then go back to EasyFlowQ, and select **Simple mapping** in the menu, and load the file created above. The pop-out will preview your renaming pairs for you the confirm it. 

## [CytoFLEX](https://www.beckman.com/landing/ppc/flow/cytoflex) format file names
---
BECKMAN's CytoFLEX flow cytometer use a unique naming system when under the plate mode. The schemes follows the patterns `(plate#)-('Tube' or 'Well')-(plate coordinate)` (e.g., `01-Well-B3`). Based on this, EasyflowQ can rename them with a excel sheet "resembling" a 2D plate labels, similar to the following:




## Notes applies to both method of batch renaming
1. The renames are only applied on the EasyFlowQ session level. This means nothing in the fcs file, including the content or the file names, were changed.
2. You can run rename multiple times, with different or same (edited) xlsx file. 
3. Technically you can rename two different sample to a the same name, but it is not recommended.