'use client';

import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Zap, Shield, Globe, ArrowRightLeft, Phone, Menu, X,
  Smartphone, Check, CreditCard, Receipt, QrCode, BarChart3,
  Wifi, Droplet, Tv, Lock, Fingerprint, Bell,
  Eye, EyeOff, ArrowUpRight, ArrowDownLeft,
  TrendingUp, Users, Home, Settings as SettingsIcon, LogOut, GraduationCap,
  Signal, Target, User, Search, LogIn, UserPlus, ChevronRight, ChevronDown,
  Download, Moon, Sun, HelpCircle, Languages, WifiOff, Plus, Filter, Copy,
  AlertTriangle, Clock, CheckCircle, XCircle, DollarSign, Activity, ShieldAlert
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Separator } from '@/components/ui/separator';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { PieChart, Pie, Cell, ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, LineChart, Line } from 'recharts';
import { toast, Toaster } from 'sonner';

import { useAuth } from '@/contexts/AuthContext';
import { transfersApi, contactsApi, analyticsApi, servicesApi, adminApi, walletApi, Transaction, Contact } from '@/lib/api';

const theme = { sun: '#F59E0B', grass: '#10B981', earth: '#78350F', sky: '#0EA5E9', night: '#1E293B' };
// eslint-disable-next-line @typescript-eslint/no-unused-vars
const _theme = theme; const _Phone = Phone; const _CreditCard = CreditCard; const _QrCode = QrCode; const _Lock = Lock; const _Search = Search; const _ChevronDown = ChevronDown; const _Download = Download; const _HelpCircle = HelpCircle; const _Languages = Languages; const _Plus = Plus; const _Filter = Filter; const _LineChart = LineChart; const _Line = Line;

type NavigationView = 'landing' | 'dashboard' | 'transfers' | 'services' | 'analytics' | 'account' | 'settings' | 'login' | 'register' | 'admin';

