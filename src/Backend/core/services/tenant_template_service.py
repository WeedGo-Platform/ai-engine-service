"""
Tenant Template Service
Manages the relationship between tenants and their templates
Follows Single Responsibility Principle for template management
"""

import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4
import json
import asyncpg

logger = logging.getLogger(__name__)


@dataclass
class TemplateConfiguration:
    """Value object for template configuration"""
    template_id: str
    template_name: str
    is_default: bool
    configuration: Dict[str, Any] = field(default_factory=dict)
    custom_css: Optional[str] = None
    custom_logo_url: Optional[str] = None
    theme_colors: Dict[str, str] = field(default_factory=dict)
    active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "template_id": self.template_id,
            "template_name": self.template_name,
            "is_default": self.is_default,
            "configuration": self.configuration,
            "custom_css": self.custom_css,
            "custom_logo_url": self.custom_logo_url,
            "theme_colors": self.theme_colors,
            "active": self.active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


@dataclass
class TenantTemplateMapping:
    """Entity for tenant-template relationship"""
    id: UUID
    tenant_id: UUID
    template_config: TemplateConfiguration
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id),
            **self.template_config.to_dict()
        }


class TenantTemplateRepository:
    """Repository for tenant-template mappings"""
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
    
    async def create_mapping(
        self,
        tenant_id: UUID,
        template_config: TemplateConfiguration
    ) -> TenantTemplateMapping:
        """Create a new tenant-template mapping"""
        try:
            async with self.db_pool.acquire() as conn:
                # If this is set as default, unset other defaults for this tenant
                if template_config.is_default:
                    await conn.execute("""
                        UPDATE tenant_templates 
                        SET is_default = false 
                        WHERE tenant_id = $1 AND is_default = true
                    """, tenant_id)
                
                # Insert new mapping
                row = await conn.fetchrow("""
                    INSERT INTO tenant_templates (
                        tenant_id, template_id, template_name, is_default,
                        configuration, custom_css, custom_logo_url, theme_colors, active
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    RETURNING *
                """, tenant_id, template_config.template_id, template_config.template_name,
                    template_config.is_default, json.dumps(template_config.configuration),
                    template_config.custom_css, template_config.custom_logo_url,
                    json.dumps(template_config.theme_colors), template_config.active)
                
                return self._row_to_mapping(row)
                
        except asyncpg.UniqueViolationError:
            raise ValueError(f"Template {template_config.template_id} already exists for tenant")
        except Exception as e:
            logger.error(f"Error creating tenant-template mapping: {e}")
            raise
    
    async def get_mapping(
        self,
        tenant_id: UUID,
        template_id: str
    ) -> Optional[TenantTemplateMapping]:
        """Get a specific tenant-template mapping"""
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT * FROM tenant_templates 
                    WHERE tenant_id = $1 AND template_id = $2
                """, tenant_id, template_id)
                
                if row:
                    return self._row_to_mapping(row)
                return None
                
        except Exception as e:
            logger.error(f"Error getting tenant-template mapping: {e}")
            raise
    
    async def get_default_mapping(
        self,
        tenant_id: UUID
    ) -> Optional[TenantTemplateMapping]:
        """Get the default template for a tenant"""
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT * FROM tenant_templates 
                    WHERE tenant_id = $1 AND is_default = true
                """, tenant_id)
                
                if row:
                    return self._row_to_mapping(row)
                return None
                
        except Exception as e:
            logger.error(f"Error getting default template: {e}")
            raise
    
    async def list_mappings(
        self,
        tenant_id: UUID,
        active_only: bool = True
    ) -> List[TenantTemplateMapping]:
        """List all templates for a tenant"""
        try:
            async with self.db_pool.acquire() as conn:
                query = """
                    SELECT * FROM tenant_templates 
                    WHERE tenant_id = $1
                """
                if active_only:
                    query += " AND active = true"
                query += " ORDER BY is_default DESC, template_name"
                
                rows = await conn.fetch(query, tenant_id)
                return [self._row_to_mapping(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Error listing tenant templates: {e}")
            raise
    
    async def update_mapping(
        self,
        tenant_id: UUID,
        template_id: str,
        updates: Dict[str, Any]
    ) -> Optional[TenantTemplateMapping]:
        """Update a tenant-template mapping"""
        try:
            async with self.db_pool.acquire() as conn:
                # Build update query dynamically
                set_clauses = []
                values = []
                param_count = 1
                
                allowed_fields = [
                    'template_name', 'is_default', 'configuration',
                    'custom_css', 'custom_logo_url', 'theme_colors', 'active'
                ]
                
                for field in allowed_fields:
                    if field in updates:
                        set_clauses.append(f"{field} = ${param_count}")
                        if field in ['configuration', 'theme_colors']:
                            values.append(json.dumps(updates[field]))
                        else:
                            values.append(updates[field])
                        param_count += 1
                
                if not set_clauses:
                    return None
                
                # Add updated_at
                set_clauses.append(f"updated_at = ${param_count}")
                values.append(datetime.utcnow())
                param_count += 1
                
                # Add WHERE clause parameters
                values.extend([tenant_id, template_id])
                
                # Handle default flag
                if updates.get('is_default'):
                    await conn.execute("""
                        UPDATE tenant_templates 
                        SET is_default = false 
                        WHERE tenant_id = $1 AND is_default = true AND template_id != $2
                    """, tenant_id, template_id)
                
                # Execute update
                query = f"""
                    UPDATE tenant_templates 
                    SET {', '.join(set_clauses)}
                    WHERE tenant_id = ${param_count} AND template_id = ${param_count + 1}
                    RETURNING *
                """
                
                row = await conn.fetchrow(query, *values)
                
                if row:
                    return self._row_to_mapping(row)
                return None
                
        except Exception as e:
            logger.error(f"Error updating tenant-template mapping: {e}")
            raise
    
    async def delete_mapping(
        self,
        tenant_id: UUID,
        template_id: str
    ) -> bool:
        """Delete a tenant-template mapping"""
        try:
            async with self.db_pool.acquire() as conn:
                # Check if it's the default template
                is_default = await conn.fetchval("""
                    SELECT is_default FROM tenant_templates 
                    WHERE tenant_id = $1 AND template_id = $2
                """, tenant_id, template_id)
                
                if is_default:
                    raise ValueError("Cannot delete default template. Set another template as default first.")
                
                result = await conn.execute("""
                    DELETE FROM tenant_templates 
                    WHERE tenant_id = $1 AND template_id = $2
                """, tenant_id, template_id)
                
                return result.split()[1] == "1"
                
        except Exception as e:
            logger.error(f"Error deleting tenant-template mapping: {e}")
            raise
    
    def _row_to_mapping(self, row: asyncpg.Record) -> TenantTemplateMapping:
        """Convert database row to TenantTemplateMapping"""
        config = TemplateConfiguration(
            template_id=row['template_id'],
            template_name=row['template_name'],
            is_default=row['is_default'],
            configuration=json.loads(row['configuration']) if row['configuration'] else {},
            custom_css=row['custom_css'],
            custom_logo_url=row['custom_logo_url'],
            theme_colors=json.loads(row['theme_colors']) if row['theme_colors'] else {},
            active=row['active'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )
        
        return TenantTemplateMapping(
            id=row['id'],
            tenant_id=row['tenant_id'],
            template_config=config
        )


class TenantTemplateService:
    """Service for managing tenant-template relationships"""
    
    def __init__(self, repository: TenantTemplateRepository):
        self.repository = repository
    
    async def assign_template(
        self,
        tenant_id: UUID,
        template_id: str,
        template_name: Optional[str] = None,
        configuration: Optional[Dict[str, Any]] = None,
        set_as_default: bool = False
    ) -> TenantTemplateMapping:
        """Assign a template to a tenant"""
        # Default template name if not provided
        if not template_name:
            template_name = template_id.replace("-", " ").title()
        
        # Create template configuration
        template_config = TemplateConfiguration(
            template_id=template_id,
            template_name=template_name,
            is_default=set_as_default,
            configuration=configuration or {},
            active=True
        )
        
        # Check if mapping already exists
        existing = await self.repository.get_mapping(tenant_id, template_id)
        if existing:
            # Update existing mapping
            updates = {
                "configuration": configuration or {},
                "is_default": set_as_default,
                "active": True
            }
            return await self.repository.update_mapping(tenant_id, template_id, updates)
        
        # Create new mapping
        return await self.repository.create_mapping(tenant_id, template_config)
    
    async def configure_template(
        self,
        tenant_id: UUID,
        template_id: str,
        configuration: Dict[str, Any],
        custom_css: Optional[str] = None,
        custom_logo_url: Optional[str] = None,
        theme_colors: Optional[Dict[str, str]] = None
    ) -> Optional[TenantTemplateMapping]:
        """Configure a template for a tenant"""
        updates = {
            "configuration": configuration
        }
        
        if custom_css is not None:
            updates["custom_css"] = custom_css
        if custom_logo_url is not None:
            updates["custom_logo_url"] = custom_logo_url
        if theme_colors is not None:
            updates["theme_colors"] = theme_colors
        
        return await self.repository.update_mapping(tenant_id, template_id, updates)
    
    async def set_default_template(
        self,
        tenant_id: UUID,
        template_id: str
    ) -> Optional[TenantTemplateMapping]:
        """Set a template as the default for a tenant"""
        # Check if template exists
        mapping = await self.repository.get_mapping(tenant_id, template_id)
        if not mapping:
            raise ValueError(f"Template {template_id} not found for tenant")
        
        # Update to set as default
        return await self.repository.update_mapping(
            tenant_id, 
            template_id,
            {"is_default": True}
        )
    
    async def get_tenant_templates(
        self,
        tenant_id: UUID,
        active_only: bool = True
    ) -> List[TenantTemplateMapping]:
        """Get all templates for a tenant"""
        return await self.repository.list_mappings(tenant_id, active_only)
    
    async def get_default_template(
        self,
        tenant_id: UUID
    ) -> Optional[TenantTemplateMapping]:
        """Get the default template for a tenant"""
        return await self.repository.get_default_mapping(tenant_id)
    
    async def deactivate_template(
        self,
        tenant_id: UUID,
        template_id: str
    ) -> Optional[TenantTemplateMapping]:
        """Deactivate a template for a tenant"""
        # Check if it's the default template
        mapping = await self.repository.get_mapping(tenant_id, template_id)
        if mapping and mapping.template_config.is_default:
            raise ValueError("Cannot deactivate default template")
        
        return await self.repository.update_mapping(
            tenant_id,
            template_id,
            {"active": False}
        )
    
    async def remove_template(
        self,
        tenant_id: UUID,
        template_id: str
    ) -> bool:
        """Remove a template from a tenant"""
        return await self.repository.delete_mapping(tenant_id, template_id)
    
    async def clone_template_config(
        self,
        source_tenant_id: UUID,
        source_template_id: str,
        target_tenant_id: UUID,
        target_template_id: Optional[str] = None
    ) -> TenantTemplateMapping:
        """Clone template configuration from one tenant to another"""
        # Get source configuration
        source = await self.repository.get_mapping(source_tenant_id, source_template_id)
        if not source:
            raise ValueError("Source template not found")
        
        # Use same template ID if not specified
        if not target_template_id:
            target_template_id = source_template_id
        
        # Create new configuration for target tenant
        target_config = TemplateConfiguration(
            template_id=target_template_id,
            template_name=source.template_config.template_name,
            is_default=False,  # Don't automatically set as default
            configuration=source.template_config.configuration.copy(),
            custom_css=source.template_config.custom_css,
            custom_logo_url=source.template_config.custom_logo_url,
            theme_colors=source.template_config.theme_colors.copy(),
            active=True
        )
        
        return await self.repository.create_mapping(target_tenant_id, target_config)
    
    async def get_available_templates(self) -> List[Dict[str, str]]:
        """Get list of available template IDs and names"""
        # This could be enhanced to read from a configuration file or database
        return [
            {"id": "modern-minimal", "name": "Modern Minimal"},
            {"id": "pot-palace", "name": "Pot Palace"},
            {"id": "dark-tech", "name": "Dark Tech"},
            {"id": "rasta-vibes", "name": "Rasta Vibes"},
            {"id": "weedgo", "name": "WeedGo Professional"},
            {"id": "vintage", "name": "Vintage Classic"},
            {"id": "dirty", "name": "Dirty Grunge"},
            {"id": "metal", "name": "Metal Industrial"}
        ]