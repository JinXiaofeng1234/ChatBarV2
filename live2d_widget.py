import pygame
from PyQt5.QtWidgets import QOpenGLWidget
from PyQt5.QtCore import QTimer, Qt
from OpenGL.GL import *
import live2d.v3 as live2d
from live2d.v3 import StandardParams, MotionPriority, Parameter
from live2d.utils.lipsync import WavHandler
from live2d.utils import log
import math
import random

# 假设 Live2DModel 和 Live2DRenderer 类的定义在 live2d_wrapper.py 中
# 您需要将它们复制到这里或确保它们可以被导入
# 为了示例的简洁性，我将 Live2DModel 的大部分内容直接复制到这里
# 但在实际项目中，您应该组织好您的代码结构。

class Live2DModel:
    """封装 Live2D 模型的加载、渲染和交互逻辑。"""

    def __init__(self, model_path: str, canvas_width: int = 1000,
                 canvas_height: int = 800, audio_path: str='tmp_audio/8146dcb8-37ae-11f0-bd82-d843aec491a3.mp3'):
        """
        初始化 Live2D 模型。

        Args:
            model_path: Live2D 模型文件的路径（.model3.json）。
            canvas_width: 画布宽度。
            canvas_height: 画布高度。
        """
        self.model = live2d.LAppModel()
        self.model.LoadModelJson(model_path)
        self.model.Resize(canvas_width, canvas_height)
        self.model.SetAutoBlinkEnable(True)
        self.model.SetAutoBreathEnable(True)
        self.model.StartRandomMotion()

        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        self.dx = 0.0
        self.dy = 0.0
        self.scale = 1.0
        self.wav_handler = WavHandler()
        self.lip_sync_n = 3
        self.audio_played = False
        self.wheel_delta = 0
        self.audio_path = audio_path

        self.motion_done_flag = True

        # 获取全部可用参数
        self.param_dic = []
        for i in range(self.model.GetParameterCount()):
            param: Parameter = self.model.GetParameter(i)
            # print(param.id, param.type, param.value, param.max, param.min, param.default)
            self.param_dic.append({"id": param.id, "value": param.value,
                                   "max": param.max, "min": param.min, "default": param.default})

        # 用于 Pygame 音频的初始化，在 PyQt 中可能需要调整
        # pygame.mixer.init()

    def start_callback(self, group, no):
        audio_path = self.audio_path  # 确保这个音频文件存在
        log.Info("start motion: [%s_%d]" % (group, no))
        # 在 PyQt 中，不直接使用 pygame.mixer.music，可以考虑 QSoundEffect 或 QMediaPlayer
        try:
            pygame.mixer.music.load(audio_path)
            pygame.mixer.music.play()
        except Exception as e:
            print(f'生成的音频文件无法正常读取,请检查{e}')
        log.Info("start lipSync")
        self.wav_handler.Start(audio_path)


    def on_finish_motion_callback(self):
        self.motion_done_flag = True
        log.Info("motion finished")

    def update(self, delta_time: float):
        """更新模型状态（如旋转、位置、缩放等）。"""
        progress = delta_time * math.pi * 10 / 1000 * 0.5
        deg = math.sin(progress) * 5  # 最大旋转角度为5度
        self.model.Rotate(deg)
        self.model.Update()

    def update_setoff(self):
        self.set_offset(self.dx, self.dy)
        self.set_scale(self.scale)
        live2d.clearBuffer()

    def draw(self):
        """绘制模型到当前 OpenGL 上下文。"""
        self.model.Draw()

    def handle_mouse_press(self, x=0, y=0):
        self.motion_done_flag = False
        self.model.SetRandomExpression()
        self.model.StartRandomMotion(priority=3, onFinishMotionHandler=self.on_finish_motion_callback)

    def handle_key_press(self, key):
        if key == Qt.Key_Left:
            self.dx -= 0.1
        elif key == Qt.Key_Right:
            self.dx += 0.1
        elif key == Qt.Key_Up:
            self.dy += 0.1
        elif key == Qt.Key_Down:
            self.dy -= 0.1
        elif key == Qt.Key_I:
            self.scale += 0.1
        elif key == Qt.Key_U:
            self.scale -= 0.1
        elif key == Qt.Key_R:
            self.model.StopAllMotions()
            self.model.ResetPose()
        elif key == Qt.Key_E:
            self.model.ResetExpression()

    def handle_mouse_move(self, x, y):
        self.model.Drag(x, y)

    def handle_mouse_wheel(self, delta):
        # 假设 delta 是鼠标滚轮的步长
        self.scale += delta * 0.1

    def set_offset(self, dx: float, dy: float):
        """设置模型偏移量。"""
        self.dx = dx
        self.dy = dy
        self.model.SetOffset(dx, dy)

    def set_scale(self, scale: float):
        """设置模型缩放比例。"""
        self.scale = scale
        self.model.SetScale(scale)

# 动作开始播放前调用该函数
def onStartCallback(group: str, no: int):
    print(f"touched and motion [{group}_{no}] is started")

# 动作播放结束后会调用该函数
def onFinishCallback():
    print("motion finished")

