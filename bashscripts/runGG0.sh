#!/bin/bash

show() {
    set -x
    "$@"
    { set +x; } 2>/dev/null
}


show python -m dincli.main ipfs upload --file-path /home/azureuser/projects/DINv1MVC/tasks/local/0x54Ff998A8368Aa028b44d889D91F49fF5C2AC3cf/services/modelowner.py --name modelowner.py

show python -m dincli.main ipfs upload --file-path /home/azureuser/projects/DINv1MVC/dincli/services/aggregator.py --name aggregator.py

show python -m dincli.main ipfs upload --file-path /home/azureuser/projects/DINv1MVC/tasks/local/0x54Ff998A8368Aa028b44d889D91F49fF5C2AC3cf/services/model.py --name model.py

show python -m dincli.main ipfs upload --file-path /home/azureuser/projects/DINv1MVC/dincli/services/auditor.py --name auditor.py



cp /home/azureuser/projects/DINv1MVC/tasks/local/0x54Ff998A8368Aa028b44d889D91F49fF5C2AC3cf/dataset/test/test_dataset.pt /home/azureuser/.cache/dincli/local/model_0/dataset/test/test_dataset.pt


show python -m dincli.main system dataset distribute-mnist --seed 42 --network local --clients --num-clients 9 --model-id 0

# show python -m dincli.main system dataset distribute-mnist --seed 42 --network local --clients --numm-clients 9


show python -m dincli.main system connect-wallet --account 1
show python -m dincli.main model-owner gi start --network local --model-id 0



show python -m dincli.main system connect-wallet --account 1
show python -m dincli.main model-owner gi reg aggregators-open --network local --model-id 0

show python -m dincli.main system connect-wallet --account 11
show python -m dincli.main aggregator dintoken buy 1 --network local

show python -m dincli.main system connect-wallet --account 12
show python -m dincli.main aggregator dintoken buy 1 --network local

show python -m dincli.main system connect-wallet --account 13
show python -m dincli.main aggregator dintoken buy 1 --network local

show python -m dincli.main system connect-wallet --account 14
show python -m dincli.main aggregator dintoken buy 1 --network local

show python -m dincli.main system connect-wallet --account 15
show python -m dincli.main aggregator dintoken buy 1 --network local

show python -m dincli.main system connect-wallet --account 16
show python -m dincli.main aggregator dintoken buy 1 --network local

show python -m dincli.main system connect-wallet --account 17
show python -m dincli.main aggregator dintoken buy 1 --network local

show python -m dincli.main system connect-wallet --account 18
show python -m dincli.main aggregator dintoken buy 1 --network local

show python -m dincli.main system connect-wallet --account 19
show python -m dincli.main aggregator dintoken buy 1 --network local

show python -m dincli.main system connect-wallet --account 20
show python -m dincli.main aggregator dintoken buy 1 --network local

show python -m dincli.main system connect-wallet --account 21
show python -m dincli.main aggregator dintoken buy 1 --network local

show python -m dincli.main system connect-wallet --account 22
show python -m dincli.main aggregator dintoken buy 1 --network local

show python -m dincli.main system connect-wallet --account 11
show python -m dincli.main aggregator dintoken stake 1000000 --network local

show python -m dincli.main aggregator dintoken read-stake --network local

show python -m dincli.main aggregator register --network local --model-id 0


show python -m dincli.main system connect-wallet --account 12
show python -m dincli.main aggregator dintoken stake 1000000 --network local

show python -m dincli.main aggregator dintoken read-stake --network local

show python -m dincli.main aggregator register --network local --model-id 0


show python -m dincli.main system connect-wallet --account 13
show python -m dincli.main aggregator dintoken stake 1000000 --network local

show python -m dincli.main aggregator dintoken read-stake --network local

show python -m dincli.main aggregator register --network local --model-id 0


show python -m dincli.main system connect-wallet --account 14
show python -m dincli.main aggregator dintoken stake 1000000 --network local

show python -m dincli.main aggregator dintoken read-stake --network local

show python -m dincli.main aggregator register --network local --model-id 0


show python -m dincli.main system connect-wallet --account 15
show python -m dincli.main aggregator dintoken stake 1000000 --network local

