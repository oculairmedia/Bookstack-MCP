import { Buffer } from "node:buffer";
import { z } from "zod";
const fallbackFileName = "upload.bin";
const defaultMimeType = "application/octet-stream";
export const imageInputSchema = z
    .string()
    .min(1)
    .describe("Image payload as a base64 string or data URL");
export function prepareImagePayload(image, fallbackName = fallbackFileName, fallbackType = defaultMimeType) {
    const value = image.trim();
    if (value.startsWith("data:")) {
        return decodeDataUrl(value, fallbackName, fallbackType);
    }
    return decodeBase64(value, fallbackName, fallbackType);
}
function decodeDataUrl(dataUrl, fallbackName, fallbackType) {
    const match = /^data:([^;,]+)?(;base64)?,(.*)$/i.exec(dataUrl);
    if (!match) {
        throw new Error("Invalid data URL supplied for image payload");
    }
    const mimeType = match[1] ?? fallbackType;
    const isBase64 = Boolean(match[2]);
    const rawPayload = match[3] ?? "";
    const buffer = isBase64
        ? Buffer.from(rawPayload, "base64")
        : Buffer.from(decodeURIComponent(rawPayload), "utf8");
    if (!buffer.length) {
        throw new Error("Image payload is empty after decoding data URL");
    }
    const blob = new Blob([buffer], { type: mimeType });
    return {
        blob,
        fileName: fallbackName,
        mimeType,
    };
}
function decodeBase64(base64Value, fileName, mimeType) {
    try {
        const cleaned = base64Value.replace(/\s+/g, "");
        const buffer = Buffer.from(cleaned, "base64");
        if (!buffer.length) {
            throw new Error("Decoded image payload is empty");
        }
        const blob = new Blob([buffer], { type: mimeType });
        return {
            blob,
            fileName,
            mimeType,
        };
    }
    catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        throw new Error(`Failed to decode base64 image data: ${message}`);
    }
}
