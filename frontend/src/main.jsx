import React,{useState,useEffect} from 'react';
import {createRoot} from 'react-dom/client';
import {LayoutDashboard,Wallet,TrendingUp,Target,Landmark,Sparkles,FlaskConical,Settings,ChevronRight,LogOut,Menu,ShieldCheck,Check,AlertTriangle,X,FileText,Loader2} from 'lucide-react';
import './styles.css';
import {api,post} from './lib/api.js';
import {Brand,Button} from './components/ui.jsx';
import {AppErrorBoundary} from './PlanTools.jsx';
import FirePlanner from './FirePlanner.jsx';
import FinancialHealth,{HealthSetup} from './FinancialHealth.jsx';
import Auth from './pages/Auth.jsx';
import Overview from './pages/Overview.jsx';
import Finances from './pages/Finances.jsx';
import Simulator from './pages/Simulator.jsx';
import Goals from './pages/Goals.jsx';
import DebtPlanner from './pages/DebtPlanner.jsx';
import Advisor from './pages/Advisor.jsx';
import Research from './pages/Research.jsx';
import SettingsPage from './pages/Settings.jsx';
import Reports from './pages/Reports.jsx';

const NAV=[['overview','Overview',LayoutDashboard],['financials','My finances',Wallet],['health','Financial health',ShieldCheck],['healthsetup','Personal & protection',Wallet],['fire','FIRE planner',Target],['projections','Wealth simulator',TrendingUp],['goals','Goals',Target],['debt','Debt planner',Landmark],['advisor','Financial guide',Sparkles],['research','ML research',FlaskConical],['reports','Reports',FileText],['settings','Settings',Settings]];
function App(){
 const [user,setUser]=useState(null),[state,setState]=useState(null),[version,setVersion]=useState(0),[dash,setDash]=useState(null),[loading,setLoading]=useState(true),[page,setPage]=useState('overview'),[busy,setBusy]=useState(false),[toast,setToast]=useState(null),[mobile,setMobile]=useState(false),[loadError,setLoadError]=useState('');
 function notify(text,error=false){setToast({text,error});setTimeout(()=>setToast(null),6000)}
 async function load(){setLoading(true);setLoadError('');try{const me=await api('/me');const [s,d]=await Promise.all([api('/state'),api('/dashboard')]);setUser(me);setState(s.state);setVersion(s.version);setDash(d);}catch(e){if(/sign in|expired|Account unavailable/.test(e.message)){setUser(null);setState(null);}else setLoadError(e.message)}finally{setLoading(false)}}
 useEffect(()=>{load()},[]);
 async function save(next){setBusy(true);try{const r=await api('/state',{method:'PUT',body:JSON.stringify({state:next,version})});setState(r.state);setVersion(r.version);setDash(r.dashboard);window.wealthPlanDirty=false;notify('Your plan is saved.');return true}catch(e){notify(e.message,true);return false}finally{setBusy(false)}}
 function navigate(p){if(window.wealthPlanDirty&&!confirm('You have unsaved changes. Leave this page and discard them?'))return;setPage(p);setMobile(false);window.scrollTo({top:0,behavior:'smooth'})}
 if(loading)return <div className="app-loading"><Brand/><Loader2 className="spin"/><p>Bringing your plan into focus…</p></div>;
 if(loadError)return <div className="app-loading"><Brand/><p className="error">{loadError}</p><Button onClick={load}>Try again</Button></div>;
 if(!user)return <Auth onLogin={load}/>;
 const common={state,summary:dash.summary,projection:dash.projection,wellness:dash.wellness,save,busy,navigate};
 return <div className="app-shell"><aside className={`sidebar ${mobile?'open':''}`}><Brand/><span className="nav-label">YOUR WORKSPACE</span><nav>{NAV.map(([id,label,Icon],i)=><React.Fragment key={id}>{id==='research'&&<div className="nav-divider"/>}<button className={page===id?'active':''} onClick={()=>navigate(id)}><Icon size={19}/><span>{label}</span>{id==='advisor'&&<span className="nav-new">GUIDE</span>}</button></React.Fragment>)}</nav><div className="sidebar-bottom"><div className="private-card"><ShieldCheck size={21}/><div><strong>Your plan stays local</strong><span>Private by design</span></div></div><button className="user-card" onClick={()=>navigate('settings')}><span className="avatar">{state.profile.name.slice(0,1).toUpperCase()}</span><span><strong>{user.demo?'Demo workspace':state.profile.name}</strong><small>{user.demo?'Fictional sample data':'Personal account'}</small></span><ChevronRight size={17}/></button></div></aside>{mobile&&<div className="sidebar-overlay" onClick={()=>setMobile(false)}/>}
 <div className="main-shell"><header className="topbar"><div className="breadcrumbs"><button className="icon-btn mobile-menu" aria-label="Open navigation" onClick={()=>setMobile(true)}><Menu size={22}/></button><span>Workspace</span><ChevronRight size={14}/><strong>{NAV.find(x=>x[0]===page)?.[1]}</strong></div><div className="top-actions"><span className={`status-pill ${user.demo?'demo':''}`}><i/>{user.demo?'Demo mode':'Saved locally'}</span><button className="icon-btn" aria-label="Sign out" title="Sign out" onClick={async()=>{try{await post('/logout');setUser(null);setState(null);setPage('overview')}catch(e){notify(e.message,true)}}}><LogOut size={18}/></button></div></header><main className="main-content">{page==='overview'?<Overview {...common}/>:page==='health'?<FinancialHealth {...common}/>:page==='healthsetup'?<HealthSetup {...common}/>:page==='financials'?<Finances {...common}/>:page==='fire'?<FirePlanner {...common}/>:page==='projections'?<Simulator {...common}/>:page==='goals'?<Goals {...common}/>:page==='debt'?<DebtPlanner {...common}/>:page==='advisor'?<Advisor/>:page==='research'?<Research/>:page==='settings'?<SettingsPage {...common} onDeleted={()=>{setUser(null);setPage('overview')}}/>:<Reports {...common}/>}<footer className="footer"><span>wealthwise<span className="mint">.</span> <span className="footer-divider">/</span> AI Wealth Growth Planner</span><span>Educational planning · Assumptions, not promises</span></footer></main></div>{toast&&<div className={`toast ${toast.error?'error':''}`} role="status">{toast.error?<AlertTriangle size={18}/>:<Check size={18}/>} {toast.text}<button className="icon-btn" aria-label="Dismiss notification" onClick={()=>setToast(null)}><X size={16}/></button></div>}</div>
}
createRoot(document.getElementById('root')).render(<AppErrorBoundary><App/></AppErrorBoundary>);
