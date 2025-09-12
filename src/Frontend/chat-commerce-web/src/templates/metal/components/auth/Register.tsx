import React, { useState } from 'react';
import Button from '../ui/Button';
import Input from '../ui/Input';
import Modal from '../ui/Modal';
import Card from '../ui/Card';
import Badge from '../ui/Badge';
import { RegisterFormProps } from '../../../../core/contracts/template.contracts';
import { useAuth } from '../../../../contexts/AuthContext';

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
      setLocalError('Terms acceptance required');
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
          <div className={`w-12 h-12 flex items-center justify-center font-black text-lg border-4 ${
            step <= currentStep 
              ? 'bg-gradient-to-br from-red-600 to-red-800 text-white border-black shadow-lg shadow-red-900/50' 
              : 'bg-black text-gray-600 border-gray-800'
          }`}>
            {step}
          </div>
          {step < 3 && (
            <div className={`w-10 h-1 ${
              step < currentStep ? 'bg-red-600' : 'bg-gray-800'
            }`} />
          )}
        </React.Fragment>
      ))}
    </div>
  );

  const renderStep1 = () => (
    <div className="space-y-6">
      <div className="text-center">
        <div className="w-16 h-16 bg-gradient-to-br from-red-600 to-red-900 text-white border-4 border-black flex items-center justify-center mx-auto mb-6 text-2xl font-black shadow-lg shadow-red-900/50">
          1
        </div>
        <h3 className="text-2xl font-black text-white mb-2 uppercase tracking-widest">PERSONAL INFO</h3>
        <p className="text-gray-400 text-xs uppercase tracking-wider">BASIC DETAILS</p>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <Input
          label="FIRST NAME"
          value={formData.first_name}
          placeholder="John"
          required
          onChange={(value) => handleInputChange('first_name', value)}
        />
        <Input
          label="LAST NAME"
          value={formData.last_name}
          placeholder="Doe"
          required
          onChange={(value) => handleInputChange('last_name', value)}
        />
      </div>

      <Input
        type="email"
        label="EMAIL"
        value={formData.email}
        placeholder="john.doe@domain.com"
        required
        onChange={(value) => handleInputChange('email', value)}
      />

      <Button
        onClick={handleNextStep}
        disabled={!formData.first_name || !formData.last_name || !formData.email}
        className="w-full"
        size="lg"
      >
        CONTINUE →
      </Button>
    </div>
  );

  const renderStep2 = () => (
    <div className="space-y-6">
      <div className="text-center">
        <div className="w-16 h-16 bg-gradient-to-br from-red-600 to-red-900 text-white border-4 border-black flex items-center justify-center mx-auto mb-6 text-2xl font-black shadow-lg shadow-red-900/50">
          2
        </div>
        <h3 className="text-2xl font-black text-white mb-2 uppercase tracking-widest">CONTACT</h3>
        <p className="text-gray-400 text-xs uppercase tracking-wider">VERIFICATION INFO</p>
      </div>

      <Input
        type="tel"
        label="PHONE"
        value={formData.phoneNumber}
        placeholder="+1 (555) 123-4567"
        required
        onChange={(value) => handleInputChange('phoneNumber', value)}
      />

      <Input
        type="date"
        label="BIRTH DATE"
        value={formData.dateOfBirth}
        required
        onChange={(value) => handleInputChange('dateOfBirth', value)}
      />

      <Card variant="outlined" className="p-4 bg-black/50 border-2 border-red-800">
        <div className="text-sm text-white font-black">
          <p className="uppercase mb-2 tracking-wider">⚠ VERIFICATION NOTICE</p>
          <p className="text-xs text-gray-400 uppercase">AGE VERIFICATION REQUIRED FOR COMPLIANCE.</p>
        </div>
      </Card>

      <div className="grid grid-cols-2 gap-3">
        <Button
          variant="outline"
          onClick={handlePrevStep}
        >
          ← BACK
        </Button>
        <Button
          onClick={handleNextStep}
          disabled={!formData.phoneNumber || !formData.dateOfBirth}
        >
          CONTINUE →
        </Button>
      </div>
    </div>
  );

  const renderStep3 = () => (
    <div className="space-y-6">
      <div className="text-center">
        <div className="w-16 h-16 bg-gradient-to-br from-red-600 to-red-900 text-white border-4 border-black flex items-center justify-center mx-auto mb-6 text-2xl font-black shadow-lg shadow-red-900/50">
          3
        </div>
        <h3 className="text-2xl font-black text-white mb-2 uppercase tracking-widest">SECURITY</h3>
        <p className="text-gray-400 text-xs uppercase tracking-wider">SET PASSWORD</p>
      </div>

      <div className="space-y-4">
        <div className="relative">
          <Input
            type={showPassword ? 'text' : 'password'}
            label="PASSWORD"
            value={formData.password}
            placeholder="Min 8 characters"
            required
            onChange={(value) => handleInputChange('password', value)}
          />
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute right-3 top-8 text-gray-400 hover:text-red-500 transition-colors font-black text-xs uppercase tracking-wider"
          >
            {showPassword ? 'HIDE' : 'SHOW'}
          </button>
        </div>

        <Input
          type="password"
          label="CONFIRM PASSWORD"
          value={formData.confirmPassword}
          placeholder="Repeat password"
          required
          error={formData.confirmPassword && formData.password !== formData.confirmPassword ? "✖ MISMATCH" : ''}
          onChange={(value) => handleInputChange('confirmPassword', value)}
        />
      </div>

      <div className="space-y-4 border-4 border-black bg-gradient-to-r from-gray-900 to-black p-4">
        <label className="flex items-start gap-3 cursor-pointer">
          <input
            type="checkbox"
            checked={acceptTerms}
            onChange={(e) => setAcceptTerms(e.target.checked)}
            className="w-4 h-4 text-red-600 bg-black border-gray-600 rounded-none focus:ring-red-500 mt-0.5"
          />
          <div className="text-xs font-black uppercase tracking-wider">
            <span className="text-gray-400">I ACCEPT THE </span>
            <button type="button" className="text-red-500 hover:text-red-400 underline">
              TERMS
            </button>
            <span className="text-gray-400"> & </span>
            <button type="button" className="text-red-500 hover:text-red-400 underline">
              PRIVACY
            </button>
          </div>
        </label>

        <label className="flex items-start gap-3 cursor-pointer">
          <input
            type="checkbox"
            checked={acceptMarketing}
            onChange={(e) => setAcceptMarketing(e.target.checked)}
            className="w-4 h-4 text-red-600 bg-black border-gray-600 rounded-none focus:ring-red-500 mt-0.5"
          />
          <span className="text-xs text-gray-400 font-black uppercase tracking-wider">
            RECEIVE METAL UPDATES & PROMOS
          </span>
        </label>
      </div>

      {(localError || authError) && (
        <Card variant="outlined" className="p-4 border-2 border-red-600 bg-red-950/20">
          <div className="text-red-500 text-sm font-black uppercase tracking-wider">
            ✖ ERROR: {localError || authError}
          </div>
        </Card>
      )}

      <div className="grid grid-cols-2 gap-3">
        <Button
          variant="outline"
          onClick={handlePrevStep}
        >
          ← BACK
        </Button>
        <Button
          type="submit"
          onClick={handleSubmit}
          disabled={authLoading || !acceptTerms || formData.password !== formData.confirmPassword}
          loading={authLoading}
        >
          {authLoading ? 'CREATING...' : 'CREATE →'}
        </Button>
      </div>
    </div>
  );

  return (
    <Modal isOpen onClose={onClose} title="JOIN THE METAL LEGION">
      <div className="space-y-6">
        {renderStepIndicator()}
        
        <form onSubmit={handleSubmit}>
          {currentStep === 1 && renderStep1()}
          {currentStep === 2 && renderStep2()}
          {currentStep === 3 && renderStep3()}
        </form>

        {/* Login Link */}
        <div className="text-center pt-6 border-t-4 border-gray-800">
          <p className="text-gray-400 mb-4 font-black text-xs uppercase tracking-wider">ALREADY A METALHEAD?</p>
          <Button
            variant="outline"
            onClick={() => {
              onClose();
              onLogin();
            }}
            className="w-full"
          >
            SIGN IN
          </Button>
        </div>

      </div>
    </Modal>
  );
};

export default Register;