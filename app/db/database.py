import json
import logging
import threading
import time

import sqlalchemy
from sqlalchemy import create_engine, engine
import base64
import re

from tiktok_mobile.models.tiktok_apk import TikTokApk
from tiktok_mobile.models.tiktok_phone import TikTokPhone

from app.utils.user_search import PostInfo, UserInfo
from app.utils.utils import singleton


@singleton
class Database:

    def __init__(self):
        self.engine = create_engine('sqlite:///cached_data.db')

    def create_tables(self):
        with self.engine.connect() as con:
            con.execute('''CREATE TABLE IF NOT EXISTS devices
                   (id int primary key, apk varchar(256), install_id varchar(256), device_id varchar(256) )''')
            con.execute('''CREATE TABLE IF NOT EXISTS tiktok_accounts
                           (sec_user_id varchar(256) primary key,
                            add_time int,
                            username varchar(256))''')
            con.execute('''CREATE TABLE IF NOT EXISTS tiktok_posts
                                        (aweme_id varchar(256) primary key,
                                        add_time int,
                                        create_time int,
                                        author_sec_user_id varchar(256),
                                        cover_url varchar(1024),
                                        animated_cover_url varchar(1024),
                                        download_url_1 varchar(1024),
                                        download_url_2 varchar(1024),
                                        download_url_3 varchar(1024),
                                        play_url_1 varchar(1024),
                                        play_url_2 varchar(1024),
                                        play_url_3 varchar(1024),
                                        share_link varchar(1024),
                                        web_link varchar(1024),
                                        short_link varchar(256),
                                        comment_count int,
                                        digg_count int,
                                        download_count int,
                                        forward_count int,
                                        lose_comment_count int,
                                        lose_count int,
                                        play_count int, 
                                        share_count int,
                                        whatsapp_share_count int,
                                        description varchar(1024),
                                        earliest_urls_expire_time int )''')
            con.execute('''CREATE TABLE IF NOT EXISTS tiktok_accounts_full
                                       (sec_user_id varchar(256) primary key,
                                        add_time int,
                                        username varchar(256) unique,
                                        fullname varchar(256),
                                        followers int,
                                        following int,
                                        likes int,
                                        avatar_url varchar(1024),
                                        secret int,
                                        earliest_urls_expire_time int)''')
            con.execute('''DELETE from tiktok_posts''')
            con.execute('''DELETE from tiktok_accounts_full''')

    def insert_device(self, device: TikTokPhone):
        apk = base64.b64encode(json.dumps(device.apk).encode('ascii'))
        install_id = device.install_id
        device_id = device.device_id
        with self.engine.connect() as con:
            con.execute('''
                INSERT INTO devices (apk, install_id, device_id) VALUES (
                    ?, ?, ?)
                ''', (apk, install_id, device_id))

    def fetch_created_devices(self, size: int):
        devices = list()
        with self.engine.connect() as con:
            curs = con.execute('''
               SELECT apk, install_id, device_id FROM devices order by random() limit ?
               ''', (size,))
            rows = curs.fetchall()
            for row in rows:
                devices.append(TikTokPhone(apk=TikTokApk(json.loads(base64.b64decode(row[0]))), device_id=row[1], install_id=row[2]))

            return devices

    def cache_user_info(self, username: str, sec_uid: str):
        with self.engine.connect() as con:
            con.execute('''
                INSERT INTO tiktok_accounts (sec_user_id,
                            add_time, username) 
                VALUES (?,?,?)
                ON CONFLICT(sec_user_id) DO UPDATE SET
                    add_time = excluded.add_time,
                    username = excluded.username
                ''', (sec_uid,
                      round(time.time()),
                      username
                      ))

    def cache_user_full_info(self, user: UserInfo):
        earliest_expire_time = None
        try:
            regex = r"x-expires=(\d+)"
            earliest_expire_time = re.findall(regex, user.avatar)[0]
        except Exception as ex:
            logging.error("failed fetching urls expire date", ex)

        with self.engine.connect() as con:
            con.execute('''
                INSERT INTO tiktok_accounts_full (sec_user_id,
                            add_time, username, fullname,
                            followers, following, likes,
                            avatar_url, secret, earliest_urls_expire_time) 
                VALUES (?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(sec_user_id) DO UPDATE SET
                    add_time = excluded.add_time,
                    username = excluded.username,
                    fullname = excluded.fullname,
                    followers = excluded.followers,
                    following = excluded.following,
                    likes = excluded.likes,
                    avatar_url = excluded.avatar_url,
                    secret = excluded.secret,
                    earliest_urls_expire_time = excluded.earliest_urls_expire_time
                ''', (user.sid,
                      round(time.time()),
                      user.login_name,
                      user.name,
                      user.followers,
                      user.following,
                      user.likes,
                      user.avatar,
                      user.secret,
                      earliest_expire_time
                      ))

    def fetch_cached_sec_uid_by_username(self, username: str):
        with self.engine.connect() as con:
            curs = con.execute('''
                    SELECT sec_user_id
                    FROM tiktok_accounts
                    WHERE username=?''', (username,))
            rows = curs.fetchall()
            if len(rows) == 0:
                return None
            return rows[0][0]

    def cache_post_info(self, post: PostInfo):
        download_url_1 = None
        download_url_2 = None
        download_url_3 = None
        play_url_1 = None
        play_url_2 = None
        play_url_3 = None
        earliest_expire_time = None
        try:
            download_url_1 = post.download_links.pop()
            download_url_2 = post.download_links.pop()
            download_url_3 = post.download_links.pop()
        except Exception as ex:
            logging.error("download links length < 3. error {}".format(str(ex)))
        try:
            play_url_1 = post.play_links.pop()
            play_url_2 = post.play_links.pop()
            play_url_3 = post.play_links.pop()
        except Exception as ex:
            logging.error("play links length < 3. error {}".format(str(ex)))
        try:
            regex = r"x-expires=(\d+)"
            earliest_expire_time = re.findall(regex, post.cover)[0]
        except Exception as ex:
            logging.error("failed fetching urls expire date. error {}".format(str(ex)))

        with self.engine.connect() as con:
            con.execute('''
                INSERT INTO tiktok_posts (aweme_id, add_time, create_time, author_sec_user_id,
                    cover_url, animated_cover_url, download_url_1, download_url_2, download_url_3,
                    play_url_1, play_url_2, play_url_3, share_link, web_link, short_link,
                    comment_count, digg_count, download_count, forward_count, lose_comment_count, lose_count, 
                    play_count, share_count, whatsapp_share_count, description, earliest_urls_expire_time) 
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(aweme_id) DO UPDATE SET
                    add_time = excluded.add_time,
                    create_time = excluded.create_time,
                    cover_url = excluded.cover_url,
                    animated_cover_url = excluded.animated_cover_url,
                    download_url_1 = excluded.download_url_1,
                    download_url_2 = excluded.download_url_2,
                    download_url_3 = excluded.download_url_3,
                    play_url_1 = excluded.play_url_1,
                    play_url_2 = excluded.play_url_2,
                    play_url_3 = excluded.play_url_3,
                    comment_count = excluded.comment_count,
                    digg_count = excluded.digg_count,
                    download_count = excluded.download_count,
                    forward_count = excluded.forward_count,
                    lose_comment_count = excluded.lose_comment_count,
                    lose_count = excluded.lose_count, 
                    play_count = excluded.play_count,
                    share_count = excluded.share_count,
                    whatsapp_share_count = excluded.whatsapp_share_count,
                    earliest_urls_expire_time = excluded.earliest_urls_expire_time,
                    description = excluded.description
                ''', (post.aweme_id, round(time.time()), post.create_time, post.author_sec_user_id,
                      post.cover, post.animated_cover, download_url_1, download_url_2, download_url_3,
                      play_url_1, play_url_2, play_url_3, post.share_link, post.web_link, post.short_link,
                      post.comment_count, post.digg_count, post.download_count, post.forward_count,
                      post.lose_comment_count, post.lose_count,
                      post.play_count, post.share_count, post.whatsapp_share_count, post.description,
                      earliest_expire_time
                      ))

    def fetch_latest_cached_posts(self, sec_user_id: str, amount: int):
        with self.engine.connect() as con:
            curs = con.execute('''
                        SELECT aweme_id, add_time, author_sec_user_id,
                            cover_url, animated_cover_url, download_url_1, download_url_2, download_url_3,
                            play_url_1, play_url_2, play_url_3, share_link, web_link, short_link,
                            comment_count, digg_count, download_count, forward_count, lose_comment_count, lose_count, 
                            play_count, share_count, whatsapp_share_count, description,
                            earliest_urls_expire_time
                        FROM tiktok_posts
                        WHERE author_sec_user_id = ?
                        ORDER by create_time desc
                        LIMIT ?''', (sec_user_id, amount))
            fetched_posts = list()
            rows = curs.fetchall()
            for row in rows:
                post = PostInfo()
                post.aweme_id = row[0]
                post.cover = row[3]
                post.animated_cover = row[4]

                download_links = list()
                if row[5] is not None:
                    download_links.append(row[5])
                if row[6] is not None:
                    download_links.append(row[6])
                if row[7] is not None:
                    download_links.append(row[7])
                post.download_links = download_links

                play_links = list()
                if row[8] is not None:
                    play_links.append(row[8])
                if row[9] is not None:
                    play_links.append(row[9])
                if row[10] is not None:
                    play_links.append(row[10])
                post.play_links = play_links

                post.share_link = row[11]
                post.web_link = row[12]
                post.short_link = row[13]
                post.comment_count = row[14]
                post.digg_count = row[15]
                post.download_count = row[16]
                post.forward_count = row[17]
                post.lose_comment_count = row[18]
                post.lose_count = row[19]
                post.play_count = row[20]
                post.share_count = row[21]
                post.whatsapp_share_count = row[22]
                post.description = row[23]
                post.author_sec_user_id = row[2]
                fetched_posts.append(post)
            return fetched_posts

    def fetch_cached_user_full_info(self, sec_user_id: str):
        with self.engine.connect() as con:
            curs = con.execute('''
                    SELECT sec_user_id, add_time, username,
                        fullname, followers, following, likes, avatar_url, secret,
                        earliest_urls_expire_time
                    FROM tiktok_accounts_full
                    WHERE sec_user_id=?''', (sec_user_id,))
            rows = curs.fetchall()
            if len(rows) == 0:
                return None
            user = UserInfo()
            row = rows[0]
            user.sid = row[0]
            user.login_name = row[2]
            user.name = row[3]
            user.followers = row[4]
            user.following = row[5]
            user.likes = row[6]
            user.avatar = row[7]
            user.secret = row[8]
            return user

    def clean_posts_cache(self, interval_min=15):
        with self.engine.connect() as con:
            con.execute('''
                    DELETE from tiktok_posts
                    where ?-add_time>?''', (round(time.time()), interval_min*60))

    def clean_accounts_full_cache(self, interval_min=15):
        with self.engine.connect() as con:
            con.execute('''
                    DELETE from tiktok_accounts_full
                    where ?-add_time>?''', (round(time.time()), interval_min*60))


@singleton
class DataCleaner(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.database = Database()

    def run(self):
        while True:
            time.sleep(5*60)
            self.database.clean_posts_cache()
            self.database.clean_accounts_full_cache()
