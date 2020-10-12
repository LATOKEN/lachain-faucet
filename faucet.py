import logging
from web3 import Web3
from jsonrpcserver import method, dispatch
from http.server import BaseHTTPRequestHandler, HTTPServer
import requests

nodeUrl = 'http://116.203.75.72:7070'
w3 = Web3(Web3.HTTPProvider(nodeUrl))

ADDRESS = Web3.toChecksumAddress('0x6bc32575acb8754886dc283c2c8ac54b1bd93195')
PRIVATE_KEY = bytes.fromhex('d95d6db65f3e2223703c5d8e205d98e3e6b470f067b0f94f6c6bf73d4301ce48')
CHAIN_ID = 41
NONCE = 0
FUND_AMOUNT = 2 * 10 ** 21
FUND_LIMIT = 10 * FUND_AMOUNT
LAST_BLOCK_CHECKED = 0


def signTransaction(to, value, privkey, nonce, gasPrice, gas):
    signed_txn = w3.eth.account.signTransaction(dict(
        nonce=nonce,
        gasPrice=gasPrice,
        gas=gas,
        to=to,
        value=value,
        data=b'',
        chainId=CHAIN_ID
    ), privkey)

    return signed_txn.rawTransaction.hex()


def get_nonce():
    global NONCE, LAST_BLOCK_CHECKED

    last_block = w3.eth.getBlock('latest')
    block_number = last_block['number']
    delta = block_number - LAST_BLOCK_CHECKED

    if delta < 0 or delta > 5:
        NONCE = w3.eth.getTransactionCount(ADDRESS)

    LAST_BLOCK_CHECKED = block_number

    result = NONCE

    NONCE += 1
    return result


@method
def get_money(address):
    global FUND_LIMIT, FUND_AMOUNT

    if not address.startswith('0x') or len(address) != 42:
        raise RuntimeError('Not an address')

    address = Web3.toChecksumAddress(address)

    if not Web3.isAddress(address):
        raise RuntimeError('Not an address')

    balance = w3.eth.getBalance(address)

    if balance > FUND_LIMIT:
        raise RuntimeError('Already funded')

    rawtx = signTransaction(address, FUND_AMOUNT, PRIVATE_KEY, nonce=get_nonce(), gasPrice=1, gas=4000000)
    resp = requests.post(
        nodeUrl,
        data='{"jsonrpc": "2.0", "method": "eth_sendRawTransaction", "id": "1", "params": ["' + rawtx + '"]}'
    )

    print(resp.json())
    return "ok"


class FaucetHttpServer(BaseHTTPRequestHandler):
    def do_POST(self):
        # Process request
        request = self.rfile.read(int(self.headers["Content-Length"])).decode()
        response = dispatch(request)
        # Return response
        self.send_response(response.http_status)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(str(response).encode())

    def do_OPTIONS(self):
        self.send_response(200, "ok")
        self.send_header('Access-Control-Allow-Credentials', 'true')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header("Access-Control-Allow-Headers", "X-Requested-With, Content-type")
        self.end_headers()

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        BaseHTTPRequestHandler.end_headers(self)


if __name__ == '__main__':
    NONCE = w3.eth.getTransactionCount(ADDRESS)

    block = w3.eth.getBlock('latest')
    LAST_BLOCK_CHECKED = block['number']

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler()
        ]
    )

    HTTPServer(("localhost", 3020), FaucetHttpServer).serve_forever()
