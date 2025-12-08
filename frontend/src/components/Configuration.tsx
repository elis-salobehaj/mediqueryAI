import React from 'react';

interface ConfigurationProps {
  apiKey: string;
  setApiKey: (key: string) => void;
}

const Configuration: React.FC<ConfigurationProps> = ({ apiKey, setApiKey }) => {
  return (
    <div className="flex-1 flex items-center justify-center p-8 bg-gradient-to-br from-slate-900 to-slate-800">
      <div className="glass-panel p-8 rounded-2xl w-full max-w-md">
        <h2 className="text-2xl font-bold mb-4 bg-clip-text text-transparent bg-gradient-to-r from-cyan-400 to-blue-500">
          Configuration
        </h2>
        <p className="text-slate-400 mb-6">
          To use the AI Agent, please provide your Google Gemini API Key.
        </p>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">
              Gemini API Key
            </label>
            <input
              type="password"
              className="w-full px-4 py-3 rounded-lg bg-slate-800 border border-slate-700 focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400 outline-none transition-all placeholder-slate-600"
              placeholder="AIzaSy..."
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
            />
          </div>
          <button
            className="w-full py-3 rounded-lg bg-gradient-to-r from-cyan-500 to-blue-600 font-semibold text-white shadow-lg hover:shadow-cyan-500/20 hover:scale-[1.02] transition-all"
            onClick={() => alert('Configuration Saved!')}
          >
            Save Configuration
          </button>
        </div>
      </div>
    </div>
  );
};

export default Configuration;
