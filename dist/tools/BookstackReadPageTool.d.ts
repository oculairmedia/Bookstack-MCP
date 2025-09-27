import { MCPTool } from "mcp-framework";
import { z } from "zod";
import { BookstackToolBase } from "./BookstackToolBase.js";
interface ReadPageInput {
    id: string;
}
declare class BookstackReadPageTool extends MCPTool<ReadPageInput> {
    name: string;
    description: string;
    toolBase: BookstackToolBase;
    schema: {
        id: {
            type: z.ZodString;
            description: string;
        };
    };
    execute(input: ReadPageInput): Promise<string>;
}
export default BookstackReadPageTool;
