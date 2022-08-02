import asyncio
import collections
import logging
import socket
import ssl

import httpcore
import socks
import socksio
from tiktok_mobile.api.user_search import SearchApi
from tiktok_mobile.functional.utils import *
from tiktok_mobile.models.tiktok_phone import *
from tiktok_utils.proxy.dto import Proxy
import httpx


import tiktok_mobile.utils.sender as sender_module

from app.utils.utils import format_except

sender_module.SENDER_DEFAULT_TIMEOUT = 10
sender_module.SENDER_DEFAULT_PROXY_SWITCH_COUNT = 10


class SearchException(Exception):
    """! Special class to catch exception due to failed search. """
    def __init__(self, error_str: str = None, http_code: int = 500):
        self.error_str = error_str
        self.http_code = http_code


def current_milli_time():
    return round(time.time() * 1000)


@dataclass
class UserInfo:
    """! Describes user information. """
    login_name: str = None
    name: str = None
    followers: int = None
    following: int = None
    likes: int = None
    avatar: str = None
    sid: str = None
    secret: int = 0


@dataclass
class UserPair:
    """! Describes user pair. """
    login_name: str = None
    sid: str = None


@dataclass
class PostInfo:
    """! Describes post inforamation. """
    cover: str = None
    animated_cover: str = None
    aweme_id: str = None
    download_links: list = None
    play_links: list = None
    share_link: str = None
    web_link: str = None
    short_link: str = None
    comment_count: int = None
    digg_count: int = None
    download_count: int = None
    forward_count: int = None
    lose_comment_count: int = None
    lose_count: int = None
    play_count: int = None
    share_count: int = None
    whatsapp_share_count: int = None
    description: str = None
    author_sec_user_id: str = None
    create_time: int = None

@dataclass
class RequestInfo:
    """! Describes information about http request. """
    method: str
    url: str
    headers: dict
    body: bytes

    def __init__(self, method: str, url: str, headers: dict, body: bytes):
        self.method = method
        self.url = url
        self.headers = headers
        self.body = body


def create_phone(sender: Sender = None) -> TikTokPhone:
    """! Create phone. If failed raise exception. """
    apk = TikTokApk.generate()

    phone = TikTokPhone(apk=apk,
                        sender=sender if sender is not None else Sender())

    device_register(phone)
    LogApi.app_alert_check(phone)
    return phone


def search_user(phone: TikTokPhone, username: str) -> list:
    """! Search list of sec_user_id suitable to username. """
    result = SearchApi.search_general(phone, username)
    if len(result.data) == 0:
        raise SearchException("Failed to get user list")

    user_list = result.data[0].user_list

    if user_list is None or len(user_list) == 0:
        raise SearchException("User list is empty")

    sec_user_id_list = list()
    for user in user_list:
        sec_user_id_list.append((user.user_info.sec_uid, user.user_info.nickname))

    return sec_user_id_list


def get_user_info(phone: TikTokPhone, sec_user_id: str):
    """! Get users posts by sec_user_id. """
    result = UserApi.user_profile_other(phone, sec_user_id)
    user = UserInfo()

    if result.user.sec_uid is None:
        raise SearchException("Failed to find user")

    user.login_name = result.user.unique_id
    user.name = str(result.user.nickname)
    user.followers = result.user.follower_count
    user.following = result.user.following_count
    user.likes = result.user.total_favorited
    if len(result.user.avatar_168x168.url_list):
        user.avatar = str(result.user.avatar_168x168.url_list[-1])
    user.sid = result.user.sec_uid
    user.secret = result.user.secret

    return user


def get_user_info_build_request(phone: TikTokPhone, sec_user_id: str) -> RequestInfo:
    """! Build request to get users posts by sec_user_id. """
    return UserApi.user_profile_other_build_request(phone, sec_user_id)


def get_user_posts_build_request(phone: TikTokPhone, sec_user_id: str, cursor=0, count=20) -> RequestInfo:
    """! Build request to get users posts by sec_user_id. """
    return UserApi.user_post_list_build_request(phone,
                                                sec_user_id,
                                                max_cursor=cursor,
                                                count=count)


