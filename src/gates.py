# This is paritially adopted from matplotlib's official document example:
# https://matplotlib.org/stable/gallery/event_handling/poly_editor.html#sphx-glr-gallery-event-handling-poly-editor-py 

import numpy as np
from matplotlib.lines import Line2D
from matplotlib.artist import Artist
from matplotlib.path import Path as mpl_path

from PyQt5 import QtCore


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

class polygonGateEditor(QtCore.QObject):
    """
    This class deal with creating and editing gate
    it take, edit, and generate a plygonGate instance
    """
    gateConfirmed = QtCore.pyqtSignal(object)

    def __init__(self, ax, canvasParam=None, gate:polygonGate=None) -> None:
        super(QtCore.QObject, self).__init__()

        self.ax = ax
        self.canvas = self.ax.figure.canvas
        self.background = None

        self.mouseholdAll = False
        self.mouseholdOnPoint = False
        self.mouseOverPoint = -1

        self.trans_axis2data = self.ax.transAxes + self.ax.transData.inverted()
        self.trans_data2axis = self.trans_axis2data.inverted()

        if not gate:
            self.line = Line2D([], [], animated=True,
                            marker='s', markerfacecolor='w', markersize=5, color='r')
            self.chnls, self.axScales = canvasParam
        else:
            self.chnls = gate.chnls
            self.axScales = gate.axScales

            xydata = np.vstack([gate.verts, gate.verts[0, :]])
            self.line = Line2D(xydata[:, 0], xydata[:, 1], animated=True,
                            marker='s', markerfacecolor='w', markersize=5, color='r')

        self.ax.add_line(self.line)
        self.background = self.canvas.copy_from_bbox(self.ax.bbox)
        self.blitDraw()

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

            if len(xydata) > 3:
                finishedNewGate = polygonGate(self.chnls, self.axScales, closedLine=self.line)
                self.gateConfirmed.emit(finishedNewGate)
            else:
                self.gateConfirmed.emit(None)

    def addGate_on_motion(self, event):
        vert = [event.xdata, event.ydata]
        xydata = self.line.get_xydata()
        xydata = np.vstack((xydata[0:-1], vert))
        self.line.set_data(xydata.T)

        self.blitDraw()

    def addGate_connect(self):
        self.pressCid = self.canvas.mpl_connect('button_press_event', self.addGate_on_press)
        self.moveCid = self.canvas.mpl_connect('motion_notify_event', self.addGate_on_motion)

    def editGate_on_press(self, event):
        if self.mouseOverPoint == -1:
            self.mouseholdAll = True
            self.canvas.setCursor(QtCore.Qt.ClosedHandCursor)
        else:
            self.mouseholdOnPoint = True

        self.lastPos = np.array([event.xdata, event.ydata])
        

    def editGate_on_release(self, event):
        self.mouseholdAll = False
        self.mouseholdOnPoint = False
        self.mouseOverPoint = -1
        self.canvas.setCursor(QtCore.Qt.OpenHandCursor)
        pass

    def editGate_on_motion(self, event):
        curPos = np.array([event.xdata, event.ydata])
        curPos_Axes = self.trans_data2axis.transform(curPos)
        xydata_Axes = self.trans_data2axis.transform(self.line.get_xydata())

        if not (self.mouseholdOnPoint or self.mouseholdAll):
            for idx, point in enumerate(xydata_Axes):
                if dist(curPos_Axes, point) < 0.02:
                    self.canvas.setCursor(QtCore.Qt.SizeAllCursor)
                    self.mouseOverPoint = idx
                    return
            self.canvas.setCursor(QtCore.Qt.OpenHandCursor)
            self.mouseOverPoint = -1

        elif self.mouseholdAll:
            moveVector_Axes = curPos_Axes - self.trans_data2axis.transform(self.lastPos)

            new_xydata_Axes = xydata_Axes + np.repeat(moveVector_Axes[np.newaxis], repeats=xydata_Axes.shape[0], axis=0)
            new_xydata = self.trans_axis2data.transform(new_xydata_Axes).T
            self.line.set_data(new_xydata)

            self.lastPos = curPos
            self.blitDraw()

        else:
            moveVector_Axes = curPos_Axes - self.trans_data2axis.transform(self.lastPos)
            
            if self.mouseOverPoint == 0 or self.mouseOverPoint == len(xydata_Axes):
                xydata_Axes[0] = curPos_Axes
                xydata_Axes[-1] = curPos_Axes
            else:
                xydata_Axes[self.mouseOverPoint] = curPos_Axes

            new_xydata = self.trans_axis2data.transform(xydata_Axes).T

            self.line.set_data(new_xydata)
            self.lastPos = curPos
            self.blitDraw()
        pass

    def editGate_connect(self):
        self.lastPos = None
        self.pressCid = self.canvas.mpl_connect('button_press_event', self.editGate_on_press)
        self.releaseCid = self.canvas.mpl_connect('button_release_event', self.editGate_on_release)
        self.moveCid = self.canvas.mpl_connect('motion_notify_event', self.editGate_on_motion)

    def blitDraw(self):
        self.canvas.restore_region(self.background)
        self.ax.draw_artist(self.line)
        self.canvas.blit(self.ax.bbox)

