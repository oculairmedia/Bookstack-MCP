import { z } from "zod";
import { BookstackTool } from "../bookstack/BookstackTool.js";
declare const schema: z.ZodObject<{
    offset: z.ZodOptional<z.ZodNumber>;
    count: z.ZodOptional<z.ZodNumber>;
}, "strip", z.ZodTypeAny, {
    offset?: number | undefined;
    count?: number | undefined;
}, {
    offset?: number | undefined;
    count?: number | undefined;
}>;
type ListBooksInput = z.infer<typeof schema>;
declare class BookstackListBooksTool extends BookstackTool<ListBooksInput> {
    name: string;
    description: string;
    schema: z.ZodObject<{
        offset: z.ZodOptional<z.ZodNumber>;
        count: z.ZodOptional<z.ZodNumber>;
    }, "strip", z.ZodTypeAny, {
        offset?: number | undefined;
        count?: number | undefined;
    }, {
        offset?: number | undefined;
        count?: number | undefined;
    }>;
    execute(input: ListBooksInput): Promise<import("../bookstack/BookstackTool.js").ToolContent[]>;
}
export default BookstackListBooksTool;
