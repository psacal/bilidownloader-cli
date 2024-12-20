import asyncio
from bilibili_api import video, Credential, HEADERS, login, sync, exceptions, user, settings
import bilibili_api
from bilibili_api.login import login_with_password, login_with_sms, send_sms, PhoneNumber, Check
import httpx
import yaml
import re
import ffmpeg
import os
from tqdm import tqdm
def inputInList(prompt,list):
    '''
        获取输入并检测其是否在给定元素列表里且忽略大小写
    '''
    while True:
        str = input(prompt)
        str = str.upper()
        if str in list :
            break
        else:
            print('输入有误！请重新输入')
    return str
def checkOrCreateDirectory(path):
    """
    检查路径是否存在，如果不存在则创建该路径。
 
    参数:
    path (str): 要检查或创建的路径。
 
    """
    if not os.path.exists(path):
        try:
            # 路径成功创建
            os.makedirs(path)
        except OSError as e:
            # 如果创建目录时发生错误（例如权限不足）
            print(f"创建目录 {path} 失败: {e}")
def inputDirectory(prompt):
    """
    获取用户输入的目录路径，如果不存在则创建。
    如果输入的是'.'或者空字符串则使用程序所在目录

    参数：
    prompt:提示词
    """
    currentDir = os.path.dirname(os.path.abspath(__file__))
    userInput = input(prompt).strip()
    # 如果输入是'.'或空字符串，则使用程序所在目录
    if userInput == '.' or userInput == '':
        print("你选择了程序运行目录")
        return currentDir
    # 否则，解析用户输入的路径
    dirPath = os.path.abspath(os.path.expanduser(userInput))
    # 如果路径不存在，则创建它
    checkOrCreateDirectory(dirPath)
    return dirPath
def initGlobalConfig():
    '''
        初始化全局设置
        downloadPath:下载路径
        tempPath:缓存路径
    '''
    globalConfig = {
        'downloadPath' : '',
        'tempPath' : ''
    }
    globalConfig['downloadPath'] = inputDirectory("请输入请输入下载目录路径（输入'.'表示程序所在文件夹）")
    globalConfig['tempPath'] = inputDirectory("请输入缓存目录路径（输入'.'表示程序所在文件夹）:")
    return globalConfig
def initDownloadConfig():
    '''
        初始化下载配置
        nologin:免登录下载
        defaultResolution:默认分辨率
        defaultCodec:默认编码
        defaultByterate:默认音质
        defaultChoice:下载配置的指定方式:自动最佳,每次手动,固定
        audioOnly:是否只下载音频流
    '''
    downloadConfig = {
        'noLogin': False,
        'defaultResolution' : 'max',
        'defaultCodec' : 'h264',
        'defaultByterate' : '192k',
        'defaultChoice' : 'MANUAL',
        'audioOnly':'false'
    }
    downloadConfig['noLogin'] = (True if input("请输入是否免登录下载 (y/n) 默认否 [n]: ").strip().lower() == 'y' else False)
    downloadConfig['audioOnly'] = (True if input("请输入是否只下载音频 (y/n) 默认否 [n]: ").strip().lower() == 'y' else False)
    if downloadConfig['audioOnly']:
        print('打开此选项的情况下，本下载器将只下载视频的音频流部分并保存为mp3格式')
    downloadConfig['defaultChoice'] = inputInList("请输入下载配置的指定方式(不分大小写),MAX:最佳,MANUAL:每次手动指定,FIXED:固定"
                                                  ,["MAX","MANUAL","FIXED"])
    if downloadConfig['defaultChoice'] ==  "FIXED":
        #如果选择流的配置为固定才会继续配置默认画质，编码，音质
        downloadConfig['defaultResolution'] = inputInList("请输入默认画质(不分大小写):8K,4K,HDR,1080P_60,1080P_plus,1080P,720P,480P,360P "
                                                        ,["8K","4K","DOUBY","HDR","1080P_60","1080P_PLUS","1080P", "720P", "480P", "360P"])
        downloadConfig['defaultCodec'] = inputInList("请输入默认编码(不分大小写):H264,H265,AV1 "
                                                    ,["H264","H265","AV1"])
        downloadConfig['defaultByterate'] = inputInList("请输入音质(不分大小写):Dolby,HIRES,192K,132K,64K "
                                                        ,["Dolby","HIRES","192K","132K","64K"])
    return downloadConfig
