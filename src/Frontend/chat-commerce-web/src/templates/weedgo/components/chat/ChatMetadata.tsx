import React from 'react';
import type { ChatMetadataProps } from '../../../../core/contracts/template.contracts';
import { formatTime, formatResponseTime } from '../../../../utils/formatters';

const ChatMetadata: React.FC<ChatMetadataProps> = ({
  timestamp,
  responseTime,
  tokens,
  agent,
  personality,
  toolsUsed
}) => {
  return (
    <div className="mt-2 px-1 text-xs text-gray-500 flex items-center gap-3 justify-start">
      <span className="font-light">{formatTime(timestamp)}</span>
      
      {responseTime && (
        <>
          <span className="text-gray-300">|</span>
          <span className="font-light">{formatResponseTime(responseTime)}</span>
        </>
      )}
      
      {tokens && (
        <>
          <span className="text-gray-300">|</span>
          <span className="font-light">{tokens} tokens</span>
        </>
      )}
      
      {agent && (
        <>
          <span className="text-gray-300">|</span>
          <span className="font-light">Agent: {agent}</span>
        </>
      )}
      
      {personality && (
        <>
          <span className="text-gray-300">|</span>
          <span className="font-light">Mode: {personality}</span>
        </>
      )}
      
      {toolsUsed && toolsUsed.length > 0 && (
        <>
          <span className="text-gray-300">|</span>
          <span className="font-light">Tools: {toolsUsed.join(', ')}</span>
        </>
      )}
    </div>
  );
};

export default ChatMetadata;