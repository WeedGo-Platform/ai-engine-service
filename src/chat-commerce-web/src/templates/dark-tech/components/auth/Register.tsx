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
      setLocalError('PROTOCOL AGREEMENT REQUIRED');
      return;
    }

    if (formData.password !== formData.confirmPassword) {
      setLocalError('PASSWORD MISMATCH DETECTED');
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
      setLocalError(err.message || 'NEURAL PROFILE CREATION FAILED');
    }
  };

  const renderStepIndicator = () => (
    <div className="flex items-center justify-center mb-8">
      {[1, 2, 3].map((step) => (
        <React.Fragment key={step}>
          <div className={`w-12 h-12 border-2 flex items-center justify-center font-mono font-bold relative ${
            step <= currentStep 
              ? 'border-cyan-400 text-cyan-100 bg-cyan-900 shadow-lg shadow-cyan-400/20' 
              : 'border-cyan-800 text-cyan-600 bg-gray-900'
          }`}>
            {step <= currentStep ? '◉' : step}
            {/* Corner brackets */}
            <div className={`absolute top-0 left-0 w-2 h-2 border-l border-t ${step <= currentStep ? 'border-cyan-400' : 'border-cyan-800'}`}></div>
            <div className={`absolute top-0 right-0 w-2 h-2 border-r border-t ${step <= currentStep ? 'border-cyan-400' : 'border-cyan-800'}`}></div>
            <div className={`absolute bottom-0 left-0 w-2 h-2 border-l border-b ${step <= currentStep ? 'border-cyan-400' : 'border-cyan-800'}`}></div>
            <div className={`absolute bottom-0 right-0 w-2 h-2 border-r border-b ${step <= currentStep ? 'border-cyan-400' : 'border-cyan-800'}`}></div>
          </div>
          {step < 3 && (
            <div className={`w-16 h-0.5 mx-2 ${
              step < currentStep 
                ? 'bg-gradient-to-r from-cyan-400 to-magenta-400 animate-pulse' 
                : 'bg-cyan-800'
            }`} />
          )}
        </React.Fragment>
      ))}
    </div>
  );

  const renderStep1 = () => (
    <div className="space-y-6">
      <div className="text-center">
        <div className="w-16 h-16 bg-gray-900 border-2 border-cyan-400 text-cyan-400 flex items-center justify-center mx-auto mb-6 font-mono text-xl relative">
          <span className="animate-pulse">{'ID'}</span>
          {/* Scanning line */}
          <div className="absolute top-0 left-0 w-full h-0.5 bg-gradient-to-r from-transparent via-cyan-400 to-transparent animate-pulse"></div>
        </div>
        <h3 className="text-xl font-bold text-cyan-100 mb-2 font-mono uppercase tracking-wider">
          IDENTITY INITIALIZATION
        </h3>
        <p className="text-cyan-400 text-sm font-mono">{'>>> '} PERSONAL DATA MATRIX</p>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <Input
          label="FIRST NAME"
          value={formData.first_name}
          placeholder="Neo"
          required
          onChange={(value) => handleInputChange('first_name', value)}
        />
        <Input
          label="LAST NAME"
          value={formData.last_name}
          placeholder="Anderson"
          required
          onChange={(value) => handleInputChange('last_name', value)}
        />
      </div>

      <Input
        type="email"
        label="NEURAL INTERFACE"
        value={formData.email}
        placeholder="neo@matrix.underground"
        required
        onChange={(value) => handleInputChange('email', value)}
      />

      <Button
        onClick={handleNextStep}
        disabled={!formData.first_name || !formData.last_name || !formData.email}
        className="w-full"
        size="lg"
      >
        CONTINUE SEQUENCE ⚡
      </Button>
    </div>
  );

  const renderStep2 = () => (
    <div className="space-y-6">
      <div className="text-center">
        <div className="w-16 h-16 bg-gray-900 border-2 border-magenta-400 text-magenta-400 flex items-center justify-center mx-auto mb-6 font-mono text-xl relative">
          <span className="animate-pulse">{'<>'}</span>
          {/* Side scanning lights */}
          <div className="absolute left-0 top-1/4 w-0.5 h-1/2 bg-gradient-to-b from-transparent via-magenta-400 to-transparent animate-pulse"></div>
          <div className="absolute right-0 top-1/4 w-0.5 h-1/2 bg-gradient-to-b from-transparent via-cyan-400 to-transparent animate-pulse"></div>
        </div>
        <h3 className="text-xl font-bold text-cyan-100 mb-2 font-mono uppercase tracking-wider">
          VERIFICATION PROTOCOLS
        </h3>
        <p className="text-cyan-400 text-sm font-mono">{'>>> '} BIOMETRIC SCANNING</p>
      </div>

      <Input
        type="tel"
        label="COMM FREQUENCY"
        value={formData.phoneNumber}
        placeholder="+1-555-MATRIX"
        required
        onChange={(value) => handleInputChange('phoneNumber', value)}
      />

      <Input
        type="date"
        label="BIRTH TIMESTAMP"
        value={formData.dateOfBirth}
        required
        onChange={(value) => handleInputChange('dateOfBirth', value)}
      />

      <Card variant="filled" className="p-6 border-yellow-600">
        <div className="flex items-start gap-4">
          <span className="text-2xl animate-pulse text-yellow-400">⚠</span>
          <div className="text-sm text-cyan-100 font-mono">
            <p className="font-bold mb-2 uppercase text-yellow-400">SECURITY PROTOCOL</p>
            <p className="text-xs text-cyan-400">
              AGE VERIFICATION REQUIRED FOR MATRIX ACCESS. NEURAL INTERFACES RESTRICTED TO ADULTS ONLY.
            </p>
          </div>
        </div>
      </Card>

      <div className="grid grid-cols-2 gap-4">
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
          ADVANCE ⚡
        </Button>
      </div>
    </div>
  );

  const renderStep3 = () => (
    <div className="space-y-6">
      <div className="text-center">
        <div className="w-16 h-16 bg-gray-900 border-2 border-lime-400 text-lime-400 flex items-center justify-center mx-auto mb-6 font-mono text-xl relative">
          <span className="animate-pulse">{'🔐'}</span>
          {/* Matrix rain effect hint */}
          <div className="absolute inset-0 overflow-hidden opacity-20">
            <div className="absolute top-0 left-2 w-px h-full bg-gradient-to-b from-lime-400 to-transparent animate-pulse" style={{ animationDelay: '0s' }}></div>
            <div className="absolute top-0 right-2 w-px h-full bg-gradient-to-b from-cyan-400 to-transparent animate-pulse" style={{ animationDelay: '1s' }}></div>
          </div>
        </div>
        <h3 className="text-xl font-bold text-cyan-100 mb-2 font-mono uppercase tracking-wider">
          SECURITY ENCRYPTION
        </h3>
        <p className="text-cyan-400 text-sm font-mono">{'>>> '} ACCESS CODE GENERATION</p>
      </div>

      <div className="space-y-4">
        <div className="relative">
          <Input
            type={showPassword ? 'text' : 'password'}
            label="MASTER PASSWORD"
            value={formData.password}
            placeholder="Choose your red pill..."
            required
            onChange={(value) => handleInputChange('password', value)}
          />
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute right-3 top-9 text-cyan-400 hover:text-cyan-100 transition-colors font-mono text-sm"
          >
            {showPassword ? 'HIDE' : 'SHOW'}
          </button>
        </div>

        <Input
          type="password"
          label="CONFIRM PASSWORD"
          value={formData.confirmPassword}
          placeholder="Verify access code"
          required
          error={formData.confirmPassword && formData.password !== formData.confirmPassword ? "PASSWORD MISMATCH DETECTED" : ''}
          onChange={(value) => handleInputChange('confirmPassword', value)}
        />
      </div>

      <div className="space-y-4 border-2 border-cyan-800 p-6 bg-gray-900/50">
        <label className="flex items-start gap-4 cursor-pointer">
          <input
            type="checkbox"
            checked={acceptTerms}
            onChange={(e) => setAcceptTerms(e.target.checked)}
            className="w-5 h-5 text-cyan-400 bg-gray-800 border-2 border-cyan-600 focus:ring-cyan-400 focus:ring-2 mt-1"
          />
          <div className="text-sm font-mono">
            <span className="text-cyan-300 uppercase">I ACCEPT THE </span>
            <button type="button" className="text-magenta-400 hover:text-magenta-300 underline font-bold uppercase">
              MATRIX PROTOCOLS
            </button>
            <span className="text-cyan-300 uppercase"> AND </span>
            <button type="button" className="text-magenta-400 hover:text-magenta-300 underline font-bold uppercase">
              DATA SECURITY TERMS
            </button>
          </div>
        </label>

        <label className="flex items-start gap-4 cursor-pointer">
          <input
            type="checkbox"
            checked={acceptMarketing}
            onChange={(e) => setAcceptMarketing(e.target.checked)}
            className="w-5 h-5 text-cyan-400 bg-gray-800 border-2 border-cyan-600 focus:ring-cyan-400 focus:ring-2 mt-1"
          />
          <span className="text-sm text-cyan-300 font-mono uppercase">
            RECEIVE UNDERGROUND INTELLIGENCE UPDATES & SYSTEM NOTIFICATIONS
          </span>
        </label>
      </div>

      {(localError || authError) && (
        <Card variant="filled" className="p-4 border-red-500 bg-red-900/20">
          <div className="flex items-center gap-3 text-red-400 text-sm font-mono">
            <span className="animate-pulse text-lg">⚠</span>
            <span className="uppercase">SYSTEM ERROR: {localError || authError}</span>
          </div>
        </Card>
      )}

      <div className="grid grid-cols-2 gap-4">
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
          {authLoading ? 'UPLOADING PROFILE...' : 'JACK INTO MATRIX ⚡'}
        </Button>
      </div>
    </div>
  );

  return (
    <Modal isOpen onClose={onClose} title="NEURAL PROFILE CREATION">
      <div className="space-y-6">
        {renderStepIndicator()}
        
        <form onSubmit={handleSubmit}>
          {currentStep === 1 && renderStep1()}
          {currentStep === 2 && renderStep2()}
          {currentStep === 3 && renderStep3()}
        </form>

        {/* Login Link */}
        <div className="text-center pt-6 border-t-2 border-cyan-800/50">
          <p className="text-cyan-400 mb-4 font-mono text-sm uppercase">PROFILE ALREADY EXISTS?</p>
          <Button
            variant="outline"
            onClick={() => {
              onClose();
              onLogin();
            }}
            className="w-full"
          >
            JACK IN INSTEAD ⚡
          </Button>
        </div>

        {/* Security Badges */}
        <div className="flex items-center justify-center gap-4 text-xs font-mono pt-4">
          <Badge variant="primary" size="sm">◉ QUANTUM ENCRYPTED</Badge>
          <Badge variant="secondary" size="sm">◈ NEURAL SECURED</Badge>
          <Badge variant="success" size="sm">✓ MATRIX COMPLIANT</Badge>
        </div>
      </div>
    </Modal>
  );
};

export default Register;