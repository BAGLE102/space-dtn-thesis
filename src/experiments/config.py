"""Load JSON scenarios and optional CSV contacts, using exact rational values."""
import csv
import json
from copy import deepcopy
from fractions import Fraction
from pathlib import Path

from src.validation.model import normalize, number, occupancy, validate_input


class ConfigError(ValueError):
    """An input error, with the field name included in the message."""


def _fields(value, allowed, required, location):
    if not isinstance(value, dict):
        raise ConfigError(f'{location}: 必須是物件')
    missing, extra = required - value.keys(), value.keys() - allowed
    if missing:
        raise ConfigError(f'{location}: 缺少欄位 {sorted(missing)}')
    if extra:
        raise ConfigError(f'{location}: 未知欄位 {sorted(extra)}')


def _id(value, location):
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ConfigError(f'{location}: 必須是非空字串，且前後不能有空白')
    return value


def _numeric(value, location, minimum=0, positive=False):
    if isinstance(value, bool) or not isinstance(value, (int, float, str, Fraction)):
        raise ConfigError(f'{location}: 必須是數值或有理數字串')
    try:
        result = number(value)
    except (ValueError, ZeroDivisionError, OverflowError) as error:
        raise ConfigError(f'{location}: 無效數值 {value!r}') from error
    if result < minimum or (positive and result == 0):
        relation = '> 0' if positive else f'>= {minimum}'
        raise ConfigError(f'{location}: 必須 {relation}')
    return result


def _records(values, location):
    if not isinstance(values, list):
        raise ConfigError(f'{location}: 必須是陣列')
    return values


def _unique(records, location):
    seen = set()
    for index, item in enumerate(records):
        if not isinstance(item, dict):
            raise ConfigError(f'{location}[{index}]: 必須是物件')
        identifier = _id(item.get('id'), f'{location}[{index}].id')
        if identifier in seen:
            raise ConfigError(f'{location}: 重複 ID {identifier!r}')
        seen.add(identifier)


def _csv_contacts(path):
    try:
        with path.open(encoding='utf-8-sig', newline='') as stream:
            reader = csv.DictReader(stream)
            required = {'id', 'source', 'target', 'start', 'end', 'rate'}
            allowed = required | {'delay', 'remaining_capacity'}
            headers = reader.fieldnames or []
            if (len(headers) != len(set(headers)) or required - set(headers)
                    or set(headers) - allowed):
                raise ConfigError(f'contacts_file: CSV 欄位必須包含 {sorted(required)}，'
                                  '僅可另加 delay、remaining_capacity')
            rows = []
            for line, row in enumerate(reader, 2):
                if None in row or any(value is None for value in row.values()):
                    raise ConfigError(f'contacts_file: 第 {line} 列的欄位數不正確')
                # Blank OPTIONAL cells use explicit documented defaults.
                rows.append({key: value.strip() for key, value in row.items()
                             if value.strip() or key in required})
            return rows
    except (OSError, UnicodeError, csv.Error) as error:
        raise ConfigError(f'contacts_file: 無法讀取 {path}: {error}') from error


def _version_one(raw, base_dir):
    required = {'schema_version', 'name', 'time_step', 'horizon', 'nodes', 'bundles'}
    allowed = required | {'description', 'units', 'contacts', 'contacts_file'}
    _fields(raw, allowed, required, 'scenario')
    if type(raw['schema_version']) is not int or raw['schema_version'] != 1:
        raise ConfigError('schema_version: 目前只支援整數 1')
    if 'units' in raw and raw['units'] != {'time': 's', 'data': 'MB', 'rate': 'MB/s'}:
        raise ConfigError('units: 本版使用 s、MB、MB/s，不會自動換算單位')
    if ('contacts' in raw) == ('contacts_file' in raw):
        raise ConfigError('scenario: contacts 與 contacts_file 必須擇一提供')
    nodes = _records(raw['nodes'], 'nodes')
    _unique(nodes, 'nodes')
    buffers = {}
    for index, node in enumerate(nodes):
        _fields(node, {'id', 'buffer'}, {'id', 'buffer'}, f'nodes[{index}]')
        buffers[node['id']] = _numeric(node['buffer'], f'nodes[{index}].buffer')
    if 'contacts_file' in raw:
        filename = _id(raw['contacts_file'], 'contacts_file')
        contacts = _csv_contacts(base_dir / filename)
    else:
        contacts = _records(raw['contacts'], 'contacts')
    _unique(contacts, 'contacts')
    converted_contacts = []
    for index, edge in enumerate(contacts):
        loc = f'contacts[{index}]'
        required_edge = {'id', 'source', 'target', 'start', 'end', 'rate'}
        _fields(edge, required_edge | {'delay', 'remaining_capacity'}, required_edge, loc)
        start = _numeric(edge['start'], f'{loc}.start')
        end = _numeric(edge['end'], f'{loc}.end')
        rate = _numeric(edge['rate'], f'{loc}.rate', positive=True)
        if end <= start:
            raise ConfigError(f'{loc}: end 必須大於 start')
        volume = rate * (end - start)
        converted_contacts.append(dict(
            id=edge['id'], u=_id(edge['source'], f'{loc}.source'),
            v=_id(edge['target'], f'{loc}.target'), start=start, end=end,
            rate=rate, delay=_numeric(edge.get('delay', 0), f'{loc}.delay'),
            quota=_numeric(edge.get('remaining_capacity', str(volume)),
                           f'{loc}.remaining_capacity')))
    bundles = _records(raw['bundles'], 'bundles')
    _unique(bundles, 'bundles')
    converted_bundles = []
    for index, bundle in enumerate(bundles):
        loc = f'bundles[{index}]'
        _fields(bundle, {'id', 'source', 'destination', 'release', 'size'},
                {'id', 'source', 'destination', 'release', 'size'}, loc)
        converted_bundles.append(dict(
            id=bundle['id'], source=_id(bundle['source'], f'{loc}.source'),
            dest=_id(bundle['destination'], f'{loc}.destination'),
            g=_numeric(bundle['release'], f'{loc}.release'),
            size=_numeric(bundle['size'], f'{loc}.size', positive=True)))
    return dict(name=_id(raw['name'], 'name'), contacts=converted_contacts,
                bundles=converted_bundles, buffers=buffers, background={},
                delta=_numeric(raw['time_step'], 'time_step', positive=True),
                horizon=_numeric(raw['horizon'], 'horizon'))


