"""Build narrowly targeted source changes and guard text-formatting semantics."""
import re
from lua_strings import extract_literals, encode_literal


class TranslationError(Exception):
    pass


_TAG = re.compile(r'\[(?:/?[A-Za-z_][A-Za-z0-9_/-]*(?:=[^\]\s]+)?|\.\d+(?:\.\d+)?)\]')
_FORMAT = re.compile(r'%(?:\d+\$)?[-+ #0]*\d*(?:\.\d+)?[diouxXeEfFgGcsq]|\{[A-Za-z_][A-Za-z0-9_]*\}')
_NUMBERS = re.compile(r'\d+(?:[-.,]\d+)*')
_ESCAPED_LABEL = re.compile(r'\[\[\]([^\]]*)\]')
_KEY_IN_LABEL = re.compile(r'(?i)\b(?:[a-z]|shift|ctrl|alt|space|enter|escape|tab)\b')


# These three exact English lines contain broken highlight-closing tags in the
# target demo. Normalize only those known originals when checking the translation.
_KNOWN_MARKUP_REPAIRS = {
    'By manipulating zee light photons they manage to hide themselves in any video footage, [hl]altering their form, or becoming invisible entirely![/h]': ('[/h]', '[/hl]'),
    'Oh, but I do! I have managed to reverse engineer their photo manipulation mechanic, allowing me to restore their original image[/hl].': ('[/hl]', ''),
    'Now that I have a cutout, I can go back to the canvas by pressing [hl][[]A][/hl], [hl][[]J][/h], or the [hl][[]left arrow key][/hl].': ('[/h]', '[/hl]'),
}


def validate_translation(original, translation):
    if not isinstance(translation, str) or not translation:
        raise TranslationError('译文为空')
    expected = original
    if original in _KNOWN_MARKUP_REPAIRS:
        before, after = _KNOWN_MARKUP_REPAIRS[original]
        expected = original.replace(before, after, 1)
    for rule, pattern in [('标记', _TAG), ('格式变量', _FORMAT), ('数字', _NUMBERS)]:
        if pattern.findall(expected) != pattern.findall(translation):
            raise TranslationError(f'{rule}与原文不一致：{original!r}')
    old_labels, new_labels = _ESCAPED_LABEL.findall(original), _ESCAPED_LABEL.findall(translation)
    if len(old_labels) != len(new_labels) or original.count('[[]') != translation.count('[[]'):
        raise TranslationError(f'转义按键标签不一致：{original!r}')
    for old, new in zip(old_labels, new_labels):
        if [k.lower() for k in _KEY_IN_LABEL.findall(old)] != [k.lower() for k in _KEY_IN_LABEL.findall(new)]:
            raise TranslationError(f'按键与原文不一致：{original!r}')


def apply_translations(source, entries):
    literals = extract_literals(source)
    changes = []
    seen = set()
    for item in entries:
        line, original, translated = item['line'], item['original'], item['translation']
        validate_translation(original, translated)
        matches = [v for v in literals if v.line == line and v.value == original]
        if 'column' in item:
            matches = [v for v in matches if v.start - (source.rfind('\n', 0, v.start) + 1) + 1 == item['column']]
        if len(matches) != 1 or matches[0].start in seen:
            raise TranslationError(f'原文字面量定位不唯一或已变化（第 {line} 行）：{original!r}')
        literal = matches[0]
        seen.add(literal.start)
        changes.append((literal.start, literal.end, encode_literal(translated)))
    for start, end, text in sorted(changes, reverse=True):
        source = source[:start] + text + source[end:]
    return source


def _replace_once(source, old, new):
    if source.count(old) != 1:
        raise TranslationError('游戏脚本结构与补丁预期不符')
    return source.replace(old, new, 1)


def patch_asset_font(source):
    source = _replace_once(source, 'local font_formats = {', 'local zhFallbackFonts = {}\n\nlocal font_formats = {')
    old = 'font = love.graphics.newFont("assets/fonts/" .. path .. v, size, hinting)'
    new = '''font = love.graphics.newFont("assets/fonts/" .. path .. v, size, hinting)
                local zhFont = zhFallbackFonts[size]
                if not zhFont then
                    zhFont = love.graphics.newFont("assets/fonts/fusion-pixel-zh.ttf", math.max(1, math.floor(size * 0.75 + 0.5)), hinting)
                    zhFont:setFilter(CONFIG.defaultGraphicsFilter, CONFIG.defaultGraphicsFilter)
                    zhFallbackFonts[size] = zhFont
                end
                font:setFallbacks(zhFont)
                font:setLineHeight(math.max(font:getLineHeight(), zhFont:getHeight() / font:getHeight() + 0.08))'''
    return _replace_once(source, old, new)


def patch_textbox_spacing(source):
    return _replace_once(source, 'adjust_line_height = -3,', 'adjust_line_height = 3,')


