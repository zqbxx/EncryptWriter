# 加密文档编辑器（EncryptWriter）
![EncryptWriter](doc/images/icon.png "EncyptWriter Logo")

加密文档编辑器（EncryptWriter）是一个基于https://github.com/goldsborough/Writer-Tutorial 
开发的富文本编辑器。
主要目的是加密保存和编辑文档，不在系统上留下未加密的临时文件。
# 下载

https://github.com/zqbxx/EncryptWriter/releases

# 使用
...
# 编译
下载源代码
```commandline
git clone https://github.com/zqbxx/EncryptWriter.git
```
完成以后进入项目目录
### 安装依赖
```commandline
pip install -r requirements.txt
```
### 编译工具
使用nuitka1.1.7版本或者兼容此版的的nuitka进行编译
### 图标转换支持
nuitka需要使用Pillow转换图标文件，需要自行安装
```commandline 
pip install Pillow
```
### 编译
```commandline
compile.bat
```


