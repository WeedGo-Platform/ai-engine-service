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
          <div className={`w-10 h-10 flex items-center justify-center font-serif text-lg rounded-lg border-2 ${
            step <= currentStep 
              ? 'bg-gradient-to-br from-amber-700 to-amber-800 text-amber-50 border-amber-700' 
              : 'bg-amber-50 text-amber-600 border-amber-300'
          }`}>
            {step}
          </div>
          {step < 3 && (
            <div className={`w-12 h-0.5 mx-2 ${
              step < currentStep ? 'bg-amber-700' : 'bg-amber-300'
            }`} />
          )}
        </React.Fragment>
      ))}
    </div>
  );

  const renderStep1 = () => (
    <div className="space-y-6">
      <div className="text-center">
        <div className="w-16 h-16 bg-gradient-to-br from-amber-700 to-amber-900 text-amber-100 rounded-lg shadow-lg flex items-center justify-center mx-auto mb-6 text-2xl font-serif">
          1
        </div>
        <h3 className="text-2xl font-serif text-amber-900 mb-2">Personal Information</h3>
        <p className="text-amber-700 text-sm italic">Your basic details</p>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <Input
          label="First Name"
          value={formData.first_name}
          placeholder="John"
          required
          onChange={(value) => handleInputChange('first_name', value)}
        />
        <Input
          label="Last Name"
          value={formData.last_name}
          placeholder="Doe"
          required
          onChange={(value) => handleInputChange('last_name', value)}
        />
      </div>

      <Input
        type="email"
        label="Email Address"
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
        Continue
      </Button>
    </div>
  );

  const renderStep2 = () => (
    <div className="space-y-6">
      <div className="text-center">
        <div className="w-16 h-16 bg-gradient-to-br from-amber-700 to-amber-900 text-amber-100 rounded-lg shadow-lg flex items-center justify-center mx-auto mb-6 text-2xl font-serif">
          2
        </div>
        <h3 className="text-2xl font-serif text-amber-900 mb-2">Contact Details</h3>
        <p className="text-amber-700 text-sm italic">Verification information</p>
      </div>

      <Input
        type="tel"
        label="Phone Number"
        value={formData.phoneNumber}
        placeholder="+1 (555) 123-4567"
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

      <Card variant="outlined" className="p-4 bg-amber-50 border-amber-300">
        <div className="text-sm text-amber-900 font-serif">
          <p className="font-bold mb-2">Verification Notice</p>
          <p className="text-xs text-amber-700 italic">Age verification is required for compliance purposes.</p>
        </div>
      </Card>

      <div className="grid grid-cols-2 gap-3">
        <Button
          variant="outline"
          onClick={handlePrevStep}
        >
          Back
        </Button>
        <Button
          onClick={handleNextStep}
          disabled={!formData.phoneNumber || !formData.dateOfBirth}
        >
          Continue
        </Button>
      </div>
    </div>
  );

  const renderStep3 = () => (
    <div className="space-y-6">
      <div className="text-center">
        <div className="w-16 h-16 bg-gradient-to-br from-amber-700 to-amber-900 text-amber-100 rounded-lg shadow-lg flex items-center justify-center mx-auto mb-6 text-2xl font-serif">
          3
        </div>
        <h3 className="text-2xl font-serif text-amber-900 mb-2">Account Security</h3>
        <p className="text-amber-700 text-sm italic">Create your password</p>
      </div>

      <div className="space-y-4">
        <div className="relative">
          <Input
            type={showPassword ? 'text' : 'password'}
            label="Password"
            value={formData.password}
            placeholder="Minimum 8 characters"
            required
            onChange={(value) => handleInputChange('password', value)}
          />
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute right-3 top-9 text-amber-600 hover:text-amber-800 transition-colors text-sm font-serif"
          >
            {showPassword ? 'Hide' : 'Show'}
          </button>
        </div>

        <Input
          type="password"
          label="Confirm Password"
          value={formData.confirmPassword}
          placeholder="Repeat password"
          required
          error={formData.confirmPassword && formData.password !== formData.confirmPassword ? "Passwords don't match" : ''}
          onChange={(value) => handleInputChange('confirmPassword', value)}
        />
      </div>

      <div className="space-y-4 border-2 border-amber-300 rounded-lg p-4 bg-amber-50">
        <label className="flex items-start gap-3 cursor-pointer">
          <input
            type="checkbox"
            checked={acceptTerms}
            onChange={(e) => setAcceptTerms(e.target.checked)}
            className="w-4 h-4 text-amber-700 border-amber-400 rounded focus:ring-amber-500 mt-0.5"
          />
          <div className="text-sm font-serif">
            <span className="text-amber-800">I accept the </span>
            <button type="button" className="text-amber-700 hover:text-amber-900 underline italic">
              Terms & Conditions
            </button>
            <span className="text-amber-800"> and </span>
            <button type="button" className="text-amber-700 hover:text-amber-900 underline italic">
              Privacy Policy
            </button>
          </div>
        </label>

        <label className="flex items-start gap-3 cursor-pointer">
          <input
            type="checkbox"
            checked={acceptMarketing}
            onChange={(e) => setAcceptMarketing(e.target.checked)}
            className="w-4 h-4 text-amber-700 border-amber-400 rounded focus:ring-amber-500 mt-0.5"
          />
          <span className="text-sm text-amber-800 font-serif">
            Receive product updates and marketing communications
          </span>
        </label>
      </div>

      {(localError || authError) && (
        <Card variant="outlined" className="p-4 border-red-700 bg-red-50">
          <div className="text-red-700 text-sm font-serif">
            Error: {localError || authError}
          </div>
        </Card>
      )}

      <div className="grid grid-cols-2 gap-3">
        <Button
          variant="outline"
          onClick={handlePrevStep}
        >
          Back
        </Button>
        <Button
          type="submit"
          onClick={handleSubmit}
          disabled={authLoading || !acceptTerms || formData.password !== formData.confirmPassword}
          loading={authLoading}
        >
          {authLoading ? 'Creating...' : 'Create Account'}
        </Button>
      </div>
    </div>
  );

  return (
    <Modal isOpen onClose={onClose} title="Join Our Vintage Collection">
      <div className="space-y-6">
        {renderStepIndicator()}
        
        <form onSubmit={handleSubmit}>
          {currentStep === 1 && renderStep1()}
          {currentStep === 2 && renderStep2()}
          {currentStep === 3 && renderStep3()}
        </form>

        {/* Login Link */}
        <div className="text-center pt-6 border-t-2 border-amber-200">
          <p className="text-amber-700 mb-4 font-serif text-sm italic">Already a member?</p>
          <Button
            variant="outline"
            onClick={() => {
              onClose();
              onLogin();
            }}
            className="w-full"
          >
            Sign In
          </Button>
        </div>

      </div>
    </Modal>
  );
};

export default Register;