import React from "react";
import "./ComponentOpenAIKeys.css";
import { KeyIcon } from "./icons";

interface ApiService {
	get: (url: string, options?: any) => Promise<any>;
	post: (url: string, data: any) => Promise<any>;
}

interface ThemeService {
	getCurrentTheme: () => string;
	addThemeChangeListener: (callback: (theme: string) => void) => void;
	removeThemeChangeListener: (callback: (theme: string) => void) => void;
}

interface ComponentOpenAIKeysProps {
	services?: {
		api?: ApiService;
		theme?: ThemeService;
	};
}

interface ComponentOpenAIKeysState {
	apiKey: string;
	isLoading: boolean;
	error: string | null;
	success: string | null;
	currentTheme: string;
	isKeyVisible: boolean;
	isRemoving: boolean;
	showRemoveConfirm: boolean;
	hasApiKey: boolean;
	keyValid: boolean;
	maskedKey: string | null;
	lastUpdated: string | null;
	settingId: string | null;
	currentUserId: string | null;
}

/**
 * ComponentOpenAIKeys - A component that allows users to configure their OpenAI API key
 * for accessing OpenAI models like GPT-4, GPT-4o, etc.
 *

 */
class ComponentOpenAIKeys extends React.Component<
	ComponentOpenAIKeysProps,
	ComponentOpenAIKeysState
