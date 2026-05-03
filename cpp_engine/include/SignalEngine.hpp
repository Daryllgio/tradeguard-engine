#pragma once

#include "Types.hpp"
#include <vector>

class SignalEngine {
public:
    Signal generate(const std::vector<Candle>& candles, size_t index) const;

private:
    double momentum(const std::vector<Candle>& candles, size_t index, int lookback) const;
};
