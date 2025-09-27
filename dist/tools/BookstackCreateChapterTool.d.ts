import { z } from "zod";
import { BookstackTool } from "../bookstack/BookstackTool.js";
declare const schema: z.ZodObject<{
    book_id: z.ZodNumber;
    name: z.ZodString;
    description: z.ZodOptional<z.ZodString>;
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
    book_id: number;
    description?: string | undefined;
    tags?: {
        value: string;
        name: string;
    }[] | undefined;
    priority?: number | undefined;
}, {
    name: string;
    book_id: number;
    description?: string | undefined;
    tags?: {
        value: string;
        name: string;
    }[] | undefined;
    priority?: number | undefined;
}>;
type CreateChapterInput = z.infer<typeof schema>;
declare class BookstackCreateChapterTool extends BookstackTool<CreateChapterInput> {
    name: string;
    description: string;
    schema: z.ZodObject<{
        book_id: z.ZodNumber;
        name: z.ZodString;
        description: z.ZodOptional<z.ZodString>;
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
        book_id: number;
        description?: string | undefined;
        tags?: {
            value: string;
            name: string;
        }[] | undefined;
        priority?: number | undefined;
    }, {
        name: string;
        book_id: number;
        description?: string | undefined;
        tags?: {
            value: string;
            name: string;
        }[] | undefined;
        priority?: number | undefined;
    }>;
    execute(input: CreateChapterInput): Promise<import("../bookstack/BookstackTool.js").ToolContent[]>;
}
export default BookstackCreateChapterTool;