class lineGate:
    def __init__(self, chnl, ends) -> None:

        self.chnl = chnl
        self.ends = ends

    def isInsideGate(self, fcsData):
        points = fcsData[:, self.chnls[0]].copy()

        insideFlags = np.logical_and(points > self.ends[0], points < self.ends[1])

        return insideFlags

    @property
    def chnls(self):
        return [self.chnl, self.chnl]

class lineGateEditor(QtCore.QObject):

    gateConfirmed = QtCore.pyqtSignal(object)

    def __init__(self, ax, chnl=None, gate=None) -> None:

        super().__init__()

        self.ax = ax
        self.canvas = self.ax.figure.canvas
        self.background = None
        self.chnl = chnl

        if not gate:
            self.line = Line2D([], [], animated=True,
                            marker='|', markerfacecolor='w', markersize=5, color='r')
        else:
            pass
        self.ax.add_line(self.line)
        self.background = self.canvas.copy_from_bbox(self.ax.bbox)

    def addGate_on_press(self, event):
        if event.button == 1:
            vert = [event.xdata, event.ydata]
            xydata = self.line.get_xydata()

            if xydata.shape[0] < 2:
                xydata = np.vstack((xydata[0:-1], vert, vert))
                self.line.set_data(xydata.T)

                self.blitDraw()
            else:
                self.canvas.mpl_disconnect(self.pressCid)
                self.canvas.mpl_disconnect(self.moveCid)

                xydata = np.vstack((xydata[0:-1], [vert[0], xydata[0, 1]]))
                self.line.set_data(xydata.T)
                self.blitDraw()
                
                if xydata[0, 0] < xydata[1, 0]:
                    newLineGate = lineGate(self.chnl, [xydata[0, 0], xydata[1, 0]])
                else: 
                    newLineGate = lineGate(self.chnl, [xydata[1, 0], xydata[0, 0]])

                self.gateConfirmed.emit(newLineGate)
        
        elif event.button == 3:
            self.gateConfirmed.emit(None)
            pass
            
    def addGate_on_motion(self, event):
        vert = [event.xdata, event.ydata]
        xydata = self.line.get_xydata()

        if xydata.shape[0] < 2:
            xydata = np.vstack((xydata[0:-1], vert))
        else:
            xydata = np.vstack((xydata[0:-1], [vert[0], xydata[0, 1]]))

        self.line.set_data(xydata.T)
        self.blitDraw()

    def addGate_connect(self):
        self.pressCid = self.canvas.mpl_connect('button_press_event', self.addGate_on_press)
        self.moveCid = self.canvas.mpl_connect('motion_notify_event', self.addGate_on_motion)

    def blitDraw(self):
        self.canvas.restore_region(self.background)
        self.ax.draw_artist(self.line)
        self.canvas.blit(self.ax.bbox)

