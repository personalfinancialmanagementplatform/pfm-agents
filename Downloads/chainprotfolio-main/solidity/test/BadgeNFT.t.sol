// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {Test} from "forge-std/Test.sol";
import {BadgeNFT} from "../src/BadgeNFT.sol";

contract BadgeNFTTest is Test {
    BadgeNFT public badgeNFT;

    address public owner = address(1);
    address public issuer = address(2);
    address public student = address(3);

    bytes32 public certHash = keccak256("test certificate");

    function setUp() public {
        vm.prank(owner);
        badgeNFT = new BadgeNFT();

        vm.prank(owner);
        badgeNFT.approveIssuer(issuer);
    }

    function testIssuerCanIssueBadge() public {
        vm.prank(issuer);
        uint256 tokenId = badgeNFT.issueBadge(student, certHash, "Competition", "AI Hackathon");

        assertEq(tokenId, 0);
        assertEq(badgeNFT.ownerOf(tokenId), student);

        bool verified = badgeNFT.isExperienceVerified(tokenId);
        assertTrue(verified);
    }

    function testStudentCanSubmitExperience() public {
        vm.prank(student);
        uint256 tokenId = badgeNFT.submitExperience(certHash, "Competition", "AI Hackathon");

        uint256[] memory experiences = badgeNFT.getStudentExperiences(student);

        assertEq(tokenId, 0);
        assertEq(experiences.length, 1);
        assertEq(experiences[0], 0);
    }

    function testIssuerCanVerifyExperience() public {
        vm.prank(student);
        uint256 tokenId = badgeNFT.submitExperience(certHash, "Competition", "AI Hackathon");

        vm.prank(issuer);
        badgeNFT.verifyExperience(tokenId);

        bool verified = badgeNFT.isExperienceVerified(tokenId);
        assertTrue(verified);
    }
}
