import React, { useState } from 'react';
import Modal from '../ui/Modal';
import { RegisterFormProps } from '../../../../core/contracts/template.contracts';

const Register: React.FC<RegisterFormProps> = ({ onClose, onSubmit, onLogin }) => {
  const { register, error: authError, clearError, isLoading: authLoading } = useAuth();
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [agreedToTerms, setAgreedToTerms] = useState(false);
  const [localError, setLocalError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLocalError('');
    
    if (!agreedToTerms) {
      setLocalError('Please accept the terms and conditions');
      return;
    }
    
    if (formData.password !== formData.confirmPassword) {
      setLocalError('Passwords do not match');
      return;
    }
    
    try {
      await register({
        first_name: formData.first_name,
        last_name: formData.last_name,
        email: formData.email,
        password: formData.password,
      });
      
      if (onSubmit) {
        await onSubmit(formData);
      }
      
      onClose();
    } catch (err: any) {
      setLocalError(err.message || 'Registration failed');
    }
  };

  const passwordsMatch = formData.password === formData.confirmPassword || !formData.confirmPassword;
  const isFormValid = formData.first_name && formData.last_name && formData.email && 
                      formData.password && formData.confirmPassword && 
                      passwordsMatch && agreedToTerms;

  return (
    <Modal isOpen onClose={onClose} title="Join the Movement">
      <div className="space-y-6">
        {/* Logo and Header */}
        <div className="text-center">
          <div className="flex justify-center mb-4">
            <div className="relative">
              <div className="text-6xl lion-glow" style={{ color: '#FCD34D' }}>
                🦁
              </div>
              <div className="absolute -bottom-2 left-1/2 transform -translate-x-1/2">
                <div className="flex space-x-1">
                  <div className="w-2 h-2 rounded-full bg-red-500"></div>
                  <div className="w-2 h-2 rounded-full bg-yellow-500"></div>
                  <div className="w-2 h-2 rounded-full bg-green-500"></div>
                </div>
              </div>
            </div>
          </div>
          <h2 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-red-500 via-yellow-400 to-green-500">
            JOIN THE MOVEMENT
          </h2>
          <p className="text-sm text-yellow-300 opacity-80 mt-2">
            Become Part of the Irie Family
          </p>
        </div>

        {/* Error Display */}
        {(localError || authError) && (
          <div className="p-3 rounded-lg bg-red-900/50 border border-red-500/50 text-red-300 text-sm">
            {localError || authError}
          </div>
        )}

        {/* Registration Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Name Fields */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-yellow-300 mb-2">
                First Name
              </label>
              <div className="relative">
                <input
                  type="text"
                  value={formData.first_name}
                  onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                  className="w-full px-4 py-3 bg-black/50 border-2 border-yellow-500/30 rounded-lg text-yellow-100 placeholder-yellow-700 focus:outline-none focus:border-yellow-400 focus:ring-2 focus:ring-yellow-400/20"
                  placeholder="First name"
                  required
                />
                <span className="absolute left-3 top-3.5 text-yellow-500">
                  👤
                </span>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-yellow-300 mb-2">
                Last Name
              </label>
              <div className="relative">
                <input
                  type="text"
                  value={formData.last_name}
                  onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                  className="w-full px-4 py-3 bg-black/50 border-2 border-yellow-500/30 rounded-lg text-yellow-100 placeholder-yellow-700 focus:outline-none focus:border-yellow-400 focus:ring-2 focus:ring-yellow-400/20"
                  placeholder="Last name"
                  required
                />
              </div>
            </div>
          </div>

          {/* Email Field */}
          <div>
            <label className="block text-sm font-medium text-yellow-300 mb-2">
              Email Address
            </label>
            <div className="relative">
              <input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className="w-full px-4 py-3 bg-black/50 border-2 border-yellow-500/30 rounded-lg text-yellow-100 placeholder-yellow-700 focus:outline-none focus:border-yellow-400 focus:ring-2 focus:ring-yellow-400/20"
                placeholder="your@email.com"
                required
              />
              <span className="absolute left-3 top-3.5 text-yellow-500">
                ✉️
              </span>
            </div>
          </div>

          {/* Password Field */}
          <div>
            <label className="block text-sm font-medium text-yellow-300 mb-2">
              Password
            </label>
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                className="w-full px-4 py-3 bg-black/50 border-2 border-yellow-500/30 rounded-lg text-yellow-100 placeholder-yellow-700 focus:outline-none focus:border-yellow-400 focus:ring-2 focus:ring-yellow-400/20 pr-12"
                placeholder="Create a strong password"
                required
              />
              <span className="absolute left-3 top-3.5 text-yellow-500">
                🔒
              </span>
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-3.5 text-yellow-500 hover:text-yellow-400"
              >
                {showPassword ? '👁️' : '👁️‍🗨️'}
              </button>
            </div>
          </div>

          {/* Confirm Password Field */}
          <div>
            <label className="block text-sm font-medium text-yellow-300 mb-2">
              Confirm Password
            </label>
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                value={formData.confirmPassword}
                onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
                className={`w-full px-4 py-3 bg-black/50 border-2 rounded-lg text-yellow-100 placeholder-yellow-700 focus:outline-none focus:ring-2 ${
                  !passwordsMatch && formData.confirmPassword
                    ? 'border-red-500/50 focus:border-red-400 focus:ring-red-400/20'
                    : 'border-yellow-500/30 focus:border-yellow-400 focus:ring-yellow-400/20'
                }`}
                placeholder="Repeat your password"
                required
              />
              <span className="absolute left-3 top-3.5">
                {!passwordsMatch && formData.confirmPassword ? '❌' : '✅'}
              </span>
            </div>
            {!passwordsMatch && formData.confirmPassword && (
              <p className="mt-1 text-xs text-red-400">
                Passwords do not match
              </p>
            )}
          </div>

          {/* Terms Agreement */}
          <div className="flex items-start space-x-2">
            <input
              type="checkbox"
              id="terms"
              checked={agreedToTerms}
              onChange={(e) => setAgreedToTerms(e.target.checked)}
              className="w-4 h-4 rounded border-yellow-500/30 bg-black/50 text-yellow-500 focus:ring-yellow-400/20 mt-1"
            />
            <label htmlFor="terms" className="text-sm text-yellow-300 cursor-pointer">
              I agree to spread love, peace, and positive vibes. I accept the{' '}
              <span className="text-green-400 hover:underline">
                Terms of Unity
              </span>{' '}
              and{' '}
              <span className="text-green-400 hover:underline">
                Privacy of the Movement
              </span>
            </label>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={authLoading || !isFormValid}
            className="w-full px-6 py-3 bg-gradient-to-r from-red-500 via-yellow-500 to-green-500 text-black font-bold rounded-lg hover:from-red-400 hover:via-yellow-400 hover:to-green-400 disabled:opacity-50 disabled:cursor-not-allowed transform transition-all hover:scale-105 active:scale-95"
          >
            {authLoading ? 'Creating Account...' : 'Join the Movement'}
          </button>
        </form>

        {/* Footer Links */}
        <div className="text-center space-y-2">
          <button
            onClick={onLogin}
            className="text-yellow-300 hover:text-yellow-200 text-sm"
          >
            Already have an account? <span className="font-bold">Sign In</span>
          </button>
          <div className="text-xs text-green-300 opacity-60">
            One Love • One Heart • One Destiny
          </div>
        </div>
      </div>
    </Modal>
  );
};

export default Register;