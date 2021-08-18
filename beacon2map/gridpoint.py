#!/usr/bin/env python

import logging

from PySide6.QtCore import QEvent, QPropertyAnimation, QRect, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QFontMetrics, QPainter, QPen
from PySide6.QtWidgets import QGraphicsItem, QGraphicsObject, QStyleOption, QWidget


logger = logging.getLogger(__name__)


class GridPoint(QGraphicsObject):
    '''GridPoint is a QGraphicsObject which has attributes suitable
    to displaying information about a map point.

    Args:
        title (str): the main text to be displayed next to the item
        subtitle (str): text to be displayed below the title, in smaller font
        source_obj (any): a reference to the source object of which the
            GridPoint is a representation

        color (QColor): if not set, defaults to white
        icon (unicode): if not set, defaults to circle
    Returns:
        GridPoint object
    '''

    # Base font for gridpoint title
    FONT_SIZE = 16
    FONT_FAMILY = 'Helvetica Neue'

    # Base offset of title from the gridpoint icon
    LABEL_OFFSET_X = 15
    LABEL_OFFSET_Y = -3

    # Colors
    COLOR_DEFAULT = QColor('white')
    COLOR_SELECTED = QColor('white')

    def __init__(self, **kwargs):
        super().__init__()

        self.source = None
        self._title = None
        self._subtitle = None

        self._color = None
        self._icon = None
        self._hover_fg_color = None
        self._hover_bg_color = None

        # Set the variables passed in the named parameters
        for k, v in kwargs.items():
            if k in self.__dict__:
                setattr(self, k, v)
            else:
                raise ValueError(
                    f'\nInvalid paramater for Gridpoint: \'{k}\'')

        self.font_title = QFont()
        self.font_title.setFamily(self.FONT_FAMILY)
        self.font_title.setPixelSize(self.FONT_SIZE)
        self.font_title.setBold(True)

        self.font_subtitle = QFont()
        self.font_subtitle.setFamily(self.FONT_FAMILY)
        self.font_subtitle.setPixelSize(self.FONT_SIZE * 0.85)
        self.font_subtitle.setBold(True)

        self.mouse_hover = False

        self.anim_opacity = QPropertyAnimation(self, b'opacity')
        self.anim_opacity.setDuration(150)
        self.anim_opacity.finished.connect(self.anim_opacity_finished)
        self.visible = True

        # Set Qt flags
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemIgnoresTransformations)
        self.setFlag(QGraphicsItem.ItemIsFocusable)
        self.setAcceptHoverEvents(True)


    def paint(self, painter: QPainter, option: QStyleOption, widget: QWidget) -> None:
        if self.mouse_hover:
            self.hover_bg_color.setAlpha(128)
            painter.setPen(Qt.NoPen)
            painter.setBrush(self.hover_bg_color)
            painter.drawRoundedRect(self.boundingRect(), 5, 5)

        if self.isSelected():
            painter.setPen(QPen(self.COLOR_SELECTED, 1))
            painter.setBrush(self.hover_bg_color)
            painter.drawRoundedRect(self.boundingRect(), 5, 5)

        color = self.hover_fg_color if (
            self.mouse_hover or self.isSelected()) else self.color

        brush = QBrush(Qt.SolidPattern)
        brush.setColor(color)
        painter.setPen(QPen(color))
        painter.setBrush(brush)

        # Draw icon
        painter.setFont(self.font_title)
        painter.drawText(-8, 6, self.icon)

        # Draw title
        painter.drawText(self.LABEL_OFFSET_X, self.LABEL_OFFSET_Y, self.title)

        # Draw subtitle
        painter.setFont(self.font_subtitle)
        painter.drawText(self.LABEL_OFFSET_X,
                         self.LABEL_OFFSET_Y + self.FONT_SIZE,
                         self.subtitle)

    def boundingRect(self) -> QRect:
        '''
        Return the boundingRect of the entire object by uniting the title,
        subtitle and icon boundingRects.
        https://stackoverflow.com/questions/68431451/
        '''
        rect_icon = QFontMetrics(self.font_title).boundingRect(
            self.icon).translated(-8, 6)
        rect_title = QFontMetrics(self.font_title).boundingRect(
            self.title).translated(
                self.LABEL_OFFSET_X, self.LABEL_OFFSET_Y)
        rect_subtitle = QFontMetrics(self.font_subtitle).boundingRect(
            self.subtitle).translated(
                self.LABEL_OFFSET_X,
                self.LABEL_OFFSET_Y + self.FONT_SIZE)
        return (
            rect_title | rect_subtitle | rect_icon).adjusted(-10, -5, 10, 5)

    def setVisible(self, state: bool) -> None:
        # Override setVisible to animate opacity when showing or hiding.
        # self.visible is used as a target value
        # We only do the animation if the state is changing
        if state is not self.visible:
            self.anim_opacity.stop()
            if state is False:
                self.visible = False
                self.anim_opacity.setStartValue(self.opacity())
                self.anim_opacity.setEndValue(0.0)
                self.anim_opacity.start()
            elif state is True:
                super().setVisible(True)
                self.visible = True
                self.anim_opacity.setStartValue(self.opacity())
                self.anim_opacity.setEndValue(1.0)
                self.anim_opacity.start()

    def anim_opacity_finished(self) -> None:
        if self.opacity() == 0:
            super().setVisible(False)

    def hoverEnterEvent(self, e: QEvent) -> QEvent:
        self.mouse_hover = True
        self.update()
        return super().hoverLeaveEvent(e)

    def hoverLeaveEvent(self, e: QEvent) -> QEvent:
        self.mouse_hover = False
        self.update()
        return super().hoverLeaveEvent(e)

    # Modifying the title or subtitle will change the QGraphicsItem boundingRect
    # so we need to call prepareGeometryChange() first

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, value):
        self.prepareGeometryChange()
        self._title = str(value)

    @property
    def subtitle(self):
        return self._subtitle

    @subtitle.setter
    def subtitle(self, value):
        self.prepareGeometryChange()
        self._subtitle = str(value)

    @property
    def color(self):
        if self._color is None:
            return self.COLOR_DEFAULT
        return self._color

    @color.setter
    def color(self, value: QColor):
        self._color = value

    @property
    def icon(self):
        return '\u25cf' if self._icon is None else self._icon

    @icon.setter
    def icon(self, value):
        self._icon = value

    @property
    def hover_fg_color(self):
        if self._hover_fg_color is None:
            return QColor('white')
        return self._hover_fg_color

    @hover_fg_color.setter
    def hover_fg_color(self, value: QColor):
        self._hover_fg_color = value

    @property
    def hover_bg_color(self):
        if self._hover_bg_color is None:
            return QColor('lime')
        return self._hover_bg_color

    @hover_bg_color.setter
    def hover_bg_color(self, value: QColor):
        self._hover_bg_color = value

    def __repr__(self):
        rep = f'GridPoint object: {self.title} zValue={self.zValue()} {self.source.beacon}'
        return rep


#
# Barebones test window for QGraphicsItem/QGraphicsObject 
#

if (__name__ == '__main__'):
    from PySide6.QtWidgets import QApplication
    from PySide6.QtWidgets import QGraphicsScene, QGraphicsView
    a = QApplication()
    s = QGraphicsScene()

    # Modify with required class
    i = GridPoint()
    i.title = 'Title'
    i.subtitle = 'Subtitle'
    s.addItem(i)
    t = s.addText('GridPoint Class')
    t.setPos(0, -50)

    v = QGraphicsView(s)
    v.show()
    i.setVisible(True)
    a.exec()
