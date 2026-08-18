import React from 'react';
import { Compass, ListOrdered, Globe, ShieldCheck, Award, CheckCircle2 } from 'lucide-react';
import { PipelineStage } from '../types/schemas';

interface PipelineStagesProps {
  currentStage: PipelineStage | 0;
  isCompleted: boolean;
}

const STAGES = [
  { id: 1, name: 'Understand', desc: 'Constraint Extraction', icon: Compass },
  { id: 2, name: 'Plan', desc: 'Atomic Step Ordering', icon: ListOrdered },
  { id: 3, name: 'Browse & Process', desc: 'Playwright & MarkItDown', icon: Globe },
  { id: 4, name: 'Verify', desc: 'Cross-Source Math', icon: ShieldCheck },
  { id: 5, name: 'Deliver', desc: 'Verified Intelligence', icon: Award },
];

export const PipelineStages: React.FC<PipelineStagesProps> = ({ currentStage, isCompleted }) => {
  return (
    <div className="glass-panel" style={{ padding: '1.25rem 1.5rem' }}>
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          gap: '1rem',
          position: 'relative',
        }}
      >
        {STAGES.map((stage) => {
          const Icon = stage.icon;
          const isCurrent = currentStage === stage.id && !isCompleted;
          const isDone = currentStage > stage.id || isCompleted;

          return (
            <div
              key={stage.id}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.85rem',
                padding: '0.85rem 1rem',
                borderRadius: 'var(--radius-md)',
                background: isCurrent
                  ? 'rgba(0, 242, 254, 0.08)'
                  : isDone
                  ? 'rgba(16, 185, 129, 0.06)'
                  : 'rgba(255, 255, 255, 0.02)',
                border: `1px solid ${
                  isCurrent
                    ? 'rgba(0, 242, 254, 0.4)'
                    : isDone
                    ? 'rgba(16, 185, 129, 0.3)'
                    : 'var(--border-subtle)'
                }`,
                boxShadow: isCurrent ? '0 0 15px rgba(0, 242, 254, 0.2)' : 'none',
                transition: 'all 0.3s ease',
              }}
            >
              <div
                style={{
                  width: '36px',
                  height: '36px',
                  borderRadius: '10px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  background: isCurrent
                    ? 'var(--accent-cyan)'
                    : isDone
                    ? 'var(--status-success)'
                    : 'rgba(255, 255, 255, 0.05)',
                  color: isCurrent || isDone ? '#040914' : 'var(--text-muted)',
                  fontWeight: 700,
                  fontSize: '0.9rem',
                }}
              >
                {isDone ? <CheckCircle2 size={20} /> : <Icon size={18} />}
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', minWidth: 0 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <span
                    style={{
                      fontSize: '0.85rem',
                      fontWeight: 700,
                      color: isCurrent
                        ? 'var(--accent-cyan)'
                        : isDone
                        ? 'var(--text-primary)'
                        : 'var(--text-muted)',
                    }}
                  >
                    {stage.id}. {stage.name}
                  </span>
                </div>
                <span
                  style={{
                    fontSize: '0.72rem',
                    color: isCurrent ? 'var(--text-secondary)' : 'var(--text-muted)',
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                  }}
                >
                  {stage.desc}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
