from dotenv import load_dotenv
import os
import sys

current_dir = os.getcwd()
path = os.path.join(current_dir, '../twittergui')
sys.path.append(path)

import time
import pyautogui as pag
from time import sleep
import subprocess
import pyperclip
import urllib.parse
from bs4 import BeautifulSoup
import datetime
import csv
import copy
# .envファイルを読み込む
load_dotenv()

# 環境変数を取得
twitter_username = os.getenv('TWITTER_USERNAME')
twitter_password = os.getenv('TWITTER_PASSWORD')

# インスタンス作成時に環境変数の値を渡す
#twitter_obj = TwitterGui(3, twitter_username, twitter_password)

class TwitterGui:
    ## 共通定数
    wait_time = 4 #キーボード入力やマウス操作後の待機秒数
    #chrome_path = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'  # 修正済み

    ## ログインに関する変数
    twitter_login_url = 'https://twitter.com/i/flow/login' #Twitterのログイン画面へのURL
    twitter_url = 'https://twitter.com/' #TwitterのトップページへのURL
    is_login_check_text = '"screen_name":"' #Twitterにログイン済みかどうかを確認するための文字列(要チューニング)

    ## ツイート取得に関する変数
    twitter_search_url = 'https://twitter.com/search?q=' # ツイートの検索URL
    body_image = '/Users/kenjiokabe/x_botter_pyout/data/body-image.png'  # デベロッパーツール内の<body>の画像(要チューニング)
    target_tag = 'data-testid' # ツイート抽出用のタグ(要チューニング)
    target_tag_value = 'cellInnerDiv' # ツイート抽出用のタグ(要チューニング)
    pagedown_speed = 3 # 1回でページダウンさせる回数

    ## 関数群
    """
    コンストラクタ
      wait_time: キーボード入力やマウス操作後の待機秒数
      twitter_username: Twitterのアカウント名
      twitter_password: Twitterにログインするためのパスワード
    """
    def __init__(self, wait_time, twitter_username, twitter_password):
        self.wait_time = wait_time
        self.twitter_username = twitter_username
        self.twitter_password = twitter_password
        self.twitter_url += self.twitter_username
        
        
    """
    Twitterへログインする関数
    """
    def login_twitter(self):
        return_code = 0 # 0の場合は正常終了　1の場合は異常終了
        
        try:            
            ## Chromeを起動する
            #chrome_path = self.chrome_path
            process = subprocess.Popen(['open', '-a', 'Safari'])
 # macの場合に変更
            #process = subprocess.Popen([r"google-chrome --simulate-outdated-no-au='Tue, 31 Dec 2099 23:59:59 GMT'"], shell=True) # linuxの場合
            sleep(self.wait_time)
            is_opend_chrome = True

            ## Twitter(X)を開く
            with pag.hold('command'):
                time.sleep(1)
                pag.press('l')
                sleep(self.wait_time)

            with pag.hold('command'):
                time.sleep(1)
                pag.press('a')
                sleep(self.wait_time)
                    
            pyperclip.copy(self.twitter_url)
            with pag.hold('command'):
                time.sleep(1)
                pag.press('v')
                sleep(self.wait_time)            
            
            pag.press("enter")
            sleep(self.wait_time)
            
            ## ページのソースを表示
            pag.hotkey("command", "option","i")
            sleep(self.wait_time)
            pag.hotkey("command", "a")
            sleep(self.wait_time)
            pag.hotkey("command", "c")
            sleep(self.wait_time)
            html_src_text = pyperclip.paste()
            sleep(self.wait_time)

            ## Twitterにログイン済みか確認
            if self.is_login_check_text not in html_src_text:
                ## ログイン画面を表示
                pag.hotkey('command', "l")
                sleep(self.wait_time)

                pyperclip.copy(self.twitter_login_url)
                pag.hotkey("command", "v")
                sleep(self.wait_time)
                pag.press("enter")
                sleep(self.wait_time)

                ## アカウント名の入力欄に移動
                for i in range(0,3):
                    pag.hotkey("tab")
                    sleep(self.wait_time)

                ## アカウント名を入力
                pyperclip.copy(self.twitter_username)
                pag.hotkey("command", "v")
                sleep(self.wait_time)
                pag.press("enter")
                sleep(self.wait_time)

                ## パスワードを入力
                pag.hotkey("command", "a")
                sleep(self.wait_time)
                pyperclip.copy(self.twitter_password)
                pag.hotkey("command", "v")
                sleep(self.wait_time)
                pag.press("enter")
                sleep(self.wait_time)

                ## プロフィール画面へ移動
                pag.hotkey('command', "l")
                sleep(self.wait_time)

                pag.hotkey('command', "a")
                sleep(self.wait_time)

                pyperclip.copy(self.twitter_url)
                pag.hotkey("command", "v")
                sleep(self.wait_time)

                pag.press("enter")
                sleep(self.wait_time)
            else:
                pag.hotkey('command', "w")

        except Exception as e:
            print(e)
            return_code = 1
            # Chromeを起動した場合は閉じる
            if is_opend_chrome == True:
                pag.FAILSAFE = False
                #macではこの行は不要
                #pag.moveTo(0,0)
                pag.hotkey('command', "q")
        return return_code        

    """
    HTMLからツイートを抽出する関数
      body_html: 抽出対象となるHTML
    """
    def extract_tweet_from_html(self, body_html):
        tweet_list = []
        
        # ツイート情報が記載されたタグ抽出
        soup = BeautifulSoup(body_html, 'lxml')
        tag_list = soup.find_all(attrs={self.target_tag: self.target_tag_value})
        
        # 各タグからツイート情報を抽出
        for tag in tag_list:
          tmp_list = []
          
          try:
            user_name = tag.find('span').text # アカウント名を抽出
            user_id = tag.find('a')['href'] # アカウントIDを抽出
            tweet_time = tag.find('time')['datetime'] # 投稿時刻を抽出
            tweet_url = tag.find_all('a')[3]['href'] # ツイートURLを抽出
            tweet_text = tag.find(attrs={'data-testid': "tweetText"}).text # ツイート内容を抽出
         
            tmp_list.append(user_name)
            tmp_list.append(user_id)
            tmp_list.append(tweet_time)
            tmp_list.append(tweet_url)
            tmp_list.append(tweet_text)
            tweet_list.append(tmp_list)
          
          except:
            pass

        return tweet_list

    """
    デベロッパーツールを開きbodyソースを抽出する関数
    """
    def extract_body_by_devtool(self):
        ## デベロッパーツールを起動
        pag.hotkey("command", "option", "i")
        sleep(self.wait_time)
        
        # <body>をクリック
        time.sleep(2)  # 2秒待機
        p = pag.locateOnScreen(self.body_image, confidence=0.4)
        x, y = pag.center(p)
        pag.click(x, y)
        sleep(self.wait_time)
        
        ## デベロッパーツール内から<body>をコピー
        pag.hotkey("command", "c")
        sleep(self.wait_time)

        ## デベロッパーツールを終了
        pag.hotkey("command", "option", "i")
        sleep(self.wait_time)
             
        ## クリップボードを変数に格納
        body_html = pyperclip.paste()
        
        return body_html

    """
    検索したツイート一覧を抽出する関数
      search_condition: ツイートの検索条件　例）#python  OR #駆け出しエンジニア
      max_tweet_num: 取得する最大ツイート数
    """
    max_tweet_num = 30
    
    def extract_search_tweets(self, search_condition, max_tweet_num):
        search_tweet_dict = {} # 抽出したブックマーク格納用 key:ツイートのURL value:[アカウント名, ツイート時刻, ツイートURL, ツイート内容]
        old_search_tweet_dict = {} # 比較用
        extracted_tweets_count = 0  # 抽出したツイートの数を追跡
        
        # Twitterの画面を開く
        return_code = self.login_twitter()

        if return_code == 0:
            # アドレスバーにフォーカスしツイートを検索
            pag.hotkey('command', "l")
            sleep(self.wait_time)

            pag.hotkey('command', "a")
            sleep(self.wait_time)

            access_url = self.twitter_search_url + urllib.parse.quote(search_condition) + '&src=typed_query&f=live'
            pyperclip.copy(access_url)
            pag.hotkey("command", "v")
            sleep(self.wait_time)

            pag.press("enter")
            sleep(self.wait_time*2)

            # max_tweet_numに設定した数だけツイートを抽出するまでループ
            while True:                
                # デベロッパーツールを開きbodyソースを抽出
                body_html = self.extract_body_by_devtool()
                
                # ツイートを抽出
                tweet_list = self.extract_tweet_from_html(body_html)
                
                # 抽出したツイートを保存
                for data_list in tweet_list:
                    tweet_url = data_list[2]
                    if tweet_url not in search_tweet_dict:  # 重複を避ける
                        search_tweet_dict[tweet_url] = data_list
                        extracted_tweets_count += 1  # 抽出したツイート数をインクリメント
                
                # 取得情報変化なし　または　指定した数だけツイートを取得した場合、繰り返し終了
                if old_search_tweet_dict == search_tweet_dict or len(search_tweet_dict) > max_tweet_num:
                    break
                
                old_search_tweet_dict = copy.deepcopy(search_tweet_dict)
                
                # max_tweet_numに達したか、さらにツイートを取得する必要がない場合にループを抜ける
                if extracted_tweets_count >= max_tweet_num:
                    break

                # 画面をスクロール
                for i in range(self.pagedown_speed):
                    pag.press('pagedown')
                sleep(self.wait_time)

            ## Chromeを閉じる
            pag.hotkey('command', "w")

        return search_tweet_dict

if __name__ == "__main__":
    # オブジェクト作成
    twitter_obj = TwitterGui(3, twitter_username, twitter_password)

    # ツイートの検索式
    search_text = '#懸賞 OR #プレキャン OR #プレゼント企画 OR #キャンペーン OR #プレゼント'
    
    # 検索式に該当するツイートを取得する
    search_tweet_dict = twitter_obj.extract_search_tweets(search_text, 10)
    
    # 抽出したツイートをCSVファイルへ書き込み
    with open('output.csv', 'w', newline='', encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["アカウント名", "アカウントID", "投稿時刻", "URL", "内容"])
        for key, data_list in search_tweet_dict.items():
            writer.writerow(data_list)