show python -m dincli.main aggregator dintoken read-stake --network local

show python -m dincli.main aggregator register --network local --model-id 0


show python -m dincli.main system connect-wallet --account 16
show python -m dincli.main aggregator dintoken stake 1000000 --network local

show python -m dincli.main aggregator dintoken read-stake --network local

show python -m dincli.main aggregator register --network local --model-id 0


show python -m dincli.main system connect-wallet --account 17
show python -m dincli.main aggregator dintoken stake 1000000 --network local

show python -m dincli.main aggregator dintoken read-stake --network local

show python -m dincli.main aggregator register --network local --model-id 0


show python -m dincli.main system connect-wallet --account 18
show python -m dincli.main aggregator dintoken stake 1000000 --network local

show python -m dincli.main aggregator dintoken read-stake --network local

show python -m dincli.main aggregator register --network local --model-id 0


show python -m dincli.main system connect-wallet --account 19
show python -m dincli.main aggregator dintoken stake 1000000 --network local

show python -m dincli.main aggregator dintoken read-stake --network local

show python -m dincli.main aggregator register --network local --model-id 0


show python -m dincli.main system connect-wallet --account 20
show python -m dincli.main aggregator dintoken stake 1000000 --network local

show python -m dincli.main aggregator dintoken read-stake --network local

show python -m dincli.main aggregator register --network local --model-id 0


show python -m dincli.main system connect-wallet --account 21
show python -m dincli.main aggregator dintoken stake 1000000 --network local

show python -m dincli.main aggregator dintoken read-stake --network local

show python -m dincli.main aggregator register --network local --model-id 0


show python -m dincli.main system connect-wallet --account 22
show python -m dincli.main aggregator dintoken stake 1000000 --network local

show python -m dincli.main aggregator dintoken read-stake --network local

show python -m dincli.main aggregator register --network local --model-id 0


show python -m dincli.main system connect-wallet --account 1

show python -m dincli.main model-owner gi show-registered-aggregators --network local --model-id 0

show python -m dincli.main model-owner gi reg aggregators-close --network local --model-id 0

show python -m dincli.main model-owner gi reg auditors-open --network local --model-id 0



show python -m dincli.main system connect-wallet --account 50
show python -m dincli.main auditor dintoken buy 1 --network local
show python -m dincli.main auditor dintoken stake 1000000 --network local
show python -m dincli.main auditor dintoken read-stake --network local
show python -m dincli.main auditor register --network local --model-id 0

show python -m dincli.main system connect-wallet --account 51
show python -m dincli.main auditor dintoken buy 1 --network local
show python -m dincli.main auditor dintoken stake 1000000 --network local
show python -m dincli.main auditor dintoken read-stake --network local
show python -m dincli.main auditor register --network local --model-id 0

show python -m dincli.main system connect-wallet --account 52
show python -m dincli.main auditor dintoken buy 1 --network local
show python -m dincli.main auditor dintoken stake 1000000 --network local
show python -m dincli.main auditor dintoken read-stake --network local
show python -m dincli.main auditor register --network local --model-id 0

show python -m dincli.main system connect-wallet --account 53
show python -m dincli.main auditor dintoken buy 1 --network local
show python -m dincli.main auditor dintoken stake 1000000 --network local
show python -m dincli.main auditor dintoken read-stake --network local
show python -m dincli.main auditor register --network local --model-id 0

show python -m dincli.main system connect-wallet --account 54
show python -m dincli.main auditor dintoken buy 1 --network local
show python -m dincli.main auditor dintoken stake 1000000 --network local
show python -m dincli.main auditor dintoken read-stake --network local
show python -m dincli.main auditor register --network local --model-id 0

show python -m dincli.main system connect-wallet --account 55
show python -m dincli.main auditor dintoken buy 1 --network local
show python -m dincli.main auditor dintoken stake 1000000 --network local
show python -m dincli.main auditor dintoken read-stake --network local
show python -m dincli.main auditor register --network local --model-id 0

show python -m dincli.main system connect-wallet --account 56
show python -m dincli.main auditor dintoken buy 1 --network local
show python -m dincli.main auditor dintoken stake 1000000 --network local
show python -m dincli.main auditor dintoken read-stake --network local
show python -m dincli.main auditor register --network local --model-id 0

