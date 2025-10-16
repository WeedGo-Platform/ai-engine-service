import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import { toast } from '@/components/ui/use-toast';
import {
  CreditCard,
  DollarSign,
  TrendingUp,
  TrendingDown,
  RefreshCw,
  Download,
  Settings,
  AlertCircle,
  CheckCircle,
  XCircle,
  Clock,
  ArrowUpRight,
  ArrowDownRight,
  Search,
  Filter,
  Eye,
  Undo,
  Shield,
  Activity,
} from 'lucide-react';
import { DateRangePicker } from '@/components/date-range-picker';
import { format } from 'date-fns';

interface Transaction {
  id: string;
  transaction_reference: string;
  provider_transaction_id: string;
  type: string;
  status: string;
  amount: number;
  currency: string;
  provider_name: string;
  customer_name: string;
  order_id: string;
  created_at: string;
  completed_at: string;
  error_message?: string;
}

interface PaymentProvider {
  id: string;
  name: string;
  provider_type: string;
  is_active: boolean;
  is_default: boolean;
  supported_currencies: string[];
  capabilities: any;
  fee_structure: any;
}

interface PaymentMetrics {
  total_transactions: number;
  successful_transactions: number;
  failed_transactions: number;
  total_amount: number;
  total_fees: number;
  total_refunds: number;
  success_rate: number;
  avg_transaction_time: number;
}

