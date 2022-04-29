import seaborn as sns
import numpy as np

from PyQt5.QtGui import QDoubleValidator

class colorGenerator:
    allColors = np.vstack([
        sns.husl_palette(8, h=0, s=.9, l=.7),
        sns.husl_palette(5, h=0.0625, s=.6, l=.5),
        sns.husl_palette(2, h=0.2, s=.5, l=.3),
        sns.husl_palette(5, h=-0.1, s=.8, l=.8)
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

class axlimValidator(QDoubleValidator):
    def fixup(self, a0: str) -> str:
        if float(a0) > self.top():
            return str(self.top())
        elif float(a0) < self.bottom():
            return str(self.bottom())
        
        return super().fixup(a0)