def patch_speech_bubble(source):
    # The Chinese fallback is taller than the original pixel font. Move the
    # bottom-anchored bubble text inward so its last line stays above the frame.
    source = _replace_once(source, 'local text = self:setText(0, 8)', 'local text = self:setText(0, 4)')
    return _replace_once(source, 'function SpeechBubble:update(dt)', '''function SpeechBubble:handleSize()
    SpeechBubble.super.handleSize(self)
    self.size.y = self.size.y + 3
end

function SpeechBubble:update(dt)''')


WRAP_LOOP = '''        local noLineStart = { ["，"]=true, ["。"]=true, ["！"]=true, ["？"]=true, ["、"]=true,
            ["；"]=true, ["："]=true, ["）"]=true, ["】"]=true, ["》"]=true, ["」"]=true,
            ["』"]=true, ["…"]=true, [","]=true, ["."]=true, ["!"]=true, ["?"]=true,
            [";"]=true, [":"]=true, [")"]=true, ["}"]=true }
        local i = 1
        while i <= #self.table_string do
            local token = self.table_string[i]
            local unicodeChar = token:sub(1, 2) == special_character[1] .. special_character[5]
            if #token == 1 or unicodeChar then
                local char = unicodeChar and token:sub(3, #token - 1) or token
                local width = get_character_width(char)
                if not unicodeChar and self.modify_character_width_table[char] then
                    width = width + self.modify_character_width_table[char]
                end
                -- Reserve space for following closing punctuation. A CJK
                -- character and its punctuation must wrap as a unit, rather
                -- than leaving a comma or question mark at the next line start.
                if char ~= " " and not noLineStart[char] and pixel_count > 0 then
                    local lookahead, following_width = i + 1, 0
                    while lookahead <= #self.table_string do
                        local next_token = self.table_string[lookahead]
                        local next_unicode = next_token:sub(1, 2) == special_character[1] .. special_character[5]
                        if #next_token == 1 or next_unicode then
                            local next_char = next_unicode and next_token:sub(3, #next_token - 1) or next_token
                            if noLineStart[next_char] then
                                following_width = following_width + get_character_width(next_char)
                            else
                                break
                            end
                        elseif next_token:match("newline") or next_token:match("end") or next_token:match("icon") then
                            break
                        end
                        lookahead = lookahead + 1
                    end
                    if following_width > 0 and math.floor(pixel_count + width + following_width) > wrap_num
                        and width + following_width <= wrap_num then
                        table.insert(self.table_string, i, special_character[1] .. "newline" .. special_character[2])
                        line_start[#line_start + 1] = i + 1
                        pixel_count, pixel_count_last_space, last_space = 0, 0, 0
                        i = i + 1
                    end
                end
                if char == " " then
                    last_space = i
                    pixel_count_last_space = 0
                else
                    pixel_count_last_space = pixel_count_last_space + width
                end
                pixel_count = pixel_count + width
                if math.floor(pixel_count) > wrap_num then
                    if last_space ~= 0 then
                        self.table_string[last_space] = special_character[1] .. "newline" .. special_character[2]
                        line_start[#line_start + 1] = last_space + 1
                        pixel_count = pixel_count_last_space
                    else
                        table.insert(self.table_string, i, special_character[1] .. "newline" .. special_character[2])
                        line_start[#line_start + 1] = i + 1
                        pixel_count = width
                        i = i + 1
                    end
                    last_space = 0
                    pixel_count_last_space = 0
                end
            else
                if token:match("newline") then
                    line_start[#line_start + 1] = i + 1
                    last_space = 0
                    pixel_count = 0
                    pixel_count_last_space = 0
                end
                if token:match("icon") then
                    pixel_count = pixel_count + self.icon_width
                    pixel_count_last_space = pixel_count_last_space + self.icon_width
                end
                if token:match("font") then
                    if font_table ~= nil and token ~= special_character[1] .. "/font" .. special_character[2] then
                        local font_table = string_to_table(font_table)
                        if font_table[token:sub(7, #token - 1)] then
                            love.graphics.setFont(font_table[token:sub(7, #token - 1)])
                        end
                    else
                        love.graphics.setFont(self.default_font)
                    end
                end
            end
            i = i + 1
        end
'''


def patch_asset_images(source):
    anchor = 'image = love.graphics.newImage("assets/images/" .. path .. ".png")'
    if source.count(anchor) != 1:
        raise TranslationError('图片加载脚本结构与补丁预期不符')
    return source.replace(anchor, anchor + '\n        image = require("zh_card_text").translate(path, image)', 1)


def patch_fancy_text(source):
    beginning = '        local fulljustspace = {}\n'
    after = '        if self.rendering ~= "left" then\n'
    if source.count(beginning) != 1 or source.count(after) != 1:
        raise TranslationError('文字换行脚本结构与补丁预期不符')
    start = source.index(beginning) + len(beginning)
    end = source.index(after, start)
    if not source[start:end].startswith('        for i = 1, #self.table_string do\n'):
        raise TranslationError('文字换行代码未找到')
    return source[:start] + WRAP_LOOP + source[end:]
