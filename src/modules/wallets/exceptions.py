from src.core.exceptions import JsonException


class WalletException(JsonException):
    pass


class WalletNotFound(WalletException):
    status_code = 404
    error_name = "WALLET_NOT_FOUND"

    def __init__(self, external_id: str | None = None):
        self.error_description = f"Wallet with {external_id=} not found"
        super().__init__(error_description=self.error_description)


class WalletIsNotActive(WalletException):
    status_code = 400
    error_name = "WALLET_IS_NOT_ACTIVE"

    def __init__(self, external_id: str | None = None):
        self.error_description = f"Wallet with {external_id=} is not active"
        super().__init__(error_description=self.error_description)


class WalletWithIndexAlreadyExists(WalletException):
    status_code = 400
    error_name = "WALLET_ALREADY_EXISTS"

    def __init__(self, index: int | None = None):
        self.error_description = f"Wallet with {index=} is already exists"
        super().__init__(error_description=self.error_description)
