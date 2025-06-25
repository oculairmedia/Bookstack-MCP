import { MCPTool } from "mcp-framework";
import { z } from "zod";
import { BookstackToolBase } from "./BookstackToolBase.js";
interface ListPagesInput {
    offset?: string;
    count?: string;
}
declare class BookstackListPagesTool extends MCPTool<ListPagesInput> {
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
    execute(input: ListPagesInput): Promise<string>;
}
export default BookstackListPagesTool;
