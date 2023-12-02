from src.core.exceptions import JsonException


class TransactionException(JsonException):
    pass


class NonceIsTooLow(TransactionException):
    status_code = 400
    error_name = "NONCE_IS_TOO_LOW"

    def __init__(self, external_id: str | None = None):
        self.error_description = f"Nonce is too low for {external_id=}"
        super().__init__(error_description=self.error_description)


class ReplacementTransactionUnderpriced(TransactionException):
    status_code = 400
    error_name = "REPLACEMENT_TRANSACTION_UNDERPRICED"

    def __init__(self, external_id: str | None = None):
        self.error_description = f"Replacement transaction underpriced for {external_id=}"
        super().__init__(error_description=self.error_description)
