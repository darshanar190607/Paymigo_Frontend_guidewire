import React, { useState, useRef, useEffect } from 'react';
import { motion } from 'motion/react';
import { 
  User, 
  Shield, 
  CreditCard, 
  Edit2, 
  Save, 
  X, 
  Phone, 
  Mail, 
  MapPin, 
  Calendar, 
  CheckCircle2, 
  AlertCircle,
  Plus,
  Trash2,
  Zap,
  ShieldCheck,
  Camera,
  Loader2
} from 'lucide-react';
import { cn, formatCurrency } from '@/lib/utils';
import { useAuth } from '../App';
import { storage, auth } from '../firebase';
import { ref, uploadBytes, getDownloadURL } from 'firebase/storage';
import { updateProfile } from 'firebase/auth';

const Profile = () => {
  const { user } = useAuth();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(user?.photoURL || null);
  const [uploadStatus, setUploadStatus] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  const [personalInfo, setPersonalInfo] = useState({
    name: user?.displayName || 'Ravi Kumar',
    email: user?.email || 'ravi.k@delivery.com',
    phone: '+91 98765 43210',
    location: 'Chennai, Tamil Nadu',
    joinedDate: user?.metadata.creationTime ? new Date(user.metadata.creationTime).toLocaleDateString('en-US', { month: 'short', year: 'numeric' }) : 'Jan 2024',
    partnerId: user?.uid ? `PM-${user.uid.slice(0, 5).toUpperCase()}` : 'PM-88291'
  });

  useEffect(() => {
    if (user) {
      setPersonalInfo(prev => ({
        ...prev,
        name: user.displayName || prev.name,
        email: user.email || prev.email,
        joinedDate: user.metadata?.creationTime ? new Date(user.metadata.creationTime).toLocaleDateString('en-US', { month: 'short', year: 'numeric' }) : prev.joinedDate,
        partnerId: user.uid ? `PM-${user.uid.slice(0, 5).toUpperCase()}` : prev.partnerId
      }));
      setPreviewUrl(user.photoURL);
    }
  }, [user]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setPreviewUrl(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile || !user) return;

    setIsUploading(true);
    setUploadStatus(null);
    try {
      const storageRef = ref(storage, `profile_pictures/${user.uid}`);
      await uploadBytes(storageRef, selectedFile);
      const downloadURL = await getDownloadURL(storageRef);
      await updateProfile(user, { photoURL: downloadURL });
      setPreviewUrl(downloadURL);
      setSelectedFile(null);
      setUploadStatus({ type: 'success', message: 'Profile picture updated successfully!' });
    } catch (error) {
      console.error('Error uploading profile picture:', error);
      setUploadStatus({ type: 'error', message: 'Failed to upload profile picture. Please try again.' });
    } finally {
      setIsUploading(false);
    }
  };

  const [policyDetails, setPolicyDetails] = useState({
    planName: 'Pro',
    status: 'Active',
    premium: 119,
    coverage: 50000,
    nextRenewal: 'Mar 25, 2026',
    benefits: [
      'Rainfall Protection (Parametric)',
      'Income Loss Coverage',
      'AQI Protection'
    ]
  });

  const [paymentMethods, setPaymentMethods] = useState([
    { id: 1, type: 'UPI', detail: 'ravi.k@okaxis', isDefault: true },
    { id: 2, type: 'Bank', detail: 'HDFC Bank **** 4421', isDefault: false }
  ]);

  const handleSave = () => {
    setIsEditing(false);
    // In a real app, this would call an API
  };

  return (
    <div className="max-w-5xl mx-auto px-6 py-12">
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex flex-col md:flex-row justify-between items-start md:items-center mb-12 gap-6"
      >
        <div className="flex items-center gap-6">
          <div className="relative group">
            <div className="w-24 h-24 rounded-3xl bg-accent/10 flex items-center justify-center border-2 border-accent/20 overflow-hidden">
              {previewUrl ? (
                <img src={previewUrl} alt="Profile" className="w-full h-full object-cover" referrerPolicy="no-referrer" />
              ) : (
                <User className="w-12 h-12 text-accent" />
              )}
            </div>
            <button 
              onClick={() => fileInputRef.current?.click()}
              className="absolute -bottom-2 -right-2 p-2 bg-accent text-white rounded-xl shadow-lg hover:scale-110 transition-transform"
            >
              <Camera className="w-4 h-4" />
            </button>
            <input 
              type="file" 
              ref={fileInputRef} 
              onChange={handleFileChange} 
              className="hidden" 
              accept="image/*"
            />
          </div>
          <div>
            <h1 className="text-3xl font-display font-black text-text-primary">{personalInfo.name}</h1>
            <p className="text-text-secondary font-medium">Partner ID: {personalInfo.partnerId} • Joined {personalInfo.joinedDate}</p>
            {selectedFile && (
              <button
                onClick={handleUpload}
                disabled={isUploading}
                className="mt-2 flex items-center gap-2 px-3 py-1.5 bg-accent/10 text-accent rounded-lg text-xs font-bold hover:bg-accent/20 transition-all disabled:opacity-50"
              >
                {isUploading ? <Loader2 className="w-3 h-3 animate-spin" /> : <Save className="w-3 h-3" />}
                Save Photo
              </button>
            )}
            {uploadStatus && (
              <p className={cn(
                'mt-2 text-[11px] font-bold flex items-center gap-1',
                uploadStatus.type === 'success' ? 'text-success' : 'text-red-400'
              )}>
                {uploadStatus.type === 'success'
                  ? <CheckCircle2 className="w-3 h-3" />
                  : <AlertCircle className="w-3 h-3" />}
                {uploadStatus.message}
              </p>
            )}
          </div>
        </div>
        <button 
          onClick={() => isEditing ? handleSave() : setIsEditing(true)}
          className={cn(
            "flex items-center gap-2 px-6 py-3 rounded-2xl font-bold transition-all",
            isEditing 
              ? "bg-success text-white shadow-lg shadow-success/20" 
              : "bg-surface border border-border text-text-primary hover:bg-white"
          )}
        >
          {isEditing ? <><Save className="w-4 h-4" /> Save Changes</> : <><Edit2 className="w-4 h-4" /> Edit Profile</>}
        </button>
      </motion.div>

      <div className="grid lg:grid-cols-3 gap-8">
        {/* Personal Information */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="lg:col-span-2 space-y-8"
        >
          <div className="glass-card p-8">
            <h2 className="text-xl font-display font-bold mb-6 flex items-center gap-2">
              <User className="w-5 h-5 text-accent" /> Personal Information
            </h2>
            <div className="grid md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <label className="text-xs font-bold text-text-secondary uppercase tracking-widest">Full Name</label>
                {isEditing ? (
                  <input 
                    type="text" 
                    value={personalInfo.name} 
                    onChange={(e) => setPersonalInfo({...personalInfo, name: e.target.value})}
                    className="w-full px-4 py-3 rounded-xl border border-border focus:border-accent outline-none transition-all"
                  />
                ) : (
                  <p className="text-lg font-semibold">{personalInfo.name}</p>
                )}
              </div>
              <div className="space-y-2">
                <label className="text-xs font-bold text-text-secondary uppercase tracking-widest">Email Address</label>
                {isEditing ? (
                  <input 
                    type="email" 
                    value={personalInfo.email} 
                    onChange={(e) => setPersonalInfo({...personalInfo, email: e.target.value})}
                    className="w-full px-4 py-3 rounded-xl border border-border focus:border-accent outline-none transition-all"
                  />
                ) : (
                  <p className="text-lg font-semibold">{personalInfo.email}</p>
                )}
              </div>
              <div className="space-y-2">
                <label className="text-xs font-bold text-text-secondary uppercase tracking-widest">Phone Number</label>
                {isEditing ? (
                  <input 
                    type="text" 
                    value={personalInfo.phone} 
                    onChange={(e) => setPersonalInfo({...personalInfo, phone: e.target.value})}
                    className="w-full px-4 py-3 rounded-xl border border-border focus:border-accent outline-none transition-all"
                  />
                ) : (
                  <p className="text-lg font-semibold">{personalInfo.phone}</p>
                )}
              </div>
              <div className="space-y-2">
                <label className="text-xs font-bold text-text-secondary uppercase tracking-widest">Location</label>
                {isEditing ? (
                  <input 
                    type="text" 
                    value={personalInfo.location} 
                    onChange={(e) => setPersonalInfo({...personalInfo, location: e.target.value})}
                    className="w-full px-4 py-3 rounded-xl border border-border focus:border-accent outline-none transition-all"
                  />
                ) : (
                  <p className="text-lg font-semibold">{personalInfo.location}</p>
                )}
              </div>
            </div>
          </div>

          {/* Payment Methods */}
          <div className="glass-card p-8">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-display font-bold flex items-center gap-2">
                <CreditCard className="w-5 h-5 text-accent" /> Payment Methods
              </h2>
              <button className="text-accent text-sm font-bold flex items-center gap-1 hover:underline">
                <Plus className="w-4 h-4" /> Add New
              </button>
            </div>
            <div className="space-y-4">
              {paymentMethods.map((method) => (
                <div key={method.id} className="flex items-center justify-between p-4 rounded-2xl border border-border bg-surface/50">
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-xl bg-accent/5 flex items-center justify-center">
                      {method.type === 'UPI' ? <Zap className="w-5 h-5 text-accent" /> : <ShieldCheck className="w-5 h-5 text-accent" />}
                    </div>
                    <div>
                      <p className="font-bold text-text-primary">{method.detail}</p>
                      <p className="text-xs text-text-secondary font-medium uppercase tracking-widest">{method.type} {method.isDefault && '• Default'}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {!method.isDefault && <button className="p-2 text-text-secondary hover:text-danger transition-colors"><Trash2 className="w-4 h-4" /></button>}
                    <CheckCircle2 className={cn("w-5 h-5", method.isDefault ? "text-success" : "text-border")} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </motion.div>

        {/* Policy Details Sidebar */}
        <motion.div 
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
          className="space-y-8"
        >
          <div className="glass-card p-8 bg-accent text-white border-none overflow-hidden relative">
            <div className="absolute top-0 right-0 p-4 opacity-10">
              <Shield className="w-32 h-32 -mr-8 -mt-8" />
            </div>
            <div className="relative z-10">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/20 text-[10px] font-bold uppercase tracking-widest mb-4">
                Active Policy
              </div>
              <h3 className="text-2xl font-display font-black mb-2">{policyDetails.planName}</h3>
              <p className="text-white/80 text-sm mb-6 font-medium">Next renewal: {policyDetails.nextRenewal}</p>
              
              <div className="space-y-4 mb-8">
                <div className="flex justify-between items-center py-2 border-b border-white/10">
                  <span className="text-white/60 text-sm">Premium</span>
                  <span className="font-bold">{formatCurrency(policyDetails.premium)}/week</span>
                </div>
                <div className="flex justify-between items-center py-2 border-b border-white/10">
                  <span className="text-white/60 text-sm">Coverage</span>
                  <span className="font-bold">{formatCurrency(policyDetails.coverage)}</span>
                </div>
              </div>

              <div className="space-y-3">
                <p className="text-xs font-bold uppercase tracking-widest text-white/60">Key Benefits</p>
                {policyDetails.benefits.map((benefit, i) => (
                  <div key={i} className="flex items-center gap-2 text-sm font-medium">
                    <CheckCircle2 className="w-4 h-4 text-white" />
                    {benefit}
                  </div>
                ))}
              </div>

              <button className="w-full mt-8 py-4 bg-white text-accent rounded-xl font-bold hover:bg-white/90 transition-all">
                View Policy Document
              </button>
            </div>
          </div>

          <div className="glass-card p-8">
            <h3 className="text-lg font-display font-bold mb-4 flex items-center gap-2">
              <AlertCircle className="w-5 h-5 text-warning" /> Support
            </h3>
            <p className="text-sm text-text-secondary mb-6 leading-relaxed">
              Need help with your policy or account? Our support team is available 24/7 for delivery partners.
            </p>
            <button className="w-full py-3 border border-border rounded-xl font-bold text-sm hover:bg-surface transition-all">
              Contact Support
            </button>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default Profile;
