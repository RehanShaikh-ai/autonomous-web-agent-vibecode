import React from 'react';
import { Activity, Globe, Cpu, RefreshCw, Sparkles } from 'lucide-react';
import { HealthResponse } from '../types/schemas';

interface HeaderProps {
  health: HealthResponse | null;
  onReset: () => void;
  isExecuting: boolean;
}

export const Header: React.FC<HeaderProps> = ({ health, onReset, isExecuting }) => {
  const isHealthy = health?.status === 'healthy' || health?.status === 'demo_mode';

  return (
    <header className="glass-panel" style={{ padding: '1rem 1.75rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
        {/* Left: Branding */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
          <div
            style={{
              width: '42px',
              height: '42px',
              borderRadius: '12px',
              background: 'linear-gradient(135deg, #00f2fe 0%, #6366f1 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 0 20px rgba(0, 242, 254, 0.4)',
            }}
          >
            <Sparkles size={22} color="#050b14" />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              <h1 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                Autonomous Web Agent
              </h1>
              <span className="badge badge-cyan" style={{ fontSize: '0.65rem' }}>
                v0.1.0-LIVE
              </span>
            </div>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Execution & Intelligence Dashboard • Owned by Member D (Frontend Developer)
            </p>
          </div>
        </div>

        {/* Right: Service Health & Reset */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
          {/* Health indicators */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'rgba(0,0,0,0.3)', padding: '0.35rem 0.75rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
              <Activity size={14} color="var(--accent-cyan)" />
              <span>Gateway:</span>
              <span style={{ color: isHealthy ? 'var(--status-success)' : 'var(--status-warning)', fontWeight: 600 }}>
                {health?.status || 'Active'}
              </span>
            </div>
            <span style={{ color: 'rgba(255,255,255,0.15)' }}>|</span>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
              <Globe size={14} color="#3b82f6" />
              <span>Playwright:</span>
              <span style={{ color: 'var(--status-success)', fontWeight: 600 }}>Ready</span>
            </div>
            <span style={{ color: 'rgba(255,255,255,0.15)' }}>|</span>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
              <Cpu size={14} color="#a855f7" />
              <span>LLM Reasoner:</span>
              <span style={{ color: 'var(--status-success)', fontWeight: 600 }}>Online</span>
            </div>
          </div>

          <button
            className="btn btn-secondary"
            onClick={onReset}
            disabled={isExecuting}
            title="Reset active execution session"
            style={{ padding: '0.5rem 0.85rem' }}
          >
            <RefreshCw size={14} className={isExecuting ? 'animate-spin-slow' : ''} />
            <span>Reset</span>
          </button>
        </div>
      </div>
    </header>
  );
};
