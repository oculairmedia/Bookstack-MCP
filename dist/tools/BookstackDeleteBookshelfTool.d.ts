import { z } from "zod";
import { BookstackTool } from "../bookstack/BookstackTool.js";
declare const schema: any;
type DeleteBookshelfInput = z.infer<typeof schema>;
declare class BookstackDeleteBookshelfTool extends BookstackTool<DeleteBookshelfInput> {
    name: string;
    description: string;
    schema: any;
    execute(input: DeleteBookshelfInput): Promise<import("../bookstack/BookstackTool.js").ToolContent[]>;
}
export default BookstackDeleteBookshelfTool;
