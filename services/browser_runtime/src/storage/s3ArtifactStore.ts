import { createHash } from "node:crypto";

import { DeleteObjectCommand, GetObjectCommand, PutObjectCommand, S3Client } from "@aws-sdk/client-s3";
import { getSignedUrl } from "@aws-sdk/s3-request-presigner";

import type { BrowserRuntimeConfig } from "../config.js";
import type { ArtifactStore, PutObjectInput, StoredArtifact } from "./artifactStore.js";

export class S3ArtifactStore implements ArtifactStore {
  private readonly client: S3Client;

  constructor(private readonly config: BrowserRuntimeConfig) {
    this.client = new S3Client({
      endpoint: config.objectStorageEndpoint,
      region: config.objectStorageRegion,
      forcePathStyle: config.objectStorageForcePathStyle,
      credentials: {
        accessKeyId: config.objectStorageAccessKey,
        secretAccessKey: config.objectStorageSecretKey,
      },
    });
  }

  ensureBucket(): Promise<void> {
    return Promise.resolve(undefined);
  }

  async putObject(input: PutObjectInput): Promise<StoredArtifact> {
    const sha256Hex = createHash("sha256").update(input.content).digest("hex");
    const response = await this.client.send(
      new PutObjectCommand({
        Bucket: this.config.objectStorageBucket,
        Key: input.objectKey,
        Body: input.content,
        ContentType: input.contentType,
        Metadata: sanitizeMetadata({ ...input.metadata, sha256_hex: sha256Hex }),
      }),
    );
    const artifact: StoredArtifact = {
      artifactId: input.artifactId,
      bucket: this.config.objectStorageBucket,
      objectKey: input.objectKey,
      contentType: input.contentType,
      sizeBytes: input.content.byteLength,
      sha256Hex,
    };
    if (response.ETag !== undefined) {
      artifact.etag = response.ETag;
    }
    return artifact;
  }

  async getPresignedGetUrl(objectKey: string, expiresSeconds: number): Promise<string> {
    return getSignedUrl(
      this.client,
      new GetObjectCommand({ Bucket: this.config.objectStorageBucket, Key: objectKey }),
      { expiresIn: Math.min(expiresSeconds, this.config.objectStoragePresignedUrlTtlSeconds) },
    );
  }

  async deleteObject(objectKey: string): Promise<void> {
    await this.client.send(
      new DeleteObjectCommand({ Bucket: this.config.objectStorageBucket, Key: objectKey }),
    );
  }
}

function sanitizeMetadata(metadata: Record<string, string>): Record<string, string> {
  const output: Record<string, string> = {};
  for (const [key, value] of Object.entries(metadata)) {
    if (/secret|token|password|cookie|authorization/i.test(key)) {
      continue;
    }
    output[key] = value;
  }
  return output;
}
