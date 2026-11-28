#include "board.h"

#include "main.h"

#define DISP_CS_PORT GPIOA
#define DISP_CS_PIN GPIO_PIN_4
#define DISP_DC_PORT GPIOA
#define DISP_DC_PIN GPIO_PIN_6
#define DISP_RES_PORT GPIOB
#define DISP_RES_PIN GPIO_PIN_0

#define KEY1_PORT GPIOB
#define KEY1_PIN GPIO_PIN_1
#define KEY2_PORT GPIOB
#define KEY2_PIN GPIO_PIN_2
#define KEY3_PORT GPIOB
#define KEY3_PIN GPIO_PIN_10
#define KEY4_PORT GPIOB
#define KEY4_PIN GPIO_PIN_11

#define FLASH_CS_PORT GPIOB
#define FLASH_CS_PIN GPIO_PIN_12

#define LED_PORT GPIOC
#define LED_PIN GPIO_PIN_13

#define FAN_PORT GPIOA
#define FAN_PIN GPIO_PIN_2
#define SENSE_PORT GPIOA
#define SENSE_PIN GPIO_PIN_3

/* TIM2 clock is 72 MHz. /3 /960 = 25 kHz, with 960 duty steps. */
#define FAN_TIM_PSC 2U
#define FAN_TIM_PERIOD 960U

#define ADC_VREF_MV 3300U
#define ADC_FULL_SCALE 4095U
#define FAN_SHUNT_MOHM 1U
#define FAN_SENSE_GAIN 50U

extern SPI_HandleTypeDef hspi1;

static SPI_HandleTypeDef hspi2;
static uint16_t fan_permille;

static void pin_output(GPIO_TypeDef *port, uint16_t pin, GPIO_PinState idle)
{
  GPIO_InitTypeDef gpio = {0};

  HAL_GPIO_WritePin(port, pin, idle);
  gpio.Pin = pin;
  gpio.Mode = GPIO_MODE_OUTPUT_PP;
  gpio.Pull = GPIO_NOPULL;
  gpio.Speed = GPIO_SPEED_FREQ_HIGH;
  HAL_GPIO_Init(port, &gpio);
}

static void pin_input_pullup(GPIO_TypeDef *port, uint16_t pin)
{
  GPIO_InitTypeDef gpio = {0};

  gpio.Pin = pin;
  gpio.Mode = GPIO_MODE_INPUT;
  gpio.Pull = GPIO_PULLUP;
  HAL_GPIO_Init(port, &gpio);
}

static int wait_clear(volatile uint32_t *reg, uint32_t mask)
{
  uint32_t spins = 1000000U;

  while ((*reg & mask) != 0U) {
    if (--spins == 0U) {
      return -1;
    }
  }
  return 0;
}

static void display_spi_init(void)
{
  /* Cube generated SPI1 as full duplex and claimed PA6 as MISO.
   * The panel has no MISO; PA6 is the data/command pin. */
  HAL_SPI_DeInit(&hspi1);
  hspi1.Init.Direction = SPI_DIRECTION_1LINE;
  if (HAL_SPI_Init(&hspi1) != HAL_OK) {
    Error_Handler();
  }
  pin_output(DISP_DC_PORT, DISP_DC_PIN, GPIO_PIN_RESET);
}

static void flash_spi_init(void)
{
  GPIO_InitTypeDef gpio = {0};

  __HAL_RCC_SPI2_CLK_ENABLE();

  gpio.Pin = GPIO_PIN_13 | GPIO_PIN_15;
  gpio.Mode = GPIO_MODE_AF_PP;
  gpio.Pull = GPIO_NOPULL;
  gpio.Speed = GPIO_SPEED_FREQ_HIGH;
  HAL_GPIO_Init(GPIOB, &gpio);

  gpio.Pin = GPIO_PIN_14;
  gpio.Mode = GPIO_MODE_INPUT;
  gpio.Pull = GPIO_NOPULL;
  HAL_GPIO_Init(GPIOB, &gpio);

  hspi2.Instance = SPI2;
  hspi2.Init.Mode = SPI_MODE_MASTER;
  hspi2.Init.Direction = SPI_DIRECTION_2LINES;
  hspi2.Init.DataSize = SPI_DATASIZE_8BIT;
  hspi2.Init.CLKPolarity = SPI_POLARITY_LOW;
  hspi2.Init.CLKPhase = SPI_PHASE_1EDGE;
  hspi2.Init.NSS = SPI_NSS_SOFT;
  hspi2.Init.BaudRatePrescaler = SPI_BAUDRATEPRESCALER_2;
  hspi2.Init.FirstBit = SPI_FIRSTBIT_MSB;
  hspi2.Init.TIMode = SPI_TIMODE_DISABLE;
  hspi2.Init.CRCCalculation = SPI_CRCCALCULATION_DISABLE;
  hspi2.Init.CRCPolynomial = 7;
  if (HAL_SPI_Init(&hspi2) != HAL_OK) {
    Error_Handler();
  }
}

