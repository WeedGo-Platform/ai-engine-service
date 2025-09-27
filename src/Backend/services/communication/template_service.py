"""
Message Template Service
Manages reusable message templates with variable substitution and validation
"""

import logging
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
import json
import re
import uuid
from jinja2 import Template, Environment, meta, TemplateSyntaxError

logger = logging.getLogger(__name__)


class TemplateService:
    """
    Service for managing message templates
    Supports variable substitution, validation, and multi-channel templates
    """

    def __init__(self, db_pool):
        self.db_pool = db_pool

        # Jinja2 environment for template rendering
        self.jinja_env = Environment(
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True
        )

        # Default system templates
        self.system_templates = {
            "welcome_email": {
                "name": "Welcome Email",
                "channel": "email",
                "category": "transactional",
                "subject": "Welcome to {{store_name}}!",
                "content": """
                    <h1>Welcome {{customer_name}}!</h1>
                    <p>Thank you for joining {{store_name}}. We're excited to have you as part of our community.</p>
                    <p>As a new member, you can:</p>
                    <ul>
                        <li>Browse our extensive catalog of products</li>
                        <li>Enjoy member-exclusive deals</li>
                        <li>Track your orders in real-time</li>
                        <li>Earn loyalty points with every purchase</li>
                    </ul>
                    <p>Get started by <a href="{{store_url}}">visiting our store</a>.</p>
                    <p>Best regards,<br>The {{store_name}} Team</p>
                """,
                "variables": {
                    "customer_name": {"type": "string", "required": True},
                    "store_name": {"type": "string", "required": True},
                    "store_url": {"type": "string", "required": True}
                }
            },
            "order_confirmation_email": {
                "name": "Order Confirmation",
                "channel": "email",
                "category": "transactional",
                "subject": "Order #{{order_number}} Confirmed",
                "content": """
                    <h1>Order Confirmation</h1>
                    <p>Hi {{customer_name}},</p>
                    <p>Your order #{{order_number}} has been confirmed!</p>
                    <div style="border: 1px solid #ddd; padding: 15px; margin: 20px 0;">
                        <h3>Order Details:</h3>
                        <p>Total Amount: ${{total_amount}}</p>
                        <p>Items: {{item_count}}</p>
                        <p>Estimated Delivery: {{delivery_date}}</p>
                    </div>
                    <p><a href="{{tracking_url}}">Track your order</a></p>
                    <p>Thank you for your purchase!</p>
                """,
                "variables": {
                    "customer_name": {"type": "string", "required": True},
                    "order_number": {"type": "string", "required": True},
                    "total_amount": {"type": "number", "required": True},
                    "item_count": {"type": "number", "required": True},
                    "delivery_date": {"type": "string", "required": True},
                    "tracking_url": {"type": "string", "required": True}
                }
            },
            "order_confirmation_sms": {
                "name": "Order Confirmation SMS",
                "channel": "sms",
                "category": "transactional",
                "subject": None,
                "content": "Hi {{customer_name}}, Order #{{order_number}} confirmed! Total: ${{total_amount}}. Track: {{tracking_url}}",
                "variables": {
                    "customer_name": {"type": "string", "required": True},
                    "order_number": {"type": "string", "required": True},
                    "total_amount": {"type": "number", "required": True},
                    "tracking_url": {"type": "string", "required": True}
                }
            },
            "promotional_email": {
                "name": "Promotional Campaign",
                "channel": "email",
                "category": "promotional",
                "subject": "{{promotion_title}} - Save {{discount_percentage}}%!",
                "content": """
                    <h1>{{promotion_title}}</h1>
                    <p>Hi {{customer_name}},</p>
                    <p>{{promotion_description}}</p>
                    <div style="text-align: center; margin: 30px 0;">
                        <h2>Save {{discount_percentage}}%</h2>
                        <p>Use code: <strong>{{promo_code}}</strong></p>
                        <a href="{{shop_url}}" style="display: inline-block; padding: 12px 30px; background: #007bff; color: white; text-decoration: none; border-radius: 5px;">Shop Now</a>
                    </div>
                    <p><small>Valid until {{expiry_date}}. Terms and conditions apply.</small></p>
                """,
                "variables": {
                    "customer_name": {"type": "string", "required": True},
                    "promotion_title": {"type": "string", "required": True},
                    "promotion_description": {"type": "string", "required": True},
                    "discount_percentage": {"type": "number", "required": True},
                    "promo_code": {"type": "string", "required": True},
                    "shop_url": {"type": "string", "required": True},
                    "expiry_date": {"type": "string", "required": True}
                }
            },
            "birthday_greeting": {
                "name": "Birthday Greeting",
                "channel": "email",
                "category": "promotional",
                "subject": "Happy Birthday {{customer_name}}! 🎉",
                "content": """
                    <h1>Happy Birthday {{customer_name}}! 🎉</h1>
                    <p>We hope you have a wonderful day!</p>
                    <p>As our gift to you, enjoy <strong>{{birthday_discount}}% off</strong> your next purchase.</p>
                    <p>Use code: <strong>BIRTHDAY{{birthday_code}}</strong></p>
                    <p>Valid for the next {{validity_days}} days.</p>
                    <p>Warmest wishes,<br>The {{store_name}} Team</p>
                """,
                "variables": {
                    "customer_name": {"type": "string", "required": True},
                    "birthday_discount": {"type": "number", "required": True},
                    "birthday_code": {"type": "string", "required": True},
                    "validity_days": {"type": "number", "required": True},
                    "store_name": {"type": "string", "required": True}
                }
            },
            "abandoned_cart": {
                "name": "Abandoned Cart Reminder",
                "channel": "email",
                "category": "promotional",
                "subject": "You left something behind...",
                "content": """
                    <h1>Your cart is waiting for you!</h1>
                    <p>Hi {{customer_name}},</p>
                    <p>You have {{item_count}} items in your cart worth ${{cart_value}}.</p>
                    <p>Complete your purchase now and we'll give you <strong>{{discount}}% off</strong>!</p>
                    <a href="{{cart_url}}">Return to Cart</a>
                    <p>This offer expires in {{hours_remaining}} hours.</p>
                """,
                "variables": {
                    "customer_name": {"type": "string", "required": True},
                    "item_count": {"type": "number", "required": True},
                    "cart_value": {"type": "number", "required": True},
                    "discount": {"type": "number", "required": True},
                    "cart_url": {"type": "string", "required": True},
                    "hours_remaining": {"type": "number", "required": True}
                }
            },
            "review_request": {
                "name": "Review Request",
                "channel": "email",
                "category": "transactional",
                "subject": "How was your experience with {{product_name}}?",
                "content": """
                    <h1>Share Your Feedback</h1>
                    <p>Hi {{customer_name}},</p>
                    <p>We hope you're enjoying your {{product_name}}!</p>
                    <p>Your opinion matters to us and helps other customers make informed decisions.</p>
                    <a href="{{review_url}}">Write a Review</a>
                    <p>As a thank you, you'll earn {{points}} loyalty points for your review.</p>
                """,
                "variables": {
                    "customer_name": {"type": "string", "required": True},
                    "product_name": {"type": "string", "required": True},
                    "review_url": {"type": "string", "required": True},
                    "points": {"type": "number", "required": True}
                }
            },
            "push_notification": {
                "name": "Push Notification Template",
                "channel": "push",
                "category": "alert",
                "subject": "{{notification_title}}",
                "content": "{{notification_body}}",
                "variables": {
                    "notification_title": {"type": "string", "required": True},
                    "notification_body": {"type": "string", "required": True},
                    "action_url": {"type": "string", "required": False}
                }
            }
        }

    async def create_template(
        self,
        name: str,
        channel_type: str,
        category: str,
        subject: Optional[str],
        content: str,
        variables: Dict[str, Any],
        store_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        created_by: str = None,
        is_global: bool = False
    ) -> str:
        """
        Create a new message template

        Args:
            name: Template name
            channel_type: Channel type (email, sms, push)
            category: Template category
            subject: Message subject (for email/push)
            content: Template content with variables
            variables: Variable definitions
            store_id: Store ID (for store-specific templates)
            tenant_id: Tenant ID (for tenant-specific templates)
            created_by: User who created the template
            is_global: Whether template is system-wide

        Returns:
            Template ID
        """
        # Validate template syntax
        validation_result = self.validate_template_syntax(content)
        if not validation_result["valid"]:
            raise ValueError(f"Invalid template syntax: {validation_result['error']}")

        # Extract variables from content
        detected_variables = self.extract_variables(content)
        if subject:
            detected_variables.update(self.extract_variables(subject))

        async with self.db_pool.acquire() as conn:
            template_id = await conn.fetchval("""
                INSERT INTO message_templates (
                    name, description, channel_type, category,
                    subject, content, variables,
                    store_id, tenant_id, is_global,
                    created_by, created_at, is_active
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, NOW(), true)
                RETURNING id
            """, name, f"Template for {channel_type}",
                channel_type, category, subject, content,
                json.dumps(variables),
                uuid.UUID(store_id) if store_id else None,
                uuid.UUID(tenant_id) if tenant_id else None,
                is_global,
                uuid.UUID(created_by) if created_by else None)

            return str(template_id)

    async def update_template(
        self,
        template_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """Update an existing template"""
        async with self.db_pool.acquire() as conn:
            # Build update query dynamically
            set_clauses = []
            params = []
            param_count = 1

            for field, value in updates.items():
                if field in ["name", "subject", "content", "category", "variables"]:
                    set_clauses.append(f"{field} = ${param_count}")
                    if field == "variables" and isinstance(value, dict):
                        params.append(json.dumps(value))
                    else:
                        params.append(value)
                    param_count += 1

            if not set_clauses:
                return False

            params.append(uuid.UUID(template_id))
            query = f"""
                UPDATE message_templates
                SET {', '.join(set_clauses)}, updated_at = NOW()
                WHERE id = ${param_count}
            """

            result = await conn.execute(query, *params)

            # Update usage count
            if result:
                await conn.execute("""
                    UPDATE message_templates
                    SET usage_count = usage_count + 1, last_used_at = NOW()
                    WHERE id = $1
                """, uuid.UUID(template_id))

            return bool(result)

    async def get_template(
        self,
        template_id: Optional[str] = None,
        name: Optional[str] = None,
        channel_type: Optional[str] = None,
        store_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get a specific template"""
        async with self.db_pool.acquire() as conn:
            query = "SELECT * FROM message_templates WHERE is_active = true"
            params = []
            param_count = 1

            if template_id:
                query += f" AND id = ${param_count}"
                params.append(uuid.UUID(template_id))
                param_count += 1
            elif name:
                # Check system templates first
                if name in self.system_templates:
                    return self.system_templates[name]

                query += f" AND name = ${param_count}"
                params.append(name)
                param_count += 1

            if channel_type:
                query += f" AND channel_type = ${param_count}"
                params.append(channel_type)
                param_count += 1

            if store_id:
                query += f" AND (store_id = ${param_count} OR is_global = true)"
                params.append(uuid.UUID(store_id))

            template = await conn.fetchrow(query, *params)

            if template:
                return dict(template)
            return None

    async def list_templates(
        self,
        store_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        channel_type: Optional[str] = None,
        category: Optional[str] = None,
        include_system: bool = True
    ) -> List[Dict[str, Any]]:
        """List available templates"""
        templates = []

        # Include system templates if requested
        if include_system:
            for key, template in self.system_templates.items():
                if channel_type and template["channel"] != channel_type:
                    continue
                if category and template["category"] != category:
                    continue

                templates.append({
                    "id": key,
                    "name": template["name"],
                    "channel_type": template["channel"],
                    "category": template["category"],
                    "is_system": True,
                    "variables": template["variables"]
                })

        # Get custom templates from database
        async with self.db_pool.acquire() as conn:
            query = """
                SELECT id, name, channel_type, category, subject,
                       variables, usage_count, last_used_at,
                       is_global, created_at
                FROM message_templates
                WHERE is_active = true
            """
            params = []
            param_count = 1

            if store_id and store_id.strip():
                query += f" AND (store_id = ${param_count} OR is_global = true)"
                params.append(uuid.UUID(store_id))
                param_count += 1

            if tenant_id and tenant_id.strip():
                query += f" AND (tenant_id = ${param_count} OR is_global = true)"
                params.append(uuid.UUID(tenant_id))
                param_count += 1

            if channel_type:
                query += f" AND channel_type = ${param_count}"
                params.append(channel_type)
                param_count += 1

            if category:
                query += f" AND category = ${param_count}"
                params.append(category)
                param_count += 1

            query += " ORDER BY usage_count DESC, created_at DESC"

            db_templates = await conn.fetch(query, *params)

            for template in db_templates:
                templates.append({
                    "id": str(template["id"]),
                    "name": template["name"],
                    "channel_type": template["channel_type"],
                    "category": template["category"],
                    "subject": template["subject"],
                    "variables": json.loads(template["variables"]) if template["variables"] else {},
                    "usage_count": template["usage_count"],
                    "last_used_at": template["last_used_at"].isoformat() if template["last_used_at"] else None,
                    "is_global": template["is_global"],
                    "is_system": False
                })

        return templates

    async def render_template(
        self,
        template_id: Optional[str] = None,
        template_name: Optional[str] = None,
        variables: Dict[str, Any] = None,
        channel_type: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Render a template with variables

        Args:
            template_id: Template ID
            template_name: Template name (for system templates)
            variables: Variable values
            channel_type: Channel type filter

        Returns:
            Rendered subject and content
        """
        # Get template
        if template_name and template_name in self.system_templates:
            template = self.system_templates[template_name]
        else:
            template = await self.get_template(
                template_id=template_id,
                name=template_name,
                channel_type=channel_type
            )

        if not template:
            raise ValueError("Template not found")

        # Prepare variables
        render_vars = variables or {}

        # Add default variables
        render_vars.setdefault("current_year", datetime.now().year)
        render_vars.setdefault("current_date", datetime.now().strftime("%B %d, %Y"))

        # Render content
        try:
            content_template = self.jinja_env.from_string(template["content"])
            rendered_content = content_template.render(**render_vars)

            # Render subject if present
            rendered_subject = None
            if template.get("subject"):
                subject_template = self.jinja_env.from_string(template["subject"])
                rendered_subject = subject_template.render(**render_vars)

            return {
                "subject": rendered_subject,
                "content": rendered_content,
                "channel_type": template.get("channel_type") or template.get("channel")
            }

        except Exception as e:
            logger.error(f"Template rendering error: {e}")
            raise ValueError(f"Failed to render template: {e}")

    def validate_template_syntax(self, template_content: str) -> Dict[str, Any]:
        """Validate Jinja2 template syntax"""
        try:
            self.jinja_env.from_string(template_content)
            return {"valid": True}
        except TemplateSyntaxError as e:
            return {
                "valid": False,
                "error": str(e),
                "line": e.lineno
            }

    def extract_variables(self, template_content: str) -> Set[str]:
        """Extract variable names from template"""
        try:
            ast = self.jinja_env.parse(template_content)
            return meta.find_undeclared_variables(ast)
        except:
            # Fallback to regex for simple cases
            pattern = r'\{\{[\s]*(\w+)[\s]*\}\}'
            matches = re.findall(pattern, template_content)
            return set(matches)

    async def preview_template(
        self,
        template_id: Optional[str] = None,
        template_name: Optional[str] = None,
        sample_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Preview a template with sample data

        Args:
            template_id: Template ID
            template_name: Template name
            sample_data: Sample variable values

        Returns:
            Preview of rendered template
        """
        # Get template
        if template_name and template_name in self.system_templates:
            template = self.system_templates[template_name]
        else:
            template = await self.get_template(template_id=template_id, name=template_name)

        if not template:
            return {"error": "Template not found"}

        # Generate sample data if not provided
        if not sample_data:
            sample_data = self._generate_sample_data(template.get("variables", {}))

        # Render template
        try:
            rendered = await self.render_template(
                template_id=template_id,
                template_name=template_name,
                variables=sample_data
            )

            return {
                "template_name": template.get("name"),
                "channel_type": template.get("channel_type") or template.get("channel"),
                "subject": rendered["subject"],
                "content": rendered["content"],
                "sample_data": sample_data,
                "variables": template.get("variables", {})
            }
        except Exception as e:
            return {"error": str(e)}

    def _generate_sample_data(self, variables: Any) -> Dict[str, Any]:
        """Generate sample data for template variables"""
        sample_data = {}

        # Handle different variable formats
        if isinstance(variables, dict):
            for var_name, var_info in variables.items():
                if isinstance(var_info, dict):
                    var_type = var_info.get("type", "string")
                    if var_type == "string":
                        sample_data[var_name] = f"Sample {var_name}"
                    elif var_type == "number":
                        sample_data[var_name] = 42
                    elif var_type == "boolean":
                        sample_data[var_name] = True
                    elif var_type == "date":
                        sample_data[var_name] = datetime.now().strftime("%Y-%m-%d")
                else:
                    sample_data[var_name] = f"Sample {var_name}"

        # Common sample values
        sample_data.setdefault("customer_name", "John Doe")
        sample_data.setdefault("store_name", "WeedGo Store")
        sample_data.setdefault("store_url", "https://weedgo.ai")
        sample_data.setdefault("order_number", "ORD-12345")
        sample_data.setdefault("total_amount", 99.99)
        sample_data.setdefault("tracking_url", "https://weedgo.ai/track/12345")
        sample_data.setdefault("promo_code", "SAVE20")
        sample_data.setdefault("discount_percentage", 20)
        sample_data.setdefault("expiry_date", "December 31, 2024")

        return sample_data

    async def delete_template(self, template_id: str) -> bool:
        """Soft delete a template"""
        async with self.db_pool.acquire() as conn:
            result = await conn.execute("""
                UPDATE message_templates
                SET is_active = false, updated_at = NOW()
                WHERE id = $1
            """, uuid.UUID(template_id))
            return bool(result)

    async def duplicate_template(
        self,
        template_id: str,
        new_name: str,
        store_id: Optional[str] = None,
        created_by: Optional[str] = None
    ) -> str:
        """Duplicate an existing template"""
        template = await self.get_template(template_id=template_id)

        if not template:
            raise ValueError("Template not found")

        return await self.create_template(
            name=new_name,
            channel_type=template["channel_type"],
            category=template["category"],
            subject=template.get("subject"),
            content=template["content"],
            variables=json.loads(template["variables"]) if template["variables"] else {},
            store_id=store_id,
            created_by=created_by
        )