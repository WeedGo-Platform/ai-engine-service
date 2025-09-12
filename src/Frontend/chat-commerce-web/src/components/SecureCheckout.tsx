import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Separator } from '@/components/ui/separator';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { toast } from '@/components/ui/use-toast';
import {
  CreditCard,
  Lock,
  Shield,
  AlertCircle,
  CheckCircle,
  Loader2,
  Mail,
  Smartphone,
  Building,
  ArrowLeft,
  Info,
} from 'lucide-react';
import { formatCardNumber, formatExpiryDate, validateCardNumber } from '@/lib/payment-utils';

interface CheckoutProps {
  orderId: string;
  amount: number;
  currency?: string;
  customerEmail?: string;
  customerPhone?: string;
  onSuccess?: (transaction: any) => void;
  onError?: (error: any) => void;
  onCancel?: () => void;
}

interface PaymentMethod {
  id: string;
  type: 'card' | 'interac' | 'saved';
  display: string;
  icon: React.ReactNode;
  last4?: string;
  brand?: string;
}

interface OrderSummaryItem {
  name: string;
  quantity: number;
  price: number;
}

const SecureCheckout: React.FC<CheckoutProps> = ({
  orderId,
  amount,
  currency = 'CAD',
  customerEmail = '',
  customerPhone = '',
  onSuccess,
  onError,
  onCancel,
}) => {
  const [selectedMethod, setSelectedMethod] = useState<string>('card');
  const [savedMethods, setSavedMethods] = useState<PaymentMethod[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [step, setStep] = useState<'method' | 'details' | 'processing' | 'complete'>('method');
  const [errors, setErrors] = useState<Record<string, string>>({});
  
  // Card payment fields
  const [cardNumber, setCardNumber] = useState('');
  const [cardName, setCardName] = useState('');
  const [expiryDate, setExpiryDate] = useState('');
  const [cvv, setCvv] = useState('');
  const [saveCard, setSaveCard] = useState(false);
  
  // Interac fields
  const [interacEmail, setInteracEmail] = useState(customerEmail);
  const [interacPhone, setInteracPhone] = useState(customerPhone);
  const [useAutoDeposit, setUseAutoDeposit] = useState(false);
  
  // Billing address
  const [billingAddress, setBillingAddress] = useState({
    line1: '',
    line2: '',
    city: '',
    state: '',
    postal_code: '',
    country: 'CA',
  });

  // Order summary (mock data - would come from props in real implementation)
  const orderItems: OrderSummaryItem[] = [
    { name: 'Premium Cannabis Product', quantity: 2, price: amount / 2 },
  ];

  const taxRate = 0.13; // 13% HST for Ontario
  const subtotal = amount;
  const tax = subtotal * taxRate;
  const total = subtotal + tax;

  useEffect(() => {
    fetchSavedPaymentMethods();
  }, []);

  const fetchSavedPaymentMethods = async () => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/api/payments/methods`, {
        credentials: 'include',
      });
      const data = await response.json();
      if (data.methods) {
        setSavedMethods(data.methods.map((method: any) => ({
          id: method.id,
          type: 'saved',
          display: `${method.card_brand} ****${method.card_last_four}`,
          icon: <CreditCard className="h-4 w-4" />,
          last4: method.card_last_four,
          brand: method.card_brand,
        })));
      }
    } catch (error) {
      console.error('Error fetching saved methods:', error);
    }
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (selectedMethod === 'card') {
      if (!cardNumber) {
        newErrors.cardNumber = 'Card number is required';
      } else if (!validateCardNumber(cardNumber.replace(/\s/g, ''))) {
        newErrors.cardNumber = 'Invalid card number';
      }

      if (!cardName) {
        newErrors.cardName = 'Cardholder name is required';
      }

      if (!expiryDate) {
        newErrors.expiryDate = 'Expiry date is required';
      } else {
        const [month, year] = expiryDate.split('/');
        const expiry = new Date(2000 + parseInt(year), parseInt(month) - 1);
        if (expiry < new Date()) {
          newErrors.expiryDate = 'Card has expired';
        }
      }

      if (!cvv || cvv.length < 3) {
        newErrors.cvv = 'CVV is required';
      }

      if (!billingAddress.line1) {
        newErrors.address = 'Billing address is required';
      }
      if (!billingAddress.city) {
        newErrors.city = 'City is required';
      }
      if (!billingAddress.postal_code) {
        newErrors.postal = 'Postal code is required';
      }
    } else if (selectedMethod === 'interac') {
      if (!interacEmail && !interacPhone) {
        newErrors.interac = 'Email or phone number is required';
      }
      if (interacEmail && !interacEmail.includes('@')) {
        newErrors.interacEmail = 'Invalid email address';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const processPayment = async () => {
    if (!validateForm()) {
      toast({
        title: 'Validation Error',
        description: 'Please fix the errors before continuing',
        variant: 'destructive',
      });
      return;
    }

    setIsProcessing(true);
    setStep('processing');

    try {
      const paymentData: any = {
        order_id: orderId,
        amount: total,
        currency,
        provider_type: selectedMethod === 'interac' ? 'interac' : 'moneris',
      };

      if (selectedMethod === 'card') {
        paymentData.payment_data = {
          card_number: cardNumber.replace(/\s/g, ''),
          exp_month: parseInt(expiryDate.split('/')[0]),
          exp_year: 2000 + parseInt(expiryDate.split('/')[1]),
          cvv,
          cardholder_name: cardName,
        };
        paymentData.billing_address = billingAddress;
        paymentData.save_card = saveCard;
      } else if (selectedMethod === 'interac') {
        paymentData.metadata = {
          customer_email: interacEmail,
          customer_phone: interacPhone,
          auto_deposit: useAutoDeposit,
        };
      } else if (selectedMethod.startsWith('saved_')) {
        paymentData.payment_method_id = selectedMethod.replace('saved_', '');
      }

      const response = await fetch(`${import.meta.env.VITE_API_URL}/api/payments/process`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(paymentData),
      });

      const result = await response.json();

      if (result.success) {
        setStep('complete');
        toast({
          title: 'Payment Successful',
          description: 'Your payment has been processed successfully',
        });
        if (onSuccess) {
          onSuccess(result);
        }
      } else {
        throw new Error(result.error || 'Payment failed');
      }
    } catch (error: any) {
      console.error('Payment error:', error);
      setStep('details');
      toast({
        title: 'Payment Failed',
        description: error.message || 'An error occurred processing your payment',
        variant: 'destructive',
      });
      if (onError) {
        onError(error);
      }
    } finally {
      setIsProcessing(false);
    }
  };

  const paymentMethods: PaymentMethod[] = [
    {
      id: 'card',
      type: 'card',
      display: 'Credit/Debit Card',
      icon: <CreditCard className="h-5 w-5" />,
    },
    {
      id: 'interac',
      type: 'interac',
      display: 'Interac e-Transfer',
      icon: <Building className="h-5 w-5" />,
    },
    ...savedMethods.map(method => ({
      ...method,
      id: `saved_${method.id}`,
    })),
  ];

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Payment Form */}
        <div className="lg:col-span-2 space-y-6">
          {/* Security Badge */}
          <Alert>
            <Shield className="h-4 w-4" />
            <AlertDescription className="flex items-center gap-2">
              <Lock className="h-3 w-3" />
              Secure checkout powered by industry-standard encryption
            </AlertDescription>
          </Alert>

          {step === 'method' && (
            <Card>
              <CardHeader>
                <CardTitle>Select Payment Method</CardTitle>
                <CardDescription>
                  Choose how you'd like to pay for your order
                </CardDescription>
              </CardHeader>
              <CardContent>
                <RadioGroup value={selectedMethod} onValueChange={setSelectedMethod}>
                  <div className="space-y-3">
                    {paymentMethods.map((method) => (
                      <div
                        key={method.id}
                        className="flex items-center space-x-3 p-3 border rounded-lg hover:bg-accent cursor-pointer"
                        onClick={() => setSelectedMethod(method.id)}
                      >
                        <RadioGroupItem value={method.id} />
                        <div className="flex items-center gap-3 flex-1">
                          {method.icon}
                          <div>
                            <p className="font-medium">{method.display}</p>
                            {method.type === 'saved' && (
                              <p className="text-sm text-muted-foreground">
                                Expires {method.brand}
                              </p>
                            )}
                          </div>
                        </div>
                        {method.type === 'saved' && (
                          <Badge variant="secondary">Saved</Badge>
                        )}
                      </div>
                    ))}
                  </div>
                </RadioGroup>
              </CardContent>
              <CardFooter className="flex justify-between">
                {onCancel && (
                  <Button variant="outline" onClick={onCancel}>
                    <ArrowLeft className="h-4 w-4 mr-2" />
                    Back to Cart
                  </Button>
                )}
                <Button onClick={() => setStep('details')}>
                  Continue
                </Button>
              </CardFooter>
            </Card>
          )}

          {step === 'details' && selectedMethod === 'card' && (
            <Card>
              <CardHeader>
                <CardTitle>Card Details</CardTitle>
                <CardDescription>
                  Enter your card information securely
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label htmlFor="card-number">Card Number</Label>
                  <div className="relative">
                    <Input
                      id="card-number"
                      placeholder="1234 5678 9012 3456"
                      value={cardNumber}
                      onChange={(e) => setCardNumber(formatCardNumber(e.target.value))}
                      maxLength={19}
                      className={errors.cardNumber ? 'border-destructive' : ''}
                    />
                    <CreditCard className="absolute right-3 top-3 h-4 w-4 text-muted-foreground" />
                  </div>
                  {errors.cardNumber && (
                    <p className="text-sm text-destructive mt-1">{errors.cardNumber}</p>
                  )}
                </div>

                <div>
                  <Label htmlFor="card-name">Cardholder Name</Label>
                  <Input
                    id="card-name"
                    placeholder="John Doe"
                    value={cardName}
                    onChange={(e) => setCardName(e.target.value)}
                    className={errors.cardName ? 'border-destructive' : ''}
                  />
                  {errors.cardName && (
                    <p className="text-sm text-destructive mt-1">{errors.cardName}</p>
                  )}
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="expiry">Expiry Date</Label>
                    <Input
                      id="expiry"
                      placeholder="MM/YY"
                      value={expiryDate}
                      onChange={(e) => setExpiryDate(formatExpiryDate(e.target.value))}
                      maxLength={5}
                      className={errors.expiryDate ? 'border-destructive' : ''}
                    />
                    {errors.expiryDate && (
                      <p className="text-sm text-destructive mt-1">{errors.expiryDate}</p>
                    )}
                  </div>
                  <div>
                    <Label htmlFor="cvv">CVV</Label>
                    <Input
                      id="cvv"
                      type="password"
                      placeholder="123"
                      value={cvv}
                      onChange={(e) => setCvv(e.target.value.replace(/\D/g, '').slice(0, 4))}
                      maxLength={4}
                      className={errors.cvv ? 'border-destructive' : ''}
                    />
                    {errors.cvv && (
                      <p className="text-sm text-destructive mt-1">{errors.cvv}</p>
                    )}
                  </div>
                </div>

                <Separator />

                <div className="space-y-4">
                  <h3 className="font-medium">Billing Address</h3>
                  <div>
                    <Label htmlFor="address1">Address Line 1</Label>
                    <Input
                      id="address1"
                      placeholder="123 Main St"
                      value={billingAddress.line1}
                      onChange={(e) => setBillingAddress({ ...billingAddress, line1: e.target.value })}
                      className={errors.address ? 'border-destructive' : ''}
                    />
                  </div>
                  <div>
                    <Label htmlFor="address2">Address Line 2 (Optional)</Label>
                    <Input
                      id="address2"
                      placeholder="Apt 4B"
                      value={billingAddress.line2}
                      onChange={(e) => setBillingAddress({ ...billingAddress, line2: e.target.value })}
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="city">City</Label>
                      <Input
                        id="city"
                        placeholder="Toronto"
                        value={billingAddress.city}
                        onChange={(e) => setBillingAddress({ ...billingAddress, city: e.target.value })}
                        className={errors.city ? 'border-destructive' : ''}
                      />
                    </div>
                    <div>
                      <Label htmlFor="state">Province</Label>
                      <Select
                        value={billingAddress.state}
                        onValueChange={(value) => setBillingAddress({ ...billingAddress, state: value })}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select province" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="ON">Ontario</SelectItem>
                          <SelectItem value="BC">British Columbia</SelectItem>
                          <SelectItem value="AB">Alberta</SelectItem>
                          <SelectItem value="QC">Quebec</SelectItem>
                          <SelectItem value="MB">Manitoba</SelectItem>
                          <SelectItem value="SK">Saskatchewan</SelectItem>
                          <SelectItem value="NS">Nova Scotia</SelectItem>
                          <SelectItem value="NB">New Brunswick</SelectItem>
                          <SelectItem value="NL">Newfoundland and Labrador</SelectItem>
                          <SelectItem value="PE">Prince Edward Island</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  <div>
                    <Label htmlFor="postal">Postal Code</Label>
                    <Input
                      id="postal"
                      placeholder="M5V 3A8"
                      value={billingAddress.postal_code}
                      onChange={(e) => setBillingAddress({ ...billingAddress, postal_code: e.target.value.toUpperCase() })}
                      className={errors.postal ? 'border-destructive' : ''}
                    />
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="save-card"
                    checked={saveCard}
                    onCheckedChange={(checked) => setSaveCard(checked as boolean)}
                  />
                  <Label htmlFor="save-card" className="text-sm">
                    Save this card for future purchases
                  </Label>
                </div>
              </CardContent>
              <CardFooter className="flex justify-between">
                <Button variant="outline" onClick={() => setStep('method')}>
                  Back
                </Button>
                <Button onClick={processPayment} disabled={isProcessing}>
                  {isProcessing ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Processing...
                    </>
                  ) : (
                    `Pay $${total.toFixed(2)} ${currency}`
                  )}
                </Button>
              </CardFooter>
            </Card>
          )}

          {step === 'details' && selectedMethod === 'interac' && (
            <Card>
              <CardHeader>
                <CardTitle>Interac e-Transfer</CardTitle>
                <CardDescription>
                  We'll send you payment instructions via email or SMS
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <Alert>
                  <Info className="h-4 w-4" />
                  <AlertDescription>
                    You'll receive instructions to complete your payment. The transfer will be
                    automatically deposited once approved.
                  </AlertDescription>
                </Alert>

                <div>
                  <Label htmlFor="interac-email">Email Address</Label>
                  <div className="relative">
                    <Input
                      id="interac-email"
                      type="email"
                      placeholder="john@example.com"
                      value={interacEmail}
                      onChange={(e) => setInteracEmail(e.target.value)}
                      className={errors.interacEmail ? 'border-destructive' : ''}
                    />
                    <Mail className="absolute right-3 top-3 h-4 w-4 text-muted-foreground" />
                  </div>
                  {errors.interacEmail && (
                    <p className="text-sm text-destructive mt-1">{errors.interacEmail}</p>
                  )}
                </div>

                <div className="text-center text-sm text-muted-foreground">OR</div>

                <div>
                  <Label htmlFor="interac-phone">Phone Number</Label>
                  <div className="relative">
                    <Input
                      id="interac-phone"
                      type="tel"
                      placeholder="+1 (555) 123-4567"
                      value={interacPhone}
                      onChange={(e) => setInteracPhone(e.target.value)}
                    />
                    <Smartphone className="absolute right-3 top-3 h-4 w-4 text-muted-foreground" />
                  </div>
                </div>

                {errors.interac && (
                  <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>{errors.interac}</AlertDescription>
                  </Alert>
                )}

                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="auto-deposit"
                    checked={useAutoDeposit}
                    onCheckedChange={(checked) => setUseAutoDeposit(checked as boolean)}
                  />
                  <Label htmlFor="auto-deposit" className="text-sm">
                    I have auto-deposit enabled for this email/phone
                  </Label>
                </div>

                <Alert>
                  <Shield className="h-4 w-4" />
                  <AlertDescription>
                    <strong>Security Note:</strong> Your payment request will expire in 30 days if not
                    completed. You'll receive a security question to verify your identity.
                  </AlertDescription>
                </Alert>
              </CardContent>
              <CardFooter className="flex justify-between">
                <Button variant="outline" onClick={() => setStep('method')}>
                  Back
                </Button>
                <Button onClick={processPayment} disabled={isProcessing}>
                  {isProcessing ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Processing...
                    </>
                  ) : (
                    `Request Payment of $${total.toFixed(2)} ${currency}`
                  )}
                </Button>
              </CardFooter>
            </Card>
          )}

          {step === 'processing' && (
            <Card>
              <CardContent className="py-12">
                <div className="text-center space-y-4">
                  <Loader2 className="h-12 w-12 animate-spin mx-auto text-primary" />
                  <h3 className="text-lg font-medium">Processing your payment...</h3>
                  <p className="text-sm text-muted-foreground">
                    Please don't close this window
                  </p>
                </div>
              </CardContent>
            </Card>
          )}

          {step === 'complete' && (
            <Card>
              <CardContent className="py-12">
                <div className="text-center space-y-4">
                  <CheckCircle className="h-12 w-12 text-green-500 mx-auto" />
                  <h3 className="text-lg font-medium">Payment Successful!</h3>
                  <p className="text-sm text-muted-foreground">
                    Your order has been confirmed and will be processed shortly.
                  </p>
                  <div className="pt-4">
                    <Button onClick={() => window.location.href = '/orders'}>
                      View Order Details
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Order Summary */}
        <div className="lg:col-span-1">
          <Card className="sticky top-6">
            <CardHeader>
              <CardTitle>Order Summary</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                {orderItems.map((item, index) => (
                  <div key={index} className="flex justify-between text-sm">
                    <span>
                      {item.name} x {item.quantity}
                    </span>
                    <span>${item.price.toFixed(2)}</span>
                  </div>
                ))}
              </div>
              
              <Separator />
              
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Subtotal</span>
                  <span>${subtotal.toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Tax (HST)</span>
                  <span>${tax.toFixed(2)}</span>
                </div>
              </div>
              
              <Separator />
              
              <div className="flex justify-between font-medium">
                <span>Total</span>
                <span className="text-lg">${total.toFixed(2)} {currency}</span>
              </div>

              <Alert>
                <Lock className="h-4 w-4" />
                <AlertDescription className="text-xs">
                  Your payment information is encrypted and secure. We never store your card details.
                </AlertDescription>
              </Alert>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default SecureCheckout;