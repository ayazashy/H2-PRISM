/* =========================================================
   الدول: الاسم بالعربية والإنجليزية ورمز ISO — القائمة نفسها في تحكيم،
   فالجنسية تصل من الباك اند بالاسم الإنجليزي (nameEn) كما هنا.
   العلم رمز تعبيري يُبنى من رمز ISO (حرفا «المؤشّر الإقليمي») بلا صور.
   ========================================================= */
export const COUNTRIES = [
  { iso2: 'SA', dial: '+966', nameAr: 'السعودية', nameEn: 'Saudi Arabia' },
  { iso2: 'AE', dial: '+971', nameAr: 'الإمارات', nameEn: 'United Arab Emirates' },
  { iso2: 'KW', dial: '+965', nameAr: 'الكويت', nameEn: 'Kuwait' },
  { iso2: 'QA', dial: '+974', nameAr: 'قطر', nameEn: 'Qatar' },
  { iso2: 'BH', dial: '+973', nameAr: 'البحرين', nameEn: 'Bahrain' },
  { iso2: 'OM', dial: '+968', nameAr: 'عُمان', nameEn: 'Oman' },
  { iso2: 'EG', dial: '+20', nameAr: 'مصر', nameEn: 'Egypt' },
  { iso2: 'JO', dial: '+962', nameAr: 'الأردن', nameEn: 'Jordan' },
  { iso2: 'LB', dial: '+961', nameAr: 'لبنان', nameEn: 'Lebanon' },
  { iso2: 'IQ', dial: '+964', nameAr: 'العراق', nameEn: 'Iraq' },
  { iso2: 'SY', dial: '+963', nameAr: 'سوريا', nameEn: 'Syria' },
  { iso2: 'YE', dial: '+967', nameAr: 'اليمن', nameEn: 'Yemen' },
  { iso2: 'PS', dial: '+970', nameAr: 'فلسطين', nameEn: 'Palestine' },
  { iso2: 'SD', dial: '+249', nameAr: 'السودان', nameEn: 'Sudan' },
  { iso2: 'LY', dial: '+218', nameAr: 'ليبيا', nameEn: 'Libya' },
  { iso2: 'TN', dial: '+216', nameAr: 'تونس', nameEn: 'Tunisia' },
  { iso2: 'DZ', dial: '+213', nameAr: 'الجزائر', nameEn: 'Algeria' },
  { iso2: 'MA', dial: '+212', nameAr: 'المغرب', nameEn: 'Morocco' },
  { iso2: 'MR', dial: '+222', nameAr: 'موريتانيا', nameEn: 'Mauritania' },
  { iso2: 'SO', dial: '+252', nameAr: 'الصومال', nameEn: 'Somalia' },
  { iso2: 'DJ', dial: '+253', nameAr: 'جيبوتي', nameEn: 'Djibouti' },
  { iso2: 'ER', dial: '+291', nameAr: 'إريتريا', nameEn: 'Eritrea' },
  { iso2: 'US', dial: '+1', nameAr: 'الولايات المتحدة', nameEn: 'United States' },
  { iso2: 'CA', dial: '+1', nameAr: 'كندا', nameEn: 'Canada' },
  { iso2: 'GB', dial: '+44', nameAr: 'المملكة المتحدة', nameEn: 'United Kingdom' },
  { iso2: 'DE', dial: '+49', nameAr: 'ألمانيا', nameEn: 'Germany' },
  { iso2: 'FR', dial: '+33', nameAr: 'فرنسا', nameEn: 'France' },
  { iso2: 'IT', dial: '+39', nameAr: 'إيطاليا', nameEn: 'Italy' },
  { iso2: 'ES', dial: '+34', nameAr: 'إسبانيا', nameEn: 'Spain' },
  { iso2: 'NL', dial: '+31', nameAr: 'هولندا', nameEn: 'Netherlands' },
  { iso2: 'BE', dial: '+32', nameAr: 'بلجيكا', nameEn: 'Belgium' },
  { iso2: 'CH', dial: '+41', nameAr: 'سويسرا', nameEn: 'Switzerland' },
  { iso2: 'SE', dial: '+46', nameAr: 'السويد', nameEn: 'Sweden' },
  { iso2: 'NO', dial: '+47', nameAr: 'النرويج', nameEn: 'Norway' },
  { iso2: 'DK', dial: '+45', nameAr: 'الدنمارك', nameEn: 'Denmark' },
  { iso2: 'FI', dial: '+358', nameAr: 'فنلندا', nameEn: 'Finland' },
  { iso2: 'TR', dial: '+90', nameAr: 'تركيا', nameEn: 'Türkiye' },
  { iso2: 'RU', dial: '+7', nameAr: 'روسيا', nameEn: 'Russia' },
  { iso2: 'CN', dial: '+86', nameAr: 'الصين', nameEn: 'China' },
  { iso2: 'JP', dial: '+81', nameAr: 'اليابان', nameEn: 'Japan' },
  { iso2: 'KR', dial: '+82', nameAr: 'كوريا الجنوبية', nameEn: 'South Korea' },
  { iso2: 'IN', dial: '+91', nameAr: 'الهند', nameEn: 'India' },
  { iso2: 'PK', dial: '+92', nameAr: 'باكستان', nameEn: 'Pakistan' },
  { iso2: 'BD', dial: '+880', nameAr: 'بنغلاديش', nameEn: 'Bangladesh' },
  { iso2: 'NP', dial: '+977', nameAr: 'النيبال', nameEn: 'Nepal' },
  { iso2: 'MM', dial: '+95', nameAr: 'ميانمار', nameEn: 'Myanmar' },
  { iso2: 'ID', dial: '+62', nameAr: 'إندونيسيا', nameEn: 'Indonesia' },
  { iso2: 'MY', dial: '+60', nameAr: 'ماليزيا', nameEn: 'Malaysia' },
  { iso2: 'SG', dial: '+65', nameAr: 'سنغافورة', nameEn: 'Singapore' },
  { iso2: 'PH', dial: '+63', nameAr: 'الفلبين', nameEn: 'Philippines' },
  { iso2: 'TH', dial: '+66', nameAr: 'تايلاند', nameEn: 'Thailand' },
  { iso2: 'IR', dial: '+98', nameAr: 'إيران', nameEn: 'Iran' },
  { iso2: 'AF', dial: '+93', nameAr: 'أفغانستان', nameEn: 'Afghanistan' },
  { iso2: 'TJ', dial: '+992', nameAr: 'طاجيكستان', nameEn: 'Tajikistan' },
  { iso2: 'AU', dial: '+61', nameAr: 'أستراليا', nameEn: 'Australia' },
  { iso2: 'NZ', dial: '+64', nameAr: 'نيوزيلندا', nameEn: 'New Zealand' },
  { iso2: 'BR', dial: '+55', nameAr: 'البرازيل', nameEn: 'Brazil' },
  { iso2: 'MX', dial: '+52', nameAr: 'المكسيك', nameEn: 'Mexico' },
  { iso2: 'ZA', dial: '+27', nameAr: 'جنوب أفريقيا', nameEn: 'South Africa' },
  { iso2: 'NG', dial: '+234', nameAr: 'نيجيريا', nameEn: 'Nigeria' },
  { iso2: 'KE', dial: '+254', nameAr: 'كينيا', nameEn: 'Kenya' },
  { iso2: 'ET', dial: '+251', nameAr: 'إثيوبيا', nameEn: 'Ethiopia' },
  { iso2: 'ML', dial: '+223', nameAr: 'مالي', nameEn: 'Mali' }
];

// الاسم الإنجليزي ← سجلّ الدولة (أو undefined)
export const countryOf = value => COUNTRIES.find(c => c.nameEn === value);

// الاسم الإنجليزي ← علمها رمزًا تعبيريًّا (🇸🇦)، أو null إن لم تكن في القائمة
export const getCountryFlag = value => {
  const iso2 = countryOf(value)?.iso2;
  if (!iso2) return null;
  return String.fromCodePoint(...[...iso2.toUpperCase()].map(ch => 0x1f1a5 + ch.charCodeAt(0)));
};
