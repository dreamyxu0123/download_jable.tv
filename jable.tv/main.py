import requests
import os
import threading
import m3u8
import shutil
from M3u8 import M3u8
from binascii import hexlify, unhexlify
from utils import log, save
from threading import Lock
from Crypto.Cipher import AES
from config import headers
from hex import read_hex_file


completion_number = 0
total = 0
lo = Lock()
maxthreads = 30
sema = threading.Semaphore(value=maxthreads)
fail_urls = []


def create_dir(url):
    url_list = url.split('/')
    dirname = url_list[-2]
    path = dirname
    if not os.path.exists(path):
        os.makedirs(path)
    return dirname


def read_key_and_iv(dirname):
    m3u8_path = dirname + '/' + 'm3u8.m3u8'
    m3u8_obj = m3u8.load(m3u8_path)

    uri = ''
    iv = ''
    for key in m3u8_obj.keys:
        if key:  # First one could be None
            # print(key.uri)
            # print(key.method)
            # print(key.iv)
            uri = key.uri
            iv = key.iv
    key_file = uri[0:-3] + '.key'
    key_file = dirname + '/' + key_file

    key_bytes = read_hex_file(key_file)
    # [key, iv]
    # log('str(key_bytes), iv[2:]', str(key_bytes), iv[2:])
    return [key_bytes, iv[2:]]


def m3u8_decode(dirname, filename):
    [key, iv] = read_key_and_iv(dirname)
    log('len(key), len(iv)', len(key), len(iv))
    new_filename = '0' + filename
    cmd = f'openssl aes-128-cbc -d -in {filename} -out {new_filename} -nosalt -iv {iv[2:]} -K {key}'
    cmd = f'cd {dirname} && {cmd} '
    # log(cmd)
    os.system(cmd)
    os.remove(f'{dirname}/{filename}')


def file_list(dirname):
    for root, dirs, files in os.walk(dirname):
        # print(root)  # 当前目录路径
        # print(dirs)  # 当前路径下所有子目录
        return files


# 判断文件是否已存在
def check_file(url, dirname):
    filename = url.split('/')[-1]
    files = file_list(dirname)
    # log('filename', filename, filename in files)
    return filename in files


def thread_download(urls, dirname):
    threads = []
    l = len(urls)
    for i, url in enumerate(urls):
        # 创建线程01，不指定参数
        progress = [str(i), str(l)]
        if check_file(url, dirname) == False:
            t = threading.Thread(
                target=download, args=(url, dirname, progress))
            # 启动线程01
            threads.append(t)
            t.start()
        else:
            add_completion_number()
    for t in threads:
        t.join()


def download(url, dirname, progress):
    try:
        sema.acquire()
        response = requests.get(url, headers=headers, timeout=10)
        status_code = response.status_code
        # log('status_code', status_code)
        if status_code == 200:
            filename = url.split('/')[-1]
            decrypt_save(dirname, filename, response.content)
            # m3u8_decode(dirname, filename)
            add_completion_number()
        else:
            raise Exception("not 200")

        if url in fail_urls:
            fail_urls.remove(url)
        sema.release()
    except Exception as e:
        log(' fail_url', e, url)

        fail_urls.append(url)


def merge_m3u8(dirname, filename, sava_path):
    if not os.path.exists(sava_path):
        os.makedirs(sava_path)
    ts_filenames = []
    # Parse playlist for filenames with ending .ts and put them into the list ts_filenames
    m3u8 = f'{dirname}/m3u8.m3u8'
    with open(m3u8, 'r') as playlist:
        # ts_filenames = [line.rstrip() for line in playlist
        #                 if line.rstrip().endswith('.ts')]
        for line in playlist:
            if line.rstrip().endswith('.ts'):
                f = f'{dirname}/{line}'.rstrip()
                ts_filenames.append(f)

    # print('ts_filenames', len(ts_filenames), ts_filenames[0])
    # open one ts_file from the list after another and append them to merged.ts
    sava_path = f'{sava_path}/{filename}.ts'
    print('merge m3u8 sava path', sava_path)
    with open(sava_path, 'wb') as merged:
        for ts_file in ts_filenames:
            with open(ts_file, 'rb') as mergefile:
                shutil.copyfileobj(mergefile, merged)


def add_completion_number():
    global lo
    with lo:
        global completion_number
        global total
        # log('completion_number, total', completion_number, total)
        completion_number += 1
        percent = 'percent: {:.0%}'.format(completion_number / total)
        log(
            '\r' + str(completion_number),
            str(total),
            percent,
            end='',
            flush=True)


def decrypt_save(dirname, filename, content):
    [key, iv] = read_key_and_iv(dirname)
    # key = unhexlify('c8a9ded8b41a7daa57e224968934f86f')
    # iv = unhexlify('962ec00083ed2a46d7c1c8a8271157c3')
    key = bytes.fromhex(key)
    iv = bytes.fromhex(iv)

    # log('len key', key, len(key))
    # log('len iv', iv, len(iv))

    decipher = AES.new(key, AES.MODE_CBC, iv)
    pt = decipher.decrypt(content)
    # decrypt method parameter needs to be a multiple of 16, if not, you need to add binary "0"
    # while len(content) % 16 != 0:
    #     content += b"0"
    with open(f'{dirname}/{filename}', "wb") as file:
        file.write(pt)
        # print("save success:" + filename)


def main(page_url):
    dirname = create_dir(page_url)
    filename = dirname

    # log(filename)
    log(dirname)
    # 获取 m3u8 page_url 地址
    m = M3u8(page_url, dirname)

    # 下载m3u8文件
    m.download_m3u8_file()

    # 下载key文件
    m.download_m3u8_key()

    # 获取m3u8列表
    urls = m.m3u8_url_list()
    log('m3u8 number', len(urls))
    global total
    total = len(urls)

    # 下载所有ts文件并解密保存
    thread_download(urls, dirname)
    if len(fail_urls) > 0:
        thread_download(fail_urls, dirname)
    fs = file_list(dirname)
    log(f' {dirname} file count ', len(fs))
    merge_m3u8(dirname, filename, 'videos')


if __name__ == "__main__":
    page_url = 'https://jable.tv/videos/vec-448/'
    main(page_url)
