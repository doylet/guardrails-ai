#!/usr/bin/env python3
import os, re, sys
ROOT = os.getcwd()
FORBIDDEN = [r"from\s+src\.ai_deck_gen\.engine", r"from\s+ai_deck_gen\.engine", r"import\s+src\.ai_deck_gen\.engine"]
def scan_py(path):
    try:
        with open(path, "r", encoding="utf-8") as f: txt = f.read()
    except Exception: return []
    return [pat for pat in FORBIDDEN if re.search(pat, txt)]
def main():
    bad=[]
    for root,_,files in os.walk(ROOT):
        for fn in files:
            if fn.endswith(".py") and ("demo" in fn.lower() or "demos" in root.lower()):
                p=os.path.join(root,fn); hits=scan_py(p)
                if hits: bad.append((p,hits))
    if bad:
        print("Found demo scripts importing internal modules:")
        for p,h in bad: print(" -",p,"patterns:",h)
        sys.exit(1)
    print("Demo lint passed."); sys.exit(0)
if __name__=="__main__": main()
