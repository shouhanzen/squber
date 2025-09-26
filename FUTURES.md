# 🎯 Squid Futures Market Feature

## Overview

Add futures trading capabilities to the Squber MCP server, allowing squid fishing captains to hedge price risk and processors to secure future supply. This feature integrates with the existing maritime database and MCP tools.

## Problem Statement

**Current Issues**:
- Squid prices are highly volatile and unpredictable
- Captains bear all price risk during fishing trips
- Processors struggle to secure consistent supply at stable prices
- No forward-looking price discovery mechanism
- Trip planning lacks price risk management tools

**Market Opportunity**:
- Enable risk management for $2B+ global squid industry
- Provide price transparency and forward-looking market signals
- Create new revenue streams for fishing industry participants
- Improve supply chain stability for processors and exporters

## Architecture Decision

**✅ Database Tables + MCP Tools Approach**

**Rationale**:
- ✅ **Data consistency** - futures prices relate to current market prices
- ✅ **Query efficiency** - JOIN futures with spot prices, catch reports, regulations
- ✅ **Unified analytics** - captains can see spot vs futures in one query
- ✅ **Simpler deployment** - no additional services to manage
- ✅ **Existing auth & transport** - leverage current HTTP/ngrok setup

**Alternative Considered**: External microservice
- ❌ **Complexity** - Additional deployment, auth, networking
- ❌ **Data silos** - Separate databases reduce analytical power
- ❌ **Latency** - Cross-service queries slower than SQL JOINs

## Database Schema Design

### New Tables (add to existing maritime.db)

#### 1. `futures_contracts`
```sql
CREATE TABLE futures_contracts (
    contract_id INTEGER PRIMARY KEY,
    symbol TEXT UNIQUE NOT NULL,           -- 'SQ-MAR25', 'SQ-JUN25'
    contract_type TEXT NOT NULL,           -- 'monthly', 'quarterly'
    delivery_month TEXT NOT NULL,          -- '2025-03', '2025-Q2'
    expiry_date DATE NOT NULL,
    contract_size_tons INTEGER NOT NULL,   -- 50 tons standard
    delivery_port_id INTEGER,              -- FK to ports (NULL = cash settled)
    grade TEXT NOT NULL,                   -- 'A', 'B', 'C'
    tick_size REAL NOT NULL,               -- 0.01 (1 cent)
    created_date DATE NOT NULL,
    status TEXT NOT NULL,                  -- 'active', 'expired', 'delivered'
    FOREIGN KEY (delivery_port_id) REFERENCES ports(port_id)
);
```

#### 2. `futures_prices`
```sql
CREATE TABLE futures_prices (
    price_id INTEGER PRIMARY KEY,
    contract_id INTEGER NOT NULL,
    trade_date DATE NOT NULL,
    open_price REAL,
    high_price REAL,
    low_price REAL,
    close_price REAL,
    settle_price REAL NOT NULL,            -- Daily settlement price
    volume INTEGER DEFAULT 0,              -- Contracts traded
    open_interest INTEGER DEFAULT 0,       -- Outstanding positions
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (contract_id) REFERENCES futures_contracts(contract_id),
    UNIQUE(contract_id, trade_date)
);
```

#### 3. `futures_positions`
```sql
CREATE TABLE futures_positions (
    position_id INTEGER PRIMARY KEY,
    vessel_id INTEGER NOT NULL,
    contract_id INTEGER NOT NULL,
    position_type TEXT NOT NULL,           -- 'long' (buy), 'short' (sell)
    quantity INTEGER NOT NULL,             -- Number of contracts
    entry_price REAL NOT NULL,
    entry_date DATE NOT NULL,
    exit_price REAL,
    exit_date DATE,
    status TEXT NOT NULL,                  -- 'open', 'closed', 'delivered'
    margin_requirement REAL,              -- Required margin
    unrealized_pnl REAL,                  -- Mark-to-market P&L
    realized_pnl REAL,                     -- Closed position P&L
    notes TEXT,
    FOREIGN KEY (vessel_id) REFERENCES vessels(vessel_id),
    FOREIGN KEY (contract_id) REFERENCES futures_contracts(contract_id)
);
```

#### 4. `futures_settlements`
```sql
CREATE TABLE futures_settlements (
    settlement_id INTEGER PRIMARY KEY,
    contract_id INTEGER NOT NULL,
    vessel_id INTEGER NOT NULL,
    settlement_type TEXT NOT NULL,         -- 'physical', 'cash'
    delivery_port_id INTEGER,              -- Actual delivery port
    delivery_date DATE,
    physical_quantity_tons REAL,           -- Actual delivery amount
    cash_settlement_amount REAL,           -- Cash settlement value
    final_price REAL NOT NULL,             -- Final settlement price
    grade_delivered TEXT,                  -- Actual grade delivered
    settlement_date DATE NOT NULL,
    FOREIGN KEY (contract_id) REFERENCES futures_contracts(contract_id),
    FOREIGN KEY (vessel_id) REFERENCES vessels(vessel_id),
    FOREIGN KEY (delivery_port_id) REFERENCES ports(port_id)
);
```

## New MCP Tools

### 1. `futures_market_data(contract_symbol, days)`
**Purpose**: Get futures price data and analysis
**Parameters**:
- `contract_symbol`: e.g., "SQ-MAR25" or "ALL"
- `days`: Historical days to analyze (default: 30)

**Returns**: JSON with price charts, volume, open interest, volatility

