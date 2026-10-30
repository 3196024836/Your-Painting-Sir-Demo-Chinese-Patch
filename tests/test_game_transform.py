import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'source'))
from game_transform import TranslationError, apply_translations, validate_translation, patch_asset_font, patch_fancy_text, patch_textbox_spacing, patch_speech_bubble, patch_asset_images

class GameTransformTest(unittest.TestCase):
    def test_replaces_only_the_exact_selected_literal(self):
        source = 'local internal = "Hello"\nlocal text = "Hello"\n'
        result = apply_translations(source, [{'line': 2, 'original':'Hello', 'translation':'你好'}])
        self.assertEqual(result, 'local internal = "Hello"\nlocal text = "你好"\n')

    def test_rejects_ambiguous_or_missing_location(self):
        with self.assertRaises(TranslationError):
            apply_translations('return "hello", "hello"', [{'line': 1, 'original':'hello', 'translation':'你好'}])
        with self.assertRaises(TranslationError):
            apply_translations('return "hello"', [{'line': 2, 'original':'hello', 'translation':'你好'}])

    def test_rejects_changed_control_tags_numbers_and_placeholders(self):
        original = '[sfx=bell]Call 526-257 for [hl]%s[/hl].'
        validate_translation(original, '[sfx=bell]拨打526-257找[hl]%s[/hl]。')
        for bad in ['[sfx=bell]拨打526-258找[hl]%s[/hl]。', '拨打526-257找[hl]%s[/hl]。', '[sfx=bell]拨打526-257找[hl]他[/hl]。']:
            with self.assertRaises(TranslationError):
                validate_translation(original, bad)

    def test_three_source_markup_errors_are_repaired_only_for_exact_originals(self):
        pairs = [
            ('By manipulating zee light photons they manage to hide themselves in any video footage, [hl]altering their form, or becoming invisible entirely![/h]', '他们操纵光子，在录像中隐藏自己，[hl]改变形态，甚至完全隐形！[/hl]'),
            ('Oh, but I do! I have managed to reverse engineer their photo manipulation mechanic, allowing me to restore their original image[/hl].', '我破解了机制，可以还原他们的模样。'),
            ('Now that I have a cutout, I can go back to the canvas by pressing [hl][[]A][/hl], [hl][[]J][/h], or the [hl][[]left arrow key][/hl].', '按[hl][[]A][/hl]、[hl][[]J][/hl]或[hl][[]左方向键][/hl]。'),
        ]
        for original, translated in pairs:
            validate_translation(original, translated)
        with self.assertRaises(TranslationError):
            validate_translation('another [hl]unrelated[/h]', '其他[hl]内容[/hl]')

    def test_card_image_patch_is_scoped_to_original_loader(self):
        source = 'image = love.graphics.newImage("assets/images/" .. path .. ".png")'
        patched = patch_asset_images(source)
        self.assertIn('require("zh_card_text").translate(path, image)', patched)
        with self.assertRaises(TranslationError):
            patch_asset_images('image = another_loader(path)')
        with self.assertRaises(TranslationError):
            patch_asset_images(source + "\n" + source)

    def test_font_patch_requires_expected_anchor(self):
        source='local font_formats = {\n    ".ttf",\n}\nfont = love.graphics.newFont("assets/fonts/" .. path .. v, size, hinting)\n'
        patched=patch_asset_font(source)
        self.assertIn('font:setFallbacks(zhFont)', patched)
        self.assertIn('fusion-pixel-zh.ttf', patched)
        with self.assertRaises(TranslationError): patch_asset_font('not the expected source')

    def test_font_patch_uses_smaller_cjk_fallback_and_non_overlapping_line_height(self):
        source='local font_formats = {\n}\nfont = love.graphics.newFont("assets/fonts/" .. path .. v, size, hinting)\n'
        patched=patch_asset_font(source)
        self.assertIn('size * 0.75', patched)
        self.assertIn('font:setLineHeight', patched)
        self.assertIn('zhFont:getHeight()', patched)

    def test_textbox_line_spacing_is_adjusted_only_at_exact_anchor(self):
        self.assertIn('adjust_line_height = 3,', patch_textbox_spacing('adjust_line_height = -3,'))
        with self.assertRaises(TranslationError): patch_textbox_spacing('adjust_line_height = -2,')

    def test_speech_bubble_moves_text_up_and_requires_exact_source(self):
        sample='local text = self:setText(0, 8)\nfunction SpeechBubble:update(dt)'
        patched=patch_speech_bubble(sample)
        self.assertIn('local text = self:setText(0, 4)',patched)
        self.assertIn('self.size.y = self.size.y + 3',patched)
        with self.assertRaises(TranslationError): patch_speech_bubble('local text = self:setText(0, 7)')

    def test_escaped_key_labels_must_preserve_literal_brackets(self):
        original='Press [hl][[]A or D][/hl].'
        validate_translation(original, '按[hl][[]A 或 D][/hl]。')
        with self.assertRaises(TranslationError): validate_translation(original, '按[hl]A 或 D[/hl]。')
        with self.assertRaises(TranslationError): validate_translation(original, '按[hl][[]A 或 X][/hl]。')

    def test_wrap_patch_requires_expected_anchor(self):
        source='        local fulljustspace = {}\n        for i = 1, #self.table_string do\n            ORIGINAL\n        end\n        if self.rendering ~= "left" then\n'
        patched=patch_fancy_text(source)
        self.assertIn('while i <= #self.table_string do', patched)
        self.assertIn('get_character_width(char)', patched)
        self.assertNotIn('ORIGINAL', patched)
        with self.assertRaises(TranslationError): patch_fancy_text('not the expected source')

if __name__ == '__main__': unittest.main()

