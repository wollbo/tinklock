# tinklock
cl-hackathon fall 2021 
decentralized escrow utilizing open banking api
![alt text](https://github.com/wollbo/tinklock/blob/main/logo.png?raw=true)


## authentication setup for node operator

1. Register a tink account to attain client id and client secret
2. Enable continuous access
3. Save 'client_id', 'client_secret' and 'actor_client_id' to .env
4. Set up bridge and external adapter
5. Seller completes tink authentication with bridge

## tink authentication

1. Node operator generates bearer token
2. Node operator creates tink 'user_id' (using bearer token)
3. Node operator generates auth code (using bearer token)
4. Node operator initiates credentials creation (using auth code)
5. Node operator sends credentials creation url to Seller
6. Seller opens url with browser and completes authentication (ex. BankID)
7. Callback to app/Seller registers 'credentialsId' with node operator
8. Node operator adds 'credentialsId' and 'user_id' to .env

## API consumer

1. Node operator deploys TinkConsumer.sol which is linked to Sellers bank account
2. Seller funds TinkConsumer contract with LINK

## SC initialization

1. Seller lists offer
2. Buyer notifies Seller 
3. Buyer and Seller both call initContract

## SC flow

1. Seller deposits funds to SC through depositFunds(), SC moves from  State 'AWAITING_FUNDS' to 'AWAITING_FULFILLMENT'
2. Buyer deposits fiat to sellers bank account (Off-chain)
4. The function confirmBalance() is called until either condition is triggered  
5. tinkPrice >= price, SC pays out funds to Buyer, SC moves from State 'AWAITING_FULFILLMENT' to 'FINISHED'
6. (to be implemented; timer/timeout)


## improvements

- web3 application interface which handles offers and contract initialization
- integration with tink authentication, move credentials_id automatically to node
- add separate contract state awaiting tink authentication, node operator should trigger this event after account has been verified 
- in this stage the node operator should also verify that the bank account is reachable
- buyer should deposit collateral to avoid spoofing
- add a timer to avoid credentials timeout and funds being stuck forever
- buyer and seller should deposit collateral and funds through application interface
- if seller never deposits funds, collateral should be withdrawable by buyer
- buyer should receive sellers IBAN through the app
- seller must not be able to withdraw received fiat before confirmBalance is called
