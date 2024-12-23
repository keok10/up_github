# AWS LAMBDA
import tweepy
import requests
from bs4 import BeautifulSoup
import os
import json
import re
from datetime import datetime
import pandas as pd
import random
import numpy as np
import logging

# JSONファイルからAPIキーを読み込む関数
def load_twitter_keys(json_file):
    try:
        with open(json_file, 'r') as file:
            keys = json.load(file)
        print("Twitter keys loaded successfully.")
        return keys
    except Exception as e:
        print(f"Error loading Twitter keys: {e}")
        raise e

# キーをロード
keys = load_twitter_keys('twitter_key_newsbot.json')
# keys = load_twitter_keys('twitter_keys.json')

# Tweepyを使ったTwitter認証
try:
    # v2クライアント
    twitter_client = tweepy.Client(
        bearer_token=keys['bearer_token'],
        consumer_key=keys['consumer_key'],
        consumer_secret=keys['consumer_secret'],
        access_token=keys['access_token'],
        access_token_secret=keys['access_token_secret']
    )

    # v1.1クライアント（画像アップロード用）
    auth = tweepy.OAuth1UserHandler(
        keys['consumer_key'],
        keys['consumer_secret'],
        keys['access_token'],
        keys['access_token_secret']
    )
    api_v1 = tweepy.API(auth)

    print("Twitter authentication successful.")
except Exception as e:
    print(f"Error during Twitter authentication: {e}")
    raise e

