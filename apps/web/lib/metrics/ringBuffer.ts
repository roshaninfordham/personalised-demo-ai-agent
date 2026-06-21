export class RingBuffer<T> {
  private readonly values: Array<T | undefined>;
  private start = 0;
  private size = 0;

  constructor(readonly capacity: number) {
    if (!Number.isInteger(capacity) || capacity <= 0) {
      throw new Error("RingBuffer capacity must be a positive integer.");
    }
    this.values = Array.from<T | undefined>({ length: capacity });
  }

  push(value: T): void {
    const index = (this.start + this.size) % this.capacity;
    this.values[index] = value;
    if (this.size < this.capacity) {
      this.size += 1;
    } else {
      this.start = (this.start + 1) % this.capacity;
    }
  }

  toArray(): T[] {
    const output: T[] = [];
    for (let offset = 0; offset < this.size; offset += 1) {
      const value = this.values[(this.start + offset) % this.capacity];
      if (value !== undefined) output.push(value);
    }
    return output;
  }

  clear(): void {
    this.values.fill(undefined);
    this.start = 0;
    this.size = 0;
  }

  get length(): number {
    return this.size;
  }
}
