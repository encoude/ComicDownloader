import sys
import os
import re
import logging
import jmcomic
import datetime
import configparser
import random
import math
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QPushButton, QTextEdit, 
                               QLabel, QFrame, QMessageBox, QFileDialog)
from PySide6.QtGui import (QPixmap, QPalette, QBrush, QFont, QIcon, 
                           QPainter, QColor, QRadialGradient, QLinearGradient ,QPen)
from PySide6.QtCore import Qt, Signal, QThread, QSize, QObject, QTimer, QPointF

# 设置中文字体支持
font = QFont()
font.setFamily("SimHei")

# 资源路径
BACKGROUND_IMAGE_PATH = "pink Gril.png"  # 背景图片路径
APP_ICON_PATH = "black.ico"    # 应用图标路径
LOG_DIR = "logs"  # 日志目录
CONFIG_FILE = "config.ini"  # 配置文件路径

# 默认下载目录（根据操作系统不同设置）
if sys.platform == 'win32':
    DEFAULT_DOWNLOAD_DIR = os.path.join(os.environ['USERPROFILE'], 'Downloads', 'JMComic')
elif sys.platform == 'darwin':
    DEFAULT_DOWNLOAD_DIR = os.path.join(os.path.expanduser('~'), 'Downloads', 'JMComic')
else:  # Linux/Android
    DEFAULT_DOWNLOAD_DIR = os.path.join(os.path.expanduser('~'), 'JMComic')

class OutputRedirector(QObject):
    """重定向标准输出到信号"""
    output_signal = Signal(str)

    def write(self, text):
        self.output_signal.emit(text)
    
    def flush(self):
        pass

class DownloadThread(QThread):
    """下载线程"""
    update_signal = Signal(str)  # 用于更新UI的信号
    finished_signal = Signal(bool, str)  # 完成信号：是否成功，消息
    result_signal = Signal(dict)  # 下载结果信号
    
    def __init__(self, album_ids, download_dir, logger):
        super().__init__()
        self.album_ids = album_ids
        self.download_dir = download_dir  # 存储下载目录
        self.logger = logger
        self.results = {}  # 存储每个ID的下载结果
        
        # 创建输出重定向器
        self.output_redirector = OutputRedirector()
        self.output_redirector.output_signal.connect(self.handle_output)
    
    def handle_output(self, text):
        """处理重定向的输出"""
        if text.strip():  # 忽略空行
            self.update_signal.emit(text.strip())
    
    def run(self):
        try:
            # 重定向标准输出
            sys.stdout = self.output_redirector
            sys.stderr = self.output_redirector
            
            # 确保下载目录存在
            os.makedirs(self.download_dir, exist_ok=True)
            
            # 遍历所有专辑ID
            self.update_signal.emit(f"开始批量下载 {len(self.album_ids)} 个专辑...")
            self.logger.info(f"用户输入专辑ID: {self.album_ids}")
            self.logger.info(f"下载目录设置为: {self.download_dir}")
            
            # 创建jmcomic选项 - 使用JmOption设置下载目录
            from jmcomic import JmOption
            jm_option = JmOption.default()
            # 设置下载目录到dir_rule.base_dir
            jm_option.dir_rule.base_dir = self.download_dir
            
            for index, album_id in enumerate(self.album_ids, 1):
                current_album_id = album_id  # 保存当前album_id到局部变量
                self.update_signal.emit(f"\n===== 开始下载第{index}个专辑，ID：{current_album_id} =====")
                self.logger.info(f"开始下载专辑ID: {current_album_id}")
                
                # 记录开始时间
                start_time = datetime.datetime.now()
                
                try:
                    # 下载当前专辑
                    jm_option.download_album(current_album_id)
                    success = True
                    message = f"✅ 第{index}个专辑下载完成，ID：{current_album_id}\n保存位置: {self.download_dir}"
                    self.logger.info(f"专辑ID {current_album_id} 下载成功")
                except Exception as e:
                    success = False
                    message = f"❌ 专辑ID {current_album_id} 下载失败: {str(e)}"
                    self.logger.error(f"专辑ID {current_album_id} 下载失败: {str(e)}", exc_info=True)
                
                # 记录结束时间和耗时
                end_time = datetime.datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                # 更新结果
                if current_album_id not in self.results:
                    self.results[current_album_id] = {"success": 0, "failure": 0}
                
                if success:
                    self.results[current_album_id]["success"] += 1
                else:
                    self.results[current_album_id]["failure"] += 1
                
                # 发送更新
                self.update_signal.emit(message)
                self.logger.info(f"专辑ID {current_album_id} 下载耗时: {duration:.2f}秒")
            
            # 发送最终结果
            self.result_signal.emit(self.results)
            self.finished_signal.emit(True, "所有专辑下载完成！")
            self.logger.info("所有专辑下载完成")
        except Exception as e:
            self.update_signal.emit(f"❌ 下载出错：{str(e)}")
            self.finished_signal.emit(False, f"下载出错：{str(e)}")
            self.logger.critical(f"下载线程崩溃: {str(e)}", exc_info=True)
        finally:
            # 恢复标准输出
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__

