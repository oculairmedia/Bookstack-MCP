import { z } from "zod";
import { BookstackTool } from "../bookstack/BookstackTool.js";
declare const schema: z.ZodObject<{
    id: z.ZodNumber;
}, "strip", z.ZodTypeAny, {
    id: number;
}, {
    id: number;
}>;
type DeleteBookInput = z.infer<typeof schema>;
declare class BookstackDeleteBookTool extends BookstackTool<DeleteBookInput> {
    name: string;
    description: string;
    schema: z.ZodObject<{
        id: z.ZodNumber;
    }, "strip", z.ZodTypeAny, {
        id: number;
    }, {
        id: number;
    }>;
    execute(input: DeleteBookInput): Promise<import("../bookstack/BookstackTool.js").ToolContent[]>;
}
export default BookstackDeleteBookTool;
