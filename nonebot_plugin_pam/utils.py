from typing import Any, Callable, Coroutine


class AwaitAttrDict:
    obj: Any

    def __getattr__(self, name):
        async def _(d):
            return d

        try:
            if hasattr(self.obj, name):
                ret = getattr(self.obj, name)
            else:
                ret = self[name]
            if isinstance(ret, Coroutine):
                return ret
            elif isinstance(ret, Callable):
                return ret
            return _(ret)
        except KeyError:
            return _(None)

    def __setattr__(self, name, value):
        if isinstance(self.obj, dict):
            self.obj[name] = value
        else:
            self.obj.__dict__[name] = value

    def __getitem__(self, key):
        if isinstance(self.obj, dict):
            return self.obj[key]
        else:
            return self.obj.__dict__[key]

    def __setitem__(self, key, value):
        if isinstance(self.obj, dict):
            self.obj[key] = value
        else:
            self.obj.__dict__[key] = value

    def __init__(self, obj: Any = None) -> None:
        super().__setattr__("obj", obj or {})


class AttrDict:
    obj: Any

    def __getattr__(self, name):
        try:
            if hasattr(self.obj, name):
                ret = getattr(self.obj, name)
            else:
                ret = self[name]
            if isinstance(ret, Callable):
                return ret
            return ret
        except KeyError:
            return None

    def __setattr__(self, name, value):
        if isinstance(self.obj, dict):
            self.obj[name] = value
        else:
            self.obj.__dict__[name] = value

    def __getitem__(self, key):
        if isinstance(self.obj, dict):
            return self.obj[key]
        else:
            return self.obj.__dict__[key]

    def __setitem__(self, key, value):
        if isinstance(self.obj, dict):
            self.obj[key] = value
        else:
            self.obj.__dict__[key] = value

    def __init__(self, obj: Any = None) -> None:
        super().__setattr__("obj", obj or {})
