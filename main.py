from time import sleep
from http.cookiejar import LWPCookieJar
from os import remove, path, makedirs
from requests.packages.urllib3 import disable_warnings
from requests import get,session
from json import loads
from re import findall
from tkinter import StringVar, Tk, messagebox, Entry
from io import BytesIO
from functools import partial
from PIL import Image, ImageTk
from qrcode import QRCode
from tkinter.ttk import Button, Label
from threading import Thread
from moviepy.editor import VideoFileClip, AudioFileClip
from moviepy.config import change_settings

headers = {
    'authority': 'api.vc.bilibili.com', 'accept': 'application/json, text/plain, */*',
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
    'content-type': 'application/x-www-form-urlencoded',
    'origin': 'https://message.bilibili.com', 'referer': 'https://message.bilibili.com/',
    'sec-ch-ua': '"Chromium";v="116", "Not)A;Brand";v="24", "Microsoft Edge";v="116"', 'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty', 'sec-fetch-mode': 'cors', 'sec-fetch-site': 'same-site',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36 Edg/116.0.1938.81',
}


def create_down_bilibili_folder():
    desktop_path = path.join(path.expanduser("~"), 'Desktop')
    down_bilibili_path = path.join(desktop_path, 'Down_bilibili')
    down_video_path = path.join(down_bilibili_path, 'down_video')
    cookie_path = path.join(down_bilibili_path, 'bzcookies.txt')
    try:
        if not path.exists(down_bilibili_path):
            makedirs(down_bilibili_path)
        else:
            pass
        if not path.exists(down_video_path):
            makedirs(down_video_path)
            with open(cookie_path, 'w', encoding='utf-8') as file:
                file.write('')
        return down_bilibili_path, cookie_path
    except Exception as e:
        print(f"初始化发生错误: {e},请联系开发者-->")


# 音乐和视频合二为一
def combine_audio_video(video_path, audio_path, output_path):
    try:
        # 加载视频和音频文件
        ffmpeg_path = path.abspath(r"C:\Users\86156\Desktop\WeChatMsg-master\app\resources\data\ffmpeg.exe")
        change_settings({"FFMPEG_BINARY": ffmpeg_path})
        video = VideoFileClip(video_path)
        audio = AudioFileClip(audio_path)
        video_with_audio = video.set_audio(audio)
        video_with_audio.write_videofile(output_path, codec='libx264', audio_codec='aac', logger='bar')

        if path.exists(output_path):
            remove(video_path)
            remove(audio_path)
        else:
            print("输出文件未生成，不执行删除操作。")
    except Exception as e:
        messagebox.showinfo('e', e)
        print(f'发生错误: {e}')
        print("由于错误，未删除源文件。")


def down_video(bvcode, s2, path_need):
    url = f'https://www.bilibili.com/video/{bvcode}/'
    response = s2.get(url=url, headers=headers)
    html = response.text
    # 解析数据: 提取视频标题
    title = findall('title="(.*?)"', html)[0]
    title = title.replace('”', '')
    title = title.replace('“', '')
    info = findall('window.__playinfo__=(.*?)</script>', html)[0]
    json_data = loads(info)
    video_url = json_data['data']['dash']['video'][0]['baseUrl']
    # print('提取视频链接-->', video_url)
    # 提取音频链接
    audio_url = json_data['data']['dash']['audio'][0]['baseUrl']
    # print('提取音频链接-->', audio_url)
    video_content = s2.get(url=video_url, headers=headers).content
    # 获取音频内容
    audio_content = s2.get(url=audio_url, headers=headers).content
    # video
    with open(f'{path_need}\{title}.mp4', 'wb') as file:
        file.write(video_content)
    # audio
    with open(f'{path_need}\{title}.mp3', 'wb') as file:
        file.write(audio_content)
    print('开始合成视频...')
    combine_audio_video(f'{path_need}\{title}.mp4', f'{path_need}\{title}.mp3', f'{path_need}\down_video\{title}_.mp4')


def is_login(session):
    try:
        # 加载ck
        session.cookies.load(ignore_discard=True)
    except Exception as e:
        print(e)
        # 通过请求一个网站来判断是否ck有效 带上ck
    login_url = session.get("https://api.bilibili.com/x/web-interface/nav", verify=False, headers=headers).json()
    if login_url['code'] == 0:
        print(f"Cookies值有效, {login_url['data']['uname']}, 已登录！")
        return True
    else:
        print('Cookies值已经失效，请重新扫码登录！')
        return False


