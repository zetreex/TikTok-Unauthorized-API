from concurrent.futures import wait, FIRST_COMPLETED
from flask_executor import Executor

from flask_restplus import Resource, Namespace, fields

from app.api.types_.search import *
from app.db.database import Database
from app.utils.device_pool import DevicePoll

from app.utils.factory_search import SearchBySidCreator, \
    SearchPostByShareLinkCreator, \
    SearchLikedPostsCreator, \
    BuildSearchBySidCreator, BuildSearchPostByShareLinkCreator, BuildSearchPostsBySidCreator
from app.utils.user_search import SearchException, get_sec_uid_by_username
from app.utils.utils import singleton
from config.application import USE_CACHING


@dataclass
class ApiLikedPostSearchResponse:
    """! Dataclass response for /liked, /liked_full. """
    posts: List

    def __init__(self, posts):
        self.posts = posts


@singleton
class RestExecutorWrapper:
    executor: Executor

    def __init__(self, executor):
        self.executor = executor


# Namespace for all endpoints with `api/` path
ns = Namespace('api/', description='TikTok Viewer API')

# Describe model of request. Duplicate class `ApiSearchRequest` for Flask and Swagger.
search_request = ns.model(
    'SearchRequest', {
        'username':
            fields.String(readonly=True,
                          required=True,
                          description='Username of searching user'),
        'amount_of_posts':
            fields.Integer(
                readonly=True, required=False, description='Number of posts'),
    })

# Describe model of request. Duplicate class `ApiSearchRequest` for Flask and Swagger.
search_sid_request = ns.model(
    'SearchSidRequest', {
        'sid':
            fields.String(readonly=True,
                          required=True,
                          description='Secure user ID of searching user'),
        'amount_of_posts':
            fields.Integer(
                readonly=True, required=False, description='Number of posts'),
    })

search_sid_request_build = ns.model(
    'SearchSidBuildRequest', {
        'sid':
            fields.String(readonly=True,
                          required=True,
                          description='Secure user ID of searching user'),
        'count_requests':
            fields.Integer(readonly=True, required=False, description='Count of requests'),
    })

posts_sid_request_build = ns.model(
    'PostsSidBuildRequest', {
        'sid':
            fields.String(readonly=True,
                          required=True,
                          description='Secure user ID of searching user'),
        'amount_of_posts':
            fields.Integer(readonly=True, required=False, description='Number of posts'),
        'count_requests':
            fields.Integer(readonly=True, required=False, description='Count of requests'),
    })

# Describe model of request. Duplicate class `ApiPostSearchRequest` for Flask and Swagger.
post_request = ns.model(
    'PostSearchRequest', {
        'share_link': fields.String(readonly=True, description='Share link'),
        'web_link': fields.String(readonly=True, description='Web link'),
        'short_link': fields.String(readonly=True, description='Short link'),
        'aweme_id': fields.String(readonly=True, description='Aweme ID'),
    })

post_request_build = ns.model(
    'PostSearchBuildRequest', {
        'share_link': fields.String(readonly=True, description='Share link'),
        'web_link': fields.String(readonly=True, description='Web link'),
        'short_link': fields.String(readonly=True, description='Short link'),
        'aweme_id': fields.String(readonly=True, description='Aweme ID'),
        'count_requests': fields.Integer(readonly=True, required=False, description='Count of requests'),
    }
)

# Describe model of request. Duplicate class `PostInfo` for Flask and Swagger.
post_info_full = ns.model(
    'PostInfoFull', {
        'cover':
            fields.String(
                readonly=True, required=True, description='Usual cover of post'),
        'animated_cover':
            fields.String(readonly=True,
                          required=True,
                          description='Animated cover of post'),
        'aweme_id':
            fields.String(readonly=True, required=True, description='Id of post'),
        'download_links':
            fields.List(fields.String,
                        readonly=True,
                        required=True,
                        description='Download URL of post'),
        'play_links':
            fields.List(fields.String,
                        readonly=True,
                        required=True,
                        description='Download URL of post'),
        'share_link':
            fields.String(readonly=True,
                          required=True,
                          description='Full URL to share post'),
        'web_link':
            fields.String(
                readonly=True, required=True, description='Web URL to share post'),
        'short_link':
            fields.String(readonly=True,
                          required=True,
                          description='Short URL to share post'),
        'comment_count':
            fields.Integer(
                readonly=True, required=True, description='Number of comments'),
        'digg_count':
            fields.Integer(
                readonly=True, required=True, description='Number of likes/diggs'),
        'download_count':
            fields.Integer(
                readonly=True, required=True, description='Number of downloads'),
        'forward_count':
            fields.Integer(
                readonly=True, required=True, description='Number of forwards'),
        'lose_comment_count':
            fields.Integer(readonly=True,
                           required=True,
                           description='Number of lose comments(?)'),
        'lose_count':
            fields.Integer(readonly=True,
                           required=True,
                           description='Number of lose counts(?)'),
        'play_count':
            fields.Integer(
                readonly=True, required=True, description='Number of plays'),
        'share_count':
            fields.Integer(
                readonly=True, required=True, description='Number of shares'),
        'whatsapp_share_count':
            fields.Integer(readonly=True,
                           required=True,
                           description='Number of whatsapp_shares'),
    })

