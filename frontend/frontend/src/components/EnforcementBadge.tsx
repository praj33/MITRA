import React from 'react';

interface EnforcementBadgeProps {
    decision: 'allow' | 'rewrite' | 'block';
    reason?: string;
    traceId?: string;
}

const EnforcementBadge: React.FC<EnforcementBadgeProps> = ({ decision, reason, traceId }) => {
    const styles = {
        allow: {
            badge: 'bg-green-500/20 text-green-300 border-green-500/40',
            dot: 'bg-green-500',
        },
        rewrite: {
            badge: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/40',
            dot: 'bg-yellow-500',
        },
        block: {
            badge: 'bg-red-500/20 text-red-300 border-red-500/40',
            dot: 'bg-red-500',
        },
    };

    const labels = {
        allow: 'Allowed',
        rewrite: 'Rephrased',
        block: 'Blocked',
    };

    // Convert reason to short 1-2 word tag
    const getReasonTag = (reason?: string): string => {
        if (!reason) return '';
        // Convert snake_case or long text to short tag
        const shortMap: Record<string, string> = {
            'policy_check_passed': 'POLICY OK',
            'prohibited_content': 'PROHIBITED',
            'tone_adjustment': 'TONE',
            'content_filter': 'FILTER',
            'safety_violation': 'SAFETY',
        };
        
        // Check if we have a direct mapping
        const lowerReason = reason.toLowerCase();
        for (const [key, value] of Object.entries(shortMap)) {
            if (lowerReason.includes(key.replace('_', ''))) {
                return value;
            }
        }
        
        // Otherwise, take first two words or first word if it's descriptive
        const words = reason.split(/[_\s]+/);
        if (words.length >= 2) {
            return words.slice(0, 2).map(w => w.toUpperCase().slice(0, 6)).join(' ');
        }
        return words[0].toUpperCase().slice(0, 10);
    };

    const reasonTag = getReasonTag(reason);
    const style = styles[decision];

    return (
        <div className="flex items-center gap-2 flex-wrap">
            {/* Main Decision Badge - Prominent */}
            <div className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md border-2 ${style.badge} uppercase tracking-wider font-bold text-xs`}>
                <span className={`w-2 h-2 rounded-full ${style.dot} animate-pulse`}></span>
                {labels[decision]}
            </div>
            
            {/* Reason Tag - Short 1-2 words */}
            {reasonTag && (
                <span className="px-2 py-1 rounded bg-gray-800/50 border border-gray-700 text-xs font-medium text-gray-400 uppercase tracking-wide">
                    {reasonTag}
                </span>
            )}
            
            {/* Trace ID - Hidden from users */}
        </div>
    );
};

export default EnforcementBadge;
