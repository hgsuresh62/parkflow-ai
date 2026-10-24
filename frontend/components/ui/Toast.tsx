'use client';

interface ToastProps {
  title: string;
  message: string;
  type: 'success' | 'info' | 'warning' | 'error';
  onClose: () => void;
}

const typeStyles = {
  success: { bg: '#f0fdf4', border: '#86efac', accent: '#16a34a', icon: '✓' },
  info:    { bg: '#eff6ff', border: '#93c5fd', accent: '#2563eb', icon: 'ℹ' },
  warning: { bg: '#fffbeb', border: '#fcd34d', accent: '#d97706', icon: '⚠' },
  error:   { bg: '#fff1f2', border: '#fca5a5', accent: '#dc2626', icon: '✕' },
};

export default function Toast({ title, message, type, onClose }: ToastProps) {
  const s = typeStyles[type];
  return (
    <div
      className="toast"
      style={{ background: s.bg, borderColor: s.border }}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10 }}>
        <div style={{
          width: 24,
          height: 24,
          borderRadius: '50%',
          background: s.accent,
          color: 'white',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: 13,
          fontWeight: 700,
          flexShrink: 0,
        }}>
          {s.icon}
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ fontWeight: 700, fontSize: 13, color: '#0f172a', marginBottom: 2 }}>{title}</div>
          <div style={{ fontSize: 12, color: '#475569' }}>{message}</div>
        </div>
        <button
          onClick={onClose}
          style={{
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            fontSize: 16,
            color: '#94a3b8',
            lineHeight: 1,
            padding: 0,
          }}
        >×</button>
      </div>
    </div>
  );
}
