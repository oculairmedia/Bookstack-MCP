import { MCPTool } from "mcp-framework";
import { z } from "zod";
import { BookstackToolBase } from "./BookstackToolBase.js";
interface ReadBookInput {
    id: string;
}
declare class BookstackReadBookTool extends MCPTool<ReadBookInput> {
    name: string;
    description: string;
    toolBase: BookstackToolBase;
    schema: {
        id: {
            type: z.ZodString;
            description: string;
        };
    };
    execute(input: ReadBookInput): Promise<string>;
}
export default BookstackReadBookTool;
