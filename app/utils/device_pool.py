import logging
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED

import requests
from tiktok_mobile.models.tiktok_phone import TikTokPhone
from tiktok_mobile.utils.sender import HttpxSender
from tiktok_utils.proxy.providers.simple import proxy_provider_from_file
from tiktok_utils.proxy.providers.zeta import ZetaBatchProxyProvider, ZetaProviderArguments
from tiktok_utils.proxy.utils import load_socks5, wrap_requests_proxy

from app.db.database import Database
from app.utils.user_search import current_milli_time, create_phone
from app.utils.utils import singleton, format_except
from config.application import PROXY_FILE, DEVICES_SOURCE, DEFAULT_EXC_PAUSE, \
    MAX_ATTEMPTS_DEVICE_CREATION


@singleton
class DevicePoll:
    """! Container/Poll with prepared phones. """

    def __init__(self, device_pool_size: int = 10):

        logging.info("Device pull starting..")
        self._db_session = Database()
        self._thread_lock = threading.Lock()
        self.device_usage_lock = threading.Lock()
        self.device_pool_size = device_pool_size
        self.devices = []
        self._cursor = 0
        self._thread_pool_executor = ThreadPoolExecutor(max_workers=10)

        self.last_devices_reload_time = -1
        self.devices_reload_interval_millis = 60 * 60 * 1000

        if PROXY_FILE is not None and os.path.isfile(PROXY_FILE):
            self.proxy_service = proxy_provider_from_file(
                PROXY_FILE, modifier=load_socks5)
        else:
            self.proxy_service = ZetaBatchProxyProvider(
                zeta_arguments=ZetaProviderArguments(
                    application_name="tiktokViewer",
                    country_name="Indonesia",
                    booking_time_millis=0,
                    amount=10
                ),
                fetch_max_delay_ms=10 * 1000
            )
        self.load_devices()

    def load_devices(self):
        logging.warning("loading all devices")
        try:
            self.devices.clear()
            if DEVICES_SOURCE == "CREATE_NEW":
                self.create_devices(self.device_pool_size)
            elif DEVICES_SOURCE == "DATABASE":
                devices_from_db = self._db_session.fetch_created_devices(self.device_pool_size)
                for device in devices_from_db:
                    device.update_session(self.get_sender())
                self.devices.extend(devices_from_db)
            else:
                raise ValueError("incorrect devices source")
            self.last_devices_reload_time = sys.maxsize
        except Exception as e:
            logging.error(e)

    def get_sender(self):
        sender = HttpxSender(max_attempt=1, proxy_switcher=self.proxy_service)
        #sender = Sender(max_attempt=1, proxy_switcher=self.proxy_service)
        # adapter = requests.adapters.HTTPAdapter(pool_connections=1000,
        #                                             pool_maxsize=1000)
        # sender.mount("https://", adapter)
        # sender.mount("http://", adapter)
        return sender

    def get_device(self, proxy_on: bool = True) -> TikTokPhone:
        """! Get any device from devices queue pool. """
        self.device_usage_lock.acquire()
        if current_milli_time() - self.last_devices_reload_time > self.devices_reload_interval_millis:
            self.load_devices()

        logging.debug("Pulling device from Queue with Length: [%2d]",
                      len(self.devices))

        device: TikTokPhone = self.devices[self._cursor % len(self.devices)]
        self._cursor = (self._cursor + 1) % len(self.devices)

        self.device_usage_lock.release()
        return device

    def update_device_proxy(self, device=TikTokPhone) -> TikTokPhone:
        """Updating proxy of device"""
        proxy = self._get_proxy()
        device.session.proxies.update(proxy)
        return device

    def register_device(self):
        """Updating device in devices queue pool """
        for i in range(MAX_ATTEMPTS_DEVICE_CREATION):
            try:
                sender = self.get_sender()
                device = create_phone(sender)
                logging.warning(
                    "new device {} created on proxy proxy {}".format(device.device_id, str(device.session.proxies)))
                self.devices.append(device)
                self._thread_lock.acquire(True)
                self._db_session.insert_device(device)
                self._thread_lock.release()
                return

            except requests.exceptions.ConnectionError:
                logging.warning(
                    "Device not created. Connection error. Attempts: [%d]", i)
                time.sleep(DEFAULT_EXC_PAUSE)
                continue
            except Exception as e:
                logging.error(format_except(e))
                continue
        logging.warning(
            "All attempts to create device have failed")

    def create_devices(self, count: int):
        logging.info("Create [%2d] devices", count)
        futures = [self._thread_pool_executor.submit(self.register_device) for _ in range(self.device_pool_size)]
        counter = 0
        counter_completed_min_limit = 7
        while counter < counter_completed_min_limit:
            done, not_done = wait(futures, return_when=FIRST_COMPLETED)
            futures = not_done
            if len(done) != 0:
                future = done.pop()
                if not future.cancelled() and not future.exception():
                    counter += 1

    def _get_proxy(self) -> dict:
        return wrap_requests_proxy(self.proxy_service.next())