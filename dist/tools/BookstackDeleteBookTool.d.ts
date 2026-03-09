import { z } from "zod";
import { BookstackTool } from "../bookstack/BookstackTool.js";
declare const schema: any;
type DeleteBookInput = z.infer<typeof schema>;
declare class BookstackDeleteBookTool extends BookstackTool<DeleteBookInput> {
    name: string;
    description: string;
    schema: any;
    execute(input: DeleteBookInput): Promise<import("../bookstack/BookstackTool.js").ToolContent[]>;
}
export default BookstackDeleteBookTool;