async def generateAndInitConfigFile():
    '''
        从默认模版生成配置文件
    '''
    configTemplete ={
        'download_config' : {
            'noLogin': '',
            'defaultResolution': '',
            'defaultCodec' : '',
            'defaultByterate' : '',
            'audioOnly':''
        },
        'global_config' : {
            'downloadPath' : '',
            'tempPath' : ''
        },
        'user_credential':{
            'DedeUserID': '',
            'SESSDATA': '',
            'ac_time_value': '',
            'bili_jct': '',
            'buvid3': ''
        }
    }      
    configTemplete['download_config'] = initDownloadConfig()
    configTemplete['global_config'] = initGlobalConfig()
    with open('config.yaml', 'w') as file:
        yaml.dump(configTemplete, file, default_flow_style=False, allow_unicode=True)
def isUserCookiesNone(config):
    '''
        检查用户Cookies是否为空
    '''
    #默认不存在空值
    isNone = False
    user_config = config['user_credential']
    for key in user_config.keys():
        isNone = isNone or (True if user_config[key]=="" else False)
    #每次循环结果都会与值是否为空的表达式做或运算，只要有一次为空，结果就会被置真，如果全部不为空，则结果始终为否
    return isNone
def isLogin(config): 
    '''
        检查是否需要登陆
    '''
    #默认需要登录
    result =True
    #判断账户信息是否存在空项
    isNone = isUserCookiesNone(config)
    noLogin = config['download_config']['noLogin']
    if (noLogin):
        #只要不登录生效，则始终不用登录
        print("你选择了免登录下载")
        result = False
    elif (isNone):
        #如果需要登录且登录信息为空，则需要登录
        print("你的账户信息存在空项，请登录")
        result = True
    else :
        #如果需要登录且登录信息不为空，则不用登录
        print("检测到账户信息,即将开始下载")
        result = False
    return result
async def userLogin():
    '''
        通过账号密码/手机验证码/终端内二维码登陆
    '''
    choose = 0
    credential = None
    settings.geetest_auto_open = False
    while (credential == None):
        if (choose == 1):
            username = input("请输入手机号/邮箱：")
            password = input("请输入密码：")
            print("正在登录。")
            try:
                tempCredential = login_with_password(username, password)
            except exceptions.LoginError:
                print("登录失败，请考虑使用其他方式登录")
            if isinstance(tempCredential, Check):
                # 还需验证
                print("需要进行验证。请考虑使用其他方式登录")
            else:
                credential = tempCredential
                print("通过账号密码登录成功")
        elif (choose == 2):
            countryNumber = input('输入电话国家代码，默认为中国大陆+86')
            countryNumber = countryNumber if (countryNumber != '') else "+86"
            phoneNumber = input("请输入手机号:")
            send_sms(PhoneNumber(phoneNumber, country=countryNumber)) # 默认设置地区为中国大陆
            code = input("请输入验证码：")
            tempCredential = login_with_sms(PhoneNumber(phoneNumber, country="+86"), code)
            if isinstance(tempCredential, Check):
                print("需要进行验证。请考虑使用其他方式登录")
            else:
                credential = tempCredential
                print("通过手机验证码登录成功")
        elif (choose == 3):
            credential = login.login_with_qrcode_term() # 在终端扫描二维码登录
            try:
                credential.raise_for_no_bili_jct() # 判断是否成功
                credential.raise_for_no_sessdata() # 判断是否成功
            except exceptions.LoginError:
                print("二维码登陆失败")
                credential = None
            print('通过终端二维码登录成功')
        else:
                print('请选择登录方式 (1/2/3)')
                print('1.账号密码(需要打开浏览器进行人机验证)')
                print('2.手机验证码(需要打开浏览器进行人机验证)')
                print('3.终端内二维码登陆')
                choose = int(input())
    print("欢迎，", sync(user.get_self_info(credential))['name'], "!",sep='')
    return credential
async def saveCookies(tempCoockies,Config):
    '''
        保存用户Cookies
    '''
    Config['user_credential']=tempCoockies
    with open('config.yaml', 'w') as file:
        yaml.dump(Config, file, default_flow_style=False, allow_unicode=True)
