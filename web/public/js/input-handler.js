class InputHandler {
    constructor(sessionId) {
        this.sessionId = sessionId;
        this.enabled = false;
        this.ws = null;
        this.cursorX = 0;
        this.cursorY = 0;
        this.viewport = null;
        this.cursor = null;

        this.BUTTON_MAP = {
            0: 'left',
            1: 'middle',
            2: 'right',
            3: 'back',
            4: 'forward'
        };

        this.KEY_MAP = {
            ' ': 'Space',
            'ArrowUp': 'ArrowUp',
            'ArrowDown': 'ArrowDown',
            'ArrowLeft': 'ArrowLeft',
            'ArrowRight': 'ArrowRight',
            'Enter': 'Enter',
            'Tab': 'Tab',
            'Escape': 'Escape',
            'Backspace': 'Backspace',
            'Delete': 'Delete',
            'Home': 'Home',
            'End': 'End',
            'PageUp': 'PageUp',
            'PageDown': 'PageDown'
        };
    }

    init(viewportSelector, cursorSelector) {
        this.viewport = document.querySelector(viewportSelector);
        this.cursor = document.querySelector(cursorSelector);

        if (!this.viewport || !this.cursor) {
            console.error('InputHandler: viewport or cursor element not found');
            return;
        }

        this.viewport.addEventListener('mousemove', this.onMouseMove.bind(this));
        this.viewport.addEventListener('mousedown', this.onMouseDown.bind(this));
        this.viewport.addEventListener('mouseup', this.onMouseUp.bind(this));
        this.viewport.addEventListener('click', this.onClick.bind(this));
        this.viewport.addEventListener('dblclick', this.onDblClick.bind(this));
        this.viewport.addEventListener('wheel', this.onWheel.bind(this), { passive: false });

        document.addEventListener('keydown', this.onKeyDown.bind(this));
        document.addEventListener('keyup', this.onKeyUp.bind(this));
        document.addEventListener('beforeinput', this.onBeforeInput.bind(this));

        this.cursor.style.display = 'none';
    }

    connect() {
        const wsProtocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
        this.ws = new WebSocket(`${wsProtocol}//${location.host}/input?session=${this.sessionId}`);

        this.ws.onopen = () => {
            console.log('Input WebSocket connected');
        };

        this.ws.onerror = (err) => {
            console.error('Input WebSocket error:', err);
        };

        this.ws.onclose = () => {
            console.log('Input WebSocket closed');
            this.ws = null;
        };
    }

    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }

    enable() {
        this.enabled = true;
        this.cursor.style.display = 'block';
        this.cursor.style.opacity = '1';
        this.viewport.style.cursor = 'none';
        this.connect();
    }

    disable() {
        this.enabled = false;
        this.cursor.style.opacity = '0';
        this.viewport.style.cursor = 'default';
        this.disconnect();
    }

    toggle() {
        if (this.enabled) {
            this.disable();
        } else {
            this.enable();
        }
        return this.enabled;
    }

    send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        }
    }

    getViewportCoordinates(clientX, clientY) {
        const rect = this.viewport.getBoundingClientRect();
        return {
            x: Math.round(clientX - rect.left),
            y: Math.round(clientY - rect.top)
        };
    }

    updateCursor(clientX, clientY) {
        const rect = this.viewport.getBoundingClientRect();
        this.cursor.style.left = `${clientX - rect.left}px`;
        this.cursor.style.top = `${clientY - rect.top}px`;
    }

    onMouseMove(e) {
        if (!this.enabled) return;
        e.preventDefault();

        const coords = this.getViewportCoordinates(e.clientX, e.clientY);
        this.updateCursor(e.clientX, e.clientY);

        this.send({
            type: 'mouse',
            action: 'move',
            x: coords.x,
            y: coords.y
        });
    }

    onMouseDown(e) {
        if (!this.enabled) return;
        e.preventDefault();

        const coords = this.getViewportCoordinates(e.clientX, e.clientY);
        const button = this.BUTTON_MAP[e.button] || 'left';

        this.send({
            type: 'mouse',
            action: 'down',
            x: coords.x,
            y: coords.y,
            button: button
        });
    }

    onMouseUp(e) {
        if (!this.enabled) return;
        e.preventDefault();

        const coords = this.getViewportCoordinates(e.clientX, e.clientY);
        const button = this.BUTTON_MAP[e.button] || 'left';

        this.send({
            type: 'mouse',
            action: 'up',
            x: coords.x,
            y: coords.y,
            button: button
        });
    }

    onClick(e) {
        if (!this.enabled) return;
        e.preventDefault();

        const coords = this.getViewportCoordinates(e.clientX, e.clientY);
        const button = this.BUTTON_MAP[e.button] || 'left';

        this.send({
            type: 'mouse',
            action: 'click',
            x: coords.x,
            y: coords.y,
            button: button
        });
    }

    onDblClick(e) {
        if (!this.enabled) return;
        e.preventDefault();

        const coords = this.getViewportCoordinates(e.clientX, e.clientY);

        this.send({
            type: 'mouse',
            action: 'dblclick',
            x: coords.x,
            y: coords.y
        });
    }

    onWheel(e) {
        if (!this.enabled) return;
        e.preventDefault();

        const coords = this.getViewportCoordinates(e.clientX, e.clientY);

        this.send({
            type: 'mouse',
            action: 'wheel',
            x: coords.x,
            y: coords.y,
            deltaX: e.deltaX,
            deltaY: e.deltaY
        });
    }

    onKeyDown(e) {
        if (!this.enabled) return;

        const key = this.KEY_MAP[e.key] || e.key;

        if (e.key.length === 1 || e.key.startsWith('Arrow') || e.key === 'Backspace' || e.key === 'Delete' || e.key === ' ') {
            if (e.key !== ' ' && !e.ctrlKey && !e.metaKey && !e.altKey) {
                e.preventDefault();
            }
        }

        this.send({
            type: 'keyboard',
            action: 'down',
            key: key
        });
    }

    onKeyUp(e) {
        if (!this.enabled) return;

        const key = this.KEY_MAP[e.key] || e.key;

        this.send({
            type: 'keyboard',
            action: 'up',
            key: key
        });
    }

    onBeforeInput(e) {
        if (!this.enabled) return;

        if (e.data && e.inputType === 'insertText') {
            this.send({
                type: 'text',
                action: 'input',
                text: e.data
            });
        }
    }
}

window.InputHandler = InputHandler;