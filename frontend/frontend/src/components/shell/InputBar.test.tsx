import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import InputBar, { validateAttachment } from './InputBar';
import { useCompanionStore } from '../../store/companion.store';

describe('InputBar Component Phase A', () => {
  beforeEach(() => {
    useCompanionStore.setState({ status: 'active', isMobile: false });
  });

  test('renders attach button and file input with restricted accept types', () => {
    const handleSend = jest.fn();
    const { container } = render(<InputBar onSend={handleSend} />);

    const attachBtn = screen.getByLabelText(/attach file/i);
    expect(attachBtn).toBeInTheDocument();
    expect(attachBtn).toHaveAttribute('id', 'inputbar-attach');
    expect(attachBtn.className).toContain('flex');
    expect(attachBtn.className).not.toContain('hidden sm:flex');

    const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement;
    expect(fileInput).toBeInTheDocument();
    // Must NOT contain generic image/*
    expect(fileInput.getAttribute('accept')).not.toContain('image/*');
    // Must contain declared types
    expect(fileInput.getAttribute('accept')).toBe(
      '.pdf,.docx,.txt,.md,.json,.csv,.jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp'
    );
  });

  describe('validateAttachment Contract', () => {
    test('accepts whitelisted document and image extensions', () => {
      const allowed = [
        { name: 'document.pdf', type: 'application/pdf' },
        { name: 'resume.docx', type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' },
        { name: 'notes.txt', type: 'text/plain' },
        { name: 'README.md', type: 'text/markdown' },
        { name: 'data.json', type: 'application/json' },
        { name: 'table.csv', type: 'text/csv' },
        { name: 'photo.jpg', type: 'image/jpeg' },
        { name: 'photo.jpeg', type: 'image/jpeg' },
        { name: 'screenshot.png', type: 'image/png' },
        { name: 'banner.webp', type: 'image/webp' },
      ];

      for (const item of allowed) {
        const result = validateAttachment(item);
        expect(result.valid).toBe(true);
        expect(result.error).toBeUndefined();
      }
    });

    test('strictly rejects forbidden vector and non-whitelisted image formats', () => {
      const forbiddenImages = [
        { name: 'icon.svg', type: 'image/svg+xml' },
        { name: 'animation.gif', type: 'image/gif' },
        { name: 'graphic.bmp', type: 'image/bmp' },
        { name: 'scan.tiff', type: 'image/tiff' },
        { name: 'scan.tif', type: 'image/tiff' },
        { name: 'photo.heic', type: 'image/heic' },
        { name: 'favicon.ico', type: 'image/x-icon' },
      ];

      for (const item of forbiddenImages) {
        const result = validateAttachment(item);
        expect(result.valid).toBe(false);
        expect(result.error).toContain('SVG, GIF, and other image types are not supported');
      }
    });

    test('rejects arbitrary executables and script files', () => {
      const forbiddenFiles = [
        { name: 'virus.exe', type: 'application/x-msdownload' },
        { name: 'script.sh', type: 'application/x-sh' },
        { name: 'archive.zip', type: 'application/zip' },
        { name: 'code.py', type: 'text/x-python' },
      ];

      for (const item of forbiddenFiles) {
        const result = validateAttachment(item);
        expect(result.valid).toBe(false);
      }
    });
  });

  test('allows selecting and clearing an attached PDF file in UI', () => {
    const handleSend = jest.fn();
    const { container } = render(<InputBar onSend={handleSend} />);

    const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(['test pdf content'], 'sample.pdf', { type: 'application/pdf' });
    fireEvent.change(fileInput, { target: { files: [file] } });

    // File pill should appear
    expect(screen.getByText('sample.pdf')).toBeInTheDocument();

    // Remove file button
    const removeBtn = screen.getByLabelText(/remove attached file/i);
    expect(removeBtn).toBeInTheDocument();
    fireEvent.click(removeBtn);

    // File pill should disappear
    expect(screen.queryByText('sample.pdf')).not.toBeInTheDocument();
  });

  test('rejects SVG file and does not show attachment pill in UI', () => {
    const handleSend = jest.fn();
    const { container } = render(<InputBar onSend={handleSend} />);

    const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement;
    const svgFile = new File(['<svg></svg>'], 'badge.svg', { type: 'image/svg+xml' });
    fireEvent.change(fileInput, { target: { files: [svgFile] } });

    // File pill must NOT be rendered
    expect(screen.queryByText('badge.svg')).not.toBeInTheDocument();
  });

  test('rejects GIF file and does not show attachment pill in UI', () => {
    const handleSend = jest.fn();
    const { container } = render(<InputBar onSend={handleSend} />);

    const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement;
    const gifFile = new File(['GIF89a'], 'meme.gif', { type: 'image/gif' });
    fireEvent.change(fileInput, { target: { files: [gifFile] } });

    // File pill must NOT be rendered
    expect(screen.queryByText('meme.gif')).not.toBeInTheDocument();
  });

  test('appends [Attached file: name] to message when sent with attachment', () => {
    const handleSend = jest.fn();
    const { container } = render(<InputBar onSend={handleSend} />);

    const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(['image bytes'], 'diagram.png', { type: 'image/png' });
    fireEvent.change(fileInput, { target: { files: [file] } });

    const textarea = screen.getByPlaceholderText(/ask mitra anything/i);
    fireEvent.change(textarea, { target: { value: 'Analyze this chart' } });

    const sendBtn = screen.getByLabelText(/send message/i);
    fireEvent.click(sendBtn);

    expect(handleSend).toHaveBeenCalledWith('Analyze this chart [Attached file: diagram.png]', false);
    expect(screen.queryByText('diagram.png')).not.toBeInTheDocument();
  });

  test('renders Stop button when companion status is thinking and triggers onStop', () => {
    const handleSend = jest.fn();
    const handleStop = jest.fn();

    useCompanionStore.setState({ status: 'thinking' });

    render(<InputBar onSend={handleSend} onStop={handleStop} />);

    const stopBtn = screen.getByLabelText(/stop generation/i);
    expect(stopBtn).toBeInTheDocument();
    expect(stopBtn).toHaveAttribute('id', 'inputbar-stop');
    expect(screen.queryByLabelText(/send message/i)).not.toBeInTheDocument();

    fireEvent.click(stopBtn);
    expect(handleStop).toHaveBeenCalledTimes(1);
  });

  test('renders Send button when companion status is active', () => {
    const handleSend = jest.fn();
    useCompanionStore.setState({ status: 'active' });

    render(<InputBar onSend={handleSend} />);

    const sendBtn = screen.getByLabelText(/send message/i);
    expect(sendBtn).toBeInTheDocument();
    expect(sendBtn).toHaveAttribute('id', 'inputbar-send');
    expect(screen.queryByLabelText(/stop generation/i)).not.toBeInTheDocument();
  });
});
