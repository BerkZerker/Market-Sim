type MessageHandler = (data: unknown) => void;
type StatusHandler = (connected: boolean) => void;

export class WSClient {
  private ws: WebSocket | null = null;
  private channel: string;
  private handlers: MessageHandler[] = [];
  private statusHandlers: StatusHandler[] = [];
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;

  constructor(channel: string) {
    this.channel = channel;
  }

  connect() {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host;
    this.ws = new WebSocket(`${protocol}//${host}/ws/${this.channel}`);

    this.ws.onopen = () => {
      this.statusHandlers.forEach((h) => h(true));
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.handlers.forEach((h) => h(data));
      } catch {
        // ignore parse errors
      }
    };

    this.ws.onclose = () => {
      this.statusHandlers.forEach((h) => h(false));
      this.reconnectTimer = setTimeout(() => this.connect(), 3000);
    };

    this.ws.onerror = () => {
      this.ws?.close();
    };
  }

  onMessage(handler: MessageHandler) {
    this.handlers.push(handler);
    return () => {
      this.handlers = this.handlers.filter((h) => h !== handler);
    };
  }

  onStatusChange(handler: StatusHandler) {
    this.statusHandlers.push(handler);
    return () => {
      this.statusHandlers = this.statusHandlers.filter((h) => h !== handler);
    };
  }

  disconnect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
    }
    this.ws?.close();
    this.ws = null;
    this.handlers = [];
    this.statusHandlers = [];
  }
}
