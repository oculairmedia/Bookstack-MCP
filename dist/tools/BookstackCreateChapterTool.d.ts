import { MCPTool } from "mcp-framework";
import { z } from "zod";
import { BookstackToolBase } from "./BookstackToolBase.js";
interface Tag {
    name: string;
    value: string;
}
interface CreateChapterInput {
    book_id: string;
    name: string;
    description?: string;
    tags?: Tag[];
    priority?: string;
}
declare class BookstackCreateChapterTool extends MCPTool<CreateChapterInput> {
    name: string;
    description: string;
    toolBase: BookstackToolBase;
    schema: {
        book_id: {
            type: z.ZodString;
            description: string;
        };
        name: {
            type: z.ZodString;
            description: string;
        };
        description: {
            type: z.ZodOptional<z.ZodString>;
            description: string;
        };
        tags: {
            type: z.ZodOptional<z.ZodArray<z.ZodObject<{
                name: z.ZodString;
                value: z.ZodString;
            }, "strip", z.ZodTypeAny, {
                value: string;
                name: string;
            }, {
                value: string;
                name: string;
            }>, "many">>;
            description: string;
        };
        priority: {
            type: z.ZodOptional<z.ZodString>;
            description: string;
        };
    };
    execute(input: CreateChapterInput): Promise<string>;
}
export default BookstackCreateChapterTool;
