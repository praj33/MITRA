import { Header } from './Header.js';
import { ConversationPanel } from './ConversationPanel.js';
import { Footer } from './Footer.js';
import { CapabilityLauncher } from './CapabilityLauncher.js';
import { HealthPanel } from './HealthPanel.js';
import { ActivityIndicator } from './ActivityIndicator.js';

export class MITRAWindow {
  constructor(runtimeService, eventBus, dockController) {
    this.runtimeService = runtimeService;
    this.eventBus = eventBus;
    this.dockController = dockController;
    
    this.element = document.createElement('div');
    this.element.className = 'mitra-window';
    this.state = 'minimized'; // 'minimized', 'expanded'

    this.header = new Header(
      () => this.minimize(),
      () => {
        // Toggle health panel
        this.healthPanel.toggle();
      }
    );

    this.healthPanel = new HealthPanel(eventBus);
    
    // Inject dock controller into header
    this.header.element.querySelector('.mitra-controls').prepend(dockController.element);

    this.conversation = new ConversationPanel(eventBus, runtimeService.context);
    
    this.launcher = new CapabilityLauncher(
      () => {}, 
      (capability) => {
        this.runtimeService.sendCapabilityRequest(capability);
      }
    );

    this.activityIndicator = new ActivityIndicator(eventBus);

    this.footer = new Footer(
      (text) => this.runtimeService.sendMessage(text),
      () => this.launcher.open()
    );

    // Assembly
    this.element.appendChild(this.header.element);
    this.element.appendChild(this.healthPanel.element);
    
    const contentArea = document.createElement('div');
    contentArea.className = 'mitra-content';
    contentArea.appendChild(this.conversation.element);
    contentArea.appendChild(this.launcher.element);
    this.element.appendChild(contentArea);

    this.element.appendChild(this.activityIndicator.element);
    this.element.appendChild(this.footer.element);
    
    this.onMinimize = null;
  }

  expand() {
    this.state = 'expanded';
    this.element.classList.add('expanded');
  }

  minimize() {
    this.state = 'minimized';
    this.element.classList.remove('expanded');
    if (this.onMinimize) this.onMinimize();
  }
}
