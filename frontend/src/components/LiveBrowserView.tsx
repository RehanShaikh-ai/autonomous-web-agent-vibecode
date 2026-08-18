import React from 'react';
import {
  Globe,
  Lock,
  Code2,
  Maximize2,
  Sparkles,
} from 'lucide-react';
import { StepRecord } from '../types/schemas';

interface LiveBrowserViewProps {
  activeRecord: StepRecord | null;
  onOpenScreenshot: (path: string) => void;
  onOpenRawDom: (html: string, stepId: number) => void;
}

export const LiveBrowserView: React.FC<LiveBrowserViewProps> = ({
  activeRecord,
  onOpenScreenshot,
  onOpenRawDom,
}) => {
  if (!activeRecord) {
    return (
      <div
        className="glass-panel"
        style={{
          height: '100%',
          minHeight: '360px',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '0.75rem',
          color: 'var(--text-muted)',
          textAlign: 'center',
        }}
      >
        <Globe size={40} color="rgba(255,255,255,0.15)" />
        <p style={{ fontSize: '0.9rem' }}>Launch the agent or select a step to inspect the browser viewport.</p>
      </div>
    );
  }

  const { step, browserResult, processedPage, status } = activeRecord;
  const displayUrl = browserResult?.final_url || step.url || 'about:blank';

  return (
    <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      {/* Browser Chrome Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem',
          padding: '0.65rem 1rem',
          background: 'rgba(0, 0, 0, 0.4)',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-subtle)',
        }}
      >
        {/* Window controls */}
        <div style={{ display: 'flex', gap: '0.35rem' }}>
          <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#ef4444' }} />
          <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#f59e0b' }} />
          <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#10b981' }} />
        </div>

        {/* Address Bar */}
        <div
          style={{
            flex: 1,
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            background: 'rgba(255, 255, 255, 0.04)',
            padding: '0.35rem 0.85rem',
            borderRadius: 'var(--radius-sm)',
            fontSize: '0.78rem',
            fontFamily: 'var(--font-mono)',
            color: 'var(--text-secondary)',
            overflow: 'hidden',
          }}
        >
          <Lock size={12} color="var(--status-success)" />
          <span style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {displayUrl}
          </span>
        </div>

        {/* Quick Actions */}
        <div style={{ display: 'flex', gap: '0.35rem' }}>
          {browserResult?.raw_html && (
            <button
              className="btn btn-ghost"
              onClick={() => onOpenRawDom(browserResult.raw_html, step.step_id)}
              title="Inspect raw DOM HTML"
              style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem' }}
            >
              <Code2 size={14} />
              <span>DOM</span>
            </button>
          )}

          {browserResult?.screenshot_path && (
            <button
              className="btn btn-ghost"
              onClick={() => onOpenScreenshot(browserResult.screenshot_path!)}
              title="View full-resolution screenshot"
              style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem' }}
            >
              <Maximize2 size={14} />
              <span>Screenshot</span>
            </button>
          )}
        </div>
      </div>

      {/* Viewport Content Area */}
      <div
        style={{
          background: 'rgba(3, 7, 18, 0.95)',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-subtle)',
          padding: '1.25rem',
          minHeight: '260px',
          display: 'flex',
          flexDirection: 'column',
          gap: '1rem',
        }}
      >
        {/* Step telemetry header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span className="badge badge-cyan">Step {step.step_id}</span>
            <span style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-primary)' }}>
              {step.description}
            </span>
          </div>
          <span className={`badge badge-${status === 'success' ? 'success' : status === 'running' ? 'cyan' : 'warning'}`}>
            Status: {status.toUpperCase()}
          </span>
        </div>

        {/* Live / Cleaned text view */}
        {processedPage?.cleaned_markdown ? (
          <div
            style={{
              background: 'rgba(255, 255, 255, 0.02)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-sm)',
              padding: '1rem',
              fontSize: '0.85rem',
              color: 'var(--text-secondary)',
              maxHeight: '200px',
              overflowY: 'auto',
              whiteSpace: 'pre-wrap',
            }}
          >
            {processedPage.cleaned_markdown}
          </div>
        ) : browserResult?.raw_html ? (
          <div
            style={{
              background: 'rgba(255, 255, 255, 0.02)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-sm)',
              padding: '0.85rem',
              fontSize: '0.75rem',
              fontFamily: 'var(--font-mono)',
              color: 'var(--text-muted)',
              maxHeight: '180px',
              overflowY: 'auto',
            }}
          >
            {browserResult.raw_html.substring(0, 500)}...
          </div>
        ) : (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '140px', color: 'var(--text-muted)' }}>
            <span>Waiting for browser telemetry capture...</span>
          </div>
        )}

        {/* Extracted Entities preview bar */}
        {processedPage?.entities && Object.keys(processedPage.entities).length > 0 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem', paddingTop: '0.75rem', borderTop: '1px solid var(--border-subtle)' }}>
            <span style={{ fontSize: '0.72rem', textTransform: 'uppercase', color: 'var(--accent-cyan)', fontWeight: 700 }}>
              <Sparkles size={11} style={{ display: 'inline', marginRight: '4px' }} /> Extracted Entities (Stage 3)
            </span>
            <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
              {Object.entries(processedPage.entities).map(([k, v]) => (
                <div
                  key={k}
                  style={{
                    padding: '0.3rem 0.65rem',
                    background: 'rgba(0, 242, 254, 0.08)',
                    border: '1px solid rgba(0, 242, 254, 0.2)',
                    borderRadius: 'var(--radius-sm)',
                    fontSize: '0.75rem',
                  }}
                >
                  <span style={{ color: 'var(--text-muted)' }}>{k}: </span>
                  <strong style={{ color: 'var(--accent-cyan)' }}>{String(v)}</strong>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
