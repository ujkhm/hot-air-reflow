# hot-air-reflow

A closed-loop hot-air reflow oven for double-sided SMT, built from scratch. The controller is an STM32F103C8T6. The mechanical model, control board, and firmware live in this repository.

#### 繁體中文說明在 [README.zh-TW.md](README.zh-TW.md)。

## Layout

```
hot-air-reflow
├── FreeCAD/                      oven model (save the FCStd here)
├── KiCad/hot-air-reflow/         control board
├── BOM/                          bills of materials
├── Code/STM32/hot-air-reflow/    STM32CubeIDE + HAL firmware
└── scripts/                      read coordinates and sync aliases
```

Board-analysis output stays in `KiCad/hot-air-reflow/analysis/`, next to the KiCad project.

## License

[MIT](LICENSE)
