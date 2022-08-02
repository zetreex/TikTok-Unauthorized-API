from typing import List
from dataclasses import dataclass
from app.utils.user_search import UserInfo, PostInfo, UserPair, RequestInfo


@dataclass
class ApiSearchRequest:
    """! Dataclass request for /search, /search_full. """
    username: str = None
    amount_of_posts: int = 0

@dataclass
class ApiScheduleViewsRequest:
    """! Dataclass request for /schedule_views """
    aweme_id: str = None
    amount: int = 0

@dataclass
class ApiSearchSidRequest:
    """! Dataclass request for /search, /search_full, /liked, /liked_full. """
    sid: str = None
    amount_of_posts: int = 0

@dataclass
class ApiSearchBuildSidRequest(ApiSearchSidRequest):
    """! Dataclass request for /search, /search_full, /liked, /liked_full. """
    count_requests: int = 1


@dataclass
class ApiPostSearchRequest:
    """! Dataclass request for /post. """
    share_link: str = None
    web_link: str = None
    short_link: str = None
    aweme_id: str = None

@dataclass
class ApiPostSearchBuildRequest(ApiPostSearchRequest):
    """! Dataclass request for /post. """
    count_requests: int = 1

@dataclass
class ApiSearchResponse:
    """! Dataclass response for /search, /search_full. """
    user: UserInfo
    posts: List

    def __init__(self, user, posts):
        self.user = user
        self.posts = posts


@dataclass
class ApiPostSearchResponse:
    """! Dataclass response for /post. """
    posts: PostInfo

    def __init__(self, posts):
        self.posts = posts


@dataclass
class ApiLikedPostSearchResponse:
    """! Dataclass response for /liked, /liked_full. """
    posts: List

    def __init__(self, posts):
        self.posts = posts

@dataclass
class ApiUserSearchResponse:
    """! Dataclass response for /user. """
    users: List[UserPair]

    def __init__(self, users):
        self.users = [UserPair(x[0], x[1]) for x in users]


@dataclass
class ApiBuildedRequest:
    """! Dataclass response for /*_build_request. """
    request: List[RequestInfo]

    def __init__(self, request):
        self.request = request