import { z } from "zod";
import { BookstackTool } from "../bookstack/BookstackTool.js";
declare const schema: any;
type UpdateBookInput = z.infer<typeof schema>;
declare class BookstackUpdateBookTool extends BookstackTool<UpdateBookInput> {
    name: string;
    description: string;
    schema: any;
    execute(input: UpdateBookInput): Promise<import("../bookstack/BookstackTool.js").ToolContent[]>;
}
export default BookstackUpdateBookTool;
