from PySide6.QtGui import QColor

filename = 'sub-sample.csv'

major_grid = 500
minor_grid = 100

major_grid_color = QColor('dodgerblue')
minor_grid_color = QColor('mediumblue')
bg_color = QColor('darkblue')
marker_done_color = QColor('slateblue')
hover_bg_color = QColor('lime')
hover_fg_color = QColor('white')

init_scale = 0.75
window_width = 2560
window_height = 1440

font_family = 'Helvetica Neue'
font_size = 16
font_bold = True

label_offset_x = 10
label_offset_y = -2

markers = {
    'pod':         {'color': 'limegreen', 'icon': 'star'},
    'wreck':       {'color': 'coral', 'icon': 'x'},
    'biome':       {'color': 'limegreen', 'icon': 'circle'},
    'interest':    {'color': 'gold', 'icon': 'triangle'},
    'alien':       {'color': 'fuchsia', 'icon': 'square'},
    'mur':         {'color': 'deepskyblue', 'icon': 'square'},
    'misc':        {'color': 'darkorange', 'icon': 'circle'}
    }

icons = {
    'square': [(-4, -4), (4, -4), (4, 4), (-4, 4)],
    'triangle': [(0, -4), (4, 4), (-4, 4)],
    'star': [(-1, -1), (0, -5), (1, -1), (5, 4), (0, 1), (-5, 4), (-1, -1)],
    'x': [(0, -2), (3, -5), (5, -3), (2, 0), (5, 3),
          (3, 5), (0, 2), (-3, 5), (-5, 3), (-2, 0), (-5, -3), (-3, -5)]
    }

circle = 4  # Radius in pixels
