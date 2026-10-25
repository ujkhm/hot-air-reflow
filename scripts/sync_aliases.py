# -*- coding: utf-8 -*-
"""Copy column D onto column C as the spreadsheet alias.

Column D is the name you read. Column C is the number the model reads.
Run this after editing column D. Expressions use Spreadsheet.<name>.

A name must start with a letter and use only letters, digits, and underscores.
"""

import os
import re

import FreeCAD as App

NAME_COL = "D"
VALUE_COL = "C"
MAX_ROW = 200
IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
CELL_ADDR = re.compile(r"^[A-Za-z]+[0-9]+$")
PROJECT_ROOT = r"E:\hot-air-reflow"
FREECAD_DIR = os.path.join(PROJECT_ROOT, "FreeCAD")


def cell_string(sheet, addr):
    try:
        value = sheet.get(addr)
    except Exception:
        return ""
    if value is None:
        return ""
    text = str(value).strip()
    if len(text) >= 2 and text[0] == "'" and text[-1] == "'":
        text = text[1:-1].strip()
    elif text.startswith("'"):
        text = text[1:].strip()
    return text


def alias_of(sheet, addr):
    try:
        return sheet.getAlias(addr) or ""
    except Exception:
        return ""


def last_used_row(sheet):
    last = 1
    blank = 0
    for row in range(1, MAX_ROW + 1):
        busy = False
        for col in "ABCD":
            addr = "%s%d" % (col, row)
            if cell_string(sheet, addr) or alias_of(sheet, addr):
                busy = True
                break
        if busy:
            last = row
            blank = 0
        else:
            blank += 1
            if blank >= 15 and row > last:
                break
    return last


def owner_of(sheet, name, last_row):
    for row in range(1, last_row + 1):
        for col in "ABCDEFGHIJKLMNOP":
            addr = "%s%d" % (col, row)
            if alias_of(sheet, addr) == name:
                return addr
    return ""


def sync_sheet(sheet):
    last = last_used_row(sheet)
    lines = []
    changed = 0
    seen = {}
    for row in range(1, last + 1):
        name_addr = "%s%d" % (NAME_COL, row)
        value_addr = "%s%d" % (VALUE_COL, row)
        name = cell_string(sheet, name_addr)
        if not name:
            continue
        if not IDENT.match(name) or CELL_ADDR.match(name):
            lines.append("%s  「%s」不能當別名" % (name_addr, name))
            continue
        if name in seen:
            lines.append("%s  「%s」和 %s 重複" % (name_addr, name, seen[name]))
            continue
        seen[name] = name_addr
        current = alias_of(sheet, value_addr)
        if current == name:
            lines.append("%s  %s" % (value_addr, name))
            continue
        other = owner_of(sheet, name, last)
        if other and other != value_addr:
            sheet.setAlias(other, "")
        sheet.setAlias(value_addr, name)
        changed += 1
        lines.append("%s  %s  （已寫入）" % (value_addr, name))
    return changed, lines


def newest_fcstd():
    if not os.path.isdir(FREECAD_DIR):
        return ""
    found = []
    for name in os.listdir(FREECAD_DIR):
        if name.lower().endswith(".fcstd"):
            path = os.path.join(FREECAD_DIR, name)
            found.append((os.path.getmtime(path), path))
    if not found:
        return ""
    found.sort()
    return found[-1][1]


def open_target():
    if App.ActiveDocument is not None:
        return App.ActiveDocument, False
    path = newest_fcstd()
    if not path:
        return None, False
    return App.openDocument(path), True


def main():
    doc, opened = open_target()
    if doc is None:
        App.Console.PrintError("sync_aliases: 沒有打開的文件\n")
        return

    sheets = [obj for obj in doc.Objects if obj.TypeId == "Spreadsheet::Sheet"]
    if not sheets:
        App.Console.PrintError("sync_aliases: 這份文件沒有試算表\n")
        if opened:
            App.closeDocument(doc.Name)
        return

    lines = ["file: %s" % (doc.FileName or "(unsaved)")]
    changed = 0
    for sheet in sheets:
        count, detail = sync_sheet(sheet)
        changed += count
        lines.append(sheet.Name)
        lines.extend("  " + line for line in detail)
    if changed:
        doc.recompute()
        lines.append("寫入 %d 個別名。存檔後才會留下。" % changed)
    else:
        lines.append("別名已和 D 欄一致。")

    text = "\n".join(lines) + "\n"
    App.Console.PrintMessage(text)
    if opened:
        App.closeDocument(doc.Name)


if __name__ == "__main__":
    main()
