import { z } from "zod";
import { BookstackTool } from "../bookstack/BookstackTool.js";
declare const schema: z.ZodObject<{
    id: z.ZodNumber;
    book_id: z.ZodOptional<z.ZodNumber>;
    name: z.ZodOptional<z.ZodString>;
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
    id: number;
    name?: string | undefined;
    description?: string | undefined;
    tags?: {
        value: string;
        name: string;
    }[] | undefined;
    book_id?: number | undefined;
    priority?: number | undefined;
}, {
    id: number;
    name?: string | undefined;
    description?: string | undefined;
    tags?: {
        value: string;
        name: string;
    }[] | undefined;
    book_id?: number | undefined;
    priority?: number | undefined;
}>;
type UpdateChapterInput = z.infer<typeof schema>;
declare class BookstackUpdateChapterTool extends BookstackTool<UpdateChapterInput> {
    name: string;
    description: string;
    schema: z.ZodObject<{
        id: z.ZodNumber;
        book_id: z.ZodOptional<z.ZodNumber>;
        name: z.ZodOptional<z.ZodString>;
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
        id: number;
        name?: string | undefined;
        description?: string | undefined;
        tags?: {
            value: string;
            name: string;
        }[] | undefined;
        book_id?: number | undefined;
        priority?: number | undefined;
    }, {
        id: number;
        name?: string | undefined;
        description?: string | undefined;
        tags?: {
            value: string;
            name: string;
        }[] | undefined;
        book_id?: number | undefined;
        priority?: number | undefined;
    }>;
    execute(input: UpdateChapterInput): Promise<import("../bookstack/BookstackTool.js").ToolContent[]>;
}
export default BookstackUpdateChapterTool;
