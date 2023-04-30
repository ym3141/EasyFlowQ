import seaborn as sns
import numpy as np


class colorGenerator:
    allColors = np.vstack([
        sns.color_palette('Dark2'),
        sns.color_palette('Set1'),
        sns.color_palette('cool', 4),
        sns.color_palette('autumn', 4)
    ])

    divColors = np.vstack([
        sns.color_palette('winter_d', 4),
        sns.color_palette('autumn_d', 4),
    ])


    def __init__(self) -> None:
        self.count = 0
        pass

    def giveColors(self, n=1, startCount=None):
        if startCount is None:
            startCount = self.count
            self.count += n
            self.count = self.count % self.colorLibLength


        if startCount + n < self.colorLibLength:
            returnColors =  colorGenerator.allColors[startCount: startCount + n]
        else:
            cycledColors = np.vstack([colorGenerator.allColors] * int(np.ceil(n / self.colorLibLength)))
            returnColors = cycledColors[startCount: startCount + n]

        return returnColors
    
    def giveColors_div(self, n=1):
        if n <= len(colorGenerator.divColors):
            return colorGenerator.divColors[0: n]
        else:
            extraColorN = n - len(colorGenerator.divColors)
            return np.vstack([colorGenerator.divColors, self.giveColors(extraColorN, startCount=0)])
        
    
    @property
    def colorLibLength(self):
        return len(colorGenerator.allColors)