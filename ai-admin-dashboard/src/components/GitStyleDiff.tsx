import React from 'react';
import { diffWords, diffLines } from 'diff';

interface GitStyleDiffProps {
  original: string;
  modified: string;
  title?: string;
  mode?: 'words' | 'lines' | 'chars';
}

export default function GitStyleDiff({ 
  original, 
  modified, 
  title = 'Response Comparison',
  mode = 'words' 
}: GitStyleDiffProps) {
  // Calculate the diff based on mode
  const getDiff = () => {
    switch (mode) {
      case 'lines':
        return diffLines(original, modified);
      case 'words':
      default:
        return diffWords(original, modified);
    }
  };

  const differences = getDiff();
  
  // Calculate statistics
  const stats = {
    additions: differences.filter((d: any) => d.added).reduce((acc: number, d: any) => acc + (d.value.split(' ').length), 0),
    deletions: differences.filter((d: any) => d.removed).reduce((acc: number, d: any) => acc + (d.value.split(' ').length), 0),
    unchanged: differences.filter((d: any) => !d.added && !d.removed).reduce((acc: number, d: any) => acc + (d.value.split(' ').length), 0)
  };

  const similarityScore = Math.round((stats.unchanged / (stats.unchanged + stats.additions + stats.deletions)) * 100);

  return (
    <div className="bg-gray-900 rounded-lg overflow-hidden">
      {/* Header */}
      <div className="bg-gray-800 px-4 py-3 border-b border-gray-700">
        <div className="flex items-center justify-between">
          <h3 className="text-white font-mono text-sm">{title}</h3>
          <div className="flex items-center gap-4 text-xs font-mono">
            <span className="text-green-400">+{stats.additions} additions</span>
            <span className="text-red-400">-{stats.deletions} deletions</span>
            <span className="text-blue-400">{similarityScore}% similar</span>
          </div>
        </div>
      </div>

      {/* Diff Content */}
      <div className="p-4 font-mono text-sm overflow-auto max-h-96">
        <div className="space-y-2">
          {/* Original (removed) */}
          <div className="border-l-4 border-red-500 pl-3">
            <div className="text-red-400 text-xs mb-1">- Original Response</div>
            <div className="bg-red-950/30 p-2 rounded">
              {differences.map((part: any, index: number) => (
                <span
                  key={index}
                  className={
                    part.removed 
                      ? 'bg-red-800/50 text-red-200 px-0.5 rounded' 
                      : part.added 
                      ? 'hidden' 
                      : 'text-gray-400'
                  }
                >
                  {part.value}
                </span>
              ))}
            </div>
          </div>

          {/* Modified (added) */}
          <div className="border-l-4 border-green-500 pl-3">
            <div className="text-green-400 text-xs mb-1">+ New Response</div>
            <div className="bg-green-950/30 p-2 rounded">
              {differences.map((part: any, index: number) => (
                <span
                  key={index}
                  className={
                    part.added 
                      ? 'bg-green-800/50 text-green-200 px-0.5 rounded' 
                      : part.removed 
                      ? 'hidden' 
                      : 'text-gray-400'
                  }
                >
                  {part.value}
                </span>
              ))}
            </div>
          </div>

          {/* Inline Diff */}
          <div className="border-l-4 border-blue-500 pl-3 mt-4">
            <div className="text-blue-400 text-xs mb-1">⟷ Inline Diff</div>
            <div className="bg-gray-800 p-2 rounded">
              {differences.map((part: any, index: number) => (
                <span
                  key={index}
                  className={
                    part.added 
                      ? 'bg-green-800/50 text-green-200 px-0.5 rounded' 
                      : part.removed 
                      ? 'bg-red-800/50 text-red-200 px-0.5 rounded line-through' 
                      : 'text-gray-300'
                  }
                >
                  {part.value}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Summary */}
        <div className="mt-6 pt-4 border-t border-gray-700">
          <div className="grid grid-cols-2 gap-4 text-xs">
            <div>
              <span className="text-gray-500">Response Length:</span>
              <div className="text-gray-300 mt-1">
                Original: {original.length} chars → New: {modified.length} chars
                <span className={`ml-2 ${modified.length > original.length ? 'text-green-400' : 'text-red-400'}`}>
                  ({modified.length > original.length ? '+' : ''}{modified.length - original.length})
                </span>
              </div>
            </div>
            <div>
              <span className="text-gray-500">Change Impact:</span>
              <div className="text-gray-300 mt-1">
                {stats.additions + stats.deletions === 0 ? 'No changes' :
                 stats.additions + stats.deletions < 5 ? 'Minor changes' :
                 stats.additions + stats.deletions < 20 ? 'Moderate changes' :
                 'Significant changes'}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}