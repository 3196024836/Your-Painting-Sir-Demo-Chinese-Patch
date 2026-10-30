"""Explicitly labelled offline test build; formal release remains gated."""
import sys
import tkinter as tk
from app import Application, load_resources
from patch_engine import PatchError
from release_bundle import check_translation_rows


def main():
    if '--check-resources' in sys.argv:
        try:
            profile, _, rows, font, licence, module = load_resources()
            check_translation_rows(rows)
            if not profile or not font or not licence or not module:
                raise PatchError('测试版内置资源缺失。')
        except (PatchError, OSError, ValueError) as e:
            print(str(e))
            return 2
        print('测试版资源检查通过；部分场景仍待验收。')
        return 0
    root = tk.Tk()
    Application(root, candidate=True)
    root.mainloop()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
