# tinklock
cl-hackathon fall 2021 
decentralized escrow utilizing open banking api


## authentication setup for node operator

1. Register a tink account to attain client id and client secret
2. Enable continuous access
3. Save 'client_id', 'client_secret' and 'actor_client_id' to .env
4. Set up bridge and external adapter

## SC initialization

1. Seller lists offer (app)
2. Buyer notifies Seller (app)
3. Buyer and Seller both call initContract (through app)
4. (Contract waits until seller has completed tink authentication with node operator) 


## tink authentication

1. Node operator generates bearer token
2. Node operator creates tink 'user_id' (using bearer token)
3. Node operator generates auth code (using bearer token)
4. Node operator initiates credentials creation (using auth code)
5. Node operator sends credentials creation url to Seller
6. Seller opens url with browser and completes authentication (ex. BankID)
7. Callback to app/Seller registers 'credentialsId' with node operator
8. Node operator adds 'credentialsId' and 'user_id' to .env

## SC flow

0. (SC moves from State 'AWAITING_AUTHENTICATION' to 'AWAITING_COLLATERAL')
1. Buyer deposits asset collateral to SC through depositCollateral(), SC moves from State 'AWAITING_COLLATERAL' to 'AWAITING_FUNDS'
2. Seller deposits funds to SC through depositFunds(), SC moves from  State 'AWAITING_FUNDS' to 'AWAITING_FULFILLMENT'
3. Buyer deposits fiat to sellers bank account (Off-chain, communicated with app?)
4. Someone (Keeper?) calls confirmBalance (loophole- Seller can empty fiat account before Buyer is able to call the function, fiat account should be locked)
5a. if tinkPrice >= price, SC pays out funds and collateral to Buyer, SC moves from State 'AWAITING_FULFILLMENT' to 'FINISHED'
5b. if time >= timeInit + timeLock, SC pays out funds and collateral to Seller, SC moves from State 'AWAITING_FULFILLMENT' to 'FINISHED'


## improvements

- web3 application interface which handles offers and contract initialization
- integration with tink authentication, move credentials_id automatically to node
- add separate contract state awaiting tink authentication, node operator should trigger this event after account has been verified 
- in this stage the node operator should also verify that the bank account is reachable
- buyer and seller should deposit funds through application interface
- if seller never deposits funds, collateral should be withdrawable by buyer
- buyer should receive sellers IBAN through the app
- buyer should optionally interact through a tink link as well, such that the node operator can trigger confirmBalance through an external initiator
- seller must not be able to withdraw received fiat before confirmBalance is called
- confirmBalance should perhaps be called by a keeper