async def loadAllConfig():
    '''
        读取配置
    '''
    try:
        with open('config.yaml', 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
    except FileNotFoundError:
        print("未找到配置文件！")
        await generateAndInitConfigFile()
        with open('config.yaml', 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
    needLogin = isLogin(config)
    if needLogin :
        tempCredential = await userLogin()
        tempCookies = tempCredential.get_cookies()
        await saveCookies(tempCookies,config)
    else:
        tempCookies = config['user_credential']
    tempDownloadConfig = config["download_config"]
    tempGlobalconfig = config["global_config"]
    allConfig = {}
    allConfig['cookies'] = tempCookies
    allConfig['download_config'] = tempDownloadConfig
    allConfig['global_config'] = tempGlobalconfig
    return allConfig
def normalizeBvid(bvid:str):
    """
    将用户输入的 bv 号以 Bv, bV 或 bv 开头的情况统一改为以 BV 开头，
    同时保持后面的字符串大小写不变。

    返回:
    str: 规范化后的 bv 号。
    """
    # 检查输入字符串是否以 Bv, bV 或 bv 开头（不改变大小写）
    if bvid.startswith(('Bv', 'bV', 'bv')):
        # 将前缀统一改为 BV，并连接上后面的字符串
        return 'BV' + bvid[2:]
    else:
        # 如果输入不符合条件，直接返回原字符串
        return bvid
def extractAvidBvid(url_or_code:str):
    '''
        从输入中分离avid,bvid并转为bvid
    '''
    avid_pattern = re.compile(r'[aA][vV](\d+)')
    bvid_pattern = re.compile(r'[bB][vV][\d\w]+')
    number_pattern = re.compile(r'^\d+$')
    avid_match = avid_pattern.search(url_or_code)
    bvid_match = bvid_pattern.search(url_or_code)
    number_match = number_pattern.search(url_or_code)
    avid = avid_match.group(1) if avid_match else None
    bvid = bvid_match.group(0) if bvid_match else None
    number = number_match.group(0) if number_match else None
    if avid == None and bvid == None:
        if number_match :
            avid = number
    if bvid != None:
        bvid = normalizeBvid(bvid=bvid)
    return avid, bvid
def isInputVaild(inputString:str):
    '''
        判断输入是否合法并返回bvid

        返回：str
    '''
    avid, bvid = extractAvidBvid(inputString)
    if avid and bvid:
        # 如果同时存在AV号和BV号，则报错
        print("请勿同时输入AV号与BV号")
    elif avid:
        # 为AV号则转为BV号 注意此处aid2bvid传入int返回str
        bvid = bilibili_api.aid2bvid(int(avid))
        return bvid
    elif bvid:
        # 如果不存在AV号但存在BV号，则直接返回BV号
        return bvid
    else:
        # 如果都不存在，则返回无效输入提示
        return "什么也没有呢"
def sanitizeFilename(filename, replacement='_'):
    '''
        格式化文件名
    '''
    # 保留文件名的扩展名
    name, ext = os.path.splitext(filename)
    illegal_chars = re.compile(r'[\/\\:*?"<>|\s]+')
    # 替换非法字符
    sanitized_name = illegal_chars.sub(replacement, name)
    # 去除前导和尾随的替换字符（如果有的话）
    sanitized_name = sanitized_name.strip(replacement)
    # 重新组合文件名和扩展名
    return sanitized_name + ext
def enhanceStreamDataReadability(str):
    #我也不想硬编码。。。
    qualityOfVideoAndAudio = {
        #视频清晰度
        '_360P': '流畅360P',
        '_480P': '清晰480P',
        '_720P': '高清720P',
        '_1080P': '高清1080P',
        '_1080P_PLUS': '高清 1080P高码率',
        '_1080P_60': '高清 1080P60帧',
        '_4K': '超清4K',
        'HDR': '真彩HDR',
        'DOLBY': '杜比视界',
        '_8K': '超高清 8K',
        #音频清晰度
        '_64K': '64K',
        '_132K': '132K',
        '_192K': '192K',
        'HI_RES': 'Hi Res 无损',
        'DOLBY': '杜比全景声',
        #视频编码
        'HEV' : "H.265 (HEVC)",
        'AVC' : "H.264 (AVC)",
        'AV1' : "AV1"
    }
    return qualityOfVideoAndAudio[str]
def config2reality(str):
    qualityOfVideoAndAudio = {
        #视频清晰度
        '360P': '_360P',
        '480P': '_480P',
        '720P': '_720P',
        '1080P': '_1080P',
        '1080P_PLUS': '_1080P_PLUS',
        '1080P_60': '_1080P_60',
        '4K': '_4K',
        'HDR': 'HDR',
        'DOLBY': 'DOLBY',
        '8K': '_8K',
        #音频清晰度
        '64K': '_64K',
        '132K': '_132K',
        '192K': '_192K',
        'HIRES': 'HI_RES',
        'DOLBY': 'DOLBY',
        #视频编码
        'H265' : "HEV",
        'H264' : "AVC",
        'AV1' : "AV1"
    }
    return qualityOfVideoAndAudio[str]
async def downloadFromUrl(url: str, out: str, info: str):
    '''
        从指定url中下载
    '''
    async with httpx.AsyncClient(headers=HEADERS) as sess:
        resp = await sess.get(url)
        length = resp.headers.get('content-length')
        with open(out, 'wb') as f:
            pbar = tqdm(total=int(length),desc=info+'进度')
            for chunk in resp.iter_bytes(1024):
                if not chunk:
                    break
                pbar.update(len(chunk))
                f.write(chunk)
            pbar.close()
def mixStreams(videoPath='',audioPath='',finalPath='default.mp4',name=''):
    '''
        混流

        参数：
        videoPath:临时视频流路径(含文件名)
        audioPath:临时音频流路径(含文件名)
        finalPath:混流文件存放路径
        name:混流文件名
    '''
    checkOrCreateDirectory(finalPath)#检测下载路径是否存在
    finalFilePath = os.path.join(finalPath,name)#完整路径+下载文件名
    if (audioPath != '' and videoPath != ''):
        #视频，音频流都存在，即mp4
        audioStream = ffmpeg.input(audioPath)
        videoStream = ffmpeg.input(videoPath)
        outputStream = ffmpeg.output(audioStream, videoStream, finalFilePath, acodec='copy', vcodec='copy',loglevel='info')
        ffmpeg.run(outputStream)
        os.remove(videoPath)
        os.remove(audioPath)
    elif (audioPath == '' and videoPath != ''):
        #音频视频流，即flv
        inputStream = ffmpeg.input(videoPath)
        outputStream = ffmpeg.output(inputStream, finalFilePath, vcodec='libx264', loglevel='info')
        ffmpeg.run(outputStream)
        os.remove(videoPath)
    elif (audioPath != '' and videoPath == ''):
        #音频流转mp3
        inputStream = ffmpeg.input(audioPath)
        finalMp3Path = finalFilePath.replace('.mp4','.mp3')
        outputStream = ffmpeg.output(inputStream, finalMp3Path, loglevel='info')
        ffmpeg.run(outputStream)
        os.remove(audioPath)
def selectStreams(detecter,downloadConfig):
    '''
        从解析出的视频/音频流中选择流
    '''
    choice = downloadConfig['defaultChoice']
    resolution = downloadConfig['defaultResolution']
    codec = downloadConfig['defaultCodec']
    byterate = downloadConfig['defaultByterate']
    if choice == 'MAX' :
        streamsList = detecter.detect_best_streams()
        videoUrl = streamsList[0].url
        audioUrl = streamsList[1].url
    elif choice == 'MANUAL':
        streamsList = detecter.detect()
        streamsListSize = len(streamsList)
        print("请选择你要下载的流")
        if (detecter.check_flv_stream()):
            print('Flv流,无需选择')
            videoUrl = streamsList[0].url
        else:
            for i in range(streamsListSize):
                    if type(streamsList[i]).__name__ == 'VideoStreamDownloadURL':
                        print(i,'视频:',enhanceStreamDataReadability(streamsList[i].video_quality.name),'编码:',enhanceStreamDataReadability(streamsList[i].video_codecs.name))
                    elif type(streamsList[i]).__name__ == 'AudioStreamDownloadURL':
                        print(i,'音频:',enhanceStreamDataReadability(streamsList[i].audio_quality.name))
            videoIndex,audioIndex = int(input("请输入画质序号")),int(input('请输入音质序号'))
            videoUrl = streamsList[videoIndex].url
            audioUrl = streamsList[audioIndex].url
    elif choice == 'FIXED':
        videoIndex,audioIndex = None,None
        streamsList = detecter.detect()
        streamsListSize = len(streamsList)
        for i in range(streamsListSize):
                    if type(streamsList[i]).__name__ == 'VideoStreamDownloadURL':
                        if (streamsList[i].video_quality.name == config2reality(resolution) 
                            and streamsList[i].video_codecs.name == config2reality(codec)):
                            videoIndex = i
                    elif type(streamsList[i]).__name__ == 'AudioStreamDownloadURL':
                        if streamsList[i].audio_quality.name == config2reality(byterate):
                            audioIndex= i
        if (videoIndex != None) and (audioIndex != None):
            videoUrl = streamsList[videoIndex].url
            audioUrl = streamsList[audioIndex].url
        else :
            print("设置的清晰度/编码/音质超过了原视频，自动以最佳画质下载")
            streamsList = detecter.detect_best_streams()
            videoUrl = streamsList[0].url
            audioUrl = streamsList[1].url
    return videoUrl,audioUrl 
def initCredential(cookies):
    '''
        从cookies中实例化credential并检测是否要刷新
    '''
    credential=Credential(sessdata=cookies['SESSDATA'],
                                bili_jct=cookies['bili_jct'],
                                buvid3=cookies['buvid3'],
                                dedeuserid=cookies['DedeUserID'],
                                ac_time_value=cookies['ac_time_value'])
    try :
        sync(credential.check_refresh())
        if sync(credential.check_refresh()):
            print("刷新cookies!")
            sync(credential.refresh())
    except exceptions.CredentialNoSessdataException:
            print("没有用户信息,无需刷新Cookies")
    return credential
async def downloadAndSave(videoId,allconfig):
    '''
        下载并保存文件
    '''
    credential = initCredential(allconfig['cookies'])
    #根据BV号与用户信息实例化下载视频类downloadVideo
    downloadVideo = video.Video(bvid=videoId, credential=credential)
    #解析视频基本信息
    downloadVideoInfo = await downloadVideo.get_info()
    downloadVideoName = downloadVideoInfo["title"]
    downloadUrlData = await downloadVideo.get_download_url(0)
    #解析视频下载信息
    Detecter = video.VideoDownloadURLDataDetecter(data=downloadUrlData)
    tempPath = allconfig['global_config']['tempPath'] #缓存目录
    checkOrCreateDirectory(tempPath)
    tempFlv = os.path.join(tempPath,"flv_temp.flv") #临时flv流(含路径)
    tempVideo = os.path.join(tempPath,"video_temp.m4s") #临时视频流名(含路径)
    tempAudio = os.path.join(tempPath,"audio_temp.m4s") #临时音频流名(含路径)
    finalFileName = sanitizeFilename(downloadVideoName) + '.mp4' #下载文件名
    downloadPath = allconfig['global_config']['downloadPath'] #下载目录
    videoUrl,audioUrl = selectStreams(Detecter, allconfig['download_config'])
    if Detecter.check_flv_stream():
        # 下载FLV
        print('此视频只有flv流')
        await downloadFromUrl(videoUrl, tempFlv, "FLV音视频流")
        mixStreams(videoPath=tempVideo, finalPath=downloadPath, name=finalFileName)
    else:
        #下载MP4流
        if allconfig['download_config']['audioOnly']:
            #如果设置了只下载音频流，则不用下载视频流
            await downloadFromUrl(audioUrl, tempAudio,'音频流')
            mixStreams(audioPath=tempAudio, finalPath=downloadPath, name=finalFileName)
        else:
            #下载视频流与音频流
            await downloadFromUrl(videoUrl, tempVideo, "视频流")
            await downloadFromUrl(audioUrl, tempAudio, "音频流")
            mixStreams(videoPath=tempVideo, audioPath=tempAudio, finalPath=downloadPath, name=finalFileName)
    print(f'{downloadVideoName}下载完成了！')
async def main():
    allconfig = await loadAllConfig()
    videoId = isInputVaild(input("请输入下载地址,AV号或BV号(bv号请不要只输入bv号后的部分)"))
    await downloadAndSave(videoId, allconfig)
if __name__ == '__main__':
    # 主入口
    asyncio.get_event_loop().run_until_complete(main())