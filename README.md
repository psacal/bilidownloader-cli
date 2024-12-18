<div align="center">

# 比利下载器 命令行交互版
一个极简B站视频下载器

</div>


## 简介
这是一个极简且功能完备的B站视频下载器,仅一个python文件~~与ffmpeg运行库~~

## 功能
1. 自由选择你想下载的所有流：
    - 视频流:8K,HDR,杜比视界,4K,1080P60帧,1080P高码率,720P,480P,360P
    - 音频流：Dolby,HI_Res,192K,132K,64K
    - 编码：H264,H265,AV1
2. 自定义缓存与下载目录
3. 设置默认下载质量
   - 每次手动选择
   - 全都最佳
   - 固定
4. 免登录下载
## TODO
- [ ]  添加字幕，弹幕，视频简介及信息下载并与视频文件保存在同一文件夹
- [ ]  测试在linux系统下的运行情况
- [ ]  重构出可读取命令行参数版

## 本程序使用了以下开源库：
- [bilibili-api](https://github.com/Nemo2011/bilibili-api):用 Python 写的调用 Bilibili 各种 API 的库
- [ffmpeg-python](https://github.com/kkroening/ffmpeg-python):为Python调用ffmpeg提供封装的库
- [pyyaml](https://github.com/yaml/pyyaml):解析Yaml
- [tqdm](https://github.com/tqdm/tqdm):Python下实现命令行进度条
- [httpx](https://github.com/encode/httpx):A next generation HTTP client for Python
## 上手使用
### 简要步骤
1. 确保你的电脑已经安装好Python环境，然后使用Pip命令安装以下依赖：
```batch
pip install pyyaml
pip install httpx
pip install bilibili-api-python
pip install tqdm
pip install ffmpeg-python
```
2. 接下来安装ffmpeg,并设置环境变量
[教程](https://www.cnblogs.com/wwwwariana/p/18191233)
~~介于篇幅有限且网上的教程比我写的更好，请自行点击链接学习~~

3. 下载main.py(或者拷贝里面的内容并存到你新建的.py文件中)

4. 打开CMD或Powershell
```batch
python main.py
```
根据提示初始化配置
**如果对配置不满意，直接把config.yaml删掉即可**

## 注意事项
本下载器无法下载番剧,课程

## 成为贡献者

## 最后

- 这是我的<font color='#FF0000'>第一个<font color = '000000'>github项目,如果喜欢,请多多star
- 遇到了令人不爽😡的BUG🐜或有更棒的想法？发issue告诉我，也许就会出现在TODO中