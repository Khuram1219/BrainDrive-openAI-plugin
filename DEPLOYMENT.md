# BrainDrive OpenAI Plugin - Deployment Guide

## Overview

The BrainDrive OpenAI Plugin is designed to work seamlessly in both development and production environments. In deployment, users can install this plugin through the Plugin Manager, and it will automatically appear in their Settings page.

## How It Works in Deployment

### 1. **Plugin Discovery**

- The plugin is packaged with all necessary metadata in `package.json`
- The Plugin Manager scans available plugins and displays them to users
- Users can browse and install the plugin through the UI

### 2. **Installation Process**

When a user installs the plugin:

1. **Plugin Files**: Plugin files are copied to the user's plugin directory
2. **Database Records**: Plugin and module records are created in the database
3. **Settings Creation**: Settings definition and instance are automatically created
4. **Validation**: Installation is validated to ensure everything works correctly

### 3. **Settings Page Integration**

After installation:

- The plugin's `ComponentOpenAIKeys` module appears in the Settings page
- Users can configure their OpenAI API keys
- Settings are automatically saved and managed

## Plugin Structure

```
plugins/BrainDriveOpenAI/
├── src/
│   ├── ComponentOpenAIKeys.tsx    # Main component
│   ├── bootstrap.tsx              # Plugin bootstrap
│   └── index.tsx                  # Plugin entry point
├── dist/                          # Built plugin files
│   └── remoteEntry.js             # Webpack bundle
├── package.json                   # Plugin metadata
├── lifecycle_manager.py           # Installation logic
├── api_endpoints.py               # API endpoints
└── webpack.config.js              # Build configuration
```

## Key Files

### `package.json`

Contains plugin metadata that the Plugin Manager uses:

```json
{
	"plugin_metadata": {
		"plugin_slug": "BrainDriveOpenAI",
		"display_name": "BrainDrive OpenAI",
		"description": "OpenAI API Key Management Plugin",
		"modules": [
			{
				"name": "ComponentOpenAIKeys",
				"tags": ["openai_api_keys_settings", "Settings"]
			}
		],
		"settings": {
			"definition_id": "openai_api_keys_settings"
		}
	}
}
```

### `lifecycle_manager.py`

Handles the complete installation/uninstallation process:

- Creates database records
- Copies plugin files
- Creates settings definitions and instances
- Validates installation

### `api_endpoints.py`

Provides REST API endpoints for:

- `/api/plugins/brain-drive-openai/install` - Install plugin
- `/api/plugins/brain-drive-openai/uninstall` - Uninstall plugin
- `/api/plugins/brain-drive-openai/status` - Check installation status

## Deployment Workflow

### 1. **Plugin Packaging**

```bash
# Build the plugin
cd plugins/BrainDriveOpenAI
npm run build

# The dist/ directory contains the built plugin
```

### 2. **Plugin Distribution**

The plugin can be distributed via:

- **GitHub Repository**: Users install via GitHub URL
- **Local File Upload**: Users upload plugin archive
- **Plugin Store**: Centralized plugin repository

### 3. **User Installation**

1. User navigates to Plugin Manager
2. User finds "BrainDrive OpenAI" plugin
3. User clicks "Install"
4. Plugin is automatically installed and configured
5. Plugin appears in Settings page

### 4. **Plugin Usage**

1. User goes to Settings page
2. User sees "OpenAI API Keys" section
3. User enters their OpenAI API key
4. Settings are saved and plugin is ready to use

## Database Schema

The plugin creates these database records:

### Plugin Table

```sql
INSERT INTO plugin (
    id, name, plugin_slug, user_id,
    bundle_location, enabled, status
) VALUES (
    'user_id_BrainDriveOpenAI', 'BrainDrive OpenAI',
    'BrainDriveOpenAI', 'user_id',
    'dist/remoteEntry.js', 1, 'activated'
);
```

### Module Table

```sql
INSERT INTO module (
    id, plugin_id, name, display_name,
    tags, enabled, user_id
) VALUES (
    'user_id_componentOpenAIKeys', 'user_id_BrainDriveOpenAI',
    'ComponentOpenAIKeys', 'OpenAI API Keys',
    '["openai_api_keys_settings", "Settings"]', 1, 'user_id'
);
```

### Settings Tables

```sql
-- Settings Definition
INSERT INTO settings_definitions (
    id, name, description, category, tags
) VALUES (
    'openai_api_keys_settings', 'OpenAI API Keys Settings',
    'Configure OpenAI API key', 'AI Settings',
    '["openai_api_keys_settings", "Settings"]'
);

-- Settings Instance
INSERT INTO settings_instances (
    id, name, definition_id, user_id, value
) VALUES (
    'openai_settings_user_id', 'OpenAI API Keys',
    'openai_api_keys_settings', 'user_id', '{}'
);
```

## Testing Installation

### Manual Testing

```bash
# Test installation via API
curl -X POST "http://localhost:8000/api/plugins/brain-drive-openai/install" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Check status
curl -X GET "http://localhost:8000/api/plugins/brain-drive-openai/status" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Uninstall
curl -X DELETE "http://localhost:8000/api/plugins/brain-drive-openai/uninstall" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Automated Testing

The plugin includes lifecycle manager methods that can be tested:

```python
# Test installation
result = await lifecycle_manager.install_plugin(user_id, db)
assert result['success'] == True

# Test uninstallation
result = await lifecycle_manager.uninstall_plugin(user_id, db)
assert result['success'] == True
```

## Troubleshooting

### Common Issues

1. **Plugin not appearing in Settings page**

   - Check if module has "Settings" tag
   - Verify settings definition and instance exist
   - Ensure plugin files are accessible

2. **Installation fails**

   - Check plugin file permissions
   - Verify database connectivity
   - Review lifecycle manager logs

3. **Component not loading**
   - Check webpack build output
   - Verify remoteEntry.js exists
   - Check browser console for errors

### Debug Commands

```bash
# Check plugin status
python backend/test_settings_page_loading.py

# Check module tags
python backend/check_module_tags.py

# Verify plugin files
ls -la backend/plugins/BrainDriveOpenAI/dist/
```

## Security Considerations

1. **User Isolation**: Each user gets their own plugin instance
2. **API Key Security**: OpenAI API keys are encrypted and user-specific
3. **File Permissions**: Plugin files are restricted to user directories
4. **Database Isolation**: All records are user-scoped

## Future Enhancements

1. **Plugin Updates**: Automatic version updates
2. **Dependencies**: Plugin dependency management
3. **Configuration**: Plugin-specific configuration options
4. **Analytics**: Plugin usage tracking
5. **Backup/Restore**: Plugin data backup functionality