static void fan_pwm_init(void)
{
  pin_output(FAN_PORT, FAN_PIN, GPIO_PIN_RESET);

  __HAL_RCC_TIM2_CLK_ENABLE();
  TIM2->PSC = FAN_TIM_PSC;
  TIM2->ARR = FAN_TIM_PERIOD - 1U;
  TIM2->CCR3 = 0U;
  TIM2->CCMR2 = (TIM2->CCMR2 & ~TIM_CCMR2_OC3M) |
                TIM_CCMR2_OC3M_2 | TIM_CCMR2_OC3M_1 | TIM_CCMR2_OC3PE;
  TIM2->CCER |= TIM_CCER_CC3E;
  TIM2->CR1 |= TIM_CR1_ARPE;
  TIM2->EGR = TIM_EGR_UG;
  TIM2->CR1 |= TIM_CR1_CEN;

  GPIO_InitTypeDef gpio = {0};
  gpio.Pin = FAN_PIN;
  gpio.Mode = GPIO_MODE_AF_PP;
  gpio.Pull = GPIO_NOPULL;
  gpio.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(FAN_PORT, &gpio);
  fan_permille = 0U;
}

static void sense_adc_init(void)
{
  GPIO_InitTypeDef gpio = {0};

  __HAL_RCC_ADC1_CLK_ENABLE();
  /* 72 MHz / 6 = 12 MHz, inside the 14 MHz ADC clock limit. */
  RCC->CFGR = (RCC->CFGR & ~RCC_CFGR_ADCPRE) | RCC_CFGR_ADCPRE_DIV6;

  gpio.Pin = SENSE_PIN;
  gpio.Mode = GPIO_MODE_ANALOG;
  gpio.Pull = GPIO_NOPULL;
  HAL_GPIO_Init(SENSE_PORT, &gpio);

  ADC1->CR1 = 0U;
  ADC1->CR2 = 0U;
  ADC1->SQR1 = 0U;
  ADC1->SQR3 = 3U;
  ADC1->SMPR2 = ADC_SMPR2_SMP3;

  ADC1->CR2 |= ADC_CR2_ADON;
  HAL_Delay(1);
  ADC1->CR2 |= ADC_CR2_RSTCAL;
  if (wait_clear(&ADC1->CR2, ADC_CR2_RSTCAL) != 0) {
    Error_Handler();
  }
  ADC1->CR2 |= ADC_CR2_CAL;
  if (wait_clear(&ADC1->CR2, ADC_CR2_CAL) != 0) {
    Error_Handler();
  }
}

static uint16_t sense_adc_read(void)
{
  uint32_t spins = 1000000U;

  ADC1->SR = 0U;
  ADC1->CR2 |= ADC_CR2_ADON;
  while ((ADC1->SR & ADC_SR_EOC) == 0U) {
    if (--spins == 0U) {
      Error_Handler();
    }
  }
  return (uint16_t)ADC1->DR;
}

void board_init(void)
{
  __HAL_RCC_GPIOA_CLK_ENABLE();
  __HAL_RCC_GPIOB_CLK_ENABLE();
  __HAL_RCC_GPIOC_CLK_ENABLE();

  pin_output(DISP_CS_PORT, DISP_CS_PIN, GPIO_PIN_SET);
  pin_output(DISP_RES_PORT, DISP_RES_PIN, GPIO_PIN_RESET);
  pin_output(FLASH_CS_PORT, FLASH_CS_PIN, GPIO_PIN_SET);
  pin_output(LED_PORT, LED_PIN, GPIO_PIN_RESET);
  pin_input_pullup(KEY1_PORT, KEY1_PIN);
  pin_input_pullup(KEY2_PORT, KEY2_PIN);
  pin_input_pullup(KEY3_PORT, KEY3_PIN);
  pin_input_pullup(KEY4_PORT, KEY4_PIN);

  display_spi_init();
  flash_spi_init();
  fan_pwm_init();
  sense_adc_init();

  HAL_GPIO_WritePin(DISP_RES_PORT, DISP_RES_PIN, GPIO_PIN_RESET);
  HAL_Delay(10);
  HAL_GPIO_WritePin(DISP_RES_PORT, DISP_RES_PIN, GPIO_PIN_SET);
}

