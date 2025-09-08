import React, { useState } from 'react';
import { useAuth } from '../../../../contexts/AuthContext';
import Button from '../ui/Button';
import Input from '../ui/Input';
import Modal from '../ui/Modal';
import Card from '../ui/Card';
import Badge from '../ui/Badge';
import { RegisterFormProps } from '../../../../core/contracts/template.contracts';

const Register: React.FC<RegisterFormProps> = ({ onClose, onSubmit, onLogin }) => {
  const { register, error: authError, clearError, isLoading: authLoading } = useAuth();
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phoneNumber: '',
    dateOfBirth: '',
    password: '',
    confirmPassword: '',
  });
  const [acceptTerms, setAcceptTerms] = useState(false);
  const [acceptMarketing, setAcceptMarketing] = useState(false);
  const [localError, setLocalError] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    setLocalError('');
    clearError();
  };

  const handleNextStep = () => {
    if (currentStep < 3) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handlePrevStep = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!acceptTerms) {
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
        phoneNumber: formData.phoneNumber,
        dateOfBirth: formData.dateOfBirth,
        password: formData.password,
      });
      
      // Call the parent onSubmit to handle any additional logic
      if (onSubmit) {
        await onSubmit({
          ...formData,
          acceptTerms,
          acceptMarketing,
        });
      }
      
      onClose();
    } catch (err: any) {
      setLocalError(err.message || 'Registration failed');
    }
  };

  const renderStepIndicator = () => (
    <div className="flex items-center justify-center mb-8">
      {[1, 2, 3].map((step) => (
        <React.Fragment key={step}>
          <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold ${
            step <= currentStep 
              ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white' 
              : 'bg-purple-100 text-purple-400'
          }`}>
            {step <= currentStep ? '🌿' : step}
          </div>
          {step < 3 && (
            <div className={`w-12 h-1 mx-2 ${
              step < currentStep ? 'bg-gradient-to-r from-purple-600 to-pink-600' : 'bg-purple-200'
            }`} />
          )}
        </React.Fragment>
      ))}
    </div>
  );

  const renderStep1 = () => (
    <div className="space-y-6">
      <div className="text-center">
        <div className="w-16 h-16 bg-gradient-to-br from-purple-100 to-pink-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <span className="text-2xl">👋</span>
        </div>
        <h3 className="text-xl font-bold text-purple-800 mb-2">Let's Get Started!</h3>
        <p className="text-purple-600">Tell us about yourself</p>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <Input
          label="First Name"
          value={formData.first_name}
          placeholder="Your first name"
          required
          onChange={(value) => handleInputChange('first_name', value)}
        />
        <Input
          label="Last Name"
          value={formData.last_name}
          placeholder="Your last name"
          required
          onChange={(value) => handleInputChange('last_name', value)}
        />
      </div>

      <Input
        type="email"
        label="Email Address"
        value={formData.email}
        placeholder="your@email.com"
        required
        onChange={(value) => handleInputChange('email', value)}
      />

      <Button
        onClick={handleNextStep}
        disabled={!formData.first_name || !formData.last_name || !formData.email}
        className="w-full"
        size="lg"
      >
        Continue 🌱
      </Button>
    </div>
  );

  const renderStep2 = () => (
    <div className="space-y-6">
      <div className="text-center">
        <div className="w-16 h-16 bg-gradient-to-br from-purple-100 to-pink-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <span className="text-2xl">📱</span>
        </div>
        <h3 className="text-xl font-bold text-purple-800 mb-2">Contact Details</h3>
        <p className="text-purple-600">We need this for age verification</p>
      </div>

      <Input
        type="tel"
        label="Phone Number"
        value={formData.phoneNumber}
        placeholder="(555) 123-4567"
        required
        onChange={(value) => handleInputChange('phoneNumber', value)}
      />

      <Input
        type="date"
        label="Date of Birth"
        value={formData.dateOfBirth}
        required
        onChange={(value) => handleInputChange('dateOfBirth', value)}
      />

      <Card variant="filled" className="p-4">
        <div className="flex items-start gap-3">
          <span className="text-xl">🔞</span>
          <div className="text-sm text-purple-800">
            <p className="font-semibold mb-1">Age Verification Required</p>
            <p className="text-xs">You must be 21 or older to use our services. This information helps us comply with local cannabis regulations.</p>
          </div>
        </div>
      </Card>

      <div className="flex gap-3">
        <Button
          variant="outline"
          onClick={handlePrevStep}
          className="flex-1"
        >
          ← Back
        </Button>
        <Button
          onClick={handleNextStep}
          disabled={!formData.phoneNumber || !formData.dateOfBirth}
          className="flex-1"
        >
          Continue 🌿
        </Button>
      </div>
    </div>
  );

  const renderStep3 = () => (
    <div className="space-y-6">
      <div className="text-center">
        <div className="w-16 h-16 bg-gradient-to-br from-purple-100 to-pink-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <span className="text-2xl">🔒</span>
        </div>
        <h3 className="text-xl font-bold text-purple-800 mb-2">Secure Your Account</h3>
        <p className="text-purple-600">Create a strong password</p>
      </div>

      <div className="space-y-4">
        <div className="relative">
          <Input
            type={showPassword ? 'text' : 'password'}
            label="Password"
            value={formData.password}
            placeholder="Create a secure password"
            required
            onChange={(value) => handleInputChange('password', value)}
          />
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute right-3 top-9 text-purple-600 hover:text-purple-800 transition-colors"
          >
            {showPassword ? '👁️' : '👁️‍🗨️'}
          </button>
        </div>

        <Input
          type="password"
          label="Confirm Password"
          value={formData.confirmPassword}
          placeholder="Confirm your password"
          required
          error={formData.confirmPassword && formData.password !== formData.confirmPassword ? "Passwords don't match" : ''}
          onChange={(value) => handleInputChange('confirmPassword', value)}
        />
      </div>

      <div className="space-y-4">
        <label className="flex items-start gap-3 cursor-pointer">
          <input
            type="checkbox"
            checked={acceptTerms}
            onChange={(e) => setAcceptTerms(e.target.checked)}
            className="w-5 h-5 text-purple-600 border-purple-300 rounded focus:ring-purple-500 mt-0.5"
          />
          <div className="text-sm">
            <span className="text-purple-700">I accept the </span>
            <button type="button" className="text-pink-600 hover:text-pink-700 font-semibold">
              Terms & Conditions
            </button>
            <span className="text-purple-700"> and </span>
            <button type="button" className="text-pink-600 hover:text-pink-700 font-semibold">
              Privacy Policy
            </button>
          </div>
        </label>

        <label className="flex items-start gap-3 cursor-pointer">
          <input
            type="checkbox"
            checked={acceptMarketing}
            onChange={(e) => setAcceptMarketing(e.target.checked)}
            className="w-5 h-5 text-purple-600 border-purple-300 rounded focus:ring-purple-500 mt-0.5"
          />
          <span className="text-sm text-purple-700">
            Send me exclusive deals, product updates, and cannabis education content 🌿
          </span>
        </label>
      </div>

      {(localError || authError) && (
        <Card variant="filled" className="p-4 bg-gradient-to-r from-red-100 to-red-50 border-red-300">
          <div className="flex items-center gap-2 text-red-700 text-sm">
            <span>⚠️</span>
            {localError || authError}
          </div>
        </Card>
      )}

      <div className="flex gap-3">
        <Button
          variant="outline"
          onClick={handlePrevStep}
          className="flex-1"
        >
          ← Back
        </Button>
        <Button
          type="submit"
          disabled={authLoading || !acceptTerms || formData.password !== formData.confirmPassword}
          loading={authLoading}
          className="flex-1"
        >
          {authLoading ? 'Creating Account...' : 'Join Pot Palace ✨'}
        </Button>
      </div>
    </div>
  );

  return (
    <Modal isOpen onClose={onClose} title="Join the Pot Palace Community">
      <div className="space-y-6">
        {renderStepIndicator()}
        
        <form onSubmit={handleSubmit}>
          {currentStep === 1 && renderStep1()}
          {currentStep === 2 && renderStep2()}
          {currentStep === 3 && renderStep3()}
        </form>

        {/* Login Link */}
        <div className="text-center pt-4 border-t border-purple-200">
          <p className="text-purple-600 mb-2">Already have an account?</p>
          <Button
            variant="ghost"
            onClick={() => {
              onClose();
              onLogin();
            }}
            className="w-full"
          >
            Sign In Instead 🚪
          </Button>
        </div>

      </div>
    </Modal>
  );
};

export default Register;