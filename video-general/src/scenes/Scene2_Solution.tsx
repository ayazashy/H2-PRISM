import React from 'react';
import { AbsoluteFill, spring, useCurrentFrame, useVideoConfig } from 'remotion';
import { Layers, ArrowLeft, Cpu, Scale, Waves, CheckCircle2 } from 'lucide-react';
import { Header } from '../components/Header';

export const Scene2_Solution: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleAnim = spring({ frame, fps, config: { damping: 15 } });
  const pipe1Anim = spring({ frame: frame - 40, fps, config: { damping: 15 } });
  const pipe2Anim = spring({ frame: frame - 180, fps, config: { damping: 15 } });
  const pipe3Anim = spring({ frame: frame - 320, fps, config: { damping: 15 } });
  const pipe4Anim = spring({ frame: frame - 460, fps, config: { damping: 15 } });

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
      <Header currentSceneTitle="الحل والابتكار — منظومة H2-PRISM" sceneNumber={2} />

      {/* Main Header */}
      <div
        style={{
          transform: `scale(${titleAnim})`,
          textAlign: 'center',
          marginBottom: 28,
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
            marginBottom: 12,
          }}
        >
          <Layers size={16} />
          <span>إسناد الأحداث الذكي (Event Attribution) بدلاً من الشذوذ الأعمى</span>
        </div>
        <h1 style={{ fontSize: 38, fontWeight: 900, color: '#ffffff', margin: 0 }}>
          منظومة H2-PRISM: دمج فيزياء الغاز الحقيقي مع الذكاء الاصطناعي
        </h1>
      </div>

      {/* Engineering Workflow Architecture Diagram */}
      <div
        style={{
          width: '100%',
          maxWidth: 1320,
          backgroundColor: '#111827',
          border: '1px solid #1f2937',
          borderRadius: 12,
          padding: '22px 26px',
          marginBottom: 20,
        }}
      >
        <div style={{ fontSize: 14, fontWeight: 800, color: '#9ca3af', marginBottom: 14 }}>
          مخطط سير العمليات الهندسية (H2-PRISM Processing Workflow):
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr auto 1fr auto 1fr auto 1fr', alignItems: 'center', gap: 12 }}>
          {/* Stage 1: SCADA Stream */}
          <div
            style={{
              opacity: pipe1Anim,
              transform: `translateY(${(1 - pipe1Anim) * 15}px)`,
              backgroundColor: '#1e293b',
              border: '1px solid #334155',
              borderRadius: 8,
              padding: 16,
            }}
          >
            <div style={{ fontSize: 12, fontWeight: 800, color: '#94a3b8', marginBottom: 4 }}>المدخلات 01</div>
            <div style={{ fontSize: 16, fontWeight: 800, color: '#ffffff' }}>بيانات SCADA الحية</div>
            <div style={{ fontSize: 12, color: '#cbd5e1', marginTop: 4 }}>الضغط، التدفق، درجة الحرارة</div>
          </div>

          <ArrowLeft size={18} color="#64748b" />

          {/* Stage 2: Physics Engine */}
          <div
            style={{
              opacity: pipe2Anim,
              transform: `translateY(${(1 - pipe2Anim) * 15}px)`,
              backgroundColor: '#064e3b',
              border: '1px solid #059669',
              borderRadius: 8,
              padding: 16,
            }}
          >
            <div style={{ fontSize: 12, fontWeight: 800, color: '#6ee7b7', marginBottom: 4 }}>المحرك الفيزيائي 02</div>
            <div style={{ fontSize: 16, fontWeight: 800, color: '#ffffff' }}>معادلة الغاز الحقيقي</div>
            <div style={{ fontSize: 12, color: '#a7f3d0', marginTop: 4 }}>حساب دقيق لتخزين الأنبوب (Line-Pack)</div>
          </div>

          <ArrowLeft size={18} color="#64748b" />

          {/* Stage 3: Acoustic Localization */}
          <div
            style={{
              opacity: pipe3Anim,
              transform: `translateY(${(1 - pipe3Anim) * 15}px)`,
              backgroundColor: '#0c4a6e',
              border: '1px solid #0284c7',
              borderRadius: 8,
              padding: 16,
            }}
          >
            <div style={{ fontSize: 12, fontWeight: 800, color: '#7dd3fc', marginBottom: 4 }}>الرصد الصوتي 03</div>
            <div style={{ fontSize: 16, fontWeight: 800, color: '#ffffff' }}>الترابط المتقاطع</div>
            <div style={{ fontSize: 12, color: '#bae6fd', marginTop: 4 }}>تحديد نطاق التسريب (±650m)</div>
          </div>

          <ArrowLeft size={18} color="#64748b" />

          {/* Stage 4: Calibrated AI Attribution */}
          <div
            style={{
              opacity: pipe4Anim,
              transform: `translateY(${(1 - pipe4Anim) * 15}px)`,
              backgroundColor: '#4c1d95',
              border: '1px solid #7c3aed',
              borderRadius: 8,
              padding: 16,
            }}
          >
            <div style={{ fontSize: 12, fontWeight: 800, color: '#c4b5fd', marginBottom: 4 }}>الذكاء المعاير 04</div>
            <div style={{ fontSize: 16, fontWeight: 800, color: '#ffffff' }}>إسناد السبب الجذري</div>
            <div style={{ fontSize: 12, color: '#ddd6fe', marginTop: 4 }}>فصل قاطع: تسريب / مناورة / حساس</div>
          </div>
        </div>
      </div>

      {/* 3 Core Pillars Summary */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16, width: '100%', maxWidth: 1320 }}>
        <div style={{ backgroundColor: '#111827', border: '1px solid #1f2937', borderRadius: 10, padding: '16px 20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
            <Scale size={20} color="#22c55e" />
            <h3 style={{ fontSize: 16, fontWeight: 800, color: '#ffffff', margin: 0 }}>تصحيح كتلة Line-Pack</h3>
          </div>
          <p style={{ fontSize: 13, color: '#9ca3af', lineHeight: 1.5, margin: 0 }}>
            يفسر تذبذبات التدفق الناتجة عن انضغاط الهيدروجين وتغير درجات الحرارة دون فقدان فعلي للمادة.
          </p>
        </div>

        <div style={{ backgroundColor: '#111827', border: '1px solid #1f2937', borderRadius: 10, padding: '16px 20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
            <Waves size={20} color="#38bdf8" />
            <h3 style={{ fontSize: 16, fontWeight: 800, color: '#ffffff', margin: 0 }}>السرعة الصوتية (~1300 m/s)</h3>
          </div>
          <p style={{ fontSize: 13, color: '#9ca3af', lineHeight: 1.5, margin: 0 }}>
            قياس زمن وصول الموجة الصوتية بين محطات الإدخال والإخراج لحصر موقع العطل بدقة عالية.
          </p>
        </div>

        <div style={{ backgroundColor: '#111827', border: '1px solid #1f2937', borderRadius: 10, padding: '16px 20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
            <Cpu size={20} color="#a855f7" />
            <h3 style={{ fontSize: 16, fontWeight: 800, color: '#ffffff', margin: 0 }}>احتمالات معايرة وتفسيرية</h3>
          </div>
          <p style={{ fontSize: 13, color: '#9ca3af', lineHeight: 1.5, margin: 0 }}>
            إخراج أوزان ثقة احتمالية معايرة تتيح لمهندسي غرفة التحكم اتخاذ قرارات حاسمة وفورية.
          </p>
        </div>
      </div>
    </AbsoluteFill>
  );
};
