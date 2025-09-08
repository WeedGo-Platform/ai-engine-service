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
    <div className="mt-1 px-2 text-xs flex items-center gap-2 justify-start" style={{ color: '#FCD34D' }}>
      <span>{formatTime(timestamp)}</span>
      
      {responseTime && (
        <>
          <span style={{ color: '#16A34A' }}>•</span>
          <span>{formatResponseTime(responseTime)}</span>
        </>
      )}
      
      {tokens && (
        <>
          <span style={{ color: '#DC2626' }}>•</span>
          <span>{tokens} tokens</span>
        </>
      )}
      
      {agent && (
        <>
          <span style={{ color: '#FCD34D' }}>•</span>
          <span>Agent: {agent}</span>
        </>
      )}
      
      {personality && (
        <>
          <span style={{ color: '#16A34A' }}>•</span>
          <span>Vibe: {personality}</span>
        </>
      )}
      
      {toolsUsed && toolsUsed.length > 0 && (
        <>
          <span style={{ color: '#DC2626' }}>•</span>
          <span>Tools: {toolsUsed.join(', ')}</span>
        </>
      )}
    </div>
  );
};

export default ChatMetadata;