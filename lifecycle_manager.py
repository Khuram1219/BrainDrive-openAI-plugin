#!/usr/bin/env python3
"""
BrainDrive OpenAI Plugin Lifecycle Manager (New Architecture)

This script handles install/update/delete operations for the BrainDrive OpenAI plugin
using the new multi-user plugin lifecycle management architecture.
"""

import json
import logging
import datetime
import os
import shutil
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import structlog

logger = structlog.get_logger()

# Import the new base lifecycle manager
try:
    from app.plugins.base_lifecycle_manager import BaseLifecycleManager
    logger.info("Using new architecture: BaseLifecycleManager imported from app.plugins")
except ImportError:
    try:
        import sys
        current_dir = os.path.dirname(os.path.abspath(__file__))
        backend_path = os.path.join(current_dir, "..", "..", "backend", "app", "plugins")
        backend_path = os.path.abspath(backend_path)
        if os.path.exists(backend_path):
            if backend_path not in sys.path:
                sys.path.insert(0, backend_path)
            from base_lifecycle_manager import BaseLifecycleManager
            logger.info(f"Using new architecture: BaseLifecycleManager imported from local backend: {backend_path}")
        else:
            logger.warning(f"BaseLifecycleManager not found at {backend_path}, using minimal implementation")
            from abc import ABC, abstractmethod
            from datetime import datetime
            from pathlib import Path
            from typing import Set
            class BaseLifecycleManager(ABC):
                def __init__(self, plugin_slug: str, version: str, shared_storage_path: Path):
                    self.plugin_slug = plugin_slug
                    self.version = version
                    self.shared_path = shared_storage_path
                    self.active_users: Set[str] = set()
                    self.instance_id = f"{plugin_slug}_{version}"
                    self.created_at = datetime.now()
                    self.last_used = datetime.now()
                async def install_for_user(self, user_id: str, db, shared_plugin_path: Path):
                    if user_id in self.active_users:
                        return {'success': False, 'error': 'Plugin already installed for user'}
                    result = await self._perform_user_installation(user_id, db, shared_plugin_path)
                    if result['success']:
                        self.active_users.add(user_id)
                        self.last_used = datetime.now()
                    return result
                async def uninstall_for_user(self, user_id: str, db):
                    if user_id not in self.active_users:
                        return {'success': False, 'error': 'Plugin not installed for user'}
                    result = await self._perform_user_uninstallation(user_id, db)
                    if result['success']:
                        self.active_users.discard(user_id)
                        self.last_used = datetime.now()
                    return result
                @abstractmethod
                async def get_plugin_metadata(self): pass
                @abstractmethod
                async def get_module_metadata(self): pass
                @abstractmethod
                async def _perform_user_installation(self, user_id, db, shared_plugin_path): pass
                @abstractmethod
                async def _perform_user_uninstallation(self, user_id, db): pass
            logger.info("Using minimal BaseLifecycleManager implementation for remote installation")
    except ImportError as e:
        logger.error(f"Failed to import BaseLifecycleManager: {e}")
        raise ImportError("BrainDrive OpenAI plugin requires the new architecture BaseLifecycleManager")

