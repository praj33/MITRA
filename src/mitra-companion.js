import { runtimeService } from './services/RuntimeService.js';
import { eventBus } from './services/eventBus.js';
import { MITRAButton } from './components/MITRAButton.js';
import { MITRAWindow } from './components/MITRAWindow.js';
import { NotificationCenter } from './components/NotificationCenter.js';
import { DockController } from './components/DockController.js';

class MitraCompanion extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
  }

  async connectedCallback() {
    this.render();
    
    // Connect runtime after rendering UI
    await runtimeService.connectAll();
  }

  render() {
    // Inject stylesheet
    const styleLink = document.createElement('link');
    styleLink.setAttribute('rel', 'stylesheet');
    styleLink.setAttribute('href', '../styles/mitra-companion.css');
    this.shadowRoot.appendChild(styleLink);

    // Shell container
    const shell = document.createElement('div');
    shell.id = 'mitra-shell';
    shell.classList.add('floating');
    this.shadowRoot.appendChild(shell);

    // Global Notifications
    const notificationCenter = new NotificationCenter(eventBus);
    shell.appendChild(notificationCenter.element);

    // Dock Controller
    const dockController = new DockController(shell);

    // Main Window
    const mitraWindow = new MITRAWindow(runtimeService, eventBus, dockController);
    
    // FAB
    const mitraButton = new MITRAButton(() => {
      mitraButton.hide();
      mitraWindow.expand();
    });

    // Wire up events
    mitraWindow.onMinimize = () => {
      setTimeout(() => mitraButton.show(), 300); 
    };

    eventBus.on('runtime.thinking', () => mitraButton.setThinking(true));
    eventBus.on('runtime.idle', () => mitraButton.setThinking(false));
    eventBus.on('capability.finished', () => mitraButton.setThinking(false));
    eventBus.on('notification.received', () => mitraButton.setThinking(false));

    // Append to shell
    shell.appendChild(mitraWindow.element);
    shell.appendChild(mitraButton.element);
  }
}

customElements.define('mitra-companion', MitraCompanion);
