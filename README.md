在开始之前需要先创建 ```database.conf``` 配置文件、以及安装依赖。

```database.conf``` 文件内容如下：
```
{
  "mariadb_url":"sqlite:///./pycrawler.sqlite"
}
```
你可以修改为你自己的数据库地址。


使用以下命令来安装依赖文件
```
pip install -r requirement.txt
```
