import React, { useState } from 'react';
import {
  ShieldCheck,
  Award,
  AlertOctagon,
  Download,
  Copy,
  Check,
  ExternalLink,
  Table,
  FileCheck,
  Image as ImageIcon,
} from 'lucide-react';
import { FinalReport } from '../types/schemas';

interface VerificationDashboardProps {
  report: FinalReport;
  onOpenScreenshot: (path: string) => void;
}

export const VerificationDashboard: React.FC<VerificationDashboardProps> = ({
  report,
  onOpenScreenshot,
}) => {
  const [copied, setCopied] = useState(false);

  const confidencePct = Math.round(report.confidence_score * 100);
  const isHighConfidence = report.confidence_score >= 0.8;
  const isModerateConfidence = report.confidence_score >= 0.5 && report.confidence_score < 0.8;

  const confidenceColor = isHighConfidence
    ? 'var(--status-success)'
    : isModerateConfidence
    ? 'var(--status-warning)'
    : 'var(--status-error)';

  const handleCopy = () => {
    navigator.clipboard.writeText(
      `# Autonomous Web Agent Intelligence Report\n\n${report.summary}\n\nConfidence Score: ${confidencePct}%\nSources: ${report.sources
        .map((s) => s.url)
        .join(', ')}`
    );
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleExportJson = () => {
    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(report, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute('href', dataStr);
    downloadAnchor.setAttribute('download', `awa_report_${report.goal_id}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  return (
    <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Top Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
          <div
            style={{
              width: '36px',
              height: '36px',
              borderRadius: '10px',
              background: 'rgba(16, 185, 129, 0.15)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Award size={20} color="var(--status-success)" />
          </div>
          <div>
            <h3 style={{ fontSize: '1.15rem', color: 'var(--text-primary)' }}>
              Stage 5 Deliverable: Verified Intelligence Report
            </h3>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Cross-verified across multiple authoritative web sources
            </span>
          </div>
        </div>

        {/* Confidence Badge */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.75rem',
            padding: '0.5rem 1rem',
            borderRadius: 'var(--radius-md)',
            background: 'rgba(0, 0, 0, 0.35)',
            border: `1px solid ${confidenceColor}`,
          }}
        >
          <ShieldCheck size={20} color={confidenceColor} />
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span style={{ fontSize: '0.68rem', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 700 }}>
              Confidence Score
            </span>
            <span style={{ fontSize: '1.1rem', fontWeight: 800, color: confidenceColor }}>
              {confidencePct}% Agreement
            </span>
          </div>
        </div>
      </div>

      {/* Contradictions Alert */}
      {report.contradictions && report.contradictions.length > 0 && (
        <div
          style={{
            padding: '1rem 1.25rem',
            borderRadius: 'var(--radius-md)',
            background: 'rgba(239, 68, 68, 0.08)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            display: 'flex',
            alignItems: 'flex-start',
            gap: '0.75rem',
          }}
        >
          <AlertOctagon size={20} color="var(--status-error)" style={{ flexShrink: 0, marginTop: '2px' }} />
          <div>
            <h4 style={{ fontSize: '0.9rem', color: 'var(--status-error)' }}>Source Discrepancies Detected</h4>
            <ul style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginTop: '0.35rem', paddingLeft: '1.25rem' }}>
              {report.contradictions.map((c, i) => (
                <li key={i}>{c}</li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* Natural Language Summary Card */}
      <div
        style={{
          background: 'rgba(255, 255, 255, 0.03)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-md)',
          padding: '1.25rem',
          fontSize: '0.95rem',
          lineHeight: '1.6',
          color: 'var(--text-primary)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.5rem', color: 'var(--accent-cyan)', fontSize: '0.8rem', fontWeight: 700, textTransform: 'uppercase' }}>
          <FileCheck size={14} /> Executive Summary
        </div>
        <p>{report.summary}</p>
      </div>

      {/* Comparison Table */}
      {report.comparison_table && report.comparison_table.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--text-secondary)', fontSize: '0.85rem', fontWeight: 600 }}>
            <Table size={16} color="var(--accent-cyan)" /> Comparative Data Analysis
          </div>

          <div className="data-table-container">
            <table className="data-table">
              <thead>
                <tr>
                  {Object.keys(report.comparison_table[0]).map((key) => (
                    <th key={key} style={{ textTransform: 'capitalize' }}>
                      {key.replace(/_/g, ' ')}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {report.comparison_table.map((row, rowIdx) => (
                  <tr key={rowIdx}>
                    {Object.entries(row).map(([key, val], cellIdx) => (
                      <td key={cellIdx}>
                        {key === 'price' ? (
                          <strong style={{ color: 'var(--accent-cyan)', fontSize: '0.95rem' }}>
                            {String(val)}
                          </strong>
                        ) : key === 'stock' || key === 'availability' ? (
                          <span className="badge badge-success" style={{ fontSize: '0.7rem' }}>
                            {String(val)}
                          </span>
                        ) : (
                          String(val)
                        )}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Verified Sources Grid */}
      {report.sources && report.sources.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
            Verified Source Citations ({report.sources.length})
          </span>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '0.85rem' }}>
            {report.sources.map((src, i) => (
              <div
                key={i}
                style={{
                  padding: '0.85rem 1rem',
                  background: 'rgba(0, 0, 0, 0.3)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-md)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: '0.75rem',
                }}
              >
                <div style={{ display: 'flex', flexDirection: 'column', minWidth: 0 }}>
                  <span style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--accent-cyan)' }}>
                    {src.domain}
                  </span>
                  <a
                    href={src.url}
                    target="_blank"
                    rel="noreferrer"
                    style={{
                      fontSize: '0.75rem',
                      color: 'var(--text-muted)',
                      textDecoration: 'none',
                      whiteSpace: 'nowrap',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.25rem',
                    }}
                  >
                    {src.url} <ExternalLink size={11} />
                  </a>
                </div>

                <button
                  className="btn btn-ghost"
                  onClick={() => onOpenScreenshot(src.screenshot_path)}
                  title="View verification screenshot"
                  style={{ padding: '0.4rem 0.6rem', fontSize: '0.72rem', flexShrink: 0 }}
                >
                  <ImageIcon size={14} />
                  <span>Proof</span>
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Export Toolbar */}
      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', paddingTop: '1rem', borderTop: '1px solid var(--border-subtle)' }}>
        <button className="btn btn-secondary" onClick={handleCopy}>
          {copied ? <Check size={16} color="var(--status-success)" /> : <Copy size={16} />}
          <span>{copied ? 'Copied to Clipboard!' : 'Copy Summary'}</span>
        </button>

        <button className="btn btn-primary" onClick={handleExportJson}>
          <Download size={16} />
          <span>Export JSON</span>
        </button>
      </div>
    </div>
  );
};