class AnimatedBackground(QWidget):
    """带有动态背景效果的小部件"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)  # 启用鼠标跟踪
        self.mouse_pos = QPointF(0, 0)
        
        # 创建粒子系统
        self.particles = []
        self.lines = []
        self.circles = []
        
        # 初始化粒子
        self.init_particles()
        
        # 设置定时器更新动画
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(30)  # 约30FPS
        
        # 背景图片
        self.background_pixmap = None
        if os.path.exists(BACKGROUND_IMAGE_PATH):
            self.background_pixmap = QPixmap(BACKGROUND_IMAGE_PATH)
        
        # 交互半径
        self.interaction_radius = 150
    
    def init_particles(self):
        """初始化粒子系统"""
        # 创建粒子
        for _ in range(50):
            x = random.randint(0, self.width())
            y = random.randint(0, self.height())
            size = random.randint(2, 6)
            speed_x = random.uniform(-0.5, 0.5)
            speed_y = random.uniform(-0.5, 0.5)
            color = QColor(
                random.randint(150, 255),
                random.randint(150, 255),
                random.randint(150, 255),
                100 + random.randint(0, 155)
            )
            self.particles.append({
                'pos': QPointF(x, y),
                'size': size,
                'speed': QPointF(speed_x, speed_y),
                'color': color
            })
        
        # 创建线条
        for _ in range(20):
            x1 = random.randint(0, self.width())
            y1 = random.randint(0, self.height())
            x2 = x1 + random.randint(-100, 100)
            y2 = y1 + random.randint(-100, 100)
            speed_x = random.uniform(-0.8, 0.8)
            speed_y = random.uniform(-0.8, 0.8)
            width = random.uniform(0.5, 2.0)
            color = QColor(
                random.randint(180, 255),
                random.randint(180, 255),
                random.randint(180, 255),
                80 + random.randint(0, 80)
            )
            self.lines.append({
                'start': QPointF(x1, y1),
                'end': QPointF(x2, y2),
                'speed': QPointF(speed_x, speed_y),
                'width': width,
                'color': color
            })
        
        # 创建圆形
        for _ in range(15):
            x = random.randint(0, self.width())
            y = random.randint(0, self.height())
            radius = random.randint(10, 50)
            speed_x = random.uniform(-0.5, 0.5)
            speed_y = random.uniform(-0.5, 0.5)
            color = QColor(
                random.randint(100, 200),
                random.randint(100, 200),
                random.randint(100, 200),
                30 + random.randint(0, 50)
            )
            self.circles.append({
                'center': QPointF(x, y),
                'radius': radius,
                'speed': QPointF(speed_x, speed_y),
                'color': color
            })
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        self.mouse_pos = event.position()
        self.update()
    
    def update_animation(self):
        """更新动画状态"""
        # 更新粒子位置
        for particle in self.particles:
            particle['pos'] += particle['speed']
            
            # 边界检查
            if particle['pos'].x() < 0 or particle['pos'].x() > self.width():
                particle['speed'].setX(-particle['speed'].x())
            if particle['pos'].y() < 0 or particle['pos'].y() > self.height():
                particle['speed'].setY(-particle['speed'].y())
            
            # 鼠标交互
            dist = math.sqrt((particle['pos'].x() - self.mouse_pos.x())**2 + 
                            (particle['pos'].y() - self.mouse_pos.y())**2)
            if dist < self.interaction_radius:
                # 排斥粒子
                dx = particle['pos'].x() - self.mouse_pos.x()
                dy = particle['pos'].y() - self.mouse_pos.y()
                force = (self.interaction_radius - dist) / self.interaction_radius * 2.0
                particle['speed'] += QPointF(dx * force * 0.02, dy * force * 0.02)
        
        # 更新线条位置
        for line in self.lines:
            line['start'] += line['speed']
            line['end'] += line['speed']
            
            # 边界检查
            if (line['start'].x() < 0 or line['start'].x() > self.width() or
                line['end'].x() < 0 or line['end'].x() > self.width()):
                line['speed'].setX(-line['speed'].x())
            if (line['start'].y() < 0 or line['start'].y() > self.height() or
                line['end'].y() < 0 or line['end'].y() > self.height()):
                line['speed'].setY(-line['speed'].y())
        
        # 更新圆形位置
        for circle in self.circles:
            circle['center'] += circle['speed']
            
            # 边界检查
            if (circle['center'].x() < circle['radius'] or 
                circle['center'].x() > self.width() - circle['radius']):
                circle['speed'].setX(-circle['speed'].x())
            if (circle['center'].y() < circle['radius'] or 
                circle['center'].y() > self.height() - circle['radius']):
                circle['speed'].setY(-circle['speed'].y())
            
            # 鼠标交互 - 圆形会轻微跟随鼠标
            dist = math.sqrt((circle['center'].x() - self.mouse_pos.x())**2 + 
                            (circle['center'].y() - self.mouse_pos.y())**2)
            if dist < self.interaction_radius * 1.5:
                dx = self.mouse_pos.x() - circle['center'].x()
                dy = self.mouse_pos.y() - circle['center'].y()
                force = (self.interaction_radius * 1.5 - dist) / (self.interaction_radius * 1.5) * 0.5
                circle['speed'] += QPointF(dx * force * 0.01, dy * force * 0.01)
        
        self.update()
    
    def paintEvent(self, event):
        """绘制背景和动态元素"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制背景图片
        if self.background_pixmap and not self.background_pixmap.isNull():
            scaled_pixmap = self.background_pixmap.scaled(
                self.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation
            )
            painter.drawPixmap(0, 0, scaled_pixmap)
        else:
            # 如果没有背景图片，使用渐变背景
            gradient = QLinearGradient(0, 0, self.width(), self.height())
            gradient.setColorAt(0, QColor(25, 25, 50))
            gradient.setColorAt(1, QColor(10, 10, 30))
            painter.fillRect(self.rect(), gradient)
        
        # 绘制动态元素（半透明覆盖层）
        overlay = QColor(0, 0, 0, 60)
        painter.fillRect(self.rect(), overlay)
        
        # 绘制粒子
        for particle in self.particles:
            painter.setPen(Qt.NoPen)
            painter.setBrush(particle['color'])
            painter.drawEllipse(particle['pos'], particle['size'], particle['size'])
        
        # 绘制线条
        for line in self.lines:
            painter.setPen(QPen(line['color'], line['width']))
            painter.drawLine(line['start'], line['end'])
        
        # 绘制圆形
        for circle in self.circles:
            painter.setPen(QPen(circle['color'], 1))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(circle['center'], circle['radius'], circle['radius'])
        
        # 绘制鼠标交互效果
        if not self.mouse_pos.isNull():
            # 鼠标周围的发光效果
            radial_gradient = QRadialGradient(
                self.mouse_pos, 
                self.interaction_radius
            )
            radial_gradient.setColorAt(0, QColor(255, 255, 255, 30))
            radial_gradient.setColorAt(1, QColor(255, 255, 255, 0))
            
            painter.setPen(Qt.NoPen)
            painter.setBrush(radial_gradient)
            painter.drawEllipse(self.mouse_pos, self.interaction_radius, self.interaction_radius)
            
            # 鼠标位置的小圆点
            painter.setBrush(QColor(255, 255, 255, 180))
            painter.drawEllipse(self.mouse_pos, 3, 3)

