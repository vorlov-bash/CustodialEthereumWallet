from web3 import AsyncWeb3


async def get_gas_from_history(w3: AsyncWeb3) -> tuple[int, int, int]:
    result = await w3.eth.fee_history(10, "latest", [10, 95])
    base_fee_per_gas_list = result["baseFeePerGas"]
    return (
        min(base_fee_per_gas_list),
        int(sum(base_fee_per_gas_list) / len(base_fee_per_gas_list)),
        max(base_fee_per_gas_list),
    )
