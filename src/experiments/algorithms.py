"""Routing plug-ins. Each call searches one bundle without reserving resources."""
from dataclasses import dataclass
from importlib import import_module
from typing import Callable


@dataclass(frozen=True)
class Algorithm:
    name: str
    search: Callable
    disable_dominance: bool = False


def resolve_algorithm(name):
    """Built-ins or a trusted local Python entry point, module:function."""
    from src.validation.proposed_v04 import search
    builtins = {
        'label_setting_v04': Algorithm('label_setting_v04', search),
        'label_setting_no_dominance': Algorithm(
            'label_setting_no_dominance', search, disable_dominance=True),
    }
    if name in builtins:
        return builtins[name]
    if ':' not in name:
        raise ValueError(f'Unknown algorithm: {name}; use a built-in or module:function')
    module, function = name.split(':', 1)
    try:
        implementation = getattr(import_module(module), function)
    except (ImportError, AttributeError, ValueError) as error:
        raise ValueError(f'Cannot load algorithm {name}: {error}') from error
    if not callable(implementation):
        raise ValueError(f'Algorithm entry point is not callable: {name}')
    return Algorithm(name, implementation)
