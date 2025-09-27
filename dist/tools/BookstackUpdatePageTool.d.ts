import { z } from "zod";
import { BookstackTool } from "../bookstack/BookstackTool.js";
declare const schema: z.ZodObject<{
    id: z.ZodNumber;
    book_id: z.ZodOptional<z.ZodNumber>;
    chapter_id: z.ZodOptional<z.ZodNumber>;
    name: z.ZodOptional<z.ZodString>;
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
    id: number;
    name?: string | undefined;
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
    id: number;
    name?: string | undefined;
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
type UpdatePageInput = z.infer<typeof schema>;
declare class BookstackUpdatePageTool extends BookstackTool<UpdatePageInput> {
    name: string;
    description: string;
    schema: z.ZodObject<{
        id: z.ZodNumber;
        book_id: z.ZodOptional<z.ZodNumber>;
        chapter_id: z.ZodOptional<z.ZodNumber>;
        name: z.ZodOptional<z.ZodString>;
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
        id: number;
        name?: string | undefined;
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
        id: number;
        name?: string | undefined;
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
    execute(input: UpdatePageInput): Promise<import("../bookstack/BookstackTool.js").ToolContent[]>;
}
export default BookstackUpdatePageTool;
