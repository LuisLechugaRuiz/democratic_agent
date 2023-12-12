import abc


class Model(abc.ABC):
    """Simple interface for models."""

    @abc.abstractmethod
    def get_response(self, *args, **kwargs) -> str:
        """Get a response from the model with variable arguments."""
        pass
