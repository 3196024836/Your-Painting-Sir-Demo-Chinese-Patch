"""Read Lua string literals without treating comments or identifiers as translations."""
from dataclasses import dataclass
import re


@dataclass(frozen=True)
class Literal:
    start: int
    end: int
    line: int
    value: str


_LONG_OPEN = re.compile(r"\[(=*)\[")
_ESCAPES = {"a": "\a", "b": "\b", "f": "\f", "n": "\n", "r": "\r", "t": "\t", "v": "\v", "\\": "\\", '"': '"', "'": "'"}


def _long_end(source, start):
    match = _LONG_OPEN.match(source, start)
    if not match:
        return None
    closing = "]" + match.group(1) + "]"
    stop = source.find(closing, match.end())
    if stop < 0:
        raise ValueError("Unterminated Lua long string/comment")
    return match.end(), stop, stop + len(closing)


def _short_string(source, start):
    quote = source[start]
    i = start + 1
    result = []
    while i < len(source):
        ch = source[i]
        if ch == quote:
            return i + 1, "".join(result)
        if ch != "\\":
            result.append(ch)
            i += 1
            continue
        i += 1
        if i >= len(source):
            break
        ch = source[i]
        if ch in _ESCAPES:
            result.append(_ESCAPES[ch])
            i += 1
        elif ch == "\n":
            result.append("\n")
            i += 1
        elif ch == "\r":
            result.append("\n")
            i += 2 if i + 1 < len(source) and source[i + 1] == "\n" else 1
        elif ch == "z":
            i += 1
            while i < len(source) and source[i].isspace():
                i += 1
        elif ch.isdigit() and ch.isascii():
            end = i
            while end < min(i + 3, len(source)) and source[end].isdigit() and source[end].isascii():
                end += 1
            result.append(chr(int(source[i:end], 10)))
            i = end
        elif ch == "x" and re.fullmatch(r"[0-9a-fA-F]{2}", source[i + 1:i + 3]):
            result.append(chr(int(source[i + 1:i + 3], 16)))
            i += 3
        elif ch == "u" and i + 1 < len(source) and source[i + 1] == "{":
            end = source.index("}", i + 2)
            result.append(chr(int(source[i + 2:end], 16)))
            i = end + 1
        else:
            raise ValueError(f"Unsupported Lua escape \\{ch} at offset {i}")
    raise ValueError(f"Unterminated Lua string at offset {start}")


def extract_literals(source):
    literals = []
    i = 0
    while i < len(source):
        if source.startswith("--", i):
            block = _long_end(source, i + 2)
            if block:
                i = block[2]
            else:
                end = source.find("\n", i + 2)
                i = len(source) if end < 0 else end + 1
            continue
        start = i
        if source[i] in "\"'":
            end, value = _short_string(source, i)
        elif source[i] == "[":
            block = _long_end(source, i)
            if not block:
                i += 1
                continue
            body_start, body_end, end = block
            value = source[body_start:body_end]
            if value.startswith("\r\n"):
                value = value[2:]
            elif value.startswith(("\n", "\r")):
                value = value[1:]
        else:
            i += 1
            continue
        literals.append(Literal(start, end, source.count("\n", 0, start) + 1, value))
        i = end
    return literals


def encode_literal(value):
    escaped = []
    for ch in value:
        replacements = {"\\": "\\\\", '"': '\\"', "\n": "\\n", "\r": "\\r", "\t": "\\t", "\a": "\\a", "\b": "\\b", "\f": "\\f", "\v": "\\v"}
        if ch in replacements:
            escaped.append(replacements[ch])
        elif ord(ch) < 32 or ord(ch) == 127:
            escaped.append("\\%03d" % ord(ch))
        else:
            escaped.append(ch)
    return '"' + "".join(escaped) + '"'