### 2. `futures_hedge_advisor(vessel_name, expected_catch_tons, target_month)`
**Purpose**: Recommend hedging strategies for planned trips
**Parameters**:
- `vessel_name`: Captain's vessel
- `expected_catch_tons`: Anticipated catch size
- `target_month`: Expected landing month

**Returns**: Hedge recommendations, risk analysis, contract suggestions

### 3. `futures_contract_explorer(delivery_month, port_code)`
**Purpose**: Browse available contracts
**Parameters**:
- `delivery_month`: e.g., "2025-03" or "ALL"
- `port_code`: Delivery port filter (optional)

**Returns**: Available contracts, specifications, current prices

### 4. `futures_position_tracker(vessel_name)`
**Purpose**: Track current positions and P&L
**Parameters**:
- `vessel_name`: Captain's vessel

**Returns**: Open positions, unrealized P&L, margin requirements

### 5. `futures_basis_analysis(port_code, contract_symbol)`
**Purpose**: Analyze basis (futures - spot price difference)
**Parameters**:
- `port_code`: Local port for spot prices
- `contract_symbol`: Futures contract

**Returns**: Historical basis, convergence patterns, arbitrage opportunities

## Integration with Existing Tools

### Enhanced `get_market_report()`
**New Additions**:
- Futures vs spot price comparisons
- Basis analysis for each port
- Forward curve visualization
- Hedging opportunity alerts

### Enhanced `trip_advisor()`
**New Additions**:
- Price risk assessment for planned trips
- Hedging recommendations based on trip timing
- Contract delivery coordination
- Market timing suggestions with futures signals

### Enhanced `query_data()`
**New Capabilities**:
- JOIN futures and spot market tables
- Complex risk analysis queries
- Portfolio optimization queries
- Historical basis analysis

## Use Cases & User Stories

### Captain Use Cases
1. **Hedge Price Risk**: "I'm planning a 3-week trip in March. How do I protect against price drops?"
2. **Market Timing**: "Should I delay my trip based on futures prices?"
3. **Position Monitoring**: "What's my current P&L on my futures positions?"

### Processor Use Cases
1. **Supply Security**: "Lock in 500 tons of Grade A squid for Q2 processing"
2. **Inventory Planning**: "What's the forward price curve for planning production?"
3. **Basis Trading**: "Arbitrage opportunities between different delivery ports?"

### Market Maker Use Cases
1. **Liquidity Provision**: "Provide bid/ask spreads across all active contracts"
2. **Risk Management**: "Monitor aggregate open interest and margin requirements"

## Implementation Phases

### Phase 1: Core Infrastructure (Week 1)
- [ ] Add futures tables to maritime.db
- [ ] Create sample futures data (10 contracts, 90 days history)
- [ ] Implement `futures_contract_explorer` tool
- [ ] Basic futures price queries

### Phase 2: Market Data & Analysis (Week 2)
- [ ] Implement `futures_market_data` tool
- [ ] Add price chart and volatility analysis
- [ ] Implement `futures_basis_analysis` tool
- [ ] Integrate futures data into `get_market_report`

### Phase 3: Position Management (Week 3)
- [ ] Implement `futures_position_tracker` tool
- [ ] Add P&L calculations and margin tracking
- [ ] Position entry/exit functionality
- [ ] Risk alerts and notifications

### Phase 4: Hedging Intelligence (Week 4)
- [ ] Implement `futures_hedge_advisor` tool
- [ ] Advanced risk analysis and optimization
- [ ] Integration with `trip_advisor`
- [ ] Settlement and delivery tracking

## Risk Considerations

### Technical Risks
- **Data Complexity**: Futures calculations more complex than spot prices
- **Performance**: Large datasets may slow queries
- **Real-time**: Futures need frequent price updates

### Business Risks
- **Regulatory**: Futures trading heavily regulated
- **Liquidity**: New market may lack trading volume
- **Education**: Captains need training on derivatives

### Mitigation Strategies
- Start with simulated trading environment
- Partner with existing commodity exchanges
- Provide educational content and tutorials
- Implement position limits and risk controls

## Success Metrics

### Usage Metrics
- Number of active futures positions
- Daily query volume for futures tools
- Captain engagement with hedging recommendations

### Business Impact
- Reduction in captain price risk exposure
- Improved trip planning decision accuracy
- Increased supply chain efficiency for processors

### Market Development
- Contract trading volume growth
- Basis convergence efficiency
- Market maker participation

## Technical Notes

### Database Indexing
```sql
-- Performance indexes
CREATE INDEX idx_futures_prices_contract_date ON futures_prices(contract_id, trade_date);
CREATE INDEX idx_positions_vessel_status ON futures_positions(vessel_id, status);
CREATE INDEX idx_contracts_expiry ON futures_contracts(expiry_date);
```

### Sample Contract Symbols
- `SQ-JAN25` - January 2025 Market Squid
- `SQ-Q1-25` - Q1 2025 Quarterly Contract
- `SQ-MAR25-MNT` - March 2025, Monterey Delivery
- `SQ-APR25-CASH` - April 2025, Cash Settled

### Integration Points
- Futures prices feed into existing `market_prices` analysis
- Vessel performance data informs hedging recommendations
- Regulatory data affects contract specifications
- Demand signals influence futures curve shape

---

*This document serves as the technical specification for implementing squid futures trading capabilities in the Squber MCP server. Implementation should follow existing code patterns and maintain compatibility with current tools.*