news_site = {
     '00:00':[
        'https://www.fashion-press.net/news/search/beauty',
        'https://prtimes.jp/fashion/',
        'https://follow.yahoo.co.jp/themes/09d859b7b0ad7d462236/',
    ],
     '00:30':[
        'https://prtimes.jp/topics/keywords/グッズ',
        'https://www.oricon.co.jp/news/tag/id/news_character/',
        'https://charalab.com/category/goods/',
    ],
     '01:00':[
        'https://prtimes.jp/entertainment/',
        'https://prtimes.jp/topics/keywords/カフェ',
        'https://follow.yahoo.co.jp/themes/0f949f1b2dbe62d60008/',
    ],
     '02:30':[
        'https://prtimes.jp/topics/keywords/スイーツ',
        'https://www.fashion-press.net/words/899',
        'https://www.oricon.co.jp/news/tag/id/sweets/',
        'https://follow.yahoo.co.jp/themes/0b358ef990dbb2cd5353/',
    ],
     '01:45':[
        'https://www.fashion-press.net/news/search/fashion',
        'https://www.fashionsnap.com/article/news/fashion/?category=ファッション',
        'https://prtimes.jp/topics/keywords/ファッション',
    ],
     '02:30':[
        'https://prtimes.jp/topics/keywords/アニメ',
        'https://prtimes.jp/topics/keywords/キャラクター/',
        'https://www.fashion-press.net/words/936',
        'https://news.yahoo.co.jp/search?p=キャラクター+アニメ%E3%80%80グッズ&ei=utf-8',
    ],
     '03:00':[
        'https://news.yahoo.co.jp/ranking/access/photo',
        'https://news.yahoo.co.jp/ranking/access/video',
        'https://news.mynavi.jp/ranking/digital/',
    ],
     '03:30':[
        'https://news.yahoo.co.jpcp=アニメ%E3%80%80グッズ&ei=utf-8',
        'https://prtimes.jp/topics/keywords/キャラクターグッズ',
        'https://news.mynavi.jp/ranking/digital/game/',
    ],
     '04:00':[
        'https://www.fashion-press.net/news/search/beauty',
        'https://prtimes.jp/fashion/',
        'https://follow.yahoo.co.jp/themes/09d859b7b0ad7d462236/',
    ],
     '04:30':[
        'https://prtimes.jp/topics/keywords/グッズ',
        'https://www.oricon.co.jp/news/tag/id/news_character/',
        'https://charalab.com/category/goods/',
    ],
     '05:00':[
        'https://prtimes.jp/entertainment/',
        'https://prtimes.jp/topics/keywords/カフェ',
        'https://follow.yahoo.co.jp/themes/0f949f1b2dbe62d60008/',
    ],
     '05:30':[
        'https://prtimes.jp/topics/keywords/スイーツ',
        'https://www.fashion-press.net/words/899',
        'https://www.oricon.co.jp/news/tag/id/sweets/',
        'https://follow.yahoo.co.jp/themes/0b358ef990dbb2cd5353/',
    ],
     '06:00':[
        'https://www.fashion-press.net/news/search/fashion',
        'https://www.fashionsnap.com/article/news/fashion/?category=ファッション',
        'https://prtimes.jp/topics/keywords/ファッション',
    ],
     '06:30':[
        'https://prtimes.jp/topics/keywords/アニメ',
        'https://prtimes.jp/topics/keywords/キャラクター/',
        'https://www.fashion-press.net/words/936',
        'https://news.yahoo.co.jp/search?p=キャラクター+アニメ%E3%80%80グッズ&ei=utf-8',
    ],
     '07:00':[
        'https://news.yahoo.co.jp/ranking/access/photo',
        'https://news.yahoo.co.jp/ranking/access/video',
        'https://news.mynavi.jp/ranking/digital/',
    ],
     '07:30':[
        'https://news.yahoo.co.jpcp=アニメ%E3%80%80グッズ&ei=utf-8',
        'https://prtimes.jp/topics/keywords/キャラクターグッズ',
        'https://news.mynavi.jp/ranking/digital/game/',
    ],
     '08:00':[
        'https://www.fashion-press.net/news/search/beauty',
        'https://prtimes.jp/fashion/',
        'https://follow.yahoo.co.jp/themes/09d859b7b0ad7d462236/',
    ],
     '08:30':[
        'https://prtimes.jp/topics/keywords/グッズ',
        'https://www.oricon.co.jp/news/tag/id/news_character/',
        'https://charalab.com/category/goods/',
    ],
     '09:00':[
        'https://prtimes.jp/entertainment/',
        'https://prtimes.jp/topics/keywords/カフェ',
        'https://follow.yahoo.co.jp/themes/0f949f1b2dbe62d60008/',
    ],
     '09:30':[
        'https://prtimes.jp/topics/keywords/スイーツ',
        'https://www.fashion-press.net/words/899',
        'https://www.oricon.co.jp/news/tag/id/sweets/',
        'https://follow.yahoo.co.jp/themes/0b358ef990dbb2cd5353/',
    ],
     '10:00':[
        'https://www.fashion-press.net/news/search/fashion',
        'https://www.fashionsnap.com/article/news/fashion/?category=ファッション',
        'https://prtimes.jp/topics/keywords/ファッション',
    ],
     '10:30':[
        'https://prtimes.jp/topics/keywords/アニメ',
        'https://prtimes.jp/topics/keywords/キャラクター/',
        'https://www.fashion-press.net/words/936',
        'https://news.yahoo.co.jp/search?p=キャラクター+アニメ%E3%80%80グッズ&ei=utf-8',
    ],
     '11:00':[
        'https://news.yahoo.co.jp/ranking/access/photo',
        'https://news.yahoo.co.jp/ranking/access/video',
        'https://news.mynavi.jp/ranking/digital/',
    ],
     '11:30':[
        'https://news.yahoo.co.jpcp=アニメ%E3%80%80グッズ&ei=utf-8',
        'https://prtimes.jp/topics/keywords/キャラクターグッズ',
        'https://news.mynavi.jp/ranking/digital/game/',
    ],
     '12:00':[
        'https://www.fashion-press.net/news/search/beauty',
        'https://prtimes.jp/fashion/',
        'https://follow.yahoo.co.jp/themes/09d859b7b0ad7d462236/',
    ],
     '12:30':[
        'https://prtimes.jp/topics/keywords/グッズ',
        'https://www.oricon.co.jp/news/tag/id/news_character/',
        'https://charalab.com/category/goods/',
    ],
     '13:00':[
        'https://prtimes.jp/entertainment/',
        'https://prtimes.jp/topics/keywords/カフェ',
        'https://follow.yahoo.co.jp/themes/0f949f1b2dbe62d60008/',
    ],
     '13:30':[
        'https://prtimes.jp/topics/keywords/スイーツ',
        'https://www.fashion-press.net/words/899',
        'https://www.oricon.co.jp/news/tag/id/sweets/',
        'https://follow.yahoo.co.jp/themes/0b358ef990dbb2cd5353/',
    ],
     '14:00':[
        'https://www.fashion-press.net/news/search/fashion',
        'https://www.fashionsnap.com/article/news/fashion/?category=ファッション',
        'https://prtimes.jp/topics/keywords/ファッション',
    ],
     '14:30':[
        'https://prtimes.jp/topics/keywords/アニメ',
        'https://prtimes.jp/topics/keywords/キャラクター/',
        'https://www.fashion-press.net/words/936',
        'https://news.yahoo.co.jp/search?p=キャラクター+アニメ%E3%80%80グッズ&ei=utf-8',
    ],
     '15:00':[
        'https://news.yahoo.co.jp/ranking/access/photo',
        'https://news.yahoo.co.jp/ranking/access/video',
        'https://news.mynavi.jp/ranking/digital/',
    ],
     '15:30':[
        'https://news.yahoo.co.jpcp=アニメ%E3%80%80グッズ&ei=utf-8',
        'https://prtimes.jp/topics/keywords/キャラクターグッズ',
        'https://news.mynavi.jp/ranking/digital/game/',
    ],
     '16:00':[
        'https://www.fashion-press.net/news/search/beauty',
        'https://prtimes.jp/fashion/',
        'https://follow.yahoo.co.jp/themes/09d859b7b0ad7d462236/',
    ],
     '16:30':[
        'https://prtimes.jp/topics/keywords/グッズ',
        'https://www.oricon.co.jp/news/tag/id/news_character/',
        'https://charalab.com/category/goods/',
    ],
     '17:00':[
        'https://prtimes.jp/entertainment/',
        'https://prtimes.jp/topics/keywords/カフェ',
        'https://follow.yahoo.co.jp/themes/0f949f1b2dbe62d60008/',
    ],
     '17:30':[
        'https://prtimes.jp/topics/keywords/スイーツ',
        'https://www.fashion-press.net/words/899',
        'https://www.oricon.co.jp/news/tag/id/sweets/',
        'https://follow.yahoo.co.jp/themes/0b358ef990dbb2cd5353/',
    ],
     '18:00':[
        'https://www.fashion-press.net/news/search/fashion',
        'https://www.fashionsnap.com/article/news/fashion/?category=ファッション',
        'https://prtimes.jp/topics/keywords/ファッション',
    ],
     '18:30':[
        'https://prtimes.jp/topics/keywords/アニメ',
        'https://prtimes.jp/topics/keywords/キャラクター/',
        'https://www.fashion-press.net/words/936',
        'https://news.yahoo.co.jp/search?p=キャラクター+アニメ%E3%80%80グッズ&ei=utf-8',
    ],
     '19:00':[
        'https://news.yahoo.co.jp/ranking/access/photo',
        'https://news.yahoo.co.jp/ranking/access/video',
        'https://news.mynavi.jp/ranking/digital/',
    ],
     '19:30':[
        'https://news.yahoo.co.jpcp=アニメ%E3%80%80グッズ&ei=utf-8',
        'https://prtimes.jp/topics/keywords/キャラクターグッズ',
        'https://news.mynavi.jp/ranking/digital/game/',
    ],
     '20:00':[
        'https://www.fashion-press.net/news/search/beauty',
        'https://prtimes.jp/fashion/',
        'https://follow.yahoo.co.jp/themes/09d859b7b0ad7d462236/',
    ],
     '20:30':[
        'https://prtimes.jp/topics/keywords/グッズ',
        'https://www.oricon.co.jp/news/tag/id/news_character/',
        'https://charalab.com/category/goods/',
    ],
     '21:00':[
        'https://prtimes.jp/entertainment/',
        'https://prtimes.jp/topics/keywords/カフェ',
        'https://follow.yahoo.co.jp/themes/0f949f1b2dbe62d60008/',
    ],
     '21:30':[
        'https://prtimes.jp/topics/keywords/スイーツ',
        'https://www.fashion-press.net/words/899',
        'https://www.oricon.co.jp/news/tag/id/sweets/',
        'https://follow.yahoo.co.jp/themes/0b358ef990dbb2cd5353/',
    ],
     '22:00':[
        'https://www.fashion-press.net/news/search/fashion',
        'https://www.fashionsnap.com/article/news/fashion/?category=ファッション',
        'https://prtimes.jp/topics/keywords/ファッション',
    ],
     '22:30':[
        'https://prtimes.jp/topics/keywords/アニメ',
        'https://prtimes.jp/topics/keywords/キャラクター/',
        'https://www.fashion-press.net/words/936',
        'https://news.yahoo.co.jp/search?p=キャラクター+アニメ%E3%80%80グッズ&ei=utf-8',
    ],
     '23:00':[
        'https://news.yahoo.co.jp/ranking/access/photo',
        'https://news.yahoo.co.jp/ranking/access/video',
        'https://news.mynavi.jp/ranking/digital/',
    ],
     '23:30':[
        'https://news.yahoo.co.jpcp=アニメ%E3%80%80グッズ&ei=utf-8',
        'https://prtimes.jp/topics/keywords/キャラクターグッズ',
        'https://news.mynavi.jp/ranking/digital/game/',
    ],
}

