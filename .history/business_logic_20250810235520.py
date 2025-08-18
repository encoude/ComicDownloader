import sys
import os
import datetime
from PyQt5.QtCore import QThread, pyqtSignal, QObject

class OutputRedirector(QObject):
    """输出重定向器"""
    output_signal = pyqtSignal(str)

    def write(self, text):
        self.output_signal.emit(text)
    
    def flush(self):
        pass  # 统一实现，避免重复

class BusinessLogic:
    """业务逻辑处理类"""
    def __init__(self):
        self.DEFAULT_DOWNLOAD_DIR = os.path.join(os.path.expanduser("~"), "JM_Downloads")
        self.LOG_DIR = os.path.join(os.path.expanduser("~"), "JM_Downloads", "logs")
        self.CONFIG_FILE = os.path.join(self.LOG_DIR, "config.ini")
        self.config = None

    def get_default_download_dir(self):
        return self.DEFAULT_DOWNLOAD_DIR

    def setup_logger(self):
        """设置日志记录器（从主窗口类迁移统一逻辑）"""
        import logging
        os.makedirs(self.LOG_DIR, exist_ok=True)
        
        date_str = datetime.datetime.now().strftime("%Y%m%d")
        log_filename = os.path.join(self.LOG_DIR, f"jmcomic_downloader_{date_str}.log")
        log_exists = os.path.exists(log_filename)
        
        logger = logging.getLogger("JmComicDownloader")
        logger.setLevel(logging.INFO)
        
        file_handler = logging.FileHandler(log_filename, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        if not log_exists:
            logger.info("=" * 70)
            logger.info(f"JMComic下载器启动 - 首次创建日志文件")
            logger.info(f"日志文件: {log_filename}")
            logger.info(f"默认下载目录: {self.DEFAULT_DOWNLOAD_DIR}")
            logger.info("=" * 70)
        else:
            logger.info("\n" + "=" * 70)
            logger.info(f"新的会话启动于 {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("=" * 70)
        
        return logger

    def load_config(self):
        """加载配置文件"""
        import configparser
        self.config = configparser.ConfigParser()
        if os.path.exists(self.CONFIG_FILE):
            try:
                self.config.read(self.CONFIG_FILE, encoding='utf-8')
            except Exception as e:
                self.create_default_config()
        else:
            self.create_default_config()

    def create_default_config(self):
        """创建默认配置文件"""
        try:
            self.config['Settings'] = {
                'download_dir': self.DEFAULT_DOWNLOAD_DIR,
                'version': main.VERSION
            }
            with open(self.CONFIG_FILE, 'w', encoding='utf-8') as configfile:
                self.config.write(configfile)
        except Exception as e:
            pass

    def save_config(self, download_dir):
        """保存配置"""
        try:
            self.config['Settings']['download_dir'] = download_dir
            with open(self.CONFIG_FILE, 'w', encoding='utf-8') as configfile:
                self.config.write(configfile)
        except Exception as e:
            pass

    def parse_album_ids(self, input_text):
        """解析专辑ID"""
        import re
        if not input_text.strip():
            return []
        return re.findall(r'\d+', input_text)

    def create_download_thread(self, album_ids, download_dir, logger):
        """创建下载线程"""
        return DownloadThread(album_ids, download_dir, logger)

class DownloadThread(QThread):
    """下载线程（业务逻辑核心）"""
    update_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    result_signal = pyqtSignal(dict)
    
    def __init__(self, album_ids, download_dir, logger):
        super().__init__()
        self.album_ids = album_ids
        self.download_dir = download_dir
        self.logger = logger
        self.results = {}
        self.output_redirector = OutputRedirector()
        self.output_redirector.output_signal.connect(self.handle_output)

    def handle_output(self, text):
        if text.strip():
            self.update_signal.emit(text.strip())

    def run(self):
        """执行下载逻辑"""
        try:
            sys.stdout = self.output_redirector
            sys.stderr = self.output_redirector
            
            os.makedirs(self.download_dir, exist_ok=True)
            self.update_signal.emit(f"开始批量下载 {len(self.album_ids)} 个专辑...")
            
            # 下载逻辑实现（注意：需确保jmcomic库已安装）
            from jmcomic import JmOption
            jm_option = JmOption.default()
            jm_option.dir_rule.base_dir = self.download_dir
            
            for index, album_id in enumerate(self.album_ids, 1):
                current_album_id = album_id
                self.update_signal.emit(f"\n===== 开始下载第{index}个专辑，ID：{current_album_id} =====")
                self.logger.info(f"开始下载专辑ID: {current_album_id}")
                
                start_time = datetime.datetime.now()
                success = False
                try:
                    jm_option.download_album(current_album_id)
                    success = True
                    message = f"✅ 第{index}个专辑下载完成，ID：{current_album_id}\n保存位置: {self.download_dir}"
                    self.logger.info(f"专辑ID {current_album_id} 下载成功")
                except Exception as e:
                    message = f"❌ 专辑ID {current_album_id} 下载失败: {str(e)}"
                    self.logger.error(f"专辑ID {current_album_id} 下载失败: {str(e)}", exc_info=True)
                
                end_time = datetime.datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                if current_album_id not in self.results:
                    self.results[current_album_id] = {"success": 0, "failure": 0}
                self.results[current_album_id]["success" if success else "failure"] += 1
                
                self.update_signal.emit(message)
                self.logger.info(f"专辑ID {current_album_id} 下载耗时: {duration:.2f}秒")
            
            self.result_signal.emit(self.results)
            self.finished_signal.emit(True, "所有专辑下载完成！")
        except Exception as e:
            self.update_signal.emit(f"❌ 下载出错：{str(e)}")
            self.finished_signal.emit(False, f"下载出错：{str(e)}")
        finally:
            # 确保恢复标准输出
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__