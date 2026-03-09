import { z } from "zod";
import { BookstackTool } from "../bookstack/BookstackTool.js";
declare const schema: any;
type UpdateBookshelfInput = z.infer<typeof schema>;
declare class BookstackUpdateBookshelfTool extends BookstackTool<UpdateBookshelfInput> {
    name: string;
    description: string;
    schema: any;
    execute(input: UpdateBookshelfInput): Promise<import("../bookstack/BookstackTool.js").ToolContent[]>;
}
export default BookstackUpdateBookshelfTool;
