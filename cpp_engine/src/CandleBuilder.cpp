#include "CandleBuilder.hpp"
#include <algorithm>
#include <stdexcept>

CandleBuilder::CandleBuilder(int ticksPerCandle) : ticksPerCandle_(ticksPerCandle) {
    if (ticksPerCandle_ <= 0) {
        throw std::invalid_argument("ticksPerCandle must be positive");
    }
}

std::vector<Candle> CandleBuilder::build(const std::vector<Tick>& ticks) const {
    std::vector<Candle> candles;

    for (size_t i = 0; i + static_cast<size_t>(ticksPerCandle_) <= ticks.size(); i += ticksPerCandle_) {
        Candle candle;
        candle.timestamp = ticks[i].timestamp;
        candle.open = ticks[i].price;
        candle.high = ticks[i].price;
        candle.low = ticks[i].price;
        candle.close = ticks[i + ticksPerCandle_ - 1].price;
        candle.volume = 0.0;

        for (size_t j = i; j < i + static_cast<size_t>(ticksPerCandle_); ++j) {
            candle.high = std::max(candle.high, ticks[j].price);
            candle.low = std::min(candle.low, ticks[j].price);
            candle.volume += ticks[j].volume;
        }

        candles.push_back(candle);
    }

    return candles;
}
