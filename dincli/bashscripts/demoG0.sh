#!/bin/bash



source /home/azureuser/projects/pyDIN/.pyDIN/bin/activate 


show cd /home/azureuser/projects/DINv1MVC



python -m dincli.main system configure-network --network local 


python -m dincli.main system connect-wallet --account 0 

python -m dincli.main dindao deploy din-coordinator --network local --artifact "/home/azureuser/projects/DINv1MVC/hardhat/artifacts/contracts/DinCoordinator.sol/DinCoordinator.json" 

python -m dincli.main dindao deploy din-validator-stake --network local --artifact "/home/azureuser/projects/DINv1MVC/hardhat/artifacts/contracts/DinValidatorStake.sol/DinValidatorStake.json" 


python -m dincli.main system connect-wallet --account 1


echo "y" | python -m dincli.main system buy-usdt 3000 --network local


python -m dincli.main model-owner deploy task-coordinator --network local --artifact "/home/azureuser/projects/DINv1MVC/hardhat/artifacts/contracts/DINTaskCoordinator.sol/DINTaskCoordinator.json"


python -m dincli.main model-owner deploy task-auditor --network local --artifact "/home/azureuser/projects/DINv1MVC/hardhat/artifacts/contracts/DINTaskAuditor.sol/DINTaskAuditor.json"


python -m dincli.main model-owner deposit-reward-in-dintask-auditor --network local --amount 1000 


python -m dincli.main system connect-wallet --account 0 

python -m dincli.main dindao add-slasher --taskCoordinator --network local 

python -m dincli.main system connect-wallet --account 1

python -m dincli.main model-owner add-slasher --taskCoordinator --network local 

python -m dincli.main system connect-wallet --account 0 

python -m dincli.main dindao add-slasher --taskAuditor --network local 

python -m dincli.main system connect-wallet --account 1

python -m dincli.main model-owner add-slasher --taskAuditor --network local 

python -m dincli.main model-owner model create-genesis --network local 

python -m dincli.main model-owner model submit-genesis --network local 