def get_user_posts(phone: TikTokPhone, sec_user_id: str, cursor, count,
                   full) -> list:
    """! Get users posts by sec_user_id. """
    result = UserApi.user_post_list(phone,
                                    sec_user_id,
                                    max_cursor=cursor,
                                    count=count)
    if result is None or result.aweme_list is None:
        return list()

    result.aweme_list.sort(key=lambda x: x.create_time, reverse=True)
    if len(result.aweme_list) > count:
        result.aweme_list = result.aweme_list[:10]

    return [aweme_detail_to_post(aweme, phone) for aweme in result.aweme_list]


def get_user_liked_posts(phone: TikTokPhone, sec_user_id: str, cursor: int,
                         count: int, full: bool) -> list:
    """! Get liked posts by sec_user_id.
        @param phone            TiktokPhone
        @param sec_user_id      secUserId of user
        @param cursor           index from where get posts
        @param count            number of posts 
        @param full             return full description of posts or not
        
        @note that works only if user change privacy settings
    """
    posts = list()

    result = UserApi.aweme_favorite(phone,
                                    sec_user_id,
                                    max_cursor=cursor,
                                    count=count)
    if result is None or result.aweme_list is None:
        return posts

    for aweme in result.aweme_list:
        post = aweme_detail_to_post(aweme, phone)
        posts.append(post)

    return posts


def get_liked_posts(phone: TikTokPhone,
                    sec_user_id: str,
                    number: int = 20,
                    full: bool = False) -> list:
    """! Get liked posts by sec_user_id. """
    cursor = number // 20
    last = number % 20

    posts = list()

    for cursor_i in range(0, cursor):
        post = get_user_liked_posts(phone, sec_user_id, cursor_i * 20, 20,
                                    full)
        posts += post

    if last:
        post = get_user_liked_posts(phone, sec_user_id, cursor * 20, last,
                                    full)
        posts += post

    return posts


def get_posts(phone: TikTokPhone,
              sec_user_id: str,
              number: int = 20,
              full: bool = False) -> list:
    """! Get users posts by sec_user_id. """
    cursor = number // 20
    last = number % 20

    posts = list()

    for cursor_i in range(0, cursor):
        post = get_user_posts(phone, sec_user_id, cursor_i * 20, 20, full)
        posts += post

    if last:
        post = get_user_posts(phone, sec_user_id, cursor * 20, last, full)
        posts += post

    return posts


def get_post_by_aweme_id(phone: TikTokPhone, aweme_id: str) -> PostInfo:
    """! Get post by aweme_id. """
    r = UserApi.aweme_details(phone, aweme_id)
    aweme = r.aweme_detail
    post = aweme_detail_to_post(aweme, phone)
    return post


def aweme_detail_to_post(aweme, phone) -> PostInfo:
    post = PostInfo()
    post.aweme_id = aweme.aweme_id
    if len(aweme.video.cover.url_list):
        post.cover = str(aweme.video.cover.url_list[-1])
    post.animated_cover = None
    if aweme.video.animated_cover is not None and len(aweme.video.animated_cover.url_list):
        post.animated_cover = str(aweme.video.animated_cover.url_list[-1])

    post.download_links = list(aweme.video.download_addr.url_list)
    post.play_links = list(aweme.video.play_addr.url_list)

    post.share_link = aweme.share_info.share_url
    post.web_link = generate_web_url(aweme.author.unique_id,
                                     aweme.aweme_id).url
    post.short_link = generate_short_url(phone, post.share_link).url
    post.comment_count = aweme.statistics.comment_count
    post.digg_count = aweme.statistics.digg_count
    post.download_count = aweme.statistics.download_count
    post.forward_count = aweme.statistics.forward_count
    post.lose_comment_count = aweme.statistics.lose_comment_count
    post.lose_count = aweme.statistics.lose_count
    post.play_count = aweme.statistics.play_count
    post.share_count = aweme.statistics.share_count
    post.whatsapp_share_count = aweme.statistics.whatsapp_share_count
    post.description = aweme.desc
    post.author_sec_user_id = aweme.author.sec_uid
    post.create_time = aweme.create_time

    return post


