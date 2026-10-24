"""Minimal JSON Schema 2020-12 validator (standard library only).

Covers the keywords used by share/php-quickpatch/schemas: type, enum, const,
properties, required, additionalProperties (bool), items, pattern, minimum,
maximum, allOf, oneOf, anyOf and local "$ref": "#/$defs/...". Unknown
keywords are ignored, like a lenient validator would.
"""
import re

_TYPES = {
    'object': lambda v: isinstance(v, dict),
    'array': lambda v: isinstance(v, list),
    'string': lambda v: isinstance(v, str),
    'integer': lambda v: isinstance(v, int) and not isinstance(v, bool),
    'number': lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    'boolean': lambda v: isinstance(v, bool),
    'null': lambda v: v is None,
}


def _resolve(root, ref):
    if not ref.startswith('#/'):
        raise ValueError('only local $ref is supported: %s' % ref)
    node = root
    for part in ref[2:].split('/'):
        node = node[part.replace('~1', '/').replace('~0', '~')]
    return node


def iter_errors(instance, schema, root=None, path='$'):
    """Yield 'path: message' strings for every violation."""
    root = schema if root is None else root
    if schema is True or schema == {}:
        return
    if schema is False:
        yield '%s: not allowed' % path
        return
    if '$ref' in schema:
        yield from iter_errors(instance, _resolve(root, schema['$ref']), root, path)
    if 'type' in schema:
        types = schema['type'] if isinstance(schema['type'], list) else [schema['type']]
        if not any(_TYPES[t](instance) for t in types):
            yield '%s: expected %s, got %s' % (path, '|'.join(types), type(instance).__name__)
            return
    if 'const' in schema and instance != schema['const']:
        yield '%s: expected const %r' % (path, schema['const'])
    if 'enum' in schema and instance not in schema['enum']:
        yield '%s: %r not in %r' % (path, instance, schema['enum'])
    if isinstance(instance, str) and 'pattern' in schema and not re.search(schema['pattern'], instance):
        yield '%s: %r does not match %s' % (path, instance, schema['pattern'])
    if _TYPES['number'](instance):
        if 'minimum' in schema and instance < schema['minimum']:
            yield '%s: %r < minimum %r' % (path, instance, schema['minimum'])
        if 'maximum' in schema and instance > schema['maximum']:
            yield '%s: %r > maximum %r' % (path, instance, schema['maximum'])
    if isinstance(instance, dict):
        props = schema.get('properties', {})
        for key in schema.get('required', []):
            if key not in instance:
                yield '%s: missing required %r' % (path, key)
        for key, value in instance.items():
            if key in props:
                yield from iter_errors(value, props[key], root, '%s.%s' % (path, key))
            elif schema.get('additionalProperties') is False:
                yield '%s: unexpected property %r' % (path, key)
    if isinstance(instance, list) and 'items' in schema:
        for i, value in enumerate(instance):
            yield from iter_errors(value, schema['items'], root, '%s[%d]' % (path, i))
    for sub in schema.get('allOf', []):
        yield from iter_errors(instance, sub, root, path)
    if 'anyOf' in schema and not any(not list(iter_errors(instance, s, root, path)) for s in schema['anyOf']):
        yield '%s: matches none of anyOf' % path
    if 'oneOf' in schema:
        n = sum(1 for s in schema['oneOf'] if not list(iter_errors(instance, s, root, path)))
        if n != 1:
            yield '%s: matches %d of oneOf (need exactly 1)' % (path, n)


def validate(instance, schema):
    """Return the list of violations (empty when valid)."""
    return list(iter_errors(instance, schema))
