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
    <div className="mt-2 px-2 text-xs text-cyan-500/70 font-mono flex items-center gap-2 justify-start">
      <span className="text-green-500">[{formatTime(timestamp)}]</span>
      
      {responseTime && (
        <>
          <span className="text-cyan-500/30">::</span>
          <span className="text-yellow-500">{formatResponseTime(responseTime)}</span>
        </>
      )}
      
      {tokens && (
        <>
          <span className="text-cyan-500/30">::</span>
          <span className="text-blue-500">{tokens}t</span>
        </>
      )}
      
      {agent && (
        <>
          <span className="text-cyan-500/30">::</span>
          <span className="text-purple-500">@{agent}</span>
        </>
      )}
      
      {personality && (
        <>
          <span className="text-cyan-500/30">::</span>
          <span className="text-pink-500">#{personality}</span>
        </>
      )}
      
      {toolsUsed && toolsUsed.length > 0 && (
        <>
          <span className="text-cyan-500/30">::</span>
          <span className="text-orange-500">[{toolsUsed.join('|')}]</span>
        </>
      )}
    </div>
  );
};

export default ChatMetadata;