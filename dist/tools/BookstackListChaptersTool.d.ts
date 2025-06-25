import { MCPTool } from "mcp-framework";
import { z } from "zod";
import { BookstackToolBase } from "./BookstackToolBase.js";
interface ListChaptersInput {
    offset?: string;
    count?: string;
}
declare class BookstackListChaptersTool extends MCPTool<ListChaptersInput> {
    name: string;
    description: string;
    toolBase: BookstackToolBase;
    schema: {
        offset: {
            type: z.ZodOptional<z.ZodString>;
            description: string;
        };
        count: {
            type: z.ZodOptional<z.ZodString>;
            description: string;
        };
    };
    execute(input: ListChaptersInput): Promise<string>;
}
export default BookstackListChaptersTool;