def scan_code(session2):
    # 这个时候session的ck什么都没有,相当于空白没有ck请求
    # 定义一个全局变量  bili_jct
    global bili_jct
    get_login = session2.get('https://passport.bilibili.com/x/passport-login/web/qrcode/generate?source=main-fe-header',
                             headers=headers).json()
    # 获取qrcode_key
    qrcode_key = get_login['data']['qrcode_key']
    # 开始进入生成二维码逻辑
    qr = QRCode()
    # 对获取到的url转换成二维码
    qr.add_data(get_login['data']['url'])
    # img就是二维码了
    img = qr.make_image()
    # 对二维码设置一些尺寸
    pil_image_change = img.resize((200, 200), resample=Image.BICUBIC, box=None, reducing_gap=None)
    # 将其转换为可以在 Tkinter GUI 中显示的格式
    code_pic = ImageTk.PhotoImage(pil_image_change)
    # 将tooken带入url里  这个是确定扫码的状态 如果扫码成功那么就会写入ck
    token_url = f'https://passport.bilibili.com/x/passport-login/web/qrcode/poll?qrcode_key={qrcode_key}&source=main-fe-header'
    # 图片设置到页面里
    label_ver1 = Label(root, image=code_pic)
    v1.set('正在等待扫码...')
    label_ver1.grid(row=1, column=1, rowspan=8, columnspan=1, sticky='n')
    while 1:
        # 扫码结果状态码
        qrcode_data = session2.get(token_url, headers=headers).json()
        if qrcode_data['data']['code'] == 0:
            v1.set('扫码成功!')
            session2.get(qrcode_data['data']['url'], headers=headers)
            break
        else:
            v1.set(qrcode_data['data']['message'])
        sleep(1)
        root.update()
        # 成功,然后保存ck
    session2.cookies.save()

    with open(temp_cookie, 'r', encoding='utf-8') as f:
        bzcookie = f.read()
        # 获取注销登录需要的变量
    bili_jct = findall(r'bili_jct=(.*?);', bzcookie)[0]


def bz_login():
    # 定义一个全局变量
    global code_pic
    # 套上一层LWPCookieJar
    session1.cookies = LWPCookieJar(filename=temp_cookie)
    # 调用is_login函数,传入session对象,判断ck是不是还有效  如果有效 返回True 否则是False
    status = is_login(session1)
    if not status:
        # ck失效的逻辑,调用这个函数,传入一个session对象
        scan_code(session1)
        verification()
    else:
        verification()


def verification():
    url = 'https://api.bilibili.com/x/web-interface/nav'
    resp1 = session1.get(url=url, headers=headers).json()
    global tk_image
    if resp1['data']['isLogin']:
        face_url = resp1['data']['face']
        image_bytes = get(face_url).content
        data_stream = BytesIO(image_bytes)
        pil_image = Image.open(data_stream)
        pil_image_change = pil_image.resize((200, 200), resample=Image.BICUBIC, box=None, reducing_gap=None)
        tk_image = ImageTk.PhotoImage(pil_image_change)
        status = "cookie有效！登录成功！"
    else:
        thread_it(bz_login)
        status = 'cookie无效！重新登录'
    label_ver = Label(root, image=tk_image)
    label_ver.grid(row=1, column=1, rowspan=8, columnspan=1, sticky='n')
    v1.set(status)


def thread_it(func, *args):
    thread = Thread(target=func, args=args, daemon=True)
    thread.start()
    return thread


def cancel_login():
    msg1 = messagebox.askyesno(title="提示", message="注销后cookie将失效，是否注销登录？")
    if msg1:
        url3 = 'https://passport.bilibili.com/login/exit/v2'
        data3 = {'biliCSRF': f'{bili_jct}'}
        session1.post(url=url3, headers=headers, data=data3).json()
        verification()


def get_bv_value(entry_widget, s2, path_):
    pattern = r'https://www\.bilibili\.com/video/(BV[\da-zA-Z]+)(?:\?t=\d+\.\d+)?'
    try:
        bv_value = findall(pattern, entry_widget.get())[0]
        messagebox.showinfo('SCUUESS', '开始下载,等待即可(请忽视未响应)')
        down_video(bv_value, s2, path_)
        messagebox.showinfo('SCUUESS', '视频已存储在桌面Down_bilibili->down_video')
    except:
        messagebox.showinfo('ERROR', "输入的链接不合法")


if __name__ == '__main__':
    res_path = create_down_bilibili_folder()
    path_bilibili = res_path[0]
    temp_cookie = res_path[1]
    root = Tk()
    v1 = StringVar()
    with open(temp_cookie, 'r', encoding='utf-8') as f:
        bzcookie = f.read()
    try:
        bili_jct = findall(r'bili_jct=(.*?);', bzcookie)[0]
    except Exception as e:
        print(e)

    disable_warnings()
    session1 = session()
    root.geometry('362x357')  # 调整窗口大小以适应新的控件
    root.title("B站视频下载   By_I6xn")

    thread_it(bz_login)

    btn1 = Button(root, width=8, text='注销登录', command=cancel_login)
    btn1.grid(row=4, column=2)  # 设置注销登录按钮的位置

    # 新增的文本框和按钮放在注销登录按钮下面
    entry_bv = Entry(root, width=20)  # 创建文本框
    entry_bv.insert(0, "输入视频链接 Ctrl+V粘贴")  # 设置提示文本
    entry_bv.bind("<FocusIn>", lambda args: entry_bv.delete('0', 'end'))  # 点击时清除提示文本
    entry_bv.grid(row=5, column=2, pady=5)  # 放置文本框在注销登录按钮下方
    btn_get_bv = Button(root, width=10, text='提交', command=partial(get_bv_value, entry_bv, session1, path_bilibili))
    btn_get_bv.grid(row=6, column=2, pady=5)  # 放置按钮在文本框下方
    label_ver2 = Label(root, textvariable=v1)
    label_ver2.grid(row=9, column=1, rowspan=8, columnspan=1, sticky='n')
    root.mainloop()
