/**
 * UX Translation Layer
 * Converts system internals to human-friendly messages
 * Based on Chandragupta Maurya Sprint Document
 */

// Enforcement decision translations
export const translateEnforcement = (decision: string, reason?: string | null): string | null => {
    if (!decision) return null;

    const translations: Record<string, string | null> = {
        'allow': null, // No message needed, just show the response
        'soft_rewrite': 'I rephrased this to keep things safe.',
        'rewrite': 'I adjusted my response to be more helpful.',
        'block': "I can't help with that specific request, but I'm here if you need something else.",
        'flag': 'I noticed something sensitive here and proceeded carefully.',
    };

    return translations[decision.toLowerCase()] || null;
};

// Safety level translations (gentle, never panic)
export const translateSafetyLevel = (level: string): { message: string | null; icon: string } => {
    if (!level) return { message: null, icon: '' };

    const translations: Record<string, { message: string | null; icon: string }> = {
        'safe': { message: null, icon: '✓' },
        'low': { message: null, icon: '' },
        'normal': { message: null, icon: '' },
        'medium': { message: "I'll proceed carefully.", icon: '⚡' },
        'high': { message: 'Let me handle this sensitively.', icon: '💙' },
        'critical': { message: "I want to make sure you're okay. Here's some helpful information.", icon: '💙' },
    };

    return translations[level.toLowerCase()] || { message: null, icon: '' };
};

// Task status translations with visual badges
export const translateTaskStatus = (status: string): { label: string; emoji: string; color: string; hint: string } => {
    if (!status) {
        return { label: 'Pending', emoji: '⏳', color: 'yellow', hint: 'Review and confirm this task' };
    }

    const translations: Record<string, { label: string; emoji: string; color: string; hint: string }> = {
        'pending': { label: 'Pending', emoji: '⏳', color: 'yellow', hint: 'Review and confirm this task' },
        'in_progress': { label: 'In Progress', emoji: '🔄', color: 'blue', hint: 'Working on this now' },
        'running': { label: 'In Progress', emoji: '🔄', color: 'blue', hint: 'Working on this now' },
        'completed': { label: 'Completed', emoji: '✅', color: 'green', hint: 'All done!' },
        'done': { label: 'Completed', emoji: '✅', color: 'green', hint: 'All done!' },
        'failed': { label: 'Needs Attention', emoji: '⚠️', color: 'red', hint: 'Something went wrong. Try again?' },
        'cancelled': { label: 'Cancelled', emoji: '❌', color: 'gray', hint: 'This task was cancelled' },
    };

    return translations[status.toLowerCase()] || { label: status, emoji: '📋', color: 'gray', hint: '' };
};

// Task type translations
export const translateTaskType = (type: string): { label: string; icon: string } => {
    if (!type) return { label: 'Task', icon: '📋' };

    const translations: Record<string, { label: string; icon: string }> = {
        'reminder': { label: 'Reminder', icon: '⏰' },
        'meeting': { label: 'Meeting', icon: '📅' },
        'call': { label: 'Call', icon: '📞' },
        'email': { label: 'Email', icon: '✉️' },
        'note': { label: 'Note', icon: '📝' },
        'alarm': { label: 'Alarm', icon: '🔔' },
        'calendar': { label: 'Calendar Event', icon: '📆' },
        'search': { label: 'Search', icon: '🔍' },
        'weather': { label: 'Weather', icon: '🌤️' },
        'music': { label: 'Music', icon: '🎵' },
        'directions': { label: 'Directions', icon: '🗺️' },
        'general_task': { label: 'Task', icon: '📋' },
        'workflow': { label: 'Workflow', icon: '⚡' },
    };

    return translations[type.toLowerCase()] || { label: 'Task', icon: '📋' };
};

// Decision outcome translations
export const translateDecision = (decision: string): string => {
    if (!decision) return 'Response generated';

    const translations: Record<string, string> = {
        'response_generated': 'Here\'s what I found',
        'task_created': 'Task created',
        'summary_generated': 'Summary ready',
        'voice_response': 'Response ready',
        'fallback_response': 'Here\'s my response',
        'bhiv_core': 'Processing your request',
    };

    return translations[decision.toLowerCase()] || 'Response generated';
};

// Format response for human readability
export const humanizeResponse = (response: string): string => {
    if (!response) return '';

    // Remove any remaining technical artifacts
    let humanized = response
        .replace(/\[.*?Mock\]/gi, '') // Remove mock markers
        .replace(/Context:/gi, '') // Remove context labels
        .replace(/\.\.\./g, '.') // Clean up ellipses
        .trim();

    // Ensure sentence ends properly
    if (humanized && !humanized.match(/[.!?]$/)) {
        humanized += '.';
    }

    return humanized;
};

// Generate friendly confirmation messages for tasks
export const getTaskConfirmation = (taskType: string, description: string): string => {
    const { label, icon } = translateTaskType(taskType);

    const confirmations: Record<string, string> = {
        'reminder': `${icon} I've set a reminder for you: "${description}"`,
        'meeting': `${icon} I've scheduled this meeting: "${description}"`,
        'call': `${icon} I've noted this call: "${description}"`,
        'email': `${icon} I'll help you draft this email: "${description}"`,
        'note': `${icon} I've created a note: "${description}"`,
        'alarm': `${icon} Alarm set: "${description}"`,
        'calendar': `${icon} Added to your calendar: "${description}"`,
        'general_task': `${icon} Task created: "${description}"`,
    };

    return confirmations[taskType.toLowerCase()] || `${icon} I've created a ${label.toLowerCase()} for you: "${description}"`;
};
