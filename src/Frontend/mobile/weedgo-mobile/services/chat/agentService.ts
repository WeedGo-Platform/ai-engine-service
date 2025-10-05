/**
 * Agent Service
 * Handles fetching agents and personalities from the API
 */

import { API_URL } from '../../config/api';

export interface Agent {
  id: string;
  name: string;
  has_prompts: boolean;
  has_config: boolean;
  path: string;
  type?: string; // Optional, not always provided by backend
}

export interface Personality {
  id: string;
  name: string;
  filename: string;
  path: string;
}

class AgentService {
  /**
   * Get all available agents
   */
  async getAgents(): Promise<Agent[]> {
    try {
      const response = await fetch(`${API_URL}/api/admin/agents`);
      if (!response.ok) {
        throw new Error(`Failed to fetch agents: ${response.status}`);
      }
      const data = await response.json();
      return data.agents || data || [];
    } catch (error) {
      console.error('[AgentService] Failed to fetch agents:', error);
      throw error;
    }
  }

  /**
   * Get a specific agent by type
   */
  async getAgentByType(type: string): Promise<Agent | null> {
    try {
      const agents = await this.getAgents();
      return agents.find(agent => agent.type === type) || null;
    } catch (error) {
      console.error(`[AgentService] Failed to get agent by type ${type}:`, error);
      return null;
    }
  }

  /**
   * Get personalities for a specific agent
   */
  async getPersonalities(agentId: string): Promise<Personality[]> {
    try {
      const response = await fetch(`${API_URL}/api/admin/agents/${agentId}/personalities`);
      if (!response.ok) {
        throw new Error(`Failed to fetch personalities: ${response.status}`);
      }
      const data = await response.json();
      return data.personalities || data || [];
    } catch (error) {
      console.error(`[AgentService] Failed to fetch personalities for agent ${agentId}:`, error);
      throw error;
    }
  }

  /**
   * Get the dispensary agent and its first personality
   */
  async getDispensaryAgentPersonality(): Promise<{ agent: Agent; personality: Personality } | null> {
    try {
      console.log('[AgentService] Fetching dispensary agent...');

      // 1. Get all agents
      const agents = await this.getAgents();
      console.log('[AgentService] Available agents:', agents.map(a => ({ id: a.id, name: a.name, type: a.type })));

      // 2. Find the dispensary agent
      const dispensaryAgent = agents.find(agent =>
        agent.id === 'dispensary' ||
        agent.name?.toLowerCase() === 'dispensary'
      );

      if (!dispensaryAgent) {
        console.error('[AgentService] No dispensary agent found');
        return null;
      }

      console.log('[AgentService] Found dispensary agent:', dispensaryAgent);

      // 3. Get personalities for this agent
      const personalities = await this.getPersonalities(dispensaryAgent.id);
      console.log('[AgentService] Available personalities:', personalities.map(p => ({ id: p.id, name: p.name })));

      if (personalities.length === 0) {
        console.error('[AgentService] No personalities found for dispensary agent');
        return null;
      }

      // 4. ALWAYS use Marcel personality for dispensary agent
      let selectedPersonality = personalities.find(p =>
        p.id === 'marcel' ||
        p.name?.toLowerCase() === 'marcel'
      );

      // If Marcel not found (shouldn't happen), log error but use first as fallback
      if (!selectedPersonality) {
        console.error('[AgentService] Marcel personality not found! Using fallback:', personalities[0]);
        selectedPersonality = personalities[0];
      }

      console.log('[AgentService] Selected personality:', selectedPersonality);

      return {
        agent: dispensaryAgent,
        personality: selectedPersonality
      };
    } catch (error) {
      console.error('[AgentService] Failed to get dispensary agent personality:', error);
      return null;
    }
  }

  /**
   * Update the personality for a specific agent
   * @param agentId The agent ID (e.g., 'dispensary')
   * @param personalityId The new personality ID to set
   */
  async updateAgentPersonality(agentId: string, personalityId: string): Promise<boolean> {
    try {
      // personality_id is a query parameter, not in the body
      const response = await fetch(`${API_URL}/api/admin/agents/${agentId}/personality?personality_id=${personalityId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to update personality: ${response.status}`);
      }

      const data = await response.json();
      console.log('[AgentService] Successfully updated personality:', data);
      return true;
    } catch (error) {
      console.error(`[AgentService] Failed to update personality for agent ${agentId}:`, error);
      return false;
    }
  }
}

// Export singleton instance
const agentService = new AgentService();
export default agentService;