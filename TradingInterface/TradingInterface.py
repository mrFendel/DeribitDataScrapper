import AvailableCurrencies
from MSG_LIST import *

import asyncio
from websocket import WebSocketApp, enableTrace, ABNF
import threading
from threading import Thread

from datetime import datetime
import logging
import json
import time
import warnings
from typing import Optional, Union


class DeribitClient(Thread, WebSocketApp):
    websocket: Optional[WebSocketApp]

    def __init__(self, loopB):

        test_mode = True

        Thread.__init__(self)
        self.testMode = test_mode
        self.exchange_version = self._set_exchange()
        self.time = datetime.now()

        self.websocket = None
        self.loop = loopB
        asyncio.set_event_loop(self.loop)
        # Set logger settings
        logging.basicConfig(
            level="INFO",
            format='%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    def _set_exchange(self):
        if self.testMode:
            print("Initialized TEST NET mode")
            return 'wss://test.deribit.com/ws/api/v2'
        else:
            print("Initialized REAL MARKET mode")
            return 'wss://www.deribit.com/ws/api/v2'

    def run(self):
        self.websocket = WebSocketApp(self.exchange_version,
                                      on_message=self._on_message, on_open=self._on_open, on_error=self._on_error)
        # Run forever loop
        while True:
            try:
                self.websocket.run_forever()
            except:
                logging.error("Error at run_forever loop")
                # TODO: place here notificator
                continue

    def _on_error(self, websocket, error):
        # TODO: send Telegram notification
        logging.error(error)
        print("ERROR:", error)

    def _on_message(self, websocket, message):
        """
        Логика реакции на ответ сервера.
        :param websocket:
        :param message:
        :return:
        """
        response = json.loads(message)
        asyncio.run_coroutine_threadsafe(self._process_callback(response),
                                         loop=self.loop)

    async def _process_callback(self, response):
        logging.info(response)
        await asyncio.sleep(0.5)
        return 0

    def _on_open(self, websocket):
        logging.info("Client start his work")

    def send_new_request(self, request: dict):
        self.websocket.send(json.dumps(request), ABNF.OPCODE_TEXT)
        # TODO: do it better. Unsync.
        time.sleep(.1)


async def f():
    derLoop = asyncio.new_event_loop()

    deribitWorker = DeribitClient(loopB=derLoop)

    deribitWorker.start()
    th = threading.Thread(target=derLoop.run_forever)
    print("Thread started")
    th.start()
    # Very important time sleep. I spend smth around 3 hours to understand why my connection
    # is closed when i try to place new request :(
    time.sleep(1)
    deribitWorker.send_new_request(auth_message(client_id="W6-2Gwvq",
                                                client_secret="W9VQRlL7bIdc59DK2s7YrhqHTvw8k2U86nq_Tedsvfc"))

    deribitWorker.send_new_request(request_order_updates_to_currency(AvailableCurrencies.Currency.BITCOIN))
    deribitWorker.send_new_request(request=order_request(
        order_side="buy",
        instrument_name="BTC-PERPETUAL",
        amount=10_00,
        order_type="limit",
        order_price=21_134.5
    ))
    print("OK")

if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(f())
    loop.run_forever()
    time.sleep(1)
