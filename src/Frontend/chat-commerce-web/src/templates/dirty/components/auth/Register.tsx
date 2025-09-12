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
          <div className={`w-10 h-10 flex items-center justify-center font-bold text-sm border-2 ${
            step <= currentStep 
              ? 'bg-gradient-to-br from-zinc-800 to-black text-gray-100 border-zinc-600' 
              : 'bg-zinc-900 text-gray-600 border-zinc-700'
          }`}>
            {step}
          </div>
          {step < 3 && (
            <div className={`w-8 h-0.5 ${
              step < currentStep ? 'bg-zinc-600' : 'bg-zinc-800'
            }`} />
          )}
        </React.Fragment>
      ))}
    </div>
  );

  const renderStep1 = () => (
    <div className="space-y-6">
      <div className="text-center">
        <div className="w-14 h-14 bg-gradient-to-br from-zinc-800 to-black text-gray-400 border-2 border-zinc-700 flex items-center justify-center mx-auto mb-6 text-xl font-bold">
          1
        </div>
        <h3 className="text-xl font-bold text-gray-200 mb-2 uppercase tracking-wider">Personal Info</h3>
        <p className="text-gray-500 text-xs uppercase">Basic details</p>
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
        CONTINUE
      </Button>
    </div>
  );

  const renderStep2 = () => (
    <div className="space-y-6">
      <div className="text-center">
        <div className="w-14 h-14 bg-gradient-to-br from-zinc-800 to-black text-gray-400 border-2 border-zinc-700 flex items-center justify-center mx-auto mb-6 text-xl font-bold">
          2
        </div>
        <h3 className="text-xl font-bold text-gray-200 mb-2 uppercase tracking-wider">Contact</h3>
        <p className="text-gray-500 text-xs uppercase">Verification info</p>
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

      <Card variant="outlined" className="p-4 bg-zinc-900/50 border-zinc-700">
        <div className="text-sm text-gray-300 font-bold">
          <p className="uppercase mb-2">⚠ Verification Notice</p>
          <p className="text-xs text-gray-500">Age verification required for compliance.</p>
        </div>
      </Card>

      <div className="grid grid-cols-2 gap-3">
        <Button
          variant="outline"
          onClick={handlePrevStep}
        >
          BACK
        </Button>
        <Button
          onClick={handleNextStep}
          disabled={!formData.phoneNumber || !formData.dateOfBirth}
        >
          CONTINUE
        </Button>
      </div>
    </div>
  );

  const renderStep3 = () => (
    <div className="space-y-6">
      <div className="text-center">
        <div className="w-14 h-14 bg-gradient-to-br from-zinc-800 to-black text-gray-400 border-2 border-zinc-700 flex items-center justify-center mx-auto mb-6 text-xl font-bold">
          3
        </div>
        <h3 className="text-xl font-bold text-gray-200 mb-2 uppercase tracking-wider">Security</h3>
        <p className="text-gray-500 text-xs uppercase">Set password</p>
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
            className="absolute right-3 top-8 text-gray-500 hover:text-gray-300 transition-colors font-bold text-xs uppercase"
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
          error={formData.confirmPassword && formData.password !== formData.confirmPassword ? "MISMATCH" : ''}
          onChange={(value) => handleInputChange('confirmPassword', value)}
        />
      </div>

      <div className="space-y-4 border-2 border-zinc-700 bg-zinc-900/50 p-4">
        <label className="flex items-start gap-3 cursor-pointer">
          <input
            type="checkbox"
            checked={acceptTerms}
            onChange={(e) => setAcceptTerms(e.target.checked)}
            className="w-4 h-4 text-zinc-700 bg-zinc-800 border-zinc-600 rounded-none focus:ring-zinc-500 mt-0.5"
          />
          <div className="text-xs font-bold uppercase">
            <span className="text-gray-400">I accept the </span>
            <button type="button" className="text-gray-300 hover:text-gray-100 underline">
              Terms
            </button>
            <span className="text-gray-400"> & </span>
            <button type="button" className="text-gray-300 hover:text-gray-100 underline">
              Privacy
            </button>
          </div>
        </label>

        <label className="flex items-start gap-3 cursor-pointer">
          <input
            type="checkbox"
            checked={acceptMarketing}
            onChange={(e) => setAcceptMarketing(e.target.checked)}
            className="w-4 h-4 text-zinc-700 bg-zinc-800 border-zinc-600 rounded-none focus:ring-zinc-500 mt-0.5"
          />
          <span className="text-xs text-gray-400 font-bold uppercase">
            Receive updates & promos
          </span>
        </label>
      </div>

      {(localError || authError) && (
        <Card variant="outlined" className="p-4 border-red-800 bg-red-950/30">
          <div className="text-red-500 text-sm font-bold uppercase">
            ✗ Error: {localError || authError}
          </div>
        </Card>
      )}

      <div className="grid grid-cols-2 gap-3">
        <Button
          variant="outline"
          onClick={handlePrevStep}
        >
          BACK
        </Button>
        <Button
          type="submit"
          onClick={handleSubmit}
          disabled={authLoading || !acceptTerms || formData.password !== formData.confirmPassword}
          loading={authLoading}
        >
          {authLoading ? 'CREATING...' : 'CREATE'}
        </Button>
      </div>
    </div>
  );

  return (
    <Modal isOpen onClose={onClose} title="Join The Darkness">
      <div className="space-y-6">
        {renderStepIndicator()}
        
        <form onSubmit={handleSubmit}>
          {currentStep === 1 && renderStep1()}
          {currentStep === 2 && renderStep2()}
          {currentStep === 3 && renderStep3()}
        </form>

        {/* Login Link */}
        <div className="text-center pt-6 border-t border-zinc-700">
          <p className="text-gray-500 mb-4 font-bold text-xs uppercase">Already member?</p>
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