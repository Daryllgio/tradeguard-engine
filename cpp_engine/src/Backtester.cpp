#include "Backtester.hpp"
#include <algorithm>
#include <unordered_map>
#include <vector>

struct OpenPosition {
    std::string symbol;
    double notionalValue{};
    size_t exitIndex{};
};

Backtester::Backtester(RiskConfig config)
    : config_(config), riskEngine_(config) {
    equityCurve_.push_back(config_.accountEquity);
}

void Backtester::run(const std::vector<Candle>& candles) {
    double equity = config_.accountEquity;
    double realizedPnl = 0.0;
    double currentPortfolioExposure = 0.0;
    std::unordered_map<std::string, double> currentSymbolExposure;
    std::vector<OpenPosition> openPositions;

    for (size_t i = 0; i < candles.size(); ++i) {
        openPositions.erase(
            std::remove_if(openPositions.begin(), openPositions.end(), [&](const OpenPosition& pos) {
                if (pos.exitIndex <= i) {
                    currentPortfolioExposure -= pos.notionalValue;
                    currentSymbolExposure[pos.symbol] -= pos.notionalValue;

                    if (currentPortfolioExposure < 0) currentPortfolioExposure = 0;
                    if (currentSymbolExposure[pos.symbol] < 0) currentSymbolExposure[pos.symbol] = 0;

                    return true;
                }
                return false;
            }),
            openPositions.end()
        );

        Signal signal = signalEngine_.generate(candles, i);

        TradeDecision decision = riskEngine_.evaluate(
            candles[i],
            signal,
            realizedPnl,
            currentPortfolioExposure,
            currentSymbolExposure
        );

        decisions_.push_back(decision);

        if (decision.decision == DecisionType::ACCEPTED && i + 1 < candles.size()) {
            TradeResult result = simulateTrade(candles, i, decision);

            trades_.push_back(result);
            equity += result.pnl;
            realizedPnl += result.pnl;

            currentPortfolioExposure += decision.notionalValue;
            currentSymbolExposure[decision.symbol] += decision.notionalValue;

            openPositions.push_back(OpenPosition{
                decision.symbol,
                decision.notionalValue,
                result.exitIndex
            });

            equityCurve_.push_back(equity);
        }
    }
}

TradeResult Backtester::simulateTrade(const std::vector<Candle>& candles, size_t entryIndex, const TradeDecision& decision) const {
    TradeResult result;
    result.timestamp = decision.timestamp;
    result.symbol = decision.symbol;
    result.side = decision.signal;
    result.entryPrice = decision.entryPrice;
    result.quantity = decision.quantity;

    size_t maxExit = std::min(entryIndex + 18, candles.size() - 1);

    for (size_t i = entryIndex + 1; i <= maxExit; ++i) {
        const Candle& candle = candles[i];

        if (candle.symbol != decision.symbol) {
            continue;
        }

        if (decision.signal == SignalType::LONG) {
            if (candle.low <= decision.stopLoss) {
                result.exitPrice = decision.stopLoss;
                result.exitReason = "STOP_LOSS";
                result.exitIndex = i;
                result.pnl = (result.exitPrice - result.entryPrice) * result.quantity;
                return result;
            }

            if (candle.high >= decision.takeProfit) {
                result.exitPrice = decision.takeProfit;
                result.exitReason = "TAKE_PROFIT";
                result.exitIndex = i;
                result.pnl = (result.exitPrice - result.entryPrice) * result.quantity;
                return result;
            }
        }

        if (decision.signal == SignalType::SHORT) {
            if (candle.high >= decision.stopLoss) {
                result.exitPrice = decision.stopLoss;
                result.exitReason = "STOP_LOSS";
                result.exitIndex = i;
                result.pnl = (result.entryPrice - result.exitPrice) * result.quantity;
                return result;
            }

            if (candle.low <= decision.takeProfit) {
                result.exitPrice = decision.takeProfit;
                result.exitReason = "TAKE_PROFIT";
                result.exitIndex = i;
                result.pnl = (result.entryPrice - result.exitPrice) * result.quantity;
                return result;
            }
        }
    }

    const Candle& exitCandle = candles[maxExit];
    result.exitPrice = exitCandle.close;
    result.exitReason = "TIME_EXIT";
    result.exitIndex = maxExit;

    if (decision.signal == SignalType::LONG) {
        result.pnl = (result.exitPrice - result.entryPrice) * result.quantity;
    } else {
        result.pnl = (result.entryPrice - result.exitPrice) * result.quantity;
    }

    return result;
}

const std::vector<TradeDecision>& Backtester::decisions() const {
    return decisions_;
}

const std::vector<TradeResult>& Backtester::trades() const {
    return trades_;
}

const std::vector<double>& Backtester::equityCurve() const {
    return equityCurve_;
}
