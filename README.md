# Your Painting, Sir Demo 简体中文汉化工具 / Simplified Chinese Patch

> **测试版 / Beta:** 译文和功能仍在验证中。完整通关、部分剧情分支、图片文字及解谜流程尚未全部实机验收。
> **Beta:** Translation and gameplay validation are ongoing. A full playthrough and some story branches, image text, and puzzles have not yet been verified in-game.

为 **Windows 试玩版 `DEMO-1.2.16`** 制作的非官方简体中文汉化工具。下载独立 EXE，选择你自己安装的游戏 EXE，即可离线安装或恢复英文版。

An unofficial Simplified Chinese localization tool for the **Windows demo `DEMO-1.2.16`**. Download the standalone EXE and select your own installed game EXE to install the patch or restore English, entirely offline.

## 下载 / Download

[下载测试版 · Download the beta](https://github.com/3196024836/Your-Painting-Sir-Demo-Chinese-Patch/releases/tag/v0.1.0-beta.1)

下载发布页中的 `YourPaintingSir-ZH-Beta.exe`。工具已内置译文、字体和所需运行组件，不需要另外安装 Python，也不需要联网。请自行取得并安装游戏；仓库及安装器不包含原版游戏 EXE 或完整游戏资源。

Download `YourPaintingSir-ZH-Beta.exe` from the release page. The tool bundles the translations, font, and runtime; Python and an internet connection are not required to use it. You must obtain and install the game separately. Neither the repository nor the installer includes the original game EXE or complete game assets.

## 安装汉化 / Install the patch

1. 关闭游戏。运行 `YourPaintingSir-ZH-Beta.exe`。
2. 点击 **选择文件…**，选择游戏目录中的 `Your Painting, Sir.exe`。
3. 点击 **开始汉化**，等待完成提示，然后尝试从 Steam 启动游戏。
4. 如果游戏目录不允许写入，关闭游戏后右键工具，选择“以管理员身份运行”。

1. Exit the game and run `YourPaintingSir-ZH-Beta.exe`.
2. Click **选择文件…** (Choose file) and select `Your Painting, Sir.exe` in the game folder.
3. Click **开始汉化** (Install Chinese), wait for the completion message, then try launching the game through Steam.
4. If Windows denies write access to the game directory, close the game and run the tool as administrator.

工具会检查游戏文件是否与支持的试玩版完全匹配，在原位置保留 `Your Painting, Sir.exe.zh-backup` 备份，并先生成临时文件再替换；重复安装不会覆盖原版备份。工具不修改玩家存档。请保留备份，不要手动改名或删除。

The tool checks the game file against the exact supported demo build, keeps an original backup named `Your Painting, Sir.exe.zh-backup` alongside it, and creates a temporary patched file before replacement. Reinstalling does not overwrite the backup. The tool does not modify player saves. Keep the backup and do not rename or delete it.

## 恢复英文 / Restore English

关闭游戏，再次打开工具并选择同一个游戏 EXE，点击 **恢复英文版**。Steam 更新或验证游戏文件后，如果游戏恢复为受支持的英文原版，可重新运行工具；如果版本或文件不匹配，工具会停止并提示。

Exit the game, reopen the tool, select the same game EXE, and click **恢复英文版** (Restore English). If Steam updates or verifies the game and restores the supported English build, you can run the tool again. The tool stops with a message if the version or file no longer matches.

## 测试版状态 / Beta status

- 翻译清单有 **999** 项：**929** 项标记为已校对，**70** 项保留原文。部分图片保留英文并附有中文。
  The translation inventory contains **999** entries: **929** marked as proofread and **70** retained in English. Some images retain English with Chinese annotations.
- 已在隔离副本检查菜单、教程画面、报纸、电话任务画面、小游戏和沙盒；五幅画各抽取一张裁片，比较过原版与汉化版在指定位置的判定。
  Menu, tutorial screens, newspapers, phone-quest screens, a minigame and sandbox were inspected using an isolated copy. One cutout from each of the five paintings was compared at selected positions between the original and patched game.
- **尚未完成完整自然通关、所有剧情分支及图片线索的逐一实机检查。** 可能仍有漏译、排版或剧情问题。
  **A full natural playthrough and individual checks of every story branch and image clue are still outstanding.** Missing translations, layout issues, or story-specific problems may remain.
- 安装、重复安装与恢复流程已在隔离副本测试；当前测试版不代表已完成正式版验收。
  Installation, repeat installation, and restoration were tested on an isolated copy. This beta has not passed the formal release checklist.

发现问题时，欢迎提交 Issue，并说明场景、操作步骤及截图。请勿上传包含个人信息的存档。

Please report problems through an issue with the scene, reproduction steps, and a screenshot. Do not upload saves containing personal information.

## 源码与字体 / Source and font

- 译文及校对状态 / Translations and review status: [`data/待译文本.csv`](data/待译文本.csv)
- 术语表 / Terminology: [`data/术语表.md`](data/术语表.md)
- 自动化测试 / Automated tests: `python -m unittest discover -s tests -v`
- 在 Windows 使用 Python 3.11 和 PyInstaller 6.20.0 构建测试版 / Build the beta on Windows with Python 3.11 and PyInstaller 6.20.0: `python source/build_candidate.py`
- 中文字体使用 [Fusion Pixel Font](https://github.com/TakWolf/fusion-pixel-font)，许可为 SIL Open Font License 1.1；完整许可见 [`data/fonts/OFL.txt`](data/fonts/OFL.txt)。
  The Chinese font is [Fusion Pixel Font](https://github.com/TakWolf/fusion-pixel-font), licensed under the SIL Open Font License 1.1; see [`data/fonts/OFL.txt`](data/fonts/OFL.txt).

本项目是非官方汉化。游戏及其名称、角色、原文等相关权利归各自权利人所有。
This is an unofficial localization. The game, its name, characters, original text, and associated rights belong to their respective owners.
