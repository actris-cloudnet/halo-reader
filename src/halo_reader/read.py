from pathlib import Path

def read(src: list[Path], src_bg: list[Path]) -> None:
    for s in src:
        print(s)
    for sbg in src_bg:
        print(sbg)