void board_error_led(bool on)
{
  HAL_GPIO_WritePin(LED_PORT, LED_PIN, on ? GPIO_PIN_SET : GPIO_PIN_RESET);
}

void board_fan_set(uint16_t permille)
{
  uint32_t compare;

  if (permille > 1000U) {
    permille = 1000U;
  }
  compare = ((uint32_t)permille * FAN_TIM_PERIOD) / 1000U;
  TIM2->CCR3 = compare;
  fan_permille = permille;
}

uint16_t board_fan_get(void)
{
  return fan_permille;
}

int32_t board_fan_current_ma(void)
{
  uint32_t sum = 0U;
  uint32_t counts;
  int sample;

  for (sample = 0; sample < 4; sample++) {
    sum += sense_adc_read();
  }
  counts = sum / 4U;
  return (int32_t)(((uint64_t)counts * ADC_VREF_MV * 1000ULL) /
                   ((uint64_t)ADC_FULL_SCALE * FAN_SHUNT_MOHM * FAN_SENSE_GAIN));
}

uint8_t board_keys(void)
{
  uint8_t pressed = 0U;

  if (HAL_GPIO_ReadPin(KEY1_PORT, KEY1_PIN) == GPIO_PIN_RESET) {
    pressed |= 1U << 0;
  }
  if (HAL_GPIO_ReadPin(KEY2_PORT, KEY2_PIN) == GPIO_PIN_RESET) {
    pressed |= 1U << 1;
  }
  if (HAL_GPIO_ReadPin(KEY3_PORT, KEY3_PIN) == GPIO_PIN_RESET) {
    pressed |= 1U << 2;
  }
  if (HAL_GPIO_ReadPin(KEY4_PORT, KEY4_PIN) == GPIO_PIN_RESET) {
    pressed |= 1U << 3;
  }
  return pressed;
}

void board_disp_cs(bool selected)
{
  HAL_GPIO_WritePin(DISP_CS_PORT, DISP_CS_PIN, selected ? GPIO_PIN_RESET : GPIO_PIN_SET);
}

void board_disp_dc(bool data)
{
  HAL_GPIO_WritePin(DISP_DC_PORT, DISP_DC_PIN, data ? GPIO_PIN_SET : GPIO_PIN_RESET);
}

int board_disp_write(const uint8_t *data, uint16_t length)
{
  if (data == NULL || length == 0U) {
    return -1;
  }
  if (HAL_SPI_Transmit(&hspi1, (uint8_t *)data, length, 100) != HAL_OK) {
    return -1;
  }
  return 0;
}

void board_flash_cs(bool selected)
{
  HAL_GPIO_WritePin(FLASH_CS_PORT, FLASH_CS_PIN, selected ? GPIO_PIN_RESET : GPIO_PIN_SET);
}

int board_flash_transfer(const uint8_t *tx, uint8_t *rx, uint16_t length)
{
  HAL_StatusTypeDef status;

  if (length == 0U) {
    return -1;
  }
  if (tx != NULL && rx != NULL) {
    status = HAL_SPI_TransmitReceive(&hspi2, (uint8_t *)tx, rx, length, 100);
  } else if (tx != NULL) {
    status = HAL_SPI_Transmit(&hspi2, (uint8_t *)tx, length, 100);
  } else if (rx != NULL) {
    uint16_t index;
    uint8_t clock = 0xFFU;

    for (index = 0U; index < length; index++) {
      status = HAL_SPI_TransmitReceive(&hspi2, &clock, &rx[index], 1, 100);
      if (status != HAL_OK) {
        return -1;
      }
    }
    return 0;
  } else {
    return -1;
  }
  return (status == HAL_OK) ? 0 : -1;
}
