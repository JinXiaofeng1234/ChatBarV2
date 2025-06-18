from PyQt5.QtWidgets import QVBoxLayout, QDialog, QLabel, QComboBox, QHBoxLayout, QPushButton
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt


class SettingMenu(QDialog):
    def __init__(self, parent=None, width=0, height=0, bg_ls=list):
        super().__init__(parent)
        self.setWindowTitle('菜单')
        # 根据父窗口大小设置对话框位置，并在屏幕中央显示
        self.setGeometry(width // 2 - 150, height // 2 - 75, 300, 150)
        self.setFixedSize(300, 150) # 固定对话框大小

        self.setStyleSheet("""
            QDialog {
                background-color: #2e2e2e; /* 与主窗口背景色一致 */
                border: 2px solid #555555; /* 与主窗口边框一致 */
                border-radius: 5px; /* 与主窗口边框圆角一致 */
            }
            /* 如果有内部容器，也可以这样设置，例如： */
            QWidget#dialog_content_container {
                background-color: #3c3c3c;
                border: 2px solid #666666;
                border-radius: 8px;
                padding: 10px;
            } 
            QPushButton {
                background-color: #555555;
                color: #ffffff;
                border: 1px solid #777777;
                border-radius: 3px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #666666;
            }
            QLabel {
                color: #ffffff;
                font-size: 16px; /* 调整字体大小 */
                padding: 5px;
            }
            QComboBox {
                background-color: #555555;
                color: #ffffff;
                border: 1px solid #777777;
                border-radius: 3px;
                padding: 5px;
                radius: 15px;
            }
            QComboBox::drop-down {
                border: 0px; /* 去掉下拉箭头边框 */
            }
            QComboBox::down-arrow {
                image: url(icons/arrow_down.png); /* 设置下拉箭头图标 */
                width: 15px;
                height: 15px;
            }
            QComboBox::on { /* 当QComboBox被按下时 */
                padding-top: 3px;
                padding-left: 4px;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #777777;
                selection-background-color: #666666;
                color: #ffffff;
                background-color: #555555;
                radius: 15px;
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20) # 设置边距

        # 标签
        self.label = QLabel("背景图选择")
        self.label.setAlignment(Qt.AlignCenter) # 居中对齐
        self.label.setFont(QFont("幼圆", 14))
        layout.addWidget(self.label)

        # 下拉选择框
        self.combo_box = QComboBox()
        self.combo_box.setFont(QFont("幼圆", 12))
        self.combo_box.addItems(bg_ls) # 添加示例选项
        layout.addWidget(self.combo_box)

        button_layout = QHBoxLayout()
        clear_button = QPushButton('取消')
        clear_button.setFont(QFont("黑体"))
        clear_button.clicked.connect(self.reject)
        clear_button.setFixedSize(50, 50)

        close_button = QPushButton('确认')
        close_button.setFont(QFont("黑体"))
        close_button.clicked.connect(self.accept)
        close_button.setFixedSize(50, 50)

        button_layout.addWidget(clear_button)
        button_layout.addWidget(close_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def get_selected_background(self):
        return [self.combo_box.currentText()]