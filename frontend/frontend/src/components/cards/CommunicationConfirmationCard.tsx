// components/cards/CommunicationConfirmationCard.tsx — Phase B.COMM-2 Communication Approval Card
import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Mail, MessageSquare, Send, X, ShieldAlert, CheckCircle } from 'lucide-react';
import { cn } from '../../lib/utils';

export interface CommunicationConfirmationData {
  type?: string;
  channel: 'EMAIL' | 'WHATSAPP';
  sender_account?: string | null;
  recipient?: string | null;
  subject?: string | null;
  content?: string | null;
  action?: string;
  idempotency_key?: string | null;
  requires_confirmation?: boolean;
}

interface Props {
  confirmation: CommunicationConfirmationData;
  onConfirm: () => void;
  onCancel: () => void;
  className?: string;
}

export const CommunicationConfirmationCard: React.FC<Props> = ({
  confirmation,
  onConfirm,
  onCancel,
  className,
}) => {
  const [isConfirmed, setIsConfirmed] = useState(false);
  const [isCancelled, setIsCancelled] = useState(false);
  const isEmail = confirmation.channel === 'EMAIL';

  const handleSendNow = () => {
    setIsConfirmed(true);
    onConfirm();
  };

  const handleCancel = () => {
    setIsCancelled(true);
    onCancel();
  };

  if (isCancelled) {
    return (
      <div className={cn('p-3 rounded-lg bg-surface-raised border border-border-subtle text-xs text-text-muted', className)}>
        <span>Communication action was cancelled.</span>
      </div>
    );
  }

  if (isConfirmed) {
    return (
      <div className={cn('p-3 rounded-lg bg-surface-raised border border-brand/40 text-xs text-brand-light flex items-center gap-2', className)}>
        <CheckCircle size={14} className="text-brand-light" />
        <span>Action confirmed. Dispatching message...</span>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 4, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.15 }}
      className={cn(
        'card w-full p-3.5 sm:p-4 bg-surface-elevated border border-brand/30 shadow-md rounded-xl',
        className
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between gap-2 pb-2.5 mb-2.5 border-b border-border-subtle">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-md bg-brand-muted border border-brand/30 flex items-center justify-center text-brand-light">
            {isEmail ? <Mail size={13} /> : <MessageSquare size={13} />}
          </div>
          <span className="text-xs font-semibold text-text-primary tracking-wide">
            {isEmail ? 'Send email?' : 'Send WhatsApp message?'}
          </span>
        </div>
        <div className="flex items-center gap-1 px-1.5 py-0.5 rounded bg-brand/10 border border-brand/20 text-brand-light text-2xs font-medium">
          <ShieldAlert size={10} />
          <span>Approval Required</span>
        </div>
      </div>

      {/* Fields */}
      <div className="space-y-2 text-xs">
        {isEmail && confirmation.sender_account && (
          <div className="flex flex-col sm:flex-row sm:items-baseline gap-0.5 sm:gap-2">
            <span className="text-text-muted font-medium w-16 flex-shrink-0">From:</span>
            <span className="text-text-primary font-mono text-2xs truncate">
              {confirmation.sender_account}
            </span>
          </div>
        )}

        <div className="flex flex-col sm:flex-row sm:items-baseline gap-0.5 sm:gap-2">
          <span className="text-text-muted font-medium w-16 flex-shrink-0">To:</span>
          <span className="text-text-primary font-medium truncate">
            {confirmation.recipient || '(No recipient specified)'}
          </span>
        </div>

        {isEmail && confirmation.subject && (
          <div className="flex flex-col sm:flex-row sm:items-baseline gap-0.5 sm:gap-2">
            <span className="text-text-muted font-medium w-16 flex-shrink-0">Subject:</span>
            <span className="text-text-primary font-medium">
              {confirmation.subject}
            </span>
          </div>
        )}

        <div className="flex flex-col sm:flex-row sm:items-baseline gap-0.5 sm:gap-2 pt-1">
          <span className="text-text-muted font-medium w-16 flex-shrink-0">Message:</span>
          <div className="flex-1 p-2 rounded-md bg-surface-base border border-border-subtle text-text-primary italic whitespace-pre-wrap max-h-32 overflow-y-auto">
            "{confirmation.content || ''}"
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex items-center justify-end gap-2 mt-3.5 pt-2.5 border-t border-border-subtle">
        <button
          type="button"
          onClick={handleCancel}
          className="px-3 py-1.5 rounded-lg text-xs font-medium text-text-secondary bg-surface-overlay border border-border-subtle hover:bg-surface-raised hover:text-text-primary transition-all active:scale-95 flex items-center gap-1.5"
        >
          <X size={12} />
          <span>Cancel</span>
        </button>

        <button
          type="button"
          onClick={handleSendNow}
          className="px-3.5 py-1.5 rounded-lg text-xs font-medium text-white bg-brand hover:bg-brand-light transition-all active:scale-95 shadow-sm flex items-center gap-1.5"
        >
          <Send size={12} />
          <span>Send Now</span>
        </button>
      </div>
    </motion.div>
  );
};

export default CommunicationConfirmationCard;
