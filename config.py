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

label_offset_x = 20
label_offset_y = -5

markers = {
    'pod':         {'color': 'limegreen', 'icon': '\u25a3'},
    'wreck':       {'color': 'coral', 'icon': '\u25e9'},
    'biome':       {'color': 'limegreen', 'icon': '\u25b2'},
    'interest':    {'color': 'gold', 'icon': '\u25fc'},
    'alien':       {'color': 'fuchsia', 'icon': '\u25c8'},
    'mur':         {'color': 'deepskyblue', 'icon': '\u2630'},
    'misc':        {'color': 'darkorange', 'icon': '\u25ef'}
    }