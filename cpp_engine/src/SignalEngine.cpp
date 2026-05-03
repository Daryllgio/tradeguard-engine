#include "SignalEngine.hpp"
#include <algorithm>
#include <cmath>

double SignalEngine::momentum(const std::vector<Candle>& candles, size_t index, int lookback) const {
    if (index < static_cast<size_t>(lookback)) return 0.0;
    double past = candles[index - lookback].close;
    double current = candles[index].close;
    return past > 0 ? (current - past) / past : 0.0;
}

double SignalEngine::movingAverage(const std::vector<Candle>& candles, size_t index, int lookback) const {
    if (index + 1 < static_cast<size_t>(lookback)) return candles[index].close;

    double sum = 0.0;
    for (size_t i = index + 1 - lookback; i <= index; ++i) {
        sum += candles[i].close;
    }

    return sum / lookback;
}

double SignalEngine::averageVolume(const std::vector<Candle>& candles, size_t index, int lookback) const {
    if (index + 1 < static_cast<size_t>(lookback)) return candles[index].volume;

    double sum = 0.0;
    for (size_t i = index + 1 - lookback; i <= index; ++i) {
        sum += candles[i].volume;
    }

    return sum / lookback;
}

double SignalEngine::volatility(const std::vector<Candle>& candles, size_t index, int lookback) const {
    if (index < static_cast<size_t>(lookback)) return 0.0;

    double sumAbsReturns = 0.0;
    for (size_t i = index + 1 - lookback; i <= index; ++i) {
        double prev = candles[i - 1].close;
        double current = candles[i].close;
        if (prev > 0) {
            sumAbsReturns += std::abs((current - prev) / prev);
        }
    }

    return sumAbsReturns / lookback;
}

Signal SignalEngine::generate(const std::vector<Candle>& candles, size_t index) const {
    if (index < 12) {
        return {SignalType::NONE, "Not enough candles", 0.0};
    }

    const Candle& current = candles[index];

    double shortMomentum = momentum(candles, index, 3);
    double longMomentum = momentum(candles, index, 8);
    double smaFast = movingAverage(candles, index, 5);
    double smaSlow = movingAverage(candles, index, 12);
    double avgVol = averageVolume(candles, index, 10);
    double vol = volatility(candles, index, 10);

    double candleRange = current.high - current.low;
    double body = std::abs(current.close - current.open);
    double bodyStrength = candleRange > 0 ? body / candleRange : 0.0;

    bool volumeConfirmed = avgVol <= 0 || current.volume >= avgVol * 0.90;
    bool volatilityConfirmed = vol >= 0.00005;

    if (
        shortMomentum > 0.0015 &&
        longMomentum > 0.0025 &&
        smaFast >= smaSlow * 0.999 &&
        bodyStrength > 0.30 &&
        volumeConfirmed &&
        volatilityConfirmed
    ) {
        return {SignalType::LONG, "Bullish momentum with MA, volume, and volatility confirmation", std::min(0.99, shortMomentum * 120)};
    }

    if (
        shortMomentum < -0.0015 &&
        longMomentum < -0.0025 &&
        smaFast <= smaSlow * 1.001 &&
        bodyStrength > 0.30 &&
        volumeConfirmed &&
        volatilityConfirmed
    ) {
        return {SignalType::SHORT, "Bearish momentum with MA, volume, and volatility confirmation", std::min(0.99, std::abs(shortMomentum) * 120)};
    }

    return {SignalType::NONE, "No confirmed momentum setup", 0.0};
}
