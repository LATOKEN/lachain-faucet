import time

import rlp
from ethereum import transactions
from jsonrpcserver import method, serve
import requests

# 0x838a80e082dbcb72741f903fe1b479ea87fba8cd

ADDRESS = '0x6bc32575acb8754886dc283c2c8ac54b1bd93195'
PRIVATE_KEY = bytes.fromhex('d95d6db65f3e2223703c5d8e205d98e3e6b470f067b0f94f6c6bf73d4301ce48')
CUR_NONCE = int(requests.post(
    'http://116.203.75.72:7070',
    data='{"jsonrpc": "2.0", "method": "eth_getTransactionCount", "id": "1", '
         '"params": ["0x6bc32575acb8754886dc283c2c8ac54b1bd93195", 0]}'
).json()['result'])
LAST_TIME = time.time() - 1000.0
CHAIN_ID = 41


def signTransaction(to, value, privkey, nonce, gasPrice, gas, data):
    tx = transactions.Transaction(nonce, gasPrice, gas, bytes.fromhex(to[2:]), value, data, 0, 0, 0)
    tx._in_mutable_context = True
    tx = tx.sign(privkey)
    tx._in_mutable_context = True
    tx.v += 8 + 2 * CHAIN_ID
    tx._cached_rlp = None
    return rlp.encode(tx).hex()


@method
def get_money(address):
    global LAST_TIME, CUR_NONCE
    now = time.time()
    if LAST_TIME > now - 15.0:
        raise RuntimeError('Not ready yet!')
    LAST_TIME = now
    rawtx = signTransaction(address, 10 ** 21, PRIVATE_KEY, nonce=CUR_NONCE, gasPrice=1, gas=4000000000, data=bytes())
    print(rawtx)
    resp = requests.post(
        'http://116.203.75.72:7070',
        data='{"jsonrpc": "2.0", "method": "eth_sendRawTransaction", "id": "1", "params": ["' + rawtx + '"]}'
    )
    print(resp)
    print(resp.json())
    CUR_NONCE += 1
    return "ok"


if __name__ == '__main__':
    print('cur nonce:', CUR_NONCE)
    serve()