# Describe model of request. Duplicate class `PostInfo` for Flask and Swagger.
post_info = ns.model(
    'PostInfo', {
        'cover':
            fields.String(
                readonly=True, required=True, description='Usual cover of post'),
        'animated_cover':
            fields.String(readonly=True,
                          required=True,
                          description='Animated cover of post'),
        'aweme_id':
            fields.String(readonly=True, required=True, description='Id of post'),
        'description':
            fields.String(readonly=True, required=False, description='Description of post'),
    })

# Describe model of response. Duplicate class `RequestInfo` for Flask and Swagger.
request_info = ns.model(
    'RequestInfo', {
        'method':
            fields.String(
                readonly=True, required=True, description='Method of request'),
        'url':
            fields.String(
                readonly=True, required=True, description='URL of request'),
        'headers':
            fields.Wildcard(fields.String,
                            readonly=True, required=True, description='Headers of request'),
        'body':
            fields.String(
                readonly=True, required=True, description='Data of request'),
    })

# Describe model of request. Duplicate class `UserInfo` for Flask and Swagger.
user_info = ns.model(
    'UserInfo', {
        'login_name':
            fields.String(
                readonly=True, description='Login name of user'),
        'name':
            fields.String(readonly=True,
                          description='Name of user'),
        'followers':
            fields.Integer(
                readonly=True, description='Number of followers'),
        'following':
            fields.Integer(
                readonly=True, description='Number of following'),
        'likes':
            fields.Integer(
                readonly=True, description='Number of likes'),
        'avatar':
            fields.String(
                readonly=True, description='Url of user\'s avatar'),
        'sid':
            fields.String(
                readonly=True, description='Secuserid of user'),
        'secret':
            fields.Integer(
                readonly=True, description='if this user hidden on tiktok'),
    })

# Describe model of response. Duplicate class `ApiSearchResponse` for Flask and Swagger.
search_response = ns.model(
    'SearchResponse', {
        'user': fields.Nested(user_info, allow_null=False, skip_none=True),
        'posts': fields.List(fields.Nested(post_info), allow_null=False, skip_none=True),
        'error':
            fields.String(
                readonly=True,
                description='Error during proccessing'
            )
    })

# Describe model of response. Duplicate class `ApiSearchResponse` for Flask and Swagger.
search_response_full = ns.model(
    'SearchResponseFull', {
        'user': fields.Nested(user_info, allow_null=False, skip_none=True),
        'posts': fields.List(fields.Nested(post_info_full)),
        'error':
            fields.String(
                readonly=True,
                description='Error during proccessing'
            )
    })

# Describe model of response. Duplicate class `ApiPostSearchResponse` for Flask and Swagger.
post_search_response = ns.model('PostSearchResponse',
                                {'posts': fields.Nested(post_info_full, allow_null=False, skip_none=True),
                                 'error':
                                     fields.String(
                                         readonly=True,
                                         description='Error during proccessing'
                                     )
                                 })

# Describe model of response. Duplicate class `ApiLikedPostSearchResponse` for Flask and Swagger.

liked_posts_response = ns.model(
    'LikedPostSearchResponse',
    {'posts': fields.List(fields.Nested(post_info_full))})

# Describe model of response. Duplicate class `ApiBuildedRequest` for Flask and Swagger.
builded_request = ns.model('BuildedRequest',
                           {'request': fields.List(fields.Nested(request_info))})


@ns.route('/search_by_sid')
@ns.response(404, 'item not found')
@ns.response(500, 'multiple retries failed')
class SearchUserAPI(Resource):
    """! Search user information and posts by `sec_user_id`. """

    @ns.doc("Find user and info about it by `sec_user_id`")
    @ns.marshal_with(search_response, code=200)
    @ns.expect(search_sid_request, skip_none=True)
    def post(self):
        executor = RestExecutorWrapper().executor
        try:
            creator = SearchBySidCreator()
            # use parallel execution cause sometimes TT throws captcha or proxied conneciton hangs up. this way we fetch the fastest result
            futures = [executor.submit(lambda: creator.search(ns.payload, proxy_on=True)) for _ in range(4)]
            user_is_secret_counter = 0
            while True:
                done, not_done = wait(futures, return_when=FIRST_COMPLETED)
                futures = not_done
                if len(done) != 0:
                    future = done.pop()
                    if not future.cancelled() and not future.exception():
                        result = future.result()
                        if result.user.secret == 1:
                            user_is_secret_counter += 1
                            if user_is_secret_counter >= 2:  # use 2-time verification cause sometimes tiktok sends that it's secret but it's not
                                break
                        else:
                            break
                    if len(done) == 0 and len(not_done) == 0:
                        result = None
                        break
            if result is None:
                raise SearchException("search-by-sid failed", 404)
            else:
                if USE_CACHING:
                    Database().cache_user_full_info(result.user)
                return result
        except SearchException as ex:
            return {"error": ex.error_str}, ex.http_code