def get_post(phone: TikTokPhone, link: str, web_link: str, short_link: str,
             aweme_id: str):
    """! Get post by link. """
    if aweme_id and len(aweme_id):
        try:
            return get_post_by_aweme_id(phone, aweme_id)
        except Exception as e:
            logging.error(e)

    if link and len(link):
        try:
            aweme_id = parse_share_url(link)
            if aweme_id is not None:
                return get_post_by_aweme_id(phone, aweme_id)
        except Exception as e:
            logging.error(e)

    if web_link and len(web_link):
        try:
            aweme_id = parse_web_url(web_link)
            if aweme_id is not None:
                return get_post_by_aweme_id(phone, aweme_id)
        except Exception as e:
            logging.error(e)

    if short_link and len(short_link):
        try:
            aweme_id = parse_short_url(short_link)
            if aweme_id is not None:
                return get_post_by_aweme_id(phone, aweme_id)
        except Exception as e:
            logging.error(e)

    raise SearchException("Failed to find post")


def get_post_build_request(phone: TikTokPhone, link: str, web_link: str, short_link: str,
                           aweme_id: str) -> RequestInfo:
    """! Get post by link. """
    if aweme_id and len(aweme_id):
        try:
            return UserApi.aweme_details_build_request(phone, aweme_id)
        except Exception as e:
            logging.error(e)

    if link and len(link):
        try:
            aweme_id = parse_share_url(link)
            if aweme_id is not None:
                return UserApi.aweme_details_build_request(phone, aweme_id)
        except Exception as e:
            logging.error(e)

    if web_link and len(web_link):
        try:
            aweme_id = parse_web_url(web_link)
            if aweme_id is not None:
                return UserApi.aweme_details_build_request(phone, aweme_id)
        except Exception as e:
            logging.error(e)

    if short_link and len(short_link):
        try:
            aweme_id = parse_short_url(short_link)
            if aweme_id is not None:
                return UserApi.aweme_details_build_request(phone, aweme_id)
        except Exception as e:
            logging.error(e)

    raise SearchException("Failed to find post")


def get_user_liked_posts(phone: TikTokPhone, sec_user_id: str, cursor: int,
                         count: int, full: bool) -> list:
    """! Get liked posts by sec_user_id.
        @param phone            TiktokPhone
        @param sec_user_id      secUserId of user
        @param cursor           index from where get posts
        @param count            number of posts
        @param full             return full description of posts or not

        @note that works only if user change privacy settings
    """
    posts = list()

    result = UserApi.aweme_favorite(phone,
                                    sec_user_id,
                                    max_cursor=cursor,
                                    count=count)

    if result is None or result.aweme_list is None:
        return posts

    for aweme in result.aweme_list:
        post = aweme_detail_to_post(aweme, phone)
        posts.append(post)

    return posts


def get_liked_posts(phone: TikTokPhone,
                    sec_user_id: str,
                    number: int = 20,
                    full: bool = False) -> list:
    """! Get liked posts by sec_user_id. """
    cursor = number // 20
    last = number % 20

    posts = list()

    for cursor_i in range(0, cursor):
        post = get_user_liked_posts(phone, sec_user_id, cursor_i * 20, 20,
                                    full)
        posts += post

    if last:
        post = get_user_liked_posts(phone, sec_user_id, cursor * 20, last,
                                    full)
        posts += post

    return posts


