// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {ERC721} from "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";

contract BadgeNFT is ERC721, Ownable {
    uint256 private nextTokenId;

    enum VerificationStatus {
        Unverified,
        Pending,
        Verified,
        Rejected,
        Revoked
    }

    struct Experience {
        bytes32 certHash;
        address student;
        address issuer;
        string category;
        string experienceType;
        VerificationStatus status;
        uint256 submittedAt;
        uint256 verifiedAt;
    }

    mapping(uint256 => Experience) private experiences;
    mapping(address => bool) public approvedIssuers;
    mapping(address => uint256[]) private studentExperiences;

    event IssuerApproved(address indexed issuer);
    event IssuerRemoved(address indexed issuer);

    event ExperienceSubmitted(
        uint256 indexed tokenId, address indexed student, bytes32 certHash, string category, string experienceType
    );

    event ExperienceVerified(uint256 indexed tokenId, address indexed issuer);

    event ExperienceRejected(uint256 indexed tokenId, address indexed issuer);

    event ExperienceRevoked(uint256 indexed tokenId, address indexed revokedBy);

    modifier onlyApprovedIssuer() {
        require(approvedIssuers[msg.sender], "Not approved issuer");
        _;
    }

    constructor() ERC721("Student Experience Badge", "SEB") Ownable(msg.sender) {}

    function approveIssuer(address issuer) external onlyOwner {
        require(issuer != address(0), "Invalid issuer address");
        approvedIssuers[issuer] = true;

        emit IssuerApproved(issuer);
    }

    function removeIssuer(address issuer) external onlyOwner {
        require(approvedIssuers[issuer], "Issuer not approved");
        approvedIssuers[issuer] = false;

        emit IssuerRemoved(issuer);
    }

    /*
        學生自行上傳經歷
        狀態預設為 Pending
    */
    function submitExperience(bytes32 certHash, string calldata category, string calldata experienceType)
        external
        returns (uint256)
    {
        require(certHash != bytes32(0), "Invalid certHash");
        require(bytes(category).length > 0, "Category required");
        require(bytes(experienceType).length > 0, "Experience type required");

        uint256 tokenId = nextTokenId;
        nextTokenId++;

        _safeMint(msg.sender, tokenId);

        experiences[tokenId] = Experience({
            certHash: certHash,
            student: msg.sender,
            issuer: address(0),
            category: category,
            experienceType: experienceType,
            status: VerificationStatus.Pending,
            submittedAt: block.timestamp,
            verifiedAt: 0
        });

        studentExperiences[msg.sender].push(tokenId);

        emit ExperienceSubmitted(tokenId, msg.sender, certHash, category, experienceType);

        return tokenId;
    }

    /*
        發證單位直接發行已驗證經歷
    */
    function issueBadge(address student, bytes32 certHash, string calldata category, string calldata experienceType)
        external
        onlyApprovedIssuer
        returns (uint256)
    {
        require(student != address(0), "Invalid student address");
        require(certHash != bytes32(0), "Invalid certHash");
        require(bytes(category).length > 0, "Category required");
        require(bytes(experienceType).length > 0, "Experience type required");

        uint256 tokenId = nextTokenId;
        nextTokenId++;

        _safeMint(student, tokenId);

        experiences[tokenId] = Experience({
            certHash: certHash,
            student: student,
            issuer: msg.sender,
            category: category,
            experienceType: experienceType,
            status: VerificationStatus.Verified,
            submittedAt: block.timestamp,
            verifiedAt: block.timestamp
        });

        studentExperiences[student].push(tokenId);

        emit ExperienceSubmitted(tokenId, student, certHash, category, experienceType);

        emit ExperienceVerified(tokenId, msg.sender);

        return tokenId;
    }

    /*
        發證單位驗證學生自行上傳的經歷
    */
    function verifyExperience(uint256 tokenId) external onlyApprovedIssuer {
        require(_ownerOf(tokenId) != address(0), "Experience does not exist");

        Experience storage exp = experiences[tokenId];

        require(
            exp.status == VerificationStatus.Pending || exp.status == VerificationStatus.Unverified,
            "Cannot verify this experience"
        );

        exp.issuer = msg.sender;
        exp.status = VerificationStatus.Verified;
        exp.verifiedAt = block.timestamp;

        emit ExperienceVerified(tokenId, msg.sender);
    }

    /*
        發證單位拒絕驗證
    */
    function rejectExperience(uint256 tokenId) external onlyApprovedIssuer {
        require(_ownerOf(tokenId) != address(0), "Experience does not exist");

        Experience storage exp = experiences[tokenId];

        require(exp.status == VerificationStatus.Pending, "Cannot reject this experience");

        exp.issuer = msg.sender;
        exp.status = VerificationStatus.Rejected;

        emit ExperienceRejected(tokenId, msg.sender);
    }

    /*
        撤銷已驗證經歷
    */
    function revokeBadge(uint256 tokenId) external {
        require(_ownerOf(tokenId) != address(0), "Experience does not exist");

        Experience storage exp = experiences[tokenId];

        require(msg.sender == exp.issuer || msg.sender == owner(), "Not authorized");

        require(exp.status == VerificationStatus.Verified, "Only verified experience can be revoked");

        exp.status = VerificationStatus.Revoked;

        emit ExperienceRevoked(tokenId, msg.sender);
    }

    function getExperience(uint256 tokenId)
        external
        view
        returns (
            bytes32 certHash,
            address student,
            address issuer,
            string memory category,
            string memory experienceType,
            VerificationStatus status,
            uint256 submittedAt,
            uint256 verifiedAt
        )
    {
        require(_ownerOf(tokenId) != address(0), "Experience does not exist");

        Experience memory exp = experiences[tokenId];

        return (
            exp.certHash,
            exp.student,
            exp.issuer,
            exp.category,
            exp.experienceType,
            exp.status,
            exp.submittedAt,
            exp.verifiedAt
        );
    }

    function getStudentExperiences(address student) external view returns (uint256[] memory) {
        return studentExperiences[student];
    }

    function isExperienceVerified(uint256 tokenId) external view returns (bool) {
        require(_ownerOf(tokenId) != address(0), "Experience does not exist");

        return experiences[tokenId].status == VerificationStatus.Verified;
    }
}
