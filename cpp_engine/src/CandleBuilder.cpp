#include "CandleBuilder.hpp"
#include <algorithm>
#include <map>
#include <stdexcept>

CandleBuilder::CandleBuilder(int ticksPerCandle) : ticksPerCandle_(ticksPerCandle) {
    if (ticksPerCandle_ <= 0) {
        throw std::invalid_argument("ticksPerCandle must be positive");
    }
}

std::vector<Candle> CandleBuilder::build(const std::vector<Tick>& ticks) const {
    std::map<std::string, std::vector<Tick>> ticksBySymbol;

    for (const auto& tick : ticks) {
        ticksBySymbol[tick.symbol].push_back(tick);
    }

    std::vector<Candle> candles;

    for (const auto& [symbol, symbolTicks] : ticksBySymbol) {
        for (size_t i = 0; i + static_cast<size_t>(ticksPerCandle_) <= symbolTicks.size(); i += ticksPerCandle_) {
            Candle candle;
            candle.timestamp = symbolTicks[i].timestamp;
            candle.symbol = symbol;
            candle.open = symbolTicks[i].price;
            candle.high = symbolTicks[i].price;
            candle.low = symbolTicks[i].price;
            candle.close = symbolTicks[i + ticksPerCandle_ - 1].price;
            candle.volume = 0.0;

            for (size_t j = i; j < i + static_cast<size_t>(ticksPerCandle_); ++j) {
                candle.high = std::max(candle.high, symbolTicks[j].price);
                candle.low = std::min(candle.low, symbolTicks[j].price);
                candle.volume += symbolTicks[j].volume;
            }

            candles.push_back(candle);
        }
    }

    std::sort(candles.begin(), candles.end(), [](const Candle& a, const Candle& b) {
        if (a.symbol == b.symbol) return a.timestamp < b.timestamp;
        return a.symbol < b.symbol;
    });

    return candles;
}
