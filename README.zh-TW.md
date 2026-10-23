# 熱風回流焊爐

自製密閉循環熱風回流焊爐，用來焊雙面貼片。控制器是 STM32F103C8T6。爐體模型、控制板和韌體都放在這個倉庫。

英文說明在 [README.md](README.md)。

## 資料夾

```
hot-air-reflow
├── FreeCAD/        爐體模型，FCStd 存這裡
├── KiCad/          控制板
├── Code/STM32/     STM32CubeIDE + HAL 韌體
└── scripts/        從 FreeCAD 模型讀座標
```

爐體還沒畫。模型存進 `FreeCAD/`。問結構時寫模型樹上的物件名稱；要貼座標就在 FreeCAD 執行巨集 `dump_coords`。

## 授權

[MIT](LICENSE)
