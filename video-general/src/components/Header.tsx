import React from 'react';
import { ShieldCheck, Activity, Zap } from 'lucide-react';

export const Header: React.FC<{ currentSceneTitle: string; sceneNumber: number }> = ({
  currentSceneTitle,
  sceneNumber,
}) => {
  return (
    <header
      style={{
        position: 'absolute',
        top: 32,
        left: 50,
        right: 50,
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '14px 24px',
        backgroundColor: '#131b2e',
        borderRadius: '12px',
        border: '1px solid #233252',
        zIndex: 100,
        direction: 'rtl',
      }}
    >
      {/* Brand & Project Identity */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <div
          style={{
            width: 38,
            height: 38,
            borderRadius: '8px',
            backgroundColor: '#0284c7',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <Activity size={22} color="#ffffff" strokeWidth={2.5} />
        </div>
        <div>
          <div style={{ fontSize: 22, fontWeight: 900, color: '#ffffff', display: 'flex', alignItems: 'center', gap: 8 }}>
            H2-PRISM
            <span style={{ fontSize: 12, backgroundColor: '#1e293b', color: '#38bdf8', padding: '2px 8px', borderRadius: 4, border: '1px solid #334155' }}>
              AI + Physics
            </span>
          </div>
          <div style={{ fontSize: 12, color: '#94a3b8' }}>إطار إسناد أحداث شبكات الهيدروجين الموجه بالفيزياء</div>
        </div>
      </div>

      {/* Current Stage */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, backgroundColor: '#1e293b', padding: '6px 14px', borderRadius: 8, border: '1px solid #334155' }}>
          <Zap size={15} color="#38bdf8" />
          <span style={{ fontSize: 14, fontWeight: 800, color: '#38bdf8' }}>المرحلة 0{sceneNumber}:</span>
          <span style={{ fontSize: 14, fontWeight: 600, color: '#f1f5f9' }}>{currentSceneTitle}</span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: '#22c55e', fontSize: 12, fontWeight: 700, backgroundColor: '#052e16', padding: '6px 12px', borderRadius: 6, border: '1px solid #15803d' }}>
          <ShieldCheck size={15} />
          <span>Real-Gas Verified</span>
        </div>
      </div>
    </header>
  );
};
