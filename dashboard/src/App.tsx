import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  Cpu,
  Database,
  GitBranch,
  LayoutDashboard,
  Search,
  ShieldCheck,
  TrendingUp,
  WalletCards,
} from "lucide-react";
import "./App.css";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";


function titleizeKey(key: string) {
  return key
    .replace(/_/g, " ")
    .replace(/pct/g, "%")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function formatConfigValue(key: string, value: number) {
  if (key.includes("pct")) {
    return `${(value * 100).toFixed(value < 0.01 ? 2 : 1)}%`;
  }

  if (key.includes("equity") || key.includes("commission")) {
    return money(value);
  }

  return String(value);
}

function getDecisionRows(decisions: DecisionRow[]) {
  return decisions.length ? decisions : [];
}

function getRejectionReasonData(decisions: DecisionRow[]) {
  const counts = new Map<string, number>();

  decisions.forEach((row) => {
    const decision = String(row.decision || "");
    const reason = String(row.reason_code || "UNKNOWN");

    if (decision === "REJECTED") {
      counts.set(reason, (counts.get(reason) || 0) + 1);
    }
  });

  return Array.from(counts.entries())
    .map(([reason, count]) => ({ reason, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 8);
}

function getLiveExposureRows(paperState: PaperState) {
  return Object.values(paperState.positions || {})
    .map((position) => ({
      symbol: String(position.symbol || ""),
      qty: Number(position.qty || 0),
      avg_price: Number(position.avg_price || 0),
      current_price: Number(position.current_price || 0),
      market_value: Number(position.market_value || 0),
      unrealized_pnl: Number(position.unrealized_pnl || 0),
    }))
    .sort((a, b) => b.market_value - a.market_value);
}


function formatSmallPct(value: unknown) {
  const num = Number(value ?? 0);
  if (Math.abs(num) < 1) return `${(num * 100).toFixed(2)}%`;
  return `${num.toFixed(2)}%`;
}

function formatDateTime(value: unknown) {
  if (!value) return "Waiting...";

  const raw = String(value);
  const date = new Date(raw);

  if (Number.isNaN(date.getTime())) {
    return raw.replace("T", " ").slice(0, 19);
  }

  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(date);
}


type Page = "overview" | "risk" | "strategy" | "trades" | "system";

type Summary = {
  total_decisions: number;
  accepted_trades: number;
  rejected_setups: number;
  executed_trades: number;
  ending_equity: number;
  total_pnl: number;
  win_rate: number;
  average_pnl: number;
  best_trade: number;
  worst_trade: number;
  max_drawdown: number;
};

type DecisionRow = {
  timestamp: string;
  symbol: string;
  decision: string;
  reason_code: string;
  signal: string;
  notional_value: number;
  entry_price: number;
  quantity: number;
};

type TradeRow = {
  timestamp: string;
  symbol: string;
  side: string;
  entry_price: number;
  exit_price: number;
  quantity: number;
  pnl: number;
  exit_reason: string;
};

type OptimizationRow = {
  run?: string;
  total_pnl?: number;
  ending_equity?: number;
  win_rate?: number;
  risk_per_trade?: number;
  stop_loss?: number;
  take_profit?: number;
  max_drawdown?: number;
  trades?: number;
  score?: number;
};

type RiskData = {
  config: Record<string, number>;
  reason_counts: Record<string, number>;
  symbol_exposure: Record<string, number>;
  total_rejections: number;
};

type LiveStatus = {
  running: boolean;
  mode: string;
  broker: string;
  last_started_at: string | null;
  last_run_at: string | null;
};

type BrokerAccount = {
  simulated?: Record<string, unknown>;
  alpaca?: {
    adapter?: string;
    mode?: string;
    configured?: boolean;
    message?: string;
    account_number?: string;
    status?: string;
    currency?: string;
    cash?: number;
    portfolio_value?: number;
    buying_power?: number;
    equity?: number;
    paper?: boolean;
  };
};

type BrokerOrders = {
  adapter: string;
  configured: boolean;
  orders: Array<Record<string, unknown>>;
};

type BrokerPositions = {
  adapter: string;
  configured: boolean;
  positions: Array<Record<string, unknown>>;
};

type ExecutionLog = {
  entries: Array<Record<string, unknown>>;
};

type AutomationStatus = {
  enabled: boolean;
  interval_seconds: number;
  last_cycle_at: string | null;
  cycles_completed: number;
  last_result?: {
    ok?: boolean;
    stage?: string;
    message?: string;
    orders_submitted?: number;
    accepted_signals_found?: number;
  };
};

type MarketEngineState = {
  last_generated_at: string | null;
  cycle_id: number;
  symbols: string[];
  latest_prices: Record<string, number>;
  rows_generated: number;
};

type PaperState = {
  cash: number;
  equity: number;
  realized_pnl: number;
  unrealized_pnl: number;
  market_value: number;
  positions: Record<string, Record<string, unknown>>;
  orders: Array<Record<string, unknown>>;
  last_updated_at: string | null;
};





type MarketSnapshot = {
  configured: boolean;
  quotes: Array<{
    symbol: string;
    bid_price: number;
    ask_price: number;
    bid_size: number;
    ask_size: number;
    timestamp: string;
  }>;
  message?: string;
};



const fallbackSummary: Summary = {
  total_decisions: 0,
  accepted_trades: 0,
  rejected_setups: 0,
  executed_trades: 0,
  ending_equity: 10000,
  total_pnl: 0,
  win_rate: 0,
  average_pnl: 0,
  best_trade: 0,
  worst_trade: 0,
  max_drawdown: 0,
};



async function apiGet<T>(path: string, fallback: T): Promise<T> {
  try {
    const response = await fetch(`${API_BASE}${path}`);
    if (!response.ok) return fallback;
    return response.json();
  } catch {
    return fallback;
  }
}


function money(value: number | string) {
  const number = Number(value || 0);
  return number.toLocaleString(undefined, {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2,
  });
}

function percent(value: number | string) {
  return `${Number(value || 0).toFixed(2)}%`;
}


async function apiPost(path: string): Promise<void> {
  try {
    await fetch(`${API_BASE}${path}`, { method: "POST" });
  } catch (error) {
    console.error(`POST ${path} failed`, error);
  }
}

function App() {
  const [page, setPage] = useState<Page>("overview");
  const [summary, setSummary] = useState<Summary>(fallbackSummary);
  const [decisions, setDecisions] = useState<DecisionRow[]>([]);
  const [, setTrades] = useState<TradeRow[]>([]);
  const [optimization, setOptimization] = useState<OptimizationRow[]>([]);
  const [, setRisk] = useState<RiskData>({
    config: {},
    reason_counts: {},
    symbol_exposure: {},
    total_rejections: 0,
  });
  const [benchmark, setBenchmark] = useState("");
  const [brokerAccount, setBrokerAccount] = useState<BrokerAccount>({});
  const [, setBrokerOrders] = useState<BrokerOrders>({
    adapter: "AlpacaBrokerAdapter",
    configured: false,
    orders: [],
  });
  const [, setBrokerPositions] = useState<BrokerPositions>({
    adapter: "AlpacaBrokerAdapter",
    configured: false,
    positions: [],
  });
  const [executionLog, setExecutionLog] = useState<ExecutionLog>({
    entries: [],
  });
  const [automationStatus, setAutomationStatus] = useState<AutomationStatus>({
    enabled: false,
    interval_seconds: 10,
    last_cycle_at: null,
    cycles_completed: 0,
  });
  const [marketEngineState, setMarketEngineState] = useState<MarketEngineState>({
    last_generated_at: null,
    cycle_id: 0,
    symbols: [],
    latest_prices: {},
    rows_generated: 0,
  });
  const [paperState, setPaperState] = useState<PaperState>({
    cash: 100000,
    equity: 100000,
    realized_pnl: 0,
    unrealized_pnl: 0,
    market_value: 0,
    positions: {},
    orders: [],
    last_updated_at: null,
  });
  const [riskConfig, setRiskConfig] = useState<Record<string, number>>({});
  const [filters, setFilters] = useState({
    search: "",
    symbol: "",
    decision: "",
    reason: "",
  });
  const [marketSnapshot, setMarketSnapshot] = useState<MarketSnapshot>({
    configured: false,
    quotes: [],
  });
  const [liveStatus, setLiveStatus] = useState<LiveStatus>({
    running: false,
    mode: "SIMULATED_PAPER",
    broker: "SimulatedBrokerAdapter",
    last_started_at: null,
    last_run_at: null,
  });
  const [apiStatus, setApiStatus] = useState("Connecting");


  async function loadData() {
    const [
      summaryData,
      decisionsData,
      tradesData,
      optimizationData,
      benchmarkData,
      riskData,
      liveData,
      brokerAccountData,
      brokerOrdersData,
      marketSnapshotData,
      brokerPositionsData,
      executionLogData,
      automationStatusData,
      marketEngineData,
      paperStateData,
      configData,
    ] = await Promise.all([
      apiGet<Summary>("/api/summary", fallbackSummary),
      apiGet<DecisionRow[]>("/api/decisions", []),
      apiGet<TradeRow[]>("/api/trades", []),
      apiGet<OptimizationRow[]>("/api/optimization", []),
      apiGet<{ text: string }>("/api/benchmark", { text: "" }),
      apiGet<RiskData>("/api/risk", {
        config: {},
        reason_counts: {},
        symbol_exposure: {},
        total_rejections: 0,
      }),
      apiGet<LiveStatus>("/api/live/status", liveStatus),
      apiGet<BrokerAccount>("/api/broker/account", {}),
      apiGet<BrokerOrders>("/api/broker/orders", {
        adapter: "AlpacaBrokerAdapter",
        configured: false,
        orders: [],
      }),
      apiGet<MarketSnapshot>("/api/broker/market-snapshot", {
        configured: false,
        quotes: [],
      }),
      apiGet<BrokerPositions>("/api/broker/positions", {
        adapter: "AlpacaBrokerAdapter",
        configured: false,
        positions: [],
      }),
      apiGet<ExecutionLog>("/api/execution-log", {
        entries: [],
      }),
      apiGet<AutomationStatus>("/api/automation/status", {
        enabled: false,
        interval_seconds: 10,
        last_cycle_at: null,
        cycles_completed: 0,
      }),
      apiGet<MarketEngineState>("/api/market/status", {
        last_generated_at: null,
        cycle_id: 0,
        symbols: [],
        latest_prices: {},
        rows_generated: 0,
      }),
      apiGet<PaperState>("/api/paper/state", {
        cash: 100000,
        equity: 100000,
        realized_pnl: 0,
        unrealized_pnl: 0,
        market_value: 0,
        positions: {},
        orders: [],
        last_updated_at: null,
      }),
      apiGet<Record<string, number>>("/api/config", {}),
    ]);

    setSummary(summaryData);
    setDecisions(decisionsData);
    setTrades(tradesData);
    setOptimization(optimizationData);
    setBenchmark(benchmarkData.text);
    setRisk(riskData);
    setLiveStatus(liveData);
    setBrokerAccount(brokerAccountData);
    setBrokerOrders(brokerOrdersData);
    setMarketSnapshot(marketSnapshotData);
    setBrokerPositions(brokerPositionsData);
    setExecutionLog(executionLogData);
    setAutomationStatus(automationStatusData);
    setMarketEngineState(marketEngineData);
    setPaperState(paperStateData);
    setRiskConfig(configData);
    setApiStatus("Connected");
  }







  useEffect(() => {
    loadData().catch(() => setApiStatus("API offline"));
  }, []);

  useEffect(() => {
    const id = window.setInterval(() => {
      loadData().catch(() => setApiStatus("API offline"));
    }, 1000);

    return () => window.clearInterval(id);
  }, []);






  useEffect(() => {
    let mounted = true;

    const startDashboardSession = async () => {
      setApiStatus("Connected");
      setAutomationStatus((current) => ({
        ...current,
        enabled: true,
      }));

      await apiPost("/api/automation/start");

      if (mounted) {
        await loadData().catch(() => setApiStatus("API offline"));
      }

      // Fast burst refresh so the recruiter sees activity immediately after opening.
      const burstTimers = [250, 500, 900, 1300, 1800, 2500, 3500, 5000].map((delay) =>
        window.setTimeout(() => {
          if (mounted) {
            loadData().catch(() => setApiStatus("API offline"));
          }
        }, delay)
      );

      return () => burstTimers.forEach((timer) => window.clearTimeout(timer));
    };

    let cleanupBurst: void | (() => void);
    startDashboardSession().then((cleanup) => {
      cleanupBurst = cleanup;
    });

    const stopAutomation = () => {
      navigator.sendBeacon?.(`${API_BASE}/api/automation/stop`);
    };

    window.addEventListener("beforeunload", stopAutomation);
    window.addEventListener("pagehide", stopAutomation);

    return () => {
      mounted = false;
      if (cleanupBurst) cleanupBurst();
      window.removeEventListener("beforeunload", stopAutomation);
      window.removeEventListener("pagehide", stopAutomation);
      apiPost("/api/automation/stop");
    };
  }, []);

  const symbols = useMemo(() => {
    return Array.from(new Set(decisions.map((row) => row.symbol).filter(Boolean))).sort();
  }, [decisions]);

  const reasonCodes = useMemo(() => {
    return Array.from(new Set(decisions.map((row) => row.reason_code).filter(Boolean))).sort();
  }, [decisions]);

  const filteredDecisions = useMemo(() => {
    const query = filters.search.trim().toLowerCase();

    return decisions.filter((row) => {
      const matchesSymbol = !filters.symbol || row.symbol === filters.symbol;
      const matchesDecision = !filters.decision || row.decision === filters.decision;
      const matchesReason = !filters.reason || row.reason_code === filters.reason;

      const searchable = [
        row.timestamp,
        row.symbol,
        row.decision,
        row.reason_code,
        row.signal,
      ]
        .join(" ")
        .toLowerCase();

      const matchesSearch = !query || searchable.includes(query);

      return matchesSymbol && matchesDecision && matchesReason && matchesSearch;
    });
  }, [decisions, filters]);


  const topOptimization = optimization.filter((row) => row.run).slice(0, 10);

  const nav = [
    { id: "overview", label: "Overview", icon: <LayoutDashboard size={17} /> },
    { id: "risk", label: "Risk Center", icon: <ShieldCheck size={17} /> },
    { id: "strategy", label: "Strategy Lab", icon: <GitBranch size={17} /> },
    { id: "trades", label: "Trade Blotter", icon: <Database size={17} /> },
    { id: "system", label: "System", icon: <Cpu size={17} /> },
  ] as const;

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">TG</div>
          <div>
            <h1>TradeGuard</h1>
            <p>Trading risk platform</p>
          </div>
        </div>

        <nav className="nav">
          {nav.map((item) => (
            <button
              key={item.id}
              onClick={() => setPage(item.id)}
              className={page === item.id ? "active" : ""}
            >
              {item.icon}
              {item.label}
            </button>
          ))}
        </nav>

        <div className="broker-card">
          <p>Broker Mode</p>
          <strong>{liveStatus.mode}</strong>
          <span>{liveStatus.broker}</span>
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <div>
            <p className="eyebrow">C++20 · Python FastAPI · React TypeScript</p>
            <h2>{nav.find((item) => item.id === page)?.label}</h2>
          </div>

          <div className="actions">
            <span className="status">{apiStatus}</span>
 
          </div>
        </header>

        {page === "overview" && (
          <>
            <section className="hero live-overview">
              <div>
                <p className="section-label">Live paper trading</p>
                <h3>Live engine-driven paper trading operations.</h3>
                <p>
                  TradeGuard monitors the latest account, order, position, and execution data
                  through FastAPI. Accepted C++ engine signals are routed through the broker
                  adapter and submitted to Alpaca paper trading.
                </p>
              </div>

              <div className="hero-kpis centered-kpis">
                <div>
                  <span>Paper Equity</span>
                  <strong>{money(paperState.equity || 0)}</strong>
                </div>
                <div>
                  <span>Unrealized P/L</span>
                  <strong>{money(paperState.unrealized_pnl || 0)}</strong>
                </div>
              </div>
            </section>

            <section className="metrics live-metrics">
              <InfoCard
                label="Paper Cash"
                value={money(paperState.cash || 0)}
                icon={<WalletCards size={18} />}
              />
              <InfoCard
                label="Open Positions"
                value={Object.keys(paperState.positions || {}).length.toLocaleString()}
                icon={<TrendingUp size={18} />}
              />
              <InfoCard
                label="Paper Fills"
                value={(paperState.orders || []).length.toLocaleString()}
                icon={<Database size={18} />}
              />
              <InfoCard
                label="Execution Mode"
                value={brokerAccount.alpaca?.configured ? "Alpaca Paper" : "Offline"}
                icon={<ShieldCheck size={18} />}
              />
            </section>

            <section className="live-engine-panel">
              <div className="live-engine-header">
                <div>
                  <p>Live Engine Activity</p>
                  <h3>{automationStatus.enabled ? "Engine execution is active. The backend checks signals every 1 second and skips duplicate paper orders." : "Auto-execution is currently paused."}</h3>
                </div>
 
              </div>

              <div className="live-engine-grid">
                <div>
                  <span>Backend Cycles</span>
                  <strong>{automationStatus.cycles_completed}</strong>
                </div>
                <div>
                  <span>Market Cycle</span>
                  <strong>{marketEngineState.cycle_id}</strong>
                </div>
                <div>
                  <span>Rows Generated</span>
                  <strong>{marketEngineState.rows_generated.toLocaleString()}</strong>
                </div>
                <div>
                  <span>Signals Found</span>
                  <strong>{automationStatus.last_result?.accepted_signals_found ?? 0}</strong>
                </div>
                <div>
                  <span>Orders This Cycle</span>
                  <strong>{automationStatus.last_result?.orders_submitted ?? 0}</strong>
                </div>
                <div>
                  <span>Stage</span>
                  <strong>{automationStatus.last_result?.stage || "monitoring"}</strong>
                </div>
              </div>

              <div className="live-engine-footer">
                <span>Last cycle: {formatDateTime(automationStatus.last_cycle_at)}</span>
                <span>Last market input: {formatDateTime(marketEngineState.last_generated_at)}</span>
              </div>
            </section>

            <section className="section-divider">
              <div>
                <p>Broker State</p>
                <h3>Orders, positions, quotes, and execution records from the connected paper account.</h3>
              </div>
              <span>Updates when broker state changes</span>
            </section>

            <section className="grid two">
              <TableCard title="Latest TradeGuard Paper Fills" subtitle="Internal paper fills generated from accepted engine signals.">
                <PaperOrdersTable rows={(paperState.orders || []).slice(0, 5)} />
              </TableCard>

              <TableCard title="TradeGuard Paper Positions" subtitle="Internal paper positions filled by engine-driven execution.">
                <PaperPositionsTable rows={Object.values(paperState.positions || {}).slice(0, 5)} />
              </TableCard>
            </section>

            <section className="panel">
              <div className="panel-heading centered">
                <h3>Generated Engine Market Input</h3>
                <p>Fresh tick data regenerated from broker quote snapshots before each engine cycle.</p>
              </div>

              <div className="generated-market-grid">
                {Object.entries(marketEngineState.latest_prices).map(([symbol, price]) => (
                  <div key={symbol} className="generated-market-card">
                    <span>{symbol}</span>
                    <strong>{money(price)}</strong>
                  </div>
                ))}
              </div>
            </section>

            <section className="grid two">
              <TableCard title="Broker Quote Snapshot" subtitle="Latest quote snapshot returned by the broker market data feed.">
                <MarketSnapshotTable rows={marketSnapshot.quotes} />
              </TableCard>

              <TableCard title="Broker Execution Log" subtitle="Persisted broker execution and engine activity history.">
                <ExecutionLogTable rows={executionLog.entries.slice(0, 5)} />
              </TableCard>
            </section>
          </>
        )}

        {page === "risk" && (
          <>
            <section className="risk-hero">
              <div>
                <p className="section-label">Risk Center</p>
                <h3>Live portfolio exposure and engine rejection controls.</h3>
                <p>
                  Monitor current paper exposure, rejected trade reasons, and the active
                  risk configuration used by the C++ signal/risk engine.
                </p>
              </div>

              <div className="risk-health">
                <span>Risk Engine</span>
                <strong>{summary.max_drawdown < -10 ? "High Drawdown" : "Operating"}</strong>
              </div>
            </section>

            <section className="metrics live-metrics">
              <InfoCard
                label="Rejected Decisions"
                value={(summary.rejected_setups || 0).toLocaleString()}
                icon={<ShieldCheck size={18} />}
              />
              <InfoCard
                label="Accepted Trades"
                value={(summary.accepted_trades || 0).toLocaleString()}
                icon={<TrendingUp size={18} />}
              />
              <InfoCard
                label="Live Exposure"
                value={money(paperState.market_value || 0)}
                icon={<WalletCards size={18} />}
              />
              <InfoCard
                label="Max Drawdown"
                value={percent(summary.max_drawdown || 0)}
                icon={<Activity size={18} />}
              />
            </section>

            <section className="grid two risk-grid">
              <TableCard
                title="Rejection Reason Codes"
                subtitle="Why the risk engine blocked potential trade decisions."
              >
                <RejectionReasonTable rows={getRejectionReasonData(getDecisionRows(decisions))} />
              </TableCard>

              <TableCard
                title="Live Symbol Exposure"
                subtitle="Current internal paper exposure by symbol."
              >
                <LiveExposureTable rows={getLiveExposureRows(paperState)} />
              </TableCard>
            </section>

            <section className="panel">
              <div className="panel-heading centered">
                <h3>Risk Policy Configuration</h3>
                <p>Live limits currently enforced by the C++ risk engine.</p>
              </div>

              <div className="config-grid professional-config">
                {Object.entries(riskConfig).map(([key, value]) => (
                  <div key={key} className="config-item">
                    <span>{titleizeKey(key)}</span>
                    <strong>{formatConfigValue(key, Number(value))}</strong>
                  </div>
                ))}
              </div>
            </section>
          </>
        )}

        {page === "strategy" && (
          <>
            <section className="strategy-hero-clean">
              <div className="strategy-hero-inner">
                <p className="section-label">Strategy Lab</p>
                <h3>Latest strategy optimization across risk, stop-loss, and take-profit settings.</h3>
                <p>
                  TradeGuard displays the latest optimization run, ranking parameter configurations
                  by return, win rate, drawdown, and overall strategy score.
                </p>
              </div>
            </section>

            <TableCard title="Optimization Results" subtitle="Top parameter configurations.">
              <OptimizationTable rows={topOptimization} />
            </TableCard>
          </>
        )}

        {page === "trades" && (
          <>
            <section className="trade-hero">
              <div>
                <p className="section-label">Trade Blotter</p>
                <h3>Live paper fills and engine decision history.</h3>
                <p>
                  Review internal TradeGuard fills, active paper positions, and the latest
                  accepted or rejected engine decisions.
                </p>
              </div>

              <div className="trade-hero-kpis">
                <div>
                  <span>Paper Fills</span>
                  <strong>{(paperState.orders || []).length.toLocaleString()}</strong>
                </div>
                <div>
                  <span>Open Positions</span>
                  <strong>{Object.keys(paperState.positions || {}).length.toLocaleString()}</strong>
                </div>
                <div>
                  <span>Unrealized P/L</span>
                  <strong className={(paperState.unrealized_pnl || 0) >= 0 ? "positive" : "negative"}>
                    {money(paperState.unrealized_pnl || 0)}
                  </strong>
                </div>
              </div>
            </section>

            <section className="trade-filters">
              <div className="search-box">
                <Search size={16} />
                <input
                  value={filters.search}
                  onChange={(event) => setFilters({ ...filters, search: event.target.value })}
                  placeholder="Search symbol, decision, reason, signal..."
                />
              </div>

              <select
                value={filters.symbol}
                onChange={(event) => setFilters({ ...filters, symbol: event.target.value })}
              >
                <option value="">All symbols</option>
                {symbols.map((symbol) => (
                  <option key={symbol} value={symbol}>
                    {symbol}
                  </option>
                ))}
              </select>

              <select
                value={filters.decision}
                onChange={(event) => setFilters({ ...filters, decision: event.target.value })}
              >
                <option value="">All decisions</option>
                <option value="ACCEPTED">Accepted</option>
                <option value="REJECTED">Rejected</option>
              </select>

              <select
                value={filters.reason}
                onChange={(event) => setFilters({ ...filters, reason: event.target.value })}
              >
                <option value="">All reason codes</option>
                {reasonCodes.map((reason) => (
                  <option key={reason} value={reason}>
                    {reason}
                  </option>
                ))}
              </select>

              <button
                className="secondary compact"
                onClick={() => setFilters({ search: "", symbol: "", decision: "", reason: "" })}
              >
                Clear
              </button>
            </section>

            <section className="panel">
              <div className="panel-heading centered">
                <h3>Latest TradeGuard Paper Fills</h3>
                <p>Internal paper fills generated from accepted engine signals.</p>
              </div>

              <PaperOrdersTable rows={(paperState.orders || []).slice(0, 20)} />
            </section>

            <section className="panel">
              <div className="panel-heading centered">
                <h3>Decision Log</h3>
                <p>Recent accepted and rejected trading decisions from the engine.</p>
              </div>

              <DecisionTable rows={filteredDecisions.slice(0, 30)} />
            </section>
          </>
        )}

        {page === "system" && (
          <>
            <section className="grid two">
              <InfoCard label="API Status" value={apiStatus} />
              <InfoCard label="Engine Mode" value={liveStatus.mode} />
            </section>

            <section className="panel">
              <div className="panel-heading centered">
                <Cpu size={18} />
                <h3>Benchmark Report</h3>
                <p>Runtime metrics generated by the C++ benchmark reporter.</p>
              </div>
              <pre>{benchmark || "No benchmark report available."}</pre>
            </section>
          </>
        )}
      </main>
    </div>
  );
}

function InfoCard({ label, value, icon }: { label: string; value: string; icon?: React.ReactNode }) {
  return (
    <article className="info-card">
      <div className="info-icon">{icon || <Activity size={18} />}</div>
      <p>{label}</p>
      <h3>{value}</h3>
    </article>
  );
}

function TableCard({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle: string;
  children: React.ReactNode;
}) {
  return (
    <section className="panel">
      <div className="panel-heading centered">
        <h3>{title}</h3>
        <p>{subtitle}</p>
      </div>
      <div className="table-wrap">{children}</div>
    </section>
  );
}

function EmptyState({ message }: { message: string }) {
  return (
    <div className="empty-state">
      <Database size={20} />
      <p>{message}</p>
    </div>
  );
}

function DecisionTable({ rows }: { rows: DecisionRow[] }) {
  return (
    <table>
      <thead>
        <tr>
          <th>Timestamp</th>
          <th>Symbol</th>
          <th>Decision</th>
          <th>Reason Code</th>
          <th>Signal</th>
          <th>Notional</th>
        </tr>
      </thead>
      <tbody>
        {rows.length === 0 && (
          <tr>
            <td colSpan={6}>
              <EmptyState message="No decision records match the current filters." />
            </td>
          </tr>
        )}

        {rows.map((row, index) => (
          <tr key={`${row.timestamp}-${row.symbol}-${index}`}>
            <td>{row.timestamp}</td>
            <td>{row.symbol}</td>
            <td>
              <span className={`badge ${row.decision.toLowerCase()}`}>
                {row.decision}
              </span>
            </td>
            <td>{row.reason_code}</td>
            <td>{row.signal}</td>
            <td>{money(row.notional_value)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function OptimizationTable({ rows }: { rows: OptimizationRow[] }) {
  return (
    <table>
      <thead>
        <tr>
          <th>Rank</th>
          <th>Run</th>
          <th>Total PnL</th>
          <th>Ending Equity</th>
          <th>Win Rate</th>
          <th>Max Drawdown</th>
          <th>Risk / Trade</th>
          <th>Stop Loss</th>
          <th>Take Profit</th>
          <th>Score</th>
        </tr>
      </thead>
      <tbody>
        {rows.length === 0 && (
          <tr>
            <td colSpan={10}>
              <EmptyState message="No optimization results available." />
            </td>
          </tr>
        )}

        {rows.map((row, index) => (
          <tr key={row.run || index}>
            <td>{index + 1}</td>
            <td>{row.run}</td>
            <td className={Number(row.total_pnl || 0) >= 0 ? "positive" : "negative"}>
              {money(row.total_pnl ?? 0)}
            </td>
            <td>{money(row.ending_equity ?? 0)}</td>
            <td>{percent(row.win_rate ?? 0)}</td>
            <td className="negative">{percent(row.max_drawdown ?? 0)}</td>
            <td>{formatSmallPct(row.risk_per_trade ?? 0)}</td>
            <td>{formatSmallPct(row.stop_loss ?? 0)}</td>
            <td>{formatSmallPct(row.take_profit ?? 0)}</td>
            <td>{String(row.score ?? "—")}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}


function MarketSnapshotTable({
  rows,
}: {
  rows: MarketSnapshot["quotes"];
}) {
  return (
    <table>
      <thead>
        <tr>
          <th>Symbol</th>
          <th>Bid</th>
          <th>Ask</th>
          <th>Bid Size</th>
          <th>Ask Size</th>
        </tr>
      </thead>
      <tbody>
        {rows.length === 0 && (
          <tr>
            <td colSpan={6}>
              <EmptyState message="No Alpaca market snapshot data available." />
            </td>
          </tr>
        )}

        {rows.map((row) => (
          <tr key={row.symbol}>
            <td>{row.symbol}</td>
            <td>{money(row.bid_price)}</td>
            <td>{money(row.ask_price)}</td>
            <td>{row.bid_size}</td>
            <td>{row.ask_size}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function ExecutionLogTable({
  rows,
}: {
  rows: Array<Record<string, unknown>>;
}) {
  return (
    <table>
      <thead>
        <tr>
          <th>Time</th>
          <th>Type</th>
          <th>Symbol</th>
          <th>Side</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        {rows.length === 0 && (
          <tr>
            <td colSpan={5}>
              <EmptyState message="No persisted execution log entries yet." />
            </td>
          </tr>
        )}

        {rows.map((row, index) => {
          const fill = (row.fill || {}) as Record<string, unknown>;
          return (
            <tr key={`${String(row.timestamp || "")}-${index}`}>
              <td>{formatDateTime(row.timestamp)}</td>
              <td>{String(row.type || "")}</td>
              <td>{String(fill.symbol || "")}</td>
              <td>{String(fill.side || "")}</td>
              <td>{String(fill.status || "").replace("OrderStatus.", "")}</td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}


function RejectionReasonTable({
  rows,
}: {
  rows: Array<{ reason: string; count: number }>;
}) {
  const total = rows.reduce((sum, row) => sum + row.count, 0) || 1;

  return (
    <div className="risk-list">
      {rows.length === 0 && <EmptyState message="No rejected decisions found." />}

      {rows.map((row) => {
        const share = (row.count / total) * 100;

        return (
          <div key={row.reason} className="risk-list-row">
            <div>
              <strong>{row.reason}</strong>
              <span>{row.count.toLocaleString()} decisions</span>
            </div>
            <div className="risk-bar-wrap">
              <div className="risk-bar" style={{ width: `${Math.max(share, 4)}%` }} />
            </div>
            <em>{share.toFixed(1)}%</em>
          </div>
        );
      })}
    </div>
  );
}

function LiveExposureTable({
  rows,
}: {
  rows: Array<{
    symbol: string;
    qty: number;
    avg_price: number;
    current_price: number;
    market_value: number;
    unrealized_pnl: number;
  }>;
}) {
  return (
    <table>
      <thead>
        <tr>
          <th>Symbol</th>
          <th>Qty</th>
          <th>Current</th>
          <th>Exposure</th>
          <th>Unrealized P/L</th>
        </tr>
      </thead>
      <tbody>
        {rows.length === 0 && (
          <tr>
            <td colSpan={5}>
              <EmptyState message="No live symbol exposure yet." />
            </td>
          </tr>
        )}

        {rows.map((row) => (
          <tr key={row.symbol}>
            <td>{row.symbol}</td>
            <td>{row.qty.toLocaleString()}</td>
            <td>{money(row.current_price)}</td>
            <td>{money(row.market_value)}</td>
            <td className={row.unrealized_pnl >= 0 ? "positive" : "negative"}>
              {money(row.unrealized_pnl)}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function PaperPositionsTable({
  rows,
}: {
  rows: Array<Record<string, unknown>>;
}) {
  return (
    <table>
      <thead>
        <tr>
          <th>Symbol</th>
          <th>Qty</th>
          <th>Avg Price</th>
          <th>Current</th>
          <th>Market Value</th>
          <th>Unrealized P/L</th>
        </tr>
      </thead>
      <tbody>
        {rows.length === 0 && (
          <tr>
            <td colSpan={6}>
              <EmptyState message="No internal paper positions yet." />
            </td>
          </tr>
        )}

        {rows.map((row, index) => (
          <tr key={`${String(row.symbol || "")}-${index}`}>
            <td>{String(row.symbol || "")}</td>
            <td>{String(row.qty || "")}</td>
            <td>{money(String(row.avg_price || 0))}</td>
            <td>{money(String(row.current_price || 0))}</td>
            <td>{money(String(row.market_value || 0))}</td>
            <td>{money(String(row.unrealized_pnl || 0))}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function PaperOrdersTable({
  rows,
}: {
  rows: Array<Record<string, unknown>>;
}) {
  return (
    <table>
      <thead>
        <tr>
          <th>Time</th>
          <th>Symbol</th>
          <th>Side</th>
          <th>Qty</th>
          <th>Fill</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        {rows.length === 0 && (
          <tr>
            <td colSpan={6}>
              <EmptyState message="No internal paper fills yet." />
            </td>
          </tr>
        )}

        {rows.map((row, index) => (
          <tr key={`${String(row.timestamp || "")}-${index}`}>
            <td>{formatDateTime(row.timestamp)}</td>
            <td>{String(row.symbol || "")}</td>
            <td>{String(row.side || "")}</td>
            <td>{String(row.qty || "")}</td>
            <td>{money(String(row.fill_price || 0))}</td>
            <td>{String(row.status || "")}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export default App;
