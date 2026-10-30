import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "source"))
from lua_strings import extract_literals, encode_literal


class LuaStringsTest(unittest.TestCase):
    def test_extracts_strings_but_not_comments_and_preserves_positions(self):
        source = '-- "not text"\nreturn { text = "Hello\\nworld", value = [=[long \'quote\']=] } -- [["ignored"]]'
        literals = extract_literals(source)
        self.assertEqual([t.value for t in literals], ["Hello\nworld", "long 'quote'"])
        self.assertEqual([t.line for t in literals], [2, 2])
        self.assertEqual(source[literals[0].start:literals[0].end], '"Hello\\nworld"')

    def test_encoding_round_trips_control_characters_and_quotes(self):
        text = '中文 "示例"\\路径\n下一行'
        self.assertEqual(extract_literals(encode_literal(text))[0].value, text)

    def test_comment_blocks_and_long_bracket_literals(self):
        source = '--[=[ignored "comment"]=]\nlocal x = [[Hello\nworld]]'
        result = extract_literals(source)
        self.assertEqual([x.value for x in result], ['Hello\nworld'])