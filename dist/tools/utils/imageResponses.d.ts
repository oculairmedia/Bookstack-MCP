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
export declare function normalizeImageListResponse(apiResponse: JsonValue, defaults: Defaults): {
    data: JsonValue;
    metadata?: ImageMetadata;
};
export {};
