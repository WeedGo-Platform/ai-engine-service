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
    <div className="mt-1 px-2 text-xs text-white flex items-center gap-2 justify-start">
      <span>{formatTime(timestamp)}</span>
      
      {responseTime && (
        <>
          <span>•</span>
          <span>{formatResponseTime(responseTime)}</span>
        </>
      )}
      
      {tokens && (
        <>
          <span>•</span>
          <span>{tokens} tokens</span>
        </>
      )}
      
      {agent && (
        <>
          <span>•</span>
          <span>Agent: {agent}</span>
        </>
      )}
      
      {personality && (
        <>
          <span>•</span>
          <span>Personality: {personality}</span>
        </>
      )}
      
      {toolsUsed && toolsUsed.length > 0 && (
        <>
          <span>•</span>
          <span>Tools: {toolsUsed.join(', ')}</span>
        </>
      )}
    </div>
  );
};

export default ChatMetadata;