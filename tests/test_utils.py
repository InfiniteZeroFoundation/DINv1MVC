from dincli.cli.utils import load_usdt_config
from dincli.cli.contract_utils import erc20_abi, router_abi
from decimal import Decimal
def get_usdt_balance(ctx, target_address=None):
    effective_network, w3, account, console = ctx.obj.get_en_w3_account_console()
    usdt_cfg = load_usdt_config()
    if target_address is None:
        target_address = account.address
    if effective_network not in usdt_cfg:
        print(f"[red]USDT config missing for network '{effective_network}'![/red]")
        raise typer.Exit()
    usdt_address = w3.to_checksum_address(usdt_cfg[effective_network]["usdt"])    
    usdt_contract = w3.eth.contract(address=usdt_address, abi=erc20_abi)
    usdt_balance_raw = usdt_contract.functions.balanceOf(target_address).call()
    usdt_balance_fmt = Decimal(usdt_balance_raw) / Decimal(10**6)

    return usdt_balance_fmt