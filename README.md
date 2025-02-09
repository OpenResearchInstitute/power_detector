# VHDL Power Detector

A versatile VHDL implementation of a power detector supporting both IQ (complex) and real signal processing with configurable dual-stage exponential moving average filtering.


## Overview

This module implements a configurable power detector that can process either:
- Complex (IQ) signals by computing I² + Q²
- Real signals by computing I² or Q² individually
- Dual-stage filtering for enhanced smoothing capabilities

The power computation is followed by two cascaded exponential moving average (EMA) filters for flexible signal smoothing.


## Features

- Support for both IQ and real signal processing
- Configurable input data width
- Dual-stage EMA filtering with independent alpha values
- Pipeline-optimized architecture
- Selectable I/Q processing modes
- Built-in squared magnitude computation
- Automatic width handling for multiplications and accumulations


## Interface

### Generics

| Parameter | Type    | Default | Description |
|-----------|---------|---------|-------------|
| DATA_W    | NATURAL | 12      | Width of input data |
| ALPHA_W   | NATURAL | 18      | Width of alpha (smoothing factor) inputs |
| IQ_MOD    | BOOLEAN | False   | Enable IQ (complex) mode |
| I_USED    | BOOLEAN | True    | Enable I channel processing |
| Q_USED    | BOOLEAN | False   | Enable Q channel processing |

### Ports

| Port           | Direction | Width          | Description |
|----------------|-----------|----------------|-------------|
| clk            | IN        | 1              | System clock |
| init           | IN        | 1              | Reset/initialization signal |
| alpha1         | IN        | ALPHA_W        | First stage EMA smoothing factor |
| alpha2         | IN        | ALPHA_W        | Second stage EMA smoothing factor |
| data_I         | IN        | DATA_W         | I channel input data |
| data_Q         | IN        | DATA_W         | Q channel input data |
| data_ena       | IN        | 1              | Input data enable |
| power_squared  | OUT       | 2*DATA_W-2     | Output power (magnitude squared) |


## Implementation Details

The power detector implements the following processing chain:

1. **Power Computation**:
   - IQ mode: power = I² + Q²
   - I only mode: power = I²
   - Q only mode: power = Q²

2. **Dual-stage Filtering**:
   ```
   First stage:  ema1[n] = alpha1 * power[n] + (1-alpha1) * ema1[n-1]
   Second stage: ema2[n] = alpha2 * ema1[n] + (1-alpha2) * ema2[n-1]
   ```


## Usage

1. Include the module and its dependencies in your project:
```vhdl
LIBRARY work;
USE work.ALL;
```

2. Instantiate the module:
```vhdl
power_detector_inst : ENTITY work.power_detector
    GENERIC MAP (
        DATA_W  => 12,
        ALPHA_W => 18,
        IQ_MOD  => True,    -- For complex signal processing
        I_USED  => True,
        Q_USED  => True
    )
    PORT MAP (
        clk           => system_clock,
        init          => reset,
        alpha1        => first_stage_alpha,
        alpha2        => second_stage_alpha,
        data_I        => i_channel_data,
        data_Q        => q_channel_data,
        data_ena      => data_valid,
        power_squared => power_output
    );
```


## Dependencies

This module requires the `lowpass_ema` module for the filtering stages. Ensure it's included in your project.


## Level Reference Definitions

There are two common standards for referencing digital signal levels:

1. **AES Standard (dBFS)**: Defined in AES17-1998 (and subsequent revisions), where 0 dBFS is referenced to the RMS value of a full-scale sine wave. For a signed N-bit system, this means:
   ```
   0 dBFS = RMS value of sine wave with peak value = ±(2^(N-1) - 1)
   ```
   This is the most commonly used standard in professional audio applications.

2. **ITU-T G.100.1 (dBov)**: Defines 0 dBov (decibels relative to the overload point) as the RMS value of a full-scale square wave. Under this definition:
   ```
   0 dBov = RMS of full-scale square wave
   -3 dBFS = RMS of full-scale sine wave
   ```
   This standard is often used in telecommunications applications.

References:
- AES17-1998 (r2009): AES standard method for digital audio engineering - Measurement of digital audio equipment
- ITU-T G.100.1: The use of the decibel and of relative levels in speechband telecommunications


## Computing RMS and Signal Levels

The power_detector module computes |x|² (power_squared output). To convert this to RMS and then to dBFS:

1. For a signed N-bit fixed-point input:
   - Full-scale sine peak value = 2^(N-1) - 1
   - RMS value of full-scale sine = (2^(N-1) - 1)/√2
   - Reference power (0 dBFS) = ((2^(N-1) - 1)/√2)²

2. Computing RMS from power_squared:
   ```
   RMS = √(power_squared)
   ```

3. The level in dBFS can then be computed as:
   ```
   dBFS = 20 * log10(RMS / reference_RMS)
   ```
   or equivalently:
   ```
   dBFS = 10 * log10(power_squared / reference_power)
   ```

Example for 12-bit signed input (DATA_W = 12):
```vhdl
-- Full-scale peak value = 2^11 - 1 = 2047
-- Reference RMS = 2047/√2 ≈ 1447.4
-- Reference power = (2047/√2)² ≈ 2,095,104
-- For power_squared output value P:
-- RMS = √P
-- dBFS = 20 * log10(√P / 1447.4)
--      = 10 * log10(P / 2,095,104)
```

For ITU-T G.100.1 dBov:
- Subtract 3 dB from the above calculation
- dBov = dBFS - 3
- A full-scale sine wave will read -3 dBov under ITU-T G.100.1, while reading 0 dBFS under AES17

Notes:
- When using IQ mode (I² + Q²), both reference power and RMS should be doubled
- For real power measurements, use the I or Q channel reference alone
- The square root operation for RMS calculation can be implemented in hardware if needed, but is often performed in software post-processing


## Notes

- Output width is automatically adjusted to account for squared values
- The dual-stage EMA filtering provides enhanced smoothing capabilities
- Pipeline stages are optimized for FPGA implementation
- The module supports flexible configuration for various signal processing needs
- All arithmetic operations include appropriate width handling to prevent overflow


## License

This project is licensed under the CERN Open Hardware License Version 2 - Weakly Reciprocal (CERN-OHL-W v2). See the header of the source file for full license text and conditions.


## Acknowledgements

This README.md created with the assistance of Claude.ai
