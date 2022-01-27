# This is paritially adopted from matplotlib's official document example:
# https://matplotlib.org/stable/gallery/event_handling/poly_editor.html#sphx-glr-gallery-event-handling-poly-editor-py 

import numpy as np
from matplotlib.lines import Line2D
from matplotlib.artist import Artist


def dist(x, y):
    """
    Return the distance between two points.
    """
    d = x - y
    return np.sqrt(np.dot(d, d))

def dist_point_to_segment(p, s0, s1):
    """
    Get the distance of a point to a segment.
      *p*, *s0*, *s1* are *xy* sequences
    This algorithm from
    http://www.geomalgorithms.com/algorithms.html
    """
    v = s1 - s0
    w = p - s0
    c1 = np.dot(w, v)
    if c1 <= 0:
        return dist(p, s0)
    c2 = np.dot(v, v)
    if c2 <= c1:
        return dist(p, s1)
    b = c1 / c2
    pb = s0 + b * v
    return dist(p, pb)

class polygonGate:
    def __init__(self, ax, firstVert) -> None:
        self.line = Line2D([firstVert[0]], [firstVert[1]], animated=True,
                           marker='s', markerfacecolor='w', markersize=5,)
        self.ax = ax
        self.canvas = self.ax.figure.canvas

        self.ax.add_line(self.line)
        self.canvas.mpl_connect('draw_event', self.on_draw)
        # self.cid = self.line.add_callback(self.line_changed)

    def addNewVert(self, vert):
        xydata = self.line.get_xydata()
        xydata = np.vstack((xydata[0:-1], vert, vert))
        self.line.set_data(xydata.T)

    def replaceLastVert(self, vert):
        xydata = self.line.get_xydata()
        xydata = np.vstack((xydata[0:-1], vert))
        self.line.set_data(xydata.T)

    def closeGate(self):
        xydata = self.line.get_xydata()
        xydata = np.vstack((xydata[0:-1], xydata[0]))
        self.line.set_data(xydata.T)

    def on_draw(self, event):
        # self.background = self.canvas.copy_from_bbox(self.ax.bbox)
        self.ax.draw_artist(self.line)
        # do not need to blit here, this will fire before the screen is
        # updated


if __name__ == '__main__':
    pass