#pragma once

#include "Types.hpp"
#include <vector>

class SignalEngine {
public:
    Signal generate(const std::vector<Candle>& candles, size_t index) const;

private:
    double momentum(const std::vector<Candle>& candles, size_t index, int lookback) const;
    double movingAverage(const std::vector<Candle>& candles, size_t index, int lookback) const;
    double averageVolume(const std::vector<Candle>& candles, size_t index, int lookback) const;
    double volatility(const std::vector<Candle>& candles, size_t index, int lookback) const;
};
