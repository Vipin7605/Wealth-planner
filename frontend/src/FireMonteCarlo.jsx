import React, {useEffect, useMemo, useState} from 'react';
import {ResponsiveContainer, ComposedChart, Area, Line, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine} from 'recharts';
import {Loader2} from 'lucide-react';
import {api} from './lib/api.js';
import {money} from './lib/format.js';

const SCENARIOS = [['lean', 'Lean FIRE'], ['normal', 'Normal FIRE'], ['fat', 'Fat FIRE']];
const percent = (value) => `${Math.round(value * 100)}%`;
const tone = (probability) => (probability >= 0.85 ? 'good' : probability >= 0.6 ? 'caution' : 'risk');

function verdict(result) {
  const {survival_probability: p, assumptions, median_depletion_age: depletion} = result;
  if (p >= 0.85) return `In most simulated futures your investments last beyond age ${assumptions.end_age}.`;
  const base = p >= 0.6
    ? 'Your plan works in many futures but stays exposed to a poor run of returns early in retirement.'
    : `In a large share of simulated futures the money runs out before age ${assumptions.end_age}.`;
  const when = depletion ? ` Where it did run out, that typically happened around age ${Math.round(depletion)}.` : '';
  return `${base}${when} Saving more, retiring later or planning lower spending would each improve the odds.`;
}

function BandTooltip({active, payload, label, real}) {
  if (!active || !payload?.length) return null;
  const row = payload[0].payload;
  return (
    <div className="mc-tooltip" role="status">
      <strong>Age {label}</strong>
      {[['90th percentile', row.p90], ['Median', row.p50], ['10th percentile', row.p10]].map(([name, value]) => (
        <div key={name}><span>{name}</span><b>{money(value, true)}</b></div>
      ))}
      <small>{real ? 'Today’s money' : 'Future rupees'}</small>
    </div>
  );
}

