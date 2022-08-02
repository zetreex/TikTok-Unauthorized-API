# TikTok-Unauthorized API
Reverse engineered TikTok Mobile API. Only enpoints that do NOT require authorization (feed, post/user data, no-watermark, search, etc.) If you want access to API-through-authorization (like, follow, chat, stream, comment, etc.) feel free to contact us at info@zetreex.com or telegram @zetreex_api.

This repo uses Tiktok-Mobile-API and Tiktok-Utils repos which are private property of our company. 
API is actively maintained and could be tested without limits at rapidapi.com
https://rapidapi.com/zetreex-group-zetreex-group-default/api/tiktok-unauthorized-api-scraper-no-watermark-analytics-feed/details

## Prepare Environment

### Docker

```bash
# pull latest version of tiktok-api
cat GITHUB_TOKEN_FILE | docker login "https://ghcr.io" -u USERNAME --password-stdin
docker pull ghcr.io/some_private_user/tiktok-utils:dev
docker-compose up --detach --build app
```

### Pip

```bash
pip -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 manage.py
```

## All endpoints
###  apiops

| Method  | URI     | Name   | Summary |
|---------|---------|--------|---------|
| POST | /api/post | [find post by share link](#find-post-by-share-link) |  |
| POST | /api/search_full | [find user and full info about it](#find-user-and-full-info-about-it) |  |
| POST | /api/search_by_sid | [find user and info about it by sec user id](#find-user-and-info-about-it-by-sec-user-id) |  |
| POST | /api/search | [find user and info about it by username](#find-user-and-info-about-it-by-username) |  |
  


## Paths

### <span id="find-post-by-share-link"></span> find post by share link (*Find post by share link*)

```
POST /api/post
```

#### Parameters

| Name | Source | Type | Go type | Separator | Required | Default | Description |
|------|--------|------|---------|-----------| :------: |---------|-------------|
| X-Fields | `header` | mask (formatted string) | `string` |  |  |  | An optional fields mask |
| payload | `body` | [PostSearchRequest](#post-search-request) | `models.PostSearchRequest` | | ✓ | |  |

#### All responses
| Code | Status | Description | Has headers | Schema |
|------|--------|-------------|:-----------:|--------|
| [200](#find-post-by-share-link-200) | OK | Success |  | [schema](#find-post-by-share-link-200-schema) |

#### Responses


##### <span id="find-post-by-share-link-200"></span> 200 - Success
Status: OK

###### <span id="find-post-by-share-link-200-schema"></span> Schema
   
  

[PostSearchResponse](#post-search-response)

### <span id="find-user-and-full-info-about-it"></span> find user and full info about it (*Find user and full info about it*)

```
POST /api/search_full
```

#### Parameters

| Name | Source | Type | Go type | Separator | Required | Default | Description |
|------|--------|------|---------|-----------| :------: |---------|-------------|
| X-Fields | `header` | mask (formatted string) | `string` |  |  |  | An optional fields mask |
| payload | `body` | [SearchRequest](#search-request) | `models.SearchRequest` | | ✓ | |  |

#### All responses
| Code | Status | Description | Has headers | Schema |
|------|--------|-------------|:-----------:|--------|
| [200](#find-user-and-full-info-about-it-200) | OK | Success |  | [schema](#find-user-and-full-info-about-it-200-schema) |

#### Responses


##### <span id="find-user-and-full-info-about-it-200"></span> 200 - Success
Status: OK

###### <span id="find-user-and-full-info-about-it-200-schema"></span> Schema
   
  

[SearchResponseFull](#search-response-full)

### <span id="find-user-and-info-about-it-by-sec-user-id"></span> find user and info about it by sec user id (*Find user and info about it by `sec_user_id`*)

```
POST /api/search_by_sid
```

#### Parameters

| Name | Source | Type | Go type | Separator | Required | Default | Description |
|------|--------|------|---------|-----------| :------: |---------|-------------|
| X-Fields | `header` | mask (formatted string) | `string` |  |  |  | An optional fields mask |
| payload | `body` | [SearchSidRequest](#search-sid-request) | `models.SearchSidRequest` | | ✓ | |  |

#### All responses
| Code | Status | Description | Has headers | Schema |
|------|--------|-------------|:-----------:|--------|
| [200](#find-user-and-info-about-it-by-sec-user-id-200) | OK | Success |  | [schema](#find-user-and-info-about-it-by-sec-user-id-200-schema) |

#### Responses


##### <span id="find-user-and-info-about-it-by-sec-user-id-200"></span> 200 - Success
Status: OK

###### <span id="find-user-and-info-about-it-by-sec-user-id-200-schema"></span> Schema
   
  

[SearchResponse](#search-response)

### <span id="find-user-and-info-about-it-by-username"></span> find user and info about it by username (*Find user and info about it by `username`*)

```
POST /api/search
```

#### Parameters

| Name | Source | Type | Go type | Separator | Required | Default | Description |
|------|--------|------|---------|-----------| :------: |---------|-------------|
| X-Fields | `header` | mask (formatted string) | `string` |  |  |  | An optional fields mask |
| payload | `body` | [SearchRequest](#search-request) | `models.SearchRequest` | | ✓ | |  |

#### All responses
| Code | Status | Description | Has headers | Schema |
|------|--------|-------------|:-----------:|--------|
| [200](#find-user-and-info-about-it-by-username-200) | OK | Success |  | [schema](#find-user-and-info-about-it-by-username-200-schema) |

#### Responses


##### <span id="find-user-and-info-about-it-by-username-200"></span> 200 - Success
Status: OK

###### <span id="find-user-and-info-about-it-by-username-200-schema"></span> Schema
   
  

[SearchResponse](#search-response)

## Models

### <span id="post-info"></span> PostInfo


  



**Properties**

| Name | Type | Go type | Required | Default | Description | Example |
|------|------|---------|:--------:| ------- |-------------|---------|
| animated_cover | string| `string` | ✓ | | Animated cover of post |  |
| aweme_id | string| `string` | ✓ | | Id of post |  |
| cover | string| `string` | ✓ | | Usual cover of post |  |



### <span id="post-info-full"></span> PostInfoFull


  



**Properties**

| Name | Type | Go type | Required | Default | Description | Example |
|------|------|---------|:--------:| ------- |-------------|---------|
| animated_cover | string| `string` | ✓ | | Animated cover of post |  |
| aweme_id | string| `string` | ✓ | | Id of post |  |
| cover | string| `string` | ✓ | | Usual cover of post |  |
| download_links | []string| `[]string` | ✓ | | Download URL of post |  |
| play_links | []string| `[]string` | ✓ | | Download URL of post |  |
| share_link | string| `string` | ✓ | | Full URL to share post |  |
| short_link | string| `string` | ✓ | | Short URL to share post |  |
| web_link | string| `string` | ✓ | | Web URL to share post |  |



### <span id="post-search-request"></span> PostSearchRequest


  



**Properties**

| Name | Type | Go type | Required | Default | Description | Example |
|------|------|---------|:--------:| ------- |-------------|---------|
| share_link | string| `string` |  | | Share link |  |
| short_link | string| `string` |  | | Short link |  |
| web_link | string| `string` |  | | Web link |  |



### <span id="post-search-response"></span> PostSearchResponse


  



**Properties**

| Name | Type | Go type | Required | Default | Description | Example |
|------|------|---------|:--------:| ------- |-------------|---------|
| posts | [PostInfoFull](#post-info-full)| `PostInfoFull` |  | |  |  |



### <span id="search-request"></span> SearchRequest


  



**Properties**

| Name | Type | Go type | Required | Default | Description | Example |
|------|------|---------|:--------:| ------- |-------------|---------|
| amount_of_posts | integer| `int64` |  | | Number of posts |  |
| username | string| `string` | ✓ | | Username of searching user |  |



### <span id="search-response"></span> SearchResponse


  



**Properties**

| Name | Type | Go type | Required | Default | Description | Example |
|------|------|---------|:--------:| ------- |-------------|---------|
| posts | [][PostInfo](#post-info)| `[]*PostInfo` |  | |  |  |
| user | [UserInfo](#user-info)| `UserInfo` |  | |  |  |



### <span id="search-response-full"></span> SearchResponseFull


  



**Properties**

| Name | Type | Go type | Required | Default | Description | Example |
|------|------|---------|:--------:| ------- |-------------|---------|
| posts | [][PostInfoFull](#post-info-full)| `[]*PostInfoFull` |  | |  |  |
| user | [UserInfo](#user-info)| `UserInfo` |  | |  |  |



### <span id="search-sid-request"></span> SearchSidRequest


  



**Properties**

| Name | Type | Go type | Required | Default | Description | Example |
|------|------|---------|:--------:| ------- |-------------|---------|
| amount_of_posts | integer| `int64` |  | | Number of posts |  |
| sid | string| `string` | ✓ | | Secure user ID of searching user |  |



### <span id="user-info"></span> UserInfo


  



**Properties**

| Name | Type | Go type | Required | Default | Description | Example |
|------|------|---------|:--------:| ------- |-------------|---------|
| avatar | string| `string` | ✓ | | Url of user's avatar |  |
| followers | integer| `int64` | ✓ | | Number of followers |  |
| following | integer| `int64` | ✓ | | Number of following |  |
| likes | integer| `int64` | ✓ | | Number of likes |  |
| login_name | string| `string` | ✓ | | Login name of user |  |
| name | string| `string` | ✓ | | Name of user |  |
| sid | string| `string` | ✓ | | Secuserid of user |  |
