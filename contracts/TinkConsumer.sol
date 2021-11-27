// SPDX-License-Identifier: MIT
pragma solidity ^0.8.7;

import "@chainlink/contracts/src/v0.8/ChainlinkClient.sol";

/**
 * Request testnet LINK and ETH here: https://faucets.chain.link/
 * Find information on LINK Token Contracts and get the latest ETH and LINK faucets here: https://docs.chain.link/docs/link-token-contracts/
 */

contract TinkConsumer is ChainlinkClient {
    using Chainlink for Chainlink.Request;
  
    uint256 public balance;
    
    address private oracle;
    bytes32 private jobId;
    uint256 private fee;
    
    /**
     * Network: Kovan
     * Oracle: 0x479CF1F8DC88431E3414d08490E3E55214147984 (tink bridge naas)  
     * Job ID: f7cb6a19a9b44028916600f97b14d56a
     * Fee: 1 LINK
     */
    constructor() {
        setPublicChainlinkToken();
        oracle = 0x479CF1F8DC88431E3414d08490E3E55214147984;
        jobId = "f7cb6a19a9b44028916600f97b14d56a";
        fee = 1 * 10 ** 18; // (Varies by network and job)
    }
    
    /**
     * Create a Chainlink request to retrieve API response, find the target
     * data, then multiply by 1000000000000000000 (to remove decimal places from data).
     */
    function requestBalanceData() public returns (bytes32 requestId) 
    {
        Chainlink.Request memory request = buildChainlinkRequest(jobId, address(this), this.fulfill.selector);
        // Set the parameters for the bridge request
        request.add("request", "balance");
        // Sends the request
        return sendChainlinkRequestTo(oracle, request, fee);
    }
    
    /**
     * Receive the response in the form of uint256
     */ 
    function fulfill(bytes32 _requestId, uint256 _balance) public recordChainlinkFulfillment(_requestId)
    {
        balance = _balance;
    }

    // function withdrawLink() external {} - Implement a withdraw function to avoid locking your LINK in the contract
}
