"""自動探索 signals/*.py。每檔須有模組級 SIGNAL 物件，且 id == 檔名。

底線開頭（_template 等）跳過。重複 id 直接報錯。清單無需手動維護——
「放一個檔進 signals/」就是註冊，這是整個平台低摩擦擴充的關鍵。
"""
from __future__ import annotations

import importlib
import pkgutil

import signals as signals_pkg
from core.spec import SignalSpec


def discover() -> list[SignalSpec]:
    """回傳所有已註冊的 SignalSpec（依探索到的順序）。"""
    found: dict[str, SignalSpec] = {}
    for mod in pkgutil.iter_modules(signals_pkg.__path__):
        if mod.name.startswith("_"):
            continue
        module = importlib.import_module(f"signals.{mod.name}")
        spec = getattr(module, "SIGNAL", None)
        if spec is None:
            raise RuntimeError(f"signals/{mod.name}.py 缺少模組級 SIGNAL 物件")
        if not isinstance(spec, SignalSpec):
            raise RuntimeError(f"signals/{mod.name}.py 的 SIGNAL 不是 SignalSpec")
        if spec.id != mod.name:
            raise RuntimeError(f"id '{spec.id}' 必須等於檔名 '{mod.name}'")
        if spec.id in found:
            raise RuntimeError(f"重複的 signal id: {spec.id}")
        found[spec.id] = spec
    return list(found.values())
