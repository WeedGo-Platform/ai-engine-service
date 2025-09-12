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
          <div className={`w-8 h-8 flex items-center justify-center font-mono text-sm ${
            step <= currentStep 
              ? 'bg-black text-white' 
              : 'bg-gray-200 text-gray-500'
          }`}>
            {step}
          </div>
          {step < 3 && (
            <div className={`w-8 h-px mx-2 ${
              step < currentStep ? 'bg-black' : 'bg-gray-300'
            }`} />
          )}
        </React.Fragment>
      ))}
    </div>
  );

  const renderStep1 = () => (
    <div className="space-y-6">
      <div className="text-center">
        <div className="w-12 h-12 bg-black text-white flex items-center justify-center mx-auto mb-6 font-mono text-xl">
          1
        </div>
        <h3 className="text-xl font-light text-gray-900 mb-2">Personal Information</h3>
        <p className="text-gray-600 text-sm">Basic details required</p>
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
        label="EMAIL ADDRESS"
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
        <div className="w-12 h-12 bg-black text-white flex items-center justify-center mx-auto mb-6 font-mono text-xl">
          2
        </div>
        <h3 className="text-xl font-light text-gray-900 mb-2">Contact Details</h3>
        <p className="text-gray-600 text-sm">Verification information</p>
      </div>

      <Input
        type="tel"
        label="PHONE NUMBER"
        value={formData.phoneNumber}
        placeholder="+1 (555) 123-4567"
        required
        onChange={(value) => handleInputChange('phoneNumber', value)}
      />

      <Input
        type="date"
        label="DATE OF BIRTH"
        value={formData.dateOfBirth}
        required
        onChange={(value) => handleInputChange('dateOfBirth', value)}
      />

      <Card variant="outlined" className="p-4">
        <div className="text-sm text-gray-900 font-mono">
          <p className="font-medium mb-2">VERIFICATION NOTICE</p>
          <p className="text-xs text-gray-600">Age verification required for compliance purposes.</p>
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
        <div className="w-12 h-12 bg-black text-white flex items-center justify-center mx-auto mb-6 font-mono text-xl">
          3
        </div>
        <h3 className="text-xl font-light text-gray-900 mb-2">Account Security</h3>
        <p className="text-gray-600 text-sm">Password setup</p>
      </div>

      <div className="space-y-4">
        <div className="relative">
          <Input
            type={showPassword ? 'text' : 'password'}
            label="PASSWORD"
            value={formData.password}
            placeholder="Minimum 8 characters"
            required
            onChange={(value) => handleInputChange('password', value)}
          />
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute right-3 top-8 text-gray-400 hover:text-gray-600 transition-colors font-mono text-sm"
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
          error={formData.confirmPassword && formData.password !== formData.confirmPassword ? "PASSWORD MISMATCH" : ''}
          onChange={(value) => handleInputChange('confirmPassword', value)}
        />
      </div>

      <div className="space-y-4 border border-gray-300 p-4">
        <label className="flex items-start gap-3 cursor-pointer">
          <input
            type="checkbox"
            checked={acceptTerms}
            onChange={(e) => setAcceptTerms(e.target.checked)}
            className="w-4 h-4 text-black border-gray-300 rounded-none focus:ring-black mt-0.5"
          />
          <div className="text-sm font-mono">
            <span className="text-gray-700">I ACCEPT THE </span>
            <button type="button" className="text-black hover:text-gray-600 underline">
              TERMS
            </button>
            <span className="text-gray-700"> AND </span>
            <button type="button" className="text-black hover:text-gray-600 underline">
              PRIVACY POLICY
            </button>
          </div>
        </label>

        <label className="flex items-start gap-3 cursor-pointer">
          <input
            type="checkbox"
            checked={acceptMarketing}
            onChange={(e) => setAcceptMarketing(e.target.checked)}
            className="w-4 h-4 text-black border-gray-300 rounded-none focus:ring-black mt-0.5"
          />
          <span className="text-sm text-gray-700 font-mono">
            RECEIVE PRODUCT UPDATES AND MARKETING COMMUNICATIONS
          </span>
        </label>
      </div>

      {(localError || authError) && (
        <Card variant="outlined" className="p-4 border-red-600">
          <div className="text-red-600 text-sm font-mono">
            ERROR: {localError || authError}
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
          {authLoading ? 'CREATING...' : 'CREATE ACCOUNT'}
        </Button>
      </div>
    </div>
  );

  return (
    <Modal isOpen onClose={onClose} title="Join Cannabis Community">
      <div className="space-y-6">
        {renderStepIndicator()}
        
        <form onSubmit={handleSubmit}>
          {currentStep === 1 && renderStep1()}
          {currentStep === 2 && renderStep2()}
          {currentStep === 3 && renderStep3()}
        </form>

        {/* Login Link */}
        <div className="text-center pt-6 border-t border-gray-200">
          <p className="text-gray-600 mb-4 font-mono text-xs">EXISTING USER?</p>
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