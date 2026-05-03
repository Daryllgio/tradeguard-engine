#pragma once

#include "Types.hpp"
#include <vector>

class CandleBuilder {
public:
    explicit CandleBuilder(int ticksPerCandle);
    std::vector<Candle> build(const std::vector<Tick>& ticks) const;

private:
    int ticksPerCandle_;
};
