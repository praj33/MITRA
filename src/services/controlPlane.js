import { eventBus } from './eventBus.js';
export class ControlPlane {
  simulateResponse(text) {
    eventBus.emit('health.changed', { status: 'yellow' });
    setTimeout(() => {
      eventBus.emit('health.changed', { status: 'green' });
      eventBus.emit('notification.received', {
        role: 'mitra',
        text: 'Simulated response from UniGuru for: ' + text
      });
    }, 1500);
  }
}
export const controlPlane = new ControlPlane();
