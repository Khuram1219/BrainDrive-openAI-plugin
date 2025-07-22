# BrainDrive OpenAI Plugin

A dedicated plugin for managing OpenAI API keys in BrainDrive.

## Overview

The BrainDrive OpenAI plugin provides a dedicated interface for users to configure and manage their OpenAI API keys. This plugin is separate from the main settings plugin to provide focused functionality for OpenAI integration.

## Features

- **Secure API Key Management**: Securely store and manage your OpenAI API key
- **Theme Support**: Supports both light and dark themes
- **Real-time Validation**: Validates API key format and connection
- **User-Friendly Interface**: Clean, intuitive interface for key management

## Components

### ComponentOpenAIKeys

The main component that provides the OpenAI API key management interface.

**Features:**

- Input field for API key with show/hide toggle
- Secure storage of API keys
- Real-time validation and error handling
- Success/error message display
- Responsive design for mobile and desktop

**Required Services:**

- `api`: For saving and loading API key settings
- `theme`: For theme support (light/dark mode)

## Installation

This plugin is automatically installed for new users through the user initialization system. For existing users, the plugin will be available through the plugin manager.

## Usage

1. Navigate to the plugin in your BrainDrive dashboard
2. Enter your OpenAI API key in the provided field
3. Click "Save API Key" to store your key securely
4. Your API key will be available for use with OpenAI models in the chat module

## API Key Security

- API keys are encrypted and stored securely
- Keys are never displayed in plain text by default
- Use the visibility toggle to view your key when needed

## Development

### Building the Plugin

```bash
cd plugins/BrainDriveOpenAI
npm install
npm run build
```

### Development Mode

```bash
npm start
```

### File Structure

```
BrainDriveOpenAI/
├── src/
│   ├── ComponentOpenAIKeys.tsx    # Main component
│   ├── ComponentOpenAIKeys.css    # Component styles
│   ├── icons.tsx                  # Icon components
│   ├── bootstrap.tsx              # Plugin entry point
│   └── index.css                  # Global styles
├── public/
│   └── index.html                 # HTML template
├── package.json                   # Dependencies and scripts
├── tsconfig.json                  # TypeScript configuration
├── webpack.config.js              # Webpack configuration
└── README.md                      # This file
```

## Integration

This plugin integrates with the BrainDrive AI chat system to provide OpenAI model access. When an API key is configured, users can select OpenAI models in the chat interface.

## Support

For issues or questions about this plugin, please refer to the main BrainDrive documentation or contact the development team.
