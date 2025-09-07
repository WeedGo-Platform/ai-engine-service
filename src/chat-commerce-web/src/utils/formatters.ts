export const formatTime = (date: Date): string => {
  return date.toLocaleTimeString('en-US', { 
    hour: '2-digit', 
    minute: '2-digit', 
    second: '2-digit' 
  });
};

export const formatResponseTime = (ms: number): string => {
  return `${(ms / 1000).toFixed(1)}s`;
};