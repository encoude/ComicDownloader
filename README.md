# 使用手册
简介
ComicDownload 是一个用于下载和访问禁漫天堂（JMComic）内容的Python库。本手册提供了安装和使用该库的基本指南。

环境需求
Python版本要求
Python 3.9 ~ 3.12

操作系统支持
Windows 10/11

Linux (Ubuntu/Debian/CentOS等主流发行版)

依赖库
text
jmcomic 2.6.5
PySide6 6.9.1
pyinstaller 6.15.0
requests >= 2.28.0
beautifulsoup4 >= 4.11.0
lxml >= 4.9.0
tqdm >= 4.64.0
安装指南
1. 安装Python
首先确保已安装兼容的Python版本：

bash
# 检查Python版本
python --version
# 或
python3 --version
2. 创建虚拟环境（推荐）
bash
python -m venv jmcomic-env
source jmcomic-env/bin/activate  # Linux/macOS
jmcomic-env\Scripts\activate     # Windows
3. 安装jmcomic库
bash
pip install jmcomic
4. 验证安装
python
import jmcomic
print(f"jmcomic version: {jmcomic.__version__}")
基础使用示例
下载单本漫画
python
from jmcomic import download_album

# 通过禁漫天堂的album ID下载
download_album("album_id_here")
搜索漫画
python
from jmcomic import search_album

results = search_album("搜索关键词")
for album in results:
    print(f"标题: {album.title}, ID: {album.id}")
设置下载路径
python
from jmcomic import JmOption

option = JmOption()
option.download_dir = "/path/to/download/folder"

# 使用自定义配置下载
download_album("album_id_here", option=option)
高级功能
批量下载
python
from jmcomic import download_album

album_ids = ["359388", "179941"]
for album_id in album_ids:
    download_album(album_id)
使用代理
python
option = JmOption()
option.client.proxies = {
    "http": "http://127.0.0.1:8080",
    "https": "http://127.0.0.1:8080"
}

download_album("album_id_here", option=option)
多线程下载
python
option = JmOption()
option.download.threading = True
option.download.thread_count = 4  # 使用4个线程

download_album("album_id_here", option=option)
常见问题解决
安装问题
错误：找不到满足要求的版本

text
ERROR: Could not find a version that satisfies the requirement jmcomic
解决方案：

确认Python版本在3.9-3.12之间

更新pip：pip install --upgrade pip

尝试从镜像源安装：pip install jmcomic -i https://pypi.tuna.tsinghua.edu.cn/simple

运行问题
SSL证书错误

text
requests.exceptions.SSLError
解决方案：

python
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
下载问题
403禁止访问错误

text
HTTPError: 403 Client Error
解决方案：

使用代理

设置请求头

python
option = JmOption()
option.client.headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ..."
}
注意事项
请遵守当地法律法规，合理使用本库

尊重版权，下载内容仅限个人使用

避免高频请求，以免对目标网站造成压力

使用代理时请确保代理服务器的合法性


更新日志
text
v1 - 2025-08-09
  * 添加多线程下载支持
  * 优化下载速度

v1.2 - 2025-08-10
  * 修复代理设置问题
  * 增加异常处理机制
  * 增加背景元素互动
  * 增加地址自由保存
  * 增加报错日志查看
  * 增加软件崩溃检测

v1.3 - 2025-08-18
  * 背景图更新
  * 声明更新
本手册最后更新于：2025年08月18日
对应 jmcomic 版本：2.6.5
