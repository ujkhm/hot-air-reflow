#include "app.h"

#include "board.h"
#include "main.h"

/*
 * Bench control until the panel UI and the heater/temperature path exist.
 * K1 steps the fan through 0, 25, 50, 75, 100 percent.
 * K2 turns the error LED on or off. While a fault is latched it clears the
 * fault instead, and only if the fan current has fallen back under the limit.
 * Three current samples above FAN_FAULT_MA force the fan off and light D3.
 */

#define DEBOUNCE_MS 20U
#define SAMPLE_MS 50U
#define FAN_FAULT_MA 5000
#define FAN_FAULT_TRIPS 3U

static const uint16_t fan_steps[] = {0U, 250U, 500U, 750U, 1000U};

static uint8_t stable_keys;
static uint32_t key_since[4];
static uint8_t fan_step;
static uint8_t over_count;
static bool fault;
static bool led_on;
static uint32_t next_sample_ms;

static void apply_outputs(void)
{
  if (fault) {
    board_fan_set(0);
    board_error_led(true);
    return;
  }
  board_fan_set(fan_steps[fan_step]);
  board_error_led(led_on);
}

static void on_key_press(unsigned key)
{
  if (key == 0U) {
    if (fault) {
      return;
    }
    fan_step++;
    if (fan_step >= (uint8_t)(sizeof fan_steps / sizeof fan_steps[0])) {
      fan_step = 0U;
    }
    apply_outputs();
    return;
  }

  if (key != 1U) {
    return;
  }

  if (fault) {
    if (board_fan_current_ma() < FAN_FAULT_MA) {
      fault = false;
      over_count = 0U;
      fan_step = 0U;
      led_on = false;
      apply_outputs();
    }
    return;
  }

  led_on = !led_on;
  apply_outputs();
}

static void poll_keys(uint32_t now_ms)
{
  uint8_t raw = board_keys();
  unsigned key;

  for (key = 0U; key < 4U; key++) {
    uint8_t mask = (uint8_t)(1U << key);

    if ((raw & mask) == (stable_keys & mask)) {
      key_since[key] = now_ms;
      continue;
    }
    if ((now_ms - key_since[key]) < DEBOUNCE_MS) {
      continue;
    }
    stable_keys ^= mask;
    key_since[key] = now_ms;
    if ((raw & mask) != 0U) {
      on_key_press(key);
    }
  }
}

static void poll_current(uint32_t now_ms)
{
  if (fault || board_fan_get() == 0U) {
    return;
  }
  if ((int32_t)(now_ms - next_sample_ms) < 0) {
    return;
  }
  next_sample_ms = now_ms + SAMPLE_MS;

  if (board_fan_current_ma() < FAN_FAULT_MA) {
    over_count = 0U;
    return;
  }
  over_count++;
  if (over_count < FAN_FAULT_TRIPS) {
    return;
  }
  fault = true;
  fan_step = 0U;
  led_on = true;
  apply_outputs();
}

void app_init(void)
{
  uint32_t now_ms;
  unsigned key;

  board_init();
  now_ms = HAL_GetTick();
  stable_keys = board_keys();
  for (key = 0U; key < 4U; key++) {
    key_since[key] = now_ms;
  }
  fan_step = 0U;
  over_count = 0U;
  fault = false;
  led_on = false;
  next_sample_ms = now_ms + SAMPLE_MS;
  apply_outputs();
}

void app_poll(void)
{
  uint32_t now_ms = HAL_GetTick();

  poll_keys(now_ms);
  poll_current(now_ms);
}