def validate_case(case):
    """Check the configuration boundary without changing routing semantics."""
    _id(case.get('name'), 'name')
    _numeric(case['delta'], 'delta', positive=True)
    _numeric(case['horizon'], 'horizon')
    if not case['buffers']:
        raise ConfigError('nodes/buffers: 至少需要一個節點')
    for node, capacity in case['buffers'].items():
        _id(node, 'node.id')
        _numeric(str(capacity), f'node[{node}].buffer')
    _unique(case['contacts'], 'contacts')
    _unique(case['bundles'], 'bundles')
    if not case['bundles']:
        raise ConfigError('bundles: 至少需要一個 bundle')
    for index, edge in enumerate(case['contacts']):
        loc = f'contacts[{index}]'
        for key in ('u', 'v'):
            if edge[key] not in case['buffers']:
                raise ConfigError(f'{loc}.{key}: 未定義的節點 {edge[key]!r}')
        for key in ('start', 'end', 'rate', 'delay', 'quota'):
            _numeric(str(edge[key]), f'{loc}.{key}', positive=key == 'rate')
    for index, bundle in enumerate(case['bundles']):
        _numeric(str(bundle['g']), f'bundles[{index}].release')
        _numeric(str(bundle['size']), f'bundles[{index}].size', positive=True)
        try:
            validate_input(case, bundle)
        except ValueError as error:
            raise ConfigError(f'bundles[{index}] ({bundle["id"]}): {error}') from error
    # Legacy files may carry an existing reservation state; validate all curves.
    for node, curves in case['background'].items():
        if node not in case['buffers']:
            raise ConfigError(f'background: 未定義的節點 {node!r}')
        for curve in curves:
            if not curve:
                raise ConfigError(f'background[{node}]: 占用曲線不可為空')
            previous_end = None
            for segment in curve:
                if len(segment) != 4:
                    raise ConfigError(f'background[{node}]: 每段需有4個數值')
                lo, hi, y0, y1 = segment
                if min(lo, hi, y0, y1) < 0 or lo > hi:
                    raise ConfigError(f'background[{node}]: 占用曲線數值或區間不合法')
                if lo == hi and y0 != y1:
                    raise ConfigError(f'background[{node}]: 瞬間事件的兩端占用值必須相同')
                if previous_end is not None and lo < previous_end:
                    raise ConfigError(f'background[{node}]: 同一曲線內的區間不能重疊')
                previous_end = hi
        points = {x for curve in curves for seg in curve for x in seg[:2]}
        if any(occupancy(case['background'], node, t) > case['buffers'][node]
               for t in points):
            raise ConfigError(f'background[{node}]: 初始占用超過 buffer 上限')
    return case


def load_scenario(path):
    """Accept schema v1 or existing contacts/buffers/bundles audit JSON files."""
    path = Path(path)
    try:
        # Keep decimal literals as exact strings, avoiding float rounding at import.
        raw = json.loads(path.read_text(encoding='utf-8-sig'), parse_float=str)
        if not isinstance(raw, dict):
            raise ConfigError('scenario: 頂層必須是物件')
        if 'schema_version' in raw:
            case = _version_one(raw, path.parent)
        else:
            required = {'name', 'contacts', 'bundles', 'buffers', 'horizon', 'delta'}
            _fields(raw, required | {'background', 'expected'}, required, 'legacy scenario')
            case = deepcopy(raw)
            # Reject boolean numeric values before Fraction normalization.
            for edge in _records(case['contacts'], 'contacts'):
                _fields(edge, {'id', 'u', 'v', 'start', 'end', 'rate', 'delay', 'quota'},
                        {'id', 'u', 'v', 'start', 'end', 'rate', 'delay', 'quota'}, 'contact')
                for key in ('start', 'end', 'rate', 'delay', 'quota'):
                    _numeric(edge[key], f'contact.{key}', positive=key == 'rate')
            for bundle in _records(case['bundles'], 'bundles'):
                _fields(bundle, {'id', 'source', 'dest', 'g', 'size'},
                        {'id', 'source', 'dest', 'g', 'size'}, 'bundle')
                _numeric(bundle['g'], 'bundle.g')
                _numeric(bundle['size'], 'bundle.size', positive=True)
            if not isinstance(case['buffers'], dict):
                raise ConfigError('buffers: 必須是節點ID對容量的物件')
            for node, capacity in case['buffers'].items():
                _numeric(capacity, f'buffers[{node}]')
            _numeric(case['delta'], 'delta', positive=True)
            _numeric(case['horizon'], 'horizon')
        return validate_case(normalize(case))
    except ConfigError:
        raise
    except (OSError, UnicodeError, ValueError, KeyError, TypeError, AttributeError,
            ZeroDivisionError, IndexError) as error:
        raise ConfigError(f'{path}: 無效設定或無法讀取：{error}') from error
