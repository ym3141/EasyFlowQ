import seaborn as sns
import numpy as np
import re

# Characters that are illegal in a file name on at least one of the supported
# platforms. Sample names are free text, so they have to be cleaned up before
# they can be offered as a default file name.
_illegalFileNameChars = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def sanitizeFileName(name: str) -> str:
    # Make `name` usable as a file name, without its extension.
    sanitized = _illegalFileNameChars.sub('_', str(name)).strip()

    # Trailing dots and spaces are dropped by Windows, which would silently
    # change the name the user asked for.
    sanitized = sanitized.rstrip('. ')

    return sanitized if sanitized else 'sample'


def illegalFileNameReason(name: str):
    # Return why `name` cannot be used as a file name, or None if it can be.
    if not name.strip():
        return 'the name is empty'
    if _illegalFileNameChars.search(name):
        return 'the name contains one of < > : " / \\ | ? *'
    if name != name.rstrip('. '):
        return 'the name ends with a dot or a space'

    return None



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
            cycledColors = np.vstack([colorGenerator.allColors] * (n // self.colorLibLength + 2))
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