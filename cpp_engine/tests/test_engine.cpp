#include "RiskEngine.hpp"
#include "SignalEngine.hpp"
#include "CandleBuilder.hpp"
#include "ConfigLoader.hpp"
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

static Candle candle(double open, double high, double low, double close, double volume = 1200.0) {
    return Candle{
        "2026-01-02T09:30:00",
        "AAPL",
        open,
        high,
        low,
        close,
        volume
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
    assertTrue(decision.reasonCode == DecisionReasonCode::NO_SIGNAL, "RiskEngine should set NO_SIGNAL reason code");
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
    signal.reason = "Bullish setup";
    signal.confidence = 0.75;

    TradeDecision decision = engine.evaluate(candle(100, 102, 99, 100), signal, 0.0);

    assertTrue(decision.decision == DecisionType::ACCEPTED, "RiskEngine should accept valid LONG signal");
    assertTrue(decision.reasonCode == DecisionReasonCode::TRADE_ACCEPTED, "Accepted trade should use TRADE_ACCEPTED reason code");
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
    signal.reason = "Bullish setup";

    TradeDecision decision = engine.evaluate(candle(100, 102, 99, 100), signal, -301.0);

    assertTrue(decision.decision == DecisionType::REJECTED, "RiskEngine should reject after max daily loss");
    assertTrue(decision.reasonCode == DecisionReasonCode::MAX_DAILY_LOSS, "Reason code should be MAX_DAILY_LOSS");
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
    signal.reason = "Bullish setup";

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
    assertTrue(decision.reasonCode == DecisionReasonCode::PORTFOLIO_EXPOSURE_LIMIT, "Reason code should be PORTFOLIO_EXPOSURE_LIMIT");
}

static void testRiskRejectsSymbolExposureLimit() {
    RiskConfig config;
    config.accountEquity = 10000.0;
    config.maxRiskPerTradePct = 0.01;
    config.maxPositionValuePct = 0.25;
    config.maxSymbolExposurePct = 0.30;

    RiskEngine engine(config);

    Signal signal;
    signal.type = SignalType::LONG;
    signal.reason = "Bullish setup";

    std::unordered_map<std::string, double> symbolExposure;
    symbolExposure["AAPL"] = 2900.0;

    TradeDecision decision = engine.evaluate(
        candle(100, 102, 99, 100),
        signal,
        0.0,
        0.0,
        symbolExposure
    );

    assertTrue(decision.decision == DecisionType::REJECTED, "RiskEngine should reject symbol exposure breach");
    assertTrue(decision.reasonCode == DecisionReasonCode::SYMBOL_EXPOSURE_LIMIT, "Reason code should be SYMBOL_EXPOSURE_LIMIT");
}

static void testSignalEngineGeneratesLongMomentum() {
    SignalEngine engine;
    std::vector<Candle> candles;

    double price = 100.0;
    for (int i = 0; i < 16; ++i) {
        double open = price;
        double close = open * 1.006;
        double high = close + 0.05;
        double low = open - 0.02;
        candles.push_back(candle(open, high, low, close, 1500.0));
        price = close;
    }

    Signal signal = engine.generate(candles, candles.size() - 1);

    assertTrue(signal.type == SignalType::LONG, "SignalEngine should detect confirmed bullish momentum");
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

static void testCandleBuilderBuildsMultiSymbolCandles() {
    std::vector<Tick> ticks;
    for (int i = 0; i < 20; ++i) {
        ticks.push_back(Tick{"2026-01-02T09:30:" + std::to_string(i), "AAPL", 100.0 + i, 1000.0});
        ticks.push_back(Tick{"2026-01-02T09:30:" + std::to_string(i), "MSFT", 200.0 + i, 1000.0});
    }

    CandleBuilder builder(10);
    auto candles = builder.build(ticks);

    assertTrue(candles.size() == 4, "CandleBuilder should create two candles per symbol");
    assertTrue(candles[0].symbol == "AAPL", "Candles should be grouped by symbol");
}

static void testConfigLoaderLoadsRiskConfig() {
    RiskConfig config = ConfigLoader::loadRiskConfig("config/risk_config.json");

    assertTrue(config.accountEquity > 0, "ConfigLoader should load account equity");
    assertTrue(config.maxPortfolioExposurePct > 0, "ConfigLoader should load max portfolio exposure");
}

int main() {
    try {
        testRiskRejectsNoSignal();
        testRiskAcceptsValidLongSignal();
        testRiskRejectsMaxDailyLoss();
        testRiskRejectsPortfolioExposureLimit();
        testRiskRejectsSymbolExposureLimit();
        testSignalEngineGeneratesLongMomentum();
        testSignalEngineRejectsInsufficientCandles();
        testCandleBuilderBuildsMultiSymbolCandles();
        testConfigLoaderLoadsRiskConfig();

        std::cout << "All TradeGuard Engine tests passed.\n";
        return 0;
    } catch (const std::exception& ex) {
        std::cerr << ex.what() << "\n";
        return 1;
    }
}
