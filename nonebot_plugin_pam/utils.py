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
        self[name] = value

    def __getitem__(self, key):
        if isinstance(self.obj, dict):
            return self.obj[key]
        else:
            return self.obj.__dict__[key]

    def __setitem__(self, key, value):
        if isinstance(self.obj, dict):
            self.obj[key] = value
        else:
            try:
                self.obj.__dict__[key] = value
            except Exception:
                super().__setattr__(key, value)

    def __init__(self, obj: Any = None) -> None:
        super().__setattr__("obj", obj or {})


class AttrDict:
    obj: Any

    def __getattr__(self, name):
        try:
            if hasattr(self, name):
                ret = super().__getattribute__(name)
            elif hasattr(self.obj, name):
                ret = getattr(self.obj, name)
            else:
                if isinstance(self.obj, dict):
                    return self.obj[name]
                else:
                    return self.obj.__dict__[name]
            return ret
        except KeyError:
            return None

    def __setattr__(self, name, value):
        self[name] = value

    def __getitem__(self, key):
        try:
            if hasattr(self, key):
                ret = super().__getattribute__(key)
            elif hasattr(self.obj, key):
                ret = getattr(self.obj, key)
            else:
                if isinstance(self.obj, dict):
                    return self.obj[key]
                else:
                    return self.obj.__dict__[key]
            return ret
        except KeyError:
            return None

    def __setitem__(self, key, value):
        if isinstance(self.obj, dict):
            self.obj[key] = value
        else:
            try:
                self.obj.__dict__[key] = value
            except Exception:
                super().__setattr__(key, value)

    def __init__(self, obj: Any = None) -> None:
        super().__setattr__("obj", obj or {})
