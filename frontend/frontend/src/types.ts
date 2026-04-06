export interface AssistantRequest {
  message: string;
  platform?: string;
  device_context?: string;
  voice_input?: boolean;
}

export interface AssistantResponse {
  status: 'success' | 'error';
  data: {
    summary?: {
      summary: string;
    };
    intent?: {
      intent: string;
      confidence?: number;
    };
    task?: {
      task_type: string;
      priority?: string;
      status?: string;
      id?: number;
    };
    decision?: {
      final_decision: string;
      response?: string;
      task_created?: Task;
    };
    processed_at?: string;
    enforcement?: {
      decision: 'allow' | 'rewrite' | 'block';
      reason?: string;
      trace_id?: string;
    };
    safety?: {
      level: 'safe' | 'soft_risk' | 'high_risk' | 'blocked';
      confidence?: number;
      score?: number;
    };
    execution?: {
      status: 'executing' | 'completed' | 'failed' | 'skipped';
      stage?: string;
      error?: string;
    };
  };
  error?: string;
}

export interface Task {
  id: number;
  description: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface ConversationMessage {
  id: string;
  userMessage: string;
  assistantResponse: AssistantResponse | null;
  timestamp: string;
  isLoading?: boolean;
  error?: string;
}

export interface Conversation {
  id: string;
  title: string;
  messages: ConversationMessage[];
  timestamp: string;
}




// Search Types
export interface SearchRequest {
  query: string;
  max_results?: number;
}

export interface SearchResult {
  title: string;
  url: string;
  snippet: string;
  relevance: number;
}

export interface SearchResponse {
  query: string;
  results: SearchResult[];
}

// Research Types
export interface ResearchRequest {
  query: string;
  max_results?: number;
}

export interface ResearchResponse {
  topic: string;
  summary: string;
  key_findings: string[];
  sources: Array<{
    title: string;
    url: string;
    relevance: number;
  }>;
  depth: number;
}


// Task Management Types
export interface TaskRequest {
  name: string;
  description: string;
  agents: string[];
  input_data?: Record<string, any>;
  priority?: 'low' | 'medium' | 'high' | 'critical';
}

export interface TaskStatusResponse {
  task_id: string;
  name: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  result?: any;
}

export interface TaskCreateResponse {
  task_id: string;
  status: string;
}

// System Information Types
export interface SystemInfo {
  platform: string;
  python_version: string;
  working_directory: string;
  available_space: string;
  memory_usage: {
    total: number;
    available: number;
    percent: number;
    used: number;
  };
}

export interface SystemStats {
  memory_stats: {
    total_entries: number;
    users: number;
  };
  task_queue_status: {
    pending: number;
    running: number;
    completed: number;
  };
  safety_stats: {
    total_evaluations: number;
    blocked_count: number;
  };
  policy_violations: {
    total: number;
  };
  performance_metrics: number;
}

// Performance Insights Types
export interface PerformanceMetrics {
  total_interactions: number;
  successful_interactions: number;
  average_response_time: number;
  average_satisfaction: number;
  improvement_areas: string[];
}

export interface PerformancePattern {
  pattern_type: string;
  description: string;
  frequency: number;
}

export interface PerformanceInsights {
  performance_metrics: PerformanceMetrics;
  patterns: PerformancePattern[];
  recommendations: string[];
}