@ns.route('/search_by_sid_build_request')
class BuildSearchUserAPI(Resource):
    """! Build request to search user information and posts by `sec_user_id`. """

    @ns.doc("Build request to find user and info about it by `sec_user_id`")
    @ns.marshal_with(builded_request, code=200)
    @ns.expect(search_sid_request_build, skip_none=True)
    def post(self):
        creator = BuildSearchBySidCreator()
        result: ApiBuildedRequest = creator.search(ns.payload, proxy_on=False, device_return=True)
        return result


@ns.route('/posts_by_sid_build_request')
class BuildSearchPostsAPI(Resource):
    """! Build request to search user posts by `sec_user_id`. """

    @ns.doc("Build request to find user's post by `sec_user_id`")
    @ns.marshal_with(builded_request, code=200)
    @ns.expect(posts_sid_request_build, skip_none=True)
    def post(self):
        creator = BuildSearchPostsBySidCreator()
        result: ApiBuildedRequest = creator.search(ns.payload, proxy_on=False, device_return=True)
        return result


@ns.route('/search')
@ns.response(404, 'item not found')
@ns.response(500, 'multiple retries failed')
class SearchUserAPI(Resource):
    """! Search user information and posts by `username`. """

    @ns.doc("Find user and info about it by `username`")
    @ns.marshal_with(search_response, code=200)
    @ns.expect(search_request, skip_none=True)
    def post(self):
        executor = RestExecutorWrapper().executor

        try:
            username = ns.payload.get("username", None)
            sec_uid = Database().fetch_cached_sec_uid_by_username(username)
            if sec_uid is None:
                proxy_service = DevicePoll().proxy_service
                # use parallel execution cause sometimes TT throws captcha or proxied conneciton hangs up. this way we fetch the fastest result
                futures = [executor.submit(lambda f: get_sec_uid_by_username(*f),
                                           (None, username, None, proxy_service)) for _ in range(4)]
                while True:
                    done, not_done = wait(futures, return_when=FIRST_COMPLETED)
                    futures = not_done
                    if len(done) != 0:
                        future = done.pop()
                        if not future.cancelled() and not future.exception():
                            sec_uid = future.result()
                            break
                        if len(done) == 0 and len(not_done) == 0:
                            sec_uid = None
                            break

                if sec_uid is None:
                    raise SearchException("user not found", 404)
                else:
                    Database().cache_user_info(username, sec_uid)

            creator = SearchBySidCreator()
            payload = {"sid": sec_uid, "amount_of_posts": ns.payload.get("amount_of_posts", 0)}

            # use parallel execution cause sometimes TT throws captcha or proxied conneciton hangs up. this way we fetch the fastest result
            futures = [executor.submit(lambda: creator.search(payload, proxy_on=True)) for _ in range(4)]
            user_is_secret_counter = 0
            while True:
                done, not_done = wait(futures, return_when=FIRST_COMPLETED)
                futures = not_done
                if len(done) != 0:
                    future = done.pop()
                    if not future.cancelled() and not future.exception():
                        result = future.result()
                        if result.user.secret == 1:
                            user_is_secret_counter += 1
                            if user_is_secret_counter >= 2:  # use 2-time verification cause sometimes tiktok sends that it's secret but it's not
                                break
                        else:
                            break
                    if len(done) == 0 and len(not_done) == 0:
                        result = None
                        break
            if result is None:
                raise SearchException("search-by-sid failed", 404)
            else:
                if USE_CACHING:
                    Database().cache_user_full_info(result.user)
                return result
        except SearchException as ex:
            return {"error": ex.error_str}, ex.http_code