df = pd.DataFrame(dict([(k, pd.Series(v)) for k, v in news_site.items()]))
display(df)

# 辞書内の適切な時間帯を出す。
def get_current_time_slot():
    now = datetime.now()
    current_time = now.strftime('%H:%M')
    for time in news_site.keys():
        if current_time >= time and current_time < (datetime.strptime(time, "%H:%M") + pd.Timedelta(minutes=30)).strftime("%H:%M"):
            print(f"Current time slot: {time}")
            return time
    print("No matching time slot found.")        
    return None

# スクレイピングのURLをランダムに選択
def select_random_url():
    time_slot = get_current_time_slot()
    if time_slot:
        selected_url = df[time_slot].dropna().sample().values[0]
        print(f"Selected URL: {selected_url}")
        return selected_url
    else:
        print("No URL selected.")
        return None

# スクレイピングを行う関数
def scrape_news(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    img_tag = None
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # HTTPステータスコードが4xx/5xxの場合に例外を発生させる
        soup = BeautifulSoup(response.content, 'html.parser')
        news_data = {}
        
        if 'prtimes.jp' in url:
            if 'entertainment' in url or 'fashion' in url:
                article = soup.find('article', class_="list-article")
                title_tag = article.find('h3', class_='list-article__title')
                link_tag = article.find('a', class_='list-article__link')

                # 詳細ページのリンクを取得
                detail_url = link_tag['href'] if link_tag else None
                if detail_url and not detail_url.startswith('http'):
                    detail_url = "https://prtimes.jp" + detail_url  # 相対URLを絶対URLに変換

                # 詳細ページにアクセスして大きな画像を取得
                if detail_url:
                    detail_response = requests.get(detail_url, headers=headers)
                    detail_response.raise_for_status()
                    detail_soup = BeautifulSoup(detail_response.content, 'html.parser')
                    img_tag = detail_soup.find('img')
                    img_url = img_tag['src'] if img_tag else None
                      
            elif '/アニメ' in url:
                article = soup.find('article', class_='item item-ordinary')
                title_tag = article.find('h3', class_='title-item')  # 修正箇所
                link_tag = article.find('a', class_='link-title-item')
                
                #画像URLをstyle属性から取得
                style = article.find('a', class_='link-thumbnail')['style']
                img_url = re.search(r'url\((.*?)\)', style).group(1)
                
                #img_tagを作成
                soup = BeautifulSoup('<img src="{}">'.format(img_url), 'html.parser')
                img_tag = soup.find('img')
            
            elif '/カフェ' in url:
                article = soup.find('article', class_='item item-ordinary')
                title_tag = article.find('h3', class_='title-item')  # 修正箇所
                link_tag = article.find('a', class_='link-title-item')
                
                #画像URLをstyle属性から取得
                style = article.find('a', class_='link-thumbnail')['style']
                img_url = re.search(r'url\((.*?)\)', style).group(1)
                
                #img_tagを作成
                soup = BeautifulSoup('<img src="{}">'.format(img_url), 'html.parser')
                img_tag = soup.find('img')

            elif '/キャラクター/' in url:
                article = soup.find('article', class_='item item-ordinary')
                title_tag = article.find('h3', class_='title-item')  # 修正箇所
                link_tag = article.find('a', class_='link-title-item')
                
                # 画像URLをstyle属性から取得
                style = article.find('a', class_='link-thumbnail')['style']
                img_url = re.search(r'url\((.*?)\)', style).group(1)
                
                # img_tagを作成
                soup = BeautifulSoup('<img src="{}">'.format(img_url), 'html.parser')
                img_tag = soup.find('img')
                
            elif '/キャラクターグッズ' in url:
                article = soup.find('article', class_='item item-ordinary')
                title_tag = article.find('h3', class_='title-item')  # 修正箇所
                link_tag = article.find('a', class_='link-title-item')
                
                # 画像URLをstyle属性から取得
                style = article.find('a', class_='link-thumbnail')['style']
                img_url = re.search(r'url\((.*?)\)', style).group(1)
                
                # img_tagを作成
                soup = BeautifulSoup('<img src="{}">'.format(img_url), 'html.parser')
                img_tag = soup.find('img')
            elif '/グッズ' in url:
                article = soup.find('article', class_='item item-ordinary')
                title_tag = article.find('h3', class_='title-item')  # 修正箇所
                link_tag = article.find('a', class_='link-title-item')
                
                # 画像URLをstyle属性から取得
                style = article.find('a', class_='link-thumbnail')['style']
                img_url = re.search(r'url\((.*?)\)', style).group(1)
                
                # img_tagを作成
                soup = BeautifulSoup('<img src="{}">'.format(img_url), 'html.parser')
                img_tag = soup.find('img')
            elif '/スイーツ' in url:
                article = soup.find('article', class_='item item-ordinary')
                title_tag = article.find('h3', class_='title-item')  # 修正箇所
                link_tag = article.find('a', class_='link-title-item')
                
                # 画像URLをstyle属性から取得
                style = article.find('a', class_='link-thumbnail')['style']
                img_url = re.search(r'url\((.*?)\)', style).group(1)
                
                # img_tagを作成
                soup = BeautifulSoup('<img src="{}">'.format(img_url), 'html.parser')
                img_tag = soup.find('img')
            elif '/ファッション' in url:
                article = soup.find('article', class_='item item-ordinary')
                title_tag = article.find('h3', class_='title-item')  # 修正箇所
                link_tag = article.find('a', class_='link-title-item')
                
                # 画像URLをstyle属性から取得
                style = article.find('a', class_='link-thumbnail')['style']
                img_url = re.search(r'url\((.*?)\)', style).group(1)
                
                # img_tagを作成
                soup = BeautifulSoup('<img src="{}">'.format(img_url), 'html.parser')
                img_tag = soup.find('img')
            elif '/ホテル' in url:
                article = soup.find('article', class_='item item-ordinary')
                title_tag = article.find('h3', class_='title-item')  # 修正箇所
                link_tag = article.find('a', class_='link-title-item')
                
                # 画像URLをstyle属性から取得
                style = article.find('a', class_='link-thumbnail')['style']
                img_url = re.search(r'url\((.*?)\)', style).group(1)
                
                # img_tagを作成
                soup = BeautifulSoup('<img src="{}">'.format(img_url), 'html.parser')
                img_tag = soup.find('img')
            elif '/旅館' in url:
                article = soup.find('article', class_='item item-ordinary')
                title_tag = article.find('h3', class_='title-item')  # 修正箇所
                link_tag = article.find('a', class_='link-title-item')
                
                # 画像URLをstyle属性から取得
                style = article.find('a', class_='link-thumbnail')['style']
                img_url = re.search(r'url\((.*?)\)', style).group(1)
                
                # img_tagを作成
                soup = BeautifulSoup('<img src="{}">'.format(img_url), 'html.parser')
                img_tag = soup.find('img')    
        elif 'charalab.com' in url:
            if 'goods/' in url:
                article = soup.find('article')
                title_tag = article.find('div', class_='article-list_title').find('p')
                link_tag = article.find('a')     
                # 画像タグを取得
                img_tag = article.find('div', class_='article-list_img').find('img')
                
        elif 'follow.yahoo.co.jp' in url:
            article = soup.find('li', class_='ThemeArticleItem_ThemeArticleItem__1dU5j')
            title_tag = article.find('h2', class_='ThemeArticleItem_ThemeArticleItem__title__kM0El')
            link_tag = article.find('a', class_='ThemeArticleItem_ThemeArticleItem__anchor__GfZIe')

        elif 'news.biglobe.ne.jp' in url:
            if 'スイーツ' in url: 
                article = soup.find('li')
                title_tag = article.find('p', class_='kw-title')
                link_tag = article.find('a')
                # 画像URLをstyle属性から取得
                img_style = article.find('div', class_='img')['style']
                img_url = re.search(r'url\((.*?)\)', img_style).group(1)        
                # img_tagを作成
                soup_img = BeautifulSoup('<img src="{}">'.format(img_url), 'html.parser')
                img_tag = soup_img.find('img')
                
        elif 'https://news.yahoo.co.jp/search' in url:
            if 'キャラクター+アニメ' in url: 
                article = soup.find('li', class_='newsFeed_item')
                title_tag = article.find('div', class_='newsFeed_item_title')
                link_tag = article.find('a', class_='sc-110wjhy-2')        
                img_tag = article.find('img', class_='sc-1z2z0a-1')
                
            if '=アニメ%' in url: 
                article = soup.find('li', class_='newsFeed_item')
                title_tag = article.find('div', class_='newsFeed_item_title')
                link_tag = article.find('a', class_='sc-110wjhy-2')        
                img_tag = article.find('img', class_='sc-1z2z0a-1')
                
        elif 'https://news.yahoo.co.jp/ranking/access' in url:
            article = soup.find('li', class_='newsFeed_item')
            title_tag = article.find('div', class_='newsFeed_item_title')
            link_tag = article.find('a', class_='newsFeed_item_link')
            img_tag = article.find('picture').find('img', class_='sc-1z2z0a-1')
            
        elif 'fashion-press.net' in url:
            article = soup.find('div', class_='fp_list_each')
            title_tag = article.find('h3').find('a')
            link_tag = article.find('a', href=True)

            # 新しいページのHTMLから画像を取得するためにリクエストを送信
            article_url = link_tag['href']
            if not article_url.startswith('http'):
                article_url = "https://www.fashion-press.net" + article_url

            article_response = requests.get(article_url, headers=headers)
            article_response.raise_for_status()
            article_soup = BeautifulSoup(article_response.content, 'html.parser')
            # 1つ目の画像を取得
            img_tag = article_soup.find('figure').find('img', src=True)
            img_url = img_tag['src'] if img_tag else None

            # 相対URLを完全なURLに変換
            if img_url and not img_url.startswith('http'):
                img_url = "https://www.fashion-press.net" + img_url

            news_data['title'] = title_tag.get_text() if title_tag else 'No Title'
            news_data['url'] = article_url
            news_data['img_url'] = img_url
            print(f"Scraped news data: {news_data}")
            return news_data

        elif 'https://www.oricon.co.jp' in url:
            article = soup.find('article', class_='card cat-local')
            title_tag = article.find('h2', class_='title')
            link_tag = article.find('a', href=True)
            
        elif 'https://news.mynavi.jp/ranking/digital/game/' in url:
            article = soup.find('div', class_='rankingtList_listNode_info')
            title_tag = article.find('h3', class_='rankingtList_listNode_catch')
            link_tag = article.find_parent('a', href=True)  # Assuming the link is in the parent <a> tag
            img_tag = None  # No image tag is provided in the given HTML structure

        elif 'https://news.mynavi.jp/ranking/digital/' in url:
            article = soup.find('div', class_='rankingtList_listNode_info')
            title_tag = article.find('h3', class_='rankingtList_listNode_catch')
            link_tag = article.find_parent('a', href=True)  # Assuming the link is in the parent <a> tag
            img_tag = None  # No image tag is provided in the given HTML structure

        elif 'https://www.fashionsnap.com/article/news/fashion/?category' in url:
            article = soup.find('div', class_='_144h2oc0')
            title_tag = article.find('p', class_='_144h2oc1')
            link_tag = article.find('a', class_='_120s2jp0', href=True)
            #¥img_tag = article.find('img', class_='_120s2jp1')

        else:
            print("No matching site pattern found.")
            article = []

        # ベースURLを現在処理中のURLから動的に取得
        base_url = re.match(r'https?://[^/]+', url).group(0)
        print(f"base_url:{base_url}")
        title = title_tag.get_text().strip() if title_tag else 'No Title Found'
        
        if title_tag:
            print(f"title_tag: {title_tag.get_text().strip()}")

        link = link_tag['href'] if link_tag else 'No Link Available'
        if link_tag:
            print(f"link: {link}")

        # 相対URLを絶対URLに変換
        if not link.startswith('http'):
            link = base_url + link
        print(f"Converted link: {link}")  # Debug line to check the converted link

        # 画像がある場合のみURLを取得
        img_url = None
        if img_tag:
            img_url = img_tag['src']
            if not img_url.startswith('http'):
                img_url = base_url + img_url
            print(f"img_url: {img_url}")

        # ニュースデータの辞書を作成
        news_data['title'] = title
        news_data['url'] = link
        if img_url:
            news_data['img_url'] = img_url

        return news_data
    except Exception as e:
        print(f"Error scraping news: {e}")
        return None

    def resize_image(image_path, max_size=5 * 1024 * 1024):
        """Resize image to be under the max size (in bytes)."""
        with Image.open(image_path) as img:
            if img.size[0] * img.size[1] > max_size:
                scale_factor = (max_size / (img.size[0] * img.size[1])) ** 0.5
                new_size = (int(img.size[0] * scale_factor), int(img.size[1] * scale_factor))
                img = img.resize(new_size, Image.ANTIALIAS)
                img.save(image_path, optimize=True, quality=85)
    
        return image_path

# main()の実装
def main():
    # 必要なJSONファイル名を指定してキーをロード
    twitter_keys = load_twitter_keys('twitter_keys.json')
    if not twitter_keys:
        print("Twitter keys not loaded.")
        return

    # URLをランダムに選択
    url = select_random_url()
    if not url:
        print("No URL selected.")
        return

    # ニュースをスクレイピング
    news_data = scrape_news(url)
    if news_data:
        title = news_data['title']
        link = news_data['url']
        img_url = news_data.get('img_url')
        post_content = f"{title}\n{link}"
        print(f"post_content:{post_content}")

        try:
            if img_url:
                # 画像をダウンロードして一時保存
                image_path = '/tmp/news_image.jpg'
                with open(image_path, 'wb') as img_file:
                    img_file.write(requests.get(img_url).content)
                
                # 画像をアップロードしてツイート投稿
                try:
                    media = api_v1.media_upload(image_path)
                    twitter_client.create_tweet(text=post_content, media_ids=[media.media_id])
                    print(f"Posted with image: {post_content}")
                    
                    # 使用した画像を削除
                    os.remove(image_path)
                except tweepy.TweepyException as e:
                    print(f"Error posting tweet with image: {e}")
            else:
                # 画像なしのツイート投稿
                twitter_client.create_tweet(text=post_content)
                
                print(f"Posted: {post_content}")
        except Exception as e:
            print(f"Unexpected error: {e}")
    else:
        print("No news data found.")


if __name__ == "__main__":
    main()
