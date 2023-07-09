class CircularBuffer<T> {
    private size: number;
    private buffer: T[];
    private nextInsertIndex: number;

    constructor(capacity: number) {
        this.buffer = new Array<T>(capacity);
        this.size = 0;
        this.nextInsertIndex = 0;
    }

    enqueue(item: T) {
        this.buffer[this.nextInsertIndex] = item;
        this.nextInsertIndex = (this.nextInsertIndex + 1) % this.buffer.length;

        if (this.size < this.buffer.length) {
            this.size++;
        }
    }

    dequeue(): T | undefined {
        if (this.isEmpty()) {
            return undefined;
        }

        const oldestItem = this.buffer[(this.nextInsertIndex - this.size + this.buffer.length) % this.buffer.length];
        this.size--;
        return oldestItem;
    }

    isEmpty(): boolean {
        return this.size === 0;
    }

    isFull(): boolean {
        return this.size === this.buffer.length;
    }

    getSize(): number {
        return this.size;
    }

    toArray(): T[] {
        const result: T[] = [];
        for (let i = 0; i < this.size; i++) {
            result[i] = this.buffer[(this.nextInsertIndex - this.size + i + this.buffer.length) % this.buffer.length];
        }
        return result;
    }
}

export default CircularBuffer;