const PaymentsPage: React.FC = () => {
  const { t } = useTranslation(['payments', 'common', 'errors']);

  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [providers, setProviders] = useState<PaymentProvider[]>([]);
  const [metrics, setMetrics] = useState<PaymentMetrics | null>(null);
  const [selectedTransaction, setSelectedTransaction] = useState<Transaction | null>(null);
  const [dateRange, setDateRange] = useState({ from: new Date(), to: new Date() });
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [providerFilter, setProviderFilter] = useState('all');
  const [refundAmount, setRefundAmount] = useState('');
  const [refundReason, setRefundReason] = useState('');
  const [isRefundDialogOpen, setIsRefundDialogOpen] = useState(false);
  const [isDetailDialogOpen, setIsDetailDialogOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchTransactions();
    fetchProviders();
    fetchMetrics();
  }, [dateRange, statusFilter, providerFilter]);

  const fetchTransactions = async () => {
    try {
      const params = new URLSearchParams({
        start_date: format(dateRange.from, 'yyyy-MM-dd'),
        end_date: format(dateRange.to, 'yyyy-MM-dd'),
        status: statusFilter,
        provider: providerFilter,
      });

      const response = await fetch(`${import.meta.env.VITE_API_URL}/api/payments/transactions?${params}`);
      const data = await response.json();
      setTransactions(data.transactions || []);
    } catch (error) {
      console.error('Error fetching transactions:', error);
      toast({
        title: t('payments:messages.error.title'),
        description: t('payments:messages.error.fetchTransactions'),
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const fetchProviders = async () => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/api/payments/providers`);
      const data = await response.json();
      setProviders(data.providers || []);
    } catch (error) {
      console.error('Error fetching providers:', error);
    }
  };

  const fetchMetrics = async () => {
    try {
      const params = new URLSearchParams({
        start_date: format(dateRange.from, 'yyyy-MM-dd'),
        end_date: format(dateRange.to, 'yyyy-MM-dd'),
      });

      const response = await fetch(`${import.meta.env.VITE_API_URL}/api/payments/metrics?${params}`);
      const data = await response.json();
      setMetrics(data);
    } catch (error) {
      console.error('Error fetching metrics:', error);
    }
  };

  const processRefund = async () => {
    if (!selectedTransaction) return;

    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/api/payments/refund`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          transaction_id: selectedTransaction.id,
          amount: refundAmount ? parseFloat(refundAmount) : undefined,
          reason: refundReason,
        }),
      });

      const result = await response.json();

      if (result.success) {
        toast({
          title: t('common:messages.success'),
          description: t('payments:messages.success.refundProcessed'),
        });
        setIsRefundDialogOpen(false);
        fetchTransactions();
        fetchMetrics();
      } else {
        toast({
          title: t('payments:messages.error.title'),
          description: result.error || t('payments:messages.error.processRefund'),
          variant: 'destructive',
        });
      }
    } catch (error) {
      console.error('Error processing refund:', error);
      toast({
        title: t('payments:messages.error.title'),
        description: t('payments:messages.error.processRefund'),
        variant: 'destructive',
      });
    }
  };

  const toggleProviderStatus = async (providerId: string, isActive: boolean) => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/api/payments/providers/${providerId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_active: !isActive }),
      });

      if (response.ok) {
        toast({
          title: t('common:messages.success'),
          description: isActive ? t('payments:messages.success.providerDisabled') : t('payments:messages.success.providerEnabled'),
        });
        fetchProviders();
      }
    } catch (error) {
      console.error('Error updating provider:', error);
      toast({
        title: t('payments:messages.error.title'),
        description: t('payments:messages.error.updateProvider'),
        variant: 'destructive',
      });
    }
  };

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      completed: { variant: 'success' as const, icon: CheckCircle },
      pending: { variant: 'warning' as const, icon: Clock },
      processing: { variant: 'secondary' as const, icon: RefreshCw },
      failed: { variant: 'destructive' as const, icon: XCircle },
      refunded: { variant: 'outline' as const, icon: Undo },
    };

    const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.pending;
    const Icon = config.icon;

    return (
      <Badge variant={config.variant} className="flex items-center gap-1">
        <Icon className="h-3 w-3" />
        {t(`payments:status.${status}`)}
      </Badge>
    );
  };

  const getProviderIcon = (providerType: string) => {
    switch (providerType) {
      case 'moneris':
        return <CreditCard className="h-4 w-4" />;
      case 'clover':
        return <Activity className="h-4 w-4" />;
      case 'interac':
        return <Shield className="h-4 w-4" />;
      default:
        return <CreditCard className="h-4 w-4" />;
    }
  };

  const filteredTransactions = transactions.filter(transaction => {
    const matchesSearch = searchTerm === '' || 
      transaction.transaction_reference.toLowerCase().includes(searchTerm.toLowerCase()) ||
      transaction.customer_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      transaction.order_id?.toLowerCase().includes(searchTerm.toLowerCase());
    
    return matchesSearch;
  });

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">{t('payments:titles.main')}</h1>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => fetchTransactions()}>
            <RefreshCw className="h-4 w-4 mr-2" />
            {t('payments:actions.refresh')}
          </Button>
          <Button variant="outline">
            <Download className="h-4 w-4 mr-2" />
            {t('payments:actions.export')}
          </Button>
        </div>
      </div>

      {/* Metrics Cards */}
      {metrics && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{t('payments:metrics.totalRevenue')}</CardTitle>
              <DollarSign className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">${metrics.total_amount.toFixed(2)}</div>
              <p className="text-xs text-muted-foreground">
                {metrics.total_transactions} {t('payments:metrics.transactions')}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{t('payments:metrics.successRate')}</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{metrics.success_rate.toFixed(1)}%</div>
              <p className="text-xs text-muted-foreground">
                {metrics.successful_transactions} {t('payments:metrics.successful')}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{t('payments:metrics.totalRefunds')}</CardTitle>
              <TrendingDown className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">${metrics.total_refunds.toFixed(2)}</div>
              <p className="text-xs text-muted-foreground">
                {t('payments:metrics.fromRevenue')}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{t('payments:metrics.processingFees')}</CardTitle>
              <AlertCircle className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">${metrics.total_fees.toFixed(2)}</div>
              <p className="text-xs text-muted-foreground">
                {((metrics.total_fees / metrics.total_amount) * 100).toFixed(2)}% {t('payments:metrics.ofRevenue')}
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      <Tabs defaultValue="transactions" className="space-y-4">
        <TabsList>
          <TabsTrigger value="transactions">{t('payments:tabs.transactions')}</TabsTrigger>
          <TabsTrigger value="providers">{t('payments:tabs.providers')}</TabsTrigger>
          <TabsTrigger value="methods">{t('payments:tabs.methods')}</TabsTrigger>
          <TabsTrigger value="settlements">{t('payments:tabs.settlements')}</TabsTrigger>
        </TabsList>

        <TabsContent value="transactions" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>{t('payments:titles.transactionHistory')}</CardTitle>
              <CardDescription>
                {t('payments:descriptions.transactionHistory')}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-col lg:flex-row gap-6 mb-4">
                <div className="flex-1">
                  <div className="relative">
                    <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                    <Input
                      placeholder={t('payments:filters.searchPlaceholder')}
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="pl-8"
                    />
                  </div>
                </div>
                <DateRangePicker
                  date={dateRange}
                  onDateChange={setDateRange}
                />
                <Select value={statusFilter} onValueChange={setStatusFilter}>
                  <SelectTrigger className="w-[180px]">
                    <SelectValue placeholder={t('payments:filters.status')} />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">{t('payments:filters.allStatus')}</SelectItem>
                    <SelectItem value="completed">{t('payments:status.completed')}</SelectItem>
                    <SelectItem value="pending">{t('payments:status.pending')}</SelectItem>
                    <SelectItem value="failed">{t('payments:status.failed')}</SelectItem>
                    <SelectItem value="refunded">{t('payments:status.refunded')}</SelectItem>
                  </SelectContent>
                </Select>
                <Select value={providerFilter} onValueChange={setProviderFilter}>
                  <SelectTrigger className="w-[180px]">
                    <SelectValue placeholder={t('payments:filters.provider')} />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">{t('payments:filters.allProviders')}</SelectItem>
                    {providers.map(provider => (
                      <SelectItem key={provider.id} value={provider.provider_type}>
                        {provider.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="rounded-lg border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>{t('payments:table.reference')}</TableHead>
                      <TableHead>{t('payments:table.customer')}</TableHead>
                      <TableHead>{t('payments:table.amount')}</TableHead>
                      <TableHead>{t('payments:table.provider')}</TableHead>
                      <TableHead>{t('payments:table.status')}</TableHead>
                      <TableHead>{t('payments:table.date')}</TableHead>
                      <TableHead>{t('payments:table.actions')}</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredTransactions.map((transaction) => (
                      <TableRow key={transaction.id}>
                        <TableCell className="font-medium">
                          {transaction.transaction_reference}
                        </TableCell>
                        <TableCell>{transaction.customer_name || 'N/A'}</TableCell>
                        <TableCell>
                          ${transaction.amount.toFixed(2)} {transaction.currency}
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            {getProviderIcon(transaction.provider_name)}
                            {transaction.provider_name}
                          </div>
                        </TableCell>
                        <TableCell>{getStatusBadge(transaction.status)}</TableCell>
                        <TableCell>
                          {format(new Date(transaction.created_at), 'MMM dd, yyyy HH:mm')}
                        </TableCell>
                        <TableCell>
                          <div className="flex gap-2">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => {
                                setSelectedTransaction(transaction);
                                setIsDetailDialogOpen(true);
                              }}
                            >
                              <Eye className="h-4 w-4" />
                            </Button>
                            {transaction.status === 'completed' && (
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => {
                                  setSelectedTransaction(transaction);
                                  setIsRefundDialogOpen(true);
                                }}
                              >
                                <Undo className="h-4 w-4" />
                              </Button>
                            )}
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="providers" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>{t('payments:titles.paymentProviders')}</CardTitle>
              <CardDescription>
                {t('payments:descriptions.paymentProviders')}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {providers.map((provider) => (
                  <Card key={provider.id}>
                    <CardHeader>
                      <div className="flex justify-between items-start">
                        <div className="flex items-center gap-2">
                          {getProviderIcon(provider.provider_type)}
                          <div>
                            <CardTitle className="text-lg">{provider.name}</CardTitle>
                            <CardDescription>{provider.provider_type}</CardDescription>
                          </div>
                        </div>
                        <div className="flex gap-2">
                          {provider.is_default && (
                            <Badge variant="secondary">{t('payments:provider.default')}</Badge>
                          )}
                          <Badge variant={provider.is_active ? 'success' : 'destructive'}>
                            {provider.is_active ? t('payments:status.active') : t('payments:status.inactive')}
                          </Badge>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => toggleProviderStatus(provider.id, provider.is_active)}
                          >
                            {provider.is_active ? t('payments:actions.disable') : t('payments:actions.enable')}
                          </Button>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-2 gap-6 text-sm">
                        <div>
                          <p className="text-muted-foreground">{t('payments:provider.supportedCurrencies')}</p>
                          <p className="font-medium">{provider.supported_currencies.join(', ')}</p>
                        </div>
                        <div>
                          <p className="text-muted-foreground">{t('payments:provider.capabilities')}</p>
                          <div className="flex flex-wrap gap-1 mt-1">
                            {Object.entries(provider.capabilities || {}).map(([key, value]) => (
                              value && (
                                <Badge key={key} variant="outline" className="text-xs">
                                  {key}
                                </Badge>
                              )
                            ))}
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="methods" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>{t('payments:titles.paymentMethods')}</CardTitle>
              <CardDescription>
                {t('payments:descriptions.paymentMethods')}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8 text-muted-foreground">
                {t('payments:messages.comingSoon.paymentMethods')}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="settlements" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>{t('payments:titles.settlements')}</CardTitle>
              <CardDescription>
                {t('payments:descriptions.settlements')}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8 text-muted-foreground">
                {t('payments:messages.comingSoon.settlements')}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Refund Dialog */}
      <Dialog open={isRefundDialogOpen} onOpenChange={setIsRefundDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t('payments:titles.processRefund')}</DialogTitle>
            <DialogDescription>
              {t('payments:descriptions.refundTransaction')} {selectedTransaction?.transaction_reference}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>{t('payments:refund.originalAmount')}</Label>
              <p className="text-2xl font-bold">
                ${selectedTransaction?.amount.toFixed(2)} {selectedTransaction?.currency}
              </p>
            </div>
            <div>
              <Label htmlFor="refund-amount">{t('payments:refund.refundAmount')} ({t('payments:refund.refundAmountHint')})</Label>
              <Input
                id="refund-amount"
                type="number"
                step="0.01"
                max={selectedTransaction?.amount}
                value={refundAmount}
                onChange={(e) => setRefundAmount(e.target.value)}
                placeholder={t('payments:refund.enterAmount')}
              />
            </div>
            <div>
              <Label htmlFor="refund-reason">{t('payments:refund.reason')}</Label>
              <Input
                id="refund-reason"
                value={refundReason}
                onChange={(e) => setRefundReason(e.target.value)}
                placeholder={t('payments:refund.enterReason')}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsRefundDialogOpen(false)}>
              {t('payments:actions.cancel')}
            </Button>
            <Button onClick={processRefund}>{t('payments:actions.processRefund')}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Transaction Detail Dialog */}
      <Dialog open={isDetailDialogOpen} onOpenChange={setIsDetailDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>{t('payments:titles.transactionDetails')}</DialogTitle>
            <DialogDescription>
              {selectedTransaction?.transaction_reference}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-6">
              <div>
                <Label>{t('payments:details.transactionId')}</Label>
                <p className="font-medium">{selectedTransaction?.id}</p>
              </div>
              <div>
                <Label>{t('payments:details.providerTransactionId')}</Label>
                <p className="font-medium">{selectedTransaction?.provider_transaction_id || t('payments:details.notAvailable')}</p>
              </div>
              <div>
                <Label>{t('payments:details.orderId')}</Label>
                <p className="font-medium">{selectedTransaction?.order_id || t('payments:details.notAvailable')}</p>
              </div>
              <div>
                <Label>{t('payments:details.status')}</Label>
                <div className="mt-1">
                  {selectedTransaction && getStatusBadge(selectedTransaction.status)}
                </div>
              </div>
              <div>
                <Label>{t('payments:details.amount')}</Label>
                <p className="font-medium">
                  ${selectedTransaction?.amount.toFixed(2)} {selectedTransaction?.currency}
                </p>
              </div>
              <div>
                <Label>{t('payments:details.provider')}</Label>
                <p className="font-medium">{selectedTransaction?.provider_name}</p>
              </div>
              <div>
                <Label>{t('payments:details.createdAt')}</Label>
                <p className="font-medium">
                  {selectedTransaction && format(new Date(selectedTransaction.created_at), 'PPpp')}
                </p>
              </div>
              <div>
                <Label>{t('payments:details.completedAt')}</Label>
                <p className="font-medium">
                  {selectedTransaction?.completed_at
                    ? format(new Date(selectedTransaction.completed_at), 'PPpp')
                    : t('payments:details.notAvailable')}
                </p>
              </div>
            </div>
            {selectedTransaction?.error_message && (
              <div>
                <Label>{t('payments:details.errorMessage')}</Label>
                <p className="font-medium text-destructive">{selectedTransaction.error_message}</p>
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsDetailDialogOpen(false)}>
              {t('payments:actions.close')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default PaymentsPage;