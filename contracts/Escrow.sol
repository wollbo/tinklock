pragma solidity ^0.8.0;


contract Escrow {
    //Schedule job with Cron
    //Add checks for bank API being reachable and correct
    //Buyer needs to be confident that seller has registered the correct account
    //Add CL-EA for value of bank account

    //Variables
    enum State {NOT_INITIATED, AWAITING_COLLATERAL, AWAITING_FUNDS, AWAITING_FULFILLMENT, FINISHED}

    State public currentState;

    bool public buyerConfirm;
    bool public sellerConfirm;

    uint public time;       // current time, updated in confirmBalance()
    uint public timeInit;   // UNIX timestamp, initiated upon completion of AWAITING_FUNDS
    uint public timeLock;   // UNIX time; 1 Week = 604800, MAX is <90 days due to open banking laws

    uint public price;      // fiat price agreed to by seller and buyer for sale of funds
    uint public tinkPrice;  // fiat price retrieved by CL-EA from sellers bank account

    uint public funds;      // amount of tokens for sale
    uint public collateral; // percentage amount of funds held as collateral

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
        collateral = funds; // 100% deposit -> fix to be a percentage
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
        //Consider adding another timer here
    }

    function depositFunds() onlySeller public payable {// Seller deposits funds
        require(currentState == State.AWAITING_FUNDS, "Already funded");
        require(msg.value == funds, "Wrong deposit amount");
        currentState = State.AWAITING_FULFILLMENT;
        timeInit = 1636309800; // Get this from offchain
    }

    function requestTinkBalance() public onlyBuyer {// Buyer queries sellers bank account to verify payment
    // This should be called by the node operator

    }

    function getTime() public {// Get unix timestamp from offchain

    }

    function confirmBalance() public payable {// Calls external adapter to get bank balance
        require(currentState == State.AWAITING_FULFILLMENT, "Cannot settle");
        time = getTime(); // get time from CL-node ?
        if (time >= timeInit + timeLock) { // time limit exceeded, seller gets funds and collateral
            seller.transfer(collateral);
            seller.transfer(funds);
            currentState = State.FINISHED;
        }
        tinkPrice = requestTinkBalance();
        if (tinkPrice >= price) // succesful payout of funds and collateral
            buyer.transfer(collateral);
            buyer.transfer(funds);
            currentState = State.FINISHED;
    }
}