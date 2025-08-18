import sys
from PyQt5.QtWidgets import QApplication, QFont
from ui import JmcomicDownloaderUI
from business_logic import BusinessLogic

VERSION = "1.3"  # 统一版本号常量

def main():
    # 确保中文显示正常
    font = QFont()
    font.setFamily("SimHei")
    
    app = QApplication(sys.argv)
    app.setFont(font)
    
    # 初始化业务逻辑
    business_logic = BusinessLogic()
    
    # 初始化UI并传入业务逻辑实例
    window = JmcomicDownloaderUI(business_logic)
    app.instance().window = window  # 设置全局窗口引用，供异常处理使用
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()