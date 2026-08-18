import React, { useState } from 'react';
import { X, Copy, Check, Code, Image as ImageIcon } from 'lucide-react';

interface ScreenshotModalProps {
  isOpen: boolean;
  screenshotPath: string | null;
  onClose: () => void;
}

export const ScreenshotModal: React.FC<ScreenshotModalProps> = ({
  isOpen,
  screenshotPath,
  onClose,
}) => {
  if (!isOpen || !screenshotPath) return null;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '850px' }}>
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1.25rem 1.5rem', borderBottom: '1px solid var(--border-subtle)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <ImageIcon size={18} color="var(--accent-cyan)" />
            <h3 style={{ fontSize: '1rem', color: 'var(--text-primary)' }}>Browser Viewport Screenshot</h3>
          </div>
          <button className="btn btn-ghost" onClick={onClose} style={{ padding: '0.35rem' }}>
            <X size={18} />
          </button>
        </div>

        {/* Body */}
        <div style={{ padding: '1.5rem', overflowY: 'auto', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem' }}>
          <div
            style={{
              width: '100%',
              minHeight: '320px',
              borderRadius: 'var(--radius-md)',
              background: 'rgba(0,0,0,0.5)',
              border: '1px solid var(--border-subtle)',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '2rem',
              textAlign: 'center',
              gap: '1rem',
            }}
          >
            <ImageIcon size={48} color="var(--accent-cyan)" />
            <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
              Screenshot Reference Path:
            </p>
            <code style={{ background: 'rgba(255,255,255,0.05)', padding: '0.4rem 0.85rem', borderRadius: 'var(--radius-sm)', color: 'var(--accent-cyan)', fontFamily: 'var(--font-mono)', fontSize: '0.85rem' }}>
              {screenshotPath}
            </code>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
              Saved by Member B Playwright Driver into artifacts storage
            </span>
          </div>
        </div>

        {/* Footer */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', padding: '1rem 1.5rem', borderTop: '1px solid var(--border-subtle)' }}>
          <button className="btn btn-secondary" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

interface RawDomModalProps {
  isOpen: boolean;
  rawHtml: string | null;
  stepId: number | null;
  onClose: () => void;
}

export const RawDomModal: React.FC<RawDomModalProps> = ({
  isOpen,
  rawHtml,
  stepId,
  onClose,
}) => {
  const [copied, setCopied] = useState(false);

  if (!isOpen || !rawHtml) return null;

  const handleCopy = () => {
    navigator.clipboard.writeText(rawHtml);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '950px' }}>
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1.25rem 1.5rem', borderBottom: '1px solid var(--border-subtle)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Code size={18} color="var(--accent-cyan)" />
            <h3 style={{ fontSize: '1rem', color: 'var(--text-primary)' }}>
              Raw DOM Source Code (Step {stepId})
            </h3>
          </div>
          <button className="btn btn-ghost" onClick={onClose} style={{ padding: '0.35rem' }}>
            <X size={18} />
          </button>
        </div>

        {/* Body */}
        <div style={{ padding: '1.25rem 1.5rem', overflowY: 'auto', maxHeight: '60vh' }}>
          <pre
            style={{
              background: 'rgba(0, 0, 0, 0.6)',
              padding: '1.25rem',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-subtle)',
              fontSize: '0.78rem',
              fontFamily: 'var(--font-mono)',
              color: '#38bdf8',
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-all',
            }}
          >
            {rawHtml}
          </pre>
        </div>

        {/* Footer */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1rem 1.5rem', borderTop: '1px solid var(--border-subtle)' }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            DOM Payload Size: {Math.round(rawHtml.length / 1024)} KB
          </span>
          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <button className="btn btn-secondary" onClick={handleCopy}>
              {copied ? <Check size={14} color="var(--status-success)" /> : <Copy size={14} />}
              <span>{copied ? 'Copied HTML!' : 'Copy Code'}</span>
            </button>
            <button className="btn btn-primary" onClick={onClose}>
              Done
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
