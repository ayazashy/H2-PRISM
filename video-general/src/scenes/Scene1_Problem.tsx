import React from 'react';
import { AbsoluteFill, spring, useCurrentFrame, useVideoConfig } from 'remotion';
import { AlertTriangle, ArrowLeft, DollarSign, XCircle, Gauge, Sliders } from 'lucide-react';
import { Header } from '../components/Header';

export const Scene1_Problem: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleAnim = spring({ frame, fps, config: { damping: 15 } });
  const step1Anim = spring({ frame: frame - 30, fps, config: { damping: 15 } });
  const step2Anim = spring({ frame: frame - 150, fps, config: { damping: 15 } });
  const step3Anim = spring({ frame: frame - 280, fps, config: { damping: 15 } });
  const step4Anim = spring({ frame: frame - 420, fps, config: { damping: 15 } });

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
      <Header currentSceneTitle="معضلة نقل الهيدروجين والإنذارات الكاذبة" sceneNumber={1} />

      {/* Main Section Header */}
      <div
        style={{
          transform: `scale(${titleAnim})`,
          textAlign: 'center',
          marginBottom: 30,
        }}
      >
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 8,
            backgroundColor: '#1e1b4b',
            color: '#a5b4fc',
            padding: '6px 18px',
            borderRadius: 6,
            border: '1px solid #3730a3',
            fontSize: 14,
            fontWeight: 800,
            marginBottom: 12,
          }}
        >
          <span>تحدي غرف المراقبة في خطوط أنابيب الهيدروجين</span>
        </div>
        <h1 style={{ fontSize: 38, fontWeight: 900, color: '#ffffff', margin: 0 }}>
          أزمة الإنذارات الكاذبة في شبكات الهيدروجين التقليدية
        </h1>
      </div>

      {/* Process Workflow Diagram: The Traditional SCADA Failure Chain */}
      <div
        style={{
          width: '100%',
          maxWidth: 1320,
          backgroundColor: '#111827',
          border: '1px solid #1f2937',
          borderRadius: 12,
          padding: '24px 28px',
          marginBottom: 24,
        }}
      >
        <div style={{ fontSize: 14, fontWeight: 800, color: '#9ca3af', marginBottom: 16 }}>
          مخطط مسار المشكلة في الأنظمة الحالية (Traditional SCADA Pipeline):
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr auto 1fr auto 1fr auto 1fr', alignItems: 'center', gap: 12 }}>
          {/* Step 1 */}
          <div
            style={{
              opacity: step1Anim,
              transform: `translateY(${(1 - step1Anim) * 15}px)`,
              backgroundColor: '#1f2937',
              border: '1px solid #374151',
              borderRadius: 8,
              padding: 16,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: '#38bdf8', fontSize: 12, fontWeight: 800, marginBottom: 4 }}>
              <Sliders size={16} />
              <span>1. حدث تشغيلي</span>
            </div>
            <div style={{ fontSize: 16, fontWeight: 800, color: '#f9fafb' }}>تغيير صمام أو ضاغط</div>
            <div style={{ fontSize: 12, color: '#9ca3af', marginTop: 4 }}>تذبذب طبيعي في الطلب</div>
          </div>

          <ArrowLeft size={20} color="#4b5563" />

          {/* Step 2 */}
          <div
            style={{
              opacity: step2Anim,
              transform: `translateY(${(1 - step2Anim) * 15}px)`,
              backgroundColor: '#1f2937',
              border: '1px solid #374151',
              borderRadius: 8,
              padding: 16,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: '#f59e0b', fontSize: 12, fontWeight: 800, marginBottom: 4 }}>
              <Gauge size={16} />
              <span>2. استجابة التدفق</span>
            </div>
            <div style={{ fontSize: 16, fontWeight: 800, color: '#f9fafb' }}>هبوط ضغط عابر</div>
            <div style={{ fontSize: 12, color: '#9ca3af', marginTop: 4 }}>تأثير سعة تخزين الأنبوب</div>
          </div>

          <ArrowLeft size={20} color="#4b5563" />

          {/* Step 3 */}
          <div
            style={{
              opacity: step3Anim,
              transform: `translateY(${(1 - step3Anim) * 15}px)`,
              backgroundColor: '#1f2937',
              border: '1px solid #ef4444',
              borderRadius: 8,
              padding: 16,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: '#ef4444', fontSize: 12, fontWeight: 800, marginBottom: 4 }}>
              <AlertTriangle size={16} />
              <span>3. إنذار حدّي أعمى</span>
            </div>
            <div style={{ fontSize: 16, fontWeight: 800, color: '#f87171' }}>إطلاق إنذار تسريب!</div>
            <div style={{ fontSize: 12, color: '#9ca3af', marginTop: 4 }}>بسبب غياب الفهم الفيزيائي</div>
          </div>

          <ArrowLeft size={20} color="#4b5563" />

          {/* Step 4 */}
          <div
            style={{
              opacity: step4Anim,
              transform: `translateY(${(1 - step4Anim) * 15}px)`,
              backgroundColor: '#450a0a',
              border: '1px solid #991b1b',
              borderRadius: 8,
              padding: 16,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: '#fca5a5', fontSize: 12, fontWeight: 800, marginBottom: 4 }}>
              <XCircle size={16} />
              <span>4. النتيجة التشغيلية</span>
            </div>
            <div style={{ fontSize: 16, fontWeight: 800, color: '#ffffff' }}>إغلاق خاطئ للشبكة</div>
            <div style={{ fontSize: 12, color: '#fca5a5', marginTop: 4 }}>خسائر مادية وانعدام الثقة</div>
          </div>
        </div>
      </div>

      {/* 3 Impact Stats Boxes */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16, width: '100%', maxWidth: 1320 }}>
        <div style={{ backgroundColor: '#111827', border: '1px solid #1f2937', borderRadius: 10, padding: '16px 20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
            <span style={{ fontSize: 13, fontWeight: 800, color: '#ef4444' }}>معدل الإنذارات الزائفة</span>
            <AlertTriangle size={20} color="#ef4444" />
          </div>
          <div style={{ fontSize: 32, fontWeight: 900, color: '#ffffff' }}>+90%</div>
          <div style={{ fontSize: 13, color: '#9ca3af', marginTop: 4 }}>المناورات التشغيلية تُشخص خطأً كتسريب خطير</div>
        </div>

        <div style={{ backgroundColor: '#111827', border: '1px solid #1f2937', borderRadius: 10, padding: '16px 20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
            <span style={{ fontSize: 13, fontWeight: 800, color: '#f59e0b' }}>الخسائر التشغيلية</span>
            <DollarSign size={20} color="#f59e0b" />
          </div>
          <div style={{ fontSize: 32, fontWeight: 900, color: '#ffffff' }}>ملايين $</div>
          <div style={{ fontSize: 13, color: '#9ca3af', marginTop: 4 }}>تكاليف توقف خطوط الإنتاج والإغلاقات الطارئة</div>
        </div>

        <div style={{ backgroundColor: '#111827', border: '1px solid #1f2937', borderRadius: 10, padding: '16px 20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
            <span style={{ fontSize: 13, fontWeight: 800, color: '#38bdf8' }}>تحدي السلامة</span>
            <XCircle size={20} color="#38bdf8" />
          </div>
          <div style={{ fontSize: 32, fontWeight: 900, color: '#ffffff' }}>تآكل الثقة</div>
          <div style={{ fontSize: 13, color: '#9ca3af', marginTop: 4 }}>تعطيل أنظمة الحماية بسبب كثرة الإنذارات الكاذبة</div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
