"""Construct a patch from reviewed data and the user's own verified game resources."""
from collections import defaultdict
from pathlib import Path
import zipfile
from game_transform import TranslationError,validate_translation,apply_translations,patch_asset_font,patch_fancy_text,patch_textbox_spacing,patch_speech_bubble,patch_asset_images
from patch_engine import Bundle,PatchError,_check_target,_marker,_sha256,game_is_running

REQUIRED_CHECKS=('text_inventory_complete','text_proofread_complete','chinese_layout_complete',
                 'newspaper_artwork_complete','isolated_gameplay_checks_complete','installer_end_to_end_complete')

def check_translation_rows(rows):
    """Reject missing, unfinished, duplicate, or structurally unsafe translations."""
    unfinished=sum(1 for r in rows if r.get('status') not in ('已校对','保留原文'))
    if not rows or unfinished:
        raise PatchError(f'脚本清单有 {unfinished} 条待翻译或校对，未执行汉化。')
    seen=set()
    for row in rows:
        key=(row.get('path'),row.get('line'),row.get('column'))
        if key in seen:raise PatchError('文本清单有重复位置，未执行汉化。')
        seen.add(key)
        try:validate_translation(row.get('original'),row.get('translation'))
        except (TranslationError,TypeError) as e:raise PatchError('文本格式校验失败：'+str(e)) from e


def check_release(rows,checks):
    check_translation_rows(rows)
    missing=[key for key in REQUIRED_CHECKS if checks.get(key) is not True]
    if missing:
        raise PatchError(f'正式版尚未完成：还有 {len(missing)} 项发布检查未通过（包括图像和游戏验证）。')


def restore_bundle(profile):
    return Bundle(profile['original_sha256'],profile['patch_id'],{}, {})


def prepare_install_bundle(target,profile,rows,checks,font_bytes,license_bytes,card_module,*,running=game_is_running,progress=lambda *_:None,candidate=False):
    target=Path(target)
    if candidate:
        check_translation_rows(rows)
    else:
        check_release(rows,checks)
    if not font_bytes or not license_bytes or not card_module:raise PatchError('内置中文字体、许可文件或图像汉化数据缺失。')
    _check_target(target,running)
    if _marker(target):return restore_bundle(profile)
    progress('正在识别游戏版本…')
    try:
        if _sha256(target)!=profile['original_sha256']:
            raise PatchError('游戏版本或文件校验不匹配；此工具仅支持指定的试玩版。')
        by_path=defaultdict(list)
        for r in rows:
            if r['status']=='保留原文':continue
            by_path[r['path']].append({'line':int(r['line']),'column':int(r['column']),
                                      'original':r['original'],'translation':r['translation']})
        with zipfile.ZipFile(target) as archive:
            replacements={}
            for path,items in by_path.items():
                src=archive.read(path).decode('utf-8-sig')
                replacements[path]=apply_translations(src,items).encode('utf-8')
            for path,transform in [('core/utils/asset.lua',patch_asset_font),
                                   ('core/utils/asset.lua',patch_asset_images),
                                   ('libs/text.lua',patch_fancy_text),
                                   ('src/textbox/textbox.lua',patch_textbox_spacing),
                                   ('src/phone/crab/speech_bubble.lua',patch_speech_bubble)]:
                # Apply both translation and engine changes if a script appears in both groups.
                src=replacements[path].decode('utf-8') if path in replacements else archive.read(path).decode('utf-8-sig')
                replacements[path]=transform(src).encode('utf-8')
        return Bundle(profile['original_sha256'],profile['patch_id'],replacements,
                      {'assets/fonts/fusion-pixel-zh.ttf':font_bytes,
                       'assets/fonts/OFL-fusion-pixel.txt':license_bytes,
                       'zh_card_text.lua':card_module})
    except PatchError:raise
    except (OSError,KeyError,ValueError,UnicodeError,zipfile.BadZipFile,TranslationError) as e:
        raise PatchError('生成补丁数据失败；原版游戏未修改：'+str(e)) from e
