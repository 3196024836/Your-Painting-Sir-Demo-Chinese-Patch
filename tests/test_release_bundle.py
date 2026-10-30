import json,sys,tempfile,unittest,zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'source'))
from patch_engine import PatchError,_sha256,install,restore
from release_bundle import REQUIRED_CHECKS,check_release,check_translation_rows,prepare_install_bundle

class ReleaseBundleTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
  self.game=self.root/'Your Painting, Sir.exe';self.game.write_bytes(b'MZ'+b'fake-love-launcher')
  self.asset='image = love.graphics.newImage("assets/images/" .. path .. ".png")\nlocal font_formats = {\n}\nfont = love.graphics.newFont("assets/fonts/" .. path .. v, size, hinting)\n'
  self.fancy='        local fulljustspace = {}\n        for i = 1, #self.table_string do\n            ORIGINAL\n        end\n        if self.rendering ~= "left" then\n'
  with zipfile.ZipFile(self.game,'a') as z:
   z.writestr('core/utils/asset.lua',self.asset)
   z.writestr('libs/text.lua',self.fancy)
   z.writestr('src/textbox/textbox.lua','adjust_line_height = -3,')
   z.writestr('src/phone/crab/speech_bubble.lua','local text = self:setText(0, 8)\nfunction SpeechBubble:update(dt)')
   z.writestr('data/dialog/example.lua','return { text="hello" }')
  self.profile={'original_sha256':_sha256(self.game),'patch_id':'test-patch'}
  self.rows=[{'path':'data/dialog/example.lua','line':'1','column':'15','original':'hello','translation':'你好','status':'已校对'}]
  self.checks={name:True for name in REQUIRED_CHECKS}
 def tearDown(self):self.tmp.cleanup()
 def test_unfinished_quality_blocks_release(self):
  checks=dict(self.checks);checks['newspaper_artwork_complete']=False
  with self.assertRaises(PatchError):check_release(self.rows,checks)
  draft=[dict(self.rows[0],status='待校对')]
  with self.assertRaises(PatchError):check_release(draft,self.checks)
 def test_candidate_keeps_release_checks_pending_but_requires_reviewed_safe_rows(self):
  pending=dict(self.checks);pending['isolated_gameplay_checks_complete']=False
  with self.assertRaises(PatchError):
   prepare_install_bundle(self.game,self.profile,self.rows,pending,b'font',b'license',b'--card module',running=lambda _:False)
  bundle=prepare_install_bundle(self.game,self.profile,self.rows,pending,b'font',b'license',b'--card module',running=lambda _:False,candidate=True)
  self.assertIn('你好',bundle.replacements['data/dialog/example.lua'].decode())
  self.assertFalse(pending['isolated_gameplay_checks_complete'])
  with self.assertRaises(PatchError):
   prepare_install_bundle(self.game,self.profile,[dict(self.rows[0],status='待校对')],pending,b'font',b'license',b'--card module',running=lambda _:False,candidate=True)
  with self.assertRaises(PatchError):
   check_translation_rows([dict(self.rows[0],original='Press [hl]A[/hl]',translation='按A')])
 def test_release_rejects_broken_controls_even_if_marked_reviewed(self):
  broken=[dict(self.rows[0],original='Press [hl]A[/hl]',translation='按A')]
  with self.assertRaises(PatchError):check_release(broken,self.checks)
 def test_bundle_built_from_selected_original_and_round_trips(self):
  bundle=prepare_install_bundle(self.game,self.profile,self.rows,self.checks,b'font',b'license',b'--card module',running=lambda _:False)
  self.assertIn('你好',bundle.replacements['data/dialog/example.lua'].decode())
  self.assertIn(b'fusion-pixel-zh.ttf',bundle.replacements['core/utils/asset.lua'])
  self.assertIn(b'zh_card_text',bundle.replacements['core/utils/asset.lua'])
  self.assertEqual(bundle.additions['zh_card_text.lua'],b'--card module')
  self.assertEqual('installed',install(self.game,bundle,running=lambda _:False))
  repeat=prepare_install_bundle(self.game,self.profile,self.rows,self.checks,b'font',b'license',b'--card module',running=lambda _:False)
  self.assertEqual('already_installed',install(self.game,repeat,running=lambda _:False))
  self.assertEqual('restored',restore(self.game,repeat,running=lambda _:False))
 def test_wrong_version_and_running_game_are_rejected_before_extract(self):
  with self.assertRaises(PatchError):prepare_install_bundle(self.game,dict(self.profile,original_sha256='bad'),self.rows,self.checks,b'font',b'license',b'--card module',running=lambda _:False)
  with self.assertRaises(PatchError):prepare_install_bundle(self.game,self.profile,self.rows,self.checks,b'font',b'license',b'--card module',running=lambda _:True)

if __name__=='__main__':unittest.main()

