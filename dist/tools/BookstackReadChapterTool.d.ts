import { MCPTool } from "mcp-framework";
import { z } from "zod";
import { BookstackToolBase } from "./BookstackToolBase.js";
interface ReadChapterInput {
    id: string;
}
declare class BookstackReadChapterTool extends MCPTool<ReadChapterInput> {
    name: string;
    description: string;
    toolBase: BookstackToolBase;
    schema: {
        id: {
            type: z.ZodString;
            description: string;
        };
    };
    execute(input: ReadChapterInput): Promise<string>;
}
export default BookstackReadChapterTool;
