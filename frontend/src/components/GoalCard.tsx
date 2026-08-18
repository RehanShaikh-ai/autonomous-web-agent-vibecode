import React from 'react';
import { Target, CheckSquare, Tag, Hash } from 'lucide-react';
import { GoalSchema } from '../types/schemas';

interface GoalCardProps {
  goal: GoalSchema;
}

export const GoalCard: React.FC<GoalCardProps> = ({ goal }) => {
  return (
    <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Target size={18} color="var(--accent-cyan)" />
          <h3 style={{ fontSize: '1rem', color: 'var(--text-primary)' }}>Stage 1: Parsed Goal & Constraints</h3>
        </div>
        <span className="badge badge-cyan" style={{ fontFamily: 'var(--font-mono)' }}>
          <Hash size={12} /> {goal.goal_id}
        </span>
      </div>

      {/* Objective */}
      <div style={{ background: 'rgba(0, 242, 254, 0.04)', border: '1px solid rgba(0, 242, 254, 0.15)', borderRadius: 'var(--radius-md)', padding: '0.85rem 1.15rem' }}>
        <span style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--accent-cyan)', fontWeight: 700, letterSpacing: '0.05em' }}>
          Consolidated Objective
        </span>
        <p style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-primary)', marginTop: '0.25rem' }}>
          {goal.objective}
        </p>
      </div>

      {/* Constraints */}
      {goal.constraints && goal.constraints.length > 0 && (
        <div>
          <span style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 700, letterSpacing: '0.05em', display: 'flex', alignItems: 'center', gap: '0.35rem', marginBottom: '0.5rem' }}>
            <CheckSquare size={13} /> Active Execution Constraints ({goal.constraints.length})
          </span>
          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            {goal.constraints.map((c, i) => (
              <span
                key={i}
                style={{
                  fontSize: '0.8rem',
                  padding: '0.35rem 0.75rem',
                  borderRadius: 'var(--radius-sm)',
                  background: 'rgba(255, 255, 255, 0.04)',
                  border: '1px solid var(--border-subtle)',
                  color: 'var(--text-secondary)',
                }}
              >
                • {c}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Metadata */}
      {goal.metadata && Object.keys(goal.metadata).length > 0 && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap', paddingTop: '0.5rem', borderTop: '1px solid var(--border-subtle)' }}>
          <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
            <Tag size={12} /> Metadata:
          </span>
          {Object.entries(goal.metadata).map(([k, v]) => (
            <span key={k} className="badge badge-purple" style={{ fontSize: '0.7rem', textTransform: 'none' }}>
              <strong>{k}:</strong> {String(v)}
            </span>
          ))}
        </div>
      )}
    </div>
  );
};
