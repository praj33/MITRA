import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import InputBar from '../InputBar';
import { useCompanionStore } from '../../../store/companion.store';

describe('InputBar - Structured Email Draft Editing Flow', () => {
  beforeEach(() => {
    useCompanionStore.setState({
      status: 'active',
      isMobile: false,
      draftEditState: null,
      messages: [],
    });
    jest.clearAllMocks();
  });

  test('1 & 5: enters structured draft edit mode and populates fields correctly', () => {
    const handleSend = jest.fn();

    // Set structured draft state
    useCompanionStore.setState({
      draftEditState: {
        mode: 'email_draft_edit',
        draftId: 'r_draft_test_123',
        to: 'rajprajapati1729@gmail.com',
        subject: 'MITRA Test',
        body: 'Hello Raj',
      },
    });

    render(<InputBar onSend={handleSend} />);

    // 1. Verify "Editing email draft" header appears
    expect(screen.getByText('Editing email draft')).toBeInTheDocument();
    expect(screen.getByText(/r_draft_te/)).toBeInTheDocument();

    // 5. Verify fields populate with exact draft values
    const toInput = screen.getByPlaceholderText('recipient@example.com') as HTMLInputElement;
    const subjectInput = screen.getByPlaceholderText('Email subject') as HTMLInputElement;
    const bodyInput = screen.getByPlaceholderText('Write your email message...') as HTMLTextAreaElement;

    expect(toInput.value).toBe('rajprajapati1729@gmail.com');
    expect(subjectInput.value).toBe('MITRA Test');
    expect(bodyInput.value).toBe('Hello Raj');

    // Verify onSend was NOT called
    expect(handleSend).not.toHaveBeenCalled();
  });

  test('6 & 7: user can edit subject and body', () => {
    const handleSend = jest.fn();

    useCompanionStore.setState({
      draftEditState: {
        mode: 'email_draft_edit',
        draftId: 'r_draft_test_456',
        to: 'rajprajapati1729@gmail.com',
        subject: 'MITRA Test',
        body: 'Hello Raj',
      },
    });

    render(<InputBar onSend={handleSend} />);

    const subjectInput = screen.getByPlaceholderText('Email subject') as HTMLInputElement;
    const bodyInput = screen.getByPlaceholderText('Write your email message...') as HTMLTextAreaElement;

    // 7. Edit subject
    fireEvent.change(subjectInput, { target: { value: 'MITRA Test Edited' } });
    expect(subjectInput.value).toBe('MITRA Test Edited');

    // 6. Edit body
    fireEvent.change(bodyInput, { target: { value: 'Hello Raj, this is the edited message.' } });
    expect(bodyInput.value).toBe('Hello Raj, this is the edited message.');

    expect(handleSend).not.toHaveBeenCalled();
  });

  test('2, 3, 4, 10: Cancel exits draft mode without calling onSend, LLM, or generating commands', () => {
    const handleSend = jest.fn();

    useCompanionStore.setState({
      draftEditState: {
        mode: 'email_draft_edit',
        draftId: 'r_draft_test_789',
        to: 'rajprajapati1729@gmail.com',
        subject: 'MITRA Test',
        body: 'Hello Raj',
      },
    });

    render(<InputBar onSend={handleSend} />);

    // Verify in edit mode
    expect(screen.getByText('Editing email draft')).toBeInTheDocument();

    // Click Cancel
    const cancelBtn = screen.getByText('Cancel');
    fireEvent.click(cancelBtn);

    // Verify exited edit mode
    expect(useCompanionStore.getState().draftEditState).toBeNull();
    expect(screen.queryByText('Editing email draft')).not.toBeInTheDocument();

    // Verify normal chat input returns
    expect(screen.getByPlaceholderText('Ask Mitra anything...')).toBeInTheDocument();

    // Invariants:
    // 2. onSend was NOT called
    expect(handleSend).not.toHaveBeenCalled();
    // 10. Normal input value is empty (no synthetic commands generated)
    const normalInput = screen.getByPlaceholderText('Ask Mitra anything...') as HTMLTextAreaElement;
    expect(normalInput.value).toBe('');
  });

  test('8, 9, 11: Send submits structured payload to /prepare-send and adds confirmation message', async () => {
    const handleSend = jest.fn();

    const mockPendingActionId = 'pact_test_prepare_999';
    const mockConfirmationPayload = {
      channel: 'EMAIL',
      pending_action_id: mockPendingActionId,
      sender_account: 'sender@example.com',
      recipient: 'rajprajapati1729@gmail.com',
      subject: 'MITRA Test',
      content: 'Hello Raj, this is the edited message.',
      action: 'SEND_MESSAGE',
      requires_confirmation: true,
    };

    // Mock fetch for prepare-send
    global.fetch = jest.fn().mockImplementation((url: string, options: any) => {
      if (url.includes('/prepare-send')) {
        const bodyObj = JSON.parse(options.body);
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            status: 'confirmation_required',
            pending_action_id: mockPendingActionId,
            message: "I've prepared the email. Please review and confirm before I send it.",
            confirmation: {
              ...mockConfirmationPayload,
              recipient: bodyObj.recipient,
              subject: bodyObj.subject,
              content: bodyObj.body,
            },
          }),
        });
      }
      return Promise.reject(new Error(`Unhandled fetch url: ${url}`));
    });

    useCompanionStore.setState({
      draftEditState: {
        mode: 'email_draft_edit',
        draftId: 'r_draft_test_e2e',
        to: 'rajprajapati1729@gmail.com',
        subject: 'MITRA Test',
        body: 'Hello Raj',
      },
    });

    render(<InputBar onSend={handleSend} />);

    // Edit body
    const bodyInput = screen.getByPlaceholderText('Write your email message...') as HTMLTextAreaElement;
    fireEvent.change(bodyInput, { target: { value: 'Hello Raj, this is the edited message.' } });

    // Submit structured draft
    const sendBtn = screen.getByRole('button', { name: /send/i });
    fireEvent.click(sendBtn);

    // Verify fetch was called with structured JSON fields
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/communication/drafts/r_draft_test_e2e/prepare-send'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({
            recipient: 'rajprajapati1729@gmail.com',
            subject: 'MITRA Test',
            body: 'Hello Raj, this is the edited message.',
          }),
        })
      );
    });

    // 8 & 9 & 11: Verify state after submit:
    await waitFor(() => {
      // Draft edit mode is closed
      expect(useCompanionStore.getState().draftEditState).toBeNull();

      // Assistant confirmation message was appended to conversation
      const messages = useCompanionStore.getState().messages;
      expect(messages.length).toBe(1);

      const confirmMsg = messages[0];
      expect(confirmMsg.role).toBe('assistant');
      expect(confirmMsg.capabilityResult?.status).toBe('pending');
      expect(confirmMsg.capabilityResult?.data?.pending_action_id).toBe(mockPendingActionId);

      const conf = confirmMsg.capabilityResult?.data?.confirmation;
      expect(conf.recipient).toBe('rajprajapati1729@gmail.com');
      expect(conf.subject).toBe('MITRA Test');
      expect(conf.content).toBe('Hello Raj, this is the edited message.');

      // Zero command contamination
      expect(conf.content).not.toContain('Send an email to');
      expect(conf.content).not.toContain('with subject');
      expect(conf.content).not.toContain('and message');
    });

    // Verify handleSend (the chat prompt sender) was NEVER called
    expect(handleSend).not.toHaveBeenCalled();
  });
});
