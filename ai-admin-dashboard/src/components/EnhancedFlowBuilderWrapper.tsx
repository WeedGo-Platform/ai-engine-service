import { ReactFlowProvider } from 'reactflow';
import EnhancedFlowBuilder from './EnhancedFlowBuilder';

export default function EnhancedFlowBuilderWrapper() {
  return (
    <div className="h-full">
      <div className="bg-white shadow-sm border-b px-6 py-4">
        <h2 className="text-2xl font-bold text-gray-900">Enhanced Conversation Flow Builder</h2>
        <p className="text-gray-600 mt-1">Design complex conversation flows with AI-powered nodes and advanced configuration</p>
      </div>
      <div className="h-[calc(100vh-200px)]">
        <ReactFlowProvider>
          <EnhancedFlowBuilder />
        </ReactFlowProvider>
      </div>
    </div>
  );
}