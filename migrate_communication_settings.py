#!/usr/bin/env python3
"""
Migrate current Twilio and SendGrid settings from environment variables
to the Pot Palace tenant settings in the database.
"""

import asyncio
import asyncpg
import json
import os
from uuid import UUID

async def migrate_settings():
    # Database connection settings
    db_host = 'localhost'
    db_port = 5434
    db_name = 'ai_engine'
    db_user = 'weedgo'
    db_password = 'weedgo123'

    # Pot Palace tenant ID
    tenant_id = UUID('ce2d57bc-b3ba-4801-b229-889a9fe9626d')

    # Current Twilio settings from environment
    twilio_settings = {
        'accountSid': 'AC7fabaac1e3be386ed7aef21834f9805d',
        'authToken': '927eabf31e8a7c214539964bdcd6d7ec',
        'phoneNumber': '+13433420247',
        'verifyServiceSid': ''  # Not set in current env
    }

    # Current SendGrid settings from environment
    sendgrid_settings = {
        'apiKey': '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',
        'fromEmail': 'it@potpalace.cc',
        'fromName': 'WeedGo',
        'replyToEmail': ''
    }

    # Create the communication settings structure
    communication_settings = {
        'sms': {
            'provider': 'twilio',
            'enabled': True,
            'twilio': twilio_settings
        },
        'email': {
            'provider': 'sendgrid',
            'enabled': True,
            'sendgrid': sendgrid_settings
        }
    }

    # Connect to database
    conn = await asyncpg.connect(
        host=db_host,
        port=db_port,
        database=db_name,
        user=db_user,
        password=db_password
    )

    try:
        # Get current tenant settings
        current_settings = await conn.fetchval("""
            SELECT settings FROM tenants WHERE id = $1
        """, tenant_id)

        if current_settings is None:
            print(f"Tenant {tenant_id} not found!")
            return

        # Merge communication settings
        if not current_settings:
            current_settings = {}
        elif isinstance(current_settings, str):
            # If it's a JSON string, parse it
            try:
                current_settings = json.loads(current_settings)
            except:
                current_settings = {}

        current_settings['communication'] = communication_settings

        # Update tenant settings (store as JSONB)
        await conn.execute("""
            UPDATE tenants
            SET settings = $1::jsonb, updated_at = CURRENT_TIMESTAMP
            WHERE id = $2
        """, json.dumps(current_settings), tenant_id)

        print(f"Successfully updated communication settings for Pot Palace tenant")
        print(f"Twilio Account SID: {twilio_settings['accountSid'][:10]}...")
        print(f"Twilio Phone: {twilio_settings['phoneNumber']}")
        print(f"SendGrid From Email: {sendgrid_settings['fromEmail']}")

        # Verify the update
        updated_settings = await conn.fetchval("""
            SELECT settings FROM tenants WHERE id = $1
        """, tenant_id)

        if updated_settings and 'communication' in updated_settings:
            print("\nVerification: Communication settings successfully stored in database")
            print(f"SMS Provider: {updated_settings['communication']['sms']['provider']}")
            print(f"Email Provider: {updated_settings['communication']['email']['provider']}")
        else:
            print("\nWarning: Settings might not have been saved correctly")

    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(migrate_settings())