from PyQt5.QtWidgets import QPushButton
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize, pyqtSignal, Qt


def custom_buttom_with_img(img_path, w, h):
    button = QPushButton()
    button.setIcon(QIcon(img_path))  # 替换为你的发送图标路径
    button.setIconSize(QSize(w, h))  # 根据按钮大小自动调整图标大小
    button.setFixedSize(w, h)
    return button