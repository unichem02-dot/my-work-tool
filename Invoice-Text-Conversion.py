import React, { useState, useEffect, useMemo } from 'react';
import { initializeApp } from 'firebase/app';
import { 
  getFirestore, collection, doc, onSnapshot, 
  addDoc, updateDoc, deleteDoc, query 
} from 'firebase/firestore';
import { 
  getAuth, signInAnonymously, onAuthStateChanged, signInWithCustomToken 
} from 'firebase/auth';
import { 
  Plus, Search, Download, LogIn, LogOut, 
  Copy, X, Edit2, ChevronUp, ChevronDown, Monitor, Smartphone, 
  Settings, Trash2, Save
} from 'lucide-react';

// --- Firebase Configuration ---
const firebaseConfig = JSON.parse(__firebase_config);
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const db = getFirestore(app);
const appId = typeof __app_id !== 'undefined' ? __app_id : 'tomboy94-english-pro';

// --- Helper: Number to English ---
const numToEng = (num) => {
  if (num === 0) return "Zero";
  const ones = ["", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"];
  const tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"];
  const scales = ["", "thousand", "million", "billion", "trillion"];

  const convert = (n) => {
    if (n < 20) return ones[n];
    if (n < 100) return tens[Math.floor(n / 10)] + (n % 10 !== 0 ? "-" + ones[n % 10] : "");
    if (n < 1000) return ones[Math.floor(n / 100)] + " hundred" + (n % 100 !== 0 ? " " + convert(n % 100) : "");
    for (let i = 1; i < scales.length; i++) {
      if (n < Math.pow(1000, i + 1)) {
        return convert(Math.floor(n / Math.pow(1000, i))) + " " + scales[i] + (n % Math.pow(1000, i) !== 0 ? " " + convert(n % Math.pow(1000, i)) : "");
      }
    }
    return n.toString();
  };

  const res = convert(num).trim();
  return res.charAt(0).toUpperCase() + res.slice(1);
};

export default function App() {
  const [user, setUser] = useState(null);
  const [isAdmin, setIsAdmin] = useState(false);
  const [showLogin, setShowLogin] = useState(false);
  const [passwordInput, setPasswordInput] = useState("");
  
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  
  const [numInput, setNumInput] = useState("");
  const [search, setSearch] = useState("");
  const [selectedCat, setSelectedCat] = useState("🔀 랜덤 10");
  const [isSimple, setIsSimple] = useState(false);
  const [sortOrder, setSortOrder] = useState('none'); 
  const [page, setPage] = useState(1);
  const itemsPerPage = 100;

  const [showAddModal, setShowAddModal] = useState(false);
  const [editItem, setEditItem] = useState(null);

  const kstDate = new Intl.DateTimeFormat('en-US', {
    weekday: 'long', month: 'long', day: 'numeric', year: 'numeric',
    timeZone: 'Asia/Seoul'
  }).format(new Date());

  // --- Auth Setup ---
  useEffect(() => {
    const initAuth = async () => {
      if (typeof __initial_auth_token !== 'undefined' && __initial_auth_token) {
        await signInWithCustomToken(auth, __initial_auth_token);
      } else {
        await signInAnonymously(auth);
      }
    };
    initAuth();
    const unsubscribe = onAuthStateChanged(auth, setUser);
    return () => unsubscribe();
  }, []);

  // --- Firestore Sync ---
  useEffect(() => {
    if (!user) return;
    const q = collection(db, 'artifacts', appId, 'public', 'data', 'sentences');
    const unsubscribe = onSnapshot(q, (snapshot) => {
      const docs = snapshot.docs.map(d => ({ id: d.id, ...d.data() }));
      setData(docs);
      setLoading(false);
    }, (err) => {
      console.error(err);
      setLoading(false);
    });
    return () => unsubscribe();
  }, [user]);

  // --- Handlers ---
  const handleLogin = (e) => {
    e.preventDefault();
    if (passwordInput === "0315") {
      setIsAdmin(true);
      setShowLogin(false);
      setPasswordInput("");
    } else {
      alert("❌ 비밀번호가 올바르지 않습니다.");
    }
  };

  const copyDate = () => {
    const temp = document.createElement("textarea");
    temp.value = kstDate;
    document.body.appendChild(temp);
    temp.select();
    document.execCommand('copy');
    document.body.removeChild(temp);
    alert("📅 날짜가 복사되었습니다!");
  };

  const categories = useMemo(() => {
    const cats = [...new Set(data.map(item => item.category).filter(Boolean))];
    return cats.sort();
  }, [data]);

  const filteredData = useMemo(() => {
    let result = [...data];
    if (search.trim()) {
      result = result.filter(item => 
        (item.sentence || "").toLowerCase().includes(search.toLowerCase()) ||
        (item.meaning || "").toLowerCase().includes(search.toLowerCase())
      );
    } else {
      if (selectedCat === "🔀 랜덤 10") {
        result = [...result].sort(() => 0.5 - Math.random()).slice(0, 10);
      } else if (selectedCat !== "전체 분류") {
        result = result.filter(item => item.category === selectedCat);
      }
    }

    if (sortOrder === 'asc') result.sort((a, b) => (a.sentence || "").localeCompare(b.sentence || ""));
    else if (sortOrder === 'desc') result.sort((a, b) => (b.sentence || "").localeCompare(a.sentence || ""));
    else result.reverse();

    return result;
  }, [data, search, selectedCat, sortOrder]);

  const paginatedData = filteredData.slice((page - 1) * itemsPerPage, page * itemsPerPage);
  const totalPages = Math.ceil(filteredData.length / itemsPerPage) || 1;

  // --- CRUD ---
  const saveSentence = async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const payload = {
      category: formData.get('category') || formData.get('new_category'),
      sentence: formData.get('sentence'),
      meaning: formData.get('meaning'),
      pronunciation: formData.get('pronunciation'),
      memo1: formData.get('memo1'),
      memo2: formData.get('memo2'),
      updatedAt: new Date().toISOString()
    };

    try {
      if (editItem) {
        await updateDoc(doc(db, 'artifacts', appId, 'public', 'data', 'sentences', editItem.id), payload);
      } else {
        await addDoc(collection(db, 'artifacts', appId, 'public', 'data', 'sentences'), payload);
      }
      setShowAddModal(false);
      setEditItem(null);
    } catch (err) {
      alert("Error: " + err.message);
    }
  };

  const deleteSentence = async (id) => {
    if (!confirm("정말 삭제하시겠습니까?")) return;
    await deleteDoc(doc(db, 'artifacts', appId, 'public', 'data', 'sentences', id));
    setEditItem(null);
  };

  return (
    <div className="min-h-screen bg-[#224343] text-white p-4 md:p-10 font-sans selection:bg-[#FFD700] selection:text-[#224343]">
      <div className="max-w-7xl mx-auto space-y-8">
        
        {/* Top Control Bar */}
        <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-6">
          <div className="flex items-center gap-4">
            {!isAdmin ? (
              <button onClick={() => setShowLogin(true)} className="flex items-center gap-2 px-6 py-2.5 bg-white/10 border border-white/20 rounded-full font-bold hover:bg-white/20 transition-all shadow-lg">
                <LogIn size={18} /> 🔐 LOGIN
              </button>
            ) : (
              <button onClick={() => setIsAdmin(false)} className="flex items-center gap-2 px-6 py-2.5 bg-red-500/20 border border-red-500/40 rounded-full font-bold hover:bg-red-500/40 transition-all text-red-200">
                <LogOut size={18} /> 🔓 LOGOUT
              </button>
            )}
          </div>

          {/* Number Converter */}
          <div className="flex flex-wrap items-center gap-4 bg-black/20 p-3 rounded-2xl w-full lg:w-auto border border-white/5 shadow-inner">
            <span className="font-bold text-white/70">Num.ENG :</span>
            <input 
              type="text" 
              placeholder="숫자 입력..."
              value={numInput}
              onChange={(e) => setNumInput(e.target.value.replace(/[^0-9]/g, ""))}
              className="bg-white text-[#224343] px-4 py-2 rounded-xl font-bold w-full sm:w-40 outline-none ring-2 ring-transparent focus:ring-[#FFD700] transition-all"
            />
            {numInput && (
              <div className="flex items-center gap-3 bg-[#FFD700] text-[#224343] px-4 py-2 rounded-xl animate-in slide-in-from-right-2">
                <span className="font-black text-lg">{numToEng(parseInt(numInput))}</span>
                <button onClick={() => setNumInput("")} className="hover:scale-110 transition"><X size={18}/></button>
              </div>
            )}
          </div>
        </div>

        {/* Branding & Date */}
        <div className="flex flex-col md:flex-row justify-between items-end gap-4 border-b border-white/10 pb-6">
          <div>
            <h1 className="text-4xl md:text-6xl font-black tracking-tighter bg-gradient-to-br from-white to-white/60 bg-clip-text text-transparent">TOmBOy94 English</h1>
            <p className="text-white/40 font-medium mt-1">Professional Sentence Repository</p>
          </div>
          <div className="flex flex-col items-end gap-2">
            <div className="flex items-center gap-3 text-2xl md:text-4xl font-black text-[#FFD700]">
              <span className="drop-shadow-md">📅 {kstDate}</span>
              <button onClick={copyDate} className="p-2 hover:bg-white/10 rounded-xl transition-all border border-white/10"><Copy size={20}/></button>
            </div>
          </div>
        </div>

        {/* Categories */}
        <div className="flex flex-wrap gap-3">
          {["🔀 랜덤 10", "전체 분류", ...categories].map(cat => (
            <button
              key={cat}
              onClick={() => { setSelectedCat(cat); setSearch(""); setPage(1); }}
              className={`px-6 py-2.5 rounded-full font-bold text-lg transition-all transform active:scale-95 ${
                selectedCat === cat 
                ? "bg-[#FFD700] text-[#224343] shadow-[0_0_15px_rgba(255,215,0,0.3)]" 
                : "bg-white/5 border border-white/10 hover:bg-white/10"
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        {/* Action Bar */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-4 bg-white/5 p-4 rounded-3xl border border-white/10">
          <div className="md:col-span-4 relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-white/30" size={20} />
            <input 
              type="text"
              placeholder="검색어를 입력하세요..."
              className="w-full bg-white/10 border border-white/10 rounded-2xl py-3 pl-12 pr-4 focus:bg-white/20 transition-all outline-none"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <div className="md:col-span-8 flex gap-3">
            {isAdmin && (
              <button 
                onClick={() => setShowAddModal(true)}
                className="flex-1 bg-white text-[#224343] font-black rounded-2xl flex items-center justify-center gap-2 hover:bg-gray-200 transition-all shadow-lg"
              >
                <Plus size={22} /> 추가
              </button>
            )}
            <button 
              onClick={() => setIsSimple(!isSimple)}
              className={`flex-1 rounded-2xl font-black flex items-center justify-center gap-2 transition-all shadow-lg ${
                isSimple ? "bg-white/10 text-white border border-white/20" : "bg-white text-[#224343]"
              }`}
            >
              {isSimple ? <Monitor size={20}/> : <Smartphone size={20}/>}
              {isSimple ? "전체모드" : "심플모드"}
            </button>
          </div>
        </div>

        {/* Data Table */}
        <div className="bg-white/5 rounded-[2rem] border border-white/10 overflow-hidden shadow-2xl">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse min-w-[800px]">
              <thead>
                <tr className="bg-white/10 text-white/60 font-bold uppercase text-sm tracking-wider">
                  <th className="px-6 py-4 w-32">분류</th>
                  <th className="px-6 py-4 cursor-pointer hover:text-white" onClick={() => setSortOrder(s => s==='asc'?'desc':'asc')}>
                    단어-문장 {sortOrder === 'asc' ? '↑' : sortOrder === 'desc' ? '↓' : ''}
                  </th>
                  <th className="px-6 py-4">해석</th>
                  {!isSimple && (
                    <>
                      <th className="px-6 py-4">발음</th>
                      <th className="px-6 py-4">메모</th>
                    </>
                  )}
                  {isAdmin && <th className="px-6 py-4 w-20 text-center">수정</th>}
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {loading ? (
                  <tr><td colSpan="6" className="py-20 text-center text-xl font-bold opacity-30">Loading...</td></tr>
                ) : paginatedData.map((item) => (
                  <tr key={item.id} className="hover:bg-white/5 transition-colors group">
                    <td className="px-6 py-6 font-bold opacity-60 text-sm">{item.category}</td>
                    <td className={`px-6 py-6 font-black text-[#FFD700] transition-transform duration-300 group-hover:translate-x-1 ${isSimple ? 'text-2xl' : 'text-xl'}`}>
                      {item.sentence}
                    </td>
                    <td className={`px-6 py-6 leading-relaxed ${isSimple ? 'text-xl' : 'text-lg opacity-90'}`}>
                      {item.meaning}
                    </td>
                    {!isSimple && (
                      <>
                        <td className="px-6 py-6 opacity-60 text-sm italic">{item.pronunciation}</td>
                        <td className="px-6 py-6 opacity-40 text-xs">
                          <div className="line-clamp-2">{item.memo1}</div>
                          <div className="line-clamp-2 text-white/20">{item.memo2}</div>
                        </td>
                      </>
                    )}
                    {isAdmin && (
                      <td className="px-6 py-6 text-center">
                        <button onClick={() => setEditItem(item)} className="p-2 hover:bg-[#FFD700] hover:text-[#224343] rounded-xl transition-all text-white/30">
                          <Edit2 size={18} />
                        </button>
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex justify-center items-center gap-8 py-10">
            <button 
              disabled={page === 1}
              onClick={() => {setPage(p => p - 1); window.scrollTo(0, 0);}}
              className="px-8 py-3 bg-white/5 border border-white/10 rounded-2xl font-black disabled:opacity-20 hover:bg-white/10 transition-all"
            >
              PREV
            </button>
            <div className="flex items-center gap-2">
              <span className="text-2xl font-black text-[#FFD700]">{page}</span>
              <span className="opacity-30">/</span>
              <span className="font-bold opacity-50">{totalPages}</span>
            </div>
            <button 
              disabled={page === totalPages}
              onClick={() => {setPage(p => p + 1); window.scrollTo(0, 0);}}
              className="px-8 py-3 bg-white/5 border border-white/10 rounded-2xl font-black disabled:opacity-20 hover:bg-white/10 transition-all"
            >
              NEXT
            </button>
          </div>
        )}

        {/* Footer */}
        <footer className="pt-20 pb-10 border-t border-white/10 text-center">
          <p className="text-white/30 font-bold text-lg">
            © {new Date().getFullYear()} TOmBOy94 English Pro | lodus11st@naver.com | All rights reserved.
          </p>
        </footer>
      </div>

      {/* --- Modals --- */}
      
      {/* Login Modal */}
      {showLogin && (
        <div className="fixed inset-0 bg-black/90 backdrop-blur-xl flex items-center justify-center z-50 p-6">
          <div className="bg-[#224343] p-10 rounded-[2.5rem] border border-white/20 w-full max-w-md shadow-2xl scale-in">
            <div className="bg-white/10 w-20 h-20 rounded-3xl flex items-center justify-center mb-6 mx-auto">
              <Settings className="text-[#FFD700]" size={40} />
            </div>
            <h2 className="text-3xl font-black text-center mb-2">Admin Login</h2>
            <p className="text-center text-white/40 mb-8">관리자 비밀번호를 입력하세요.</p>
            <form onSubmit={handleLogin} className="space-y-4">
              <input 
                autoFocus
                type="password"
                placeholder="Password"
                className="w-full bg-white text-[#224343] py-5 px-8 rounded-2xl text-2xl font-bold outline-none ring-4 ring-transparent focus:ring-[#FFD700]/50 transition-all text-center"
                value={passwordInput}
                onChange={(e) => setPasswordInput(e.target.value)}
              />
              <div className="flex gap-3 pt-4">
                <button type="button" onClick={() => setShowLogin(false)} className="flex-1 py-4 font-black text-white/50 hover:text-white">CANCEL</button>
                <button type="submit" className="flex-[2] bg-[#FFD700] text-[#224343] py-4 font-black rounded-2xl hover:bg-yellow-400 transition-all shadow-lg">UNLOCK</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add/Edit Modal */}
      {(showAddModal || editItem) && (
        <div className="fixed inset-0 bg-black/90 backdrop-blur-md flex items-center justify-center z-50 p-4 md:p-10 overflow-y-auto">
          <div className="bg-[#224343] p-8 md:p-12 rounded-[3rem] border border-white/20 w-full max-w-3xl my-auto shadow-2xl">
            <h2 className="text-4xl font-black mb-8 flex items-center gap-4">
              {editItem ? <Edit2 className="text-[#FFD700]" size={32}/> : <Plus className="text-[#FFD700]" size={32}/>}
              {editItem ? "항목 수정" : "새 항목 추가"}
            </h2>
            <form onSubmit={saveSentence} className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <label className="text-xs font-black uppercase opacity-40 ml-2">기존 분류</label>
                  <select name="category" defaultValue={editItem?.category || ""} className="w-full bg-white/10 p-4 rounded-2xl border border-white/10 font-bold outline-none focus:ring-2 focus:ring-[#FFD700]">
                    <option value="">(새 분류 직접 입력)</option>
                    {categories.map(c => <option key={c} value={c}>{c}</option>)}
                  </select>
                </div>
                <div className="space-y-2">
                  <label className="text-xs font-black uppercase opacity-40 ml-2">새 분류명</label>
                  <input name="new_category" placeholder="직접 입력..." className="w-full bg-white/10 p-4 rounded-2xl border border-white/10 font-bold outline-none focus:ring-2 focus:ring-[#FFD700]" />
                </div>
              </div>
              
              <div className="space-y-2">
                <label className="text-xs font-black uppercase opacity-40 ml-2">단어 또는 문장</label>
                <textarea 
                  name="sentence" 
                  required 
                  defaultValue={editItem?.sentence || ""} 
                  rows="2"
                  className="w-full bg-white/10 p-4 rounded-2xl border border-white/10 font-black text-2xl text-[#FFD700] outline-none focus:ring-2 focus:ring-[#FFD700] resize-none"
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <label className="text-xs font-black uppercase opacity-40 ml-2">뜻 / 해석</label>
                  <input name="meaning" defaultValue={editItem?.meaning || ""} className="w-full bg-white/10 p-4 rounded-2xl border border-white/10 font-bold outline-none focus:ring-2 focus:ring-[#FFD700]" />
                </div>
                <div className="space-y-2">
                  <label className="text-xs font-black uppercase opacity-40 ml-2">발음 안내</label>
                  <input name="pronunciation" defaultValue={editItem?.pronunciation || ""} className="w-full bg-white/10 p-4 rounded-2xl border border-white/10 font-bold outline-none focus:ring-2 focus:ring-[#FFD700]" />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <label className="text-xs font-black uppercase opacity-40 ml-2">메모 1</label>
                  <input name="memo1" defaultValue={editItem?.memo1 || ""} className="w-full bg-white/10 p-4 rounded-2xl border border-white/10 font-medium outline-none focus:ring-2 focus:ring-[#FFD700]" />
                </div>
                <div className="space-y-2">
                  <label className="text-xs font-black uppercase opacity-40 ml-2">메모 2</label>
                  <input name="memo2" defaultValue={editItem?.memo2 || ""} className="bg-white/10 p-4 rounded-2xl border border-white/10 font-medium w-full outline-none focus:ring-2 focus:ring-[#FFD700]" />
                </div>
              </div>

              <div className="flex flex-wrap gap-4 pt-8">
                <button type="button" onClick={() => { setShowAddModal(false); setEditItem(null); }} className="px-8 py-5 font-black text-white/40 hover:text-white transition-all">취소</button>
                {editItem && (
                  <button type="button" onClick={() => deleteSentence(editItem.id)} className="px-8 py-5 font-black bg-red-500/10 text-red-400 border border-red-500/20 rounded-[1.5rem] hover:bg-red-500 hover:text-white transition-all flex items-center gap-2">
                    <Trash2 size={20}/> 삭제
                  </button>
                )}
                <button type="submit" className="flex-1 bg-[#FFD700] text-[#224343] py-5 font-black rounded-[1.5rem] hover:bg-yellow-400 transition-all shadow-xl flex items-center justify-center gap-2">
                  <Save size={24}/> 저장하기
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <style>{`
        .scale-in { animation: scaleIn 0.3s ease-out forwards; }
        @keyframes scaleIn {
          from { opacity: 0; transform: scale(0.9); }
          to { opacity: 1; transform: scale(1); }
        }
        input::placeholder, textarea::placeholder { color: rgba(255,255,255,0.2); }
        select option { background: #224343; color: white; }
      `}</style>
    </div>
  );
}
