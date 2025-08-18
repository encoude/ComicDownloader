# ui.py
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QFrame, QFileDialog, QSizePolicy
from PySide6.QtCore import Qt, QTimer, QPointF, Signal, QThread, QSize
from PySide6.QtGui import QFont, QColor, QPainter, QLinearGradient, QRadialGradient, QPixmap

"""下载器主界面"""
class JmcomicDownloaderUI(QMainWindow):
    """下载器主界面"""
    def __init__(self, business_logic):
        super().__init__()
        self.bl = business_logic  # 业务逻辑实例
        self.download_dir = self.bl.get_default_download_dir()
        self.logger = self.bl.setup_logger()
        self.crash_count = 0
        
        self.bl.load_config()
        self.init_ui()

    def init_ui(self):
        """初始化界面布局"""
        self.setWindowTitle("JM漫画下载器  -  V1.3")
        self.setGeometry(100, 100, 800, 650)
        self.setMinimumSize(QSize(700, 550))
        
        # 背景和主布局设置
        self.background_widget = AnimatedBackground()
        self.setCentralWidget(self.background_widget)
        
        content_widget = QWidget()
        content_widget.setStyleSheet("background-color: transparent;")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(15)
        
        # 顶部布局（标题和帮助按钮）
        top_layout = QHBoxLayout()
        
        # 创建标题容器（用于居中显示标题）
        title_container = QWidget()
        title_container.setStyleSheet("background-color: rgba(0, 0, 0, 0.4); border-radius: 8px;")
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
        self.album_input.setPlaceholderText("例如：\n540931, 540836,539876,535583,503149")
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
        example_label = QLabel("示例输入格式：540931,540836,539876 或每行一个ID")
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
        
        # 窗口居中显示
        self.center_window()

        # 将内容部件添加到背景部件
        self.background_widget.setLayout(QVBoxLayout())
        self.background_widget.layout().addWidget(content_widget)
        
        # 初始化下载线程
        self.download_thread = None

    def choose_download_dir(self):
        """选择下载目录（UI交互）"""
        dir_path = QFileDialog.getExistingDirectory(
            self, "选择下载目录", self.download_dir
        )
        if dir_path:
            self.download_dir = dir_path
            self.dir_display.setText(dir_path)
            self.logger.info(f"用户设置下载目录为: {dir_path}")
            self.status_text.append(f"✅ 下载目录已设置为: {dir_path}")
            self.bl.save_config(self.download_dir)

    def start_download(self):
        """启动下载（调用业务逻辑）"""
        input_text = self.album_input.toPlainText()
        album_ids = self.bl.parse_album_ids(input_text)
        
        if not album_ids:
            QMessageBox.warning(self, "输入错误", "请输入有效的专辑ID")
            return
            
        # 显示警告消息框
        warning_msg = "下载过程中请勿操作下载文件和目录，否则可能导致下载失败！\n是否继续？"
        reply = QMessageBox.question(self, "警告", warning_msg, 
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
            
        # 调用业务逻辑的下载线程
        self.download_thread = self.bl.create_download_thread(
            album_ids, self.download_dir, self.logger
        )
        self.download_thread.update_signal.connect(self.update_status)
        self.download_thread.finished_signal.connect(self.download_finished)
        self.download_thread.result_signal.connect(self.handle_download_results)
        self.download_thread.start()

    def update_status(self, message):
        """更新状态显示"""
        self.status_text.append(message)
        self.status_text.verticalScrollBar().setValue(
            self.status_text.verticalScrollBar().maximum()
        )

    def mouseMoveEvent(self, event):
        self.mouse_pos = event.position()
        self.update()

"""动态背景组件"""
class AnimatedBackground(QWidget):
    """动态背景组件"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.mouse_pos = QPointF(0, 0)
        self.particles = []
        self.lines = []
        self.circles = []
        self.init_particles()
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(30)
        
        self.background_pixmap = QPixmap(BACKGROUND_IMAGE_PATH) if os.path.exists(BACKGROUND_IMAGE_PATH) else None
        self.interaction_radius = 150

    def init_particles(self):
        """初始化粒子系统"""
        # 粒子初始化逻辑
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
        
        # 线条和圆形初始化
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
                            (particle['pos'].y() - self.mouse_pos.y())** 2)
            if dist < self.interaction_radius:
                dx = particle['pos'].x() - self.mouse_pos.x()
                dy = particle['pos'].y() - self.mouse_pos.y()
                force = (self.interaction_radius - dist) / self.interaction_radius * 2.0
                particle['speed'] += QPointF(dx * force * 0.02, dy * force * 0.02)
        
        # 更新线条和圆形位置（省略重复代码）
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
            # 渐变背景
            gradient = QLinearGradient(0, 0, self.width(), self.height())
            gradient.setColorAt(0, QColor(25, 25, 50))
            gradient.setColorAt(1, QColor(10, 10, 30))
            painter.fillRect(self.rect(), gradient)
        
        # 绘制动态元素（省略重复代码）