> {
	private themeChangeListener: ((theme: string) => void) | null = null;

	constructor(props: ComponentOpenAIKeysProps) {
		super(props);

		this.state = {
			apiKey: "",
			isLoading: true,
			error: null,
			success: null,
			currentTheme: "light",
			isKeyVisible: false,
			isRemoving: false,
			showRemoveConfirm: false,
			hasApiKey: false,
			keyValid: false,
			maskedKey: null,
			lastUpdated: null,
			settingId: null,
			currentUserId: null,
		};
	}

	componentDidMount() {
		this.initializeThemeService();
		this.getCurrentUserId();
	}

	componentWillUnmount() {
		if (this.themeChangeListener && this.props.services?.theme) {
			this.props.services.theme.removeThemeChangeListener(
				this.themeChangeListener
			);
		}
	}

	/**
	 * Initialize the theme service
	 */
	initializeThemeService() {
		if (this.props.services?.theme) {
			try {
				const theme = this.props.services.theme.getCurrentTheme();
				this.setState({ currentTheme: theme });

				// Subscribe to theme changes
				this.themeChangeListener = (newTheme: string) => {
					this.setState({ currentTheme: newTheme });
				};

				this.props.services.theme.addThemeChangeListener(
					this.themeChangeListener
				);
			} catch (error) {
				console.error("Error initializing theme service:", error);
				this.setState({ error: "Failed to initialize theme service" });
			}
		}
	}

	/**
	 * Get the current user ID from the API
	 */
	async getCurrentUserId() {
		try {
			if (this.props.services?.api) {
				const response = await this.props.services.api.get("/api/v1/auth/me");
				if (response && response.id) {
					this.setState({ currentUserId: response.id }, () => {
						// Load key status after getting user ID
						this.loadKeyStatus();
					});
				} else {
					this.setState({
						error: "Failed to get current user ID",
						isLoading: false,
					});
				}
			} else {
				this.setState({
					error: "API service not available",
					isLoading: false,
				});
			}
		} catch (error) {
			console.error("Error getting current user ID:", error);
			this.setState({
				error: "Failed to get current user ID",
				isLoading: false,
			});
		}
	}

	/**
	 * Load OpenAI API key status from the existing settings endpoint
	 * The backend now masks sensitive data before sending to frontend
	 */
	async loadKeyStatus() {
		if (!this.props.services?.api || !this.state.currentUserId) {
			this.setState({
				error: "API service or user ID not available",
				isLoading: false,
			});
			return;
		}

		try {
			const response = await this.props.services.api.get(
				"/api/v1/settings/instances",
				{
					params: {
						definition_id: "openai_api_keys_settings",
						scope: "user",
						user_id: this.state.currentUserId,
					},
				}
			);

			let instance = null;

			if (Array.isArray(response) && response.length > 0) {
				instance = response[0];
			} else if (response?.data) {
				const data = Array.isArray(response.data)
					? response.data[0]
					: response.data;
				instance = data;
			} else if (response) {
				instance = response;
			}

			if (instance) {
				// Parse the value if it's a string
				const value =
					typeof instance.value === "string"
						? JSON.parse(instance.value)
						: instance.value;

				// Extract information from the masked data
				const apiKey = value?.api_key || "";
				const hasApiKey = value?._has_key || false;
				const keyValid = value?._key_valid || false;

				this.setState({
					hasApiKey,
					keyValid,
					maskedKey: apiKey || null,
					lastUpdated: instance.updated_at || null,
					settingId: instance.id,
					isLoading: false,
				});
			} else {
				this.setState({ isLoading: false });
			}
		} catch (error) {
			console.error("Error loading OpenAI API key status:", error);
			this.setState({
				error: this.getErrorMessage(error),
				isLoading: false,
			});
		}
	}

	/**
	 * Validate OpenAI API key format
	 */
	validateApiKey(apiKey: string): { isValid: boolean; error?: string } {
		if (!apiKey.trim()) {
			return { isValid: false, error: "API key cannot be empty" };
		}

		// Check if it starts with sk-
		if (!apiKey.startsWith("sk-")) {
			return { isValid: false, error: "API key must start with 'sk-'" };
		}

		// Check minimum length (sk- + at least 20 characters)
		if (apiKey.length < 23) {
			return { isValid: false, error: "API key appears to be too short" };
		}

		// Check for common patterns
		if (
			apiKey.includes(" ") ||
			apiKey.includes("\n") ||
			apiKey.includes("\t")
		) {
			return { isValid: false, error: "API key contains invalid characters" };
		}

		return { isValid: true };
	}

	/**
	 * Save OpenAI API key using the existing settings endpoint
	 * The backend will handle encryption and storage
	 */
	async saveSettings(apiKey: string) {
		if (!this.props.services?.api || !this.state.currentUserId) {
			this.setState({ error: "API service or user ID not available" });
			return;
		}

		// Validate API key
		const validation = this.validateApiKey(apiKey);
		if (!validation.isValid) {
			this.setState({ error: validation.error || "Invalid API key" });
			return;
		}

		try {
			this.setState({ isLoading: true, error: null, success: null });

			const settingValue = {
				api_key: apiKey,
			};

			const settingData: any = {
				definition_id: "openai_api_keys_settings",
				name: "OpenAI API Keys",
				value: JSON.stringify(settingValue),
				scope: "user",
				user_id: this.state.currentUserId,
			};

			if (this.state.settingId) {
				// Update existing setting - include the ID in the payload
				settingData.id = this.state.settingId;
			}

			// Use the existing settings endpoint
			const response = await this.props.services.api.post(
				"/api/v1/settings/instances",
				settingData
			);

			if (response?.id) {
				this.setState({ settingId: response.id });
			}

			this.setState({
				success: "OpenAI API key saved successfully!",
				isLoading: false,
				apiKey: "", // Clear the input field for security
			});

			// Refresh the status to get updated masked key
			await this.loadKeyStatus();

			// Clear success message after 3 seconds
			setTimeout(() => {
				this.setState({ success: null });
			}, 3000);
		} catch (error) {
			console.error("Error saving OpenAI API key settings:", error);
			this.setState({
				error: this.getErrorMessage(error),
				isLoading: false,
			});
		}
	}

	/**
	 * Remove OpenAI API key using the existing settings endpoint
	 */
	async removeApiKey() {
		if (!this.props.services?.api || !this.state.currentUserId) {
			this.setState({ error: "API service or user ID not available" });
			return;
		}

		try {
			this.setState({ isRemoving: true, error: null, success: null });

			const settingValue = {
				api_key: "",
			};

			const settingData: any = {
				definition_id: "openai_api_keys_settings",
				name: "OpenAI API Keys",
				value: JSON.stringify(settingValue),
				scope: "user",
				user_id: this.state.currentUserId,
			};

			if (this.state.settingId) {
				// Update existing setting - include the ID in the payload
				settingData.id = this.state.settingId;
			}

			// Use the existing settings endpoint
			const response = await this.props.services.api.post(
				"/api/v1/settings/instances",
				settingData
			);

			if (response?.id) {
				this.setState({ settingId: response.id });
			}

			this.setState({
				success: "OpenAI API key removed successfully!",
				isRemoving: false,
				showRemoveConfirm: false,
				hasApiKey: false,
				keyValid: false,
				maskedKey: null,
				lastUpdated: null,
			});

			// Clear success message after 3 seconds
			setTimeout(() => {
				this.setState({ success: null });
			}, 3000);
		} catch (error) {
			console.error("Error removing OpenAI API key settings:", error);
			this.setState({
				error: this.getErrorMessage(error),
				isRemoving: false,
			});
		}
	}

	/**
	 * Handle API key input change
	 */
	handleApiKeyChange = (e: React.ChangeEvent<HTMLInputElement>) => {
		this.setState({ apiKey: e.target.value, error: null });
	};

	/**
	 * Handle save button click
	 */
	handleSave = () => {
		this.saveSettings(this.state.apiKey);
	};

	/**
	 * Handle remove button click
	 */
	handleRemove = () => {
		this.setState({ showRemoveConfirm: true });
	};

	/**
	 * Handle remove confirmation
	 */
	handleRemoveConfirm = () => {
		this.removeApiKey();
	};

	/**
	 * Handle remove cancellation
	 */
	handleRemoveCancel = () => {
		this.setState({ showRemoveConfirm: false });
	};

	/**
	 * Toggle API key visibility (only for input field, not stored key)
	 */
	toggleKeyVisibility = () => {
		this.setState((prevState) => ({ isKeyVisible: !prevState.isKeyVisible }));
	};

	/**
	 * Get error message from error object
	 */
	getErrorMessage(error: any): string {
		if (error?.response?.data?.detail) {
			return error.response.data.detail;
		} else if (error?.message) {
			return error.message;
		} else if (typeof error === "string") {
			return error;
		} else {
			return "An unknown error occurred";
		}
	}

	render() {
		const {
			apiKey,
			isLoading,
			error,
			success,
			currentTheme,
			isKeyVisible,
			isRemoving,
			showRemoveConfirm,
			hasApiKey,
			keyValid,
			maskedKey,
			lastUpdated,
		} = this.state;
		const isDarkTheme = currentTheme === "dark";

		return (
			<div
				className={`openai-keys-container ${isDarkTheme ? "dark" : "light"}`}
			>
				<div className="openai-keys-header">
					<div className="openai-keys-title">
						<KeyIcon />
						<h3>OpenAI API Keys</h3>
					</div>
					<p className="openai-keys-description">
						Configure your OpenAI API key to access GPT-4, GPT-4o, and other
						OpenAI models in the chat module. Your API key is encrypted and
						stored securely.
					</p>
				</div>

				<div className="openai-keys-content">
					{hasApiKey ? (
						<div className="api-key-section">
							<label className="api-key-label">Current API Key</label>
							<div className="api-key-display">
								<span className="masked-key">{maskedKey || "sk-..."}</span>
								<span className="key-status">
									{keyValid ? "✅ Valid" : "⚠️ Invalid"}
								</span>
							</div>
							{lastUpdated && (
								<p className="api-key-help">
									Last updated: {new Date(lastUpdated).toLocaleString()}
								</p>
							)}
						</div>
					) : (
						<div className="api-key-section">
							<label htmlFor="openai-api-key" className="api-key-label">
								OpenAI API Key
							</label>
							<div className="api-key-input-container">
								<input
									id="openai-api-key"
									type={isKeyVisible ? "text" : "password"}
									value={apiKey}
									onChange={this.handleApiKeyChange}
									placeholder="sk-..."
									className="api-key-input"
									disabled={isLoading}
								/>
								<button
									type="button"
									onClick={this.toggleKeyVisibility}
									className="visibility-toggle"
									disabled={isLoading}
								>
									{isKeyVisible ? "👁️" : "👁️‍🗨️"}
								</button>
							</div>
							<p className="api-key-help">
								Get your API key from{" "}
								<a
									href="https://platform.openai.com/api-keys"
									target="_blank"
									rel="noopener noreferrer"
									className="api-key-link"
								>
									OpenAI Platform (https://platform.openai.com/api-keys)
								</a>
							</p>
						</div>
					)}

					{error && <div className="error-message">{error}</div>}

					{success && <div className="success-message">{success}</div>}

					<div className="openai-keys-actions">
						{hasApiKey ? (
							<>
								<button
									onClick={this.handleSave}
									disabled={isLoading}
									className="save-button"
								>
									{isLoading ? "Saving..." : "Update API Key"}
								</button>
								<button
									onClick={this.handleRemove}
									disabled={isLoading || isRemoving}
									className="remove-button"
								>
									{isRemoving ? "Removing..." : "Remove API Key"}
								</button>
							</>
						) : (
							<button
								onClick={this.handleSave}
								disabled={isLoading}
								className="save-button"
							>
								{isLoading ? "Saving..." : "Save API Key"}
							</button>
						)}
					</div>

					{showRemoveConfirm && (
						<div className="remove-confirmation">
							<div className="confirmation-content">
								<h4>Remove API Key?</h4>
								<p>
									Are you sure you want to remove your OpenAI API key? This
									action cannot be undone.
								</p>
								<div className="confirmation-actions">
									<button
										onClick={this.handleRemoveConfirm}
										disabled={isRemoving}
										className="confirm-button"
									>
										{isRemoving ? "Removing..." : "Yes, Remove"}
									</button>
									<button
										onClick={this.handleRemoveCancel}
										disabled={isRemoving}
										className="cancel-button"
									>
										Cancel
									</button>
								</div>
							</div>
						</div>
					)}

					<div className="openai-keys-info">
						<h4>How it works:</h4>
						<ul>
							<li>Enter your OpenAI API key above</li>
							<li>
								Once saved, you'll be able to access OpenAI models in the chat
								module
							</li>
							<li>
								Your API key is encrypted and stored securely on the server
							</li>
							<li>
								You can use models like GPT-4, GPT-4o, GPT-3.5-turbo, and more
							</li>
							<li>You can remove your API key at any time for security</li>
						</ul>

						<h4>Security Features:</h4>
						<ul>
							<li>✅ API key format validation</li>
							<li>✅ Secure backend storage with encryption</li>
							<li>✅ Keys masked before sending to frontend</li>
							<li>✅ Masked display only</li>
							<li>✅ Easy key removal functionality</li>
							<li>✅ User-scoped access control</li>
						</ul>
					</div>
				</div>
			</div>
		);
	}
}

export default ComponentOpenAIKeys;
