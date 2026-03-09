import { z } from "zod";
export declare const imageInputSchema: any;
export type ImageInput = z.infer<typeof imageInputSchema>;
export interface PreparedImagePayload {
    blob: Blob;
    fileName: string;
    mimeType: string;
}
export declare function prepareImagePayload(image: ImageInput, fallbackName?: string, fallbackType?: string): PreparedImagePayload;
