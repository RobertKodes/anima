"""Allow ``python -m anima`` (avoids blocked ``anima.exe`` shims on Windows)."""

from anima.app.cli import main

raise SystemExit(main())
