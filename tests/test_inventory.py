import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'source'))
from inventory import candidates

class InventoryTest(unittest.TestCase):
    def test_dialog_string_and_segmented_text_keep_speaker_and_control_segments(self):
        source='''return {
        {character = "butler", text = "Hello, sir!"},
        {character = "crab", text = { 0, "Welcome, ", 1, "Snippy", 0, "!" }},
        {emotion = "happy", sfx = "some/file"},
        }'''
        found=candidates('data/dialog/example.lua',source)
        self.assertEqual([x['original'] for x in found], ['Hello, sir!', 'Welcome, ', 'Snippy', '!'])
        self.assertEqual([x['speaker'] for x in found], ['butler','crab','crab','crab'])
        self.assertTrue(all(x['status']=='待翻译' for x in found))

    def test_menu_selects_titles_and_descriptions_but_not_internal_names(self):
        source='return { name = "back", title = "Back", description = "Go back" }'
        found=candidates('data/menu_data.lua',source)
        self.assertEqual([x['original'] for x in found],['Back','Go back'])

    def test_note_includes_short_colored_text_but_not_dialog_identifier(self):
        source='Note(20, 30, Color.blue, {0,"Step 1: ",1,"Click",0," a picture"}, {dialog="picture"})'
        found=candidates('src/workshop/example.lua',source)
        self.assertEqual([x['original'] for x in found], ['Step 1: ', 'Click', ' a picture'])

    def test_text_constructor_finds_short_conditional_fragments_but_not_font_name(self):
        source='Text(0, 0, "Chapter " .. chapter .. (chapter == 2 and "(Teaser)" or ""), "font")'
        found=candidates('src/screens/chapter.lua',source)
        self.assertEqual([x['original'] for x in found], ['Chapter ', '(Teaser)'])

    def test_crab_random_lines_are_player_facing_array_entries(self):
        source = 'return { "Where to, boss?", "Need some help?" }'
        found = candidates('data/phone/crab_lines.lua', source)
        self.assertEqual([x['original'] for x in found], ['Where to, boss?', 'Need some help?'])

    def test_ignores_comments(self):
        source='-- text = "ignored"\nreturn { text = "Hello" }'
        self.assertEqual([x['original'] for x in candidates('data/dialog/a.lua',source)],['Hello'])

if __name__=='__main__': unittest.main()