def get_sec_uid_by_username(device: TikTokPhone, username: str, proxy: Proxy = None, proxy_service=None):
    while True:
        try:
            if proxy_service is not None:
                proxy = proxy_service.next()
            # proxies = wrap_requests_proxy(proxy) if proxy else device.session.proxies
            quoted_username = quote(username)

            timeout = httpx.Timeout(5.0, connect=5.0, read=5.0, write=5.0, pool=5.0)

            async def make_request():
                async with httpx.AsyncClient(verify=False, http2=True, proxies=proxy, timeout=timeout, http1=False,
                                           trust_env=True) as client:
                    return await client.get("https://www.tiktok.com/@{}?lang=en".format(quoted_username), headers={
                        "User-Agent": "Mozilla/5.0 (Linux; Android 9; Mi A1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.115 Mobile Safari/537.36",
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
                        "path": "/@{}".format(quoted_username),
                        "Accept-Encoding": "gzip, deflate",
                        "Connection": "keep-alive"
                    }, timeout=timeout)

            response = asyncio.run(
                asyncio.wait_for(
                    make_request(), 10.0)
            )
            if response.status_code == 404:
                raise NotFoundException(
                    "TikTok user with username {} does not exist".format(username)
                )
            else:
                data, method = extract_tag_contents(response.text)
                user = json.loads(data)
                if user.get("props") is not None and user.get("props").get("pageProps") is not None:
                    user_props = user["props"]["pageProps"]
                    if user_props["serverCode"] == 404:
                        raise NotFoundException(
                            "TikTok user with username {} does not exist".format(username)
                        )

                if method == 'SIGI_STATE':
                    logging.warning("resolved {} using method {}".format(user["MobileUserPage"]["secUid"], method))
                    return user["MobileUserPage"]["secUid"]
                elif method == 'NEXT_DATA':
                    logging.warning(
                        "resolved {} using method {}".format(user_props["userInfo"]["user"]["secUid"], method))
                    return user_props["userInfo"]["user"]["secUid"]

        except (
                requests.exceptions.ConnectionError,
                requests.exceptions.ProxyError,
                socks.ProxyError,
                httpx.ProxyError,
                httpx.ConnectError,
                httpx.RemoteProtocolError,
                httpx.ReadError,
                httpx.ProtocolError,
                httpx.ConnectTimeout,
                httpcore.RemoteProtocolError,
                httpcore.ReadTimeout,
                httpcore.ConnectTimeout,
                socksio.exceptions.ProtocolError,
                socks.ProxyError,
                socket.timeout,
                ConnectionResetError,
                httpx.ReadTimeout,
                ssl.SSLError,
                asyncio.exceptions.TimeoutError
        ) as e:
            logging.warning(f"{type(e)} exception processing search. moving to new iteration")
            continue
        except Exception as e:
            logging.error(format_except(e))
            raise SearchException(f"Failed to get sec_uid. Caused by: {str(e)}")


