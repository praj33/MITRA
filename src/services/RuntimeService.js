import { eventBus } from './eventBus.js';
import { contextStore } from './contextStore.js';
import { controlPlane } from './controlPlane.js';
import { capabilityRuntime } from '../mock/capabilityRuntime.js';

export class RuntimeService {
  constructor() {
    this.context = contextStore;
    this.status = 'Disconnected';
    this.latency = '0ms';
  }

  async connectAll() {
    eventBus.emit('health.changed', { status: 'Connecting', latency: 'connecting...' });
    
    return new Promise((resolve) => {
      setTimeout(() => {
        this.status = 'Healthy';
        this.latency = '42ms';
        eventBus.emit('runtime.connected', {});
        eventBus.emit('health.changed', { status: 'Healthy', latency: '42ms' });
        this.startHeartbeat();
        resolve(true);
      }, 800);
    });
  }

  startHeartbeat() {
    // Dynamic health check simulation every 5 seconds
    setInterval(() => {
      if (this.status === 'Healthy' || this.status === 'Busy') {
        const randomLatency = Math.floor(35 + Math.random() * 20) + 'ms';
        this.latency = randomLatency;
        eventBus.emit('health.changed', { status: this.status, latency: this.latency });
      }
    }, 5000);
  }

  sendCapabilityRequest(capabilityName) {
    this.status = 'Busy';
    eventBus.emit('health.changed', { status: 'Busy', latency: this.latency });
    eventBus.emit('runtime.thinking', {});

    capabilityRuntime.execute(capabilityName);

    // Reset busy status after execution
    setTimeout(() => {
      this.status = 'Healthy';
      eventBus.emit('health.changed', { status: 'Healthy', latency: this.latency });
      eventBus.emit('runtime.idle', {});
    }, 1600);
  }

  sendMessage(text) {
    this.context.addMessage('user', text);
    this.status = 'Busy';
    eventBus.emit('health.changed', { status: 'Busy', latency: this.latency });
    eventBus.emit('runtime.thinking', {});

    controlPlane.simulateResponse(text);

    setTimeout(() => {
      this.status = 'Healthy';
      eventBus.emit('health.changed', { status: 'Healthy', latency: this.latency });
      eventBus.emit('runtime.idle', {});
    }, 1600);
  }

  simulateFailure() {
    this.status = 'Error';
    eventBus.emit('runtime.failed', { reason: 'Network Timeout' });
    eventBus.emit('health.changed', { status: 'Error', latency: '--' });

    // Auto recover after 3s
    setTimeout(() => {
      this.status = 'Healthy';
      eventBus.emit('runtime.recovered', {});
      eventBus.emit('health.changed', { status: 'Healthy', latency: '48ms' });
    }, 3000);
  }
}

export const runtimeService = new RuntimeService();
