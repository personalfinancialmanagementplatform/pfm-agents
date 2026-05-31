// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {Script} from "forge-std/Script.sol";
import {BadgeNFT} from "../src/BadgeNFT.sol";

contract DeployBadgeNFT is Script {
    function run() external returns (BadgeNFT) {
        vm.startBroadcast();

        BadgeNFT badgeNFT = new BadgeNFT();

        vm.stopBroadcast();

        return badgeNFT;
    }
}
