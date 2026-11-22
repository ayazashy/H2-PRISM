import React from 'react';
import { AbsoluteFill, spring, useCurrentFrame, useVideoConfig } from 'remotion';
import { Award, CheckCircle2, ShieldCheck, Database, ArrowLeft } from 'lucide-react';
import { Header } from '../components/Header';

export const Scene4_Results: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleAnim = spring({ frame, fps, config: { damping: 15 } });
  const flowAnim = spring({ frame: frame - 30, fps, config: { damping: 15 } });
  const m1Anim = spring({ frame: frame - 150, fps, config: { damping: 15 } });
  const m2Anim = spring({ frame: frame - 240, fps, config: { damping: 15 } });
  const m3Anim = spring({ frame: frame - 330, fps, config: { damping: 15 } });
  const footerAnim = spring({ frame: frame - 450, fps, config: { damping: 15 } });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: '#0b0f19',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '110px 60px 90px',
        direction: 'rtl',
      }}
    >
      <Header currentSceneTitle="التحقق المرجعي والنتائج الهندسية" sceneNumber={4} />

      {/* Main Header */}
      <div
        style={{
          transform: `scale(${titleAnim})`,
          textAlign: 'center',
          marginBottom: 24,
        }}
      >
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 8,
            backgroundColor: '#064e3b',
            color: '#6ee7b7',
            padding: '6px 18px',
            borderRadius: 6,
            border: '1px solid #059669',
            fontSize: 14,
            fontWeight: 800,
            marginBottom: 10,
          }}
        >
          <Award size={16} />
          <span>تم التحقق على قاعدة بيانات H2-SimNet (Zenodo Record 17871393)</span>
        </div>
        <h1 style={{ fontSize: 38, fontWeight: 900, color: '#ffffff', margin: 0 }}>
          نتائج حاسمة: <span style={{ color: '#22c55e' }}>صفر إنذارات كاذبة (0.0% FPAR)</span> مع دقة رصد كاملة
        </h1>
      </div>

      {/* Validation Pipeline Flow */}
      <div
        style={{
          opacity: flowAnim,
          transform: `translateY(${(1 - flowAnim) * 15}px)`,
          width: '100%',
          maxWidth: 1320,
          backgroundColor: '#111827',
          border: '1px solid #1f2937',
          borderRadius: 12,
          padding: '16px 24px',
          marginBottom: 20,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <Database size={20} color="#38bdf8" />
          <span style={{ fontSize: 14, fontWeight: 800, color: '#ffffff' }}>نطاق التحقق الهندسي:</span>
          <span style={{ fontSize: 14, color: '#94a3b8' }}>123 سيناريو تشغيلي كامل عبر 2.47 مليون نقطة زمنية</span>
        </div>
        <div style={{ fontSize: 13, backgroundColor: '#1e293b', color: '#38bdf8', padding: '4px 12px', borderRadius: 6, border: '1px solid #334155', fontWeight: 700 }}>
          100% تغطية للسيناريوهات المرجعية
        </div>
      </div>

      {/* 3 Core Result Metrics */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16, width: '100%', maxWidth: 1320, marginBottom: 20 }}>
        {/* Metric 1 */}
        <div
          style={{
            opacity: m1Anim,
            transform: `translateY(${(1 - m1Anim) * 15}px)`,
            backgroundColor: '#052e16',
            border: '1px solid #15803d',
            borderRadius: 10,
            padding: '20px 24px',
            textAlign: 'center',
          }}
        >
          <div style={{ fontSize: 13, color: '#86efac', fontWeight: 800, marginBottom: 6 }}>معدل الإنذار الخاطئ (FPAR)</div>
          <div style={{ fontSize: 44, fontWeight: 900, color: '#22c55e', marginBottom: 4 }}>0.0%</div>
          <div style={{ fontSize: 12, color: '#dcfce7' }}>انعدام تام للإنذارات الكاذبة أثناء المناورات الطبيعية</div>
        </div>

        {/* Metric 2 */}
        <div
          style={{
            opacity: m2Anim,
            transform: `translateY(${(1 - m2Anim) * 15}px)`,
            backgroundColor: '#0c4a6e',
            border: '1px solid #0284c7',
            borderRadius: 10,
            padding: '20px 24px',
            textAlign: 'center',
          }}
        >
          <div style={{ fontSize: 13, color: '#7dd3fc', fontWeight: 800, marginBottom: 6 }}>استدعاء التسريبات (Recall)</div>
          <div style={{ fontSize: 44, fontWeight: 900, color: '#38bdf8', marginBottom: 4 }}>100%</div>
          <div style={{ fontSize: 12, color: '#e0f2fe' }}>رصد كامل ودقيق لكافة حالات فقدان الاحتواء</div>
        </div>

        {/* Metric 3 */}
        <div
          style={{
            opacity: m3Anim,
            transform: `translateY(${(1 - m3Anim) * 15}px)`,
            backgroundColor: '#4c1d95',
            border: '1px solid #7c3aed',
            borderRadius: 10,
            padding: '20px 24px',
            textAlign: 'center',
          }}
        >
          <div style={{ fontSize: 13, color: '#c4b5fd', fontWeight: 800, marginBottom: 6 }}>دقة القرارات المغطاة</div>
          <div style={{ fontSize: 44, fontWeight: 900, color: '#a855f7', marginBottom: 4 }}>100%</div>
          <div style={{ fontSize: 12, color: '#f3e8ff' }}>مطابقة تامة عند توفر شروط الرصد الهندسي</div>
        </div>
      </div>

      {/* Team & Deployment Readiness Footer */}
      <div
        style={{
          opacity: footerAnim,
          transform: `translateY(${(1 - footerAnim) * 15}px)`,
          backgroundColor: '#111827',
          border: '1px solid #1f2937',
          borderRadius: 10,
          padding: '14px 24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          width: '100%',
          maxWidth: 1320,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <ShieldCheck size={26} color="#22c55e" />
          <div>
            <div style={{ fontSize: 15, fontWeight: 800, color: '#ffffff' }}>
              H2-PRISM: تمكين النقل الآمن والموثوق لشبكات طاقة الهيدروجين
            </div>
            <div style={{ fontSize: 12, color: '#94a3b8' }}>
              فريق العمل: أحمد (Project Lead) • فيصل (AI Lead) • يزن (Integration & Materials Lead)
            </div>
          </div>
        </div>

        <div style={{ backgroundColor: '#22c55e', color: '#052e16', padding: '6px 16px', borderRadius: 6, fontSize: 13, fontWeight: 900 }}>
          جاهز للاعتماد والتشغيل الصناعي
        </div>
      </div>
    </AbsoluteFill>
  );
};
