import maya.OpenMayaUI as mui
# from PySide import QtCore, QtGui
from Qt import QtCore, QtGui ,QtWidgets
# import shiboken
import shiboken2 as shiboken
from functools import wraps


class NodeAlignDeez(QtCore.QObject):
    kDEFAULT_SPACING = 50.0

    def __init__(self, parent=None):
        super(NodeAlignDeez, self).__init__(parent)
        self.mayaWindow = shiboken.wrapInstance(int(mui.MQtUtil.mainWindow()), QtWidgets.QMainWindow)
        self.panelGraphics = None
        self._findPanelEditor()
        self.itemsToScale = []
        self.scaleCenter = None
        return

    @staticmethod
    def _getItems(graphics):
        if not isinstance(graphics, QtWidgets.QGraphicsView):
            return None
        else:
            return [ item for item in list(graphics.items()) if not isinstance(item, QtWidgets.QGraphicsPathItem) and not isinstance(item, QtWidgets.QGraphicsProxyWidget) and item.isSelected()
                   ]

    @staticmethod
    def _boundingCenter(items):
        if not items:
            return None
        else:
            points = ((item.x(), item.y()) for item in items)
            x, y = list(zip(*points))
            minPnt = (min(x), min(y))
            maxPnt = (max(x), max(y))
            return QtCore.QPointF(min(x) + max(x), min(y) + max(y)) / 2

    @staticmethod
    def _avgPos(items):
        if not items:
            return 0.0
        posX = items[0].x()
        posY = items[0].y()
        for item in items[1:]:
            posX += item.x()
            posY += item.y()

        return QtCore.QPointF(posX / len(items), posY / len(items))

    @staticmethod
    def _avgPosX(items):
        if not items:
            return 0.0
        posX = items[0].x()
        for item in items[1:]:
            posX += item.x()

        return posX / len(items)

    @staticmethod
    def _avgPosY(items):
        if not items:
            return 0.0
        posY = items[0].y()
        for item in items[1:]:
            posY += item.y()

        return posY / len(items)

    @staticmethod
    def _setAvgPosX(avgPosX, items):
        if not items:
            return
        for item in items:
            item.setPos(avgPosX, item.y())

    @staticmethod
    def _setAvgPosY(avgPosY, items):
        if not items:
            return
        for item in items:
            item.setPos(item.x(), avgPosY)

    @staticmethod
    def _editorCenter(graphicsView):
        width = graphicsView.width() / 2
        height = graphicsView.height() / 2
        centerPoint = graphicsView.mapToScene(width, height)
        return centerPoint

    @staticmethod
    def _setItemsGrpPosX(grpPos, centerPos, items):
        if not items:
            return
        for item in items:
            delta = item.x() - grpPos.x()
            posX = centerPos.x() + delta
            item.setPos(posX, item.y())

    @staticmethod
    def _setItemsGrpPosY(grpPos, centerPos, items):
        if not items:
            return
        for item in items:
            delta = item.y() - grpPos.y()
            posY = centerPos.y() + delta
            item.setPos(item.x(), posY)

    @staticmethod
    def _setItemsGrpPos(grpPos, centerPos, items):
        if not items:
            return
        for item in items:
            delta = item.pos() - grpPos
            pos = centerPos + delta
            item.setPos(pos)

    @staticmethod
    def _sortItemsByPosY(items):
        if not items:
            return None
        else:
            items.sort(key=lambda item: item.y())
            return None

    @staticmethod
    def _sortItemsByPosX(items):
        if not items:
            return None
        else:
            items.sort(key=lambda item: item.x())
            return None

    @staticmethod
    def _magnitude(item):
        return math.sqrt(sum((axis ** 2 for axis in item.pos())))

    @staticmethod
    def _itemsWidth(items):
        if not items:
            return
        return sum((item.boundingRect().width() for item in items))

    @staticmethod
    def _itemsHeight(items):
        if not items:
            return
        return sum((item.boundingRect().height() for item in items))

    @staticmethod
    def _distributePosY(items):
        if not items:
            return None
        else:
            NodeAlignDeez._sortItemsByPosY(items)
            itemsHeight = NodeAlignDeez._itemsHeight(items)
            minY = items[0].y()
            maxY = items[-1].y() + items[-1].boundingRect().height()
            distHeight = maxY - minY
            verticalSpacing = (distHeight - itemsHeight) / (len(items) - 1)
            posY = minY
            for item in items:
                item.setPos(item.x(), posY)
                posY += item.boundingRect().height() + verticalSpacing

            return None

    @staticmethod
    def _distributePosX(items):
        if not items:
            return None
        else:
            NodeAlignDeez._sortItemsByPosX(items)
            itemsWidth = NodeAlignDeez._itemsWidth(items)
            minX = items[0].x()
            maxX = items[-1].x() + items[-1].boundingRect().width()
            distWidth = maxX - minX
            horizontalSpacing = (distWidth - itemsWidth) / (len(items) - 1)
            posX = minX
            for item in items:
                item.setPos(posX, item.y())
                posX += item.boundingRect().width() + horizontalSpacing

            return None

    @classmethod
    def _stackPosX(cls, items):
        if not items:
            return None
        else:
            cls._sortItemsByPosX(items)
            itemsWidth = cls._itemsWidth(items)
            avgPosX = cls._avgPosX(items) + items[-1].boundingRect().width() / 2
            distWidth = itemsWidth + cls.kDEFAULT_SPACING * (len(items) - 1)
            posX = avgPosX - distWidth / 2
            for item in items:
                item.setPos(posX, item.y())
                posX += item.boundingRect().width() + cls.kDEFAULT_SPACING

            return None

    @classmethod
    def _stackPosY(cls, items):
        if not items:
            return None
        else:
            cls._sortItemsByPosY(items)
            itemsHeight = cls._itemsHeight(items)
            avgPosY = cls._avgPosY(items) + items[-1].boundingRect().height() / 2
            distHeight = itemsHeight + cls.kDEFAULT_SPACING * (len(items) - 1)
            posY = avgPosY - distHeight / 2
            for item in items:
                item.setPos(item.x(), posY)
                posY += item.boundingRect().height() + cls.kDEFAULT_SPACING

            return None

    @staticmethod
    def _scaleItemPos(center, itemPos, item, scale=1.0):
        if not item or scale == 1.0:
            return
        pos = [
         itemPos.x(), itemPos.y()]
        pos[0] -= center.x()
        pos[1] -= center.y()
        a = pos[0]
        b = pos[1]
        pos[0] *= scale + scale
        pos[1] *= scale + scale
        pos[0] += a
        pos[1] += b
        pos[0] += center.x()
        pos[1] += center.y()
        item.setPos(pos[0], pos[1])

    def _findPanelEditor(self):
        nodePanel = self.mayaWindow.findChild(QtWidgets.QWidget, 'nodeEditorPanel1')
        if nodePanel and shiboken.isValid(nodePanel):
            self.panelGraphics = nodePanel.findChildren(QtWidgets.QGraphicsView)[-1]
            return True
        else:
            return False

    def _validatePanelEditor(self):
        if not self.panelGraphics or not shiboken.isValid(self.panelGraphics):
            if self._findPanelEditor():
                return self.panelGraphics
            else:
                return None

        else:
            return self.panelGraphics
        return None

    def alignPos(func):

        @wraps(func)
        def decorator(self, *args, **kwargs):
            graphicsView = self._validatePanelEditor()
            if not graphicsView:
                return
            items = self._getItems(graphicsView)
            func(self, items)

        return decorator

    @alignPos
    def alignPosX(self, items):
        avgPosX = self._avgPosX(items)
        self._setAvgPosX(avgPosX, items)

    @alignPos
    def alignPosY(self, items):
        avgPosY = self._avgPosY(items)
        self._setAvgPosY(avgPosY, items)

    def centerItems(func):

        @wraps(func)
        def decorator(self, *args, **kwargs):
            graphicsView = self._validatePanelEditor()
            if not graphicsView:
                return
            items = self._getItems(graphicsView)
            boundingCenter = self._boundingCenter(items)
            centerPos = self._editorCenter(graphicsView)
            func(self, boundingCenter, centerPos, items)

        return decorator

    @centerItems
    def centerPosX(self, boundingCenter, centerPos, items):
        self._setItemsGrpPosX(boundingCenter, centerPos, items)

    @centerItems
    def centerPosY(self, boundingCenter, centerPos, items):
        self._setItemsGrpPosY(boundingCenter, centerPos, items)

    @centerItems
    def centerPos(self, boundingCenter, centerPos, items):
        self._setItemsGrpPos(boundingCenter, centerPos, items)

    def distributeItems(func):

        @wraps(func)
        def decorator(self, *args, **kwargs):
            graphicsView = self._validatePanelEditor()
            if not graphicsView:
                return
            items = self._getItems(graphicsView)
            func(self, items)

        return decorator

    @distributeItems
    def distributePosX(self, items):
        self._distributePosX(items)

    @distributeItems
    def distributePosY(self, items):
        self._distributePosY(items)

    @distributeItems
    def stackPosX(self, items):
        self._stackPosX(items)

    @distributeItems
    def stackPosY(self, items):
        self._stackPosY(items)

    def setItemsToBeScaled(self):
        graphicsView = self._validatePanelEditor()
        if not graphicsView:
            return
        items = self._getItems(graphicsView)
        if not items:
            self.itemsToScale = []
            return
        self.itemsToScale = [ (item, item.pos()) for item in items ]
        self.scaleCenter = self._boundingCenter(items)

    def scaleSetItems(self, scale=1.0):
        if scale == 1.0:
            return
        graphicsView = self._validatePanelEditor()
        if not graphicsView:
            return
        for itemData in self.itemsToScale:
            self._scaleItemPos(self.scaleCenter, itemData[1], itemData[0], scale)