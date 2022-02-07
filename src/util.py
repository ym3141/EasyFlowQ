import seaborn as sns
import numpy as np

class colorGenerator:
    allColors = np.vstack([
        sns.husl_palette(6, h=0, s=.9, l=.7),
        sns.husl_palette(6, h=0.0625, s=.9, l=.5),
        sns.husl_palette(6, h=-0.0625, s=.5, l=.7) 
    ])

    def __init__(self) -> None:
        self.count = 0
        pass

    def giveColors(self, n=1):
        colorLibLength = len(colorGenerator.allColors)
        if self.count + n < colorLibLength:
            returnColors =  colorGenerator.allColors[self.count : self.count + n]
        else:
            cycledColors = np.vstack([colorGenerator.allColors] * int(np.ceil(n / colorLibLength)))
            returnColors = cycledColors[self.count : self.count + n]

        self.count += n
        self.count = self.count % colorLibLength

        return returnColors

