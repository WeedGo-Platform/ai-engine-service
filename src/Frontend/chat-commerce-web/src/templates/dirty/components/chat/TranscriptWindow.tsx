import React from 'react';
import Scrollbar from '../ui/Scrollbar';

interface TranscriptWindowProps {
  transcript: string;
  isListening?: boolean;
  confidence?: number;
}

const TranscriptWindow: React.FC<TranscriptWindowProps> = ({
  transcript,
  isListening = false,
  confidence,
}) => {
  return (
    <div className="w-full">
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <div className="flex items-center justify-between mb-2">
          <h4 className="text-sm font-medium text-gray-700">Voice Transcript</h4>
          {isListening && (
            <div className="flex items-center space-x-1">
              <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
              <span className="text-xs text-red-500">Listening...</span>
            </div>
          )}
        </div>
        <Scrollbar className="h-24" thin>
          <p className="text-sm text-gray-600 whitespace-pre-wrap">
            {transcript || 'No transcript available. Start speaking to see the transcript.'}
          </p>
        </Scrollbar>
        {confidence !== undefined && (
          <div className="mt-2 pt-2 border-t border-gray-200">
            <div className="flex items-center justify-between">
              <span className="text-xs text-gray-500">Confidence</span>
              <span className="text-xs font-medium text-gray-700">{(confidence * 100).toFixed(1)}%</span>
            </div>
            <div className="mt-1 h-1 bg-gray-200 rounded-full overflow-hidden">
              <div 
                className="h-full bg-blue-500 transition-all duration-300"
                style={{ width: `${confidence * 100}%` }}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default TranscriptWindow;