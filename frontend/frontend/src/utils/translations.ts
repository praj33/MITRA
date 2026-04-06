/**
 * Human-friendly translations for system internals
 * Phase C: Human-Grade Assistant UX
 */

export const translateIntent = (intent: string): string => {
  const intentMap: Record<string, string> = {
    'question': 'Ask a question',
    'task_creation': 'Create a task',
    'schedule': 'Schedule something',
    'reminder': 'Set a reminder',
    'information': 'Get information',
    'general': 'General request',
    'unknown': 'General request',
  };

  if (!intent) return 'Unknown';
  return intentMap[intent.toLowerCase()] || intent.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
};

export const translateTaskType = (taskType: string): string => {
  return taskType.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
};

export const translateEnforcementDecision = (decision: 'allow' | 'rewrite' | 'block', reason?: string): string => {
  if (decision === 'block') {
    return "I can't help with that";
  }
  if (decision === 'rewrite') {
    return "I rephrased this to keep things safe";
  }
  return ''; // 'allow' doesn't need a message
};

export const translateSafetyLevel = (level: 'safe' | 'soft_risk' | 'high_risk' | 'blocked'): string => {
  const levelMap: Record<string, string> = {
    'safe': '',
    'soft_risk': 'Caution',
    'high_risk': 'Warning',
    'blocked': "I can't provide that content",
  };
  return levelMap[level] || '';
};

export const translateActionStatus = (status: string, finalDecision?: string): string => {
  if (status === 'skipped') {
    return "I can't help with that";
  }
  if (status === 'executing') {
    return 'Working on it...';
  }
  if (status === 'failed') {
    return "Couldn't complete that";
  }
  if (status === 'completed') {
    if (finalDecision?.includes('task_created')) {
      return "Task created";
    }
    if (finalDecision?.includes('summary')) {
      return "Here you go";
    }
    return 'All set!';
  }
  return 'Processing...';
};

export const formatFriendlyTimestamp = (dateString: string): string => {
  try {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;

    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return dateString;
  }
};