show python -m dincli.main system connect-wallet --account 57
show python -m dincli.main auditor dintoken buy 1 --network local
show python -m dincli.main auditor dintoken stake 1000000 --network local
show python -m dincli.main auditor dintoken read-stake --network local
show python -m dincli.main auditor register --network local --model-id 0

show python -m dincli.main system connect-wallet --account 58
show python -m dincli.main auditor dintoken buy 1 --network local
show python -m dincli.main auditor dintoken stake 1000000 --network local
show python -m dincli.main auditor dintoken read-stake --network local
show python -m dincli.main auditor register --network local --model-id 0



show python -m dincli.main system connect-wallet --account 1

show python -m dincli.main model-owner gi show-registered-auditors --network local --model-id 0

show python -m dincli.main model-owner gi reg auditors-close --network local --model-id 0

show python -m dincli.main model-owner lms open --network local --model-id 0





show python -m dincli.main system connect-wallet --account 2
# show python -m dincli.main client train-lms --network local --model-id 0
show python -m dincli.main client train-lms --network local --submit --model-id 0


show python -m dincli.main system connect-wallet --account 3
show python -m dincli.main client train-lms --network local --submit --model-id 0

show python -m dincli.main system connect-wallet --account 4
show python -m dincli.main client train-lms --network local --submit --model-id 0

show python -m dincli.main system connect-wallet --account 5
show python -m dincli.main client train-lms --network local --submit --model-id 0

show python -m dincli.main system connect-wallet --account 6
show python -m dincli.main client train-lms --network local --submit --model-id 0

show python -m dincli.main system connect-wallet --account 7
show python -m dincli.main client train-lms --network local --submit --model-id 0

show python -m dincli.main system connect-wallet --account 8
show python -m dincli.main client train-lms --network local --submit --model-id 0

show python -m dincli.main system connect-wallet --account 9
show python -m dincli.main client train-lms --network local --submit --model-id 0

show python -m dincli.main system connect-wallet --account 10
show python -m dincli.main client train-lms --network local --submit --model-id 0

show python -m dincli.main client lms show-models --network local --model-id 0

show python -m dincli.main system connect-wallet --account 1

show python -m dincli.main model-owner lms show-models --network local --model-id 0

show python -m dincli.main system connect-wallet --account 1
show python -m dincli.main model-owner lms close --network local --model-id 0

show python -m dincli.main system connect-wallet --account 1
show python -m dincli.main model-owner auditor-batches create --network local --model-id 0

show python -m dincli.main model-owner auditor-batches show --network local --model-id 0

# show python -m dincli.main model-owner auditor-batches create-testdataset --network local --model-id 0
show python -m dincli.main model-owner auditor-batches create-testdataset --network local --submit --model-id 0

show python -m dincli.main model-owner lms-evaluation start --network local --model-id 0

show python -m dincli.main model-owner lms-evaluation show --network local --model-id 0

show python -m dincli.main model-owner lms-evaluation show --network local --auditors --model-id 0

show python -m dincli.main system connect-wallet --account 50
show python -m dincli.main auditor lms-evaluation show-batch --network local --model-id 0

# show python -m dincli.main auditor lms-evaluation evaluate --network local --model-id 0

show python -m dincli.main auditor lms-evaluation evaluate --network local --submit --model-id 0

show python -m dincli.main system connect-wallet --account 51
show python -m dincli.main auditor lms-evaluation show-batch --network local --model-id 0
show python -m dincli.main auditor lms-evaluation evaluate --network local --submit --model-id 0

show python -m dincli.main system connect-wallet --account 52
show python -m dincli.main auditor lms-evaluation show-batch --network local --model-id 0
show python -m dincli.main auditor lms-evaluation evaluate --network local --submit --model-id 0

show python -m dincli.main system connect-wallet --account 53
show python -m dincli.main auditor lms-evaluation show-batch --network local --model-id 0
show python -m dincli.main auditor lms-evaluation evaluate --network local --submit --model-id 0

