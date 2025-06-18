import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QSlider, QDoubleSpinBox, QPushButton, QDialog,
    QScrollArea
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

# 假设的 Live2D 模型参数数据
# 注意：PyQt QSlider 默认处理整数，如果你的参数值是浮点数，
# 需要对滑动条的值进行缩放，或者使用 QSlider 和 QDoubleSpinBox 结合的方式。
# 这里我假设 QSlider 的值是整数，然后按比例转换。
# 另一个方案是自定义 Slider，或者直接用 QDoubleSpinBox 作为主要输入。
# 为了简化，我将QSlider的步长设置为0.01，并进行100倍的缩放。


# 用于 QSlider 的缩放因子，因为 QSlider 默认处理整数。
# 如果你的参数范围很广或者需要很高的精度，可能需要调整这个因子。
SLIDER_SCALE = 1000

class Live2DParamModifier(QDialog):
    def __init__(self, params_data, model):
        super().__init__()
        self.setWindowTitle("Live2D 参数修改器")
        self.setGeometry(100, 100, 800, 600) # x, y, width, height

        self.main_layout = QVBoxLayout(self)
        self.model = model

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
                QScrollArea { /* 为 QScrollArea 添加样式 */
                    background-color: #2e2e2e; /* 设置为与 QDialog 相同的背景色 */
                    border: none; /* 如果不想要边框，可以设置为none */
                }
                QScrollArea QWidget { /* QScrollArea 内部的 widget 也要设置背景色 */
                    background-color: #2e2e2e; /* 确保滚动区域内的内容背景色也一致 */
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

        # 创建一个可滚动的区域，以防参数过多
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content_widget)
        self.scroll_area.setWidget(self.scroll_content_widget)
        self.main_layout.addWidget(self.scroll_area)

        self.button_layout = QHBoxLayout()
        clear_button = QPushButton('取消')
        clear_button.setFont(QFont("黑体"))
        clear_button.clicked.connect(self.reject)
        clear_button.setFixedSize(50, 50)

        close_button = QPushButton('确认')
        close_button.setFont(QFont("黑体"))
        close_button.clicked.connect(self.accept)
        close_button.setFixedSize(50, 50)

        self.button_layout.addWidget(clear_button)
        self.button_layout.addWidget(close_button)

        self.params_data = params_data
        self.param_widgets = {} # 用于存储每个参数的UI控件和当前值

        self.init_ui()

        self.main_layout.addLayout(self.button_layout)

    def init_ui(self):
        for param_info in self.params_data:
            param_id = param_info["id"]
            min_val = param_info["min"]
            max_val = param_info["max"]
            default_val = param_info["default"]
            initial_val = param_info["value"] # 使用初始值

            # 每个参数一行
            param_row_layout = QHBoxLayout()

            # 参数 ID
            param_id_label = QLabel(f"{param_id}:")
            param_id_label.setFixedWidth(300)
            param_row_layout.addWidget(param_id_label)

            # 当前值显示
            current_value_label = QLabel(f"{initial_val:.3f}")
            current_value_label.setFixedWidth(80)
            param_row_layout.addWidget(current_value_label)

            # 滑动条
            # 将浮点数范围映射到整数滑动条范围
            slider = QSlider(Qt.Horizontal)
            slider.setMinimum(int(min_val * SLIDER_SCALE))
            slider.setMaximum(int(max_val * SLIDER_SCALE))
            slider.setValue(int(initial_val * SLIDER_SCALE))
            slider.setSingleStep(int(0.01 * SLIDER_SCALE)) # 设置步长，例如 0.01

            # 连接滑动条的 valueChanged 信号
            slider.valueChanged.connect(
                lambda val, p_id=param_id, c_val_label=current_value_label:
                self.on_slider_value_changed(val, p_id, c_val_label)
            )
            param_row_layout.addWidget(slider)

            # 权重输入框
            weight_spinbox = QDoubleSpinBox()
            weight_spinbox.setMinimum(0.0)
            weight_spinbox.setMaximum(1.0)
            weight_spinbox.setSingleStep(0.1)
            weight_spinbox.setValue(1.0) # 默认权重为 1.0，滑动后立即生效
            weight_spinbox.setToolTip("权重 (0.0 - 1.0): 默认为 1.0，即完全应用")

            # 连接权重输入框的 valueChanged 信号
            weight_spinbox.valueChanged.connect(
                lambda val, p_id=param_id: self.update_param_value(p_id)
            )
            param_row_layout.addWidget(weight_spinbox)

            # 重置按钮
            reset_button = QPushButton("重置")
            reset_button.clicked.connect(
                lambda _, p_id=param_id, sld=slider, w_sb=weight_spinbox, c_val_label=current_value_label:
                self.reset_param(p_id, default_val, sld, w_sb, c_val_label)
            )
            param_row_layout.addWidget(reset_button)

            self.scroll_layout.addLayout(param_row_layout)

            # 存储控件引用和当前值，以便后续操作
            self.param_widgets[param_id] = {
                "slider": slider,
                "weight_spinbox": weight_spinbox,
                "current_value_label": current_value_label,
                "default_value": default_val,
                "current_value": initial_val # 追踪每个参数的当前值
            }

        # 添加一个底部的 spacer，将内容推到顶部
        self.scroll_layout.addStretch(1)

    def on_slider_value_changed(self, scaled_value, param_id, current_value_label):
        """处理滑动条值改变事件"""
        real_value = scaled_value / SLIDER_SCALE
        self.param_widgets[param_id]["current_value"] = real_value
        current_value_label.setText(f"{real_value:.3f}")
        self.update_param_value(param_id)

    def update_param_value(self, param_id):
        """
        根据滑动条和权重框的值，模拟调用 Live2D API
        """
        param_info = self.param_widgets[param_id]
        current_value = param_info["current_value"]
        weight = param_info["weight_spinbox"].value()

        # 模拟 Live2D SDK 调用
        # 实际应用中，这里会调用 Live2D SDK 的 model.SetParameterValue 方法
        self.model.model.SetParameterValue(param_id, current_value, weight)
        print(f'model.SetParameterValue("{param_id}", {current_value:.3f}, {weight:.1f})')

    def reset_param(self, param_id, default_val, slider, weight_spinbox, current_value_label):
        """重置参数到默认值"""
        slider.setValue(int(default_val * SLIDER_SCALE))
        weight_spinbox.setValue(1.0) # 重置时通常希望立即应用
        self.param_widgets[param_id]["current_value"] = default_val
        current_value_label.setText(f"{default_val:.3f}")
        self.update_param_value(param_id) # 立即应用重置


# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     window = Live2DParamModifier()
#     window.show()
#     sys.exit(app.exec_())