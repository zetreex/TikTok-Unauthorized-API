import os

DEVICES_IN_POOL = int(os.getenv("DEVICES_IN_POOL", 30))
DEFAULT_EXC_PAUSE = int(os.getenv("DEFAULT_EXC_PAUSE", 3))
PROXY_FILE = "app/proxy/socks5_proxies.txt"
MAX_ATTEMPTS_DEVICE_CREATION = 10
DEVICES_SOURCE = os.getenv("DEVICES_SOURCE", "CREATE_NEW")
USE_CACHING = os.getenv("USE_POSTS_CACHING", True)

print(os.getcwd())