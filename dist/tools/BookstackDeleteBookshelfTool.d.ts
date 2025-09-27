import { z } from "zod";
import { BookstackTool } from "../bookstack/BookstackTool.js";
declare const schema: z.ZodObject<{
    id: z.ZodNumber;
}, "strip", z.ZodTypeAny, {
    id: number;
}, {
    id: number;
}>;
type DeleteBookshelfInput = z.infer<typeof schema>;
declare class BookstackDeleteBookshelfTool extends BookstackTool<DeleteBookshelfInput> {
    name: string;
    description: string;
    schema: z.ZodObject<{
        id: z.ZodNumber;
    }, "strip", z.ZodTypeAny, {
        id: number;
    }, {
        id: number;
    }>;
    execute(input: DeleteBookshelfInput): Promise<import("../bookstack/BookstackTool.js").ToolContent[]>;
}
export default BookstackDeleteBookshelfTool;
