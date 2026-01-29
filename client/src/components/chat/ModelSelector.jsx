import React from 'react';
import './ModelSelector.css';

const ModelSelector = ({ selectedModel, onModelChange, disabled }) => {
    const providers = {
        gemini: {
            name: 'Gemini',
            models: [
                { value: 'gemini-2.5-pro', label: '2.5 Pro' },
                { value: 'gemini-1.5-pro', label: '1.5 Pro' },
                { value: 'gemini-2.5-flash', label: '2.5 Flash' }
            ]
        },
        openai: {
            name: 'OpenAI',
            models: [
                { value: 'gpt-4o', label: 'GPT-4o' },
                { value: 'gpt-4o-mini', label: 'GPT-4o Mini' }
            ]
        }
    };

    // Determine current provider from selected model
    const getCurrentProvider = React.useCallback(() => {
        if (selectedModel.startsWith('gemini')) return 'gemini';
        if (selectedModel.startsWith('gpt')) return 'openai';
        return 'gemini';
    }, [selectedModel]);

    const [provider, setProvider] = React.useState(getCurrentProvider());

    // Update provider when model changes externally
    React.useEffect(() => {
        setProvider(getCurrentProvider());
    }, [selectedModel, getCurrentProvider]);

    const handleProviderChange = (newProvider) => {
        setProvider(newProvider);
        // Auto-select first model of new provider
        const firstModel = providers[newProvider].models[0].value;
        onModelChange(firstModel);
    };

    const handleModelChange = (newModel) => {
        onModelChange(newModel);
    };

    const currentModels = providers[provider].models;

    return (
        <div className="model-selector">
            <div className="selector-group">
                <label htmlFor="provider-select">Provider:</label>
                <select
                    id="provider-select"
                    value={provider}
                    onChange={(e) => handleProviderChange(e.target.value)}
                    disabled={disabled}
                    className="provider-select"
                >
                    {Object.entries(providers).map(([key, prov]) => (
                        <option key={key} value={key}>
                            {prov.name}
                        </option>
                    ))}
                </select>
            </div>

            <div className="selector-group">
                <label htmlFor="model-select">Model:</label>
                <select
                    id="model-select"
                    value={selectedModel}
                    onChange={(e) => handleModelChange(e.target.value)}
                    disabled={disabled}
                    className="model-select"
                >
                    {currentModels.map(model => (
                        <option key={model.value} value={model.value}>
                            {model.label}
                        </option>
                    ))}
                </select>
            </div>
        </div>
    );
};

export default ModelSelector;
