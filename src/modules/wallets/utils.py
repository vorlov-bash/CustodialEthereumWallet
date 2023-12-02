from eth_account import Account
from eth_account.signers.local import LocalAccount
from hdwallet import BIP44HDWallet
from hdwallet.cryptocurrencies import EthereumMainnet
from hdwallet.derivations import BIP44Derivation
from hdwallet.symbols import ETH


def get_main_account(xprivate_key: str) -> LocalAccount:
    bip44_hdwallet = BIP44HDWallet(symbol=ETH)
    bip44_hdwallet.from_xprivate_key(xprivate_key=xprivate_key)
    bip44_hdwallet.clean_derivation()
    deposit_private_key = bip44_hdwallet.private_key()
    return Account.from_key(deposit_private_key)


def get_account_by_index(xprivate_key: str, index: int) -> LocalAccount:
    bip44_hdwallet = BIP44HDWallet(symbol=ETH)
    bip44_hdwallet.from_xprivate_key(xprivate_key=xprivate_key)
    bip44_hdwallet.clean_derivation()
    bip44_derivation = BIP44Derivation(
        cryptocurrency=EthereumMainnet, account=0, change=False, address=index
    )

    bip44_hdwallet.from_path(path=bip44_derivation)
    deposit_private_key = bip44_hdwallet.private_key()
    return Account.from_key(deposit_private_key)


def get_address_by_index_xpk(index: int, xprivate_key: str) -> str:
    bip44_hdwallet = BIP44HDWallet(symbol=ETH)
    bip44_hdwallet.from_xprivate_key(xprivate_key=xprivate_key)
    bip44_hdwallet.clean_derivation()
    bip44_derivation = BIP44Derivation(
        cryptocurrency=EthereumMainnet, account=0, change=False, address=index
    )

    bip44_hdwallet.from_path(path=bip44_derivation)
    return bip44_hdwallet.p2pkh_address()
