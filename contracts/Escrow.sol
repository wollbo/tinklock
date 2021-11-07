pragma solidity ^0.8.0;

import "../zeppelin-solidity/contracts/ownership/Ownable.sol";

contract Escrow {
    //Schedule job with Cron
    //Add checks for bank API being reachable and correct
    //Add CL-EA for value of bank account

    //Variables
    enum State {NOT_INITIATED, AWAITING_COLLATERAL, AWAITING_FUNDS, AWAITING_FULFILLMENT, FINISHED}

    State public currentState;

    bool public buyerConfirm;
    bool public sellerConfirm;

    uint public time; // current time, updated in confirmBalance()
    uint public timeInit; // UNIX timestamp, initiated upon completion of AWAITING_FUNDS
    uint public timeLock; // UNIX time; 1 Week = 604800

    uint public price;
    uint public tinkPrice; // price retrieved by CL-EA

    uint public funds;
    uint public collateral;

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
    constructor(address payable _buyer, address payable _seller, uint _timeLock, uint _price, uint _funds){
        buyer = _buyer;
        seller = _seller;
        timeLock = _timeLock;
        price = _price; // SEK, USD ?
        funds = _funds; // LINK, ETHER ?
        collateral = funds * 0.01; // 1% deposit
    }

    function initContract() escrowNotStarted public {// First called by Seller, then by Buyer
        if (msg.sender == buyer) {
            buyerConfirm = true;
        }
        if (msg.sender == seller) {
            sellerConfirm = true;
        }
        if (buyerConfirm && sellerConfirm) {
            currentState = State.AWAITING_COLLATERAL;
        }
    }

    function depositCollateral() onlyBuyer public payable {// Buyer is required to deposit collateral
        require(currentState == State.AWAITING_COLLATERAL, "Already collateralized");
        require(msg.value == collateral, "Wrong collateral amount");
        currentState = State.AWAITING_FUNDS;
    }

    function depositFunds() onlySeller public payable {// Seller deposits funds
        require(currentState == State.AWAITING_FUNDS, "Already funded");
        require(msg.value == funds, "Wrong deposit amount");
        currentState = State.AWAITING_FULFILLMENT;
        timeInit = 1636309800; // Get this from offchain
    }

    function confirmBalance() {// Calls external adapter to get bank balance
        require(currentState == State.AWAITING_FULFILLMENT, "Cannot settle");
        tinkPrice = ExternalAdapter(tinkLink);
        if (time >= timeInit + timeLock) { // time limit exceeded, seller gets funds and collateral
            seller.transfer(collateral);
            seller.transfer(funds);
            currentState = State.FINISHED;
        }
        if (tinkPrice >= price) // succesful payout of funds and collateral
            buyer.transfer(collateral);
            buyer.transfer(funds);
            currentState = State.FINISHED;
    }
}