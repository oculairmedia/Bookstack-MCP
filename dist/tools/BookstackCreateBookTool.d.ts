import { z } from "zod";
import { BookstackTool } from "../bookstack/BookstackTool.js";
declare const schema: any;
type CreateBookInput = z.infer<typeof schema>;
declare class BookstackCreateBookTool extends BookstackTool<CreateBookInput> {
    name: string;
    description: string;
    schema: any;
    execute(input: CreateBookInput): Promise<import("../bookstack/BookstackTool.js").ToolContent[]>;
}
export default BookstackCreateBookTool;
