class PrescriberAllowList:
    """Simulated list of authorised prescriber codes (fictional data only)."""

    def __init__(self, codes):
        self._codes = frozenset(c.strip().upper() for c in codes)

    def is_authorised(self, code) -> bool:
        return isinstance(code, str) and code.strip().upper() in self._codes
