// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "./TinkConsumer.sol";


contract SimpleEscrow {
    //Schedule job with Cron
    //Add checks for bank API being reachable and correct
    //Buyer needs to be confident that seller has registered the correct account
    //Add CL-EA for value of bank account

    //Variables
    //Add another state 'AWAITING_AUTHENTICATION'?
    enum State {NOT_INITIATED, AWAITING_FUNDS, AWAITING_FULFILLMENT, FINISHED}

    State public currentState;
    TinkConsumer public tinkConsumer;

    bool public buyerConfirm;
    bool public sellerConfirm;

    uint public price;      // fiat price agreed to by seller and buyer for sale of funds
    uint public tinkBalance;  // fiat price retrieved by CL-EA from sellers bank account
    uint public initBalance; // fiat price retrieved by CL-EA from seller before deposit

    uint public funds;      // amount of tokens for sale
    address public tinkAddress;

    address payable public buyer;
    address payable public seller;

    //Modifiers
    modifier onlyBuyer() {
        require(msg.sender == buyer, "Only the buyer can call this function");
        _;
    }

    modifier onlySeller() {
        require(msg.sender == seller, "Only the seller can call this function");
        _;
    }

    modifier escrowNotStarted(){
        require(currentState == State.NOT_INITIATED);
        _;
    }

    //Functions
    constructor(address payable _buyer, address payable _seller, address _tinkAdress, uint _price, uint _funds){
        buyer = _buyer;
        seller = _seller;
        price = _price; // SEK
        funds = _funds * (0.01 ether); // 0.01 ether = 10 Finney
        tinkAddress = _tinkAdress;
    }

    function existingConsumer() public {
        tinkConsumer = TinkConsumer(tinkAddress);
    }

    function initContract() escrowNotStarted public {// First called by Seller, then by Buyer
        if (msg.sender == buyer) {
            buyerConfirm = true;
        }
        if (msg.sender == seller) {
            sellerConfirm = true;
        }
        if (buyerConfirm && sellerConfirm) {
            existingConsumer();
            currentState = State.AWAITING_FUNDS;
        }
    }

    function requestTinkBalance() public view returns (uint result) {// Queries EA to get bank account balance of seller
        return tinkConsumer.balance();
    }

    function depositFunds() onlySeller public payable {// Seller deposits funds
        require(currentState == State.AWAITING_FUNDS, "Already funded");
        require(msg.value == funds, "Wrong deposit amount");
        initBalance = requestTinkBalance(); // Up to seller to confirm that his initial account balance is correct
        currentState = State.AWAITING_FULFILLMENT;
    }

    function confirmBalance() public payable {// Calls external adapter to get bank balance
        require(currentState == State.AWAITING_FULFILLMENT, "Cannot settle");
        tinkBalance = requestTinkBalance();
        if (tinkBalance >= (initBalance + price)) // succesful payout of funds and collateral
            buyer.transfer(funds);
            currentState = State.FINISHED;
    }

    function withdraw() onlySeller public payable {
        require(currentState == State.AWAITING_FULFILLMENT, "Cannot withdraw");
        require(msg.sender == seller);
        seller.transfer(funds);
        currentState = State.FINISHED;
    }
}