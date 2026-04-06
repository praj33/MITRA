import React from 'react';

interface SafetyLabelProps {
    level: 'safe' | 'soft_risk' | 'high_risk' | 'blocked';
    score?: number;
    confidence?: number;
}

const SafetyLabel: React.FC<SafetyLabelProps> = ({ level, score, confidence }) => {
    const config = {
        safe: { 
            color: 'bg-green-500', 
            text: 'text-green-300', 
            label: 'Safe' 
        },
        soft_risk: { 
            color: 'bg-yellow-500', 
            text: 'text-yellow-300', 
            label: 'Caution' 
        },
        high_risk: { 
            color: 'bg-orange-500', 
            text: 'text-orange-300', 
            label: 'Warning' 
        },
        blocked: { 
            color: 'bg-red-500', 
            text: 'text-red-300', 
            label: 'Not Available' 
        },
    };

    const { color, text, label } = config[level] || config.safe;

    // Use confidence if provided, otherwise derive from score
    // Note: riskPercentage is hidden from users per UX requirements

    return (
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-md border-2 bg-gray-800/30 border-gray-700">
            <div className="flex items-center gap-2">
                {/* Status Dot */}
                <span className={`w-2.5 h-2.5 rounded-full ${color} ${level !== 'safe' ? 'animate-pulse' : ''}`}></span>
                
                {/* Label */}
                <span className={`text-xs font-bold ${text} tracking-wider uppercase`}>{label}</span>
            </div>
            
            {/* Confidence/Score Indicator - Hidden from users */}
        </div>
    );
};

export default SafetyLabel;
