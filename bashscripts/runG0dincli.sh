#!/bin/bash

show() {
    set -x
    "$@"
    { set +x; } 2>/dev/null
}



# show python -m dincli.main system dataset distribute-mnist --seed 42 --network local --test 


# show python -m dincli.main system reset-all
# show python -m dincli.main system init
# show python -m dincli.main system configure-network  --network local
# show python -m dincli.main system configure-logging --level debug
# show python -m dincli.main system todo

show dincli system connect-wallet --account 0
show dincli dindao deploy din-coordinator --network local --artifact "/home/azureuser/projects/DINv1MVC/hardhat/artifacts/contracts/DinCoordinator.sol/DinCoordinator.json"

# show dincli system dump-abi --official --artifact "/home/azureuser/projects/DINv1MVC/hardhat/artifacts/contracts/DinCoordinator.sol/DinCoordinator.json"

# show dincli system dump-abi --official --artifact "/home/azureuser/projects/DINv1MVC/hardhat/artifacts/contracts/DinToken.sol/DinToken.json"

show dincli dindao deploy din-validator-stake --network local --artifact "/home/azureuser/projects/DINv1MVC/hardhat/artifacts/contracts/DinValidatorStake.sol/DinValidatorStake.json"

# show dincli system dump-abi --official --artifact "/home/azureuser/projects/DINv1MVC/hardhat/artifacts/contracts/DinValidatorStake.sol/DinValidatorStake.json"

show dincli dindao deploy din-model-registry --network local --artifact "/home/azureuser/projects/DINv1MVC/hardhat/artifacts/contracts/DINModelRegistry.sol/DINModelRegistry.json"

# show dincli system dump-abi --official --artifact "/home/azureuser/projects/DINv1MVC/hardhat/artifacts/contracts/DINModelRegistry.sol/DINModelRegistry.json"

show dincli system connect-wallet --account 1
show dincli system --eth-balance --usdt-balance 

show dincli system buy-usdt 3000 --network local --yes


show dincli model-owner deploy task-coordinator --network local --artifact "/home/azureuser/projects/DINv1MVC/hardhat/artifacts/contracts/DINTaskCoordinator.sol/DINTaskCoordinator.json"

# show dincli system dump-abi --artifact "/home/azureuser/projects/DINv1MVC/hardhat/artifacts/contracts/DINTaskCoordinator.sol/DINTaskCoordinator.json"

# show dincli system dump-abi --artifact "/home/azureuser/projects/DINv1MVC/hardhat/artifacts/contracts/DINTaskCoordinator.sol/DINTaskCoordinator.json" --official

show dincli model-owner deploy task-auditor --network local --artifact "/home/azureuser/projects/DINv1MVC/hardhat/artifacts/contracts/DINTaskAuditor.sol/DINTaskAuditor.json"

# show dincli system dump-abi --artifact "/home/azureuser/projects/DINv1MVC/hardhat/artifacts/contracts/DINTaskAuditor.sol/DINTaskAuditor.json"

# show dincli system dump-abi --artifact "/home/azureuser/projects/DINv1MVC/hardhat/artifacts/contracts/DINTaskAuditor.sol/DINTaskAuditor.json" --official



show dincli model-owner deposit-reward-in-dintask-auditor --network local --amount 1000 

show dincli system connect-wallet --account 0

show dincli dindao add-slasher --taskCoordinator --network local

show dincli system connect-wallet --account 1

show dincli model-owner add-slasher --taskCoordinator --network local 

show dincli system connect-wallet --account 0

show dincli dindao add-slasher --taskAuditor --network local


show dincli system connect-wallet --account 1

show dincli model-owner add-slasher --taskAuditor --network local 




show dincli system connect-wallet --account 1


show dincli model-owner model create-genesis --network local 

show dincli model-owner model submit-genesis --network local 

show dincli task model-owner register --network local 

show dincli system connect-wallet --account 0

show dincli dindao registry total-models --network local

show dincli task explore --model-id 0 --network local 


