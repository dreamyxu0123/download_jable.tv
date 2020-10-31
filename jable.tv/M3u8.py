import requests
from config import headers
from utils import log, save
from bs4 import BeautifulSoup as bs
import m3u8


class M3u8():
    def __init__(self, page_url, dirname):
        self.page_url = page_url
        self.url_prefix = ''
        self.m3u8_path = dirname + '/' + 'm3u8.m3u8'
        self.dirname = dirname
        self.link = ''
        self.m3u8_link()

    def set_url_prefix(self, link):
        url_list = link.split('/')
        url_list.pop(-1)
        self.url_prefix = '/'.join(url_list)
        log(url_list)
        log(link)
        log(self.url_prefix)

    def m3u8_link(self):
        response = requests.get(self.page_url, headers=headers, timeout=10)
        log('response', response)
        soup = bs(response.text, 'lxml')
        r = soup.find_all('link', href=True)
        link = r[-1]['href']
        self.set_url_prefix(link)
        self.link = link

    def download_m3u8_file(self):
        log('m3u8_link', self.link)
        response = requests.get(self.link, headers=headers, timeout=10)
        if response.status_code == 200:
            save(self.m3u8_path, response.content)
        else:
            raise Exception("not 200")

        # print(response.text)
        # print(response.content)

    def download_m3u8_key(self):
        m3u8_obj = m3u8.load(self.m3u8_path)
        for key in m3u8_obj.keys:
            if key:  # First one could be None
                link = self.url_prefix + '/' + key.uri
                key_filename = key.uri[0:-3] + '.key'
                response = requests.get(link, headers=headers, timeout=10)
                save(self.dirname + '/' + key_filename, response.content)

    def m3u8_url_list(self):
        m3u8_obj = m3u8.load(self.m3u8_path)
        uri_list = []
        for seg in m3u8_obj.segments:
            uri = self.url_prefix + '/' + seg.uri
            uri_list.append(uri)
        return uri_list
