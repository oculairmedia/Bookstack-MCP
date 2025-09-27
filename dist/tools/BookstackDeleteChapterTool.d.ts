import { MCPTool } from "mcp-framework";
import { z } from "zod";
import { BookstackToolBase } from "./BookstackToolBase.js";
interface DeleteChapterInput {
    id: string;
}
declare class BookstackDeleteChapterTool extends MCPTool<DeleteChapterInput> {
    name: string;
    description: string;
    toolBase: BookstackToolBase;
    schema: {
        id: {
            type: z.ZodString;
            description: string;
        };
    };
    execute(input: DeleteChapterInput): Promise<string>;
}
export default BookstackDeleteChapterTool;
