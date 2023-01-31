from typing import Optional


def bad_display_list(output_file: Optional[str] = None) -> None:
    if output_file is None:
        with open(output_file, "w", encoding="utf-8") as fout:
            print("yay")


def good_display_list(output_file: Optional[str] = None) -> None:
    if output_file is None:
        with open(output_file, "w", encoding="utf-8") as fout:
            print("no")
