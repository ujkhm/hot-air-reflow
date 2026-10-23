# hot-air-reflow

A closed-loop hot-air reflow oven for double-sided SMT, built from scratch. The controller is an STM32F103C8T6. The mechanical model, control board, and firmware live in this repository.

#### 繁體中文說明在 [README.zh-TW.md](README.zh-TW.md)。

## Layout

```
hot-air-reflow
├── FreeCAD/        oven model (save the FCStd here)
├── KiCad/          control board
├── Code/STM32/     STM32CubeIDE + HAL firmware
└── scripts/        read coordinates from the FreeCAD model
```

The oven model is not in the repository yet. Save it under `FreeCAD/`.

## License

[MIT](LICENSE)
