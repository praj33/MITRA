import React from 'react';
import { render, screen, fireEvent, act } from '@testing-library/react';
import App from './App';
import { CompanionService } from './services/companion.service';
import { useCompanionStore } from './store/companion.store';

describe('App Component Generation & New Chat Lifecycle', () => {
  beforeEach(() => {
    useCompanionStore.setState({
      status: 'active',
      messages: [],
      isMobile: false,
    });
    jest.restoreAllMocks();
  });

  test('renders Mitra shell without crashing', () => {
    const { container } = render(<App />);
    expect(container.querySelector('.mitra-shell')).toBeInTheDocument();
  });

  test('New Chat aborts active generation and resets status and messages', async () => {
    let aborted = false;
    jest.spyOn(CompanionService, 'chatStream').mockImplementation((_userId, _msg, _onToken, signal) => {
      return new Promise((_resolve, reject) => {
        signal?.addEventListener('abort', () => {
          aborted = true;
          const err = new Error('Aborted');
          err.name = 'AbortError';
          reject(err);
        });
      });
    });

    await act(async () => {
      render(<App />);
      await new Promise(r => setTimeout(r, 10));
    });

    // Start generation
    await act(async () => {
      (window as any).__MITRA_SEND__('Test question');
    });

    expect(useCompanionStore.getState().status).toBe('thinking');

    // Trigger New Chat
    act(() => {
      (window as any).__MITRA_NEW_CHAT__();
    });

    expect(aborted).toBe(true);
    expect(useCompanionStore.getState().status).toBe('active');
    expect(useCompanionStore.getState().messages).toEqual([]);
  });

  test('Stop then immediate Send sequence cancels previous stream and starts new turn', async () => {
    let firstAborted = false;
    let streamCallCount = 0;

    jest.spyOn(CompanionService, 'chatStream').mockImplementation((_userId, _msg, _onToken, signal) => {
      streamCallCount++;
      if (streamCallCount === 1) {
        return new Promise((_resolve, reject) => {
          signal?.addEventListener('abort', () => {
            firstAborted = true;
            const err = new Error('Aborted');
            err.name = 'AbortError';
            reject(err);
          });
        });
      }
      return Promise.resolve('Answer for Message B');
    });

    await act(async () => {
      render(<App />);
      await new Promise(r => setTimeout(r, 10));
    });

    // 1. Send Message A
    await act(async () => {
      (window as any).__MITRA_SEND__('Message A');
    });
    expect(useCompanionStore.getState().status).toBe('thinking');

    // 2. Stop Generation via Stop button
    const stopBtn = screen.getByLabelText(/stop generation/i);
    expect(stopBtn).toBeInTheDocument();
    act(() => {
      fireEvent.click(stopBtn);
    });

    expect(firstAborted).toBe(true);
    expect(useCompanionStore.getState().status).toBe('active');

    const msgsAfterStop = useCompanionStore.getState().messages;
    expect(msgsAfterStop[msgsAfterStop.length - 1].content).toContain('Generation stopped');

    // 3. Immediately Send Message B
    act(() => {
      (window as any).__MITRA_SEND__('Message B');
    });

    expect(useCompanionStore.getState().status).toBe('thinking');
    expect(streamCallCount).toBe(2);
  });
});
