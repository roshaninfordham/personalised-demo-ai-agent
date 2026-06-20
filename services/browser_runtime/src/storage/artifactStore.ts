import { createHash } from "node:crypto";

export type PutObjectInput = {
  artifactId: string;
  objectKey: string;
  content: Uint8Array;
  contentType: string;
  metadata: Record<string, string>;
};

export type StoredArtifact = {
  artifactId: string;
  bucket: string;
  objectKey: string;
  contentType: string;
  sizeBytes: number;
  sha256Hex: string;
  etag?: string;
};

export interface ArtifactStore {
  ensureBucket(): Promise<void>;
  putObject(input: PutObjectInput): Promise<StoredArtifact>;
  getPresignedGetUrl(objectKey: string, expiresSeconds: number): Promise<string>;
  deleteObject(objectKey: string): Promise<void>;
}

export class InMemoryArtifactStore implements ArtifactStore {
  private readonly objects = new Map<string, Uint8Array>();

  constructor(private readonly bucket = "memory-bucket") {}

  ensureBucket(): Promise<void> {
    return Promise.resolve(undefined);
  }

  putObject(input: PutObjectInput): Promise<StoredArtifact> {
    this.objects.set(input.objectKey, input.content);
    return Promise.resolve({
      artifactId: input.artifactId,
      bucket: this.bucket,
      objectKey: input.objectKey,
      contentType: input.contentType,
      sizeBytes: input.content.byteLength,
      sha256Hex: createHash("sha256").update(input.content).digest("hex"),
      etag: "memory",
    });
  }

  getPresignedGetUrl(objectKey: string): Promise<string> {
    return Promise.resolve(`memory://${this.bucket}/${objectKey}`);
  }

  deleteObject(objectKey: string): Promise<void> {
    this.objects.delete(objectKey);
    return Promise.resolve(undefined);
  }
}