class BrainDriveOpenAILifecycleManager(BaseLifecycleManager):
    """Lifecycle manager for BrainDrive OpenAI plugin using new architecture"""

    def __init__(self, plugins_base_dir: str = None):
        self.plugin_data = {
            "name": "BrainDrive OpenAI Plugin",
            "description": "Manage OpenAI API keys and enable GPT-4, GPT-4o, and other OpenAI model access in BrainDrive.",
            "version": "1.0.0",
            "type": "frontend",
            "icon": "Key",
            "category": "AI",
            "official": False,
            "author": "Your Name or Organization",
            "compatibility": "1.0.0",
            "scope": "BrainDriveOpenAI",
            "bundle_method": "webpack",
            "bundle_location": "dist/remoteEntry.js",
            "is_local": False,
            "long_description": "Provides user-level OpenAI API key management and integration with BrainDrive's AI features.",
            "plugin_slug": "BrainDriveOpenAI",
            "source_type": "github",
            "source_url": "https://github.com/YourUsername/BrainDriveOpenAI",
            "update_check_url": "https://api.github.com/repos/YourUsername/BrainDriveOpenAI/releases/latest",
            "last_update_check": None,
            "update_available": False,
            "latest_version": None,
            "installation_type": "remote",
            "permissions": ["storage.read", "storage.write", "api.access"]
        }
        self.module_data = [
            {
                "name": "ComponentOpenAIKeys",
                "display_name": "OpenAI API Keys",
                "description": "Component for managing OpenAI API keys for GPT-4, GPT-4o, etc.",
                "icon": "Key",
                "category": "AI",
                "priority": 1,
                "props": {
                    "title": "OpenAI API Keys",
                    "description": "Manage your OpenAI API keys for BrainDrive integration.",
                },
                "config_fields": {
                    "openai_api_key": {
                        "type": "text",
                        "description": "Your OpenAI API key",
                        "default": ""
                    }
                },
                "messages": {},
                "required_services": {
                    "settings": {"methods": ["getSetting", "setSetting"], "version": "1.0.0"},
                    "api": {"methods": ["get", "post"], "version": "1.0.0"}
                },
                "dependencies": [],
                "layout": {
                    "minWidth": 4,
                    "minHeight": 2,
                    "defaultWidth": 6,
                    "defaultHeight": 4
                },
                "tags": ["openai", "api-key", "gpt", "ai", "settings", "brain-drive"]
            }
        ]
        logger.info(f"BrainDriveOpenAI: plugins_base_dir - {plugins_base_dir}")
        if plugins_base_dir:
            shared_path = Path(plugins_base_dir) / "shared" / self.plugin_data['plugin_slug'] / f"v{self.plugin_data['version']}"
        else:
            shared_path = Path(__file__).parent.parent.parent / "backend" / "plugins" / "shared" / self.plugin_data['plugin_slug'] / f"v{self.plugin_data['version']}"
        logger.info(f"BrainDriveOpenAI: shared_path - {shared_path}")
        super().__init__(
            plugin_slug=self.plugin_data['plugin_slug'],
            version=self.plugin_data['version'],
            shared_storage_path=shared_path
        )

    @property
    def PLUGIN_DATA(self):
        return self.plugin_data

    async def get_plugin_metadata(self) -> Dict[str, Any]:
        return self.plugin_data

    async def get_module_metadata(self) -> list:
        return self.module_data

    # --- Database logic is unchanged from the template ---
    async def _perform_user_installation(self, user_id: str, db: AsyncSession, shared_plugin_path: Path) -> Dict[str, Any]:
        try:
            db_result = await self._create_database_records(user_id, db)
            if not db_result['success']:
                return db_result
            logger.info(f"BrainDriveOpenAI: User installation completed for {user_id}")
            return {
                'success': True,
                'plugin_id': db_result['plugin_id'],
                'plugin_slug': self.plugin_data['plugin_slug'],
                'plugin_name': self.plugin_data['name'],
                'modules_created': db_result['modules_created']
            }
        except Exception as e:
            logger.error(f"BrainDriveOpenAI: User installation failed for {user_id}: {e}")
            return {'success': False, 'error': str(e)}

    async def _perform_user_uninstallation(self, user_id: str, db: AsyncSession) -> Dict[str, Any]:
        try:
            existing_check = await self._check_existing_plugin(user_id, db)
            if not existing_check['exists']:
                return {'success': False, 'error': 'Plugin not found for user'}
            plugin_id = existing_check['plugin_id']
            delete_result = await self._delete_database_records(user_id, plugin_id, db)
            if not delete_result['success']:
                return delete_result
            logger.info(f"BrainDriveOpenAI: User uninstallation completed for {user_id}")
            return {
                'success': True,
                'plugin_id': plugin_id,
                'deleted_modules': delete_result['deleted_modules']
            }
        except Exception as e:
            logger.error(f"BrainDriveOpenAI: User uninstallation failed for {user_id}: {e}")
            return {'success': False, 'error': str(e)}

    # --- All other methods (_create_database_records, _delete_database_records, etc.) remain as in the template ---

# Standalone functions for compatibility with remote installer
async def install_plugin(user_id: str, db: AsyncSession, plugins_base_dir: str = None) -> Dict[str, Any]:
    manager = BrainDriveOpenAILifecycleManager(plugins_base_dir)
    return await manager.install_plugin(user_id, db)

async def delete_plugin(user_id: str, db: AsyncSession, plugins_base_dir: str = None) -> Dict[str, Any]:
    manager = BrainDriveOpenAILifecycleManager(plugins_base_dir)
    return await manager.delete_plugin(user_id, db)

async def get_plugin_status(user_id: str, db: AsyncSession, plugins_base_dir: str = None) -> Dict[str, Any]:
    manager = BrainDriveOpenAILifecycleManager(plugins_base_dir)
    return await manager.get_plugin_status(user_id, db)

async def update_plugin(user_id: str, db: AsyncSession, new_version_manager: 'BrainDriveOpenAILifecycleManager', plugins_base_dir: str = None) -> Dict[str, Any]:
    old_manager = BrainDriveOpenAILifecycleManager(plugins_base_dir)
    return await old_manager.update_plugin(user_id, db, new_version_manager)