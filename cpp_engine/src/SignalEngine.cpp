#include "SignalEngine.hpp"
#include <cmath>

double SignalEngine::momentum(const std::vector<Candle>& candles, size_t index, int lookback) const {
    if (index < static_cast<size_t>(lookback)) return 0.0;
    double past = candles[index - lookback].close;
    double current = candles[index].close;
    return (current - past) / past;
}

Signal SignalEngine::generate(const std::vector<Candle>& candles, size_t index) const {
    if (index < 8) {
        return {SignalType::NONE, "Not enough candles", 0.0};
    }

    double shortMomentum = momentum(candles, index, 3);
    double longMomentum = momentum(candles, index, 8);
    const Candle& current = candles[index];

    double candleRange = current.high - current.low;
    double body = std::abs(current.close - current.open);
    double bodyStrength = candleRange > 0 ? body / candleRange : 0.0;

    if (shortMomentum > 0.0025 && longMomentum > 0.004 && bodyStrength > 0.45) {
        return {SignalType::LONG, "Bullish momentum continuation", std::min(0.99, shortMomentum * 100)};
    }

    if (shortMomentum < -0.0025 && longMomentum < -0.004 && bodyStrength > 0.45) {
        return {SignalType::SHORT, "Bearish momentum continuation", std::min(0.99, std::abs(shortMomentum) * 100)};
    }

    return {SignalType::NONE, "No valid momentum setup", 0.0};
}
