## 运行环境
1. Python 版本：Python3.7
2. 安装 sqlite。

## 开始前配置

#### 数据库配置文件

修改数据库配置文件中数据地址为你的数据库地址，当前文件内容如下：
```
{
  "mariadb_url":"sqlite:///./pycrawler.sqlite"
}
```
你可以修改为你自己的数据库地址。

#### 安装依赖库
使用以下命令来安装依赖文件
```
pip install -r requirement.txt
```

## 运行程序

使用命令 ```python main.py``` 启动程序，启动后将看到以下内容：
```shell
20-12-16 20:27:45:INFO:crawler.crawler:run:221: Thread-1 - url : https://www.szlcsc.com/brand.html
20-12-16 20:27:45:INFO:crawler.crawler:run:221: Thread-2 - url : https://www.szlcsc.com/brand.html
20-12-16 20:27:46:ERROR:crawler.crawler:get_html:204: Error: IncompleteRead(16451 bytes read, 748656 more expected)
20-12-16 20:27:48:INFO:crawler.crawler:run:221: Thread-1 - url : https://list.szlcsc.com/brand/926.html
20-12-16 20:27:51:INFO:crawler.crawler:run:221: Thread-1 - url : https://list.szlcsc.com/brand/11442.html
20-12-16 20:27:53:INFO:crawler.crawler:run:221: Thread-1 - url : https://list.szlcsc.com/brand/1033.html
20-12-16 20:27:55:INFO:crawler.crawler:run:221: Thread-1 - url : https://list.szlcsc.com/brand/967.html
20-12-16 20:27:57:INFO:crawler.crawler:run:221: Thread-1 - url : https://list.szlcsc.com/brand/11549.html
```
