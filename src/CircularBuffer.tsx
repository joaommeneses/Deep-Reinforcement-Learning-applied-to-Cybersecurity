class CircularBuffer<T> {
    private size: number;                   //tamanho do buffer
    private buffer: T[];                    //array que armazena elementos do buffer
    private nextInsertIndex: number;        //numero que representa o indice onde o proximo elemento será inserido

    constructor(capacity: number) {
        this.buffer = new Array<T>(capacity);
        this.size = 0;
        this.nextInsertIndex = 0;
    }

    //recebe um elemento como parametro e insere no buffer, atualizando o indice 
    //se o tamanho do buffer for menor que a capacidade maxima o tamanho é incrementado
    enqueue(item: T) {
        this.buffer[this.nextInsertIndex] = item;
        this.nextInsertIndex = (this.nextInsertIndex + 1) % this.buffer.length;

        if (this.size < this.buffer.length) {
            this.size++;
        }
    }

    //remove e devolve  o elemento mais antigo do buffer
    //se o buffer estiver vazio devolve undefined        
    dequeue(): T | undefined {
        if (this.isEmpty()) {
            return undefined;
        }

        const oldestItem = this.buffer[(this.nextInsertIndex - this.size + this.buffer.length) % this.buffer.length];
        this.size--;
        return oldestItem;
    }

    //verifica se o buffer está vazio 
    isEmpty(): boolean {
        return this.size === 0;
    }

    //verifica se o bugger está cheio
    isFull(): boolean {
        return this.size === this.buffer.length;
    }

    //devolve o tamanho atual do buffer
    getSize(): number {
        return this.size;
    }

    //devolve um array com os elementos do buffer
    toArray(): T[] {
        const result: T[] = [];
        for (let i = 0; i < this.size; i++) {
            result[i] = this.buffer[(this.nextInsertIndex - this.size + i + this.buffer.length) % this.buffer.length];
        }
        return result;
    }
}

export default CircularBuffer;
