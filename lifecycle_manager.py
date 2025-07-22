"""
BrainDrive OpenAI Plugin Lifecycle Manager

Handles installation, uninstallation, and management of the BrainDrive OpenAI plugin.
"""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

# Import BrainDrive models
from backend.app.models.plugin import Plugin, Module
from backend.app.models.settings import SettingsDefinition, SettingsInstance
from backend.app.core.user_initializer.initializers.brain_drive_openai_initializer import (
    PLUGIN_DATA, MODULE_DATA
)

logger = structlog.get_logger()


class BrainDriveOpenAILifecycleManager:
    """Lifecycle manager for BrainDrive OpenAI plugin"""

    def __init__(self):
        self.plugin_slug = "BrainDriveOpenAI"
        self.plugin_name = "BrainDrive OpenAI"
        self.version = "1.0.0"

    async def install_plugin(self, user_id: str, db: AsyncSession) -> Dict[str, Any]:
        """Install BrainDrive OpenAI plugin for specific user"""
        try:
            logger.info(f"Installing {self.plugin_name} plugin for user {user_id}")

            # Check if plugin already exists
            existing_check = await self._check_existing_plugin(user_id, db)
            if existing_check['exists']:
                return {
                    'success': False,
                    'error': f"Plugin already installed for user {user_id}",
                    'plugin_id': existing_check['plugin_id']
                }

            # Create user plugin directory
            user_plugin_dir = await self._create_user_plugin_directory(user_id)
            if not user_plugin_dir:
                return {'success': False, 'error': 'Failed to create user plugin directory'}

            # Copy plugin files
            copy_result = await self._copy_plugin_files(user_id, user_plugin_dir)
            if not copy_result['success']:
                await self._cleanup_user_directory(user_plugin_dir)
                return copy_result

            # Create database records
            db_result = await self._create_database_records(user_id, db)
            if not db_result['success']:
                await self._cleanup_user_directory(user_plugin_dir)
                return db_result

            # Create settings definition and instance
            settings_result = await self._create_settings(user_id, db)
            if not settings_result['success']:
                await self._cleanup_user_directory(user_plugin_dir)
                return settings_result

            # Validate installation
            validation = await self._validate_installation(user_id, user_plugin_dir)
            if not validation['valid']:
                await db.rollback()
                await self._cleanup_user_directory(user_plugin_dir)
                return {'success': False, 'error': validation['error']}

            await db.commit()
            logger.info(f"{self.plugin_name} plugin installed successfully for user {user_id}")

            return {
                'success': True,
                'plugin_id': db_result['plugin_id'],
                'plugin_slug': self.plugin_slug,
                'modules_created': db_result['modules_created'],
                'plugin_directory': str(user_plugin_dir),
                'settings_created': settings_result['settings_created']
            }

        except Exception as e:
            logger.error(f"Installation failed for {self.plugin_name}, user {user_id}: {e}")
            await db.rollback()
            return {'success': False, 'error': str(e)}

    async def uninstall_plugin(self, user_id: str, db: AsyncSession) -> Dict[str, Any]:
        """Uninstall BrainDrive OpenAI plugin for specific user"""
        try:
            logger.info(f"Uninstalling {self.plugin_name} plugin for user {user_id}")

            # Get plugin ID
            plugin_id = f"{user_id}_{self.plugin_slug}"
            
            # Remove modules
            await db.execute(
                select(Module).where(Module.plugin_id == plugin_id)
            )
            modules = await db.execute(
                select(Module).where(Module.plugin_id == plugin_id)
            )
            modules = modules.scalars().all()
            
            for module in modules:
                await db.delete(module)

            # Remove plugin
            plugin = await db.execute(
                select(Plugin).where(Plugin.id == plugin_id)
            )
            plugin = plugin.scalar_one_or_none()
            
            if plugin:
                await db.delete(plugin)

            # Remove settings instance
            settings_instance = await db.execute(
                select(SettingsInstance).where(
                    SettingsInstance.definition_id == "openai_api_keys_settings",
                    SettingsInstance.user_id == user_id
                )
            )
            settings_instance = settings_instance.scalar_one_or_none()
            
            if settings_instance:
                await db.delete(settings_instance)

            # Remove user plugin directory
            user_plugin_dir = Path(f"plugins/{user_id}/{self.plugin_slug}")
            if user_plugin_dir.exists():
                shutil.rmtree(user_plugin_dir)

            await db.commit()
            logger.info(f"{self.plugin_name} plugin uninstalled successfully for user {user_id}")

            return {
                'success': True,
                'plugin_slug': self.plugin_slug,
                'modules_removed': len(modules),
                'settings_removed': 1 if settings_instance else 0
            }

        except Exception as e:
            logger.error(f"Uninstallation failed for {self.plugin_name}, user {user_id}: {e}")
            await db.rollback()
            return {'success': False, 'error': str(e)}

    async def _check_existing_plugin(self, user_id: str, db: AsyncSession) -> Dict[str, Any]:
        """Check if plugin already exists for user"""
        plugin_id = f"{user_id}_{self.plugin_slug}"
        
        plugin = await db.execute(
            select(Plugin).where(Plugin.id == plugin_id)
        )
        plugin = plugin.scalar_one_or_none()
        
        return {
            'exists': plugin is not None,
            'plugin_id': plugin.id if plugin else None
        }

    async def _create_user_plugin_directory(self, user_id: str) -> Path:
        """Create user-specific plugin directory"""
        try:
            user_plugin_dir = Path(f"plugins/{user_id}/{self.plugin_slug}")
            user_plugin_dir.mkdir(parents=True, exist_ok=True)
            return user_plugin_dir
        except Exception as e:
            logger.error(f"Failed to create user plugin directory: {e}")
            return None

    async def _copy_plugin_files(self, user_id: str, user_plugin_dir: Path) -> Dict[str, Any]:
        """Copy plugin files to user directory"""
        try:
            # Copy from the main plugin directory
            source_dir = Path(f"plugins/{self.plugin_slug}")
            
            if not source_dir.exists():
                return {'success': False, 'error': f'Source plugin directory not found: {source_dir}'}

            # Copy dist directory
            dist_source = source_dir / "dist"
            dist_dest = user_plugin_dir / "dist"
            
            if dist_source.exists():
                if dist_dest.exists():
                    shutil.rmtree(dist_dest)
                shutil.copytree(dist_source, dist_dest)

            # Copy package.json
            package_source = source_dir / "package.json"
            package_dest = user_plugin_dir / "package.json"
            
            if package_source.exists():
                shutil.copy2(package_source, package_dest)

            return {'success': True}

        except Exception as e:
            logger.error(f"Failed to copy plugin files: {e}")
            return {'success': False, 'error': str(e)}

    async def _create_database_records(self, user_id: str, db: AsyncSession) -> Dict[str, Any]:
        """Create plugin and module records in database"""
        try:
            plugin_id = f"{user_id}_{self.plugin_slug}"
            
            # Create plugin record
            plugin_data = PLUGIN_DATA.copy()
            plugin_data.update({
                'id': plugin_id,
                'user_id': user_id,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            })
            
            plugin = Plugin(**plugin_data)
            db.add(plugin)

            # Create module record
            module_id = f"{user_id}_componentOpenAIKeys"
            module_data = MODULE_DATA.copy()
            module_data.update({
                'id': module_id,
                'plugin_id': plugin_id,
                'user_id': user_id,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            })
            
            module = Module(**module_data)
            db.add(module)

            return {
                'success': True,
                'plugin_id': plugin_id,
                'modules_created': [module_id]
            }

        except Exception as e:
            logger.error(f"Failed to create database records: {e}")
            return {'success': False, 'error': str(e)}

    async def _create_settings(self, user_id: str, db: AsyncSession) -> Dict[str, Any]:
        """Create settings definition and instance"""
        try:
            # Check if settings definition exists
            definition = await db.execute(
                select(SettingsDefinition).where(
                    SettingsDefinition.id == "openai_api_keys_settings"
                )
            )
            definition = definition.scalar_one_or_none()

            # Create settings definition if it doesn't exist
            if not definition:
                definition_data = {
                    'id': 'openai_api_keys_settings',
                    'name': 'OpenAI API Keys Settings',
                    'description': 'Configure OpenAI API key for accessing GPT-4, GPT-4o, and other OpenAI models',
                    'category': 'AI Settings',
                    'tags': json.dumps(['openai_api_keys_settings', 'OpenAI', 'API Keys', 'AI Models', 'Settings']),
                    'created_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow()
                }
                
                definition = SettingsDefinition(**definition_data)
                db.add(definition)

            # Create settings instance for user
            instance_data = {
                'id': f"openai_settings_{user_id}",
                'name': 'OpenAI API Keys',
                'definition_id': 'openai_api_keys_settings',
                'scope': 'user',
                'user_id': user_id,
                'value': '{}',
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            
            instance = SettingsInstance(**instance_data)
            db.add(instance)

            return {
                'success': True,
                'settings_created': ['openai_api_keys_settings', f"openai_settings_{user_id}"]
            }

        except Exception as e:
            logger.error(f"Failed to create settings: {e}")
            return {'success': False, 'error': str(e)}

    async def _validate_installation(self, user_id: str, user_plugin_dir: Path) -> Dict[str, Any]:
        """Validate plugin installation"""
        try:
            # Check if dist directory exists
            dist_dir = user_plugin_dir / "dist"
            if not dist_dir.exists():
                return {'valid': False, 'error': 'Plugin dist directory not found'}

            # Check if remoteEntry.js exists
            remote_entry = dist_dir / "remoteEntry.js"
            if not remote_entry.exists():
                return {'valid': False, 'error': 'Plugin remoteEntry.js not found'}

            return {'valid': True}

        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return {'valid': False, 'error': str(e)}

    async def _cleanup_user_directory(self, user_plugin_dir: Path):
        """Clean up user plugin directory on failure"""
        try:
            if user_plugin_dir.exists():
                shutil.rmtree(user_plugin_dir)
        except Exception as e:
            logger.error(f"Failed to cleanup user directory: {e}")


# Create global instance
lifecycle_manager = BrainDriveOpenAILifecycleManager() 