class TikTokException(Exception):
    """Generic exception that all other TikTok errors are children of."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class CaptchaException(TikTokException):
    """TikTok is showing captcha"""


class NotFoundException(TikTokException):
    """TikTok indicated that this object does not exist."""


def extract_tag_contents(html):
    next_json = re.search(
        r"id=\"__NEXT_DATA__\"\s+type=\"application\/json\"\s*[^>]+>\s*(?P<next_data>[^<]+)",
        html,
    )
    if next_json:
        logging.warning("searching for secUid in tag __NEXT_DATA__")
        nonce_start = '<head nonce="'
        nonce_end = '">'
        nonce = html.split(nonce_start)[1].split(nonce_end)[0]
        j_raw = html.split(
            '<script id="__NEXT_DATA__" type="application/json" nonce="%s" crossorigin="anonymous">'
            % nonce
        )[1].split("</script>")[0]
        return j_raw, 'NEXT_DATA'
    else:
        sigi_json = re.search(
            r'<script id="SIGI_STATE" type="application/json">(.*?)</script>', html
        )
        if sigi_json:
            logging.warning("searching for secUid in tag SIGI_STATE")
            return sigi_json.group(1), 'SIGI_STATE'
        else:
            logging.warning("seems like got captcha")
            raise CaptchaException(
                "TikTok blocks this request displaying a Captcha \nTip: Consider using a proxy or a custom_verify_fp as method parameters"
            )

def quote(string, safe='/', encoding=None, errors=None):
    """quote('abc def') -> 'abc%20def'

    Each part of a URL, e.g. the path info, the query, etc., has a
    different set of reserved characters that must be quoted. The
    quote function offers a cautious (not minimal) way to quote a
    string for most of these parts.

    RFC 3986 Uniform Resource Identifier (URI): Generic Syntax lists
    the following (un)reserved characters.

    unreserved    = ALPHA / DIGIT / "-" / "." / "_" / "~"
    reserved      = gen-delims / sub-delims
    gen-delims    = ":" / "/" / "?" / "#" / "[" / "]" / "@"
    sub-delims    = "!" / "$" / "&" / "'" / "(" / ")"
                  / "*" / "+" / "," / ";" / "="

    Each of the reserved characters is reserved in some component of a URL,
    but not necessarily in all of them.

    The quote function %-escapes all characters that are neither in the
    unreserved chars ("always safe") nor the additional chars set via the
    safe arg.

    The default for the safe arg is '/'. The character is reserved, but in
    typical usage the quote function is being called on a path where the
    existing slash characters are to be preserved.

    Python 3.7 updates from using RFC 2396 to RFC 3986 to quote URL strings.
    Now, "~" is included in the set of unreserved characters.

    string and safe may be either str or bytes objects. encoding and errors
    must not be specified if string is a bytes object.

    The optional encoding and errors parameters specify how to deal with
    non-ASCII characters, as accepted by the str.encode method.
    By default, encoding='utf-8' (characters are encoded with UTF-8), and
    errors='strict' (unsupported characters raise a UnicodeEncodeError).
    """
    if isinstance(string, str):
        if not string:
            return string
        if encoding is None:
            encoding = 'utf-8'
        if errors is None:
            errors = 'strict'
        string = string.encode(encoding, errors)
    else:
        if encoding is not None:
            raise TypeError("quote() doesn't support 'encoding' for bytes")
        if errors is not None:
            raise TypeError("quote() doesn't support 'errors' for bytes")
    return quote_from_bytes(string, safe)


def quote_from_bytes(bs, safe='/'):
    """Like quote(), but accepts a bytes object rather than a str, and does
    not perform string-to-bytes encoding.  It always returns an ASCII string.
    quote_from_bytes(b'abc def\x3f') -> 'abc%20def%3f'
    """
    if not isinstance(bs, (bytes, bytearray)):
        raise TypeError("quote_from_bytes() expected bytes")
    if not bs:
        return ''
    if isinstance(safe, str):
        # Normalize 'safe' by converting to bytes and removing non-ASCII chars
        safe = safe.encode('ascii', 'ignore')
    else:
        safe = bytes([c for c in safe if c < 128])
    if not bs.rstrip(_ALWAYS_SAFE_BYTES + safe):
        return bs.decode()
    try:
        quoter = _safe_quoters[safe]
    except KeyError:
        _safe_quoters[safe] = quoter = Quoter(safe).__getitem__
    return ''.join([quoter(char) for char in bs])


_ALWAYS_SAFE = frozenset(b'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
                         b'abcdefghijklmnopqrstuvwxyz'
                         b'0123456789'
                         b'_.-~')
_ALWAYS_SAFE_BYTES = bytes(_ALWAYS_SAFE)
_safe_quoters = {}


class Quoter(collections.defaultdict):
    """A mapping from bytes (in range(0,256)) to strings.

    String values are percent-encoded byte values, unless the key < 128, and
    in the "safe" set (either the specified safe set, or default set).
    """
    # Keeps a cache internally, using defaultdict, for efficiency (lookups
    # of cached keys don't call Python code at all).
    def __init__(self, safe):
        """safe: bytes object."""
        self.safe = _ALWAYS_SAFE.union(safe)

    def __repr__(self):
        # Without this, will just display as a defaultdict
        return "<%s %r>" % (self.__class__.__name__, dict(self))

    def __missing__(self, b):
        # Handle a cache miss. Store quoted string in cache and return.
        res = chr(b) if b in self.safe else '%{:02X}'.format(b)
        self[b] = res
        return res