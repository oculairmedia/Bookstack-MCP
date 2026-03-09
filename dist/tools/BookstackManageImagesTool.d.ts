import { z } from "zod";
import { BookstackTool } from "../bookstack/BookstackTool.js";
declare const schema: any;
type ImageManagementInput = z.infer<typeof schema>;
declare class BookstackManageImagesTool extends BookstackTool<ImageManagementInput> {
    name: string;
    description: string;
    schema: any;
    private static readonly listCache;
    execute(input: ImageManagementInput): Promise<import("../bookstack/BookstackTool.js").ToolContent[]>;
    private handleCreate;
    private handleRead;
    private handleUpdate;
    private handleDelete;
    private handleList;
    private buildResponse;
    private buildListCacheKey;
    private getCachedList;
    private setCachedList;
    private invalidateListCache;
}
export default BookstackManageImagesTool;