class quadrant:
    corners = [[False, False], [False, True], [True, False], [True, True]]

    def __init__(self, chnls, center) -> None:

        self.chnls = chnls
        self.center = center
        pass

    def cellNs(self, fcsData):
        xFlags = fcsData[:, self.chnls[0]] < self.center[0]
        yFlags = fcsData[:, self.chnls[1]] < self.center[1]

        Q1 = np.sum(np.logical_and(xFlags, yFlags))
        Q2 = np.sum(np.logical_and(xFlags, np.logical_not(yFlags)))
        Q3 = np.sum(np.logical_and(np.logical_not(xFlags), yFlags))
        Q4 = np.sum(np.logical_and(np.logical_not(xFlags), np.logical_not(yFlags)))

        return [np.sum(Q) for Q in [Q1, Q2, Q3, Q4]]


    def generateGates(self):
        return [quadrantGate(self.chnls, self.center, corner) for corner in quadrant.corners]
    

class quadrantGate:
    def __init__(self, chnls, center, corner) -> None:
        self.chnls = chnls
        self.center = center
        self.corner = corner
        pass

    def isInsideGate(self, fcsData):
        points = fcsData[:, self.chnls].copy()

        xFlags = points[:,0] > self.center[0] if self.corner[0] else points[:,0] < self.center[0]
        yFlags = points[:,1] > self.center[1] if self.corner[1] else points[:,1] < self.center[1]

        insideFlags = np.logical_and(xFlags, yFlags)

        return insideFlags

class quadrantEditor(QtCore.QObject):
    """
    This class deal with creating and editing quadrant
    it take, edit, and generate a quadrant instance
    """
    quadrantConfirmed = QtCore.pyqtSignal(object)

    def __init__(self, ax, canvasParam=None, quad=None) -> None:
        super(QtCore.QObject, self).__init__()

        self.ax = ax
        self.canvas = self.ax.figure.canvas
        self.background = None
        self.chnls, self.axScales = canvasParam

        if not quad:
            self.cur_xlim = self.ax.get_xlim()
            self.cur_ylim = self.ax.get_ylim()
            self.hline = self.ax.axhline(np.mean(self.cur_ylim), animated=True, color='r', ls='--')
            self.vline = self.ax.axvline(np.mean(self.cur_xlim), animated=True, color='r', ls='--')

        else:
            pass

        # self.canvas.mpl_connect('draw_event', self.on_draw)
        self.background = self.canvas.copy_from_bbox(self.ax.bbox)
        # self.cid = self.line.add_callback(self.line_changed)

    def addQuad_on_press(self, event):
        if event.button == 1:
            vert = [event.xdata, event.ydata]

            finishedQuadrant = quadrant(self.chnls, vert)
            self.quadrantConfirmed.emit(finishedQuadrant)

            self.canvas.mpl_disconnect(self.pressCid)
            self.canvas.mpl_disconnect(self.moveCid)

            self.blitDraw()

        elif event.button == 3:
            # right click recieved, cancel the quadrant

            self.canvas.mpl_disconnect(self.pressCid)
            self.canvas.mpl_disconnect(self.moveCid)
            
            self.quadrantConfirmed.emit(None)
            
            self.canvas.restore_region(self.background)
            self.canvas.blit(self.ax.bbox)


    def addQuad_on_motion(self, event):
        vert = [event.xdata, event.ydata]

        hlineLims = self.hline.get_xdata()
        self.hline.set_data(hlineLims, [vert[1], vert[1]])

        vlineLims = self.vline.get_ydata()
        self.vline.set_data([vert[0], vert[0]], vlineLims)

        self.blitDraw()

    def addQuad_connect(self):
        self.pressCid = self.canvas.mpl_connect('button_press_event', self.addQuad_on_press)
        self.moveCid = self.canvas.mpl_connect('motion_notify_event', self.addQuad_on_motion)

    def blitDraw(self):
        self.canvas.restore_region(self.background)
        self.ax.draw_artist(self.hline)
        self.ax.draw_artist(self.vline)

        self.canvas.blit(self.ax.bbox)

if __name__ == '__main__':
    pass