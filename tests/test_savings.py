# This file is part of Maker Keeper Framework.
#
# Copyright (C) 2019 grandizzy
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

import pytest

from pymaker import Address
from pymaker.deployment import DssDeployment
from pymaker.dsr import Dsr
from pymaker.numeric import Wad, Ray, Rad

from tests.test_dss import wrap_eth, frob


@pytest.fixture
def dsr(our_address: Address, mcd: DssDeployment) -> Dsr:
    return Dsr(mcd, our_address)


@pytest.mark.dependency()
def test_proxy(dsr):
    assert dsr.has_proxy() is False

    dsr.build_proxy().transact()
    assert dsr.has_proxy() is True


@pytest.mark.dependency(depends=['test_proxy'])
def test_join_and_exit(dsr):
    proxy = dsr.get_proxy()
    assert dsr.get_balance(proxy.address) == Wad.from_number(0)

    mcd = dsr.mcd

    # create a vault
    collateral = mcd.collaterals['ETH-C']
    wrap_eth(mcd, dsr.owner, Wad.from_number(2))
    collateral.approve(dsr.owner)
    assert collateral.adapter.join(dsr.owner, Wad.from_number(2)).transact(from_address=dsr.owner)
    frob(mcd, collateral, dsr.owner, dink=Wad.from_number(2), dart=Wad(0))
    dart = Wad.from_number(100)
    frob(mcd, collateral, dsr.owner, dink=Wad(0), dart=dart)

    # mint and withdraw all the Usdv
    mcd.approve_usdv(dsr.owner)
    assert mcd.usdv_adapter.exit(dsr.owner, dart).transact(from_address=dsr.owner)
    assert mcd.usdv.balance_of(dsr.owner) == dart

    initial_usdv_balance = mcd.usdv.balance_of(dsr.owner)
    assert initial_usdv_balance >= Wad.from_number(100)
    assert dsr.get_balance(proxy.address) == Wad.from_number(0)

    # approve Proxy to use 100 USDV from account
    mcd.usdv.approve(proxy.address, Wad.from_number(100)).transact(from_address=dsr.owner)

    # join 100 USDV in DSR
    assert dsr.join(Wad.from_number(100), proxy).transact(from_address=dsr.owner)
    assert mcd.usdv.balance_of(dsr.owner) == initial_usdv_balance - Wad.from_number(100)
    assert round(dsr.get_balance(proxy.address)) == Wad.from_number(100)
    assert mcd.pot.drip().transact()

    # exit 33 USDV from DSR
    assert dsr.exit(Wad.from_number(33), proxy).transact(from_address=dsr.owner)
    assert round(mcd.usdv.balance_of(dsr.owner)) == round(initial_usdv_balance) - Wad.from_number(100) + Wad.from_number(33)
    assert round(dsr.get_balance(proxy.address)) == Wad.from_number(67)
    assert mcd.pot.drip().transact()

    # exit remaining USDV from DSR and join to vat
    assert dsr.exit_all(proxy).transact(from_address=dsr.owner)
    assert round(mcd.usdv.balance_of(dsr.owner)) == round(initial_usdv_balance)
    assert dsr.get_balance(proxy.address) == Wad.from_number(0)
    assert mcd.usdv_adapter.join(dsr.owner, mcd.usdv.balance_of(dsr.owner)).transact(from_address=dsr.owner)

    # repay the vault
    assert collateral.ilk.dust == Rad(0)
    wipe: Wad = mcd.vat.get_wipe_all_dart(collateral.ilk, dsr.owner)
    frob(mcd, collateral, dsr.owner, dink=Wad(0), dart=wipe*-1)