show python -m dincli.main system connect-wallet --account 54
show python -m dincli.main auditor lms-evaluation show-batch --network local --model-id 0
show python -m dincli.main auditor lms-evaluation evaluate --network local --submit --model-id 0

show python -m dincli.main system connect-wallet --account 55
show python -m dincli.main auditor lms-evaluation show-batch --network local --model-id 0
show python -m dincli.main auditor lms-evaluation evaluate --network local --submit --model-id 0

show python -m dincli.main system connect-wallet --account 56
show python -m dincli.main auditor lms-evaluation show-batch --network local --model-id 0
show python -m dincli.main auditor lms-evaluation evaluate --network local --submit --model-id 0

show python -m dincli.main system connect-wallet --account 57
show python -m dincli.main auditor lms-evaluation show-batch --network local --model-id 0
show python -m dincli.main auditor lms-evaluation evaluate --network local --submit --model-id 0

show python -m dincli.main system connect-wallet --account 58
show python -m dincli.main auditor lms-evaluation show-batch --network local --model-id 0
show python -m dincli.main auditor lms-evaluation evaluate --network local --submit --model-id 0

# show python -m dincli.main system show-index --address 0x145e2dc5C8238d1bE628F87076A37d4a26a78544

show python -m dincli.main system connect-wallet --account 1

show python -m dincli.main model-owner lms-evaluation show --network local --model-id 0 --models
show python -m dincli.main model-owner lms-evaluation close --network local --model-id 0

show python -m dincli.main model-owner aggregation create-t1nt2-batches --network local --model-id 0

show python -m dincli.main model-owner aggregation show-t1-batches --network local --model-id 0 --detailed
show python -m dincli.main model-owner aggregation show-t2-batches --network local --model-id 0 --detailed

show python -m dincli.main model-owner aggregation T1 start --network local --model-id 0



show python -m dincli.main system connect-wallet --account 11
show python -m dincli.main aggregator show-t1-batches --network local --model-id 0 --detailed 

show python -m dincli.main aggregator aggregate-t1 --network local --model-id 0 --submit 

show python -m dincli.main system connect-wallet --account 12
show python -m dincli.main aggregator show-t1-batches --network local --detailed --model-id 0
show python -m dincli.main aggregator aggregate-t1 --network local --submit --model-id 0

show python -m dincli.main system connect-wallet --account 13
show python -m dincli.main aggregator show-t1-batches --network local --detailed --model-id 0
show python -m dincli.main aggregator aggregate-t1 --network local --submit --model-id 0

show python -m dincli.main system connect-wallet --account 14
show python -m dincli.main aggregator show-t1-batches --network local --detailed --model-id 0
show python -m dincli.main aggregator aggregate-t1 --network local --submit --model-id 0

show python -m dincli.main system connect-wallet --account 15
show python -m dincli.main aggregator show-t1-batches --network local --detailed --model-id 0
show python -m dincli.main aggregator aggregate-t1 --network local --submit --model-id 0

show python -m dincli.main system connect-wallet --account 16
show python -m dincli.main aggregator show-t1-batches --network local --detailed --model-id 0
show python -m dincli.main aggregator aggregate-t1 --network local --submit --model-id 0

show python -m dincli.main system connect-wallet --account 17
show python -m dincli.main aggregator show-t1-batches --network local --detailed --model-id 0
show python -m dincli.main aggregator aggregate-t1 --network local --submit --model-id 0

show python -m dincli.main system connect-wallet --account 18
show python -m dincli.main aggregator show-t1-batches --network local --detailed --model-id 0
show python -m dincli.main aggregator aggregate-t1 --network local --submit --model-id 0

show python -m dincli.main system connect-wallet --account 19
show python -m dincli.main aggregator show-t1-batches --network local --detailed --model-id 0
show python -m dincli.main aggregator aggregate-t1 --network local --submit --model-id 0

show python -m dincli.main system connect-wallet --account 20
show python -m dincli.main aggregator show-t1-batches --network local --detailed --model-id 0
show python -m dincli.main aggregator aggregate-t1 --network local --submit --model-id 0

show python -m dincli.main system connect-wallet --account 21
show python -m dincli.main aggregator show-t1-batches --network local --detailed --model-id 0
show python -m dincli.main aggregator aggregate-t1 --network local --submit --model-id 0

