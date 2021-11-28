pragma solidity ^0.4.24;

// Fusion between a UsdvJoin and a UsdvMove

contract GemLike {
    function transferFrom(address,address,uint) public returns (bool);
    function mint(address,uint) public;
    function burn(address,uint) public;
}

contract VatLike {
    function slip(bytes32,bytes32,int) public;
    function move(bytes32,bytes32,int) public;
    function flux(bytes32,bytes32,bytes32,int) public;
}

contract UsdvMock {
    VatLike public vat;
    GemLike public usdv;
    constructor(address vat_, address usdv_) public {
        vat = VatLike(vat_);
        usdv = GemLike(usdv_);
    }
    uint constant ONE = 10 ** 27;
    function mul(uint x, uint y) internal pure returns (int z) {
        z = int(x * y);
        require(int(z) >= 0);
        require(y == 0 || uint(z) / y == x);
    }
    mapping(address => mapping (address => bool)) public can;
    function hope(address guy) public { can[msg.sender][guy] = true; }
    function nope(address guy) public { can[msg.sender][guy] = false; }
    function move(address src, address dst, uint wad) public {
        require(src == msg.sender || can[src][msg.sender]);
        vat.move(bytes32(src), bytes32(dst), mul(ONE, wad));
    }
    function join(bytes32 urn, uint wad) public {
        vat.move(bytes32(address(this)), urn, mul(ONE, wad));
        usdv.burn(msg.sender, wad);
    }
    function exit(address guy, uint wad) public {
        vat.move(bytes32(msg.sender), bytes32(address(this)), mul(ONE, wad));
        usdv.mint(guy, wad);
    }
}
