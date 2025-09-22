import React, { useState, useEffect, useRef } from 'react';
import { Check, Copy, X } from 'lucide-react';
import Editor from '@monaco-editor/react';

interface JsonEditorProps {
  initialValue: any;
  onSave?: (value: any) => void;
  onCancel?: () => void;
  readOnly?: boolean;
  title?: string;
}

const JsonEditor: React.FC<JsonEditorProps> = ({
  initialValue,
  onSave,
  onCancel,
  readOnly = false,
  title = 'JSON Editor'
}) => {
  const [jsonString, setJsonString] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isDirty, setIsDirty] = useState(false);
  const [copied, setCopied] = useState(false);
  const editorRef = useRef<any>(null);

  useEffect(() => {
    setJsonString(JSON.stringify(initialValue, null, 2));
  }, [initialValue]);

  const handleEditorChange = (value: string | undefined) => {
    if (value === undefined) return;

    setJsonString(value);
    setIsDirty(true);

    // Validate JSON
    try {
      JSON.parse(value);
      setError(null);
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleSave = () => {
    try {
      const parsed = JSON.parse(jsonString);
      if (onSave) {
        onSave(parsed);
        setIsDirty(false);
      }
    } catch (err: any) {
      setError('Cannot save invalid JSON: ' + err.message);
    }
  };

  const handleFormat = () => {
    if (editorRef.current) {
      editorRef.current.getAction('editor.action.formatDocument')?.run();
    }
  };

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(jsonString);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const handleReset = () => {
    setJsonString(JSON.stringify(initialValue, null, 2));
    setError(null);
    setIsDirty(false);
  };

  const handleEditorMount = (editor: any) => {
    editorRef.current = editor;
  };

  const isDarkMode = document.documentElement.classList.contains('dark');

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg max-w-6xl w-full h-[70vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-2 border-b border-gray-200 dark:border-gray-700 flex-shrink-0">
          <h3 className="text-md font-semibold text-gray-900 dark:text-white">{title}</h3>
          <div className="flex items-center gap-2">
            {!readOnly && isDirty && (
              <span className="text-sm text-orange-600 dark:text-orange-400">• Unsaved changes</span>
            )}
            {error && (
              <span className="text-sm text-red-600 dark:text-red-400">Invalid JSON</span>
            )}
            <button
              onClick={handleCopy}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
              title="Copy JSON"
            >
              {copied ? (
                <Check className="h-4 w-4 text-green-600 dark:text-green-400" />
              ) : (
                <Copy className="h-4 w-4 text-gray-500 dark:text-gray-400" />
              )}
            </button>
            {onCancel && (
              <button
                onClick={onCancel}
                className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
              >
                <X className="h-5 w-5 text-gray-500 dark:text-gray-400" />
              </button>
            )}
          </div>
        </div>

        {/* Monaco Editor */}
        <div className="flex-1 overflow-hidden" style={{ minHeight: '400px' }}>
          <Editor
            height="100%"
            defaultLanguage="json"
            value={jsonString}
            onChange={handleEditorChange}
            onMount={handleEditorMount}
            theme={isDarkMode ? 'vs-dark' : 'light'}
            options={{
              readOnly: readOnly,
              minimap: { enabled: false },
              fontSize: 14,
              wordWrap: 'on',
              formatOnPaste: true,
              formatOnType: true,
              automaticLayout: true,
              scrollBeyondLastLine: false,
              folding: true,
              lineNumbers: 'on',
              renderLineHighlight: 'all',
              bracketPairColorization: {
                enabled: true
              },
              guides: {
                bracketPairs: true,
                indentation: true
              },
              suggest: {
                showMethods: true,
                showFunctions: true,
                showConstructors: true,
                showFields: true,
                showVariables: true,
                showClasses: true,
                showStructs: true,
                showInterfaces: true,
                showModules: true,
                showProperties: true,
                showEvents: true,
                showOperators: true,
                showUnits: true,
                showValues: true,
                showConstants: true,
                showEnums: true,
                showEnumMembers: true,
                showKeywords: true,
                showWords: true,
                showColors: true,
                showFiles: true,
                showReferences: true,
                showFolders: true,
                showTypeParameters: true,
                showSnippets: true
              }
            }}
          />
        </div>

        {/* Footer with actions */}
        <div className="flex items-center justify-between px-4 py-2 border-t border-gray-200 dark:border-gray-700 flex-shrink-0">
          <div className="flex items-center gap-2">
            {!readOnly && (
              <>
                <button
                  onClick={handleFormat}
                  className="px-3 py-1.5 text-sm bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                >
                  Format
                </button>
                <button
                  onClick={handleReset}
                  disabled={!isDirty}
                  className="px-3 py-1.5 text-sm bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded hover:bg-gray-200 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Reset
                </button>
              </>
            )}
          </div>

          <div className="flex items-center gap-2">
            {onCancel && (
              <button
                onClick={onCancel}
                className="px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
              >
                {readOnly ? 'Close' : 'Cancel'}
              </button>
            )}
            {!readOnly && onSave && (
              <button
                onClick={handleSave}
                disabled={!!error || !isDirty}
                className="px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                Save Changes
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default JsonEditor;