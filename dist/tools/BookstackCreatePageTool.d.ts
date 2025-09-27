import { MCPTool } from "mcp-framework";
import { z } from "zod";
import { BookstackToolBase } from "./BookstackToolBase.js";
interface Tag {
    name: string;
    value: string;
}
interface CreatePageInput {
    name: string;
    book_id?: string;
    chapter_id?: string;
    markdown?: string;
    html?: string;
    tags?: Tag[];
    priority?: string;
}
declare class BookstackCreatePageTool extends MCPTool<CreatePageInput> {
    name: string;
    description: string;
    toolBase: BookstackToolBase;
    schema: {
        name: {
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
    execute(input: CreatePageInput): Promise<string>;
}
export default BookstackCreatePageTool;
