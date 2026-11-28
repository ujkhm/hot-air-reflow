#ifndef BOARD_H
#define BOARD_H

#include <stdbool.h>
#include <stdint.h>

/*
 * Pins match the control-board netlist (U1 on hot-air-reflow.kicad_pcb).
 *
 * PA2  motor_PWM   fan low-side switch, via U4 into Q1. High turns the fan on.
 * PA3  ADC1_IN3    U5 INA181A2 output. Gain 50, shunt R10 = 1 mOhm.
 * PA4  SPI1_CS     display chip select, idle high
 * PA5  SPI1_SCK    display clock
 * PA6  DC          display data/command. High = data.
 * PA7  SPI1_MOSI   display data
 * PB0  RES         display reset, active low
 * PB1  K1          keys, idle high, pressed = low
 * PB2  K2
 * PB10 K3
 * PB11 K4
 * PB12 SPI2_CS     GD25Q16 chip select, idle high
 * PB13 SPI2_SCK
 * PB14 SPI2_MISO
 * PB15 SPI2_MOSI
 * PC13 ERROR_LED   D3 anode. High lights the LED.
 *
 * U6 (heater optocoupler) and Q2 (triac) are not connected to the MCU.
 */

void board_init(void);

void board_error_led(bool on);

/* permille: 0 is off, 1000 is fully on. Larger values are clamped. */
void board_fan_set(uint16_t permille);
uint16_t board_fan_get(void);

/* Fan current in milliamps, from the shunt amplifier. */
int32_t board_fan_current_ma(void);

/* Bit 0 is K1 .. bit 3 is K4. A set bit means that key is pressed. */
uint8_t board_keys(void);

void board_disp_cs(bool selected);
void board_disp_dc(bool data);
int board_disp_write(const uint8_t *data, uint16_t length);

void board_flash_cs(bool selected);
int board_flash_transfer(const uint8_t *tx, uint8_t *rx, uint16_t length);

#endif
