# scripts

`dump_coords.py` 讀 FreeCAD 裡命名實體的邊界，以及表面距離在 0.5 mm 以內的對象。

在 FreeCAD 裡選取物件（不選就是整份文件）後執行巨集 `dump_coords`。沒有打開文件時，腳本改讀 `FreeCAD/` 裡最新的 `.FCStd`。

`sync_aliases.py` 把試算表 D 欄的簡稱寫成同一列 C 欄的別名。在 D 欄改完名字後執行巨集 `sync_aliases`，再存檔。

[回到主頁](../README.zh-TW.md)
