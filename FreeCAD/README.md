# FreeCAD

爐體模型存成這個資料夾裡的 `.FCStd`。

三個基準點：`axis_origin`、`axis_px`、`axis_py`。空氣與板子用這些名稱：`gap_upper`、`gap_lower`、`plenum_upper`、`plenum_lower`、`plate_upper`、`plate_lower`、`return_a`、`return_b`、`impeller_in`、`heater`、`exhaust`、`board`。

在 FreeCAD 選取物件後執行巨集 `dump_coords`。剪貼簿和模型旁邊的 `coords.txt` 是同一段文字。`coords.txt` 不進 git。

試算表 D 欄是給人看的簡稱。改完後執行巨集 `sync_aliases`，同一列 C 欄的別名會跟上去。

[回到主頁](../README.zh-TW.md)
