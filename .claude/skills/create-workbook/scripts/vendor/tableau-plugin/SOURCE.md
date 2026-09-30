# Vendored from tableau/tableau-plugin

- Upstream: https://github.com/tableau/tableau-plugin
- Commit: `09de35629d347c53587fce4f8cffa09da7caa614`
- License: Apache License 2.0 (see `LICENSE.txt`, Copyright (c) 2025 Salesforce, Inc.)
- Modifications: none. Files are byte-for-byte copies; only a subset is included.

| Local path | Upstream path |
|---|---|
| `scripts/validate_workbook.py` | `plugins/tableau/skills/tableau-workbook-authoring/scripts/validate_workbook.py` |
| `scripts/requirements.txt` | `plugins/tableau/skills/tableau-workbook-authoring/scripts/requirements.txt` |
| `resources/schemas/{2025_1,2025_2,2025_3,2026_1,2026_2}/` | `plugins/tableau/skills/tableau-workbook-authoring/resources/schemas/` (same subfolders) |
| `resources/examples/*.json` | `plugins/tableau/skills/tableau-workbook-authoring/resources/examples/` |
| `LICENSE.txt` | `LICENSE.txt` |

The directory layout mirrors upstream so that `validate_workbook.py` finds `../resources/schemas/` by default.
Only schema versions 2025.1 and later are included; workbooks older than 2025.1 are rejected by the validator.
