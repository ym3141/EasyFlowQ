# This is paritially adopted from matplotlib's official document example:
# https://matplotlib.org/stable/gallery/event_handling/poly_editor.html#sphx-glr-gallery-event-handling-poly-editor-py 

import numpy as np
from matplotlib.lines import Line2D
from matplotlib.artist import Artist
from matplotlib.path import Path as mpl_path


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

class polygonGateEditor:
    """
    This class deal with creating and editing gate
    it take, edit, and generate a plygonGate instance
    """
    def __init__(self, ax, returnGateTo, canvasParam=None, gate=None) -> None:

        self.ax = ax
        self.canvas = self.ax.figure.canvas
        self.returnToFunc = returnGateTo
        self.background = None
        self.chnls, self.axScales = canvasParam

        if not gate:
            self.line = Line2D([], [], animated=True,
                            marker='s', markerfacecolor='w', markersize=5, color='r')
        else:
            pass
        self.ax.add_line(self.line)
        # self.canvas.mpl_connect('draw_event', self.on_draw)
        self.background = self.canvas.copy_from_bbox(self.ax.bbox)
        # self.cid = self.line.add_callback(self.line_changed)

    def addGate_on_press(self, event):
        if event.button == 1:
            vert = [event.xdata, event.ydata]
            xydata = self.line.get_xydata()
            xydata = np.vstack((xydata[0:-1], vert, vert))
            self.line.set_data(xydata.T)

            self.blitDraw()

        elif event.button == 3:
            # right click recieved, close the gate
            xydata = self.line.get_xydata()
            xydata = np.vstack((xydata[0:-1], xydata[0]))
            self.line.set_data(xydata.T)

            self.canvas.mpl_disconnect(self.pressCid)
            self.canvas.mpl_disconnect(self.moveCid)
            
            self.blitDraw()

            finishedNewGate = polygonGate(self.chnls, self.axScales, closedLine=self.line)
            self.returnToFunc(finishedNewGate)

            

    def addGate_on_motion(self, event):
        vert = [event.xdata, event.ydata]
        xydata = self.line.get_xydata()
        xydata = np.vstack((xydata[0:-1], vert))
        self.line.set_data(xydata.T)

        self.blitDraw()

    def addGate_connnect(self):
        self.pressCid = self.canvas.mpl_connect('button_press_event', self.addGate_on_press)
        self.moveCid = self.canvas.mpl_connect('motion_notify_event', self.addGate_on_motion)

    def blitDraw(self):
        self.canvas.restore_region(self.background)
        self.ax.draw_artist(self.line)
        self.canvas.blit(self.ax.bbox)

class polygonGate():
    def __init__(self, chnls, axScales, closedLine=None, verts=None) -> None:

        if closedLine:
            self.verts = closedLine.get_xydata()[0:-1]
        elif verts:
            self.verts = np.array(verts)
        else:
            verts = [[0, 0], [0, np.inf], [np.inf, np.inf], [np.inf, 0]]

        self.chnls = chnls
        self.axScales = axScales

        verts4path = self.verts.copy()
        for idx, scale in enumerate(self.axScales):
            if scale == 'log':
                verts4path[:, idx] = np.log10(verts4path[:, idx])
                
        self.prebuiltPath = mpl_path(verts4path)

    def isInsideGate(self, fcsData):
        points = fcsData[:, self.chnls].copy()

        for idx, scale in enumerate(self.axScales):
            if scale == 'log':
                points[:, idx] = np.log10(points[:, idx])

        insideFlags = self.prebuiltPath.contains_points(points)

        return insideFlags


if __name__ == '__main__':
    pass