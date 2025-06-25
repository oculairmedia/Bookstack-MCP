import { MCPTool } from "mcp-framework";
import { z } from "zod";
import { BookstackToolBase } from "./BookstackToolBase.js";
interface DeleteBookshelfInput {
    id: string;
}
declare class BookstackDeleteBookshelfTool extends MCPTool<DeleteBookshelfInput> {
    name: string;
    description: string;
    toolBase: BookstackToolBase;
    schema: {
        id: {
            type: z.ZodString;
            description: string;
        };
    };
    execute(input: DeleteBookshelfInput): Promise<string>;
}
export default BookstackDeleteBookshelfTool;
