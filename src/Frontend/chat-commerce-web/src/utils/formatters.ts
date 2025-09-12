export const formatTime = (date: Date): string => {
  return date.toLocaleTimeString('en-US', { 
    hour: '2-digit', 
    minute: '2-digit', 
    second: '2-digit' 
  });
};

export const formatResponseTime = (seconds: number): string => {
  // Input is already in seconds, just format it
  if (seconds < 0.1) {
    return "< 0.1s";
  }
  return `${seconds.toFixed(1)}s`;
};