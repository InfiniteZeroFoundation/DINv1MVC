#!/bin/bash

show() {
    set -x
    "$@"
    { set +x; } 2>/dev/null
}

# Kill any existing hardhat node on port 8545
lsof -ti:8545 | xargs kill -9 2>/dev/null

# Start hardhat node in the background
cd /home/azureuser/projects/DINv1MVC/hardhat
npx hardhat node > /dev/null 2>&1 &

# Save the PID if you want to kill it later
HARDHAT_PID=$!

# Wait a moment for the node to initialize
sleep 3


echo -e "\n\n********************** Starting DIN Demo **********************\n\n"

source /home/azureuser/projects/pyDIN/.pyDIN/bin/activate > /dev/null

echo -e "\n-----------Navigating to DIN project directory-----------\n"

show cd /home/azureuser/projects/DINv1MVC

echo -e "\n---------------Running DIN CLI----------------------\n"

echo -e "\n....................Getting help....................\n"
show python -m dincli.main --help

python -m dincli.main system configure-network --network local > /dev/null


python -m dincli.main system connect-wallet --account 0 > /dev/null

python -m dincli.main dindao deploy din-coordinator --network local --artifact "/home/azureuser/projects/DINv1MVC/hardhat/artifacts/contracts/DinCoordinator.sol/DinCoordinator.json" > /dev/null

python -m dincli.main dindao deploy din-validator-stake --network local --artifact "/home/azureuser/projects/DINv1MVC/hardhat/artifacts/contracts/DinValidatorStake.sol/DinValidatorStake.json" > /dev/null


echo -e "\n................... Connecting wallet to DIN cli as Model Owner ...................\n"
echo -e "command: python -m dincli.main system connect-wallet <private key>\n"
python -m dincli.main system connect-wallet --account 1


echo "y" | python -m dincli.main system buy-usdt 3000 --network local > /dev/null


echo -e "\n................... Deploying DIN Task Coordinator Contract as Model Owner ...................\n"
show python -m dincli.main model-owner deploy task-coordinator --network local --artifact "/home/azureuser/projects/DINv1MVC/hardhat/artifacts/contracts/DINTaskCoordinator.sol/DINTaskCoordinator.json"


echo -e "\n................... Deploying DIN Task Auditor Contract as Model Owner ...................\n"
show python -m dincli.main model-owner deploy task-auditor --network local --artifact "/home/azureuser/projects/DINv1MVC/hardhat/artifacts/contracts/DINTaskAuditor.sol/DINTaskAuditor.json"


echo -e "\n................... Depositing reward in DIN Task Auditor Contract as Model Owner for Learners e.g Farmers ...................\n"
show python -m dincli.main model-owner deposit-reward-in-dintask-auditor --network local --amount 1000 


python -m dincli.main system connect-wallet --account 0 > /dev/null

python -m dincli.main dindao add-slasher --taskCoordinator --network local > /dev/null

python -m dincli.main system connect-wallet --account 1 > /dev/null

python -m dincli.main model-owner add-slasher --taskCoordinator --network local > /dev/null

python -m dincli.main system connect-wallet --account 0 > /dev/null

python -m dincli.main dindao add-slasher --taskAuditor --network local > /dev/null

python -m dincli.main system connect-wallet --account 1 > /dev/null

python -m dincli.main model-owner add-slasher --taskAuditor --network local > /dev/null

echo -e "\n................... Creating Genesis Model as Model Owner ...................\n"

show python -m dincli.main model-owner model create-genesis --network local 

echo -e "\n................... Submitting Genesis Model as Model Owner with initial score of 10 ...................\n"
show python -m dincli.main model-owner model submit-genesis --network local --score 10

kill $HARDHAT_PID 2>/dev/null