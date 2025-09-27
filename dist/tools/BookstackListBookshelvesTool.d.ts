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
type ListBookshelvesInput = z.infer<typeof schema>;
declare class BookstackListBookshelvesTool extends BookstackTool<ListBookshelvesInput> {
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
    execute(input: ListBookshelvesInput): Promise<import("../bookstack/BookstackTool.js").ToolContent[]>;
}
export default BookstackListBookshelvesTool;
