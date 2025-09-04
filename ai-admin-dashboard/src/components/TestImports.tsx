import React, { useEffect, useState } from 'react';

// Test imports
import { wsService } from '../services/websocket';
import type { DeploymentProgress } from '../services/websocket.types';
import { modelDeploymentService } from '../services/modelDeploymentService';

const TestImports: React.FC = () => {
  const [status, setStatus] = useState<string>('Testing imports...');
  const [errors, setErrors] = useState<string[]>([]);
  const [successes, setSuccesses] = useState<string[]>([]);

  useEffect(() => {
    const testImports = async () => {
      const errorList: string[] = [];
      const successList: string[] = [];

      try {
        // Test 1: WebSocket service exists
        if (wsService) {
          successList.push('✅ wsService imported successfully');
        } else {
          errorList.push('❌ wsService is undefined');
        }
      } catch (e) {
        errorList.push(`❌ wsService import error: ${e}`);
      }

      try {
        // Test 2: modelDeploymentService exists
        if (modelDeploymentService) {
          successList.push('✅ modelDeploymentService imported successfully');
        } else {
          errorList.push('❌ modelDeploymentService is undefined');
        }
      } catch (e) {
        errorList.push(`❌ modelDeploymentService import error: ${e}`);
      }

      try {
        // Test 3: Can call methods
        const testHealth = await modelDeploymentService.getModelHealth('test-model');
        successList.push(`✅ getModelHealth works: ${JSON.stringify(testHealth)}`);
      } catch (e) {
        errorList.push(`❌ getModelHealth error: ${e}`);
      }

      setErrors(errorList);
      setSuccesses(successList);
      setStatus(errorList.length > 0 ? 'Errors found!' : 'All imports working!');
    };

    testImports();
  }, []);

  return (
    <div className="p-8 bg-white rounded-lg shadow-lg">
      <h2 className="text-2xl font-bold mb-4">Import Test Page</h2>
      
      <div className="mb-4">
        <p className="text-lg font-semibold">Status: {status}</p>
      </div>

      {successes.length > 0 && (
        <div className="mb-4">
          <h3 className="text-lg font-semibold text-green-600 mb-2">Successes:</h3>
          <ul className="list-disc list-inside">
            {successes.map((success, i) => (
              <li key={i} className="text-green-600">{success}</li>
            ))}
          </ul>
        </div>
      )}

      {errors.length > 0 && (
        <div className="mb-4">
          <h3 className="text-lg font-semibold text-red-600 mb-2">Errors:</h3>
          <ul className="list-disc list-inside">
            {errors.map((error, i) => (
              <li key={i} className="text-red-600">{error}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="mt-4 p-4 bg-gray-100 rounded">
        <p className="text-sm text-gray-600">
          This page tests if the imports are working correctly in the browser.
          Check the console for additional details.
        </p>
      </div>
    </div>
  );
};

export default TestImports;