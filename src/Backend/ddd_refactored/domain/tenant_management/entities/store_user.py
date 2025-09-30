"""
StoreUser Entity
Following DDD Architecture Document Section 2.1
"""

from dataclasses import dataclass, field
from datetime import datetime, time
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from enum import Enum

from ....shared.domain_base import Entity, BusinessRuleViolation


class StoreUserRole(str, Enum):
    """Store-level user roles"""
    STORE_MANAGER = "store_manager"
    ASSISTANT_MANAGER = "assistant_manager"
    BUDTENDER = "budtender"
    INVENTORY_MANAGER = "inventory_manager"
    DELIVERY_DRIVER = "delivery_driver"
    CASHIER = "cashier"
    SECURITY = "security"


class StoreUserStatus(str, Enum):
    """Store user status"""
    ACTIVE = "active"
    ON_BREAK = "on_break"
    OFF_DUTY = "off_duty"
    ON_LEAVE = "on_leave"
    TERMINATED = "terminated"


class ShiftType(str, Enum):
    """Shift types"""
    MORNING = "morning"
    AFTERNOON = "afternoon"
    EVENING = "evening"
    NIGHT = "night"
    FLEXIBLE = "flexible"


@dataclass
class StoreUser(Entity):
    """
    StoreUser Entity - Manages user access at store level
    As defined in DDD_ARCHITECTURE_REFACTORING.md Section 2.1
    """
    store_id: UUID = field(default_factory=uuid4)
    tenant_user_id: UUID = field(default_factory=uuid4)  # Reference to TenantUser
    role: StoreUserRole = StoreUserRole.BUDTENDER
    status: StoreUserStatus = StoreUserStatus.ACTIVE

    # Schedule Information
    shift_type: Optional[ShiftType] = None
    scheduled_days: List[str] = field(default_factory=list)  # ["monday", "tuesday", ...]
    scheduled_start_time: Optional[time] = None
    scheduled_end_time: Optional[time] = None
    hours_per_week: float = 0.0

    # POS Access
    pos_pin: Optional[str] = None  # Hashed PIN for POS access
    pos_permissions: List[str] = field(default_factory=list)
    register_id: Optional[str] = None  # Assigned cash register

    # Performance Metrics
    sales_count: int = 0
    sales_total: float = 0.0
    average_transaction_value: float = 0.0
    customer_satisfaction_score: Optional[float] = None

    # Commission & Compensation
    commission_rate: float = 0.0  # Percentage
    hourly_rate: Optional[float] = None
    tips_collected: float = 0.0

    # Training & Certifications
    training_completed: List[str] = field(default_factory=list)
    certifications: List[Dict[str, Any]] = field(default_factory=list)
    smart_serve_number: Optional[str] = None
    smart_serve_expiry: Optional[datetime] = None

    # Activity Tracking
    clock_in_time: Optional[datetime] = None
    clock_out_time: Optional[datetime] = None
    total_hours_worked: float = 0.0
    break_minutes_taken: int = 0

    # Settings & Preferences
    notification_preferences: Dict[str, bool] = field(default_factory=dict)
    language_preference: str = "en"
    ui_preferences: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        store_id: UUID,
        tenant_user_id: UUID,
        role: StoreUserRole = StoreUserRole.BUDTENDER,
        shift_type: Optional[ShiftType] = None
    ) -> 'StoreUser':
        """Factory method to create a new store user"""
        store_user = cls(
            store_id=store_id,
            tenant_user_id=tenant_user_id,
            role=role,
            shift_type=shift_type,
            status=StoreUserStatus.OFF_DUTY
        )

        # Set default POS permissions based on role
        store_user.pos_permissions = cls._get_default_pos_permissions(role)

        # Set default notification preferences
        store_user.notification_preferences = {
            'shift_reminders': True,
            'inventory_alerts': role == StoreUserRole.INVENTORY_MANAGER,
            'sales_updates': role in [StoreUserRole.STORE_MANAGER, StoreUserRole.ASSISTANT_MANAGER],
            'delivery_notifications': role == StoreUserRole.DELIVERY_DRIVER
        }

        return store_user

    @staticmethod
    def _get_default_pos_permissions(role: StoreUserRole) -> List[str]:
        """Get default POS permissions for role"""
        permissions_map = {
            StoreUserRole.STORE_MANAGER: [
                'create_sale', 'void_sale', 'refund', 'discount',
                'open_register', 'close_register', 'view_reports',
                'manage_inventory', 'override_price'
            ],
            StoreUserRole.ASSISTANT_MANAGER: [
                'create_sale', 'void_sale', 'refund', 'discount',
                'open_register', 'close_register', 'view_reports'
            ],
            StoreUserRole.BUDTENDER: [
                'create_sale', 'void_sale', 'apply_discount'
            ],
            StoreUserRole.CASHIER: [
                'create_sale', 'void_sale'
            ],
            StoreUserRole.INVENTORY_MANAGER: [
                'manage_inventory', 'view_reports', 'create_sale'
            ],
            StoreUserRole.DELIVERY_DRIVER: [
                'view_delivery_orders', 'update_delivery_status'
            ],
            StoreUserRole.SECURITY: [
                'view_transactions', 'view_reports'
            ]
        }
        return permissions_map.get(role, [])

    def has_pos_permission(self, permission: str) -> bool:
        """Check if user has specific POS permission"""
        return permission in self.pos_permissions

    def grant_pos_permission(self, permission: str):
        """Grant POS permission"""
        if permission not in self.pos_permissions:
            self.pos_permissions.append(permission)
            self.mark_as_modified()

    def revoke_pos_permission(self, permission: str):
        """Revoke POS permission"""
        if permission in self.pos_permissions:
            self.pos_permissions.remove(permission)
            self.mark_as_modified()

    def clock_in(self, register_id: Optional[str] = None):
        """Clock in for shift"""
        if self.clock_in_time and not self.clock_out_time:
            raise BusinessRuleViolation("Already clocked in")

        self.clock_in_time = datetime.utcnow()
        self.clock_out_time = None
        self.status = StoreUserStatus.ACTIVE
        self.break_minutes_taken = 0

        if register_id:
            self.register_id = register_id

        self.mark_as_modified()

    def clock_out(self):
        """Clock out from shift"""
        if not self.clock_in_time:
            raise BusinessRuleViolation("Not clocked in")

        if self.clock_out_time:
            raise BusinessRuleViolation("Already clocked out")

        self.clock_out_time = datetime.utcnow()

        # Calculate hours worked
        time_diff = self.clock_out_time - self.clock_in_time
        hours_worked = time_diff.total_seconds() / 3600
        self.total_hours_worked += hours_worked

        self.status = StoreUserStatus.OFF_DUTY
        self.register_id = None
        self.mark_as_modified()

    def start_break(self):
        """Start a break"""
        if self.status != StoreUserStatus.ACTIVE:
            raise BusinessRuleViolation("Must be active to take a break")

        self.status = StoreUserStatus.ON_BREAK
        self.mark_as_modified()

    def end_break(self, minutes_taken: int):
        """End a break"""
        if self.status != StoreUserStatus.ON_BREAK:
            raise BusinessRuleViolation("Not currently on break")

        self.status = StoreUserStatus.ACTIVE
        self.break_minutes_taken += minutes_taken
        self.mark_as_modified()

    def update_schedule(
        self,
        shift_type: Optional[ShiftType] = None,
        scheduled_days: Optional[List[str]] = None,
        start_time: Optional[time] = None,
        end_time: Optional[time] = None,
        hours_per_week: Optional[float] = None
    ):
        """Update user schedule"""
        if shift_type:
            self.shift_type = shift_type

        if scheduled_days is not None:
            valid_days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
            for day in scheduled_days:
                if day.lower() not in valid_days:
                    raise BusinessRuleViolation(f"Invalid day: {day}")
            self.scheduled_days = [day.lower() for day in scheduled_days]

        if start_time:
            self.scheduled_start_time = start_time

        if end_time:
            self.scheduled_end_time = end_time

        if hours_per_week is not None:
            if hours_per_week < 0 or hours_per_week > 60:
                raise BusinessRuleViolation("Hours per week must be between 0 and 60")
            self.hours_per_week = hours_per_week

        self.mark_as_modified()

    def record_sale(self, amount: float):
        """Record a sale made by this user"""
        self.sales_count += 1
        self.sales_total += amount
        self.average_transaction_value = self.sales_total / self.sales_count
        self.mark_as_modified()

    def add_training(self, training_name: str, completion_date: Optional[datetime] = None):
        """Add completed training"""
        if training_name not in self.training_completed:
            self.training_completed.append(training_name)
            self.mark_as_modified()

    def add_certification(
        self,
        name: str,
        issuer: str,
        issue_date: datetime,
        expiry_date: Optional[datetime] = None,
        certification_number: Optional[str] = None
    ):
        """Add a certification"""
        cert = {
            'name': name,
            'issuer': issuer,
            'issue_date': issue_date.isoformat(),
            'expiry_date': expiry_date.isoformat() if expiry_date else None,
            'certification_number': certification_number
        }
        self.certifications.append(cert)
        self.mark_as_modified()

    def update_smart_serve(self, smart_serve_number: str, expiry_date: datetime):
        """Update Smart Serve certification"""
        if expiry_date <= datetime.utcnow():
            raise BusinessRuleViolation("Smart Serve expiry date must be in the future")

        self.smart_serve_number = smart_serve_number
        self.smart_serve_expiry = expiry_date
        self.mark_as_modified()

    def is_smart_serve_valid(self) -> bool:
        """Check if Smart Serve is valid"""
        if not self.smart_serve_number or not self.smart_serve_expiry:
            return False
        return self.smart_serve_expiry > datetime.utcnow()

    def is_scheduled_now(self) -> bool:
        """Check if user is scheduled for current time"""
        if not self.scheduled_days or not self.scheduled_start_time or not self.scheduled_end_time:
            return False

        now = datetime.utcnow()
        current_day = now.strftime('%A').lower()
        current_time = now.time()

        if current_day not in self.scheduled_days:
            return False

        return self.scheduled_start_time <= current_time <= self.scheduled_end_time

    def calculate_commission(self, sales_amount: float) -> float:
        """Calculate commission for sales amount"""
        return sales_amount * (self.commission_rate / 100)

    def terminate(self, reason: Optional[str] = None):
        """Terminate employment"""
        self.status = StoreUserStatus.TERMINATED
        self.clock_out_time = datetime.utcnow() if self.clock_in_time and not self.clock_out_time else self.clock_out_time

        if reason:
            self.ui_preferences['termination_reason'] = reason
            self.ui_preferences['termination_date'] = datetime.utcnow().isoformat()

        self.mark_as_modified()

    def validate(self) -> List[str]:
        """Validate store user data"""
        errors = []

        if not self.store_id:
            errors.append("Store ID is required")

        if not self.tenant_user_id:
            errors.append("Tenant User ID is required")

        if self.commission_rate < 0 or self.commission_rate > 100:
            errors.append("Commission rate must be between 0 and 100")

        if self.hours_per_week < 0 or self.hours_per_week > 60:
            errors.append("Hours per week must be between 0 and 60")

        return errors