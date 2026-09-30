import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { CommunicationConfirmationCard, CommunicationConfirmationData } from '../CommunicationConfirmationCard';

// Mock framer-motion to render elements simply
jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, className, ...props }: any) => (
      <div className={className} {...props}>
        {children}
      </div>
    ),
  },
}));

describe('CommunicationConfirmationCard (B.COMM-3 Structured Pending Action)', () => {
  const sampleConfirmation: CommunicationConfirmationData = {
    channel: 'EMAIL',
    pending_action_id: 'pact_test12345678',
    sender_account: 'sender@example.com',
    recipient: 'client@example.com',
    subject: 'Meeting Confirmation',
    content: 'Are we meeting at 10 AM?',
    idempotency_key: 'idem_987654321',
    expires_at: '2026-10-01T12:00:00Z',
    requires_confirmation: true,
  };

  beforeEach(() => {
    jest.clearAllMocks();
    global.fetch = jest.fn();
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  test('renders pending action details without exposing credentials', () => {
    render(<CommunicationConfirmationCard confirmation={sampleConfirmation} />);

    expect(screen.getByText('Send email?')).toBeInTheDocument();
    expect(screen.getByText('Approval Required')).toBeInTheDocument();
    expect(screen.getByText('sender@example.com')).toBeInTheDocument();
    expect(screen.getByText('client@example.com')).toBeInTheDocument();
    expect(screen.getByText('Meeting Confirmation')).toBeInTheDocument();
    expect(screen.getByText('"Are we meeting at 10 AM?"')).toBeInTheDocument();

    // Verify pending_action_id is referenced
    expect(screen.getByText(/pact_test12/i)).toBeInTheDocument();

    // Verify no secret tokens or passwords exist in DOM
    expect(screen.queryByText(/access_token/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/password/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/secret/i)).not.toBeInTheDocument();
  });

  test('Send Now invokes dedicated /api/communication/actions/{id}/confirm endpoint directly', async () => {
    const mockOnConfirm = jest.fn();
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({
        status: 'sent',
        channel: 'EMAIL',
        recipient: 'client@example.com',
        message: 'Email sent successfully to client@example.com.',
      }),
    });

    render(
      <CommunicationConfirmationCard
        confirmation={sampleConfirmation}
        onConfirm={mockOnConfirm}
      />
    );

    const sendNowBtn = screen.getByRole('button', { name: /Send Now/i });
    fireEvent.click(sendNowBtn);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledTimes(1);
    });

    const [calledUrl, calledOptions] = (global.fetch as jest.Mock).mock.calls[0];
    expect(calledUrl).toContain('/api/communication/actions/pact_test12345678/confirm');
    expect(calledOptions.method).toBe('POST');

    // Confirmed callback invoked with structured response
    await waitFor(() => {
      expect(mockOnConfirm).toHaveBeenCalledWith(
        expect.objectContaining({ status: 'sent' })
      );
    });

    expect(screen.getByText(/Email sent successfully to client@example.com./i)).toBeInTheDocument();
  });

  test('Cancel invokes dedicated /api/communication/actions/{id}/cancel endpoint directly', async () => {
    const mockOnCancel = jest.fn();
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({
        status: 'cancelled',
        message: 'Communication action cancelled successfully.',
      }),
    });

    render(
      <CommunicationConfirmationCard
        confirmation={sampleConfirmation}
        onCancel={mockOnCancel}
      />
    );

    const cancelBtn = screen.getByRole('button', { name: /Cancel/i });
    fireEvent.click(cancelBtn);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledTimes(1);
    });

    const [calledUrl, calledOptions] = (global.fetch as jest.Mock).mock.calls[0];
    expect(calledUrl).toContain('/api/communication/actions/pact_test12345678/cancel');
    expect(calledOptions.method).toBe('POST');

    await waitFor(() => {
      expect(mockOnCancel).toHaveBeenCalled();
    });

    expect(screen.getByText(/Communication action was cancelled./i)).toBeInTheDocument();
  });

  test('Displays error message gracefully if server returns expiration or failure', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 410,
      json: async () => ({
        status: 'failed',
        error_code: 'ACTION_EXPIRED',
        error: 'Pending communication action has expired.',
      }),
    });

    render(<CommunicationConfirmationCard confirmation={sampleConfirmation} />);

    const sendNowBtn = screen.getByRole('button', { name: /Send Now/i });
    fireEvent.click(sendNowBtn);

    await waitFor(() => {
      expect(screen.getByText(/Pending communication action has expired./i)).toBeInTheDocument();
    });
  });

  test('Buttons are disabled while submitting to prevent repeated duplicate clicks', async () => {
    let resolveFetch: any;
    (global.fetch as jest.Mock).mockReturnValueOnce(
      new Promise((resolve) => {
        resolveFetch = resolve;
      })
    );

    render(<CommunicationConfirmationCard confirmation={sampleConfirmation} />);

    const sendNowBtn = screen.getByRole('button', { name: /Send Now/i });
    fireEvent.click(sendNowBtn);

    // During submission
    expect(screen.getByText(/Sending.../i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Sending.../i })).toBeDisabled();

    // Resolve
    resolveFetch({
      ok: true,
      status: 200,
      json: async () => ({ status: 'sent', message: 'Sent' }),
    });

    await waitFor(() => {
      expect(screen.queryByText(/Sending.../i)).not.toBeInTheDocument();
    });
  });
});
