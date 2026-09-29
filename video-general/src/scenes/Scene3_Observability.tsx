import React from 'react';
import { AbsoluteFill, spring, useCurrentFrame, useVideoConfig } from 'remotion';
import { Eye, HelpCircle, Check, ArrowDown, GitFork, Sliders } from 'lucide-react';
import { Header } from '../components/Header';

export const Scene3_Observability: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleAnim = spring({ frame, fps, config: { damping: 15 } });
  const formAnim = spring({ frame: frame - 40, fps, config: { damping: 15 } });
  const forkAAnim = spring({ frame: frame - 200, fps, config: { damping: 15 } });
  const forkBAnim = spring({ frame: frame - 360, fps, config: { damping: 15 } });

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
      <Header currentSceneTitle="مقياس الرصد ثلاثي المحاور والامتناع الذكي (UNKNOWN)" sceneNumber={3} />

      {/* Main Header */}
      <div
        style={{
          transform: `scale(${titleAnim})`,
          textAlign: 'center',
          marginBottom: 26,
        }}
      >
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 8,
            backgroundColor: '#451a03',
            color: '#fde68a',
            padding: '6px 18px',
            borderRadius: 6,
            border: '1px solid #d97706',
            fontSize: 14,
            fontWeight: 800,
            marginBottom: 10,
          }}
        >
          <Eye size={16} />
          <span>الشفافية الهندسية الصادقة بدلاً من التخمين الأعمى</span>
        </div>
        <h1 style={{ fontSize: 38, fontWeight: 900, color: '#ffffff', margin: 0 }}>
          مقياس الرصد المستقل وقرار الامتناع الذكي <span style={{ color: '#f59e0b' }}>UNKNOWN</span>
        </h1>
      </div>

      {/* Decision Workflow Architecture */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.3fr', gap: 20, width: '100%', maxWidth: 1320 }}>
        {/* Left: 3-Axis Observability Engine */}
        <div
          style={{
            opacity: formAnim,
            transform: `translateY(${(1 - formAnim) * 15}px)`,
            backgroundColor: '#111827',
            border: '1px solid #1f2937',
            borderRadius: 12,
            padding: '20px 24px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14 }}>
            <Sliders size={20} color="#38bdf8" />
            <h3 style={{ fontSize: 18, fontWeight: 800, color: '#ffffff', margin: 0 }}>
              معادلة الرصد: O = min( O_Q , O_S , O_E )
            </h3>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            <div style={{ backgroundColor: '#1f2937', padding: '10px 14px', borderRadius: 8, borderRight: '4px solid #22c55e' }}>
              <div style={{ fontSize: 13, fontWeight: 800, color: '#22c55e' }}>O_Q (جودة الإشارات)</div>
              <div style={{ fontSize: 12, color: '#cbd5e1' }}>خلو البيانات من الانقطاع، التجميد، والضوضاء غير المعقولة.</div>
            </div>

            <div style={{ backgroundColor: '#1f2937', padding: '10px 14px', borderRadius: 8, borderRight: '4px solid #38bdf8' }}>
              <div style={{ fontSize: 13, fontWeight: 800, color: '#38bdf8' }}>O_S (الملاءمة الهيكلية)</div>
              <div style={{ fontSize: 12, color: '#cbd5e1' }}>معدل العينات مقارنة بزمن عبور الموجة الصوتية (tau = L/a).</div>
            </div>

            <div style={{ backgroundColor: '#1f2937', padding: '10px 14px', borderRadius: 8, borderRight: '4px solid #a855f7' }}>
              <div style={{ fontSize: 13, fontWeight: 800, color: '#a855f7' }}>O_E (اتساق الأدلة)</div>
              <div style={{ fontSize: 12, color: '#cbd5e1' }}>تطابق المؤشرات الفيزيائية مع تنبؤات نموذج التعلم الآلي.</div>
            </div>
          </div>
        </div>

        {/* Right: Decision Fork Logic */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {/* Branch 1: Adequate Observability */}
          <div
            style={{
              opacity: forkAAnim,
              transform: `translateY(${(1 - forkAAnim) * 15}px)`,
              backgroundColor: '#052e16',
              border: '1px solid #15803d',
              borderRadius: 10,
              padding: '16px 20px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                <span style={{ fontSize: 11, backgroundColor: '#15803d', color: '#ffffff', fontWeight: 800, padding: '2px 8px', borderRadius: 4 }}>
                  مسار الرصد الكافي (O ≥ 0.70)
                </span>
                <span style={{ fontSize: 12, color: '#86efac' }}>ADEQUATE OBSERVABILITY</span>
              </div>
              <div style={{ fontSize: 16, fontWeight: 800, color: '#f0fdf4' }}>قرار حاسم: LEAK (تسريب مؤكد بنسبة 76%)</div>
              <div style={{ fontSize: 12, color: '#86efac', marginTop: 2 }}>تحديد الموقع: 6.3 - 7.6 كم | عجز الكتلة z_MB = 16.4</div>
            </div>
            <div style={{ width: 36, height: 36, borderRadius: 18, backgroundColor: '#15803d', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Check size={22} color="#ffffff" />
            </div>
          </div>

          {/* Branch 2: Insufficient Observability -> UNKNOWN */}
          <div
            style={{
              opacity: forkBAnim,
              transform: `translateY(${(1 - forkBAnim) * 15}px)`,
              backgroundColor: '#451a03',
              border: '1px solid #b45309',
              borderRadius: 10,
              padding: '16px 20px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                <span style={{ fontSize: 11, backgroundColor: '#b45309', color: '#ffffff', fontWeight: 800, padding: '2px 8px', borderRadius: 4 }}>
                  مسار الرصد غير الكافي (O &lt; 0.70)
                </span>
                <span style={{ fontSize: 12, color: '#fde68a' }}>INSUFFICIENT OBSERVABILITY</span>
              </div>
              <div style={{ fontSize: 16, fontWeight: 800, color: '#fffbeb' }}>قرار شفاف: UNKNOWN (امتناع ذكي)</div>
              <div style={{ fontSize: 12, color: '#fde68a', marginTop: 2 }}>السبب التشخيصي: معدل العينات يتجاوز زمن العبور الصوتي للأنبوب</div>
            </div>
            <div style={{ width: 36, height: 36, borderRadius: 18, backgroundColor: '#b45309', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <HelpCircle size={22} color="#ffffff" />
            </div>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
