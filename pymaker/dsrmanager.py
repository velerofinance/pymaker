
# This file is part of Maker Keeper Framework.
#
# Copyright (C) 2020 Maker Ecosystem Growth Holdings, INC
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


from web3 import Web3
from pymaker import Address, Contract, Transact
from pymaker.dss import Pot
from pymaker.join import UsdvJoin
from pymaker.numeric import Wad, Rad
from pymaker.token import DSToken


class DsrManager(Contract):
    """
    A client for the `DsrManger` contract, which reduces the need for proxies
    when interacting with the Pot contract.

    Ref. <https://github.com/velerofinance/dsr-manager/blob/master/src/DsrManager.sol>
    """

    abi = Contract._load_abi(__name__, 'abi/DsrManager.abi')
    bin = Contract._load_bin(__name__, 'abi/DsrManager.bin')

    def __init__(self, web3: Web3, address: Address):
        assert isinstance(web3, Web3)
        assert isinstance(address, Address)

        self.web3 = web3
        self.address = address
        self._contract = self._get_contract(web3, self.abi, address)

    def pot(self) -> Pot:
        address = Address(self._contract.functions.pot().call())
        return Pot(self.web3, address)

    def usdv(self) -> DSToken:
        address = Address(self._contract.functions.usdv().call())
        return DSToken(self.web3, address)

    def usdv_adapter(self) -> UsdvJoin:
        address = Address(self._contract.functions.usdvJoin().call())
        return UsdvJoin(self.web3, address)

    def supply(self) -> Wad:
        """Total supply of pie locked in Pot through DsrManager"""
        return Wad(self._contract.functions.supply().call())

    def pie_of(self, usr: Address) -> Wad:
        """Pie balance of a given usr address"""
        assert isinstance(usr, Address)

        return Wad(self._contract.functions.pieOf(usr.address).call())

    def usdv_of(self, usr: Address) -> Rad:
        """
        Internal Usdv balance of a given usr address - current Chi is used
        i.e. Usdv balance potentially stale
        """
        assert isinstance(usr, Address)

        pie = self.pie_of(usr)
        chi = self.pot().chi()

        usdv = Rad(pie) * Rad(chi)

        return usdv

    def join(self, dst: Address, usdv: Wad) -> Transact:
        """Lock a given amount of ERC20 USDV into the DSR Contract and give to dst address """
        assert isinstance(dst, Address)
        assert isinstance(usdv, Wad)

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'join',
                        [dst.address, usdv.value])

    def exit(self, dst: Address, usdv: Wad) -> Transact:
        """ Free a given amount of ERC20 Usdv from the DSR Contract and give to dst address """
        assert isinstance(dst, Address)
        assert isinstance(usdv, Wad)

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'exit',
                        [dst.address, usdv.value])

    def exitAll(self, dst: Address) -> Transact:
        """ Free all ERC20 Usdv from the DSR Contract and give to dst address """
        assert isinstance(dst, Address)

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'exitAll', [dst.address])

    def __repr__(self):
        return f"DsrManager('{self.address}')"
