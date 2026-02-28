import React, { useState, useEffect } from 'react';
import { 
  Clipboard, 
  Check, 
  RefreshCcw, 
  Package, 
  FileText, 
  Mail, 
  Copy,
  Info
} from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState('jeonjin');
  const [jeonjinInput, setJeonjinInput] = useState('');
  const [uniInput, setUniInput] = useState('');
  const [copied, setCopied] = useState(false);

  // 날짜 생성 로직 (KST 기준)
  const now = new Date();
  const kstOffset = 9 * 60 * 60 * 1000;
  const kstDate = new Date(now.getTime() + kstOffset);
  
  const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
  const months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
  
  const fullEnglishDate = `${days[kstDate.getUTCDay()]}, ${months[kstDate.getUTCMonth()]} ${kstDate.getUTCDate()}, ${kstDate.getUTCFullYear()}`;
  const todayStr = kstDate.getUTCFullYear().toString().slice(-2) + 
                   (kstDate.getUTCMonth() + 1).toString().padStart(2, '0') + 
                   kstDate.getUTCDate().toString().padStart(2, '0');

  const copyHeader = `<<<<<<${fullEnglishDate}, 경동마감>>>>>>`;

  const handleCopyHeader = () => {
    const el = document.createElement('textarea');
    el.value = copyHeader;
    document.body.appendChild(el);
    el.select();
    document.execCommand('copy');
    document.body.removeChild(el);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // 전진발주 변환 로직
  const convertJeonjin = (text) => {
    if (!text.trim()) return "";
    return text.trim().split('\n').map(line => {
      const parts = line.split('\t').map(p => p.trim());
      if (parts.length < 7) return "";
      try {
        const [zip, addr, name, p1, p2, qtyStr, , rawProd, note] = parts;
        const p1_clean = p1.replace(/[^0-9]/g, '');
        const p2_clean = (p2 || "").replace(/[^0-9]/g, '');
        const phone = (p2_clean && p1_clean !== p2_clean) ? `${p1} / ${p2}` : p1;
        
        const qty = parseInt(qtyStr) || 1;
        let productName = rawProd;
        if (rawProd.includes("차아염소산") || rawProd.includes("차염")) productName = "차염산";
        else if (rawProd.includes("구연산")) productName = "구연산수50%(20kg)";
        else if (rawProd.includes("PAC")) productName = "PAC17%";
        else if (rawProd.includes("가성소다")) productName = "가성소다4.5%(20kg)";

        const palletText = qty >= 10 ? " - 파래트" : "";
        
        return `${productName} ${qty}통${palletText} (송장번호필요)\n--------------\n택배선불로 보내주세요^^\n${zip}\n${addr}\n${name} ${phone}${note ? '\n' + note : ''}`;
      } catch (e) { return ""; }
    }).filter(v => v).join('\n\n');
  };

  // 유니케미칼 변환 로직
  const convertUni = (text) => {
    if (!text.trim()) return "";
    const separator = `${todayStr}${"-".repeat(24)}`;
    return text.trim().split('\n').map(line => {
      const parts = line.split('\t').map(p => p.trim());
      if (parts.length < 5) return `⚠️ 데이터 부족: ${line}`;
      try {
        const [zip, addr, name, tel1, tel2_raw, qty, pay, prod, memo] = parts;
        const t1_clean = tel1.replace(/[^0-9]/g, '');
        const t2_clean = (tel2_raw || "").replace(/[^0-9]/g, '');
        const telDisplay = (t1_clean === t2_clean || !tel2_raw) ? tel1 : `${tel1}\t${tel2_raw}`;
        
        return `${zip}\n${addr}\n${name}\t${telDisplay}\n${qty}\t${pay}\t${prod}${memo ? '\n' + memo : ''}`;
      } catch (e) { return `❌ 에러: ${line}`; }
    }).join(`\n\n${separator}\n\n`) + `\n\n${separator}`;
  };

  const jeonjinResult = convertJeonjin(jeonjinInput);
  const uniResult = convertUni(uniInput);

  return (
    <div className="min-h-screen bg-[#1a3636] text-white p-4 md:p-8 font-sans">
      <div className="max-w-7xl mx-auto space-y-6">
        
        {/* 상단 복사 섹션 */}
        <div className="flex flex-wrap items-center gap-4 py-2">
          <span className="text-lg md:text-xl font-black">{`<<<<<<${fullEnglishDate}, 경동마감>>>>>>`}</span>
          <button 
            onClick={handleCopyHeader}
            className={`flex items-center gap-2 px-5 py-2 rounded-full font-bold border transition-all ${copied ? 'bg-[#03C75A] border-[#03C75A]' : 'bg-transparent border-white hover:bg-white/10'}`}
          >
            {copied ? <Check size={18} /> : <Copy size={18} />}
            {copied ? '복사완료!' : '📋 복사하기'}
          </button>
        </div>

        {/* 메인 타이틀 */}
        <div className="flex flex-col md:flex-row md:items-baseline gap-2 border-b border-white/10 pb-4">
          <h1 className="text-3xl font-black">송장텍스트변환 &lt;LYC&gt;</h1>
          <span className="text-white/60 font-bold">lodus11st@naver.com</span>
        </div>

        {/* 탭 메뉴 */}
        <div className="flex gap-8 border-b border-white/10">
          <button 
            onClick={() => setActiveTab('jeonjin')}
            className={`pb-4 text-2xl font-black transition-all relative ${activeTab === 'jeonjin' ? 'text-white' : 'text-[#8da9a7]'}`}
          >
            📦 텍스트변환(전진발주)
            {activeTab === 'jeonjin' && <div className="absolute bottom-0 left-0 w-full h-1 bg-white" />}
          </button>
          <button 
            onClick={() => setActiveTab('uni')}
            className={`pb-4 text-2xl font-black transition-all relative ${activeTab === 'uni' ? 'text-white' : 'text-[#8da9a7]'}`}
          >
            📝 텍스트변환(유니케미칼)
            {activeTab === 'uni' && <div className="absolute bottom-0 left-0 w-full h-1 bg-white" />}
          </button>
        </div>

        {/* 컨텐츠 영역 */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 pt-4">
          
          {/* 왼쪽: 입력창 */}
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h2 className="text-xl font-bold">1. 엑셀 데이터 붙여넣기</h2>
              <button 
                onClick={() => activeTab === 'jeonjin' ? setJeonjinInput('') : setUniInput('')}
                className="flex items-center gap-2 px-4 py-1.5 rounded-full border border-white text-sm font-bold hover:bg-white/10 transition-all"
              >
                <RefreshCcw size={16} /> 입력창 비우기
              </button>
            </div>
            <textarea 
              value={activeTab === 'jeonjin' ? jeonjinInput : uniInput}
              onChange={(e) => activeTab === 'jeonjin' ? setJeonjinInput(e.target.value) : setUniInput(e.target.value)}
              className="w-full h-[500px] bg-[#122626] border border-[#3c5e5d] rounded-xl p-4 text-white focus:border-white outline-none font-mono text-sm leading-relaxed"
              placeholder="엑셀에서 복사한 내용을 여기에 붙여넣으세요..."
            />
          </div>

          {/* 오른쪽: 결과창 */}
          <div className="space-y-4">
            <h2 className="text-xl font-bold">2. 변환 결과</h2>
            {(activeTab === 'jeonjin' ? jeonjinInput : uniInput) ? (
              <textarea 
                readOnly
                value={activeTab === 'jeonjin' ? jeonjinResult : uniResult}
                className="w-full h-[500px] bg-[#122626] border border-[#3c5e5d] rounded-xl p-4 text-white font-mono text-sm leading-relaxed"
              />
            ) : (
              <div className="w-full h-[500px] bg-[#214544] rounded-xl flex flex-col items-center justify-center text-white/50 space-y-2">
                <Info size={40} />
                <p className="text-lg font-bold">왼쪽에 데이터를 붙여넣으세요.</p>
              </div>
            )}
          </div>

        </div>

        {/* 푸터 */}
        <footer className="mt-12 py-8 border-t border-white/10 text-center opacity-40 font-bold">
          © {kstDate.getUTCFullYear()} LYC TEXT CONVERTER | All rights reserved.
        </footer>
      </div>

      <style>{`
        body { background-color: #1a3636; }
        textarea::placeholder { color: rgba(255,255,255,0.2); }
      `}</style>
    </div>
  );
}
