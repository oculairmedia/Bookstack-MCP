import { MCPTool } from "mcp-framework";
import { z } from "zod";
import { BookstackToolBase } from "./BookstackToolBase.js";
interface Tag {
    name: string;
    value: string;
}
interface UpdatePageInput {
    id: string;
    book_id?: string;
    chapter_id?: string;
    name?: string;
    markdown?: string;
    html?: string;
    tags?: Tag[];
    priority?: string;
}
declare class BookstackUpdatePageTool extends MCPTool<UpdatePageInput> {
    name: string;
    description: string;
    toolBase: BookstackToolBase;
    schema: {
        id: {
            type: z.ZodString;
            description: string;
        };
        book_id: {
            type: z.ZodOptional<z.ZodString>;
            description: string;
        };
        chapter_id: {
            type: z.ZodOptional<z.ZodString>;
            description: string;
        };
        name: {
            type: z.ZodOptional<z.ZodString>;
            description: string;
        };
        markdown: {
            type: z.ZodOptional<z.ZodString>;
            description: string;
        };
        html: {
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
    execute(input: UpdatePageInput): Promise<string>;
}
export default BookstackUpdatePageTool;
