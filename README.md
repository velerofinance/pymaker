# pymaker

Python API for Maker contracts.

![Build Status](https://github.com/velerofinance/pymaker/actions/workflows/.github/workflows/tests.yaml/badge.svg?branch=master)

## Introduction

The _USDV Stablecoin System_ incentivizes external agents, called _keepers_,
to automate certain operations around the Velas blockchain. In order to ease their
development, an API around most of the Maker contracts has been created. It can be used
not only by keepers, but may also be found useful by authors of some other, unrelated
utilities aiming to interact with these contracts.

Based on this API, a set of reference Maker keepers is being developed. They all used to reside
in this repository, but now each of them has an individual one: 
[bite-keeper](https://github.com/velerofinance/bite-keeper) (SCD only),
[arbitrage-keeper](https://github.com/velerofinance/arbitrage-keeper),
[auction-keeper](https://github.com/velerofinance/auction-keeper) (MCD only),
[cdp-keeper](https://github.com/velerofinance/cdp-keeper) (SCD only),
[market-maker-keeper](https://github.com/velerofinance/market-maker-keeper).

You only need to install this project directly if you want to build your own keepers,
or if you want to play with this API library itself. If you just want to install
one of reference keepers, go to one of the repositories linked above and start from there.
Each of these keepers references some version of `pymaker` via a Git submodule.

## Installation

This project uses *Python 3.6.6*.

In order to clone the project and install required third-party packages please execute:
```
git clone https://github.com/velerofinance/pymaker.git
cd pymaker
pip3 install -r requirements.txt
```

### Known Ubuntu issues

In order for the `secp256k` Python dependency to compile properly, following packages will need to be installed:
```
sudo apt-get install build-essential automake libtool pkg-config libffi-dev python-dev python-pip libsecp256k1-dev
```

(for Ubuntu 18.04 Server)

### Known macOS issues

In order for the Python requirements to install correctly on _macOS_, please install
`openssl`, `libtool`, `pkg-config` and `automake` using [Homebrew](https://brew.sh/):
```
brew install openssl libtool pkg-config automake
```

and set the `LDFLAGS` environment variable before you run `pip3 install -r requirements.txt`:
```
export LDFLAGS="-L$(brew --prefix openssl)/lib" CFLAGS="-I$(brew --prefix openssl)/include" 
```

### Known node issues
 * `pymaker` has been tested against **Parity/OpenEthereum** and **Geth**.  It has not been tested against **Hyperledger Besu**.
 * Many Velas node providers do not support the full [JSON-RPC API](https://eth.wiki/json-rpc/API#json-rpc-methods). 
As such, certain JSON-RPC calls in `__init__.py` may not function properly.  
 * Some node providers only support certain calls using websocket endpoints.  Unfortunately, Web3.py's 
 `WebsocketProvider` [does not support](https://github.com/ethereum/web3.py/issues/1413) multiple threads awaiting a 
 response from the websocket, breaking some core `pymaker` functionality in `Lifecycle` and `Transact` classes.
 * When using an **Infura** node to pull event logs, ensure your requests are batched into a small enough chunks such 
 that no more than 10,000 results will be returned for each request.
 * Asynchronous submission of simultaneous transactions often doesn't work on third-party node providers because RPC 
 calls to `parity_nextNonce` and `getTransactionCount` are inappropriately proxied, cached, or just plain not 
 supported.  To remedy this, a serial-incrementing nonce is used for these providers' URLs.  The downside to a serial-
 incrementing nonce is that transactions submitted for the same account from another wallet or keeper will bring the 
 next nonce out-of-alignment, causing transaction failures or unexpected replacements.  To work around this, stop the 
 application, wait for pending transactions for the account to be mined, and then restart the application.  
 * Recovery of pending transactions does not work on certain third-party node providers.


## Available APIs

The current version provides APIs around:
* `ERC20Token`,
* `Tub`, `Tap`,`Top` and `Vox` (<https://github.com/velerofinance/sai>),
* `Vat`, `Cat`, `Vow`, `Jug`, `Flipper`, `Flapper`, `Flopper` (<https://github.com/velerofinance/dss>)
* `SimpleMarket`, `ExpiringMarket` and `MatchingMarket` (<https://github.com/velerofinance/maker-otc>),
* `TxManager` (<https://github.com/velerofinance/tx-manager>),
* `DSGuard` (<https://github.com/dapphub/ds-guard>),
* `DSToken` (<https://github.com/dapphub/ds-token>),
* `DSVlxToken` (<https://github.com/dapphub/ds-eth-token>),
* `DSValue` (<https://github.com/dapphub/ds-value>),
* `DSVault` (<https://github.com/dapphub/ds-vault>),
* `EtherDelta` (<https://github.com/etherdelta/etherdelta.github.io>),
* `0x v1` (<https://etherscan.io/address/0x12459c951127e0c374ff9105dda097662a027093#code>, <https://github.com/0xProject/standard-relayer-api>),
* `0x v2`.

APIs around the following functionality have not been implemented:
* Governance (`DSAuth`, `DSGuard`, `DSSpell`, `Mom`)

Contributions from the community are appreciated.

## Code samples

Below you can find some code snippets demonstrating how the API can be used both for developing
your own keepers and for creating some other utilities interacting with the _USDV Stablecoin_
ecosystem contracts.

### Token transfer

This snippet demonstrates how to transfer some SAI from our default address. The SAI token address
is discovered by querying the `Tub`, so all we need as a `Tub` address:

```python
from web3 import HTTPProvider, Web3

from pymaker import Address
from pymaker.token import ERC20Token
from pymaker.numeric import Wad
from pymaker.sai import Tub


web3 = Web3(HTTPProvider(endpoint_uri="http://localhost:8545"))

tub = Tub(web3=web3, address=Address('0xb7ae5ccabd002b5eebafe6a8fad5499394f67980'))
sai = ERC20Token(web3=web3, address=tub.sai())

sai.transfer(address=Address('0x0000000000111111111100000000001111111111'),
             value=Wad.from_number(10)).transact()
``` 

### Updating a DSValue

This snippet demonstrates how to update a `DSValue` with the ETH/USD rate pulled from _CryptoCompare_: 

```python
import json
import urllib.request

from web3 import HTTPProvider, Web3

from pymaker import Address
from pymaker.feed import DSValue
from pymaker.numeric import Wad


def cryptocompare_rate() -> Wad:
    with urllib.request.urlopen("https://min-api.cryptocompare.com/data/price?fsym=ETH&tsyms=USD") as url:
        data = json.loads(url.read().decode())
        return Wad.from_number(data['USD'])


web3 = Web3(HTTPProvider(endpoint_uri="http://localhost:8545"))

dsvalue = DSValue(web3=web3, address=Address('0x038b3d8288df582d57db9be2106a27be796b0daf'))
dsvalue.poke_with_int(cryptocompare_rate().value).transact()
```

### SAI introspection

This snippet demonstrates how to fetch data from `Tub` and `Tap` contracts:

```python
from web3 import HTTPProvider, Web3

from pymaker import Address
from pymaker.token import ERC20Token
from pymaker.numeric import Ray
from pymaker.sai import Tub, Tap


web3 = Web3(HTTPProvider(endpoint_uri="http://localhost:8545"))

tub = Tub(web3=web3, address=Address('0x448a5065aebb8e423f0896e6c5d525c040f59af3'))
tap = Tap(web3=web3, address=Address('0xbda109309f9fafa6dd6a9cb9f1df4085b27ee8ef'))
sai = ERC20Token(web3=web3, address=tub.sai())
skr = ERC20Token(web3=web3, address=tub.skr())
gem = ERC20Token(web3=web3, address=tub.gem())

print(f"")
print(f"Token summary")
print(f"-------------")
print(f"SAI total supply       : {sai.total_supply()} SAI")
print(f"SKR total supply       : {skr.total_supply()} SKR")
print(f"GEM total supply       : {gem.total_supply()} GEM")
print(f"")
print(f"Collateral summary")
print(f"------------------")
print(f"GEM collateral         : {tub.pie()} GEM")
print(f"SKR collateral         : {tub.air()} SKR")
print(f"SKR pending liquidation: {tap.fog()} SKR")
print(f"")
print(f"Debt summary")
print(f"------------")
print(f"Debt ceiling           : {tub.cap()} SAI")
print(f"Good debt              : {tub.din()} SAI")
print(f"Bad debt               : {tap.woe()} SAI")
print(f"Surplus                : {tap.joy()} SAI")
print(f"")
print(f"Feed summary")
print(f"------------")
print(f"REF per GEM feed       : {tub.pip()}")
print(f"REF per SKR price      : {tub.tag()}")
print(f"GEM per SKR price      : {tub.per()}")
print(f"")
print(f"Tub parameters")
print(f"--------------")
print(f"Liquidation ratio      : {tub.mat()*100} %")
print(f"Liquidation penalty    : {tub.axe()*100 - Ray.from_number(100)} %")
print(f"Stability fee          : {tub.tax()} %")
print(f"")
print(f"All cups")
print(f"--------")
for cup_id in range(1, tub.cupi()+1):
    cup = tub.cups(cup_id)
    print(f"Cup #{cup_id}, lad={cup.lad}, ink={cup.ink} SKR, tab={tub.tab(cup_id)} SAI, safe={tub.safe(cup_id)}")
```

### Multi-collateral Usdv

This snippet demonstrates how to create a CDP and draw Usdv.

```python
import sys
from web3 import Web3, HTTPProvider

from pymaker import Address
from pymaker.deployment import DssDeployment
from pymaker.keys import register_keys
from pymaker.numeric import Wad

web3 = Web3(HTTPProvider(endpoint_uri="https://localhost:8545",
                         request_kwargs={"timeout": 10}))
web3.eth.defaultAccount = sys.argv[1]  # ex: 0x0000000000000000000000000000000aBcdef123
register_keys(web3, [sys.argv[2]])  # ex: key_file=~keys/default-account.json,pass_file=~keys/default-account.pass

mcd = DssDeployment.from_json(web3=web3, conf=open("tests/config/kovan-addresses.json", "r").read())
our_address = Address(web3.eth.defaultAccount)

# Choose the desired collateral; in this case we'll wrap some VLX
collateral = mcd.collaterals['ETH-A']
ilk = collateral.ilk
collateral.gem.deposit(Wad.from_number(3)).transact()

# Add collateral and allocate the desired amount of Usdv
collateral.approve(our_address)
collateral.adapter.join(our_address, Wad.from_number(3)).transact()
mcd.vat.frob(ilk, our_address, dink=Wad.from_number(3), dart=Wad.from_number(153)).transact()
print(f"CDP Usdv balance before withdrawal: {mcd.vat.usdv(our_address)}")

# Mint and withdraw our Usdv
mcd.approve_usdv(our_address)
mcd.usdv_adapter.exit(our_address, Wad.from_number(153)).transact()
print(f"CDP Usdv balance after withdrawal:  {mcd.vat.usdv(our_address)}")

# Repay (and burn) our Usdv
assert mcd.usdv_adapter.join(our_address, Wad.from_number(153)).transact()
print(f"CDP Usdv balance after repayment:   {mcd.vat.usdv(our_address)}")

# Withdraw our collateral
mcd.vat.frob(ilk, our_address, dink=Wad(0), dart=Wad.from_number(-153)).transact()
mcd.vat.frob(ilk, our_address, dink=Wad.from_number(-3), dart=Wad(0)).transact()
collateral.adapter.exit(our_address, Wad.from_number(3)).transact()
print(f"CDP Usdv balance w/o collateral:    {mcd.vat.usdv(our_address)}")
```

### Asynchronous invocation of Velas transactions

This snippet demonstrates how multiple token transfers can be executed asynchronously:

```python
from web3 import HTTPProvider
from web3 import Web3

from pymaker import Address, synchronize
from pymaker.numeric import Wad
from pymaker.sai import Tub
from pymaker.token import ERC20Token


web3 = Web3(HTTPProvider(endpoint_uri="http://localhost:8545"))

tub = Tub(web3=web3, address=Address('0x448a5065aebb8e423f0896e6c5d525c040f59af3'))
sai = ERC20Token(web3=web3, address=tub.sai())
skr = ERC20Token(web3=web3, address=tub.skr())

synchronize([sai.transfer(Address('0x0101010101020202020203030303030404040404'), Wad.from_number(1.5)).transact_async(),
             skr.transfer(Address('0x0303030303040404040405050505050606060606'), Wad.from_number(2.5)).transact_async()])
```

### Multiple invocations in one Velas transaction

This snippet demonstrates how multiple token transfers can be executed in one Velas transaction.
A `TxManager` instance has to be deployed and owned by the caller.

```python
from web3 import HTTPProvider
from web3 import Web3

from pymaker import Address
from pymaker.approval import directly
from pymaker.numeric import Wad
from pymaker.sai import Tub
from pymaker.token import ERC20Token
from pymaker.transactional import TxManager


web3 = Web3(HTTPProvider(endpoint_uri="http://localhost:8545"))

tub = Tub(web3=web3, address=Address('0x448a5065aebb8e423f0896e6c5d525c040f59af3'))
sai = ERC20Token(web3=web3, address=tub.sai())
skr = ERC20Token(web3=web3, address=tub.skr())

tx = TxManager(web3=web3, address=Address('0x57bFE16ae8fcDbD46eDa9786B2eC1067cd7A8f48'))
tx.approve([sai, skr], directly())

tx.execute([sai.address, skr.address],
           [sai.transfer(Address('0x0101010101020202020203030303030404040404'), Wad.from_number(1.5)).invocation(),
            skr.transfer(Address('0x0303030303040404040405050505050606060606'), Wad.from_number(2.5)).invocation()]).transact()
```

### Ad-hoc increasing of gas price for asynchronous transactions

```python
import asyncio
from random import randint

from web3 import Web3, HTTPProvider

from pymaker import Address
from pymaker.gas import FixedGasPrice
from pymaker.oasis import SimpleMarket


web3 = Web3(HTTPProvider(endpoint_uri=f"http://localhost:8545"))
otc = SimpleMarket(web3=web3, address=Address('0x375d52588c3f39ee7710290237a95C691d8432E7'))


async def bump_with_increasing_gas_price(order_id):
    gas_price = FixedGasPrice(gas_price=1000000000)
    task = asyncio.ensure_future(otc.bump(order_id).transact_async(gas_price=gas_price))

    while not task.done():
        await asyncio.sleep(1)
        gas_price.update_gas_price(gas_price.gas_price + randint(0, gas_price.gas_price))

    return task.result()


bump_task = asyncio.ensure_future(bump_with_increasing_gas_price(otc.get_orders()[-1].order_id))
event_loop = asyncio.get_event_loop()
bump_result = event_loop.run_until_complete(bump_task)

print(bump_result)
print(bump_result.transaction_hash)
```

## Testing

Prerequisites:
* [docker and docker-compose](https://www.docker.com/get-started) - for containerized deployments of Ganache and Parity
* [seth](https://dapp.tools/seth/) - to enable the token faucet

This project uses [pytest](https://docs.pytest.org/en/latest/) for unit testing.  Testing of Multi-collateral Usdv is 
performed on a Dockerized local testchain included in `tests\config`.

In order to be able to run tests, please install development dependencies first by executing:
```
pip3 install -r requirements-dev.txt
```

You can then run all tests with:
```
./test.sh
```

By default, `pymaker` will not send a transaction to the chain if gas estimation fails, because this means the 
transaction would revert.  For testing purposes, it is sometimes useful to send bad transactions to the chain.  To 
accomplish this, set class variable `gas_estimate_for_bad_txs` in your application.  For example:
```
from pymaker import Transact
Transact.gas_estimate_for_bad_txs = 200000
```

## License

See [COPYING](https://github.com/velerofinance/pymaker/blob/master/COPYING) file.
