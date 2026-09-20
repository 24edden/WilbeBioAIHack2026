"""Provider failures that can safely be presented in a run's event log."""


class ProviderError(RuntimeError):
    """A live call failed or returned something we refuse to interpret."""
