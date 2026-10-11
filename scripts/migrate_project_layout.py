"""Retired link-based migration, preserved in Git history at 0bdc5c3.

The current layout uses canonical project folders and must not recreate links.
"""


def main():
    raise SystemExit(
        "This migration is retired: symbolic-link aliases are prohibited. "
        "Use the current canonical layout documented in docs/architecture/PROJECT_LAYOUT.md."
    )


if __name__ == "__main__":
    main()
