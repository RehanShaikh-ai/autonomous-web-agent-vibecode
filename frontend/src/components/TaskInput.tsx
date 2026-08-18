import React, { useState } from 'react';
import { Search, Play, Sliders, Sparkles, Loader2 } from 'lucide-react';

interface TaskInputProps {
  onExecute: (query: string, maxSteps: number) => void;
  isExecuting: boolean;
}

const PRESET_QUERIES = [
  'Compare prices and stock of Kindle Paperwhite 16GB on Amazon vs Best Buy',
  'Find latest official prices and availability for Apple MacBook Pro 14" M3',
  'Search NVIDIA RTX 4090 pricing across major hardware retailers',
  'Compare Python FastAPI vs Go Gin performance benchmarks and latency',
];

export const TaskInput: React.FC<TaskInputProps> = ({ onExecute, isExecuting }) => {
  const [query, setQuery] = useState(
    'Compare prices and stock of Kindle Paperwhite 16GB on Amazon vs Best Buy'
  );
  const [maxSteps, setMaxSteps] = useState(4);
  const [showAdvanced, setShowAdvanced] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || isExecuting) return;
    onExecute(query.trim(), maxSteps);
  };

  return (
    <div className="glass-panel" style={{ padding: '1.75rem' }}>
      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        {/* Top Input Row */}
        <div style={{ display: 'flex', gap: '0.85rem', alignItems: 'center' }}>
          <div style={{ position: 'relative', flex: 1 }}>
            <div
              style={{
                position: 'absolute',
                left: '1.1rem',
                top: '50%',
                transform: 'translateY(-50%)',
                color: 'var(--accent-cyan)',
                pointerEvents: 'none',
                display: 'flex',
                alignItems: 'center',
              }}
            >
              <Search size={20} />
            </div>
            <input
              type="text"
              className="input-text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="What task or comparison should the autonomous agent execute on the live web?"
              disabled={isExecuting}
              style={{ paddingLeft: '3rem', fontSize: '1rem', height: '52px' }}
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            disabled={isExecuting || !query.trim()}
            style={{ height: '52px', padding: '0 1.75rem', fontSize: '0.95rem' }}
          >
            {isExecuting ? (
              <>
                <Loader2 size={18} className="animate-spin-slow" />
                <span>Browsing & Reasoning...</span>
              </>
            ) : (
              <>
                <Play size={18} fill="currentColor" />
                <span>Launch Agent</span>
              </>
            )}
          </button>
        </div>

        {/* Preset Queries */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', flexWrap: 'wrap' }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
            <Sparkles size={12} color="var(--accent-cyan)" /> Examples:
          </span>
          {PRESET_QUERIES.map((preset, idx) => (
            <button
              key={idx}
              type="button"
              className="btn btn-ghost"
              onClick={() => setQuery(preset)}
              disabled={isExecuting}
              style={{
                fontSize: '0.75rem',
                padding: '0.35rem 0.65rem',
                background: 'rgba(255, 255, 255, 0.03)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-sm)',
                textAlign: 'left',
              }}
            >
              {preset.length > 50 ? preset.substring(0, 48) + '...' : preset}
            </button>
          ))}
        </div>

        {/* Advanced Options Toggle */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '0.5rem', borderTop: '1px solid var(--border-subtle)' }}>
          <button
            type="button"
            className="btn btn-ghost"
            onClick={() => setShowAdvanced(!showAdvanced)}
            style={{ fontSize: '0.8rem', padding: '0.35rem 0.6rem' }}
          >
            <Sliders size={14} />
            <span>{showAdvanced ? 'Hide Advanced Options' : 'Execution Settings'}</span>
          </button>

          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            Max Browser Execution Steps: <strong style={{ color: 'var(--accent-cyan)' }}>{maxSteps}</strong>
          </span>
        </div>

        {/* Advanced Controls */}
        {showAdvanced && (
          <div
            style={{
              padding: '1rem',
              background: 'rgba(0, 0, 0, 0.25)',
              borderRadius: 'var(--radius-md)',
              display: 'flex',
              alignItems: 'center',
              gap: '2rem',
              flexWrap: 'wrap',
            }}
          >
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem', flex: 1, minWidth: '200px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Maximum Step Limit:</span>
                <span style={{ fontWeight: 600, color: 'var(--accent-cyan)' }}>{maxSteps} steps</span>
              </div>
              <input
                type="range"
                min="2"
                max="8"
                value={maxSteps}
                onChange={(e) => setMaxSteps(Number(e.target.value))}
                disabled={isExecuting}
                style={{ width: '100%', accentColor: 'var(--accent-cyan)' }}
              />
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
              <span className="badge badge-purple">Ad-Block Active</span>
              <span className="badge badge-cyan">Clean Markdown Parser</span>
            </div>
          </div>
        )}
      </form>
    </div>
  );
};
