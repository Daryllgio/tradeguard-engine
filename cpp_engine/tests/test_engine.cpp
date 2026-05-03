#include "RiskEngine.hpp"
#include "SignalEngine.hpp"
#include "Types.hpp"

#include <iostream>
#include <vector>
#include <unordered_map>
#include <stdexcept>

static void assertTrue(bool condition, const std::string& message) {
    if (!condition) {
        throw std::runtime_error("Test failed: " + message);
    }
}

static Candle candle(double open, double high, double low, double close) {
    return Candle{
        "2026-01-02T09:30:00",
        "AAPL",
        open,
        high,
        low,
        close,
        1000.0
    };
}

static void testRiskRejectsNoSignal() {
    RiskConfig config;
    RiskEngine engine(config);

    Signal signal;
    signal.type = SignalType::NONE;
    signal.reason = "No setup";

    TradeDecision decision = engine.evaluate(candle(100, 101, 99, 100), signal, 0.0);

    assertTrue(decision.decision == DecisionType::REJECTED, "RiskEngine should reject NONE signal");
    assertTrue(decision.quantity == 0, "Rejected trade should have quantity 0");
}

static void testRiskAcceptsValidLongSignal() {
    RiskConfig config;
    config.accountEquity = 10000.0;
    config.maxRiskPerTradePct = 0.01;
    config.maxPositionValuePct = 0.25;
    config.stopLossPct = 0.004;
    config.takeProfitPct = 0.008;

    RiskEngine engine(config);

    Signal signal;
    signal.type = SignalType::LONG;
    signal.reason = "Bullish momentum continuation";
    signal.confidence = 0.75;

    TradeDecision decision = engine.evaluate(candle(100, 102, 99, 100), signal, 0.0);

    assertTrue(decision.decision == DecisionType::ACCEPTED, "RiskEngine should accept valid LONG signal");
    assertTrue(decision.quantity > 0, "Accepted trade should have positive quantity");
    assertTrue(decision.stopLoss < decision.entryPrice, "LONG stop loss should be below entry");
    assertTrue(decision.takeProfit > decision.entryPrice, "LONG take profit should be above entry");
}

static void testRiskRejectsMaxDailyLoss() {
    RiskConfig config;
    config.accountEquity = 10000.0;
    config.maxDailyLossPct = 0.03;

    RiskEngine engine(config);

    Signal signal;
    signal.type = SignalType::LONG;
    signal.reason = "Bullish momentum continuation";
    signal.confidence = 0.75;

    TradeDecision decision = engine.evaluate(candle(100, 102, 99, 100), signal, -301.0);

    assertTrue(decision.decision == DecisionType::REJECTED, "RiskEngine should reject after max daily loss");
    assertTrue(decision.reason.find("max daily loss") != std::string::npos, "Rejection reason should mention max daily loss");
}


static void testRiskRejectsPortfolioExposureLimit() {
    RiskConfig config;
    config.accountEquity = 10000.0;
    config.maxRiskPerTradePct = 0.01;
    config.maxPositionValuePct = 0.25;
    config.maxPortfolioExposurePct = 0.30;

    RiskEngine engine(config);

    Signal signal;
    signal.type = SignalType::LONG;
    signal.reason = "Bullish momentum continuation";
    signal.confidence = 0.75;

    std::unordered_map<std::string, double> symbolExposure;
    symbolExposure["AAPL"] = 1000.0;

    TradeDecision decision = engine.evaluate(
        candle(100, 102, 99, 100),
        signal,
        0.0,
        2900.0,
        symbolExposure
    );

    assertTrue(decision.decision == DecisionType::REJECTED, "RiskEngine should reject portfolio exposure breach");
    assertTrue(decision.reason.find("portfolio exposure") != std::string::npos, "Reason should mention portfolio exposure");
}

static void testSignalEngineGeneratesLongMomentum() {
    SignalEngine engine;
    std::vector<Candle> candles;

    double price = 100.0;
    for (int i = 0; i < 12; ++i) {
        double open = price;
        double close = open * 1.006;
        double high = close + 0.05;
        double low = open - 0.02;

        candles.push_back(candle(open, high, low, close));
        price = close;
    }

    Signal signal = engine.generate(candles, candles.size() - 1);

    assertTrue(signal.type == SignalType::LONG, "SignalEngine should detect bullish momentum");
}

static void testSignalEngineRejectsInsufficientCandles() {
    SignalEngine engine;
    std::vector<Candle> candles = {
        candle(100, 101, 99, 100),
        candle(100, 101, 99, 100.2)
    };

    Signal signal = engine.generate(candles, candles.size() - 1);

    assertTrue(signal.type == SignalType::NONE, "SignalEngine should reject insufficient candle history");
}

int main() {
    try {
        testRiskRejectsNoSignal();
        testRiskAcceptsValidLongSignal();
        testRiskRejectsMaxDailyLoss();
        testRiskRejectsPortfolioExposureLimit();
        testSignalEngineGeneratesLongMomentum();
        testSignalEngineRejectsInsufficientCandles();

        std::cout << "All TradeGuard Engine tests passed.\n";
        return 0;
    } catch (const std::exception& ex) {
        std::cerr << ex.what() << "\n";
        return 1;
    }
}
