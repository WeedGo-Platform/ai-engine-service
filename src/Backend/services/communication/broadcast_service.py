"""
Broadcast Orchestrator Service
Coordinates multi-channel message broadcasting with recipient segmentation,
scheduling, and analytics tracking
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Set, Union
from uuid import UUID
from datetime import datetime, timedelta
from enum import Enum
import json
import uuid

from .base_channel import (
    ICommunicationChannel,
    ChannelType,
    ChannelConfig,
    Recipient,
    Message,
    DeliveryResult,
    DeliveryStatus,
    MessagePriority
)
from .email_service import EmailService
from .sms_service import SMSService
from .push_notification_service import PushNotificationService

logger = logging.getLogger(__name__)


class BroadcastStatus(Enum):
    """Broadcast campaign status"""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    SENDING = "sending"
    SENT = "sent"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    FAILED = "failed"


class BroadcastService:
    """
    Main orchestrator for broadcast campaigns
    Manages multi-channel message distribution
    """

    def __init__(self, db_pool, redis_client=None, tenant_id: Optional[str] = None):
        self.db_pool = db_pool
        self.redis_client = redis_client
        self.tenant_id = tenant_id
        self.tenant_settings = {}

        # Initialize channel services
        self.channels: Dict[ChannelType, ICommunicationChannel] = {}
        self._initialize_channels()

        # Background tasks
        self._scheduler_task = None
        self._analytics_task = None

        # Rate limiting
        self._send_semaphore = asyncio.Semaphore(10)  # Max concurrent sends

    async def _load_tenant_settings(self):
        """Load tenant communication settings from database"""
        if self.tenant_id:
            try:
                async with self.db_pool.acquire() as conn:
                    settings = await conn.fetchval("""
                        SELECT settings FROM tenants WHERE id = $1
                    """, UUID(self.tenant_id) if isinstance(self.tenant_id, str) else self.tenant_id)

                    if settings:
                        self.tenant_settings = settings.get('communication', {})
            except Exception as e:
                logger.warning(f"Failed to load tenant settings: {e}")

    def _initialize_channels(self):
        """Initialize communication channel services"""
        # Load tenant settings first
        if self.tenant_id:
            # Run async load synchronously for initialization
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self._load_tenant_settings())
            else:
                loop.run_until_complete(self._load_tenant_settings())

        # Email channel
        email_config = ChannelConfig(
            enabled=True,
            rate_limit=100,
            retry_attempts=3,
            batch_size=100,
            cost_per_message=0.001
        )
        self.channels[ChannelType.EMAIL] = EmailService(
            email_config,
            tenant_settings=self.tenant_settings
        )

        # SMS channel
        sms_config = ChannelConfig(
            enabled=True,
            rate_limit=50,
            retry_attempts=2,
            batch_size=50,
            cost_per_message=0.02
        )
        self.channels[ChannelType.SMS] = SMSService(
            sms_config,
            tenant_settings=self.tenant_settings
        )

        # Push notification channel
        push_config = ChannelConfig(
            enabled=True,
            rate_limit=200,
            retry_attempts=3,
            batch_size=500,
            cost_per_message=0.0001
        )
        self.channels[ChannelType.PUSH] = PushNotificationService(push_config)

    async def create_broadcast(
        self,
        name: str,
        store_id: str,
        tenant_id: str,
        created_by: str,
        channels: List[str],
        messages: Dict[str, Dict[str, Any]],
        recipients: Optional[List[str]] = None,
        segment_criteria: Optional[Dict[str, Any]] = None,
        scheduled_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a new broadcast campaign

        Args:
            name: Campaign name
            store_id: Store ID
            tenant_id: Tenant ID
            created_by: User ID who created the broadcast
            channels: List of channel types to use
            messages: Message content per channel
            recipients: List of recipient IDs (optional)
            segment_criteria: Criteria for recipient segmentation (optional)
            scheduled_at: Schedule time for the broadcast
            metadata: Additional metadata

        Returns:
            Broadcast ID
        """
        async with self.db_pool.acquire() as conn:
            # Create broadcast record
            broadcast_id = await conn.fetchval("""
                INSERT INTO broadcasts (
                    name, description, store_id, tenant_id, created_by,
                    status, scheduled_at, metadata, send_immediately
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                RETURNING id
            """, name, metadata.get("description", ""),
                store_id, tenant_id, created_by,
                BroadcastStatus.SCHEDULED.value if scheduled_at else BroadcastStatus.DRAFT.value,
                scheduled_at, json.dumps(metadata or {}),
                not bool(scheduled_at))

            # Create message records for each channel
            for channel_type in channels:
                if channel_type in messages:
                    msg_data = messages[channel_type]
                    await conn.execute("""
                        INSERT INTO broadcast_messages (
                            broadcast_id, channel_type, subject, content,
                            template_id, template_variables, sender_name,
                            sender_email, sender_phone, push_title,
                            push_image_url, push_action_url, priority
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                    """, broadcast_id, channel_type,
                        msg_data.get("subject"), msg_data.get("content"),
                        msg_data.get("template_id"), json.dumps(msg_data.get("template_variables", {})),
                        msg_data.get("sender_name"), msg_data.get("sender_email"),
                        msg_data.get("sender_phone"), msg_data.get("push_title"),
                        msg_data.get("push_image_url"), msg_data.get("push_action_url"),
                        msg_data.get("priority", "normal"))

            # Add recipients if provided
            if recipients:
                await self._add_recipients(conn, broadcast_id, recipients, channels)

            # Add segment criteria if provided
            if segment_criteria:
                await conn.execute("""
                    INSERT INTO broadcast_segments (broadcast_id, criteria)
                    VALUES ($1, $2)
                """, broadcast_id, json.dumps(segment_criteria))

            # Log audit
            await self._log_audit(
                conn, broadcast_id, "create", created_by,
                {"channels": channels, "recipient_count": len(recipients or [])}
            )

            # Schedule if needed
            if scheduled_at:
                await self._schedule_broadcast(broadcast_id, scheduled_at)

            return str(broadcast_id)

    async def execute_broadcast(
        self,
        broadcast_id: str,
        force_send: bool = False
    ) -> Dict[str, Any]:
        """
        Execute a broadcast campaign

        Args:
            broadcast_id: Broadcast ID
            force_send: Force send even if scheduled for later

        Returns:
            Execution result with statistics
        """
        async with self._send_semaphore:
            async with self.db_pool.acquire() as conn:
                # Get broadcast details
                broadcast = await conn.fetchrow("""
                    SELECT * FROM broadcasts WHERE id = $1
                """, uuid.UUID(broadcast_id))

                if not broadcast:
                    raise ValueError(f"Broadcast {broadcast_id} not found")

                # Check status
                if broadcast["status"] in ["sent", "sending", "cancelled"]:
                    return {
                        "error": f"Cannot send broadcast with status: {broadcast['status']}"
                    }

                # Update status to sending
                await conn.execute("""
                    UPDATE broadcasts
                    SET status = $1, started_at = $2
                    WHERE id = $3
                """, BroadcastStatus.SENDING.value, datetime.now(),
                    uuid.UUID(broadcast_id))

                # Get messages for all channels
                messages = await conn.fetch("""
                    SELECT * FROM broadcast_messages
                    WHERE broadcast_id = $1 AND is_active = true
                """, uuid.UUID(broadcast_id))

                # Get recipients
                recipients = await self._get_broadcast_recipients(conn, broadcast_id)

                # Send via each channel
                results = {
                    "broadcast_id": broadcast_id,
                    "total_recipients": len(recipients),
                    "channels": {},
                    "started_at": datetime.now().isoformat()
                }

                for msg in messages:
                    channel_type = ChannelType(msg["channel_type"])
                    if channel_type in self.channels:
                        channel_results = await self._send_via_channel(
                            conn, broadcast_id, channel_type, msg, recipients
                        )
                        results["channels"][msg["channel_type"]] = channel_results

                # Update broadcast statistics
                total_sent = sum(r.get("sent", 0) for r in results["channels"].values())
                total_failed = sum(r.get("failed", 0) for r in results["channels"].values())

                await conn.execute("""
                    UPDATE broadcasts
                    SET status = $1, completed_at = $2,
                        successful_sends = $3, failed_sends = $4
                    WHERE id = $5
                """, BroadcastStatus.SENT.value if total_failed == 0 else BroadcastStatus.FAILED.value,
                    datetime.now(), total_sent, total_failed, uuid.UUID(broadcast_id))

                # Calculate analytics
                await self._update_analytics(conn, broadcast_id, results)

                # Log audit
                await self._log_audit(
                    conn, broadcast_id, "send", broadcast["created_by"],
                    {"results": results}
                )

                results["completed_at"] = datetime.now().isoformat()
                return results

    async def _send_via_channel(
        self,
        conn,
        broadcast_id: str,
        channel_type: ChannelType,
        message_record,
        all_recipients: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Send message via specific channel"""
        channel = self.channels[channel_type]

        # Filter recipients for this channel
        recipients = []
        for r in all_recipients:
            # Check if channel is enabled for recipient
            channels = r.get("channels", {})
            if isinstance(channels, str):
                channels = json.loads(channels)

            if channels.get(channel_type.value, True):
                # Create Recipient object
                recipient = Recipient(
                    id=str(r["customer_id"]),
                    email=r.get("email"),
                    phone=r.get("phone_number"),
                    push_token=r.get("push_token"),
                    name=r.get("name"),
                    metadata=r.get("metadata")
                )

                # Validate recipient for channel
                is_valid, _ = await channel.validate_recipient(recipient)
                if is_valid:
                    recipients.append(recipient)

        if not recipients:
            return {"sent": 0, "failed": 0, "skipped": len(all_recipients)}

        # Create Message object
        message = Message(
            subject=message_record.get("subject"),
            content=message_record["content"],
            template_id=str(message_record["template_id"]) if message_record.get("template_id") else None,
            template_variables=json.loads(message_record.get("template_variables", "{}")),
            priority=MessagePriority(message_record.get("priority", "normal")),
            sender_name=message_record.get("sender_name"),
            sender_email=message_record.get("sender_email"),
            sender_phone=message_record.get("sender_phone"),
            push_title=message_record.get("push_title"),
            push_image_url=message_record.get("push_image_url"),
            push_action_url=message_record.get("push_action_url"),
            push_badge_count=message_record.get("push_badge_count")
        )

        # Send batch
        results = await channel.send_batch(recipients, message)

        # Update recipient statuses
        sent_count = 0
        failed_count = 0

        for result in results:
            status_field = f"{channel_type.value}_status"
            sent_at_field = f"{channel_type.value}_sent_at"
            error_field = f"{channel_type.value}_error"

            if result.status in [DeliveryStatus.SENT, DeliveryStatus.DELIVERED]:
                sent_count += 1
                await conn.execute(f"""
                    UPDATE broadcast_recipients
                    SET {status_field} = $1, {sent_at_field} = $2
                    WHERE broadcast_id = $3 AND customer_id = $4
                """, result.status.value, result.sent_at,
                    uuid.UUID(broadcast_id), result.recipient_id)
            else:
                failed_count += 1
                await conn.execute(f"""
                    UPDATE broadcast_recipients
                    SET {status_field} = $1, {error_field} = $2
                    WHERE broadcast_id = $3 AND customer_id = $4
                """, result.status.value, result.error_message,
                    uuid.UUID(broadcast_id), result.recipient_id)

        return {
            "sent": sent_count,
            "failed": failed_count,
            "total": len(recipients),
            "skipped": len(all_recipients) - len(recipients)
        }

    async def pause_broadcast(self, broadcast_id: str, user_id: str) -> bool:
        """Pause an ongoing broadcast"""
        async with self.db_pool.acquire() as conn:
            result = await conn.execute("""
                UPDATE broadcasts
                SET status = $1
                WHERE id = $2 AND status = $3
            """, BroadcastStatus.PAUSED.value, uuid.UUID(broadcast_id),
                BroadcastStatus.SENDING.value)

            if result:
                await self._log_audit(conn, broadcast_id, "pause", user_id, {})
                return True
            return False

    async def resume_broadcast(self, broadcast_id: str, user_id: str) -> bool:
        """Resume a paused broadcast"""
        async with self.db_pool.acquire() as conn:
            result = await conn.execute("""
                UPDATE broadcasts
                SET status = $1
                WHERE id = $2 AND status = $3
            """, BroadcastStatus.SENDING.value, uuid.UUID(broadcast_id),
                BroadcastStatus.PAUSED.value)

            if result:
                await self._log_audit(conn, broadcast_id, "resume", user_id, {})
                # Re-execute broadcast
                asyncio.create_task(self.execute_broadcast(broadcast_id))
                return True
            return False

    async def cancel_broadcast(self, broadcast_id: str, user_id: str) -> bool:
        """Cancel a scheduled or ongoing broadcast"""
        async with self.db_pool.acquire() as conn:
            result = await conn.execute("""
                UPDATE broadcasts
                SET status = $1, cancelled_at = $2
                WHERE id = $3 AND status IN ($4, $5, $6)
            """, BroadcastStatus.CANCELLED.value, datetime.now(),
                uuid.UUID(broadcast_id), BroadcastStatus.SCHEDULED.value,
                BroadcastStatus.SENDING.value, BroadcastStatus.PAUSED.value)

            if result:
                await self._log_audit(conn, broadcast_id, "cancel", user_id, {})
                return True
            return False

    async def get_broadcast_analytics(
        self,
        broadcast_id: str
    ) -> Dict[str, Any]:
        """Get detailed analytics for a broadcast"""
        async with self.db_pool.acquire() as conn:
            # Get broadcast info
            broadcast = await conn.fetchrow("""
                SELECT * FROM broadcasts WHERE id = $1
            """, uuid.UUID(broadcast_id))

            if not broadcast:
                return {"error": "Broadcast not found"}

            # Get analytics
            analytics = await conn.fetchrow("""
                SELECT * FROM communication_analytics
                WHERE broadcast_id = $1
            """, uuid.UUID(broadcast_id))

            # Get channel-specific stats
            channel_stats = await conn.fetch("""
                SELECT
                    'email' as channel,
                    COUNT(*) FILTER (WHERE email_status = 'sent') as sent,
                    COUNT(*) FILTER (WHERE email_status = 'delivered') as delivered,
                    COUNT(*) FILTER (WHERE email_opened_at IS NOT NULL) as opened,
                    COUNT(*) FILTER (WHERE email_clicked_at IS NOT NULL) as clicked,
                    COUNT(*) FILTER (WHERE email_status = 'bounced') as bounced,
                    COUNT(*) FILTER (WHERE email_unsubscribed_at IS NOT NULL) as unsubscribed
                FROM broadcast_recipients
                WHERE broadcast_id = $1
                UNION ALL
                SELECT
                    'sms' as channel,
                    COUNT(*) FILTER (WHERE sms_status = 'sent') as sent,
                    COUNT(*) FILTER (WHERE sms_status = 'delivered') as delivered,
                    0 as opened,
                    0 as clicked,
                    COUNT(*) FILTER (WHERE sms_status = 'failed') as bounced,
                    0 as unsubscribed
                FROM broadcast_recipients
                WHERE broadcast_id = $1
                UNION ALL
                SELECT
                    'push' as channel,
                    COUNT(*) FILTER (WHERE push_status = 'sent') as sent,
                    COUNT(*) FILTER (WHERE push_status = 'delivered') as delivered,
                    COUNT(*) FILTER (WHERE push_opened_at IS NOT NULL) as opened,
                    0 as clicked,
                    COUNT(*) FILTER (WHERE push_status = 'failed') as bounced,
                    0 as unsubscribed
                FROM broadcast_recipients
                WHERE broadcast_id = $1
            """, uuid.UUID(broadcast_id))

            return {
                "broadcast": dict(broadcast),
                "analytics": dict(analytics) if analytics else {},
                "channel_stats": [dict(s) for s in channel_stats],
                "generated_at": datetime.now().isoformat()
            }

    async def _add_recipients(
        self,
        conn,
        broadcast_id: str,
        recipient_ids: List[str],
        channels: List[str]
    ):
        """Add recipients to broadcast"""
        # Get recipient details from customers table/view
        recipients = await conn.fetch("""
            SELECT id, email, phone_number, name
            FROM customers
            WHERE id = ANY($1::text[])
        """, recipient_ids)

        # Get push tokens if push channel is enabled
        push_tokens = {}
        if "push" in channels:
            tokens = await conn.fetch("""
                SELECT customer_id, device_token
                FROM push_subscriptions
                WHERE customer_id = ANY($1::text[]) AND is_active = true
            """, recipient_ids)
            push_tokens = {str(t["customer_id"]): t["device_token"] for t in tokens}

        # Insert recipient records
        for recipient in recipients:
            channels_config = {
                "email": "email" in channels and recipient.get("email"),
                "sms": "sms" in channels and recipient.get("phone_number"),
                "push": "push" in channels and str(recipient["id"]) in push_tokens
            }

            await conn.execute("""
                INSERT INTO broadcast_recipients (
                    broadcast_id, customer_id, email, phone_number,
                    push_token, channels
                ) VALUES ($1, $2, $3, $4, $5, $6)
            """, uuid.UUID(broadcast_id), str(recipient["id"]),
                recipient.get("email"), recipient.get("phone_number"),
                push_tokens.get(str(recipient["id"])),
                json.dumps(channels_config))

    async def _get_broadcast_recipients(
        self,
        conn,
        broadcast_id: str
    ) -> List[Dict[str, Any]]:
        """Get all recipients for a broadcast"""
        recipients = await conn.fetch("""
            SELECT r.*, c.name, c.metadata
            FROM broadcast_recipients r
            LEFT JOIN customers c ON r.customer_id = c.id::text
            WHERE r.broadcast_id = $1
        """, uuid.UUID(broadcast_id))

        return [dict(r) for r in recipients]

    async def _schedule_broadcast(
        self,
        broadcast_id: str,
        scheduled_at: datetime
    ):
        """Schedule a broadcast for future sending"""
        if self.redis_client:
            # Use Redis for scheduling
            delay = (scheduled_at - datetime.now()).total_seconds()
            if delay > 0:
                await self.redis_client.zadd(
                    "scheduled_broadcasts",
                    {broadcast_id: scheduled_at.timestamp()}
                )
        else:
            # Use asyncio for simple scheduling
            delay = (scheduled_at - datetime.now()).total_seconds()
            if delay > 0:
                asyncio.create_task(self._delayed_execute(broadcast_id, delay))

    async def _delayed_execute(self, broadcast_id: str, delay: float):
        """Execute broadcast after delay"""
        await asyncio.sleep(delay)
        await self.execute_broadcast(broadcast_id)

    async def _update_analytics(
        self,
        conn,
        broadcast_id: str,
        results: Dict[str, Any]
    ):
        """Update analytics for broadcast"""
        # Calculate costs
        email_cost = results.get("channels", {}).get("email", {}).get("sent", 0) * 0.001
        sms_cost = results.get("channels", {}).get("sms", {}).get("sent", 0) * 0.02
        push_cost = results.get("channels", {}).get("push", {}).get("sent", 0) * 0.0001
        total_cost = email_cost + sms_cost + push_cost

        await conn.execute("""
            INSERT INTO communication_analytics (
                broadcast_id, email_sent, sms_sent, push_sent,
                email_cost, sms_cost, push_cost, total_cost
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            ON CONFLICT (broadcast_id) DO UPDATE SET
                email_sent = EXCLUDED.email_sent,
                sms_sent = EXCLUDED.sms_sent,
                push_sent = EXCLUDED.push_sent,
                email_cost = EXCLUDED.email_cost,
                sms_cost = EXCLUDED.sms_cost,
                push_cost = EXCLUDED.push_cost,
                total_cost = EXCLUDED.total_cost,
                calculated_at = NOW()
        """, uuid.UUID(broadcast_id),
            results.get("channels", {}).get("email", {}).get("sent", 0),
            results.get("channels", {}).get("sms", {}).get("sent", 0),
            results.get("channels", {}).get("push", {}).get("sent", 0),
            email_cost, sms_cost, push_cost, total_cost)

    async def _log_audit(
        self,
        conn,
        broadcast_id: str,
        action: str,
        user_id: str,
        details: Dict[str, Any]
    ):
        """Log audit entry for broadcast action"""
        await conn.execute("""
            INSERT INTO broadcast_audit_logs (
                broadcast_id, action, action_category,
                performed_by, details
            ) VALUES ($1, $2, $3, $4, $5)
        """, uuid.UUID(broadcast_id) if broadcast_id else None,
            action, action, uuid.UUID(user_id) if user_id else None,
            json.dumps(details))

    async def start_background_tasks(self):
        """Start background tasks for scheduling and analytics"""
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())
        self._analytics_task = asyncio.create_task(self._analytics_loop())

    async def _scheduler_loop(self):
        """Background task to process scheduled broadcasts"""
        while True:
            try:
                async with self.db_pool.acquire() as conn:
                    # Find broadcasts ready to send
                    ready = await conn.fetch("""
                        SELECT id FROM broadcasts
                        WHERE status = 'scheduled'
                        AND scheduled_at <= NOW()
                    """)

                    for broadcast in ready:
                        asyncio.create_task(
                            self.execute_broadcast(str(broadcast["id"]))
                        )

                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                await asyncio.sleep(60)

    async def _analytics_loop(self):
        """Background task to update analytics"""
        while True:
            try:
                async with self.db_pool.acquire() as conn:
                    # Update delivery stats from webhooks
                    # Calculate engagement rates
                    await conn.execute("""
                        UPDATE communication_analytics ca
                        SET
                            email_open_rate = CASE
                                WHEN ca.email_sent > 0
                                THEN (ca.email_opened::float / ca.email_sent * 100)
                                ELSE 0
                            END,
                            email_click_rate = CASE
                                WHEN ca.email_opened > 0
                                THEN (ca.email_clicked::float / ca.email_opened * 100)
                                ELSE 0
                            END,
                            push_open_rate = CASE
                                WHEN ca.push_sent > 0
                                THEN (ca.push_opened::float / ca.push_sent * 100)
                                ELSE 0
                            END
                        WHERE calculated_at < NOW() - INTERVAL '5 minutes'
                    """)

                await asyncio.sleep(300)  # Update every 5 minutes
            except Exception as e:
                logger.error(f"Analytics error: {e}")
                await asyncio.sleep(300)

    async def cleanup(self):
        """Clean up resources"""
        if self._scheduler_task:
            self._scheduler_task.cancel()
        if self._analytics_task:
            self._analytics_task.cancel()

        for channel in self.channels.values():
            await channel.close()