show python -m dincli.main system connect-wallet --account 22
show python -m dincli.main aggregator show-t1-batches --network local --detailed --model-id 0
show python -m dincli.main aggregator aggregate-t1 --network local --submit --model-id 0

show python -m dincli.main system connect-wallet --account 1
show python -m dincli.main model-owner aggregation show-t1-batches --network local --detailed --model-id 0

show python -m dincli.main system connect-wallet --account 1
show python -m dincli.main model-owner aggregation T1 close --network local --model-id 0

show python -m dincli.main model-owner aggregation T2 start --network local --model-id 0
show python -m dincli.main model-owner gi show-state --network local --model-id 0

show python -m dincli.main model-owner aggregation show-t2-batches --network local --detailed --model-id 0

show python -m dincli.main system connect-wallet --account 11
show python -m dincli.main aggregator show-t2-batches --network local --detailed --model-id 0
show python -m dincli.main aggregator aggregate-t2 --network local --model-id 0 --submit 

show python -m dincli.main system connect-wallet --account 12
show python -m dincli.main aggregator show-t2-batches --network local --detailed --model-id 0
show python -m dincli.main aggregator aggregate-t2 --network local --model-id 0 --submit 

show python -m dincli.main system connect-wallet --account 13
show python -m dincli.main aggregator show-t2-batches --network local --detailed --model-id 0
show python -m dincli.main aggregator aggregate-t2 --network local --model-id 0 --submit 

show python -m dincli.main system connect-wallet --account 14
show python -m dincli.main aggregator show-t2-batches --network local --detailed --model-id 0
show python -m dincli.main aggregator aggregate-t2 --network local --model-id 0 --submit 

show python -m dincli.main system connect-wallet --account 15
show python -m dincli.main aggregator show-t2-batches --network local --detailed --model-id 0
show python -m dincli.main aggregator aggregate-t2 --network local --model-id 0 --submit 

show python -m dincli.main system connect-wallet --account 16
show python -m dincli.main aggregator show-t2-batches --network local --detailed --model-id 0
show python -m dincli.main aggregator aggregate-t2 --network local --model-id 0 --submit 

show python -m dincli.main system connect-wallet --account 17
show python -m dincli.main aggregator show-t2-batches --network local --detailed --model-id 0
show python -m dincli.main aggregator aggregate-t2 --network local --model-id 0 --submit 

show python -m dincli.main system connect-wallet --account 18
show python -m dincli.main aggregator show-t2-batches --network local --detailed --model-id 0
show python -m dincli.main aggregator aggregate-t2 --network local --model-id 0 --submit 

show python -m dincli.main system connect-wallet --account 19
show python -m dincli.main aggregator show-t2-batches --network local --detailed --model-id 0
show python -m dincli.main aggregator aggregate-t2 --network local --model-id 0 --submit 

show python -m dincli.main system connect-wallet --account 20
show python -m dincli.main aggregator show-t2-batches --network local --detailed --model-id 0
show python -m dincli.main aggregator aggregate-t2 --network local --model-id 0 --submit 

show python -m dincli.main system connect-wallet --account 21
show python -m dincli.main aggregator show-t2-batches --network local --detailed --model-id 0
show python -m dincli.main aggregator aggregate-t2 --network local --model-id 0 --submit 

show python -m dincli.main system connect-wallet --account 22
show python -m dincli.main aggregator show-t2-batches --network local --detailed --model-id 0
show python -m dincli.main aggregator aggregate-t2 --network local --model-id 0 --submit 

show python -m dincli.main system connect-wallet --account 1
show python -m dincli.main model-owner aggregation show-t2-batches --network local --detailed --model-id 0

show python -m dincli.main system connect-wallet --account 1
show python -m dincli.main model-owner aggregation T2 close --network local --model-id 0

show python -m dincli.main model-owner slash auditors --network local --model-id 0

show python -m dincli.main model-owner gi show-state --network local --model-id 0
show python -m dincli.main model-owner slash aggregators --network local --model-id 0
show python -m dincli.main model-owner gi end --network local --model-id 0