class Live2DOpenGLWidget(QOpenGLWidget):
    def __init__(self, parent=None, live2d_model_path=None, audio_path=None, bg_path=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus()  # 尝试在窗口显示后立即设置焦点
        self.live2d_model_path = live2d_model_path
        self.audio_path = audio_path
        self.init_bg_path = bg_path
        self.live2d_model = None
        self.background_texture_id = 0
        self.last_time = 0
        self.background_vertices = (
            (-1.0, 1.0, 0),  # 左上
            (1.0, 1.0, 0),   # 右上
            (1.0, -1.0, 0),  # 右下
            (-1.0, -1.0, 0)  # 左下
        )

        # QTimer 用于定期更新渲染
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_live2d)
        self.timer.start(16) # 大约 60 FPS

        self.performance_manager = QTimer(self)
        self.performance_manager.timeout.connect(self.performance_state_machine)
        self.performance_manager.start(500)

        self.model_drag_manager = QTimer(self)
        self.model_drag_manager.timeout.connect(self.model_drag)
        self.model_drag_manager.start(5000)

    def initializeGL(self):
        live2d.init()
        live2d.setLogEnable(True)
        if live2d.LIVE2D_VERSION == 3:
            print('Live2D V3 模式')
            live2d.glInit()

        # 初始化 Live2D 模型
        # 确保 Resources/BRAIN/BRAIN.model3.json 路径正确
        self.live2d_model = Live2DModel(self.live2d_model_path, self.width(), self.height(), self.audio_path)

        self._load_bg(img_path = self.init_bg_path)

        self.last_time = self.last_time if self.last_time else pygame.time.get_ticks() # 获取当前时间

    def _load_bg(self, img_path):
        # 加载背景图片
        try:
            # Pygame 的图片加载和 OpenGL 纹理转换
            pygame.init()  # 初始化 Pygame 用于图片加载
            pygame.display.set_mode((1, 1), pygame.HIDDEN | pygame.NOFRAME)
            img_alpha = pygame.image.load(img_path).convert_alpha()
            self.background_texture_id = self._render_texture(img_alpha)
            pygame.display.quit()  # 在加载完图片后可以退出 Pygame
        except Exception as e:
            print(f"Error loading background image: {e}")
            self.background_texture_id = 0  # 设置为 0 表示没有背景纹理

    def performance_state_machine(self):
        if self.live2d_model.motion_done_flag:
            self.live2d_model.handle_mouse_press()
        self.update()  # 立即更新显示

    def model_drag(self):
        if not self.live2d_model.wav_handler.Update():
            x = random.randint(0, 1200)
            y = random.randint(0, 1000)
            interval = random.randint(500, 10000)
            self.live2d_model.handle_mouse_move(x, y)
            self.update()
            self.model_drag_manager.setInterval(interval)

    def resizeGL(self, width, height):
        glViewport(0, 0, width, height)
        if self.live2d_model:
            self.live2d_model.model.Resize(width, height)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # 绘制背景
        if self.background_texture_id:
            self._draw_texture(self.background_texture_id, *self.background_vertices)

        # 绘制 Live2D 模型
        if self.live2d_model:
            self.live2d_model.draw()

    def update_live2d(self):
        if not self.live2d_model:
            return

        current_time = pygame.time.get_ticks()
        delta_time = (current_time - self.last_time) / 1000.0  # 转换为秒
        self.last_time = current_time

        # if not self.live2d_model.wav_handler.Update():
        if not type(delta_time) == list:
            self.live2d_model.update(delta_time)

        if self.live2d_model.wav_handler.Update():
            self.live2d_model.model.SetParameterValue(
                StandardParams.ParamMouthOpenY, self.live2d_model.wav_handler.GetRms() * self.live2d_model.lip_sync_n
            )

        if not self.live2d_model.audio_played:
            self.live2d_model.model.StartMotion(
                "",
                0,
                live2d.MotionPriority.FORCE,
                self.live2d_model.start_callback,
                self.live2d_model.on_finish_motion_callback,
            )
            self.live2d_model.audio_played = True

        self.live2d_model.update_setoff()

        # 触发重新绘制
        self.update()

    def mousePressEvent(self, event):
        if self.live2d_model and event.button() == Qt.LeftButton:
            if self.live2d_model.motion_done_flag:
                self.live2d_model.handle_mouse_press(event.x(), event.y())
                self.update() # 立即更新显示

    def mouseMoveEvent(self, event):
        if self.live2d_model and event.buttons() & Qt.LeftButton: # 只有左键按下时拖动
            # print(event.x(), event.y())
            self.live2d_model.handle_mouse_move(event.x(), event.y())
            self.update()

    def wheelEvent(self, event):
        if self.live2d_model:
            self.live2d_model.handle_mouse_wheel(event.angleDelta().y() / 120) # 滚轮步长通常是 120
            self.update()

    def keyPressEvent(self, event):
        if self.live2d_model:
            self.live2d_model.handle_key_press(event.key())
            self.update()

    def _render_texture(self, surface: pygame.Surface) -> int:
        """将 Pygame Surface 转换为 OpenGL 纹理并返回纹理 ID。"""
        texture_data = pygame.image.tobytes(surface, "RGBA", True)
        texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glTexImage2D(
            GL_TEXTURE_2D,
            0,
            GL_RGBA,
            surface.get_width(),
            surface.get_height(),
            0,
            GL_RGBA,
            GL_UNSIGNED_BYTE,
            texture_data
        )
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR) # 添加这行以确保放大时平滑
        return texture_id

    def _draw_texture(self, texture_id: int, *args: tuple) -> None:
        """绘制 OpenGL 纹理。"""
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0)
        glVertex3f(*args[3]) # 左下角顶点
        glTexCoord2f(1, 0)
        glVertex3f(*args[2]) # 右下角顶点
        glTexCoord2f(1, 1)
        glVertex3f(*args[1]) # 右上角顶点
        glTexCoord2f(0, 1)
        glVertex3f(*args[0]) # 左上角顶点
        glEnd()
        glDisable(GL_TEXTURE_2D) # 绘制完成后禁用纹理

