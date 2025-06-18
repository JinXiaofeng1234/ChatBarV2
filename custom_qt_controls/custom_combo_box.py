from PyQt5.QtWidgets import QComboBox, QStyledItemDelegate
from PyQt5.QtGui import QIcon, QPainter, QColor, QFont, QFontMetrics
from PyQt5.QtCore import Qt, QSize


class CustomItemDelegate(QStyledItemDelegate):
    def paint(self, painter: QPainter, option, index):
        painter.save()

        # 获取数据
        icon = index.data(Qt.DecorationRole)
        text = index.data(Qt.DisplayRole)

        # 绘制背景
        if option.state & Qt.ItemIsSelectable:
            painter.fillRect(option.rect, QColor("#5a5a5a"))  # 选中时的背景色
        else:
            painter.fillRect(option.rect, QColor("#3c3c3c"))  # 默认背景色


        # 计算图标和文本的位置
        icon_size = QSize(25, 25)  # 图标大小
        icon_rect = option.rect.adjusted(5, (option.rect.height() - icon_size.height()) // 2, 0, 0)
        icon_rect.setSize(icon_size)

        text_rect = option.rect.adjusted(icon_rect.width() + 10, 0, -5, 0) # 文本位置，留出图标空间

        # 绘制图标
        if icon:
            painter.drawPixmap(icon_rect, icon.pixmap(icon_size))

        # 绘制文本
        painter.setPen(Qt.white)  # 文本颜色
        painter.drawText(text_rect, Qt.AlignVCenter, text)

        painter.restore()

    def sizeHint(self, option, index):
        # 设置每个item的高度
        return QSize(option.rect.width(), 40) # 可以根据需要调整高度

def sample():
    combo_box = QComboBox()
    combo_box.setGeometry(50, 50, 300, 100)
    combo_box.setFixedSize(195, 50)
    combo_box.setFont(QFont("黑体", 15))


    delegate = CustomItemDelegate()
    combo_box.setItemDelegate(delegate)
    # 设置背景色和隐藏箭头
    combo_box.setStyleSheet("""
             QComboBox {
                 background-color: #3c3c3c;
                 color: white;
                 border: 1px solid #5a5a5a;
                 border-radius: 15px; /* 移除圆角，使其成为矩形 */
             }
             QComboBox::drop-down {
                 width: 0px; /* 将宽度设置为0，隐藏下拉箭头区域 */
                 border-left-width: 0px; /* 隐藏左边框 */
             }
             QComboBox::down-arrow {
                 image: none; /* 隐藏下拉箭头图标 */
             }
             QComboBox QAbstractItemView {
                 border-radius: 15px; /* 移除下拉菜单的圆角 */
                 background-color: #3c3c3c; /* 下拉菜单背景色 */
                 selection-background-color: #5a5a5a; /* 选中项背景色 */
                 color: white;

             }
         """)
    return combo_box

def model_combo_box(data):
    combo_box = sample()
    longgest_string = max(data.keys(), key=len)
    font_metrics = QFontMetrics(combo_box.font())
    text_width = font_metrics.width(longgest_string)
    combo_box.setFixedSize(text_width + 50, 50)

    # 添加一些带有图标和文本的item
    for key,value in data.items():
        # print(value)
        combo_box.addItem(QIcon(value['img_path']), key)

    return combo_box