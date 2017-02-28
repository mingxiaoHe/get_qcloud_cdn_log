#!/usr/bin/env python
# coding=utf-8

import hashlib
import requests
import hmac
import random
import time
import base64
import json
import gzip
import os
import sys
from datetime import datetime, timedelta

class Sign(object):

    def __init__(self, secretId, secretKey):
        self.secretId = secretId
        self.secretKey = secretKey

    # 生成签名串
    def make(self, requestHost, requestUri, params, method='GET'):
        srcStr = method.upper() + requestHost + requestUri + '?' + "&".join(k.replace("_",".") + "=" + str(params[k]) for k in sorted(params.keys()))
        hashed = hmac.new(self.secretKey, srcStr, hashlib.sha1)
        return base64.b64encode(hashed.digest())

class CdnHelper(object):
    SecretId='AKIDLVQ5UexSSSDFSLDKJFLSFJDSO5XoGiY9'
    SecretKey='SeaHjvra3sdfsdfsdfFJ7rMiz0lGV'
    requestHost='cdn.api.qcloud.com'
    requestUri='/v2/index.php'

    def __init__(self, host, startDate, endDate):
        self.host = host
        self.startDate = startDate
        self.endDate = endDate
        self.params = {
            'Timestamp': int(time.time()),
            'Action': 'GetCdnLogList',
            'SecretId': CdnHelper.SecretId,
            'Nonce': random.randint(10000000,99999999),
            'host': self.host,
            'startDate': self.startDate,
            'endDate': self.endDate
        }
        self.params['Signature'] =  Sign(CdnHelper.SecretId, CdnHelper.SecretKey).make(CdnHelper.requestHost, CdnHelper.requestUri, self.params)
        self.url = 'https://%s%s' % (CdnHelper.requestHost, CdnHelper.requestUri)


    def GetCdnLogList(self):
        ret = requests.get(self.url, params=self.params)
        return ret.json()


class GZipTool(object):
    """
    压缩与解压gzip
    """
    def __init__(self, bufSize = 1024*8):
        self.bufSize = bufSize
        self.fin = None
        self.fout = None
    def compress(self, src, dst):
        self.fin = open(src, 'rb')
        self.fout = gzip.open(dst, 'wb')
        self.__in2out()
    def decompress(self, gzFile, dst):
        self.fin = gzip.open(gzFile, 'rb')
        self.fout = open(dst, 'wb')
        self.__in2out()
    def __in2out(self,):
        while True:
            buf = self.fin.read(self.bufSize)
            if len(buf) < 1:
                break
            self.fout.write(buf)
        self.fin.close()
        self.fout.close()
    
def download(link, name):
    try:
        r = requests.get(link)
        with open(name, 'wb') as f:
            f.write(r.content)
        return True
    except:
        return False


def writelog(src, dst):
    # 保存为以天命名日志
    dst = dst.split('-')[0][:-2] + '-' + dst.split('-')[1]
    with open(src, 'r') as f1:
       with open(dst, 'a+') as f2:
        for line in f1:
            f2.write(line)

if __name__ == '__main__':
    #startDate = "2017-02-23 12:00:00"
    #endDate = "2017-02-23 12:00:00"

    # 前一小时
    # startDate = endDate = time.strftime('%Y-%m-%d ', time.localtime()) + str(time.localtime().tm_hour-1) + ":00:00"
    tm = datetime.now() + timedelta(hours=-2)
    startDate = endDate = tm.strftime("%Y-%m-%d %H:00:00")


    #hosts = ['userface.51XXX.com']
    hosts = [ 
        'pfcdn.51XXX.com',
        'pecdn.51XXX.com',
        'pdcdn.51XXX.com',
        ]                

    for host in hosts:
        try:
            obj = CdnHelper(host, startDate,endDate)
            ret = obj.GetCdnLogList()

            link = ret['data']['list'][0]['link']
            name = ret['data']['list'][0]['name']

            # 下载链接保存的文件名
            gzip_name = '/data/logs/cdn/cdn_log_temp/' + name + '.gz'
            # 解压后的文件名
            local_name = '/data/logs/cdn/cdn_log_temp/' + name + '.log'
            # 追加的文件名
            real_path = '/data/logs/cdn/' + name + '.log'
            print local_name, real_path

            status = download(link, gzip_name)
            if status:
                try:
                    GZipTool().decompress(gzip_name, local_name) 
                    writelog(local_name, real_path)
    #                os.remove(gzip_name)
                    os.remove(local_name)
                except:
                    continue
        except Exception ,e:
            print e
            continue
