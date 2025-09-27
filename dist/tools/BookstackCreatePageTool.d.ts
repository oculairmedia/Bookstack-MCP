import { z } from "zod";
import { BookstackTool } from "../bookstack/BookstackTool.js";
declare const schema: z.ZodObject<{
    name: z.ZodString;
    book_id: z.ZodOptional<z.ZodNumber>;
    chapter_id: z.ZodOptional<z.ZodNumber>;
    markdown: z.ZodOptional<z.ZodString>;
    html: z.ZodOptional<z.ZodString>;
    tags: z.ZodOptional<z.ZodArray<z.ZodObject<{
        name: z.ZodString;
        value: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        value: string;
        name: string;
    }, {
        value: string;
        name: string;
    }>, "many">>;
    priority: z.ZodOptional<z.ZodNumber>;
}, "strip", z.ZodTypeAny, {
    name: string;
    tags?: {
        value: string;
        name: string;
    }[] | undefined;
    book_id?: number | undefined;
    priority?: number | undefined;
    chapter_id?: number | undefined;
    markdown?: string | undefined;
    html?: string | undefined;
}, {
    name: string;
    tags?: {
        value: string;
        name: string;
    }[] | undefined;
    book_id?: number | undefined;
    priority?: number | undefined;
    chapter_id?: number | undefined;
    markdown?: string | undefined;
    html?: string | undefined;
}>;
type CreatePageInput = z.infer<typeof schema>;
declare class BookstackCreatePageTool extends BookstackTool<CreatePageInput> {
    name: string;
    description: string;
    schema: z.ZodObject<{
        name: z.ZodString;
        book_id: z.ZodOptional<z.ZodNumber>;
        chapter_id: z.ZodOptional<z.ZodNumber>;
        markdown: z.ZodOptional<z.ZodString>;
        html: z.ZodOptional<z.ZodString>;
        tags: z.ZodOptional<z.ZodArray<z.ZodObject<{
            name: z.ZodString;
            value: z.ZodString;
        }, "strip", z.ZodTypeAny, {
            value: string;
            name: string;
        }, {
            value: string;
            name: string;
        }>, "many">>;
        priority: z.ZodOptional<z.ZodNumber>;
    }, "strip", z.ZodTypeAny, {
        name: string;
        tags?: {
            value: string;
            name: string;
        }[] | undefined;
        book_id?: number | undefined;
        priority?: number | undefined;
        chapter_id?: number | undefined;
        markdown?: string | undefined;
        html?: string | undefined;
    }, {
        name: string;
        tags?: {
            value: string;
            name: string;
        }[] | undefined;
        book_id?: number | undefined;
        priority?: number | undefined;
        chapter_id?: number | undefined;
        markdown?: string | undefined;
        html?: string | undefined;
    }>;
    execute(input: CreatePageInput): Promise<import("../bookstack/BookstackTool.js").ToolContent[]>;
}
export default BookstackCreatePageTool;
