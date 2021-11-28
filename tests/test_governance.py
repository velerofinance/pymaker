# This file is part of Maker Keeper Framework.
#
# Copyright (C) 2019 EdNoepel
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
from web3 import Web3, HTTPProvider

from pymaker import Address
from pymaker.auth import DSAuth
from pymaker.governance import DSPause, DSChief
from pymaker.numeric import Wad
from pymaker.deployment import DssDeployment
from datetime import datetime, timedelta

from tests.test_dss import mint_vdgt

def mint_approve_lock(mcd: DssDeployment, amount: Wad, address: Address):
    prevBalance = mcd.vdgt.balance_of(address)
    mint_vdgt(mcd.vdgt, address, amount)
    assert mcd.vdgt.balance_of(address) == amount + prevBalance

    # Lock VDGT in DS-Chief
    assert mcd.vdgt.approve(mcd.ds_chief.address).transact(from_address=address)
    assert mcd.ds_chief.lock(amount).transact(from_address=address)
    assert mcd.vdgt.balance_of(address) == prevBalance

def approve_iou_free_vdgt(mcd: DssDeployment, amount: Wad, address: Address):
    prevBalance = mcd.vdgt.balance_of(address)
    iou = mcd.ds_chief.iou()
    assert iou.approve(mcd.ds_chief.address).transact(from_address=address)
    assert mcd.ds_chief.free(amount).transact(from_address=address)
    assert mcd.vdgt.balance_of(address) == amount + prevBalance

# Relevant to DS-Chief 1.2 
def launch_chief(mcd: DssDeployment, address: Address):
    launchAmount = Wad.from_number(80000)
    mint_approve_lock(mcd, launchAmount, address)

    # Vote on address(0) to activate DSChief.launch()
    zero_address = Address("0x0000000000000000000000000000000000000000")
    assert mcd.ds_chief.vote_yays([zero_address.address]).transact(from_address=address)

    # Launch Ds-Chief (1.2)
    assert mcd.ds_chief.launch().transact(from_address=address)
    approve_iou_free_vdgt(mcd, launchAmount, address)


@pytest.mark.skip(reason="not fully implemented")
class TestDSPause:
    def setup_method(self):
        self.web3 = Web3(HTTPProvider("http://localhost:8555"))
        self.web3.eth.defaultAccount = self.web3.eth.accounts[0]
        self.our_address = Address(self.web3.eth.defaultAccount)

        ds_auth = DSAuth.deploy(self.web3)
        self.ds_pause = DSPause.deploy(self.web3, 5, self.our_address, ds_auth)

        self.plan = DSPause.Plan(usr=self.our_address,
                                 fax=self.web3.toBytes(text='abi.encodeWithSignature("sig()")'),
                                 eta=(datetime.utcnow() + timedelta(seconds=10)))

    def test_drop(self):
        # assert self.ds_pause.plot(self.plan).transact()
        assert self.ds_pause.drop(self.plan).transact()

    def test_exec(self):
        # assert self.ds_pause.plot(self.plan).transact()
        assert self.ds_pause.exec(self.plan).transact()

class TestDSChief:

    def test_launch(self, mcd: DssDeployment, our_address: Address):
        assert mcd.ds_chief.live() == False
        launch_chief(mcd, our_address)
        assert mcd.ds_chief.live() == True

    def test_scenario(self, mcd: DssDeployment, our_address: Address, other_address: Address):
        isinstance(mcd, DssDeployment)
        isinstance(our_address, Address)

        amount = Wad.from_number(1000)
        mint_approve_lock(mcd, amount, our_address)

        # Vote for our address
        assert mcd.ds_chief.vote_yays([our_address.address]).transact(from_address=our_address)
        assert mcd.ds_chief.etch([other_address.address]).transact(from_address=our_address)

        # Confirm that etch(our address) != etch(other address)
        etches = mcd.ds_chief.past_etch(3)
        assert etches[0].slate !=  etches[-1].slate

        assert mcd.ds_chief.get_approvals(our_address.address) == amount

        # Lift hat for our address
        assert mcd.ds_chief.get_hat() != our_address
        assert mcd.ds_chief.lift(our_address).transact(from_address=our_address)
        assert mcd.ds_chief.get_hat() == our_address

        # Now vote for other address
        assert mcd.ds_chief.vote_etch(etches[-1]).transact(from_address=our_address)
        assert mcd.ds_chief.lift(other_address).transact(from_address=our_address)
        assert mcd.ds_chief.get_hat() == other_address

        approve_iou_free_vdgt(mcd, amount, our_address)

