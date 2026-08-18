import React from 'react';
import {
  Globe,
  MousePointerClick,
  Keyboard,
  ArrowDownCircle,
  Clock,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Loader2,
  ChevronRight,
  LucideIcon,
} from 'lucide-react';
import { BrowserAction, StepRecord } from '../types/schemas';

interface PlanStepListProps {
  steps: StepRecord[];
  activeStepId: number | null;
  onSelectStep: (stepId: number) => void;
}

const ACTION_CONFIG: Record<
  BrowserAction,
  { label: string; icon: LucideIcon; badgeClass: string }
> = {
  navigate: { label: 'NAVIGATE', icon: Globe, badgeClass: 'badge-cyan' },
  click: { label: 'CLICK', icon: MousePointerClick, badgeClass: 'badge-purple' },
  input: { label: 'INPUT', icon: Keyboard, badgeClass: 'badge-cyan' },
  scroll: { label: 'SCROLL', icon: ArrowDownCircle, badgeClass: 'badge-warning' },
  wait: { label: 'WAIT', icon: Clock, badgeClass: 'badge-ghost' },
};

export const PlanStepList: React.FC<PlanStepListProps> = ({
  steps,
  activeStepId,
  onSelectStep,
}) => {
  return (
    <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h3 style={{ fontSize: '1rem', color: 'var(--text-primary)' }}>
          Stage 2 & 3: Plan Step Telemetry ({steps.length} Steps)
        </h3>
        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
          Click step to inspect DOM & Screenshots
        </span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
        {steps.map((rec) => {
          const { step, status, durationMs } = rec;
          const config = ACTION_CONFIG[step.action] || ACTION_CONFIG.navigate;
          const ActionIcon = config.icon;
          const isSelected = activeStepId === step.step_id;

          return (
            <div
              key={step.step_id}
              onClick={() => onSelectStep(step.step_id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '0.9rem 1.15rem',
                borderRadius: 'var(--radius-md)',
                background: isSelected
                  ? 'rgba(0, 242, 254, 0.07)'
                  : 'rgba(255, 255, 255, 0.02)',
                border: `1px solid ${
                  isSelected ? 'rgba(0, 242, 254, 0.4)' : 'var(--border-subtle)'
                }`,
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                gap: '1rem',
              }}
            >
              {/* Left Details */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem', minWidth: 0 }}>
                {/* Index circle */}
                <div
                  style={{
                    width: '28px',
                    height: '28px',
                    borderRadius: '50%',
                    background: 'rgba(255, 255, 255, 0.05)',
                    border: '1px solid var(--border-subtle)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '0.75rem',
                    fontWeight: 700,
                    color: isSelected ? 'var(--accent-cyan)' : 'var(--text-secondary)',
                  }}
                >
                  {step.step_id}
                </div>

                {/* Action Badge */}
                <span className={`badge ${config.badgeClass}`} style={{ fontSize: '0.65rem' }}>
                  <ActionIcon size={12} /> {config.label}
                </span>

                {/* Description & Target */}
                <div style={{ display: 'flex', flexDirection: 'column', minWidth: 0 }}>
                  <span
                    style={{
                      fontSize: '0.85rem',
                      fontWeight: 600,
                      color: 'var(--text-primary)',
                      whiteSpace: 'nowrap',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                    }}
                  >
                    {step.description}
                  </span>
                  <span
                    style={{
                      fontSize: '0.75rem',
                      color: 'var(--text-muted)',
                      fontFamily: 'var(--font-mono)',
                      whiteSpace: 'nowrap',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                    }}
                  >
                    {step.url || step.selector || (step.input_value ? `"${step.input_value}"` : 'Page Viewport')}
                  </span>
                </div>
              </div>

              {/* Right Status & Timing */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexShrink: 0 }}>
                {durationMs !== undefined && (
                  <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                    {durationMs}ms
                  </span>
                )}

                {/* Status Indicator */}
                {status === 'running' && (
                  <span className="badge badge-cyan">
                    <Loader2 size={12} className="animate-spin-slow" /> Executing
                  </span>
                )}
                {status === 'success' && (
                  <span className="badge badge-success">
                    <CheckCircle size={12} /> Done
                  </span>
                )}
                {status === 'timeout' && (
                  <span className="badge badge-warning">
                    <AlertTriangle size={12} /> Timeout
                  </span>
                )}
                {status === 'failed' && (
                  <span className="badge badge-error">
                    <XCircle size={12} /> Failed
                  </span>
                )}
                {status === 'pending' && (
                  <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Pending</span>
                )}

                <ChevronRight size={16} color="var(--text-muted)" />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