@ns.route('/search_full')
@ns.response(404, 'item not found')
@ns.response(500, 'multiple retries failed')
class SearchFullUserAPI(Resource):
    """! Search user inforamtion and posts(with full inforamtion) by `username`. """

    @ns.doc("Find user and full info about it")
    @ns.marshal_with(search_response_full, code=200)
    @ns.expect(search_request, skip_none=True)
    def post(self):
        executor = RestExecutorWrapper().executor

        try:
            username = ns.payload.get("username", None)
            sec_uid = Database().fetch_cached_sec_uid_by_username(username)
            if sec_uid is None:
                proxy_service = DevicePoll().proxy_service
                # use parallel execution cause sometimes TT throws captcha or proxied conneciton hangs up. this way we fetch the fastest result
                futures = [executor.submit(lambda f: get_sec_uid_by_username(*f),
                                           (None, username, None, proxy_service)) for _ in range(4)]
                while True:
                    done, not_done = wait(futures, return_when=FIRST_COMPLETED)
                    futures = not_done
                    if len(done) != 0:
                        future = done.pop()
                        if not future.cancelled() and not future.exception():
                            sec_uid = future.result()
                            break
                        if len(done) == 0 and len(not_done) == 0:
                            sec_uid = None
                            break

                if sec_uid is None:
                    raise SearchException("user not found", 404)
                else:
                    Database().cache_user_info(username, sec_uid)

            creator = SearchBySidCreator()
            payload = {"sid": sec_uid, "amount_of_posts": ns.payload.get("amount_of_posts", 0)}

            # use parallel execution cause sometimes TT throws captcha or proxied conneciton hangs up. this way we fetch the fastest result
            futures = [executor.submit(lambda: creator.search(payload, proxy_on=True)) for _ in range(4)]
            while True:
                done, not_done = wait(futures, return_when=FIRST_COMPLETED)
                futures = not_done
                if len(done) != 0:
                    future = done.pop()
                    user_is_secret_counter = 0
                    if not future.cancelled() and not future.exception():
                        result = future.result()
                        if result.user.secret == 1:
                            user_is_secret_counter += 1
                            if user_is_secret_counter >= 2:  # use 2-time verification cause sometimes tiktok sends that it's secret but it's not
                                break
                        else:
                            break
                    if len(done) == 0 and len(not_done) == 0:
                        result = None
                        break
            if result is None:
                raise SearchException("search-by-sid failed", 404)
            else:
                if USE_CACHING:
                    Database().cache_user_full_info(result.user)
                return result
        except SearchException as ex:
            return {"error": ex.error_str}, ex.http_code


@ns.route('/post')
@ns.response(404, 'item not found')
@ns.response(500, 'multiple retries failed')
class SearchPostAPI(Resource):
    """! Search user posts by `link`. """

    @ns.doc("Find post by share link")
    @ns.marshal_with(post_search_response, code=200)
    @ns.expect(post_request, skip_none=True)
    def post(self):
        executor = RestExecutorWrapper().executor
        creator = SearchPostByShareLinkCreator()
        try:
            # use parallel execution cause sometimes TT throws captcha or proxied conneciton hangs up. this way we fetch the fastest result
            futures = [executor.submit(lambda: creator.search(ns.payload, proxy_on=True)) for _ in range(4)]
            while True:
                done, not_done = wait(futures, return_when=FIRST_COMPLETED)
                futures = not_done
                if len(done) != 0:
                    future = done.pop()
                    if not future.cancelled() and not future.exception():
                        result = future.result()
                        break
                    if len(done) == 0 and len(not_done) == 0:
                        result = None
                        break
            if result is None:
                raise SearchException("item not found", 404)
            else:
                return result
        except SearchException as ex:
            return {"error": ex.error_str}, ex.http_code


@ns.route('/post_build_request')
class BuildSearchPostAPI(Resource):
    """! build request to search user posts by `link`. """

    @ns.doc("Biuld request to find post by share link")
    @ns.marshal_with(builded_request, code=200)
    @ns.expect(post_request_build, skip_none=True)
    def post(self):
        creator = BuildSearchPostByShareLinkCreator()
        result: ApiBuildedRequest = creator.search(ns.payload, proxy_on=False, device_return=True)
        return result


@ns.route('/liked')
class SearchLikedPostsAPI(Resource):
    """! Search liked posts by `sec_user_id`. """

    @ns.doc("Find liked posts by `sec_user_id`")
    @ns.marshal_with(liked_posts_response, code=200)
    @ns.expect(search_sid_request, skip_none=True)
    def post(self):
        executor = RestExecutorWrapper().executor
        try:
            creator = SearchLikedPostsCreator()
            # use parallel execution cause sometimes TT throws captcha or proxied conneciton hangs up. this way we fetch the fastest result
            futures = [executor.submit(lambda: creator.search(ns.payload, proxy_on=True)) for _ in range(4)]
            while True:
                done, not_done = wait(futures, return_when=FIRST_COMPLETED)
                futures = not_done
                if len(done) != 0:
                    future = done.pop()
                    if not future.cancelled() and not future.exception():
                        result = future.result()
                        break
                    if len(done) == 0 and len(not_done) == 0:
                        result = None
                        break
            if result is None:
                raise SearchException("search-by-sid failed", 404)
            else:
                return result
        except SearchException as ex:
            return {"error": ex.error_str}, ex.http_code
