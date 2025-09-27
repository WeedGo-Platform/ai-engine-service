"""
Push Notification Communication Channel Service
Supporting FCM (Firebase Cloud Messaging) for Android/Web and APNS for iOS
Following SOLID principles for broadcast push notifications
"""

import os
import asyncio
import logging
import json
import jwt
import time
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import aiohttp
from pathlib import Path

from .base_channel import (
    ICommunicationChannel,
    ChannelType,
    ChannelConfig,
    Recipient,
    Message,
    DeliveryResult,
    DeliveryStatus,
    MessageValidator,
    BatchProcessor
)

logger = logging.getLogger(__name__)


class PushNotificationService(ICommunicationChannel):
    """
    Push notification service implementation for broadcast communications
    Supports Firebase Cloud Messaging (FCM) and Apple Push Notification Service (APNS)
    """

    def __init__(self, config: ChannelConfig):
        super().__init__(config)
        self.channel_type = ChannelType.PUSH
        self._session: Optional[aiohttp.ClientSession] = None

        # FCM configuration
        self.fcm_server_key = os.getenv("FCM_SERVER_KEY", config.api_key)
        self.fcm_sender_id = os.getenv("FCM_SENDER_ID", "")
        self.fcm_api_url = "https://fcm.googleapis.com/fcm/send"

        # APNS configuration
        self.apns_key_id = os.getenv("APNS_KEY_ID", "")
        self.apns_team_id = os.getenv("APNS_TEAM_ID", "")
        self.apns_bundle_id = os.getenv("APNS_BUNDLE_ID", "com.weedgo.app")
        self.apns_key_path = os.getenv("APNS_KEY_PATH", "")
        self.apns_api_url = self._get_apns_url()

        # Web Push (VAPID) configuration
        self.vapid_private_key = os.getenv("VAPID_PRIVATE_KEY", "")
        self.vapid_public_key = os.getenv("VAPID_PUBLIC_KEY", "")
        self.vapid_subject = os.getenv("VAPID_SUBJECT", "mailto:admin@weedgo.ai")

        # Cache for APNS token
        self._apns_token = None
        self._apns_token_expiry = None

    def _get_apns_url(self) -> str:
        """Get APNS API URL based on environment"""
        if self.config.sandbox_mode:
            return "https://api.development.push.apple.com"
        return "https://api.push.apple.com"

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if not self._session or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.timeout)
            )
        return self._session

    async def send_single(
        self,
        recipient: Recipient,
        message: Message
    ) -> DeliveryResult:
        """
        Send push notification to a single recipient

        Args:
            recipient: Recipient with push token
            message: Push notification content

        Returns:
            DeliveryResult with delivery status
        """
        # Validate recipient
        is_valid, error = await self.validate_recipient(recipient)
        if not is_valid:
            return DeliveryResult(
                message_id=f"push_{recipient.id}_{datetime.now().timestamp()}",
                recipient_id=recipient.id,
                status=DeliveryStatus.FAILED,
                channel=self.channel_type,
                error_message=error
            )

        # Check preferences
        if not await self.check_preferences(recipient):
            return DeliveryResult(
                message_id=f"push_{recipient.id}_{datetime.now().timestamp()}",
                recipient_id=recipient.id,
                status=DeliveryStatus.UNSUBSCRIBED,
                channel=self.channel_type,
                error_message="Recipient has disabled push notifications"
            )

        # Apply rate limiting
        await self._apply_rate_limiting()

        try:
            # Determine device type from token or metadata
            device_type = await self._determine_device_type(recipient)

            # Send based on device type
            if device_type == "ios":
                result = await self._send_apns(recipient, message)
            elif device_type == "web":
                result = await self._send_web_push(recipient, message)
            else:  # android or default to FCM
                result = await self._send_fcm(recipient, message)

            return DeliveryResult(
                message_id=result.get("message_id", f"push_{recipient.id}_{datetime.now().timestamp()}"),
                recipient_id=recipient.id,
                status=DeliveryStatus.SENT,
                channel=self.channel_type,
                sent_at=datetime.now(),
                cost=self.config.cost_per_message,
                metadata={**result, "device_type": device_type}
            )

        except Exception as e:
            logger.error(f"Failed to send push notification to {recipient.id}: {e}")

            # Retry on failure
            if self.config.retry_attempts > 0:
                return await self._retry_failed_message(recipient, message)

            return DeliveryResult(
                message_id=f"push_{recipient.id}_{datetime.now().timestamp()}",
                recipient_id=recipient.id,
                status=DeliveryStatus.FAILED,
                channel=self.channel_type,
                error_message=str(e)
            )

    async def send_batch(
        self,
        recipients: List[Recipient],
        message: Message
    ) -> List[DeliveryResult]:
        """
        Send push notifications to multiple recipients

        Args:
            recipients: List of recipients
            message: Push notification content

        Returns:
            List of DeliveryResult for each recipient
        """
        # Group recipients by device type for efficient batch sending
        grouped = await self._group_by_device_type(recipients)

        results = []

        # Send FCM batch (Android/Web via FCM)
        if grouped.get("fcm"):
            fcm_results = await self._send_fcm_batch(grouped["fcm"], message)
            results.extend(fcm_results)

        # Send APNS batch (iOS)
        if grouped.get("ios"):
            ios_results = await BatchProcessor.process_in_batches(
                items=grouped["ios"],
                batch_size=100,
                process_func=lambda batch: self._send_apns_batch(batch, message),
                delay_between_batches=0.5
            )
            results.extend(ios_results)

        # Send Web Push batch
        if grouped.get("web"):
            web_results = await BatchProcessor.process_in_batches(
                items=grouped["web"],
                batch_size=50,
                process_func=lambda batch: self._send_web_push_batch(batch, message),
                delay_between_batches=0.5
            )
            results.extend(web_results)

        return results

    async def validate_recipient(self, recipient: Recipient) -> Tuple[bool, Optional[str]]:
        """
        Validate push notification recipient

        Args:
            recipient: Recipient to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not recipient.push_token:
            return False, "Push token is required"

        return MessageValidator.validate_push_token(recipient.push_token)

    async def get_delivery_status(self, message_id: str) -> DeliveryResult:
        """
        Get delivery status for a push notification

        Note: Most push services don't provide real-time delivery status

        Args:
            message_id: Message ID to check

        Returns:
            DeliveryResult with status
        """
        # Push notifications typically don't have queryable delivery status
        # This would need to be implemented via webhook callbacks
        return DeliveryResult(
            message_id=message_id,
            recipient_id="",
            status=DeliveryStatus.SENT,
            channel=self.channel_type,
            metadata={"note": "Delivery status requires webhook implementation"}
        )

    async def _determine_device_type(self, recipient: Recipient) -> str:
        """Determine device type from recipient metadata or token format"""
        if recipient.metadata:
            device_type = recipient.metadata.get("device_type", "").lower()
            if device_type in ["ios", "android", "web"]:
                return device_type

        # Analyze token format
        token = recipient.push_token
        if token.startswith("http"):  # Web push endpoint
            return "web"
        elif len(token) == 64 and all(c in "0123456789abcdef" for c in token.lower()):
            return "ios"  # APNS token format
        else:
            return "android"  # Default to FCM

    async def _group_by_device_type(
        self,
        recipients: List[Recipient]
    ) -> Dict[str, List[Recipient]]:
        """Group recipients by device type"""
        grouped = {"fcm": [], "ios": [], "web": []}

        for recipient in recipients:
            device_type = await self._determine_device_type(recipient)
            if device_type == "ios":
                grouped["ios"].append(recipient)
            elif device_type == "web":
                grouped["web"].append(recipient)
            else:
                grouped["fcm"].append(recipient)

        return grouped

    async def _send_fcm(self, recipient: Recipient, message: Message) -> Dict[str, Any]:
        """Send notification via Firebase Cloud Messaging"""
        session = await self._get_session()

        payload = {
            "to": recipient.push_token,
            "notification": {
                "title": message.push_title or message.subject or "Notification",
                "body": message.content,
                "sound": message.push_sound or "default",
                "badge": message.push_badge_count or 1
            },
            "data": message.metadata or {},
            "priority": "high" if message.priority.value in ["high", "urgent"] else "normal"
        }

        if message.push_image_url:
            payload["notification"]["image"] = message.push_image_url

        if message.push_action_url:
            payload["data"]["action_url"] = message.push_action_url

        headers = {
            "Authorization": f"key={self.fcm_server_key}",
            "Content-Type": "application/json"
        }

        async with session.post(self.fcm_api_url, headers=headers, json=payload) as response:
            response_data = await response.json()

            if response.status == 200 and response_data.get("success") == 1:
                return {
                    "message_id": response_data.get("results", [{}])[0].get("message_id", ""),
                    "status": "sent",
                    "provider": "fcm"
                }
            else:
                error = response_data.get("results", [{}])[0].get("error", "Unknown error")
                raise Exception(f"FCM error: {error}")

    async def _send_fcm_batch(
        self,
        recipients: List[Recipient],
        message: Message
    ) -> List[DeliveryResult]:
        """Send batch notifications via FCM"""
        session = await self._get_session()

        # FCM supports up to 1000 tokens per request
        tokens = [r.push_token for r in recipients]

        payload = {
            "registration_ids": tokens,
            "notification": {
                "title": message.push_title or message.subject or "Notification",
                "body": message.content,
                "sound": message.push_sound or "default",
                "badge": message.push_badge_count or 1
            },
            "data": message.metadata or {},
            "priority": "high" if message.priority.value in ["high", "urgent"] else "normal"
        }

        headers = {
            "Authorization": f"key={self.fcm_server_key}",
            "Content-Type": "application/json"
        }

        async with session.post(self.fcm_api_url, headers=headers, json=payload) as response:
            response_data = await response.json()

            results = []
            for i, recipient in enumerate(recipients):
                result_data = response_data.get("results", [])[i] if i < len(response_data.get("results", [])) else {}

                if result_data.get("message_id"):
                    status = DeliveryStatus.SENT
                    error_message = None
                else:
                    status = DeliveryStatus.FAILED
                    error_message = result_data.get("error", "Unknown error")

                results.append(DeliveryResult(
                    message_id=result_data.get("message_id", f"push_{recipient.id}_{datetime.now().timestamp()}"),
                    recipient_id=recipient.id,
                    status=status,
                    channel=self.channel_type,
                    sent_at=datetime.now() if status == DeliveryStatus.SENT else None,
                    error_message=error_message,
                    cost=self.config.cost_per_message if status == DeliveryStatus.SENT else 0
                ))

            return results

    async def _get_apns_token(self) -> str:
        """Generate JWT token for APNS authentication"""
        if self._apns_token and self._apns_token_expiry and self._apns_token_expiry > time.time():
            return self._apns_token

        # Read the private key
        if not self.apns_key_path or not Path(self.apns_key_path).exists():
            raise Exception("APNS private key not found")

        with open(self.apns_key_path, 'r') as key_file:
            private_key = key_file.read()

        # Create JWT token
        headers = {
            "alg": "ES256",
            "kid": self.apns_key_id
        }

        payload = {
            "iss": self.apns_team_id,
            "iat": int(time.time())
        }

        self._apns_token = jwt.encode(payload, private_key, algorithm="ES256", headers=headers)
        self._apns_token_expiry = time.time() + 3500  # Refresh before 1 hour expiry

        return self._apns_token

    async def _send_apns(self, recipient: Recipient, message: Message) -> Dict[str, Any]:
        """Send notification via Apple Push Notification Service"""
        session = await self._get_session()
        token = await self._get_apns_token()

        headers = {
            "authorization": f"bearer {token}",
            "apns-topic": self.apns_bundle_id,
            "apns-priority": "10" if message.priority.value in ["high", "urgent"] else "5"
        }

        payload = {
            "aps": {
                "alert": {
                    "title": message.push_title or message.subject or "Notification",
                    "body": message.content
                },
                "sound": message.push_sound or "default",
                "badge": message.push_badge_count or 1
            }
        }

        if message.push_image_url:
            payload["aps"]["mutable-content"] = 1
            payload["image_url"] = message.push_image_url

        if message.metadata:
            payload.update(message.metadata)

        url = f"{self.apns_api_url}/3/device/{recipient.push_token}"

        async with session.post(url, headers=headers, json=payload) as response:
            if response.status == 200:
                return {
                    "message_id": response.headers.get("apns-id", ""),
                    "status": "sent",
                    "provider": "apns"
                }
            else:
                error_data = await response.json()
                raise Exception(f"APNS error: {error_data.get('reason', 'Unknown error')}")

    async def _send_apns_batch(
        self,
        recipients: List[Recipient],
        message: Message
    ) -> List[DeliveryResult]:
        """Send batch notifications via APNS"""
        # APNS doesn't support true batch sending, so we send individually
        tasks = []
        for recipient in recipients:
            tasks.append(self.send_single(recipient, message))

        return await asyncio.gather(*tasks)

    async def _send_web_push(self, recipient: Recipient, message: Message) -> Dict[str, Any]:
        """Send web push notification using VAPID"""
        session = await self._get_session()

        # Parse subscription info
        subscription = recipient.metadata or {}
        endpoint = subscription.get("endpoint", recipient.push_token)
        keys = subscription.get("keys", {})
        auth = keys.get("auth", "")
        p256dh = keys.get("p256dh", "")

        if not endpoint:
            raise Exception("Web push endpoint is required")

        # Create VAPID headers
        vapid_headers = self._create_vapid_headers(endpoint)

        payload = json.dumps({
            "title": message.push_title or message.subject or "Notification",
            "body": message.content,
            "icon": message.push_image_url,
            "badge": "/badge-icon.png",
            "data": {
                "url": message.push_action_url,
                **(message.metadata or {})
            }
        })

        headers = {
            **vapid_headers,
            "Content-Type": "application/json",
            "TTL": "86400"  # 24 hours
        }

        async with session.post(endpoint, headers=headers, data=payload) as response:
            if response.status in [200, 201, 204]:
                return {
                    "message_id": f"web_push_{datetime.now().timestamp()}",
                    "status": "sent",
                    "provider": "web_push"
                }
            else:
                raise Exception(f"Web push error: {response.status}")

    async def _send_web_push_batch(
        self,
        recipients: List[Recipient],
        message: Message
    ) -> List[DeliveryResult]:
        """Send batch web push notifications"""
        tasks = []
        for recipient in recipients:
            tasks.append(self.send_single(recipient, message))

        return await asyncio.gather(*tasks)

    def _create_vapid_headers(self, endpoint: str) -> Dict[str, str]:
        """Create VAPID authorization headers for web push"""
        # This is a simplified implementation
        # In production, use py-vapid library
        return {
            "Authorization": f"WebPush {self.vapid_public_key}",
            "Crypto-Key": f"p256ecdsa={self.vapid_public_key}"
        }

    async def register_device(
        self,
        customer_id: str,
        device_token: str,
        device_type: str,
        device_metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Register a device for push notifications

        Args:
            customer_id: Customer ID
            device_token: Push token or subscription info
            device_type: Device type (ios, android, web)
            device_metadata: Additional device info

        Returns:
            Success status
        """
        # This would typically save to the push_subscriptions table
        logger.info(f"Registering device for customer {customer_id}: {device_type}")
        return True

    async def unregister_device(self, device_token: str) -> bool:
        """
        Unregister a device from push notifications

        Args:
            device_token: Device token to unregister

        Returns:
            Success status
        """
        logger.info(f"Unregistering device token: {device_token}")
        return True

    async def handle_webhook(self, webhook_data: Dict[str, Any]) -> None:
        """
        Handle webhook callbacks from push providers

        Args:
            webhook_data: Webhook payload
        """
        try:
            provider = webhook_data.get("provider")

            if provider == "fcm":
                # Handle FCM feedback
                message_id = webhook_data.get("message_id")
                status = webhook_data.get("status")
                logger.info(f"FCM webhook: {message_id} - {status}")

            elif provider == "apns":
                # Handle APNS feedback
                device_token = webhook_data.get("device_token")
                status = webhook_data.get("status")

                if status == "Unregistered":
                    await self.unregister_device(device_token)

        except Exception as e:
            logger.error(f"Failed to process push webhook: {e}")

    async def close(self):
        """Clean up resources"""
        if self._session and not self._session.closed:
            await self._session.close()