class JmcomicDownloader(QMainWindow):
    def __init__(self):
        super().__init__()
        self.download_dir = DEFAULT_DOWNLOAD_DIR  # 默认下载目录
        self.logger = self.setup_logger()
        self.crash_count = 0
        self.warning_shown = False  # 添加警告显示状态标记
        
        # 加载配置文件
        self.load_config()
        
        self.init_ui()
    
    def load_config(self):
        """从配置文件加载设置"""
        self.config = configparser.ConfigParser()
        
        # 如果配置文件存在，读取设置
        if os.path.exists(CONFIG_FILE):
            try:
                self.config.read(CONFIG_FILE, encoding='utf-8')
                if 'Settings' in self.config:
                    if 'download_dir' in self.config['Settings']:
                        self.download_dir = self.config['Settings']['download_dir']
                        self.logger.info(f"从配置文件加载下载目录: {self.download_dir}")
                    # 添加警告显示状态读取
                    if 'warning_shown' in self.config['Settings']:
                        self.warning_shown = self.config['Settings'].getboolean('warning_shown')
                        self.logger.info(f"警告显示状态: {'已显示' if self.warning_shown else '未显示'}")
            except Exception as e:
                self.logger.error(f"读取配置文件失败: {str(e)}", exc_info=True)
                # 创建默认配置文件
                self.create_default_config()
        else:
            # 创建默认配置文件
            self.create_default_config()
    
    def create_default_config(self):
        """创建默认配置文件"""
        try:
            self.config['Settings'] = {
                'download_dir': self.download_dir,
                'version': '1.3',
                'warning_shown': 'False'  # 添加默认值
            }
            with open(CONFIG_FILE, 'w', encoding='utf-8') as configfile:
                self.config.write(configfile)
            self.logger.info(f"创建默认配置文件: {CONFIG_FILE}")
        except Exception as e:
            self.logger.error(f"创建配置文件失败: {str(e)}", exc_info=True)
    
    def save_config(self):
        """保存配置到文件"""
        try:
            self.config['Settings'] = {
                'download_dir': self.download_dir,
                'version': '1.3',
                'warning_shown': str(self.warning_shown)  # 保存警告显示状态
            }
            with open(CONFIG_FILE, 'w', encoding='utf-8') as configfile:
                self.config.write(configfile)
            self.logger.info(f"保存配置到文件: {CONFIG_FILE}")
        except Exception as e:
            self.logger.error(f"保存配置文件失败: {str(e)}", exc_info=True)
    
    def setup_logger(self):
        """设置日志记录器，按天生成日志文件"""
        # 创建日志目录
        os.makedirs(LOG_DIR, exist_ok=True)
        
        # 创建按天的日志文件名
        date_str = datetime.datetime.now().strftime("%Y%m%d")
        log_filename = os.path.join(LOG_DIR, f"jmcomic_downloader_{date_str}.log")
        
        # 检查日志文件是否已存在
        log_exists = os.path.exists(log_filename)
        
        # 配置日志
        logger = logging.getLogger("JmComicDownloader")
        logger.setLevel(logging.INFO)
        
        # 文件处理器
        file_handler = logging.FileHandler(log_filename, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        
        # 日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        # 如果是新启动的会话，添加分隔符
        if not log_exists:
            logger.info("=" * 70)
            logger.info(f"JMComic下载器启动 - 首次创建日志文件")
            logger.info(f"日志文件: {log_filename}")
            logger.info(f"默认下载目录: {self.download_dir}")
            logger.info("=" * 70)
        else:
            # 添加会话分隔符
            logger.info("\n" + "=" * 70)
            logger.info(f"新的会话启动于 {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("=" * 70)
        
        return logger
    
    def center_window(self):
        """将窗口居中显示在屏幕上"""
        # 获取屏幕几何信息
        screen_geometry = QApplication.primaryScreen().geometry()
        # 获取窗口几何信息
        window_geometry = self.geometry()
        
        # 计算居中位置
        x = (screen_geometry.width() - window_geometry.width()) // 2
        y = (screen_geometry.height() - window_geometry.height()) // 2
        
        # 移动窗口到居中位置
        self.move(x, y)

    def init_ui(self):
        # 设置窗口标题和大小
        self.setWindowTitle("JM漫画下载器  -  V1.3")
        self.setGeometry(100, 100, 800, 650)  # 增加窗口高度
        self.setMinimumSize(QSize(700, 550))  # 增加最小高度
        
        # 创建主部件 - 使用动态背景
        self.background_widget = AnimatedBackground()
        self.setCentralWidget(self.background_widget)
        
        # 创建内容部件（透明，覆盖在背景上）
        content_widget = QWidget()
        content_widget.setStyleSheet("background-color: transparent;")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(15)
        
        # 创建顶部水平布局（包含标题和帮助按钮）
        top_layout = QHBoxLayout()
        
        # 创建标题容器（用于居中显示标题）
        title_container = QWidget()
        title_container.setStyleSheet("background-color: rgba(0, 0, 0, 0.01); border-radius: 8px;")
        title_container_layout = QHBoxLayout(title_container)
        title_container_layout.setContentsMargins(0, 0, 0, 0)
        
        # 添加左侧弹簧
        title_container_layout.addStretch(1)
        
        # 添加标题（居中）
        title_label = QLabel("JM漫画批量下载器")
        title_label.setFont(QFont("SimHei", 24, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)  # 文本居中
        title_label.setStyleSheet("color: #ffffff; padding: 10px;")
        title_container_layout.addWidget(title_label)
        
        # 添加右侧弹簧
        title_container_layout.addStretch(1)
        
        # 将标题容器添加到顶部布局
        top_layout.addWidget(title_container)
        
        # 添加帮助按钮（右上角）
        self.help_btn = QPushButton("帮助")
        self.help_btn.setFont(QFont("SimHei", 10))
        self.help_btn.setMinimumSize(70, 40)
        self.help_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(155, 89, 182, 0.85);
                color: white;
                padding: 5px 10px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(142, 68, 173, 0.9);
            }
        """)
        self.help_btn.clicked.connect(self.show_help)
        top_layout.addWidget(self.help_btn)
        
        content_layout.addLayout(top_layout)
        
        # 添加分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: rgba(255, 255, 255, 0.3);")
        content_layout.addWidget(separator)
        
        # 添加下载目录设置区域
        dir_frame = QFrame()
        dir_frame.setStyleSheet("""
            background-color: rgba(255, 255, 255, 0.6); 
            border-radius: 10px;
            border: 1px solid rgba(189, 195, 199, 0.5);
        """)
        dir_layout = QHBoxLayout(dir_frame)
        dir_layout.setContentsMargins(15, 10, 15, 10)
        
        # 下载目录标签
        dir_label = QLabel("下载目录：")
        dir_label.setFont(QFont("SimHei", 10))
        dir_label.setStyleSheet("color: #2c3e50;")
        dir_layout.addWidget(dir_label)
        
        # 当前目录显示
        self.dir_display = QLabel(self.download_dir)
        self.dir_display.setFont(QFont("Consolas", 9))
        self.dir_display.setStyleSheet("color: #34495e;")
        self.dir_display.setMinimumWidth(300)
        self.dir_display.setWordWrap(True)
        dir_layout.addWidget(self.dir_display, 1)  # 添加伸缩因子
        
        # 选择目录按钮
        self.dir_btn = QPushButton("选择目录")
        self.dir_btn.setFont(QFont("SimHei", 10))
        self.dir_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(155, 89, 182, 0.85);
                color: white;
                padding: 5px 10px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: rgba(142, 68, 173, 0.9);
            }
        """)
        self.dir_btn.clicked.connect(self.choose_download_dir)
        dir_layout.addWidget(self.dir_btn)
        
        content_layout.addWidget(dir_frame)
        
        # 添加输入区域
        input_frame = QFrame()
        input_frame.setStyleSheet("""
            background-color: rgba(255, 255, 255, 0.6); 
            border-radius: 10px;
            border: 1px solid rgba(189, 195, 199, 0.5);
        """)
        input_frame.setMinimumHeight(160)  # 增加最小高度
        input_layout = QVBoxLayout(input_frame)
        input_layout.setContentsMargins(15, 15, 15, 15)
        
        # 输入框标签
        input_label = QLabel("输入专辑ID（多个ID用逗号、空格或分号分隔）：")
        input_label.setFont(QFont("SimHei", 10))
        input_label.setStyleSheet("color: #2c3e50;")
        input_layout.addWidget(input_label)
        
        # 输入框 - 使用多行文本框以便输入多个ID
        self.album_input = QTextEdit()
        self.album_input.setFont(QFont("Consolas", 10))
        self.album_input.setPlaceholderText("例如：\n388109, 540931, 94505, 179941")
        self.album_input.setStyleSheet("""
            padding: 8px; 
            border: 1px solid rgba(149, 165, 166, 0.7); 
            border-radius: 5px;
            background-color: rgba(255, 255, 255, 0.7);
        """)
        # 增加输入框高度
        self.album_input.setMinimumHeight(120)  # 增加最小高度
        input_layout.addWidget(self.album_input)
        
        # 示例标签
        example_label = QLabel("388109(想要成为影之实力者),359388(电锯人)，94505(死亡影片) 这个是上面编号对应的漫画")
        example_label.setFont(QFont("SimHei", 8))
        example_label.setStyleSheet("color: #34495e;")
        input_layout.addWidget(example_label)
        
        content_layout.addWidget(input_frame)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        button_layout.setContentsMargins(0, 10, 0, 10)
        
        # 开始下载按钮
        self.download_btn = QPushButton("开始下载")
        self.download_btn.setFont(QFont("SimHei", 12))
        self.download_btn.setMinimumHeight(40)
        self.download_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(39, 174, 96, 0.85);
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(46, 204, 113, 0.9);
            }
            QPushButton:pressed {
                background-color: rgba(33, 150, 83, 0.9);
            }
            QPushButton:disabled {
                background-color: rgba(189, 195, 199, 0.7);
            }
        """)
        self.download_btn.clicked.connect(self.start_download)
        button_layout.addWidget(self.download_btn)
        
        # 清空按钮
        self.clear_btn = QPushButton("清空所有")
        self.clear_btn.setFont(QFont("SimHei", 12))
        self.clear_btn.setMinimumHeight(40)
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(231, 76, 60, 0.85);
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(192, 57, 43, 0.9);
            }
        """)
        self.clear_btn.clicked.connect(self.clear_all)
        button_layout.addWidget(self.clear_btn)
        
        # 查看日志按钮
        self.log_btn = QPushButton("查看日志")
        self.log_btn.setFont(QFont("SimHei", 12))
        self.log_btn.setMinimumHeight(40)
        self.log_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(52, 152, 219, 0.85);
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(41, 128, 185, 0.9);
            }
        """)
        self.log_btn.clicked.connect(self.view_logs)
        button_layout.addWidget(self.log_btn)
        
        content_layout.addLayout(button_layout)
        
        # 状态消息区域
        status_frame = QFrame()
        status_frame.setStyleSheet("""
            background-color: rgba(255, 255, 255, 0.6); 
            border-radius: 10px;
            border: 1px solid rgba(189, 195, 199, 0.5);
        """)
        status_layout = QVBoxLayout(status_frame)
        status_layout.setContentsMargins(15, 15, 15, 15)
        
        # 状态标签
        status_label = QLabel("下载状态：")
        status_label.setFont(QFont("SimHei", 10))
        status_label.setStyleSheet("color: #2c3e50;")
        status_layout.addWidget(status_label)
        
        # 状态消息框
        self.status_text = QTextEdit()
        self.status_text.setFont(QFont("Consolas", 9))
        self.status_text.setReadOnly(True)
        self.status_text.setStyleSheet("""
            padding: 8px; 
            border: 1px solid rgba(149, 165, 166, 0.7); 
            border-radius: 5px;
            background-color: rgba(255, 255, 255, 0.7);
        """)
        self.status_text.setPlaceholderText("下载状态将显示在这里...")
        status_layout.addWidget(self.status_text)
        
        content_layout.addWidget(status_frame)
        
        # 底部状态栏 - 修改显示内容
        self.status_bar = QLabel("就绪 | 输入专辑ID后点击开始下载 | v1.3 | 崩溃次数: 0")
        self.status_bar.setFont(QFont("SimHei", 8))
        self.status_bar.setStyleSheet("""
            color: rgba(255, 255, 255, 0.8); 
            background-color: rgba(0, 0, 0, 0.4);
            padding: 5px;
            border-radius: 3px;
        """)
        self.status_bar.setAlignment(Qt.AlignRight)
        content_layout.addWidget(self.status_bar)
        
        # 窗口居中显示（添加这段代码）
        self.center_window()

        # 将内容部件添加到背景部件
        self.background_widget.setLayout(QVBoxLayout())
        self.background_widget.layout().addWidget(content_widget)
        
        # 初始化下载线程
        self.download_thread = None
    
    def choose_download_dir(self):
        """选择下载目录"""
        # 打开目录选择对话框
        dir_path = QFileDialog.getExistingDirectory(
            self, 
            "选择下载目录", 
            self.download_dir,
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        
        if dir_path:
            self.download_dir = dir_path
            self.dir_display.setText(dir_path)
            self.logger.info(f"用户设置下载目录为: {dir_path}")
            self.status_text.append(f"✅ 下载目录已设置为: {dir_path}")
            
            # 保存配置
            self.save_config()
            
            # 创建消息框
            msg_box = QMessageBox()
            msg_box.setWindowTitle("目录已更新")
            msg_box.setText(f"下载目录已更新为:\n{dir_path}\n新设置将在下次下载时生效")
            msg_box.setIcon(QMessageBox.Information)
            
            # 设置确保文字可见的样式
            msg_box.setStyleSheet("""
                QMessageBox {
                    background-color: #f0f0f0;
                    font-family: Segoe UI;
                    font-size: 11pt;
                }
                QLabel {
                    color: #000000;
                    font-size: 10pt;
                }
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                    min-width: 80px;
                    font-size: 10pt;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
            """)
            
            # 添加确定按钮
            msg_box.addButton(QMessageBox.Ok)
            
            # 显示消息框
            msg_box.exec()
    
    def parse_album_ids(self, input_text):
        """解析输入的专辑ID，支持多种分隔符"""
        if not input_text.strip():
            return []
        
        # 使用正则表达式提取所有数字ID
        # 支持逗号、空格、分号、换行等多种分隔符
        album_ids = re.findall(r'\d+', input_text)
        return album_ids
    
    def start_download(self):
        """开始下载过程"""
        # 获取并解析输入的专辑ID
        input_text = self.album_input.toPlainText()
        album_ids = self.parse_album_ids(input_text)
        
        if not album_ids:
            QMessageBox.warning(self, "输入错误", "请输入有效的专辑ID")
            self.logger.warning("用户输入无效的专辑ID")
            return
        
        # 只在第一次启动时显示警告
        if not self.warning_shown:
            # 显示警告消息框
            warning_box = QMessageBox(self)
            warning_box.setIcon(QMessageBox.Warning)
            warning_box.setWindowTitle("重要提示")
            warning_box.setText("下载时请勿点击所下载的文件！")
            warning_box.setInformativeText("该行为可能导致下载失败或停止。\n请等待下载完成后再操作文件。")
            warning_box.setStandardButtons(QMessageBox.Ok)
            warning_box.button(QMessageBox.Ok).setText("我明白了")
            
            # 设置消息框样式 - 确保按钮文字可见
            warning_box.setStyleSheet("""
                QMessageBox {
                    background-color: #f8f9fa;
                    font-family: SimHei;
                    font-size: 10pt;
                }
                QLabel {
                    color: #d35400;
                    font-size: 12pt;
                    font-weight: bold;
                }
                QLabel#qt_msgbox_informativelabel {
                    color: #7f8c8d;
                    font-size: 10pt;
                    font-weight: normal;
                }
                QPushButton {
                    background-color: #f39c12;
                    color: white;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                    min-width: 80px;
                    font-size: 10pt;
                }
                QPushButton:hover {
                    background-color: #e67e22;
                }
            """)
            
            # 显示消息框并等待用户响应
            warning_box.exec()
            
            # 更新警告显示状态并保存配置
            self.warning_shown = True
            self.save_config()
            self.logger.info("用户已确认警告提示")
        
        # 禁用下载按钮，防止重复点击
        self.download_btn.setEnabled(False)
        self.clear_btn.setEnabled(False)
        self.log_btn.setEnabled(False)
        self.dir_btn.setEnabled(False)
        self.help_btn.setEnabled(False)
        self.status_bar.setText(f"正在下载 {len(album_ids)} 个专辑... | 崩溃次数: {self.crash_count}")
        self.status_text.clear()
        self.status_text.append(f"准备下载 {len(album_ids)} 个专辑...")
        self.status_text.append(f"下载目录: {self.download_dir}\n")
        
        # 创建并启动下载线程，传递下载目录
        self.download_thread = DownloadThread(album_ids, self.download_dir, self.logger)
        self.download_thread.update_signal.connect(self.update_status)
        self.download_thread.finished_signal.connect(self.download_finished)
        self.download_thread.result_signal.connect(self.handle_download_results)
        self.download_thread.start()
    
    def update_status(self, message):
        """更新状态消息"""
        # 添加消息
        self.status_text.append(message)
        
        # 滚动到底部
        self.status_text.verticalScrollBar().setValue(
            self.status_text.verticalScrollBar().maximum()
        )
    
    def handle_download_results(self, results):
        """处理下载结果并记录日志"""
        self.logger.info("=" * 70)
        self.logger.info("下载结果汇总:")
        
        total_success = 0
        total_failure = 0
        
        for album_id, stats in results.items():
            self.logger.info(f"专辑ID {album_id}: 成功 {stats['success']} 次, 失败 {stats['failure']} 次")
            total_success += stats['success']
            total_failure += stats['failure']
        
        self.logger.info(f"总计: 成功 {total_success} 个, 失败 {total_failure} 个")
        self.logger.info(f"下载目录: {self.download_dir}")
        self.logger.info("=" * 70)
        
        # 在状态栏显示结果
        self.status_text.append(f"\n下载结果汇总:")
        self.status_text.append(f"成功: {total_success} 个专辑")
        self.status_text.append(f"失败: {total_failure} 个专辑")
        self.status_text.append(f"下载目录: {self.download_dir}")
    
    def download_finished(self, success, message):
        """下载完成后启用按钮"""
        self.download_btn.setEnabled(True)
        self.clear_btn.setEnabled(True)
        self.log_btn.setEnabled(True)
        self.dir_btn.setEnabled(True)
        self.help_btn.setEnabled(True)
        
        # 更新状态栏
        if success:
            self.status_bar.setText(f"下载完成！ | 崩溃次数: {self.crash_count}")
            self.status_text.append("\n" + message)
        else:
            self.status_bar.setText(f"下载出错！ | 崩溃次数: {self.crash_count}")
            self.status_text.append("\n❌ " + message)
    
    def clear_all(self):
        """清空所有内容"""
        self.album_input.clear()
        self.status_text.clear()
        self.status_bar.setText(f"已清空所有内容 | 输入专辑ID后点击开始下载 | v1.3 | 崩溃次数: {self.crash_count}")
        self.album_input.setFocus()  # 清空后重新聚焦到输入框
        self.logger.info("用户清空了所有输入和状态")
    
    def view_logs(self):
        """查看日志文件"""
        try:
            # 打开日志目录
            if os.path.exists(LOG_DIR):
                os.startfile(LOG_DIR)  # Windows
                # 对于macOS: os.system(f'open "{LOG_DIR}"')
                # 对于Linux: os.system(f'xdg-open "{LOG_DIR}"')
                self.logger.info("用户打开了日志目录")
            else:
                QMessageBox.information(self, "日志目录", "日志目录尚未创建")
        except Exception as e:
            self.logger.error(f"打开日志目录失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"无法打开日志目录: {str(e)}")
    
    def show_help(self):
        """显示帮助信息（独立于下载过程）"""
        help_text = """
        <h3>使用帮助</h3>
        <ol>
            <li><b>下载过程中请勿操作任何下载文件</b><br>
            在下载过程中访问或修改正在下载的文件可能导致下载失败或停止。</li>
            <li><b>下载失败原因</b><br>
            本子下载失败通常是由于网络传输问题导致。<br>
            对于过长的本子（图数较多），可能会因为网络不稳定而下载失败。<br>
            解决方案：多次重新下载，程序会逐步补全未成功下载的图片。</li>
        </ol>
        
        <p style="color: #c0392b; font-weight: bold;">提示：① 下载过程中请保持网络稳定，避免操作下载目录。</p>
        <p style="color: #c0392b; font-weight: bold;">提示：② 该项目为个人项目，不保证下载的漫画内容的合法性，该软件不进行收费，为免费使用软件。</p>
        <p style="color: #FF99CC; font-weight: bold; text-align: right;">YuKe</p>
        """
        
        help_box = QMessageBox(self)
        help_box.setWindowTitle("帮助信息")
        help_box.setIcon(QMessageBox.Information)
        help_box.setTextFormat(Qt.RichText)
        help_box.setText(help_text)
        
        # 设置消息框样式
        help_box.setStyleSheet("""
            QMessageBox {
                background-color: #ecf0f1;
                font-family: SimHei;
                font-size: 10pt;
            }
            QLabel {
                color: #2c3e50;
                font-size: 10pt;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 80px;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        
        # 显示消息框
        help_box.exec()
    
    def closeEvent(self, event):
        """关闭窗口时记录日志"""
        self.logger.info("=" * 70)
        self.logger.info(f"应用程序关闭 | 总崩溃次数: {self.crash_count}")
        self.logger.info(f"最后使用的下载目录: {self.download_dir}")
        self.logger.info("=" * 70)
        
        # 确保所有日志处理完成
        logging.shutdown()
        
        super().closeEvent(event)

def resource_path(relative_path):
    """获取资源的绝对路径。用于PyInstaller打包后定位资源文件。"""
    try:
        # PyInstaller创建的临时文件夹
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    
    path = os.path.join(base_path, relative_path)
    
    # 调试信息：记录资源路径
    print(f"资源路径: {path}")
    
    # 检查文件是否存在
    if not os.path.exists(path):
        print(f"资源文件不存在: {path}")
    
    return path

def handle_exception(exc_type, exc_value, exc_traceback):
    """全局异常处理函数"""
    # 记录崩溃信息
    logging.critical("未捕获的异常", exc_info=(exc_type, exc_value, exc_traceback))
    
    # 更新崩溃计数
    if hasattr(QApplication.instance(), 'window'):
        QApplication.instance().window.crash_count += 1
        QApplication.instance().window.status_bar.setText(
            f"应用程序崩溃! | 崩溃次数: {QApplication.instance().window.crash_count}")
    
    # 显示错误信息
    # error_msg = f"应用程序发生错误:\n\n{exc_value}"
    # QMessageBox.critical(None, "应用程序错误", error_msg)
    
    # 调用默认的异常处理
    sys.__excepthook__(exc_type, exc_value, exc_traceback)

if __name__ == "__main__":
    # 设置全局异常钩子
    sys.excepthook = handle_exception
    
    # 获取资源路径
    BACKGROUND_IMAGE_PATH = resource_path("pink Gril.png")
    APP_ICON_PATH = resource_path("black.ico")
    
    app = QApplication(sys.argv)
    app.window = None  # 用于存储主窗口引用
    
    # 设置全局字体
    app.setFont(font)
    
    # 设置应用程序图标
    if os.path.exists(APP_ICON_PATH):
        app.setWindowIcon(QIcon(APP_ICON_PATH))
    
    window = JmcomicDownloader()
    app.window = window  # 存储窗口引用
    
    # 设置窗口图标
    if os.path.exists(APP_ICON_PATH):
        window.setWindowIcon(QIcon(APP_ICON_PATH))
    
    window.show()
    sys.exit(app.exec())