const formatCurrency = (amount: number, currency = 'XOF') => new Intl.NumberFormat('fr-FR', { style: 'decimal', minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(amount) + ' ' + currency;
const formatDate = (dateStr: string) => new Date(dateStr).toLocaleDateString('fr-FR', { day: 'numeric', month: 'short', year: 'numeric' });

const telecomOperators = [
  { id: 'orange', name: 'Orange Money', color: '#FF7900', logo: '🟠', apiId: 'orange_money' },
  { id: 'mtn', name: 'MTN Mobile Money', color: '#FFCC00', logo: '🟡', apiId: 'mtn_money' },
  { id: 'moov', name: 'Moov Money', color: '#0089CF', logo: '🔵', apiId: 'moov_money' },
  { id: 'telecel', name: 'Telecel Cash', color: '#E3001B', logo: '🔴', apiId: 'telecel_cash' },
];

const billCategories = [
  { id: 'electricity', name: 'Électricité', icon: Zap, color: 'text-amber-500', providers: ['NIGELEC', 'SENELEC', 'SODECI', 'CEET'] },
  { id: 'water', name: 'Eau', icon: Droplet, color: 'text-sky-500', providers: ['SDE', 'SODECI Eau', 'ONEE'] },
  { id: 'internet', name: 'Internet', icon: Wifi, color: 'text-violet-500', providers: ['Orange Fibre', 'Moov Fibre', 'Free', 'MTN Fibre'] },
  { id: 'tv', name: 'TV', icon: Tv, color: 'text-pink-500', providers: ['Canal+', 'StarTimes', 'DSTV', 'GoTV'] },
  { id: 'school', name: 'Scolarité', icon: GraduationCap, color: 'text-emerald-500', providers: ['École Privée', 'Université', 'Institut'] },
];

const features = [
  { icon: ArrowRightLeft, title: 'Transferts Instantanés', desc: "Envoyez de l'argent en quelques secondes vers n'importe quel numéro de téléphone", color: 'text-amber-500', bg: 'bg-amber-100' },
  { icon: Smartphone, title: 'Recharges & Factures', desc: 'Recharges téléphoniques et paiement de factures en un clic', color: 'text-sky-500', bg: 'bg-sky-100' },
  { icon: Shield, title: 'Sécurité Maximale', desc: 'Authentification biométrique, code PIN et cryptage bancaire', color: 'text-emerald-500', bg: 'bg-emerald-100' },
  { icon: WifiOff, title: 'Mode Hors Ligne', desc: "Continuez à utiliser l'app même sans connexion internet", color: 'text-violet-500', bg: 'bg-violet-100' },
  { icon: BarChart3, title: 'Analytics Intelligents', desc: 'Suivez vos dépenses et visualisez votre évolution financière', color: 'text-pink-500', bg: 'bg-pink-100' },
  { icon: Globe, title: 'Impact Africain', desc: "Conçu pour l'Afrique, par des Africains, avec des tarifs adaptés", color: 'text-orange-500', bg: 'bg-orange-100' },
];

const depositAmounts = [5000, 10000, 25000, 50000, 100000, 200000];
const withdrawAmounts = [5000, 10000, 25000, 50000, 100000, 200000];

const AntelopeLogo = ({ className = 'w-10 h-10' }: { className?: string }) => (
  <svg viewBox="0 0 64 64" className={className} fill="none" xmlns="http://www.w3.org/2000/svg" aria-label="AntelopePay Logo">
    <defs>
      <linearGradient id="hornGradient" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stopColor="#F59E0B" /><stop offset="100%" stopColor="#D97706" /></linearGradient>
      <linearGradient id="bodyGradient" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stopColor="#78350F" /><stop offset="100%" stopColor="#92400E" /></linearGradient>
    </defs>
    <path d="M20 12 Q14 4 18 20 Q20 18 20 12" fill="url(#hornGradient)" />
    <path d="M18 8 Q12 2 16 16 Q18 14 18 8" fill="#F59E0B" opacity="0.8" />
    <path d="M44 12 Q50 4 46 20 Q44 18 44 12" fill="url(#hornGradient)" />
    <path d="M46 8 Q52 2 48 16 Q46 14 46 8" fill="#F59E0B" opacity="0.8" />
    <ellipse cx="32" cy="36" rx="16" ry="20" fill="url(#bodyGradient)" />
    <ellipse cx="32" cy="38" rx="8" ry="12" fill="#A16207" opacity="0.5" />
    <circle cx="26" cy="32" r="3" fill="#1E293B" />
    <circle cx="38" cy="32" r="3" fill="#1E293B" />
    <circle cx="25" cy="31" r="1" fill="white" />
    <circle cx="37" cy="31" r="1" fill="white" />
    <ellipse cx="32" cy="46" rx="4" ry="3" fill="#451A03" />
    <ellipse cx="20" cy="24" rx="4" ry="6" fill="#78350F" transform="rotate(-30 20 24)" />
    <ellipse cx="44" cy="24" rx="4" ry="6" fill="#78350F" transform="rotate(30 44 24)" />
    <path d="M26 52 Q32 58 38 52" stroke="#78350F" strokeWidth="3" fill="none" />
  </svg>
);

interface AdminUser { id: string; phone: string; full_name: string | null; email: string | null; balance: number; is_active: boolean; is_verified: boolean; created_at: string; }
interface AdminStats { total_users: number; active_users: number; total_transactions: number; total_volume: number; pending_deposits: number; pending_withdrawals: number; fraud_alerts: number; }
interface PendingTransaction { id: string; type: string; user_name: string; user_phone: string; amount: number; operator: string; risk_level: number; created_at: string; }

export default function AntelopePayApp() {
  const { user, isAuthenticated, isLoading: authLoading, login, register, logout, refreshUser } = useAuth();
  const [currentView, setCurrentView] = useState<NavigationView>('landing');
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [showBalance, setShowBalance] = useState(true);
  const [isOnline, setIsOnline] = useState(true);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [dataLoading, setDataLoading] = useState(false);
  const [transferPhone, setTransferPhone] = useState('');
  const [transferAmount, setTransferAmount] = useState('');
  const [transferNote, setTransferNote] = useState('');
  const [transferPin, setTransferPin] = useState('');
  const [transferFee, setTransferFee] = useState(0);
  const [loginPhone, setLoginPhone] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [registerData, setRegisterData] = useState({ phone: '', password: '', full_name: '', email: '', country: '', pin: '' });
  const [detectingCountry, setDetectingCountry] = useState(false);
  const [activeServiceTab, setActiveServiceTab] = useState('recharges');
  const [selectedOperator, setSelectedOperator] = useState('');
  const [rechargePhone, setRechargePhone] = useState('');
  const [rechargeAmount, setRechargeAmount] = useState('');
  const [rechargeLoading, setRechargeLoading] = useState(false);
  const [analyticsPeriod, setAnalyticsPeriod] = useState('month');
  const [analyticsData, setAnalyticsData] = useState({ income: 0, expenses: 0, breakdown: [] as Array<{ category: string; amount: number; percentage: number }>, trend: [] as Array<{ month: string; income: number; expenses: number }> });
  const [settings, setSettings] = useState({ biometric: true, notifications: true, darkMode: false });
  const [showReceiveModal, setShowReceiveModal] = useState(false);
  const [receiveAmount, setReceiveAmount] = useState('');
  const [receiveNote, setReceiveNote] = useState('');
  const [showDepositModal, setShowDepositModal] = useState(false);
  const [depositMethod, setDepositMethod] = useState<string>('');
  const [depositAmount, setDepositAmount] = useState<string>('');
  const [depositPhone, setDepositPhone] = useState('');
  const [depositLoading, setDepositLoading] = useState(false);
  const [showWithdrawModal, setShowWithdrawModal] = useState(false);
  const [withdrawMethod, setWithdrawMethod] = useState<string>('');
  const [withdrawAmount, setWithdrawAmount] = useState<string>('');
  const [withdrawPhone, setWithdrawPhone] = useState('');
  const [withdrawLoading, setWithdrawLoading] = useState(false);
  const [adminStats, setAdminStats] = useState<AdminStats>({ total_users: 0, active_users: 0, total_transactions: 0, total_volume: 0, pending_deposits: 0, pending_withdrawals: 0, fraud_alerts: 0 });
  const [adminUsers, setAdminUsers] = useState<AdminUser[]>([]);
  const [pendingTransactions, setPendingTransactions] = useState<PendingTransaction[]>([]);
  const [adminLoading, setAdminLoading] = useState(false);
  const [adminSearchQuery, setAdminSearchQuery] = useState('');
  const receivedAmount = Math.max(0, parseFloat(transferAmount || '0') - transferFee);
  const isAdmin = user?.role === 'admin';

  const detectCountry = useCallback(async () => {
    if (!navigator.geolocation) return;
    setDetectingCountry(true);
    navigator.geolocation.getCurrentPosition(
      async (position) => {
        try {
          const { latitude, longitude } = position.coords;
          const response = await fetch(`https://api.bigdatacloud.net/data/reverse-geocode-client?latitude=${latitude}&longitude=${longitude}&localityLanguage=fr`);
          const data = await response.json();
          if (data.countryName) { setRegisterData(prev => ({ ...prev, country: data.countryName })); toast.success(`📍 Pays détecté : ${data.countryName}`); }
        } catch (error) { console.error('Erreur détection pays:', error); } finally { setDetectingCountry(false); }
      },
      (error) => { setDetectingCountry(false); if (error.code === 1) toast.info('Veuillez autoriser la géolocalisation'); },
      { enableHighAccuracy: false, timeout: 10000 }
    );
  }, []);

  useEffect(() => { const handleOnline = () => setIsOnline(true); const handleOffline = () => setIsOnline(false); window.addEventListener('online', handleOnline); window.addEventListener('offline', handleOffline); return () => { window.removeEventListener('online', handleOnline); window.removeEventListener('offline', handleOffline); }; }, []);
  useEffect(() => { if (settings.darkMode) { document.documentElement.classList.add('dark'); } else { document.documentElement.classList.remove('dark'); } }, [settings.darkMode]);
  useEffect(() => { if (isAuthenticated) { setCurrentView(isAdmin ? 'admin' : 'dashboard'); fetchData(); } }, [isAuthenticated]);
  useEffect(() => { const amount = parseFloat(transferAmount || '0'); if (amount > 0) { const fee = amount * 0.015; setTransferFee(Math.max(50, Math.min(2500, fee))); } else { setTransferFee(0); } }, [transferAmount]);
  useEffect(() => { if (currentView === 'register' && !registerData.country) { detectCountry(); } }, [currentView, detectCountry, registerData.country]);
  useEffect(() => { if (isAuthenticated && isAdmin && currentView === 'admin') { fetchAdminData(); } }, [isAuthenticated, isAdmin, currentView]);

  const fetchData = async () => {
    setDataLoading(true);
    try {
      const [txRes, contactsRes, summaryRes] = await Promise.all([
        transfersApi.getHistory({ page: 1, page_size: 20 }).catch(() => ({ success: false, data: undefined })),
        contactsApi.getAll().catch(() => ({ success: false, data: undefined })),
        analyticsApi.getSummary('month').catch(() => ({ success: false, data: undefined })),
      ]);
      if (txRes.success && txRes.data) setTransactions((txRes.data as { transactions?: Transaction[] }).transactions || []);
      if (contactsRes.success && contactsRes.data) setContacts((contactsRes.data as { contacts?: Contact[] }).contacts || []);
      if (summaryRes.success && summaryRes.data) {
        const summaryData = summaryRes.data as { income?: number; expenses?: number };
        setAnalyticsData(prev => ({ ...prev, income: summaryData.income || 0, expenses: summaryData.expenses || 0 }));
      }
    } catch (error) { console.error('Failed to fetch data:', error); } finally { setDataLoading(false); }
  };

  const fetchAdminData = async () => {
    setAdminLoading(true);
    try {
      const [dashboardRes, usersRes, pendingRes] = await Promise.all([
        adminApi.getDashboard().catch(() => ({ success: false, data: undefined })),
        adminApi.getUsers({ page: 1 }).catch(() => ({ success: false, data: undefined })),
        adminApi.getPendingTransactions().catch(() => ({ success: false, data: undefined })),
      ]);
      if (dashboardRes.success && dashboardRes.data) { const dashboardData = dashboardRes.data as { stats?: AdminStats }; if (dashboardData.stats) { setAdminStats(dashboardData.stats); } }
      if (usersRes.success && usersRes.data) { const usersData = usersRes.data as { users?: AdminUser[] }; if (usersData.users) { setAdminUsers(usersData.users); } }
      if (pendingRes.success && pendingRes.data) { const pendingData = pendingRes.data as { transactions?: PendingTransaction[] }; if (pendingData.transactions) { setPendingTransactions(pendingData.transactions); } }
    } catch (error) { console.error('Failed to fetch admin data:', error); } finally { setAdminLoading(false); }
  };

  const navItems: { id: NavigationView; label: string; icon: React.ElementType }[] = isAdmin ? [
    { id: 'admin', label: 'Dashboard Admin', icon: Shield }, { id: 'dashboard', label: 'Mon Espace', icon: Home }, { id: 'settings', label: 'Paramètres', icon: SettingsIcon },
  ] : [
    { id: 'dashboard', label: 'Accueil', icon: Home }, { id: 'transfers', label: 'Transferts', icon: ArrowRightLeft }, { id: 'services', label: 'Services', icon: Smartphone }, { id: 'analytics', label: 'Analytics', icon: BarChart3 }, { id: 'account', label: 'Mon Compte', icon: User }, { id: 'settings', label: 'Paramètres', icon: SettingsIcon },
  ];

  const handleLogin = useCallback(async () => {
    if (!loginPhone || !loginPassword) { toast.error('Veuillez remplir tous les champs'); return; }
    const success = await login(loginPhone, loginPassword);
    if (success) { toast.success('Bienvenue !'); } else { toast.error('Identifiants incorrects'); }
  }, [loginPhone, loginPassword, login]);

  const handleRegister = useCallback(async () => {
    if (!registerData.phone || !registerData.password) { toast.error('Veuillez remplir tous les champs obligatoires'); return; }
    const result = await register(registerData);
    if (result.success) { toast.success('Compte créé avec succès !'); const loginSuccess = await login(registerData.phone, registerData.password); if (!loginSuccess) setCurrentView('login'); } else { toast.error(result.message); }
  }, [registerData, register, login]);

  const handleLogout = useCallback(async () => { await logout(); setCurrentView('landing'); toast.info('Déconnexion réussie'); }, [logout]);

  const handleTransfer = useCallback(async () => {
    if (!transferPhone || !transferAmount || parseFloat(transferAmount) <= 0) { toast.error('Veuillez remplir tous les champs'); return; }
    if (parseFloat(transferAmount) > (user?.balance || 0)) { toast.error('Solde insuffisant'); return; }
    try {
      const response = await transfersApi.create({ recipient_phone: transferPhone, amount: parseFloat(transferAmount), pin: transferPin || '0000', source: 'balance', note: transferNote });
      if (response.success) { toast.success('Transfert effectué !'); setTransferPhone(''); setTransferAmount(''); setTransferNote(''); setTransferPin(''); fetchData(); refreshUser(); } else { toast.error(response.message || 'Erreur'); }
    } catch { toast.error('Erreur lors du transfert'); }
  }, [transferPhone, transferAmount, transferPin, transferNote, user, fetchData, refreshUser]);

  const handleRecharge = useCallback(async () => {
    if (!rechargePhone || !rechargeAmount || !selectedOperator) { toast.error('Veuillez remplir tous les champs'); return; }
    if (parseFloat(rechargeAmount) > (user?.balance || 0)) { toast.error('Solde insuffisant'); return; }
    setRechargeLoading(true);
    try {
      const response = await servicesApi.recharge({ phone: rechargePhone, amount: parseFloat(rechargeAmount), operator: selectedOperator as 'orange' | 'mtn' | 'moov' | 'telecel', pin: '0000' });
      if (response.success) { toast.success('Recharge effectuée !'); setRechargePhone(''); setRechargeAmount(''); setSelectedOperator(''); fetchData(); refreshUser(); } else { toast.error(response.message || 'Erreur'); }
    } catch { toast.error('Erreur lors de la recharge'); } finally { setRechargeLoading(false); }
  }, [rechargePhone, rechargeAmount, selectedOperator, user, fetchData, refreshUser]);

  const handleDeposit = useCallback(async () => {
    if (!depositMethod || !depositAmount || !depositPhone) { toast.error('Veuillez remplir tous les champs'); return; }
    setDepositLoading(true);
    try {
      const response = await walletApi.deposit({ amount: parseFloat(depositAmount), method: depositMethod, phone_number: depositPhone });
      if (response.success) { toast.success(`Dépôt de ${formatCurrency(parseFloat(depositAmount))} initié`); toast.info('Vous recevrez une confirmation par SMS'); setShowDepositModal(false); setDepositAmount(''); setDepositPhone(''); setDepositMethod(''); fetchData(); refreshUser(); } else { toast.error(response.message || 'Erreur lors du dépôt'); }
    } catch { toast.error('Erreur lors du dépôt'); } finally { setDepositLoading(false); }
  }, [depositMethod, depositAmount, depositPhone, fetchData, refreshUser]);

  const handleWithdraw = useCallback(async () => {
    if (!withdrawMethod || !withdrawAmount || !withdrawPhone) { toast.error('Veuillez remplir tous les champs'); return; }
    const amount = parseFloat(withdrawAmount);
    if (amount > (user?.balance || 0)) { toast.error('Solde insuffisant'); return; }
    if (amount < 500) { toast.error('Montant minimum: 500 XOF'); return; }
    setWithdrawLoading(true);
    try {
      const response = await walletApi.withdraw({ amount: amount, method: withdrawMethod, phone_number: withdrawPhone, pin: '0000' });
      if (response.success) { const fees = Math.max(50, amount * 0.01); toast.success(`Retrait de ${formatCurrency(amount - fees)} initié (frais: ${formatCurrency(fees)})`); toast.info('Vous recevrez l\'argent sur votre Mobile Money'); setShowWithdrawModal(false); setWithdrawAmount(''); setWithdrawPhone(''); setWithdrawMethod(''); fetchData(); refreshUser(); } else { toast.error(response.message || 'Erreur lors du retrait'); }
    } catch { toast.error('Erreur lors du retrait'); } finally { setWithdrawLoading(false); }
  }, [withdrawMethod, withdrawAmount, withdrawPhone, user, fetchData, refreshUser]);

  const handleValidateTransaction = useCallback(async (txId: string, action: 'approve' | 'reject') => {
    try { const response = await adminApi.validateTransaction(txId, action); if (response.success) { toast.success(`Transaction ${txId} ${action === 'approve' ? 'approuvée' : 'rejetée'}`); fetchAdminData(); refreshUser(); } else { toast.error(response.message || 'Erreur'); } } catch { toast.error('Erreur lors de la validation'); }
  }, [fetchAdminData, refreshUser]);

  const handleUpdateUser = useCallback(async (userId: string, data: { is_active?: boolean; is_verified?: boolean; balance?: number }) => {
    try { const response = await adminApi.updateUser(userId, data); if (response.success) { toast.success('Utilisateur mis à jour'); fetchAdminData(); } else { toast.error(response.message || 'Erreur'); } } catch { toast.error('Erreur lors de la mise à jour'); }
  }, [fetchAdminData]);

  if (authLoading) { return (<div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-amber-50 to-orange-50"><div className="text-center"><AntelopeLogo className="w-20 h-20 mx-auto animate-pulse" /><p className="mt-4 text-amber-600 font-medium">Chargement...</p></div></div>); }

  const renderHeader = () => (
    <motion.header initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="sticky top-0 z-50 bg-white/95 backdrop-blur-md border-b border-amber-100 shadow-sm">
      <div className="container mx-auto px-4 py-3">
        <div className="flex items-center justify-between">
          <button onClick={() => isAuthenticated ? setCurrentView(isAdmin ? 'admin' : 'dashboard') : setCurrentView('landing')} className="flex items-center gap-2 group">
            <AntelopeLogo className="w-9 h-9 group-hover:scale-110 transition-transform" />
            <span className="text-xl font-bold bg-gradient-to-r from-amber-600 to-orange-600 bg-clip-text text-transparent font-serif">AntelopePay</span>
          </button>
          <div className="hidden lg:flex items-center gap-3">
            {isAuthenticated ? (
              <div className="flex items-center gap-3">
                <Avatar className="h-9 w-9 border-2 border-amber-200"><AvatarFallback className="bg-gradient-to-br from-amber-500 to-orange-500 text-white font-semibold text-sm">{user?.full_name?.split(' ').map(n => n[0]).join('') || user?.phone?.slice(-2) || 'AP'}</AvatarFallback></Avatar>
                {isAdmin && (<Badge className="bg-amber-100 text-amber-700"><Shield className="w-3 h-3 mr-1" /> Admin</Badge>)}
                <Button variant="ghost" size="sm" onClick={handleLogout} className="text-slate-600 hover:text-red-600"><LogOut className="w-4 h-4 mr-2" />Déconnexion</Button>
              </div>
            ) : (
              <>
                <Button variant="ghost" className="text-slate-600 hover:text-amber-600" onClick={() => setCurrentView('login')}><LogIn className="w-4 h-4 mr-2" />Connexion</Button>
                <Button className="bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white shadow-lg shadow-amber-200" onClick={() => setCurrentView('register')}><UserPlus className="w-4 h-4 mr-2" />S'inscrire</Button>
              </>
            )}
          </div>
          <Button variant="ghost" size="icon" className="lg:hidden" onClick={() => setMobileMenuOpen(!mobileMenuOpen)}>{mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}</Button>
        </div>
      </div>
      <AnimatePresence>
        {mobileMenuOpen && (
          <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }} className="lg:hidden bg-white border-t border-amber-100">
            <nav className="container mx-auto px-4 py-4 space-y-2">
              {isAuthenticated ? navItems.map((item) => (<button key={item.id} onClick={() => { setCurrentView(item.id); setMobileMenuOpen(false) }} className={`flex items-center gap-3 w-full px-4 py-3 rounded-lg text-left ${currentView === item.id ? 'bg-amber-100 text-amber-700' : 'text-slate-600 hover:bg-amber-50'}`}><item.icon className="w-5 h-5" />{item.label}</button>)) : (<><Button variant="outline" className="w-full" onClick={() => { setCurrentView('login'); setMobileMenuOpen(false) }}>Se connecter</Button><Button className="w-full bg-gradient-to-r from-amber-500 to-orange-500 text-white" onClick={() => { setCurrentView('register'); setMobileMenuOpen(false) }}>Créer un compte</Button></>)}
            </nav>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.header>
  );

  const renderMobileTabBar = () => {
    if (!isAuthenticated) return null;
    return (
      <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-slate-200 z-50 lg:hidden">
        <div className="flex justify-around py-2">
          {navItems.slice(0, 5).map((item) => (<button key={item.id} onClick={() => setCurrentView(item.id)} className={`flex flex-col items-center gap-1 px-3 py-2 rounded-lg transition-colors ${currentView === item.id ? 'text-amber-600' : 'text-slate-500'}`}><item.icon className="w-5 h-5" /><span className="text-xs font-medium">{item.label}</span></button>))}
        </div>
      </div>
    );
  };

  const renderSidebar = () => {
    if (!isAuthenticated) return null;
    return (
      <aside className="hidden lg:flex flex-col w-64 bg-white border-r border-slate-200 min-h-screen p-4 sticky top-16">
        <nav className="space-y-2">{navItems.map((item) => (<button key={item.id} onClick={() => setCurrentView(item.id)} className={`flex items-center gap-3 w-full px-4 py-3 rounded-xl text-left transition-all ${currentView === item.id ? 'bg-gradient-to-r from-amber-500 to-orange-500 text-white shadow-lg' : 'text-slate-600 hover:bg-amber-50'}`}><item.icon className="w-5 h-5" /><span className="font-medium">{item.label}</span></button>))}</nav>
        <Card className="mt-4 bg-gradient-to-br from-amber-50 to-orange-50 border-amber-200"><CardContent className="p-4"><div className="flex items-center justify-between mb-2"><span className="text-xs text-slate-500">Solde Principal</span><button onClick={() => setShowBalance(!showBalance)} className="text-slate-400 hover:text-slate-600">{showBalance ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}</button></div><p className="text-lg font-bold text-amber-600">{showBalance ? formatCurrency(user?.balance || 0) : '••• ••• •••'}</p></CardContent></Card>
        <div className="mt-auto pt-6"><div className="flex items-center gap-3 px-4 py-2 rounded-lg bg-slate-100"><Avatar className="h-10 w-10"><AvatarFallback className="bg-gradient-to-br from-amber-500 to-orange-500 text-white">{user?.full_name?.split(' ').map(n => n[0]).join('') || 'AP'}</AvatarFallback></Avatar><div className="flex-1 min-w-0"><p className="font-medium text-slate-900 truncate">{user?.full_name || 'Utilisateur'}</p><p className="text-xs text-slate-500 truncate">{isAdmin ? 'Administrateur' : user?.email || user?.phone}</p></div></div><Button variant="ghost" size="sm" className="w-full mt-2 text-red-600 hover:bg-red-50" onClick={handleLogout}><LogOut className="w-4 h-4 mr-2" />Déconnexion</Button></div>
      </aside>
    );
  };

  const renderLogin = () => (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-amber-50 to-orange-50 p-4"><Card className="w-full max-w-md"><CardHeader className="text-center"><AntelopeLogo className="w-16 h-16 mx-auto mb-4" /><CardTitle className="text-2xl font-serif">Connexion</CardTitle><CardDescription>Connectez-vous à votre compte AntelopePay</CardDescription></CardHeader><CardContent className="space-y-4"><div><Label>Téléphone</Label><Input placeholder="+221 77 123 45 67" value={loginPhone} onChange={(e) => setLoginPhone(e.target.value)} /></div><div><Label>Mot de passe</Label><Input type="password" placeholder="••••••••" value={loginPassword} onChange={(e) => setLoginPassword(e.target.value)} /></div><Button className="w-full bg-gradient-to-r from-amber-500 to-orange-500" onClick={handleLogin}>Se connecter</Button><div className="text-center text-sm text-slate-500">Pas encore de compte ? <button onClick={() => setCurrentView('register')} className="text-amber-600 hover:underline">S'inscrire</button></div></CardContent></Card></div>
  );

  const renderRegister = () => (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-amber-50 to-orange-50 p-4"><Card className="w-full max-w-md"><CardHeader className="text-center"><AntelopeLogo className="w-16 h-16 mx-auto mb-4" /><CardTitle className="text-2xl font-serif">Créer un compte</CardTitle><CardDescription>Rejoignez AntelopePay en quelques secondes</CardDescription></CardHeader><CardContent className="space-y-4"><div><Label>Téléphone *</Label><Input placeholder="+221 77 123 45 67" value={registerData.phone} onChange={(e) => setRegisterData({ ...registerData, phone: e.target.value })} /></div><div><Label>Mot de passe *</Label><Input type="password" placeholder="••••••••" value={registerData.password} onChange={(e) => setRegisterData({ ...registerData, password: e.target.value })} /></div><div><Label>Nom complet</Label><Input placeholder="Amadou Diallo" value={registerData.full_name} onChange={(e) => setRegisterData({ ...registerData, full_name: e.target.value })} /></div><div><Label>Email</Label><Input type="email" placeholder="email@exemple.com" value={registerData.email} onChange={(e) => setRegisterData({ ...registerData, email: e.target.value })} /></div><div><Label>Pays</Label><div className="flex items-center gap-2"><Input value={registerData.country || (detectingCountry ? 'Détection en cours...' : 'Non détecté')} disabled className="bg-slate-100" /><Button type="button" variant="outline" size="icon" onClick={detectCountry} disabled={detectingCountry} title="Détecter ma position"><Globe className="w-4 h-4" /></Button></div></div><Button className="w-full bg-gradient-to-r from-amber-500 to-orange-500" onClick={handleRegister}>Créer mon compte</Button><div className="text-center text-sm text-slate-500">Déjà un compte ? <button onClick={() => setCurrentView('login')} className="text-amber-600 hover:underline">Se connecter</button></div></CardContent></Card></div>
  );

  const renderReceiveModal = () => {
    const qrData = JSON.stringify({ type: 'antelopepay', phone: user?.phone, name: user?.full_name, amount: receiveAmount || null, note: receiveNote || null });
    const handleCopyPhone = () => { navigator.clipboard.writeText(user?.phone || ''); toast.success('Numéro copié !'); };
    const handleShare = async () => { const shareText = `Envoyez-moi de l'argent via AntelopePay\nTéléphone: ${user?.phone}\n${receiveAmount ? `Montant: ${formatCurrency(parseFloat(receiveAmount))}\n` : ''}${receiveNote ? `Note: ${receiveNote}` : ''}`; if (navigator.share) { try { await navigator.share({ title: 'AntelopePay - Recevoir de l\'argent', text: shareText }); } catch { navigator.clipboard.writeText(shareText); toast.success('Informations copiées !'); } } else { navigator.clipboard.writeText(shareText); toast.success('Informations copiées !'); } };
    return (<Dialog open={showReceiveModal} onOpenChange={setShowReceiveModal}><DialogContent className="sm:max-w-md"><DialogHeader><DialogTitle className="flex items-center gap-2 text-emerald-600"><ArrowDownLeft className="w-5 h-5" />Recevoir de l&apos;argent</DialogTitle><DialogDescription>Partagez vos informations pour recevoir un paiement</DialogDescription></DialogHeader><div className="space-y-4"><div className="flex justify-center"><div className="bg-white rounded-xl p-3 border-2 border-emerald-200 shadow-lg"><img src={`https://api.qrserver.com/v1/create-qr-code/?size=180x180&data=${encodeURIComponent(qrData)}&color=047857&bgcolor=ffffff`} alt="QR Code" className="w-[180px] h-[180px]" /></div></div><Card className="bg-gradient-to-br from-emerald-50 to-teal-50 border-emerald-200"><CardContent className="p-4 space-y-3"><div className="flex items-center justify-between"><div><p className="text-sm text-slate-500">Nom</p><p className="font-semibold text-slate-900">{user?.full_name || 'Utilisateur'}</p></div><Avatar className="h-10 w-10"><AvatarFallback className="bg-gradient-to-br from-emerald-500 to-teal-500 text-white">{user?.full_name?.split(' ').map(n => n[0]).join('') || 'AP'}</AvatarFallback></Avatar></div><div className="flex items-center justify-between"><div><p className="text-sm text-slate-500">Téléphone AntelopePay</p><p className="font-semibold text-slate-900">{user?.phone}</p></div><Button variant="ghost" size="sm" onClick={handleCopyPhone}><Copy className="w-4 h-4" /></Button></div></CardContent></Card><div><Label>Montant demandé (optionnel)</Label><div className="flex gap-2 mt-1"><Input type="number" placeholder="Ex: 10000" value={receiveAmount} onChange={(e) => setReceiveAmount(e.target.value)} /><span className="flex items-center text-slate-500 font-medium px-2">XOF</span></div></div><div><Label>Note (optionnel)</Label><Input placeholder="Ex: Remboursement dinner" value={receiveNote} onChange={(e) => setReceiveNote(e.target.value)} /></div></div><DialogFooter className="flex-col gap-2 sm:flex-row"><Button variant="outline" onClick={() => { setReceiveAmount(''); setReceiveNote(''); setShowReceiveModal(false); }} className="w-full sm:w-auto">Fermer</Button><Button onClick={handleShare} className="w-full sm:w-auto bg-gradient-to-r from-emerald-500 to-teal-500"><Users className="w-4 h-4 mr-2" />Partager</Button></DialogFooter></DialogContent></Dialog>);
  };

  const renderDepositModal = () => (
    <Dialog open={showDepositModal} onOpenChange={setShowDepositModal}><DialogContent className="sm:max-w-md"><DialogHeader><DialogTitle className="flex items-center gap-2 text-emerald-600"><ArrowDownLeft className="w-5 h-5" />Déposer de l&apos;argent</DialogTitle><DialogDescription>Approvisionnez votre compte AntelopePay</DialogDescription></DialogHeader><div className="space-y-4"><div><Label>Méthode de dépôt</Label><Select value={depositMethod} onValueChange={setDepositMethod}><SelectTrigger className="mt-1"><SelectValue placeholder="Sélectionner une méthode" /></SelectTrigger><SelectContent>{telecomOperators.map((op) => (<SelectItem key={op.id} value={op.apiId}><span className="flex items-center gap-2"><span>{op.logo}</span><span>{op.name}</span></span></SelectItem>))}</SelectContent></Select></div>{depositMethod && (<div><Label>Numéro Mobile Money</Label><Input placeholder="Ex: 77 123 45 67" value={depositPhone} onChange={(e) => setDepositPhone(e.target.value)} className="mt-1" /></div>)}<div><Label>Montant à déposer</Label><div className="flex gap-2 mt-1"><Input type="number" placeholder="Ex: 10000" value={depositAmount} onChange={(e) => setDepositAmount(e.target.value)} /><span className="flex items-center text-slate-500 font-medium px-2">XOF</span></div></div><div className="grid grid-cols-3 gap-2">{depositAmounts.map((amount) => (<Button key={amount} variant="outline" size="sm" onClick={() => setDepositAmount(amount.toString())} className={depositAmount === amount.toString() ? 'border-amber-500 bg-amber-50' : ''}>{amount >= 1000 ? `${amount / 1000}k` : amount}</Button>))}</div>{depositAmount && parseFloat(depositAmount) > 0 && (<Card className="bg-gradient-to-br from-emerald-50 to-teal-50 border-emerald-200"><CardContent className="p-4"><div className="flex justify-between items-center"><div><p className="text-sm text-slate-500">Montant à créditer</p><p className="text-xl font-bold text-emerald-600">{formatCurrency(parseFloat(depositAmount))}</p></div><Badge className="bg-emerald-100 text-emerald-700">Sans frais</Badge></div></CardContent></Card>)}</div><DialogFooter className="flex-col gap-2 sm:flex-row"><Button variant="outline" onClick={() => { setDepositAmount(''); setDepositPhone(''); setDepositMethod(''); setShowDepositModal(false); }} className="w-full sm:w-auto">Annuler</Button><Button onClick={handleDeposit} disabled={depositLoading || !depositMethod || !depositAmount} className="w-full sm:w-auto bg-gradient-to-r from-emerald-500 to-teal-500">{depositLoading ? 'Traitement...' : 'Déposer'}</Button></DialogFooter></DialogContent></Dialog>
  );

  const renderWithdrawModal = () => {
    const withdrawFees = withdrawAmount ? Math.max(50, parseFloat(withdrawAmount) * 0.01) : 0;
    const netAmount = withdrawAmount ? Math.max(0, parseFloat(withdrawAmount) - withdrawFees) : 0;
    return (<Dialog open={showWithdrawModal} onOpenChange={setShowWithdrawModal}><DialogContent className="sm:max-w-md"><DialogHeader><DialogTitle className="flex items-center gap-2 text-red-600"><ArrowUpRight className="w-5 h-5" />Retirer de l&apos;argent</DialogTitle><DialogDescription>Transférez votre solde vers Mobile Money</DialogDescription></DialogHeader><div className="space-y-4"><Card className="bg-gradient-to-br from-amber-50 to-orange-50 border-amber-200"><CardContent className="p-3"><div className="flex justify-between items-center"><span className="text-sm text-slate-500">Solde disponible</span><span className="font-bold text-amber-600">{formatCurrency(user?.balance || 0)}</span></div></CardContent></Card><div><Label>Méthode de retrait</Label><Select value={withdrawMethod} onValueChange={setWithdrawMethod}><SelectTrigger className="mt-1"><SelectValue placeholder="Sélectionner une méthode" /></SelectTrigger><SelectContent>{telecomOperators.map((op) => (<SelectItem key={op.id} value={op.apiId}><span className="flex items-center gap-2"><span>{op.logo}</span><span>{op.name}</span></span></SelectItem>))}</SelectContent></Select></div>{withdrawMethod && (<div><Label>Numéro Mobile Money</Label><Input placeholder="Ex: 77 123 45 67" value={withdrawPhone} onChange={(e) => setWithdrawPhone(e.target.value)} className="mt-1" /></div>)}<div><Label>Montant à retirer</Label><div className="flex gap-2 mt-1"><Input type="number" placeholder="Ex: 10000" value={withdrawAmount} onChange={(e) => setWithdrawAmount(e.target.value)} /><span className="flex items-center text-slate-500 font-medium px-2">XOF</span></div></div><div className="grid grid-cols-3 gap-2">{withdrawAmounts.map((amount) => (<Button key={amount} variant="outline" size="sm" onClick={() => setWithdrawAmount(amount.toString())} disabled={amount > (user?.balance || 0)} className={withdrawAmount === amount.toString() ? 'border-red-500 bg-red-50' : ''}>{amount >= 1000 ? `${amount / 1000}k` : amount}</Button>))}</div>{withdrawAmount && parseFloat(withdrawAmount) > 0 && (<div className="p-4 bg-slate-50 rounded-lg space-y-2"><div className="flex justify-between text-sm"><span className="text-slate-600">Montant demandé</span><span className="font-medium">{formatCurrency(parseFloat(withdrawAmount))}</span></div><div className="flex justify-between text-sm"><span className="text-slate-600">Frais (1%)</span><span className="font-medium text-red-500">-{formatCurrency(withdrawFees)}</span></div><Separator /><div className="flex justify-between"><span className="font-medium">Montant reçu</span><span className="font-bold text-emerald-600">{formatCurrency(netAmount)}</span></div></div>)}</div><DialogFooter className="flex-col gap-2 sm:flex-row"><Button variant="outline" onClick={() => { setWithdrawAmount(''); setWithdrawPhone(''); setWithdrawMethod(''); setShowWithdrawModal(false); }} className="w-full sm:w-auto">Annuler</Button><Button onClick={handleWithdraw} disabled={withdrawLoading || !withdrawMethod || !withdrawAmount || parseFloat(withdrawAmount) > (user?.balance || 0)} className="w-full sm:w-auto bg-gradient-to-r from-red-500 to-pink-500">{withdrawLoading ? 'Traitement...' : 'Retirer'}</Button></DialogFooter></DialogContent></Dialog>);
  };

  const renderAdminDashboard = () => {
    const filteredUsers = adminSearchQuery ? adminUsers.filter(u => u.phone.includes(adminSearchQuery) || (u.full_name && u.full_name.toLowerCase().includes(adminSearchQuery.toLowerCase())) || (u.email && u.email.toLowerCase().includes(adminSearchQuery.toLowerCase()))) : adminUsers;
    return (<div className="flex flex-col lg:flex-row min-h-screen bg-slate-50">{renderSidebar()}<main className="flex-1 p-4 lg:p-6 pb-24 lg:pb-6"><div className="max-w-6xl mx-auto space-y-6"><div className="flex items-center justify-between"><div><h1 className="text-2xl font-bold text-slate-900 font-serif flex items-center gap-2"><Shield className="w-7 h-7 text-amber-500" />Panel Administrateur</h1><p className="text-slate-500">Gestion et supervision de la plateforme</p></div><Badge className="bg-amber-100 text-amber-700"><Activity className="w-3 h-3 mr-1" /> Admin</Badge></div>{adminLoading ? (<div className="text-center py-12"><AntelopeLogo className="w-16 h-16 mx-auto animate-pulse" /><p className="mt-4 text-slate-500">Chargement des données...</p></div>) : (<><div className="grid grid-cols-2 md:grid-cols-4 gap-4"><Card className="bg-gradient-to-br from-blue-500 to-indigo-600 text-white"><CardContent className="p-4"><div className="flex items-center justify-between"><Users className="w-8 h-8 text-blue-100" /><span className="text-xs bg-blue-400/30 px-2 py-1 rounded-full">Total</span></div><p className="text-2xl font-bold mt-2">{adminStats.total_users.toLocaleString()}</p><p className="text-blue-100 text-sm">Utilisateurs</p></CardContent></Card><Card className="bg-gradient-to-br from-emerald-500 to-teal-600 text-white"><CardContent className="p-4"><div className="flex items-center justify-between"><DollarSign className="w-8 h-8 text-emerald-100" /><span className="text-xs bg-emerald-400/30 px-2 py-1 rounded-full">Volume</span></div><p className="text-2xl font-bold mt-2">{formatCurrency(adminStats.total_volume)}</p><p className="text-emerald-100 text-sm">Volume Total</p></CardContent></Card><Card className="bg-gradient-to-br from-amber-500 to-orange-600 text-white"><CardContent className="p-4"><div className="flex items-center justify-between"><Receipt className="w-8 h-8 text-amber-100" /><span className="text-xs bg-amber-400/30 px-2 py-1 rounded-full">Total</span></div><p className="text-2xl font-bold mt-2">{adminStats.total_transactions.toLocaleString()}</p><p className="text-amber-100 text-sm">Transactions</p></CardContent></Card><Card className="bg-gradient-to-br from-red-500 to-pink-600 text-white"><CardContent className="p-4"><div className="flex items-center justify-between"><AlertTriangle className="w-8 h-8 text-red-100" /><span className="text-xs bg-red-400/30 px-2 py-1 rounded-full">Alerte</span></div><p className="text-2xl font-bold mt-2">{adminStats.fraud_alerts}</p><p className="text-red-100 text-sm">Alertes Fraude</p></CardContent></Card></div><Card><CardHeader className="flex flex-row items-center justify-between"><CardTitle className="flex items-center gap-2"><Clock className="w-5 h-5 text-amber-500" />Transactions en Attente</CardTitle><Badge variant="outline" className="text-amber-600 border-amber-200">{pendingTransactions.length} en attente</Badge></CardHeader><CardContent>{pendingTransactions.length === 0 ? (<div className="text-center py-8 text-slate-500"><CheckCircle className="w-12 h-12 mx-auto text-emerald-400 mb-3" /><p>Aucune transaction en attente</p></div>) : (<div className="space-y-3">{pendingTransactions.map((tx) => (<div key={tx.id} className={`p-4 rounded-lg border ${tx.risk_level > 0.8 ? 'bg-red-50 border-red-200' : tx.risk_level > 0.5 ? 'bg-amber-50 border-amber-200' : 'bg-slate-50 border-slate-200'}`}><div className="flex flex-col md:flex-row md:items-center justify-between gap-3"><div className="flex items-center gap-3"><div className={`w-10 h-10 rounded-full flex items-center justify-center ${tx.type === 'deposit' ? 'bg-emerald-100' : 'bg-red-100'}`}>{tx.type === 'deposit' ? <ArrowDownLeft className="w-5 h-5 text-emerald-500" /> : <ArrowUpRight className="w-5 h-5 text-red-500" />}</div><div><p className="font-medium text-slate-900">{tx.user_name || 'Utilisateur'}</p><p className="text-xs text-slate-500">{tx.user_phone} • {tx.operator}</p></div></div><div className="flex items-center gap-4"><div className="text-right"><p className="font-bold text-slate-900">{formatCurrency(tx.amount)}</p><p className="text-xs text-slate-500">{tx.type === 'deposit' ? 'Dépôt' : 'Retrait'}</p></div>{tx.risk_level > 0.8 && <Badge className="bg-red-100 text-red-700"><ShieldAlert className="w-3 h-3 mr-1" /> Risque Élevé</Badge>}{tx.risk_level > 0.5 && tx.risk_level <= 0.8 && <Badge className="bg-amber-100 text-amber-700"><AlertTriangle className="w-3 h-3 mr-1" /> Risque Moyen</Badge>}<div className="flex gap-2"><Button size="sm" variant="outline" className="text-emerald-600 hover:bg-emerald-50" onClick={() => handleValidateTransaction(tx.id, 'approve')}><CheckCircle className="w-4 h-4 mr-1" /> Valider</Button><Button size="sm" variant="outline" className="text-red-600 hover:bg-red-50" onClick={() => handleValidateTransaction(tx.id, 'reject')}><XCircle className="w-4 h-4 mr-1" /> Rejeter</Button></div></div></div></div>))}</div>)}</CardContent></Card><Card><CardHeader className="flex flex-row items-center justify-between"><CardTitle className="flex items-center gap-2"><Users className="w-5 h-5 text-blue-500" />Utilisateurs</CardTitle><div className="flex items-center gap-2"><Input placeholder="Rechercher..." value={adminSearchQuery} onChange={(e) => setAdminSearchQuery(e.target.value)} className="w-48" /><Button variant="outline" size="sm" onClick={fetchAdminData}>Rafraîchir</Button></div></CardHeader><CardContent>{adminUsers.length === 0 ? (<div className="text-center py-8 text-slate-500"><Users className="w-12 h-12 mx-auto text-slate-300 mb-3" /><p>Aucun utilisateur trouvé</p></div>) : (<div className="overflow-x-auto"><table className="w-full"><thead><tr className="border-b"><th className="text-left py-3 px-2 text-sm font-medium text-slate-500">Utilisateur</th><th className="text-left py-3 px-2 text-sm font-medium text-slate-500">Téléphone</th><th className="text-left py-3 px-2 text-sm font-medium text-slate-500">Solde</th><th className="text-left py-3 px-2 text-sm font-medium text-slate-500">Statut</th><th className="text-left py-3 px-2 text-sm font-medium text-slate-500">Date</th><th className="text-left py-3 px-2 text-sm font-medium text-slate-500">Actions</th></tr></thead><tbody>{filteredUsers.slice(0, 10).map((u) => (<tr key={u.id} className="border-b hover:bg-slate-50"><td className="py-3 px-2"><div className="flex items-center gap-2"><Avatar className="h-8 w-8"><AvatarFallback className="bg-gradient-to-br from-amber-500 to-orange-500 text-white text-xs">{(u.full_name || u.phone).split(' ').map(n => n[0]).join('').slice(0, 2)}</AvatarFallback></Avatar><div><p className="font-medium text-slate-900 text-sm">{u.full_name || 'N/A'}</p><p className="text-xs text-slate-500">{u.email || 'Pas d\'email'}</p></div></div></td><td className="py-3 px-2 text-sm text-slate-600">{u.phone}</td><td className="py-3 px-2 text-sm font-medium text-slate-900">{formatCurrency(u.balance)}</td><td className="py-3 px-2"><div className="flex flex-col gap-1"><Badge className={u.is_active ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'}>{u.is_active ? 'Actif' : 'Inactif'}</Badge>{u.is_verified && <Badge className="bg-blue-100 text-blue-700">Vérifié</Badge>}</div></td><td className="py-3 px-2 text-sm text-slate-500">{formatDate(u.created_at)}</td><td className="py-3 px-2"><div className="flex gap-1">{!u.is_verified && (<Button size="sm" variant="outline" className="text-blue-600 hover:bg-blue-50 text-xs" onClick={() => handleUpdateUser(u.id, { is_verified: true })}>Vérifier</Button>)}{u.is_active && (<Button size="sm" variant="outline" className="text-red-600 hover:bg-red-50 text-xs" onClick={() => handleUpdateUser(u.id, { is_active: false })}>Suspendre</Button>)}{!u.is_active && (<Button size="sm" variant="outline" className="text-emerald-600 hover:bg-emerald-50 text-xs" onClick={() => handleUpdateUser(u.id, { is_active: true })}>Réactiver</Button>)}</div></td></tr>))}</tbody></table></div>)}</CardContent></Card><div className="grid grid-cols-2 md:grid-cols-4 gap-4"><Card className="hover:shadow-lg transition-shadow cursor-pointer" onClick={fetchAdminData}><CardContent className="p-4 text-center"><Users className="w-8 h-8 mx-auto text-blue-500 mb-2" /><p className="font-medium text-slate-900">Gérer Users</p><p className="text-xs text-slate-500">{adminStats.total_users} utilisateurs</p></CardContent></Card><Card className="hover:shadow-lg transition-shadow cursor-pointer" onClick={fetchAdminData}><CardContent className="p-4 text-center"><Receipt className="w-8 h-8 mx-auto text-emerald-500 mb-2" /><p className="font-medium text-slate-900">Transactions</p><p className="text-xs text-slate-500">{adminStats.total_transactions} total</p></CardContent></Card><Card className="hover:shadow-lg transition-shadow cursor-pointer"><CardContent className="p-4 text-center"><ShieldAlert className="w-8 h-8 mx-auto text-red-500 mb-2" /><p className="font-medium text-slate-900">Anti-Fraude</p><p className="text-xs text-slate-500">{adminStats.fraud_alerts} alertes</p></CardContent></Card><Card className="hover:shadow-lg transition-shadow cursor-pointer"><CardContent className="p-4 text-center"><BarChart3 className="w-8 h-8 mx-auto text-violet-500 mb-2" /><p className="font-medium text-slate-900">Rapports</p><p className="text-xs text-slate-500">Statistiques</p></CardContent></Card></div></>)}</div></main></div>);
  };

  const renderAnalytics = () => {
    // FIX: Changed 'transfer' to 'recharge' and 'bill_payment' to match API types
    const expenseTransactions = transactions.filter(tx => tx.type === 'send' || tx.type === 'recharge' || tx.type === 'bill_payment');
    const expenseCategories = [
      { name: 'Transferts', value: expenseTransactions.filter(tx => tx.type === 'send').reduce((sum, tx) => sum + tx.amount, 0), color: '#F59E0B' },
      { name: 'Recharges', value: expenseTransactions.filter(tx => tx.type === 'recharge').reduce((sum, tx) => sum + tx.amount, 0), color: '#10B981' },
      { name: 'Factures', value: expenseTransactions.filter(tx => tx.type === 'bill_payment').reduce((sum, tx) => sum + tx.amount, 0), color: '#0EA5E9' },
      { name: 'Autres', value: Math.max(0, analyticsData.expenses - expenseTransactions.reduce((sum, tx) => sum + tx.amount, 0)), color: '#8B5CF6' },
    ].filter(cat => cat.value > 0);

    const trendData = analyticsData.trend.length > 0 ? analyticsData.trend : [
      { month: 'Jan', income: 150000, expenses: 120000 }, { month: 'Fév', income: 180000, expenses: 95000 }, { month: 'Mar', income: 125000, expenses: 140000 },
      { month: 'Avr', income: 200000, expenses: 110000 }, { month: 'Mai', income: 175000, expenses: 160000 }, { month: 'Juin', income: analyticsData.income || 0, expenses: analyticsData.expenses || 0 },
    ];
    const totalTransactions = transactions.length;
    const avgTransactionAmount = totalTransactions > 0 ? Math.round(transactions.reduce((sum, tx) => sum + tx.amount, 0) / totalTransactions) : 0;
    const savingsRate = analyticsData.income > 0 ? Math.round(((analyticsData.income - analyticsData.expenses) / analyticsData.income) * 100) : 0;
    const balance = analyticsData.income - analyticsData.expenses;
    return (<div className="flex flex-col lg:flex-row min-h-screen bg-slate-50">{renderSidebar()}<main className="flex-1 p-4 lg:p-6 pb-24 lg:pb-6"><div className="max-w-4xl mx-auto space-y-6"><div className="flex items-center justify-between"><div><h1 className="text-2xl font-bold text-slate-900 font-serif">Analytics</h1><p className="text-slate-500">Suivez vos dépenses et revenus</p></div><Select value={analyticsPeriod} onValueChange={setAnalyticsPeriod}><SelectTrigger className="w-32"><SelectValue /></SelectTrigger><SelectContent><SelectItem value="week">Semaine</SelectItem><SelectItem value="month">Mois</SelectItem><SelectItem value="year">Année</SelectItem></SelectContent></Select></div><div className="grid grid-cols-2 md:grid-cols-4 gap-4"><Card className="bg-gradient-to-br from-emerald-500 to-teal-500 text-white"><CardContent className="p-4"><div className="flex items-center gap-2 mb-1"><TrendingUp className="w-4 h-4 text-emerald-100" /><span className="text-emerald-100 text-sm">Revenus</span></div><p className="text-2xl font-bold">{formatCurrency(analyticsData.income)}</p><p className="text-emerald-100 text-xs mt-1">+12% vs mois dernier</p></CardContent></Card><Card className="bg-gradient-to-br from-red-500 to-pink-500 text-white"><CardContent className="p-4"><div className="flex items-center gap-2 mb-1"><ArrowUpRight className="w-4 h-4 text-red-100" /><span className="text-red-100 text-sm">Dépenses</span></div><p className="text-2xl font-bold">{formatCurrency(analyticsData.expenses)}</p><p className="text-red-100 text-xs mt-1">-5% vs mois dernier</p></CardContent></Card><Card className="bg-gradient-to-br from-amber-500 to-orange-500 text-white"><CardContent className="p-4"><div className="flex items-center gap-2 mb-1"><Target className="w-4 h-4 text-amber-100" /><span className="text-amber-100 text-sm">Épargne</span></div><p className="text-2xl font-bold">{savingsRate}%</p><p className="text-amber-100 text-xs mt-1">Taux d'épargne</p></CardContent></Card><Card className="bg-gradient-to-br from-violet-500 to-purple-500 text-white"><CardContent className="p-4"><div className="flex items-center gap-2 mb-1"><Receipt className="w-4 h-4 text-violet-100" /><span className="text-violet-100 text-sm">Transactions</span></div><p className="text-2xl font-bold">{totalTransactions}</p><p className="text-violet-100 text-xs mt-1">Moy: {formatCurrency(avgTransactionAmount)}</p></CardContent></Card></div><Card><CardContent className="p-4"><div className="flex items-center justify-between"><div><p className="text-sm text-slate-500">Solde net du mois</p><p className={`text-2xl font-bold ${balance >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>{balance >= 0 ? '+' : ''}{formatCurrency(balance)}</p></div><div className={`px-4 py-2 rounded-full ${balance >= 0 ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'}`}>{balance >= 0 ? '✓ Épargne positive' : '⚠ Dépenses supérieures'}</div></div></CardContent></Card><div className="grid grid-cols-1 md:grid-cols-2 gap-6"><Card><CardHeader><CardTitle className="text-lg flex items-center gap-2"><BarChart3 className="w-5 h-5 text-amber-500" />Répartition des dépenses</CardTitle></CardHeader><CardContent>{expenseCategories.length > 0 ? (<div className="h-64"><ResponsiveContainer width="100%" height="100%"><PieChart><Pie data={expenseCategories} cx="50%" cy="50%" innerRadius={60} outerRadius={90} paddingAngle={3} dataKey="value">{expenseCategories.map((entry, index) => (<Cell key={`cell-${index}`} fill={entry.color} />))}</Pie><Tooltip formatter={(value: number) => formatCurrency(value)} contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)' }} /></PieChart></ResponsiveContainer></div>) : (<div className="h-64 flex items-center justify-center text-slate-400">Aucune dépense ce mois</div>)}<div className="flex flex-wrap gap-3 mt-4 justify-center">{expenseCategories.map((cat, index) => (<div key={index} className="flex items-center gap-2"><div className="w-3 h-3 rounded-full" style={{ backgroundColor: cat.color }} /><span className="text-sm text-slate-600">{cat.name}</span></div>))}</div></CardContent></Card><Card><CardHeader><CardTitle className="text-lg flex items-center gap-2"><TrendingUp className="w-5 h-5 text-emerald-500" />Évolution mensuelle</CardTitle></CardHeader><CardContent><div className="h-64"><ResponsiveContainer width="100%" height="100%"><AreaChart data={trendData}><defs><linearGradient id="colorIncome" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#10B981" stopOpacity={0.3} /><stop offset="95%" stopColor="#10B981" stopOpacity={0} /></linearGradient><linearGradient id="colorExpenses" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#EF4444" stopOpacity={0.3} /><stop offset="95%" stopColor="#EF4444" stopOpacity={0} /></linearGradient></defs><XAxis dataKey="month" tick={{ fontSize: 12 }} tickLine={false} axisLine={false} /><YAxis tick={{ fontSize: 12 }} tickLine={false} axisLine={false} tickFormatter={(value) => `${(value / 1000)}k`} /><Tooltip formatter={(value: number) => formatCurrency(value)} contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)' }} /><Area type="monotone" dataKey="income" stroke="#10B981" strokeWidth={2} fillOpacity={1} fill="url(#colorIncome)" name="Revenus" /><Area type="monotone" dataKey="expenses" stroke="#EF4444" strokeWidth={2} fillOpacity={1} fill="url(#colorExpenses)" name="Dépenses" /></AreaChart></ResponsiveContainer></div></CardContent></Card></div><Card><CardHeader className="flex flex-row items-center justify-between"><CardTitle>Transactions récentes</CardTitle><Badge variant="outline" className="text-slate-500">{transactions.length} transactions</Badge></CardHeader><CardContent>{transactions.length === 0 ? (<div className="text-center py-8 text-slate-500">Aucune transaction</div>) : (<div className="space-y-3">{transactions.slice(0, 10).map((tx) => (<div key={tx.id} className="flex items-center justify-between p-3 rounded-lg bg-slate-100 hover:bg-slate-200 transition-colors"><div className="flex items-center gap-3"><div className={`w-10 h-10 rounded-full flex items-center justify-center ${tx.type === 'receive' ? 'bg-emerald-100' : 'bg-red-100'}`}>{tx.type === 'receive' ? <ArrowDownLeft className="w-5 h-5 text-emerald-500" /> : <ArrowUpRight className="w-5 h-5 text-red-500" />}</div><div><p className="font-medium text-slate-900">{tx.recipient_name || tx.recipient_phone || tx.type}</p><p className="text-xs text-slate-500">{formatDate(tx.created_at)}</p></div></div><p className={`font-semibold ${tx.type === 'receive' ? 'text-emerald-500' : 'text-slate-900'}`}>{tx.type === 'receive' ? '+' : '-'}{formatCurrency(tx.amount)}</p></div>))}</div>)}</CardContent></Card></div></main></div>);
  };

  const renderAccount = () => (
    <div className="flex flex-col lg:flex-row min-h-screen bg-slate-50">{renderSidebar()}<main className="flex-1 p-4 lg:p-6 pb-24 lg:pb-6"><div className="max-w-2xl mx-auto space-y-6"><h1 className="text-2xl font-bold text-slate-900 font-serif">Mon Compte</h1><Card><CardContent className="p-6"><div className="flex items-center gap-4"><Avatar className="h-20 w-20"><AvatarFallback className="bg-gradient-to-br from-amber-500 to-orange-500 text-white text-2xl">{user?.full_name?.split(' ').map(n => n[0]).join('') || 'AP'}</AvatarFallback></Avatar><div><h2 className="text-xl font-bold text-slate-900">{user?.full_name || 'Utilisateur'}</h2><p className="text-slate-500">{user?.email || user?.phone}</p>
                  {/* FIX: is_verified au lieu de isVerified */}
                  {user?.is_verified ? (<Badge className="mt-2 bg-emerald-100 text-emerald-700"><Check className="w-3 h-3 mr-1" /> Vérifié</Badge>) : (<Badge className="mt-2 bg-amber-100 text-amber-700">Non vérifié</Badge>)}
                </div></div></CardContent></Card><Card><CardHeader><CardTitle>Informations personnelles</CardTitle></CardHeader><CardContent className="space-y-4"><div className="flex justify-between py-2 border-b"><span className="text-slate-500">Téléphone</span><span className="font-medium">{user?.phone}</span></div><div className="flex justify-between py-2 border-b"><span className="text-slate-500">Email</span><span className="font-medium">{user?.email || '-'}</span></div><div className="flex justify-between py-2 border-b"><span className="text-slate-500">Pays</span><span className="font-medium">{user?.country || '-'}</span></div>
              {/* FIX: created_at au lieu de createdAt */}
              <div className="flex justify-between py-2"><span className="text-slate-500">Membre depuis</span><span className="font-medium">{user?.created_at ? formatDate(user.created_at) : '-'}</span></div>
            </CardContent></Card></div></main></div>
  );

  const renderSettings = () => (
    <div className="flex flex-col lg:flex-row min-h-screen bg-slate-50">{renderSidebar()}<main className="flex-1 p-4 lg:p-6 pb-24 lg:pb-6"><div className="max-w-2xl mx-auto space-y-6"><h1 className="text-2xl font-bold text-slate-900 font-serif">Paramètres</h1><Card><CardHeader><CardTitle>Sécurité</CardTitle></CardHeader><CardContent className="space-y-4"><div className="flex items-center justify-between"><div className="flex items-center gap-3"><Fingerprint className="w-5 h-5 text-slate-500" /><div><p className="font-medium">Authentification biométrique</p><p className="text-sm text-slate-500">Déverrouillage par empreinte digitale</p></div></div><Switch checked={settings.biometric} onCheckedChange={(checked) => setSettings({ ...settings, biometric: checked })} /></div></CardContent></Card><Card><CardHeader><CardTitle>Notifications</CardTitle></CardHeader><CardContent className="space-y-4"><div className="flex items-center justify-between"><div className="flex items-center gap-3"><Bell className="w-5 h-5 text-slate-500" /><div><p className="font-medium">Notifications push</p><p className="text-sm text-slate-500">Recevoir les alertes de transactions</p></div></div><Switch checked={settings.notifications} onCheckedChange={(checked) => setSettings({ ...settings, notifications: checked })} /></div></CardContent></Card><Card><CardHeader><CardTitle>Apparence</CardTitle></CardHeader><CardContent className="space-y-4"><div className="flex items-center justify-between"><div className="flex items-center gap-3">{settings.darkMode ? <Moon className="w-5 h-5 text-slate-500" /> : <Sun className="w-5 h-5 text-slate-500" />}<div><p className="font-medium">Mode sombre</p><p className="text-sm text-slate-500">Activer le thème sombre</p></div></div><Switch checked={settings.darkMode} onCheckedChange={(checked) => setSettings({ ...settings, darkMode: checked })} /></div></CardContent></Card><Card><CardContent className="p-4"><Button variant="destructive" className="w-full" onClick={handleLogout}><LogOut className="w-4 h-4 mr-2" />Déconnexion</Button></CardContent></Card></div></main></div>
  );

  const renderLanding = () => (
    <div className="flex flex-col">
      <section className="relative overflow-hidden py-12 lg:py-20 bg-gradient-to-b from-amber-50/50 to-white"><div className="container mx-auto px-4 relative z-10"><div className="grid lg:grid-cols-2 gap-10 items-center"><motion.div initial={{ opacity: 0, x: -30 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.6 }}><Badge className="mb-4 bg-amber-100 text-amber-700"><Globe className="w-3 h-3 mr-1" /> La fintech de l&apos;Afrique</Badge><h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-slate-900 leading-tight mb-4 font-serif">AntelopePay</h1><p className="text-xl md:text-2xl text-amber-600 font-medium mb-2">La rapidité de l&apos;antilope au service de vos finances</p><p className="text-2xl md:text-3xl font-bold text-slate-900 mb-6">Envoyez. Recevez. Prospérez.</p><p className="text-base text-slate-600 mb-8 max-w-lg">Transférez de l&apos;argent instantanément, payez vos factures et gérez votre argent en toute sécurité.</p><div className="flex flex-wrap gap-3 mb-8"><Button size="lg" onClick={() => setCurrentView('register')} className="bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white shadow-xl gap-2"><Zap className="w-5 h-5" />Ouvrir un compte gratuit</Button><Button size="lg" variant="outline" onClick={() => document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' })} className="gap-2">Découvrir l&apos;app</Button></div><div className="flex items-center gap-4 md:gap-6"><div className="text-center"><p className="text-2xl md:text-3xl font-bold text-slate-900">150+</p><p className="text-sm text-slate-500">Pays</p></div><div className="w-px h-12 bg-slate-200" /><div className="text-center"><p className="text-2xl md:text-3xl font-bold text-slate-900">2M+</p><p className="text-sm text-slate-500">Utilisateurs</p></div><div className="w-px h-12 bg-slate-200" /><div className="text-center"><p className="text-2xl md:text-3xl font-bold text-slate-900">99.9%</p><p className="text-sm text-slate-500">Disponibilité</p></div></div></motion.div><motion.div initial={{ opacity: 0, x: 30 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.6, delay: 0.2 }} className="relative flex justify-center"><div className="relative w-80 h-80 md:w-96 md:h-96"><div className="absolute inset-0 bg-gradient-to-br from-amber-200/30 via-orange-200/20 to-emerald-200/30 rounded-3xl" /><AntelopeLogo className="w-full h-full p-8" /></div></motion.div></div></div></section><section id="features" className="py-16 bg-white"><div className="container mx-auto px-4"><div className="text-center mb-12"><h2 className="text-3xl md:text-4xl font-bold text-slate-900 mb-4 font-serif">Pourquoi choisir AntelopePay ?</h2><p className="text-slate-600 max-w-2xl mx-auto">Une solution complète pour tous vos besoins financiers.</p></div><div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">{features.map((feature, index) => (<Card key={index} className="hover:shadow-lg transition-shadow"><CardContent className="p-6"><div className={`w-12 h-12 rounded-xl ${feature.bg} flex items-center justify-center mb-4`}><feature.icon className={`w-6 h-6 ${feature.color}`} /></div><h3 className="text-lg font-semibold text-slate-900 mb-2">{feature.title}</h3><p className="text-slate-600">{feature.desc}</p></CardContent></Card>))}</div></div></section><section className="py-16 bg-gradient-to-r from-amber-500 to-orange-500"><div className="container mx-auto px-4 text-center"><h2 className="text-3xl md:text-4xl font-bold text-white mb-4 font-serif">Prêt à commencer ?</h2><p className="text-amber-100 mb-8 max-w-2xl mx-auto">Ouvrez votre compte en moins de 2 minutes.</p><Button size="lg" variant="secondary" onClick={() => setCurrentView('register')} className="bg-white text-amber-600 hover:bg-amber-50">Créer un compte gratuit</Button></div></section><footer className="py-12 bg-slate-900 text-white"><div className="container mx-auto px-4"><div className="flex flex-col md:flex-row items-center justify-between gap-6"><div className="flex items-center gap-2"><AntelopeLogo className="w-8 h-8" /><span className="text-xl font-bold font-serif">AntelopePay</span></div><p className="text-slate-400 text-sm">© 2026 AntelopePay. Tous droits réservés.</p></div></div></footer></div>
  );

  const renderDashboard = () => (
    <div className="flex flex-col lg:flex-row min-h-screen bg-slate-50">{renderSidebar()}<main className="flex-1 p-4 lg:p-6 pb-24 lg:pb-6"><div className="max-w-4xl mx-auto space-y-6"><div className="flex items-center justify-between"><div><h1 className="text-2xl font-bold text-slate-900 font-serif">Bonjour, {user?.full_name?.split(' ')[0] || 'Bienvenue'} 👋</h1><p className="text-slate-500">Voici votre vue d'ensemble</p></div><Badge className={isOnline ? "bg-emerald-100 text-emerald-700" : "bg-red-100 text-red-700"}>{isOnline ? <><Signal className="w-3 h-3 mr-1" /> En ligne</> : <><WifiOff className="w-3 h-3 mr-1" /> Hors ligne</>}</Badge></div><div className="grid grid-cols-1 md:grid-cols-2 gap-4"><Card className="bg-gradient-to-br from-amber-500 to-orange-500 text-white"><CardContent className="p-6"><div className="flex items-center justify-between mb-4"><span className="text-amber-100">Solde Principal</span><button onClick={() => setShowBalance(!showBalance)}>{showBalance ? <Eye className="w-5 h-5" /> : <EyeOff className="w-5 h-5" />}</button></div><p className="text-3xl font-bold">{showBalance ? formatCurrency(user?.balance || 0) : '••• ••• •••'}</p><div className="flex gap-2 mt-4"><Button size="sm" variant="secondary" className="bg-white/20 hover:bg-white/30 text-white" onClick={() => setShowDepositModal(true)}><ArrowDownLeft className="w-4 h-4 mr-1" /> Déposer</Button><Button size="sm" variant="secondary" className="bg-white/20 hover:bg-white/30 text-white" onClick={() => setShowWithdrawModal(true)}><ArrowUpRight className="w-4 h-4 mr-1" /> Retirer</Button></div></CardContent></Card><Card className="bg-gradient-to-br from-emerald-500 to-teal-500 text-white"><CardContent className="p-6"><div className="flex items-center justify-between mb-4"><span className="text-emerald-100">Épargne</span><Target className="w-5 h-5" /></div><p className="text-3xl font-bold">{showBalance ? formatCurrency(user?.savings || 0) : '••• ••• •••'}</p></CardContent></Card></div><Card><CardHeader><CardTitle className="text-lg">Actions Rapides</CardTitle></CardHeader><CardContent><div className="grid grid-cols-3 md:grid-cols-6 gap-3">{[{ icon: ArrowDownLeft, label: 'Déposer', color: 'text-emerald-500', bg: 'bg-emerald-100', action: () => setShowDepositModal(true) }, { icon: ArrowUpRight, label: 'Retirer', color: 'text-red-500', bg: 'bg-red-100', action: () => setShowWithdrawModal(true) }, { icon: ArrowUpRight, label: 'Envoyer', color: 'text-amber-500', bg: 'bg-amber-100', action: () => setCurrentView('transfers') }, { icon: ArrowDownLeft, label: 'Recevoir', color: 'text-teal-500', bg: 'bg-teal-100', action: () => setShowReceiveModal(true) }, { icon: Smartphone, label: 'Services', color: 'text-sky-500', bg: 'bg-sky-100', action: () => setCurrentView('services') }, { icon: BarChart3, label: 'Analytics', color: 'text-violet-500', bg: 'bg-violet-100', action: () => setCurrentView('analytics') }].map((action, i) => (<button key={i} onClick={action.action} className="flex flex-col items-center gap-2 p-3 rounded-xl bg-slate-100 hover:bg-slate-200 transition-colors"><div className={`w-10 h-10 rounded-full ${action.bg} flex items-center justify-center`}><action.icon className={`w-5 h-5 ${action.color}`} /></div><span className="text-xs font-medium text-slate-700">{action.label}</span></button>))}</div></CardContent></Card><Card><CardHeader className="flex flex-row items-center justify-between"><CardTitle className="text-lg">Transactions Récentes</CardTitle><Button variant="ghost" size="sm" onClick={() => setCurrentView('analytics')}>Voir tout <ChevronRight className="w-4 h-4 ml-1" /></Button></CardHeader><CardContent>{dataLoading ? (<div className="text-center py-8 text-slate-500">Chargement...</div>) : transactions.length === 0 ? (<div className="text-center py-8"><Receipt className="w-12 h-12 mx-auto text-slate-300 mb-3" /><p className="text-slate-500 mb-2">Aucune transaction</p><p className="text-sm text-slate-400">Déposez de l'argent pour commencer</p><Button className="mt-4 bg-gradient-to-r from-emerald-500 to-teal-500" onClick={() => setShowDepositModal(true)}><ArrowDownLeft className="w-4 h-4 mr-2" /> Faire un dépôt</Button></div>) : (<div className="space-y-3">{transactions.slice(0, 5).map((tx) => (<div key={tx.id} className="flex items-center justify-between p-3 rounded-lg bg-slate-100"><div className="flex items-center gap-3"><div className={`w-10 h-10 rounded-full flex items-center justify-center ${tx.type === 'receive' ? 'bg-emerald-100' : 'bg-red-100'}`}>{tx.type === 'receive' ? <ArrowDownLeft className="w-5 h-5 text-emerald-500" /> : <ArrowUpRight className="w-5 h-5 text-red-500" />}</div><div><p className="font-medium text-slate-900">{tx.recipient_name || tx.recipient_phone || 'Transfert'}</p><p className="text-xs text-slate-500">{formatDate(tx.created_at)}</p></div></div><p className={`font-semibold ${tx.type === 'receive' ? 'text-emerald-500' : 'text-slate-900'}`}>{tx.type === 'receive' ? '+' : '-'}{formatCurrency(tx.amount)}</p></div>))}</div>)}</CardContent></Card></div></main></div>
  );

  const renderTransfers = () => (
    <div className="flex flex-col lg:flex-row min-h-screen bg-slate-50">{renderSidebar()}<main className="flex-1 p-4 lg:p-6 pb-24 lg:pb-6"><div className="max-w-2xl mx-auto space-y-6"><div><h1 className="text-2xl font-bold text-slate-900 font-serif">Envoyer de l'argent</h1><p className="text-slate-500">Transférez instantanément vers n'importe quel numéro</p></div><Card><CardHeader><CardTitle>Nouveau transfert</CardTitle></CardHeader><CardContent className="space-y-4"><div><Label>Numéro du destinataire</Label><Input placeholder="+221 77 123 45 67" value={transferPhone} onChange={(e) => setTransferPhone(e.target.value)} /></div><div><Label>Montant (XOF)</Label><Input type="number" placeholder="10000" value={transferAmount} onChange={(e) => setTransferAmount(e.target.value)} /></div>{parseFloat(transferAmount) > 0 && (<div className="p-4 bg-amber-50 rounded-lg space-y-2"><div className="flex justify-between text-sm"><span className="text-slate-600">Montant</span><span className="font-medium">{formatCurrency(parseFloat(transferAmount))}</span></div><div className="flex justify-between text-sm"><span className="text-slate-600">Frais (1.5%)</span><span className="font-medium text-red-500">-{formatCurrency(transferFee)}</span></div><Separator /><div className="flex justify-between"><span className="font-medium">Reçu par le destinataire</span><span className="font-bold text-emerald-600">{formatCurrency(receivedAmount)}</span></div></div>)}<div><Label>Note (optionnel)</Label><Input placeholder="Ex: Remboursement" value={transferNote} onChange={(e) => setTransferNote(e.target.value)} /></div><div><Label>Code PIN</Label><Input type="password" placeholder="••••" value={transferPin} onChange={(e) => setTransferPin(e.target.value)} maxLength={4} /></div><Button className="w-full bg-gradient-to-r from-amber-500 to-orange-500" onClick={handleTransfer}><ArrowUpRight className="w-4 h-4 mr-2" />Envoyer</Button></CardContent></Card></div></main></div>
  );

  const renderServices = () => (
    <div className="flex flex-col lg:flex-row min-h-screen bg-slate-50">{renderSidebar()}<main className="flex-1 p-4 lg:p-6 pb-24 lg:pb-6"><div className="max-w-2xl mx-auto space-y-6"><div><h1 className="text-2xl font-bold text-slate-900 font-serif">Services</h1><p className="text-slate-500">Recharges téléphoniques et paiement de factures</p></div><Tabs value={activeServiceTab} onValueChange={setActiveServiceTab}><TabsList className="grid w-full grid-cols-2"><TabsTrigger value="recharges">Recharges</TabsTrigger><TabsTrigger value="bills">Factures</TabsTrigger></TabsList><TabsContent value="recharges" className="space-y-4 mt-4"><Card><CardHeader><CardTitle>Recharge téléphonique</CardTitle></CardHeader><CardContent className="space-y-4"><div><Label>Opérateur</Label><Select value={selectedOperator} onValueChange={setSelectedOperator}><SelectTrigger><SelectValue placeholder="Sélectionner un opérateur" /></SelectTrigger><SelectContent>{telecomOperators.map((op) => (<SelectItem key={op.id} value={op.id}><span className="flex items-center gap-2"><span>{op.logo}</span><span>{op.name}</span></span></SelectItem>))}</SelectContent></Select></div><div><Label>Numéro de téléphone</Label><Input placeholder="+221 77 123 45 67" value={rechargePhone} onChange={(e) => setRechargePhone(e.target.value)} /></div><div><Label>Montant (XOF)</Label><Input type="number" placeholder="1000" value={rechargeAmount} onChange={(e) => setRechargeAmount(e.target.value)} /></div><Button className="w-full bg-gradient-to-r from-amber-500 to-orange-500" onClick={handleRecharge} disabled={rechargeLoading}><Smartphone className="w-4 h-4 mr-2" />{rechargeLoading ? 'Traitement...' : 'Recharger'}</Button></CardContent></Card><div className="grid grid-cols-2 md:grid-cols-4 gap-3">{[500, 1000, 2000, 5000, 10000, 15000, 20000, 50000].map((amount) => (<Button key={amount} variant="outline" onClick={() => setRechargeAmount(amount.toString())}>{formatCurrency(amount)}</Button>))}</div></TabsContent><TabsContent value="bills" className="space-y-4 mt-4"><Card><CardHeader><CardTitle>Paiement de factures</CardTitle></CardHeader><CardContent><div className="grid grid-cols-2 md:grid-cols-3 gap-4">{billCategories.map((category) => (<button key={category.id} className="flex flex-col items-center gap-2 p-4 rounded-xl bg-slate-100 hover:bg-slate-200 transition-colors"><category.icon className={`w-8 h-8 ${category.color}`} /><span className="text-sm font-medium text-slate-700">{category.name}</span></button>))}</div><p className="text-center text-slate-500 mt-4">Sélectionnez une catégorie pour continuer</p></CardContent></Card></TabsContent></Tabs></div></main></div>
  );

  return (
    <div className={`min-h-screen ${settings.darkMode ? 'dark' : ''}`}>
      <div className="min-h-screen bg-white dark:bg-slate-900">
        <Toaster position="top-center" />
        {currentView !== 'login' && currentView !== 'register' && renderHeader()}
        <AnimatePresence mode="wait">
          {!isAuthenticated && currentView === 'landing' && (<motion.div key="landing" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>{renderLanding()}</motion.div>)}
          {!isAuthenticated && currentView === 'login' && (<motion.div key="login" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>{renderLogin()}</motion.div>)}
          {!isAuthenticated && currentView === 'register' && (<motion.div key="register" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>{renderRegister()}</motion.div>)}
          {isAuthenticated && currentView === 'dashboard' && (<motion.div key="dashboard" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>{renderDashboard()}</motion.div>)}
          {isAuthenticated && currentView === 'transfers' && (<motion.div key="transfers" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>{renderTransfers()}</motion.div>)}
          {isAuthenticated && currentView === 'services' && (<motion.div key="services" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>{renderServices()}</motion.div>)}
          {isAuthenticated && currentView === 'analytics' && (<motion.div key="analytics" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>{renderAnalytics()}</motion.div>)}
          {isAuthenticated && currentView === 'account' && (<motion.div key="account" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>{renderAccount()}</motion.div>)}
          {isAuthenticated && currentView === 'settings' && (<motion.div key="settings" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>{renderSettings()}</motion.div>)}
          {isAuthenticated && currentView === 'admin' && (<motion.div key="admin" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>{renderAdminDashboard()}</motion.div>)}
        </AnimatePresence>
        {renderMobileTabBar()}
        {showReceiveModal && renderReceiveModal()}
        {showDepositModal && renderDepositModal()}
        {showWithdrawModal && renderWithdrawModal()}
      </div>
    </div>
  );
}