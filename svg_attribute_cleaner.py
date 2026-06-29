from __future__ import annotations

import sys

from svg_attribute_cleaner.cli import main as cli_main


if __name__ == "__main__":
    if len(sys.argv) == 1:
        from svg_attribute_cleaner.gui import main as gui_main
        gui_main()
    else:
        raise SystemExit(cli_main())
