import React from 'react';
import {
  Cpu,
  CheckCircle,
  AlertCircle,
  Loader2
} from 'lucide-react';

interface Model {
  name: string;
  filename: string;
  path: string;
  size_gb: number;
}

interface ModelsTabProps {
  currentModel: string | null;
  models: Model[];
  isLoading: boolean;
  isLoadingModel: string | null;
  modelLoadStatus: string;
  modelError: string;
  loadModel: (modelName: string) => void;
}

const ModelsTab: React.FC<ModelsTabProps> = ({
  currentModel,
  models,
  isLoading,
  isLoadingModel,
  modelLoadStatus,
  modelError,
  loadModel
}) => {
  return (
    <div>
      {/* Current Status */}
      <div className="bg-gray-50 dark:bg-gray-900/50 rounded-lg p-4 sm:p-6 mb-4 sm:mb-6 transition-colors">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">Current Model</h3>
            {currentModel ? (
              <div className="mt-1 flex items-center gap-2">
                <CheckCircle className="h-4 w-4 text-green-500" />
                <span className="text-lg font-semibold text-gray-900 dark:text-white">{currentModel}</span>
              </div>
            ) : (
              <div className="mt-1 flex items-center gap-2">
                <AlertCircle className="h-4 w-4 text-gray-400" />
                <span className="text-lg text-gray-500 dark:text-gray-400">No model loaded</span>
              </div>
            )}
            {modelLoadStatus && (
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{modelLoadStatus}</p>
            )}
            {modelError && (
              <p className="text-sm text-red-600 dark:text-red-400 mt-1">{modelError}</p>
            )}
          </div>
          {/* Unload button commented out - endpoint not implemented
          {currentModel && (
            <button
              onClick={unloadModel}
              disabled={isLoadingModel}
              className="px-4 py-2 text-sm bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 rounded-lg hover:bg-red-200 dark:hover:bg-red-900/50 disabled:opacity-50"
            >
              {isLoadingModel ? 'Processing...' : 'Unload Model'}
            </button>
          )}
          */}
        </div>
      </div>

      {/* Available Models */}
      <div>
        <h2 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-white mb-3 sm:mb-4">Available Models</h2>
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-6 w-6 sm:h-8 sm:w-8 animate-spin text-indigo-600" />
          </div>
        ) : models.length === 0 ? (
          <p className="text-sm sm:text-base text-gray-500 dark:text-gray-400 text-center py-12">No models found</p>
        ) : (
          <div className="grid gap-3 sm:gap-4">
            {models.map((model) => (
              <div
                key={model.name}
                className={`border rounded-lg p-3 sm:p-4 transition-all ${
                  currentModel === model.name
                    ? 'border-indigo-500 dark:border-indigo-400 bg-indigo-50 dark:bg-indigo-900/20'
                    : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                }`}
              >
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <Cpu className="h-4 w-4 sm:h-5 sm:w-5 text-gray-600 dark:text-gray-400 flex-shrink-0" />
                      <h3 className="font-medium text-sm sm:text-base text-gray-900 dark:text-white truncate">{model.name}</h3>
                      {currentModel === model.name && (
                        <span className="px-2 py-0.5 text-xs bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded-full flex-shrink-0">
                          Active
                        </span>
                      )}
                    </div>
                    <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400 mt-1 truncate">
                      {model.filename} • {model.size_gb} GB
                    </p>
                  </div>
                  {currentModel !== model.name && (
                    <button
                      onClick={() => loadModel(model.name)}
                      disabled={isLoadingModel !== null}
                      className="w-full sm:w-auto px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all active:scale-95 touch-manipulation"
                    >
                      {isLoadingModel === model.name ? (
                        <span className="flex items-center justify-center gap-2">
                          <Loader2 className="h-4 w-4 animate-spin" />
                          Loading...
                        </span>
                      ) : (
                        'Load Model'
                      )}
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ModelsTab;