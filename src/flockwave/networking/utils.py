__all__ = ("aclosing",)


class aclosing:
    """Backport of `contextlib.aclosing` from Python 3.10."""

    def __init__(self, thing):
        self.thing = thing

    async def __aenter__(self):
        return self.thing

    async def __aexit__(self, *exc_info):
        await self.thing.aclose()