export default function FireMonteCarlo({state, options, onOptions}) {
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [real, setReal] = useState(false);
  const draftKey = JSON.stringify(state);
  const optionKey = JSON.stringify(options);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(''); // clear any stale error from a previous, now-superseded input immediately
    const timer = setTimeout(async () => {
      try {
        const body = {state, options: {scenario: options.scenario, end_age: Number(options.end_age), simulations: 2000,
          volatility: options.volatility === '' ? null : Number(options.volatility)}};
        const data = await api('/monte-carlo', {method: 'POST', body: JSON.stringify(body), signal: controller.signal});
        setResult(data);
        setError('');
      } catch (e) {
        if (e.name !== 'AbortError') setError(e.message);
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }, 350);
    return () => { clearTimeout(timer); controller.abort(); };
  }, [draftKey, optionKey]);

  const chart = useMemo(() => {
    if (!result) return [];
    const start = result.timeline[0].age;
    const inflation = 1 + result.assumptions.inflation_pct / 100;
    return result.timeline.map((t) => {
      const f = real ? inflation ** (t.age - start) : 1;
      const [p10, p25, p50, p75, p90] = [t.p10, t.p25, t.p50, t.p75, t.p90].map((v) => v / f);
      return {age: t.age, p10, p25, p50, p75, p90, base: p10, lower: p25 - p10, inner: p75 - p25, upper: p90 - p75};
    });
  }, [result, real]);

  const setOption = (key, value) => onOptions({...options, [key]: value});
  const a = result?.assumptions;
  const level = result ? tone(result.survival_probability) : 'good';

  return (
    <section className="health-panel mc-panel" aria-busy={loading}>
      <div className="between">
        <div>
          <span className="health-kicker">STRESS TEST · MARKET VOLATILITY</span>
          <h2>How likely is your plan to survive real markets?</h2>
        </div>
        <span className="pill">{result ? `${result.simulations.toLocaleString('en-IN')} simulated futures` : 'Monte Carlo'}</span>
      </div>
      <p className="health-footnote">
        The projection above assumes the same return every year. Real returns bounce around, and a bad start to retirement
        hurts far more than a bad end. This runs thousands of possible futures, then withdraws your planned spending
        (rising with inflation) until the chosen age.
      </p>

      <div className="form-grid mc-controls">
        <label className="field"><span>Lifestyle to test</span>
          <select value={options.scenario} onChange={(e) => setOption('scenario', e.target.value)}>
            {SCENARIOS.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select>
        </label>
        <label className="field"><span>Annual market volatility (%)</span>
          <input type="number" min="0" max="40" step="0.5" placeholder={a ? `Default ${a.volatility_pct} for your risk level` : 'Default by risk level'}
            value={options.volatility} onChange={(e) => setOption('volatility', e.target.value)}/>
          <small>Typical diversified mixes range from about 8% (cautious) to 16% (equity-heavy).</small>
        </label>
        <label className="field"><span>Plan until age</span>
          <input type="number" min="50" max="110" step="1" value={options.end_age} required
            onChange={(e) => setOption('end_age', e.target.value === '' ? '' : Number(e.target.value))}/>
        </label>
      </div>

      {error && <div className="error" role="alert">{error}</div>}
      {!result && !error && <div className="loading"><Loader2 className="spin"/> Running simulations…</div>}

      {result && (
        <div className={loading ? 'mc-result mc-stale' : 'mc-result'} aria-live="polite">
          <div className="metrics three">
            <div className="metric">
              <span className="metric-label">Chance your money lasts to {a.end_age}</span>
              <strong className={`tone-${level}`}>{percent(result.survival_probability)}</strong>
              <small>At {money(result.planned_monthly_spending)}/month in today’s money ({result.scenario})</small>
            </div>
            <div className="metric">
              <span className="metric-label">Chance of reaching the {result.scenario} target</span>
              <strong className={`tone-${tone(result.reach_target_probability)}`}>{percent(result.reach_target_probability)}</strong>
              <small>Target {money(result.target_at_retirement, true)} by age {a.retirement_age}</small>
            </div>
            <div className="metric">
              <span className="metric-label">Spending that works 9 times in 10</span>
              <strong>{result.safe_monthly_spending > 0 ? money(result.safe_monthly_spending) : '—'}</strong>
              <small>Per month in today’s money · you plan {money(result.planned_monthly_spending)}</small>
            </div>
          </div>
          <p className="mc-verdict">{verdict(result)}</p>

          <div className="between mc-chart-head">
            <h3>Range of outcomes by age</h3>
            <select aria-label="Chart currency basis" value={real ? 'real' : 'nominal'} onChange={(e) => setReal(e.target.value === 'real')}>
              <option value="nominal">Future rupees</option>
              <option value="real">Today’s money</option>
            </select>
          </div>
          <div style={{height: 320, width: '100%'}} role="img"
            aria-label={`Fan chart of projected investments by age. Median at retirement ${money(result.at_retirement.p50, true)}; 10th to 90th percentile range ${money(result.at_retirement.p10, true)} to ${money(result.at_retirement.p90, true)}.`}>
            <ResponsiveContainer>
              <ComposedChart data={chart} margin={{top: 15, right: 12, left: 12, bottom: 5}}>
                <CartesianGrid stroke="#2a3c48" vertical={false} strokeDasharray="3 5"/>
                <XAxis dataKey="age" tick={{fill: '#93a3b5', fontSize: 11}} tickFormatter={(x) => `Age ${x}`} minTickGap={35}/>
                <YAxis tick={{fill: '#93a3b5', fontSize: 11}} tickFormatter={(x) => money(x, true)} width={80} domain={[0, 'auto']}/>
                <Tooltip content={<BandTooltip real={real}/>}/>
                <Area isAnimationActive={false} stackId="band" dataKey="base" stroke="none" fill="transparent" legendType="none"/>
                <Area isAnimationActive={false} stackId="band" dataKey="lower" stroke="none" fill="#7ee2ad" fillOpacity={0.13}/>
                <Area isAnimationActive={false} stackId="band" dataKey="inner" stroke="none" fill="#7ee2ad" fillOpacity={0.3}/>
                <Area isAnimationActive={false} stackId="band" dataKey="upper" stroke="none" fill="#7ee2ad" fillOpacity={0.13}/>
                <Line isAnimationActive={false} dataKey="p50" stroke="#7ee2ad" strokeWidth={3} dot={false}/>
                <ReferenceLine x={a.retirement_age} stroke="#b9a4f3" strokeDasharray="6 4" label={{value: 'Retire', fill: '#b9a4f3', fontSize: 11, position: 'insideTopRight'}}/>
              </ComposedChart>
            </ResponsiveContainer>
          </div>
          <div className="chart-footer mc-legend">
            <span><i className="dot"/> Median</span>
            <span><i className="dot mc-band-inner"/> Middle 50% of outcomes</span>
            <span><i className="dot mc-band-outer"/> 10th–90th percentile</span>
          </div>

          <div className="budget-ledger">
            {[['Unlucky path (10th percentile)', result.at_retirement.p10], ['Typical path (median)', result.at_retirement.p50],
              ['Lucky path (90th percentile)', result.at_retirement.p90], ['Straight-line projection above', result.deterministic_at_retirement]].map(([label, value]) => (
              <div key={label}><span>{label}</span><strong>{money(value, true)}</strong></div>
            ))}
          </div>
          <p className="health-footnote">
            Fund at age {a.retirement_age}, in future rupees. The typical path sits below the straight-line figure because
            losses hurt more than equal gains help (“volatility drag”); the average of all paths still matches your assumed
            {' '}{a.expected_return_pct}% return.
          </p>

          <details>
            <summary>See the numbers behind the chart</summary>
            <div className="table-scroll" style={{maxHeight: 260}}>
              <table>
                <thead><tr><th>Age</th><th>10th percentile</th><th>Median</th><th>90th percentile</th></tr></thead>
                <tbody>{chart.map((row) => (
                  <tr key={row.age}><td>{row.age}</td><td>{money(row.p10)}</td><td>{money(row.p50)}</td><td>{money(row.p90)}</td></tr>
                ))}</tbody>
              </table>
            </div>
          </details>

          {result.warnings.map((w, i) => <div className="note warning" key={i}>{w}</div>)}
          <p className="health-footnote">
            Assumes {a.expected_return_pct}% expected return with {a.volatility_pct}% volatility, {a.inflation_pct}% inflation,
            withdrawals at the start of each month, fixed contributions of {money(a.monthly_contribution)}/month until retirement.
            {' '}{result.note} Many planners look for roughly 80–90% or higher; treat that as a rough guide, not a rule.
          </p>
        </div>
      )}
    </section>
  );
}
