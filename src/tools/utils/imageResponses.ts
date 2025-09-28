import type { JsonValue } from "../../bookstack/BookstackTool.js";

export type ImageMetadata = {
  total?: number;
  count?: number;
  offset?: number;
  cached?: boolean;
  [key: string]: JsonValue | undefined;
};

interface Defaults {
  offset: number;
  count: number;
}

interface PagedEnvelope {
  data: JsonValue;
  total?: number;
  count?: number;
  offset?: number;
}

export function normalizeImageListResponse(
  apiResponse: JsonValue,
  defaults: Defaults,
): { data: JsonValue; metadata?: ImageMetadata } {
  if (isPagedEnvelope(apiResponse)) {
    const images = apiResponse.data as JsonValue;
    const metadata: ImageMetadata = {};

    if (typeof apiResponse.total === "number") {
      metadata.total = apiResponse.total;
    }

    if (typeof apiResponse.count === "number") {
      metadata.count = apiResponse.count;
    } else if (Array.isArray(images)) {
      metadata.count = images.length;
    }

    if (typeof apiResponse.offset === "number") {
      metadata.offset = apiResponse.offset;
    } else {
      metadata.offset = defaults.offset;
    }

    return { data: images, metadata };
  }

  if (Array.isArray(apiResponse)) {
    const metadata: ImageMetadata = {
      offset: defaults.offset,
      count: apiResponse.length,
    };
    return { data: apiResponse, metadata };
  }

  return { data: apiResponse };
}

function isPagedEnvelope(value: unknown): value is PagedEnvelope {
  if (!value || typeof value !== "object") {
    return false;
  }

  return "data" in value && Array.isArray((value as { data?: unknown }).data);
}
