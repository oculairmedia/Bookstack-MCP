export function normalizeImageListResponse(apiResponse, defaults) {
    if (isPagedEnvelope(apiResponse)) {
        const images = apiResponse.data;
        const metadata = {};
        if (typeof apiResponse.total === "number") {
            metadata.total = apiResponse.total;
        }
        if (typeof apiResponse.count === "number") {
            metadata.count = apiResponse.count;
        }
        else if (Array.isArray(images)) {
            metadata.count = images.length;
        }
        if (typeof apiResponse.offset === "number") {
            metadata.offset = apiResponse.offset;
        }
        else {
            metadata.offset = defaults.offset;
        }
        return { data: images, metadata };
    }
    if (Array.isArray(apiResponse)) {
        const metadata = {
            offset: defaults.offset,
            count: apiResponse.length,
        };
        return { data: apiResponse, metadata };
    }
    return { data: apiResponse };
}
function isPagedEnvelope(value) {
    if (!value || typeof value !== "object") {
        return false;
    }
    return "data" in value && Array.isArray(value.data);
}
