# -*- coding:utf-8 -*-
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys 
import time 
import pyperclip
from urllib.request import urlopen, Request
import json
import os
import pandas as pd
from bs4 import BeautifulSoup
import requests
from urllib.parse import urlparse, parse_qs

Chrome_Driver = "/Users/hwsung/Desktop/crawl/chromedriver" ## 크롬드라이버 경로
now_dirname = os.path.dirname(os.path.abspath(__file__))


## 크롬드라이버 셋팅
options = webdriver.ChromeOptions()
options.add_experimental_option('excludeSwitches', ['enable-logging'])
options.add_argument('window-size=1920x1080')
options.add_argument('headless')
options.add_argument("disable-gpu")
options.add_argument("lang=ko-KR")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko")
driver = webdriver.Chrome(Chrome_Driver, options=options)

## 네이버 포스트 수집 리스트
maskedId = [] ## 마스킹된 아이디
UserId = [] ## 네이버 고객식별자(숫자형태)
temp_UserId = []
naverID =[] ## 실제 네이버 아이디
realUrl = [] ## json 파일 경로

def login() :
    ## 로그인하기
    url = "https://nid.naver.com/nidlogin.login"
    driver.get(url)
    login = {
        "id" : "", ## 네이버 아이디
        "pw" : "!" ## 네이버 패스워드
    }
    def clipboard_input(user_xpath, user_input): ## 클립보드 복사 & 붙여넣기 형태로 로그인
        temp_user_input = pyperclip.paste()
        pyperclip.copy(user_input)
        driver.find_element_by_xpath(user_xpath).click()
        ActionChains(driver).key_down(Keys.COMMAND).send_keys('v').key_up(Keys.COMMAND).perform()

        pyperclip.copy(temp_user_input)
        time.sleep(1)
    # id, pw 입력 후 클릭
    clipboard_input('//*[@id="id"]', login.get("id"))
    clipboard_input('//*[@id="pw"]', login.get("pw"))
    driver.find_element_by_xpath('//*[@id="log.login"]').click()
    time.sleep(0.1)

login()
# 포스트 댓글 어드민 들어가기
driver.get("https://post.naver.com/viewer/commentsAdmin.naver") ## 네이버 포스트 댓글 어드민 접속
time.sleep(1)
cookies = ''
## 로그인 후 어드민 페이지의 쿠키 획득 후 넣어주기  

print('더보기 누르기 시작')
## 네이버 api는 세션 당 1,000개씩 수집 가능 
## for 문을 2번 돌려 1000개씩 끊으려 했지만 실패함(쿠키 재설정/resession/재로그인 등 다안됨)
for j in range(0,1):
    for i in range(0,100): ## 10개씩 100번
        try:
            driver.find_element_by_xpath('//*[@id="cbox_module"]/div[1]/div[3]/a').click()
        except:
            break
        print('더보기',i+1,'번 완료')
        time.sleep(0.1)
    print('더보기 누르기 완료')

    ## Json 파일에서 name 부분 파싱 후 네이버 id 크롤링 할 수 있는 url 추출
    performance_data = driver.execute_script("return window.performance.getEntries()")
    performance_data = json.dumps(performance_data, indent=4)
    performance_data_loads = json.loads(performance_data)
    print(len(performance_data_loads))

    print('json 파일 파싱 시작')
    for name in performance_data_loads:
        api = 'https://apis.naver.com'
        for num in name:
            if api in str(name[num]):
                if name[num] not in realUrl:
                    realUrl.append(name[num])
                    
    print('json 파일 파싱 완료')
    print('################################################################')
    print('\n')
    realUrl = pd.DataFrame(realUrl)
    realUrl.to_excel('realUrl.xlsx')

    ## Requests 할 때 반드시 함께 보내줘야 하는 헤더부분
    headers = {
        'Referer': 'https://m.post.naver.com/viewer/commentsAdmin.naver',
        'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36',
        'accept' : "*/*",
        'accept-encoding' : 'gzip, deflate, br',
        'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'cookie' : cookies,
        }

    print('마스킹아이디&유저아이디 추출 시작')
    for url in realUrl :
        try:
            url_param = parse_qs(urlparse(url).query)
            url0 ='https://apis.naver.com/commentBox/cbox/web_naver_manager_list_jsonp.json?'
            callback = str(url_param['_callback']).replace('[','').replace(']', '').replace("'","")
            #print('callback:' , callback)
            params = {}
            res = requests.get(url0, headers = headers, params=url_param).text
            res = res.replace(callback, '').replace('(','').replace(');', '')
            rank_json = json.loads(res)['result']['commentList']
            vv2 = json.loads(res)['result']['commentList']
            for rank in vv2:
                maskedUserId=rank['maskedUserId']
                profileUserId=rank['profileUserId']
                if maskedUserId not in maskedId:
                    maskedId.append(maskedUserId)
                if profileUserId not in UserId:
                    UserId.append(profileUserId)
                    temp_UserId.append(profileUserId)
        except:
            continue
    print('마스킹아이디&유저아이디 추출 완료')
    print('추출할 아이디 갯수 : ',len(UserId))
    print('네이버아이디 추출 시작')
    cnt=1
    for i in temp_UserId:
        userUrl = 'https://post.naver.com/async/profile.naver?memberNo='+i+'&postListViewType=0&isExpertMy=true'
        headers = {
        'Referer': 'https://post.naver.com/myProfile.naver?memberNo='+i,
        'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36',
        'accept' : "*/*",
        'accept-encoding' : 'gzip, deflate, br',
        'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'cookie' : cookies
        }
        req = requests.get(userUrl,headers=headers)
        bs0bj = BeautifulSoup(req.text, "html.parser").text
        a=bs0bj.find('com/')
        b=bs0bj.find('''<\/a>\\n\\t\\t\\t\\t<\/div>''')
        if str(bs0bj)[int(a)+4:int(b)] not in naverID:
            naverID.append(str(bs0bj)[int(a)+4:int(b)])
            print('네이버아이디',cnt,'번째 추출 전체 완료')
        cnt += 1
        time.sleep(0.2)
    print(temp_UserId)
    temp_UserId.clear()
    print('네이버아이디 추출 전체 완료')
    time.sleep(0.2)
list = list(zip(maskedId,UserId,naverID))
list = pd.DataFrame(list)
list.to_excel('list.xlsx')
print('전체 완료')
driver.quit()