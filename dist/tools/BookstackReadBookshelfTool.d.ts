import { MCPTool } from "mcp-framework";
import { z } from "zod";
import { BookstackToolBase } from "./BookstackToolBase.js";
interface ReadBookshelfInput {
    id: string;
}
declare class BookstackReadBookshelfTool extends MCPTool<ReadBookshelfInput> {
    name: string;
    description: string;
    toolBase: BookstackToolBase;
    schema: {
        id: {
            type: z.ZodString;
            description: string;
        };
    };
    execute(input: ReadBookshelfInput): Promise<string>;
}
export default BookstackReadBookshelfTool;
