from __future__ import annotations

import time
from abc import ABC, abstractmethod

import logging

import requests.exceptions
from flask_restplus import Namespace
from tiktok_mobile.api.exceptions import EmptyResponseBodyError

from app.api.types_.search import ApiSearchResponse, \
    ApiPostSearchRequest, ApiPostSearchResponse, ApiSearchSidRequest, \
    ApiLikedPostSearchResponse, ApiBuildedRequest, \
    ApiPostSearchBuildRequest, ApiSearchBuildSidRequest, ApiScheduleViewsRequest
from app.db.database import Database
from app.utils.device_pool import DevicePoll

from app.utils.user_search import get_user_info, \
    get_post, get_posts, SearchException, get_liked_posts, \
    get_post_build_request, get_user_info_build_request, get_user_posts_build_request
from app.utils.utils import format_except
from config.application import USE_CACHING


class SearchCreator(ABC):
    """
    Factory for Searching in Api.

    To usage this factory, you should:
     - Import certainly, any, of creators, f.e:
        from app.utils.factory_search import SearchByUsernameCreator
     - Call this creator:
        search_username_creator = SearchByUsernameCreator
     - Call search method:
        search_username_creator.search(payload_from_client)
    Where is payload_from_client is Namespace.payload that you can get from your clients.

    search(self, payload: Namespace.payload): ApiSearchResponse
    """

    def __init__(self):
        pass

    @abstractmethod
    def factory_method(self):
        pass

    def search(self, payload: Namespace.payload, **params) -> ApiSearchResponse:
        """
        payload -- payload from client.
        params like a dict, with following keywords:
            - proxy_on: bool (on/off proxy for current search-request?)
            - device_return: bool (return/or no device from successfully search)
        """

        device_return: bool = params.get("device_return", True)
        proxy_on: bool = params.get("proxy_on", True)

        # Getting factory product
        product = self.factory_method()

        # Updating TikTok device for next requests
        device = DevicePoll().get_device(proxy_on=proxy_on)

        try:
            logging.warning(
                "using device {}".format(device.device_id))
            result = product.operation(device, payload)
            return result
        except (SearchException, EmptyResponseBodyError) as ex:
            logging.warning("Not found with payload [%s]. error [%s]", payload, str(ex))
        except requests.exceptions.ConnectionError:
            logging.warning("Connection error on payload [%s]", payload)
        except Exception as e:
            logging.warning("Unhandled error, [%s]", format_except(e))

        device.session.update_proxy()
        raise SearchException("item not found", 404)


class SearchBySidCreator(SearchCreator):
    def factory_method(self) -> SearchProduct:
        return SearchBySid()


class SearchPostByShareLinkCreator(SearchCreator):
    def factory_method(self) -> SearchProduct:
        return SearchPostByShareLink()


class SearchLikedPostsCreator(SearchCreator):
    def factory_method(self) -> SearchProduct:
        return SearchLikedPosts()


class BuildSearchBySidCreator(SearchCreator):
    def factory_method(self) -> SearchProduct:
        return BuildSearchBySid()


class BuildSearchPostByShareLinkCreator(SearchCreator):
    def factory_method(self) -> SearchProduct:
        return BuildSearchPostByShareLink()


class BuildSearchPostsBySidCreator(SearchCreator):
    def factory_method(self) -> SearchProduct:
        return BuildSearchPostsBySid()


"""
Below contains products of search. 
That's implements search's logic.
"""


class SearchProduct(ABC):
    """
    Interface of all Search-products that's implemented all search logic
    """

    @abstractmethod
    def operation(self, device,
                  payload: Namespace.payload) -> ApiSearchResponse:
        pass


class SearchBySid(SearchProduct):
    """
        Implements search method by sid
    """

    def operation(self, device,
                  payload: Namespace.payload) -> ApiSearchResponse:
        request = ApiSearchSidRequest(**payload)
        user = None
        if USE_CACHING:
            user = Database().fetch_cached_user_full_info(request.sid)
        if user is None:
            user = get_user_info(device, request.sid)

        if user.secret == 1:
            logging.warning("got response that this user is secret one")

        posts = None
        if request.amount_of_posts > 0 and user.secret != 1:
            if USE_CACHING:
                posts = Database().fetch_latest_cached_posts(request.sid, request.amount_of_posts)
            if posts is None or len(posts) == 0:
                posts = get_posts(device, request.sid,
                                  request.amount_of_posts)[:request.amount_of_posts]
                if USE_CACHING:
                    for item in posts:
                        Database().cache_post_info(item)

        return ApiSearchResponse(user, posts)


class BuildSearchBySid(SearchProduct):
    """
        Implements build search method by sid
    """

    def operation(self, device,
                  payload: Namespace.payload) -> ApiBuildedRequest:
        request = ApiSearchBuildSidRequest(**payload)
        packs = []
        for _ in range(request.count_requests):
            r = get_user_info_build_request(device, request.sid)
            packs.append(r)
            device = DevicePoll().get_device(proxy_on=False)

        return ApiBuildedRequest(packs)


class BuildSearchPostsBySid(SearchProduct):
    """
        Implements build search posts method by sid
    """

    def operation(self, device,
                  payload: Namespace.payload) -> ApiBuildedRequest:
        request = ApiSearchBuildSidRequest(**payload)

        packs = []
        for _ in range(0, request.count_requests):
            r = get_user_posts_build_request(device, request.sid, count=request.amount_of_posts)
            packs.append(r)
            device = DevicePoll().get_device(proxy_on=False)

        return ApiBuildedRequest(packs)


class SearchPostByShareLink(SearchProduct):
    """! Search user posts by `username`. """

    def operation(self, device,
                  payload: Namespace.payload) -> ApiSearchResponse:
        request = ApiPostSearchRequest(**payload)
        post = get_post(device, request.share_link, request.web_link,
                        request.short_link, request.aweme_id)
        return ApiPostSearchResponse(post)


class BuildSearchPostByShareLink(SearchProduct):
    """! Build request to search user posts by `username`. """

    def operation(self, device,
                  payload: Namespace.payload) -> ApiBuildedRequest:
        request = ApiPostSearchBuildRequest(**payload)
        posts = []
        for _ in range(request.count_requests):
            post = get_post_build_request(device, request.share_link, request.web_link,
                                          request.short_link, request.aweme_id)
            posts.append(post)
            device = DevicePoll().get_device(proxy_on=False)

        return ApiBuildedRequest(posts)


class SearchLikedPosts(SearchProduct):
    def operation(self, device,
                  payload: Namespace.payload) -> ApiSearchResponse:
        request = ApiSearchSidRequest(**payload)
        posts = None
        request.amount_of_posts = request.amount_of_posts if request.amount_of_posts > 0 else 20
        posts = get_liked_posts(device,
                                request.sid,
                                request.amount_of_posts,
                                full=True)[:request.amount_of_posts]

        return ApiLikedPostSearchResponse(posts)


def schedule_views(payload: Namespace.payload):
    request = ApiScheduleViewsRequest(**payload)
    DevicePoll().view_executor.schedule_global(request.aweme_id, request.amount)
